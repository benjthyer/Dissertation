"""
Win-06-01b "naive" isothermal step-heat analysis: fits the n0/lambda
exponential model independently for each of the 10 informed/naive-bracketed
isothermal sequences, then uses those fits both for the per-sequence
diagnostic plots and to derive the Arrhenius plot -- rather than the
lambda/K values already stored in the spreadsheet.

The fit itself uses forward_permeate1 (the individual, per-measurement
step-yield model: m_i = n0*(1-exp(-lambda*t_i)) - n0*(1-exp(-lambda*t_{i-1})),
weighted by each measurement's own uncertainty), NOT the naive cumulative
forward_permeate model fit directly to running-total cumulative yields.
The latter is known-biased (errors and uncertainties from earlier
measurements propagate into and inflate the leverage of later cumulative
values) -- this is exactly the same "eqn 3.6a" bias problem this chapter's
Supplementary Information used to derive its own from-scratch fix for,
duplicating work already done in Chapter 1's Eq.~\\eqref{eq:incyield}
(same file's own forward_permeate1/KenColdInversion1 already implement it,
algebraically identical to the old from-scratch derivation -- they just
weren't wired up to this script). Standardizing on Chapter 1's equation
here removes the need for Chapter 2 to carry its own redundant derivation.

FirstOrdInversion's own initial guess (n0 ~ 1 pccSTP) is tuned for the
much larger Winsor isothermal yields and fails to converge on these
~0.01-0.05 pccSTP yields, so the fit is done here directly with an
initial guess scaled to the first step's yield (same approach as
diffusion_utils.KenColdInversion/KenColdInversion1).

Reads: Win0601bHT_data_and_reduction.xlsx
  - Sheet 'Fit Lambdas' (formerly 'Apparent Permeation Rate Constants'): raw per-step 3He
    yields (and their 2-sigma uncertainties) for the 10 sequences, alongside
    the workbook's own in-sheet fit of each (not used here -- see the module
    docstring's second paragraph). Series ID is only populated on each
    block's first row (blocks of 3-4 rows separated by blank rows, starting
    row 40), so it is forward-filled here. The sheet has several duplicate
    "2σ" column headers (one per derived quantity); the one immediately
    following "3He measured (pccSTP)" is renamed for unambiguous access.
  - Sheet 'Raw Data and Corrections', cells D142:E144: two independent
    ID/OD tube-geometry measurements and their derived geometric factors
    G = 2/(ln(OD/ID)*(ID/2)^2), averaged the same way the spreadsheet's
    own 'G (cm^-1)' constant is, used to convert fitted lambda (s^-1) to
    permeability K (atoms/(sec*cm*atm)) via K = lambda/(G*Ratoms*T).
  - Sheet 'Raw Data and Corrections' again, this time its own per-measurement
    rows (matched to 'Fit Lambdas' by the shared 'Time (Pump out)' timestamp,
    a unique key for every measurement in the run): read only as a
    cross-check, immediately before writing the raw-data table below, that
    Temperature/step time/3He yield in 'Fit Lambdas' were carried over
    correctly from this master sheet -- so the published table and the
    fits/plots above can never silently drift out of sync with it. (2-sigma
    is not part of this check: 'Raw Data and Corrections' reports each
    measurement's own counting/sensitivity uncertainty, while 'Fit Lambdas'
    additionally propagates blank/calibration uncertainty into a larger
    2-sigma, so the two are legitimately different, not a copy of each
    other.)

Outputs:
  PermeationStepFits_Grid.pdf              - one panel per sequence (5x2); used in the
                                               dissertation (Chapter 2)
  PermeationStepFits_Grid_Top4.pdf         - same panels/fits as above, just the first
                                               4 sequences (top two rows of the 5x2 grid),
                                               as a smaller example figure for the GCA
                                               manuscript, whose Supporting Information
                                               carries the complete 10-sequence raw/fit
                                               tables (\ChTwoPermStepRawTable/\ChTwoPermStepFitTable
                                               below) for readers who want the rest
  PermeationStepFits_150min_byTemp.pdf     - 150-minute-step sequences, superimposed
  PermeationStepFits_120min_byTemp.pdf     - 120-minute-step sequences, superimposed
  AmpoulePermeability_Arrhenius.pdf                 - ln(K) vs 10^4/T, built from these fits,
                                               overlaid with the simulated lambda fits
                                               from goethite_thermal_sims.py (read from
                                               data/goethite_thermal_sim_lambdas.csv, if
                                               present -- run that script first to
                                               (re)generate it). Both the actual and
                                               simulated points share one "Isothermal
                                               Step Duration" color scale, and the top
                                               (Temperature) axis is ticked at exactly
                                               the simulation grid's own hold
                                               temperatures.
  generated/data/permstep_lambda_arrhenius_cache.json - slope/intercept/R^2/activation-energy
                                               (with 2 s.e. uncertainty) of the ln(K)
                                               vs 10^4/T regression above, so the main
                                               text/SI can cite these numbers from a
                                               single reproducible source rather than
                                               a hand-copied value. Also includes
                                               lam_min/lam_max (s^-1), the range of the
                                               10 per-series fitted rate constants
                                               themselves (popt[0] of each fit_n0_lambda
                                               call above), quoted in the Results text
                                               (\\ChTwoPermLamMin/\\ChTwoPermLamMax).
  ../chapter2_permstep_isothermal_tables.tex   - \\newcommand macros \\ChTwoPermStepRawTable
                                               (the 10-sequence raw step-heat dataset,
                                               from 'Fit Lambdas', cross-checked against
                                               'Raw Data and Corrections' above) and
                                               \\ChTwoPermStepFitTable (per-sequence fitted
                                               lambda/n0 +/- 2-sigma from the fits above),
                                               each expanding to a complete table
                                               environment. Same \\newcommand-macro
                                               pattern as write_chapter2_macros.py/
                                               chapter2_derived_values.tex, so
                                               chapter2goethite_SI_body.tex can
                                               \\ChTwoPermStepRawTable/\\ChTwoPermStepFitTable
                                               rather than hand-copying these tables.
                                               \\input{} by chapter2goethite_SI.tex and
                                               chapter2.tex the same way
                                               chapter2_derived_values.tex already is.
"""
import json
import os
import sys
import numpy as np
import pandas as pd
import scipy.optimize
import scipy.stats
import matplotlib as mpl
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import accumulate, forward_permeate, forward_permeate1, Ratoms, Rcal
from thermochr_utils import make_grid, swets, Jones
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)
CACHE_PATH = os.path.join(FIG_DIR, 'generated', 'data', 'permstep_lambda_arrhenius_cache.json')
TABLES_OUT_PATH = os.path.join(FIG_DIR, '..', 'Writing', 'chapter2_permstep_isothermal_tables.tex')

