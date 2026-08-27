"""
EXPERIMENTAL variant of fig_naive_isothermal_fits.py: fits the n0/lambda
exponential model to only the FIRST TWO measurements of each of the 10
isothermal sequences (instead of all steps), to see whether an early
2-point fit still predicts the rest of the sequence well.

Everything else -- data loading, the forward_permeate1 fit model, the tube
geometry / lambda->K conversion, and the Arrhenius regression -- is
unchanged from fig_naive_isothermal_fits.py. See that script's docstring
for the full data-provenance notes.

Note on fitting exactly 2 points to a 2-parameter (lambda, n0) model: this
is an exactly-determined (0 degrees-of-freedom) fit, so the residual is
identically zero and curve_fit's reported parameter uncertainties are
meaningless (typically nan) -- there's no independent data left to assess
goodness of fit. The only real check is visual: does the curve extrapolated
from just those first two points track the remaining (unused) measurements
in the grid plot below.

This is an exploratory/diagnostic script, not part of the dissertation
build: it deliberately writes to its own output filenames and its own
cache file, and does NOT touch chapter2_naive_isothermal_tables.tex or
naive_lambda_arrhenius_cache.json (the real per-step table and Arrhenius
cache cited in the dissertation text), so it can be run freely without
affecting any citable numbers.

Outputs (all suffixed _First2 / _first2 to keep them separate from the
real figures):
  NaiveIsothermalFits_Grid_First2.pdf          - one panel per sequence (5x2);
                                                  black = all measured points,
                                                  red open circles = the two
                                                  points actually used for the
                                                  fit, dashed line = fit
                                                  extrapolated across the full
                                                  sequence.
  NaiveIsothermalFits_150min_byTemp_First2.pdf
  NaiveIsothermalFits_120min_byTemp_First2.pdf
  NaiveLambda_Arrhenius_First2.pdf
  generated/data/naive_lambda_arrhenius_cache_first2.json
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
CACHE_PATH = os.path.join(FIG_DIR, 'generated', 'data', 'naive_lambda_arrhenius_cache_first2.json')

TEMP_VMIN, TEMP_VMAX = 90, 110  # shared color scale between the two by-temperature plots
N_FIT_POINTS = 2  # only the first N_FIT_POINTS measurements of each sequence are fit


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
ID_cm = 0.052
OD_cm = 0.081
G = 2 / (np.log(OD_cm / ID_cm) * (ID_cm / 2) ** 2)
def lambda_to_K(lam, T_K):
    return lam / (G * Ratoms * T_K)


# ---------------------------------------------------------------------------
# Load raw per-step data and fit each of the 10 sequences, using only the
# first N_FIT_POINTS measurements of each for the fit itself.
# ---------------------------------------------------------------------------
raw = pd.read_excel(XLSX, sheet_name='Fit Lambdas', header=None, skiprows=39)
raw.columns = raw.iloc[0]
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

    if len(t) < N_FIT_POINTS:
        raise ValueError(f"Series {int(series_id)} has only {len(t)} measurements, "
                          f"fewer than N_FIT_POINTS={N_FIT_POINTS}.")
    lam, n0, lam_sigma, n0_sigma = fit_n0_lambda(t[:N_FIT_POINTS], He[:N_FIT_POINTS],
                                                  He_sigma[:N_FIT_POINTS])
    T_C = float(group['Temperature (C)'].iloc[0])
    sequences.append({
        'id': int(series_id), 'T_C': T_C, 'T_K': T_C + 273,
        'nominal_min': float(group['Nominal (Heated) Time (Minutes)'].iloc[0]),
        't': t, 'He': He, 'He_2sigma': He_2sigma,  # full sequence, for plotting
        'lam': lam, 'n0': n0, 'lam_sigma': lam_sigma, 'n0_sigma': n0_sigma,
    })
sequences.sort(key=lambda s: s['id'])

# ---------------------------------------------------------------------------
# 5x2 grid: one panel per sequence. All measured points are shown in black;
# the points actually used for the fit are ringed in red; the fit curve
# (extrapolated from just those first N_FIT_POINTS points) is the dashed
# red line, so it's visually obvious whether it still tracks the rest of
# the sequence.
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(5, 2, figsize=(9, 14))
for seq, ax in zip(sequences, axes.flat):
    cumt_hr = accumulate(seq['t']) / 3600
    cumHe = accumulate(seq['He'])
    longt_hr = np.linspace(0, cumt_hr[-1], 500)
    ax.plot(longt_hr, forward_permeate(longt_hr * 3600, seq['lam'], seq['n0']), color='red',
            linestyle='--', label=f'Fit (first {N_FIT_POINTS} pts)')
    ax.scatter(cumt_hr, cumHe, color='black', zorder=5, label='All measurements')
    ax.scatter(cumt_hr[:N_FIT_POINTS], cumHe[:N_FIT_POINTS], facecolors='none',
               edgecolors='red', linewidth=1.5, s=80, zorder=6, label='Used for fit')
    ax.set_title(f"{seq['T_C']:.0f}°C, {seq['nominal_min']:.0f} min\n"
                 f"λ={seq['lam']:.2e} s⁻¹, n0={seq['n0']:.3f} pccSTP", fontsize=12)
axes.flat[0].legend(fontsize=7, loc='lower right')
fig.supxlabel('Cumulative Time (hours)')
fig.supylabel(r'$m_{cum}$ $^3$He (pccSTP)')
fig.suptitle(f'Win-06-01b Isothermal Step-Heat Fits Using Only First {N_FIT_POINTS} Measurements')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'NaiveIsothermalFits_Grid_First2.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Superimposed fits by step duration, colored by temperature
# ---------------------------------------------------------------------------
cmap = mpl.cm.plasma
norm = mpl.colors.Normalize(vmin=TEMP_VMIN, vmax=TEMP_VMAX)

for nominal_min, outname in [(150, 'NaiveIsothermalFits_150min_byTemp_First2.pdf'),
                              (120, 'NaiveIsothermalFits_120min_byTemp_First2.pdf')]:
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
        ax.scatter(cumt[:N_FIT_POINTS], cumHe[:N_FIT_POINTS], facecolors='none',
                   edgecolors=color, linewidth=1.5, s=80, zorder=6)
    ax.set_xlabel('Cumulative Time (s)')
    ax.set_ylabel('Cumulative ³He (pccSTP)')
    ax.set_title(f'Win-06-01b Isothermal Fits (First {N_FIT_POINTS} Pts), {nominal_min:.0f}-Minute Steps')
    ax.legend(title='Temperature', fontsize=8)
    fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, label='Temperature (°C)')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)

# ---------------------------------------------------------------------------
# Arrhenius plot, built from these first-N_FIT_POINTS-only fits
# ---------------------------------------------------------------------------
x = np.array([1E4 / s['T_K'] for s in sequences])
K = np.array([lambda_to_K(s['lam'], s['T_K']) for s in sequences])
y = np.log(K)
yerr = np.array([2 * s['lam_sigma'] / s['lam'] for s in sequences])  # 2-sigma, propagated from the fit
step_min = np.array([s['nominal_min'] for s in sequences])

reg = scipy.stats.linregress(x, y)
slope, intercept, r2 = reg.slope, reg.intercept, reg.rvalue ** 2
Ea_cal_mol = -slope * Rcal * 1E4
Ea_cal_mol_2se = 2 * reg.stderr * Rcal * 1E4
print(f"[First-{N_FIT_POINTS}-only] Naive isothermal Arrhenius regression: "
      f"ln(K) = {intercept:.3f} + {slope:.3f}*x, R^2 = {r2:.3f}, "
      f"Ea = {Ea_cal_mol:.0f} +/- {abs(Ea_cal_mol_2se):.0f} (2 s.e.) cal/mol")
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
with open(CACHE_PATH, 'w') as f:
    json.dump({
        'n_fit_points': N_FIT_POINTS,
        'slope': slope, 'intercept': intercept, 'r2': r2,
        'slope_stderr': reg.stderr, 'n_points': len(x),
        'Ea_cal_mol': Ea_cal_mol, 'Ea_cal_mol_2se': abs(Ea_cal_mol_2se),
        'temperature_range_C': [min(s['T_C'] for s in sequences), max(s['T_C'] for s in sequences)],
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

ax1.errorbar(x, y, yerr=yerr, fmt='none', ecolor='black', capsize=4, zorder=4)
sc = ax1.scatter(x, y, color='teal', alpha=0.7, edgecolor='black', linewidth=0.8,
                  zorder=5, label=f'Apparent K, First {N_FIT_POINTS} Pts Only')

ax2.set_xticks(np.linspace(x.min(), x.max(), 5))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels([f'{1E4 / xt - 273:.0f}' for xt in ax2.get_xticks()])
ax2.set_xlabel('Temperature (°C)')
ax1.set_xlabel(r'$10^4/T$ (K)')
ax1.set_ylabel(r'$\ln(K)$ (atoms sec$^{-1}$ cm$^{-1}$ atm$^{-1}$)')
ax1.set_title(f'Win-06-01b Apparent He Permeability\nFit Using Only First {N_FIT_POINTS} Measurements per Sequence')
ax1.legend(fontsize=8)
plt.sca(ax1)  # make_grid() grids whichever axes is current; twiny() left ax2 current
make_grid()
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'NaiveLambda_Arrhenius_First2.pdf'), dpi=300)
plt.close(fig)