TEMP_VMIN, TEMP_VMAX = 90, 110  # shared color scale between the two by-temperature plots


def fit_n0_lambda(t, He, He_sigma, lamb0=6E-6):
    """Fit forward_permeate1 (Chapter 1's Eq.~\\eqref{eq:incyield}: the
    individual, non-cumulative-biased step-yield model) to a step-heat
    series via weighted non-linear least squares, seeding n0 from the
    first step's yield. Returns (lambda, n0, sigma_lambda, sigma_n0)."""
    cumt = [0] + accumulate(t).tolist()
    tinput = np.array([[cumt[i], cumt[i + 1]] for i in range(len(cumt) - 1)]).T
    n0_guess = He[0] / (1 - np.exp(-lamb0 * t[0]))
    out, cov = scipy.optimize.curve_fit(forward_permeate1, tinput, He,
                                         sigma=He_sigma, p0=[lamb0, n0_guess])
    return out[0], out[1], np.sqrt(cov[0, 0]), np.sqrt(cov[1, 1])


# ---------------------------------------------------------------------------
# Tube geometry: same two ID/OD measurements, and their average G, that the
# spreadsheet itself uses to convert lambda to K.
# ---------------------------------------------------------------------------
"""ID_cm = np.array([0.0505, 0.054])
OD_cm = np.array([0.0787, 0.0832])
G = np.mean(2 / (np.log(OD_cm / ID_cm) * (ID_cm / 2) ** 2))"""
ID_cm = 0.052
OD_cm = 0.081
G = 2 / (np.log(OD_cm / ID_cm) * (ID_cm / 2) ** 2)
def lambda_to_K(lam, T_K):
    return lam / (G * Ratoms * T_K)


# ---------------------------------------------------------------------------
# Load raw per-step data and fit each of the 10 sequences
# ---------------------------------------------------------------------------
raw = pd.read_excel(XLSX, sheet_name='Fit Lambdas', header=None, skiprows=39)
raw.columns = raw.iloc[0]
# The sheet has several duplicate "2σ" column headers (one per derived
# quantity); rename the one immediately following "3He measured (pccSTP)"
# for unambiguous access as the per-measurement uncertainty used to weight
# the lambda/n0 fit below.
_meas_idx = list(raw.columns).index('3He measured (pccSTP)')
raw.columns.values[_meas_idx + 1] = '3He measured 2sigma'
raw = raw.iloc[1:].reset_index(drop=True)
raw['Series ID'] = raw['Series ID'].ffill()
raw = raw.dropna(subset=['HeRefNo'])  # drop the blank rows separating sequences

sequences = []
for series_id, group in raw.groupby('Series ID', sort=True):
    t = group['Nominal (Heated) Time (seconds)'].astype(float).to_numpy()
    He = group['3He measured (pccSTP)'].astype(float).to_numpy()
    He_2sigma = group['3He measured 2sigma'].astype(float).to_numpy()
    He_sigma = He_2sigma / 2  # 2sigma -> 1sigma
    lam, n0, lam_sigma, n0_sigma = fit_n0_lambda(t, He, He_sigma)
    T_C = float(group['Temperature (C)'].iloc[0])
    sequences.append({
        'id': int(series_id), 'T_C': T_C, 'T_K': T_C + 273,
        'T_C_each': group['Temperature (C)'].astype(float).to_numpy(),
        'nominal_min': float(group['Nominal (Heated) Time (Minutes)'].iloc[0]),
        'cooling_min': float(group['Cooling Time (seconds)'].iloc[0]) / 60,
        't': t, 'He': He, 'He_2sigma': He_2sigma,
        'timestamps': group['Time (Pump out)'].to_numpy(),  # cross-check join key, see below
        'lam': lam, 'n0': n0, 'lam_sigma': lam_sigma, 'n0_sigma': n0_sigma,
    })
sequences.sort(key=lambda s: s['id'])

# ---------------------------------------------------------------------------
# 5x2 grid: one panel per sequence
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(5, 2, figsize=(9, 14))
for seq, ax in zip(sequences, axes.flat):
    cumt_hr = accumulate(seq['t']) / 3600
    cumHe = accumulate(seq['He'])
    longt_hr = np.linspace(0, cumt_hr[-1], 500)
    ax.plot(longt_hr, forward_permeate(longt_hr * 3600, seq['lam'], seq['n0']), color='red', linestyle='--', label='Permeation Fit')
    ax.scatter(cumt_hr, cumHe, color='black', zorder=5)
    ax.set_title(f"{seq['T_C']:.0f}°C, {seq['nominal_min']:.0f} min\n"
                 f"λ={seq['lam']:.2e} s⁻¹, n0={seq['n0']:.3f} pccSTP", fontsize=12)
fig.supxlabel('Cumulative Time (hours)')
fig.supylabel(r'$m_{cum}$ $^3$He (pccSTP)')
fig.suptitle('Win-06-01b Isothermal Step-Heat Permeation Rate Constant Fits')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PermeationStepFits_Grid.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# 2x2 grid: just the first 4 sequences (top two rows of the 5x2 grid above),
# as a smaller example figure for the GCA manuscript main text -- the full
# 10-sequence figure above is used in the dissertation instead. Same fits,
# same panel content, just fewer panels/smaller figure.
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(7, 6.5))
for seq, ax in zip(sequences[:4], axes.flat):
    cumt_hr = accumulate(seq['t']) / 3600
    cumHe = accumulate(seq['He'])
    longt_hr = np.linspace(0, cumt_hr[-1], 500)
    ax.plot(longt_hr, forward_permeate(longt_hr * 3600, seq['lam'], seq['n0']), color='red', linestyle='--', label='Permeation Fit')
    ax.scatter(cumt_hr, cumHe, color='black', zorder=5)
    ax.set_title(f"{seq['T_C']:.0f}°C, {seq['nominal_min']:.0f} min\n"
                 f"λ={seq['lam']:.2e} s⁻¹, n0={seq['n0']:.3f} pccSTP", fontsize=12)
fig.supxlabel('Cumulative Time (hours)')
fig.supylabel(r'$m_{cum}$ $^3$He (pccSTP)')
fig.suptitle('Win-06-01b Isothermal Step-Heat Permeation Rate Constant Fits\n(4 of 10 sequences)')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PermeationStepFits_Grid_Top4.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Superimposed fits by step duration, colored by temperature
# ---------------------------------------------------------------------------
cmap = mpl.cm.plasma
norm = mpl.colors.Normalize(vmin=TEMP_VMIN, vmax=TEMP_VMAX)

for nominal_min, outname in [(150, 'PermeationStepFits_150min_byTemp.pdf'),
                              (120, 'PermeationStepFits_120min_byTemp.pdf')]:
    group_seqs = [s for s in sequences if s['nominal_min'] == nominal_min]
    fig, ax = plt.subplots()
    for seq in sorted(group_seqs, key=lambda s: s['T_C']):
        color = cmap(norm(seq['T_C']))
        cumt = accumulate(seq['t'])
        cumHe = accumulate(seq['He'])
        longt = np.linspace(0, cumt[-1], 500)
        ax.plot(longt, forward_permeate(longt, seq['lam'], seq['n0']), color=color,
                label=f"{seq['T_C']:.0f}°C")
        ax.scatter(cumt, cumHe, color=color, zorder=5)
    ax.set_xlabel('Cumulative Time (s)')
    ax.set_ylabel('Cumulative ³He (pccSTP)')
    ax.set_title(f'Win-06-01b Isothermal Permeation Step Fits, {nominal_min:.0f}-Minute Steps')
    ax.legend(title='Temperature', fontsize=8)
    fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, label='Temperature (°C)')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)

# ---------------------------------------------------------------------------
# Arrhenius plot, built from these fits rather than the sheet's own lambda/K
# ---------------------------------------------------------------------------
x = np.array([1E4 / s['T_K'] for s in sequences])
K = np.array([lambda_to_K(s['lam'], s['T_K']) for s in sequences])
y = np.log(K)
yerr = np.array([2 * s['lam_sigma'] / s['lam'] for s in sequences])  # 2-sigma, propagated from the fit
step_min = np.array([s['nominal_min'] for s in sequences])

reg = scipy.stats.linregress(x, y)
slope, intercept, r2 = reg.slope, reg.intercept, reg.rvalue ** 2
# x = 1E4/T, so ln(K) = intercept + slope*x = intercept + (slope*1E4)/T;
# comparing to the Arrhenius form ln(K) = ln(A) - Ea/(R*T) gives
# Ea = -slope * Rcal * 1E4 (cal/mol), with the same linear scaling applied
# to slope's own standard error, reported here (like the rest of this
# chapter's regressions) as a 2 s.e. uncertainty.
Ea_cal_mol = -slope * Rcal * 1E4
Ea_cal_mol_2se = 2 * reg.stderr * Rcal * 1E4
print(f"Isothermal permeation Arrhenius regression: ln(K) = {intercept:.3f} + {slope:.3f}*x, "
      f"R^2 = {r2:.3f}, Ea = {Ea_cal_mol:.0f} +/- {abs(Ea_cal_mol_2se):.0f} (2 s.e.) cal/mol")
lam_all = np.array([s['lam'] for s in sequences])
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
with open(CACHE_PATH, 'w') as f:
    json.dump({
        'slope': slope, 'intercept': intercept, 'r2': r2,
        'slope_stderr': reg.stderr, 'n_points': len(x),
        'Ea_cal_mol': Ea_cal_mol, 'Ea_cal_mol_2se': abs(Ea_cal_mol_2se),
        'temperature_range_C': [min(s['T_C'] for s in sequences), max(s['T_C'] for s in sequences)],
        'lam_min': float(lam_all.min()), 'lam_max': float(lam_all.max()),
    }, f, indent=2)
print(f"Wrote {CACHE_PATH}")

fig, ax1 = plt.subplots(constrained_layout=True)
ax2 = ax1.twiny()

xline = np.array([x.min(), x.max()])
ax1.plot(xline, slope * xline + intercept, color='teal',
         label=f'Regression: ln(K) = {slope:.3f}x + {intercept:.3f}')

# Reference 3He permeability of fused silica: Swets et al. 1961 give the 4He
# permeability K; Jones 1954 gives the 3He/4He permeability ratio, so their
# product is the 3He permeability plotted here for comparison.
xref = np.linspace(x.min(), x.max(), 50)
Kref = np.array([swets('K', 1E4 / xt) * Jones(1E4 / xt) for xt in xref])
ax1.plot(xref, np.log(Kref), color='black', linestyle='--',
         label='3He Permeability (Swets et al. 1961; Jones 1954')

# Load the simulated fits (if the cache exists) up front, so the shared
# "Isothermal Step Duration" color scale can be widened to cover both the
# actual sequences' durations and the simulation grid's durations before
# either scatter is drawn.
sim_cache = os.path.join(FIG_DIR, 'data', 'goethite_thermal_sim_lambdas.csv')
sim = pd.read_csv(sim_cache) if os.path.exists(sim_cache) else None
if sim is None:
    print(f"Note: {sim_cache} not found -- run goethite_thermal_sims.py first to add "
          "the simulated-lambda overlay to AmpoulePermeability_Arrhenius.pdf.")

ax1.errorbar(x, y, yerr=yerr, fmt='none', ecolor='black', capsize=4, zorder=4)
cmap2 = mpl.cm.viridis
dur_min, dur_max = step_min.min(), step_min.max()
if sim is not None:
    dur_min = min(dur_min, sim['hold_min'].min())
    dur_max = max(dur_max, sim['hold_min'].max())
norm2 = mpl.colors.Normalize(vmin=dur_min, vmax=dur_max)
sc = ax1.scatter(x, y, color='teal', alpha = 0.7, edgecolor='black', linewidth=0.8, #c=step_min, cmap=cmap2, norm=norm2, edgecolor='black',
                  zorder=5, label='Experimentally Determined Apparent K')
#fig.colorbar(sc, ax=[ax1, ax2], label='Isothermal Step Duration (min)')

# Overlay: simulated lambda fits from goethite_thermal_sims.py's
# temperature/hold-duration finite-difference permeation grid, fit with the
# same (lambda, n0) model as the actual sequences above, colored by hold
# duration on the same scale as the actual data, for direct comparison.
x_ticked = x  # x-range used to place the top (Temperature) axis's ticks below
if sim is not None:
    x_sim = 1E4 / sim['T_K'].to_numpy()
    y_sim = np.log(lambda_to_K(sim['lam'].to_numpy(), sim['T_K'].to_numpy()))
    ax1.scatter(x_sim, y_sim, marker='^', color='goldenrod', alpha=0.7, #c=sim['hold_min'], cmap=cmap2, norm=norm2,
                edgecolor='black', linewidth=0.8, zorder=6,
                label='Simulated Apparent K with Cooling')
    x_ticked = np.concatenate([x, x_sim])  # sim grid spans a wider T range than the actual data

if sim is not None:
    # Tick the top (Temperature) axis at exactly the simulation grid's own
    # hold temperatures, rather than an arbitrary evenly-spaced set.
    tick_temps_C = np.sort(sim['T_C'].unique())
    ax2.set_xticks(1E4 / (tick_temps_C + 273))
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticklabels([f'{c:.0f}' for c in tick_temps_C])
else:
    ax2.set_xticks(np.linspace(x_ticked.min(), x_ticked.max(), 5))
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticklabels([f'{1E4 / xt - 273:.0f}' for xt in ax2.get_xticks()])
ax2.set_xlabel('Temperature (°C)')
ax1.set_xlabel(r'$10^4/T$ (K)')
ax1.set_ylabel(r'$\ln(K)$ (atoms sec$^{-1}$ cm$^{-1}$ atm$^{-1}$)')
ax1.set_title('Win-06-01b Apparent He Permeability\nDetermined with Sequential Isothermal Steps')
#ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)
ax1.legend(fontsize=8)
plt.sca(ax1)  # make_grid() grids whichever axes is current; twiny() left ax2 current
make_grid()
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'AmpoulePermeability_Arrhenius.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# SI tables: raw per-step isothermal dataset + per-sequence fit results.
#
# The grid plot above already shows this raw data and quotes each sequence's
# fitted lambda/n0 in its subplot title, but neither was ever available
# anywhere in the dissertation in citable, tabulated form. Both are written
# here as auto-generated LaTeX macros -- \ChTwoPermStepRawTable and
# \ChTwoPermStepFitTable, each expanding to a complete table environment --
# following the exact \newcommand pattern write_chapter2_macros.py already
# uses for scalar values (chapter2_derived_values.tex), so
# chapter2goethite_SI_body.tex can invoke them by name instead of anyone
# hand-copying numbers into a table.
#
# Macro-wrapping (rather than a plain \input of the table text) is
# necessary here, unlike chapter2_derived_values.tex: that file only
# defines preamble macros, safe to \input from any wrapper regardless of
# its own working directory, but these tables need to appear at a specific
# point deep inside the shared body file, whose own \input path resolution
# depends on which wrapper is compiling it. Defining them as macros in each
# wrapper's preamble (where the path back to this generated file is already
# handled, exactly as chapter2_derived_values.tex is) means the shared body
# can just invoke \ChTwoPermStepRawTable/\ChTwoPermStepFitTable by name, with no
# path resolution required at the point of use. (Verified separately that
# longtable/table environments compile correctly from inside a \newcommand
# body.)
# ---------------------------------------------------------------------------


def fmt_sci(x, sig=2):
    """Format x as '\\(m.mm\\!\\times\\!10^{e}\\)', matching the scientific-
    notation convention already used for uncertainties in this chapter's
    other SI data tables."""
    if x == 0:
        return r"\(0\)"
    exp = int(np.floor(np.log10(abs(x))))
    mant = x / 10 ** exp
    return rf"\({mant:.{sig - 1}f}\!\times\!10^{{{exp}}}\)"


def _unc_place(err, sig=2):
    """Decimal exponent of the last significant digit of `err` rounded to
    `sig` significant figures (e.g. 1.13e-4 -> -5)."""
    p = int(np.floor(np.log10(abs(err)))) - (sig - 1)
    # rounding can carry into a new digit (9.96e-5 -> 1.0e-4)
    r = round(err, -p)
    return int(np.floor(np.log10(abs(r)))) - (sig - 1)


def fmt_dec_unc(x, err, sig=2):
    """Value and 2-sigma as plain decimals, the uncertainty rounded to `sig`
    significant figures and the value to the same decimal place
    (2026-10-29 sig-fig pass), e.g. (0.019003, 1.13e-4) -> ('0.01900', '0.00011')."""
    d = max(0, -_unc_place(err, sig))
    return f"{x:.{d}f}", f"{err:.{d}f}"


def fmt_sci_unc(x, err, sig=2):
    """Value and 2-sigma in scientific notation, the uncertainty to `sig`
    significant figures and the value's mantissa to the same decimal place,
    e.g. (3.1e-5, 2.6e-6) -> ('3.10x10^-5', '2.6x10^-6')."""
    exp = int(np.floor(np.log10(abs(x))))
    nd = max(0, exp - _unc_place(err, sig))
    mant = x / 10 ** exp
    return rf"\({mant:.{nd}f}\!\times\!10^{{{exp}}}\)", fmt_sci(err, sig)


# --- Cross-check: every measurement in 'Fit Lambdas' should carry the same
# Temperature/step time/3He yield as the corresponding row of 'Raw Data and
# Corrections' (the master per-measurement sheet), matched by their shared
# 'Time (Pump out)' timestamp -- a unique key per measurement in the run.
# 2-sigma is deliberately not compared: 'Raw Data and Corrections' reports
# each measurement's own counting/sensitivity uncertainty, while 'Fit
# Lambdas' additionally propagates blank/calibration uncertainty into a
# larger 2-sigma, so the two are legitimately different, not a copy of each
# other. This is not itself used for the fit -- it only confirms 'Fit
# Lambdas' hasn't drifted from the master sheet before the raw-data table
# below is built from it.
master = pd.read_excel(XLSX, sheet_name='Raw Data and Corrections', header=1)
master = master.dropna(subset=['Time (Pump out)']).set_index('Time (Pump out)')
if master.index.duplicated().any():
    raise ValueError("'Raw Data and Corrections' has duplicate 'Time (Pump out)' "
                      "timestamps -- not a safe join key; fix the workbook before "
                      "regenerating tables.")

for seq in sequences:
    missing = [ts for ts in seq['timestamps'] if ts not in master.index]
    if missing:
        raise ValueError(
            f"Series {seq['id']}: timestamp(s) {missing} from 'Fit Lambdas' not found "
            "in 'Raw Data and Corrections' -- the two sheets are out of sync.")
    ref = master.loc[seq['timestamps']]
    ok = (np.allclose(ref['Temperature (C)'].astype(float), seq['T_C_each'], atol=0.02)
          and np.allclose(ref['Nominal (Heated) Time (seconds)'].astype(float), seq['t'], atol=0.02)
          and np.allclose(ref['3He measured (pccSTP)'].astype(float), seq['He'], rtol=1E-6))
    if not ok:
        raise ValueError(
            f"Series {seq['id']}: 'Fit Lambdas' values don't match 'Raw Data and "
            "Corrections' for this series -- the two sheets are out of sync.")
print(f"'Raw Data and Corrections' cross-check OK: {len(sequences)} series match "
      "'Fit Lambdas' exactly (Temperature, step time, 3He yield).")

# --- Raw-data table (\ChTwoPermStepRawTable) ---------------------------------
raw_rows = []
for seq in sequences:
    for T_i, He_i, He2s_i in zip(seq['T_C_each'], seq['He'], seq['He_2sigma']):
        He_s, He2s_s = fmt_dec_unc(He_i, He2s_i)
        raw_rows.append(
            f"{seq['id']} & {T_i:.2f} & {seq['nominal_min']:.0f} & "
            f"{seq['cooling_min']:.0f} & {He_s} & {He2s_s} \\\\")
    raw_rows.append(r"\midrule")
raw_rows = raw_rows[:-1]  # drop the trailing \midrule after the last series

raw_table = r"""\begin{footnotesize}
\begin{longtable}{c c c c c c}
\caption{Raw step-heat data (\uppercase{`}Fit Lambdas\uppercase{'} sheet, cross-checked against \uppercase{`}Raw Data and Corrections\uppercase{'}) for the 10 isothermal 3He permeation sequences used to determine the ampoule's apparent permeability (Fig.~\ref{fig:ch2-permeation-fits}, Fig.~\ref{fig:ch2-ampoule-permeability}). Series are separated by horizontal rules; within a series, steps are listed in the order measured.}\label{tab:ch2-permeation-isothermal-raw}\\
\toprule
Series & Temp & Nominal Time & Cooling Time & $^3$He measured & $\pm2\sigma$ \\
 & (\textdegree C) & (min) & (min) & (pccSTP) & \\
\midrule
\endfirsthead
\multicolumn{6}{l}{\textit{(continued)}} \\
\toprule
Series & Temp & Nominal Time & Cooling Time & $^3$He measured & $\pm2\sigma$ \\
 & (\textdegree C) & (min) & (min) & (pccSTP) & \\
\midrule
\endhead
\midrule
\multicolumn{6}{r}{\textit{continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
""" + "\n".join(raw_rows) + "\n\\end{longtable}\n\\end{footnotesize}"

# --- Fit-results table (\ChTwoPermStepFitTable) ------------------------------
fit_rows = []
for seq in sequences:
    lam_s, lam2s_s = fmt_sci_unc(seq['lam'], 2 * seq['lam_sigma'])
    n0_s, n02s_s = fmt_dec_unc(seq['n0'], 2 * seq['n0_sigma'])
    fit_rows.append(
        f"{seq['id']} & {seq['T_C']:.2f} & {seq['nominal_min']:.0f} & {len(seq['t'])} & "
        f"{lam_s} & {lam2s_s} & {n0_s} & {n02s_s} \\\\")

fit_table = r"""\begin{table}[htbp]
\centering
\footnotesize
\caption{Fitted $\lambda$ (permeation rate constant) and $n_0$ (residual helium at the start of the series) for each of the 10 isothermal sequences in Table~\ref{tab:ch2-permeation-isothermal-raw}, from the weighted non-linear least-squares fit of Eq.~\eqref{eq:incyield} (Chapter~\ref{ch:apparatus}) described in \S\ref{sec:ch2-si-permeation}. $n$ is the number of steps in the sequence. These are the same per-sequence fits plotted in Fig.~\ref{fig:ch2-permeation-fits} and used to build the Arrhenius regression in Fig.~\ref{fig:ch2-ampoule-permeability}.}\label{tab:ch2-permeation-isothermal-fits}
\begin{tabular}{c c c c c c c c}
\toprule
Series & Temp (\textdegree C) & Duration (min) & $n$ & $\lambda$ (s$^{-1}$) & $\pm2\sigma$ & $n_0$ (pccSTP) & $\pm2\sigma$ \\
\midrule
""" + "\n".join(fit_rows) + r"""
\bottomrule
\end{tabular}
\end{table}"""


def _check_newcommand_safe(tex):
    """\\newcommand bodies can't contain a literal '#'; none of these tables
    do, so this is just a defensive check, not a transform."""
    if '#' in tex:
        raise ValueError("Generated table contains a literal '#', which would "
                          "break inside \\newcommand{}{...} -- escape it first.")
    return tex


with open(TABLES_OUT_PATH, 'w') as f:
    f.write(
        "% =============================================================\n"
        "%  chapter2_permstep_isothermal_tables.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.\n"
        "%  Written by Figures/fig_permstep_isothermal_fits.py from\n"
        "%  Win0601bHT_data_and_reduction.xlsx ('Fit Lambdas' sheet for the raw data\n"
        "%  and the per-sequence lambda/n0 fits, cross-checked against 'Raw Data and\n"
        "%  Corrections' -- the workbook's master per-measurement sheet).\n"
        "%\n"
        "%  Regenerate after any change to either sheet:\n"
        "%    python3 Figures/fig_permstep_isothermal_fits.py\n"
        "%  (run_all_figures.py does this automatically, before write_chapter2_macros.py.)\n"
        "%\n"
        "%  \\input{} by chapter2goethite_SI.tex (standalone) and chapter2.tex\n"
        "%  (dissertation -- defined early enough for chapter2_SI.tex, input later,\n"
        "%  to use), same pattern as chapter2_derived_values.tex.\n"
        "%\n"
        "%  \\ChTwoPermStepRawTable : Table~\\ref{tab:ch2-permeation-isothermal-raw}, the raw\n"
        "%    per-step dataset for all 10 isothermal sequences.\n"
        "%  \\ChTwoPermStepFitTable : Table~\\ref{tab:ch2-permeation-isothermal-fits}, the fitted\n"
        "%    lambda/n0 (+/- 2 sigma) for each of those 10 sequences.\n"
        "% =============================================================\n"
        f"\\newcommand{{\\ChTwoPermStepRawTable}}{{{_check_newcommand_safe(raw_table)}}}\n\n"
        f"\\newcommand{{\\ChTwoPermStepFitTable}}{{{_check_newcommand_safe(fit_table)}}}\n"
    )
print(f"Wrote {TABLES_OUT_PATH}")
