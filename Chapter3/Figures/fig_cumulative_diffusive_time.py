"""
Thermal-history-normalized He degassing compared across minerals: pyrite,
arsenopyrite, and galena (this chapter's sulfide step heats) vs. hematite
and goethite (vacuum and hydrothermal) MDD step-heats, plus zircon and
monazite (a phosphate), all from Chapter 1/2's mineral-retentivity
compilation. Step power is expressed as diffusive time (Fo) relative to a
common 1 um single-crystal hematite reference diffusivity, so spectra from
different minerals/experiments with different heating schedules become
directly comparable on one x-axis: a phase that needs a larger Fo dose to
reach a given cumulative fractional yield is more retentive than one that
reaches the same yield at a smaller dose.

This script started as an exact copy of Chapter2/Figures/fig_cumulative_
diffusive_time.py (same hematite/goethite comparison, used there to argue
for goethite's degassing behavior relative to hematite) with Chapter-3-
relative paths that didn't actually resolve to anything -- it was never
adapted after being copied in. It's rewritten here as a proper Chapter 3
figure: the hematite/goethite comparison is kept (for scale/context) and
extended with zircon and monazite (both already present as unused sheets
in the same compilation workbook) and this chapter's own pyrite,
arsenopyrite, and galena step heats.

Reads:
  data/MDD_Step_heat_compilation.xlsx
  - Sheets whose name contains 'GC' or 'MI' are hematite grains.
  - Sheets 'Zr1'..'Zr10' are zircon; 'Mz1'..'Mz8' are monazite (phosphate).
  - All remaining sheets except 'HT-Win-06-01bBJT' and OLD_SULFIDE_SHEETS
    (see below) are goethite, vacuum.
  - Sheet 'HT-Win-06-01bBJT' would be goethite, hydrothermal, but is a
    static snapshot that predates the "treatment as uncertainty" fix to
    the permeation-lag correction, so it's skipped in favor of
    recomputing that series live from Chapter 2's master workbook (below).
  - Sheets 'RustPy', 'LVCOPy230630', '112123LVCOPy', 'BigLvCOPy' (OLD_
    SULFIDE_SHEETS) are an earlier, frozen pyrite reduction from before
    this chapter's "treatment as uncertainty" pipeline (Chapter3/Tables/
    build_plotable_cache.py) existed. Skipped for the same reason as the
    goethite snapshot above, in favor of reading the live Reduced01_*.xlsx
    reductions directly (see _load_sulfide_step_history below).
  Chapter2/Tables/Win0601bHT_data_and_reduction.xlsx, sheets
    'diffusivitiesHTWin0601b{M,UB,LB}' (hydrothermal "treatment as
    uncertainty" reductions of Chapter 2's own Win-06-01b goethite
    experiment, via load_diffusivities_HTWin0601b_bounds). Read directly
    from Chapter 2's Tables/ rather than duplicated into Chapter 3 -- this
    one cross-chapter read is intentional (comparing THIS experiment, not
    a copy of it) and is the only exception to each chapter's Figures/
    otherwise being self-contained.
  Chapter3/Tables/Reduced01_*.xlsx, 'Diffusivities'/'Sheet2' sheet (this
    chapter's own pyrite/arsenopyrite/galena step heats -- see
    _load_sulfide_step_history's docstring for why these are read directly
    rather than via Tables/plotable_sulfides_cache.pkl).

Output:
  generated/Fo_Plot_hematite_ref_SulfideMineralComparison.pdf

Hydrothermal goethite steps flagged as low-signal (measured 3He <0.1
pccSTP, via thermochr_utils.low_signal_HTWin0601b_mask) are dropped,
matching Chapter 2's fig_3_4_plot.py isotope-ratio envelope.

Note on isotopes: every curve here is cumulative FRACTIONAL yield (a
dimensionless 0-1 quantity), so mixing 3He (all sulfides except
Rustenburg pyrite, which is radiogenic 4He measured by isotope dilution;
zircon, monazite, hematite, goethite-vacuum) and 4He (goethite-
hydrothermal, Rustenburg) on one axis is fine for a retentivity
comparison -- unlike an absolute-yield plot, no isotope-specific
normalization is needed for the fractional quantity itself.
"""
import os
import sys
import numpy as np
import pandas as pd
import openpyxl
import matplotlib as mpl
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (accumulate, make_grid, load_diffusivities_HTWin0601b_bounds,
                              low_signal_HTWin0601b_mask)
from diffusion_utils import Forward_Diffuse
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(FIG_DIR, 'data')
SULFIDE_TABLES_DIR = os.path.join(FIG_DIR, '..', 'Tables')
GOETHITE_HT_XLSX = os.path.join(FIG_DIR, '..', '..', 'Chapter2', 'Tables',
                                 'Win0601bHT_data_and_reduction.xlsx')
DATA_DIR = FIG_DIR
os.chdir(DATA_DIR)
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

# Superseded by the live Reduced01_*.xlsx reduction (see SULFIDE_GROUPS
# below) -- see module docstring.
OLD_SULFIDE_SHEETS = {'RustPy', 'LVCOPy230630', '112123LVCOPy', 'BigLvCOPy'}

# Steps flagged as known-bad measurements and excluded from every plot
# that shows them individually (fig_ch3_step_heat_regressions.py,
# fig_sulfide_arrhenius.py, fig_lambda_vs_diffusivity.py -- all three via
# Tables/build_plotable_cache.py's own MANUAL_STEP_EXCLUSIONS, applied
# when the plotable cache is built). This script reads Reduced01_*.xlsx
# directly rather than that cache (see _load_sulfide_step_history's
# docstring), so it needs its own copy of the same exclusion -- but unlike
# the other plots, a step here can't simply be dropped outright: this
# plot's x-axis is a running cumulative sum of diffusive time across the
# WHOLE step sequence, and the excluded steps' real elapsed time still
# contributed to that dose even though their yields aren't trusted.
# Dropping the rows outright would understate every later step's
# cumulative dose. Instead, _load_sulfide_step_history returns each row's
# Step number too, so make_plot() can accumulate dose over every step but
# only draw markers for the ones not in this set.
#   112123SalAspIrr (arsenopyrite): everything from step 135 onward --
#   the final 6-step high-temperature ramp tail (steps 135-140, ~435-497
#   degC, flagged as unreliable) followed immediately by step 141, a
#   60-second, 24 degC "step" whose yield jumps from 3.7% to 6.3% (not
#   physically possible via diffusion at room temperature -- an appended
#   measurement, not part of the real step-heat kinetics), and steps
#   142-147, a further ~24 hr of 400 degC holds that continue past that
#   jump. None of steps 135-147 were ever in the plotable cache (the
#   original hand-curated key already stopped at step 134); this script
#   is the only one that would otherwise show them, since it reads the
#   raw sheet in full.
#   RustenburgPyUncert (pyrite): step 90609, the last analytical step --
#   failed to reach its setpoint temperature and thermally drifted,
#   invalidating that step's diffusivity inversion (the He yield itself
#   is fine, so its dose contribution is still counted, same as above).
MANUAL_STEP_EXCLUSIONS = {
    'Reduced01_112123SalAspIrr.xlsx': set(range(135, 148)),
    'Reduced01_RustenburgPyUncert.xlsx': {90609},
}

# {group label: (color, marker, [(sample label, Reduced01 filename), ...])}
# Only pyrite, arsenopyrite, and galena are included here (not chalcopyrite
# or galena's chalcopyrite-reference-only delta-plot role from the
# regression figures) -- these three are the phases this comparison is for.
SULFIDE_GROUPS = {
    'Pyrite': ('hotpink', '+', [
        ('LVCOPy230630', 'Reduced01_LVCOPy230630.xlsx'),
        ('BigLVCOPy230707', 'Reduced01_BigLVCOPy230707.xlsx'),
        ('112123LVCOPyIrr', 'Reduced01_112123LVCOPyIrrOG.xlsx'),
        ('Rustenburg Pyrite', 'Reduced01_RustenburgPyUncert.xlsx'),
    ]),
    'Arsenopyrite': ('green', 's', [
        ('SalAspIrr', 'Reduced01_112123SalAspIrr.xlsx'),
    ]),
    #'Galena': ('silver', 'X', [
    #    ('GalTS230630', 'Reduced01_GalTS230630.xlsx'),
    #]),
}


def D_a2HemMicron(T):
    """Farley, 2018 hematite diffusivity for a 1 micron diffusion domain. T in Kelvin."""
    Ea = 171000  # J/mol
    D0_a2 = np.exp(-0.66) / ((1E-4) ** 2)
    return D0_a2 * (np.exp(-Ea / (8.314 * T)))


def _load_sulfide_step_history(xlsx_name):
    """Full (unfiltered), original-order Temp(C)/Seconds/cumulative-
    fractional-He-yield step history for a sulfide step-heat experiment,
    read directly from its Reduced01_*.xlsx 'Diffusivities' (or 'Sheet2')
    sheet -- NOT Tables/plotable_sulfides_cache.pkl, which deliberately
    excludes steps that don't meet the lambda*t>=4 "steady state"
    threshold used to bound diffusivity uncertainty (see Chapter3/Tables/
    build_plotable_cache.py). Those excluded steps are still real,
    correctly-timed measurements that evolved real cumulative yield --
    dropping them here would understate the diffusive dose/yield reached
    at a given point in the schedule, the same reason the hematite/
    goethite/zircon/monazite sheets below are read in full rather than
    filtered to some analogous "usable steps" subset.

    Returns (Temp_C, Seconds, Fim, Step) arrays, one entry per data row --
    Step included so callers can mask specific rows (e.g.
    MANUAL_STEP_EXCLUSIONS) after accumulating dose over the full
    sequence, rather than dropping them beforehand.
    """
    path = os.path.join(SULFIDE_TABLES_DIR, xlsx_name)
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb['Diffusivities'] if 'Diffusivities' in wb.sheetnames else wb['Sheet2']

    row1 = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
    row3 = [ws.cell(row=3, column=c).value for c in range(1, ws.max_column + 1)]
    step_col = row3.index('Step') + 1
    fim_col = row1.index('Fim') + 1
    temp_col = next(i + 1 for i, v in enumerate(row3) if isinstance(v, str) and v.strip().startswith('Temp'))
    secs_col = row3.index('Seconds') + 1

    steps, temps, secs, fims = [], [], [], []
    for r in range(4, ws.max_row + 1):
        st = ws.cell(row=r, column=step_col).value
        t = ws.cell(row=r, column=temp_col).value
        s = ws.cell(row=r, column=secs_col).value
        f = ws.cell(row=r, column=fim_col).value
        if (isinstance(st, (int, float)) and isinstance(t, (int, float))
                and isinstance(s, (int, float)) and isinstance(f, (int, float))):
            steps.append(st)
            temps.append(float(t))
            secs.append(float(s))
            fims.append(float(f))
    return np.array(steps), np.array(temps), np.array(secs), np.array(fims)


hematite_sheets = pd.read_excel(os.path.join(RAW_DATA_DIR, 'MDD_Step_heat_compilation.xlsx'), None)
bounds = load_diffusivities_HTWin0601b_bounds(GOETHITE_HT_XLSX)
low_signal = low_signal_HTWin0601b_mask(GOETHITE_HT_XLSX)
for iso in ('3', '4'):
    for tag in ('M', 'UB', 'LB'):
        bounds[iso][tag] = bounds[iso][tag][~low_signal].reset_index(drop=True)

Dt_a2refs = np.logspace(-10, 4, 10000)
Fcumrefs = np.array([Forward_Diffuse(n) for n in Dt_a2refs])


def make_plot(outname):
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.semilogx(Dt_a2refs, Fcumrefs, linestyle='--', color='Black', label='Hematite: 1 micron Domain')

    for label, sheet in hematite_sheets.items():
        kwargs = {'alpha': 0.5}
        if label == 'HT-Win-06-01bBJT' or label in OLD_SULFIDE_SHEETS:
            continue
        lamps = sheet['T(oC)'][:-1] < 1000
        step_power = D_a2HemMicron(sheet['T(oC)'][:-1][lamps].astype(float) + 273) * \
            (sheet['time (hrs)'][:-1][lamps].astype(float) * 3600)
        if label.startswith('Zr'):
            color = 'teal'
        elif label.startswith('Mz'):
            color = 'purple'
            kwargs['zorder'] = 200
            kwargs['alpha'] = 0.42
        elif any(tag in label for tag in ['GC', 'MI']):
            color = 'red'
        else:
            color = 'orange'
        ax.semilogx(accumulate(step_power), sheet['F3He'][:-1][lamps].astype(float),
                    marker='.', color=color, linestyle='--', **kwargs)

    # Goethite, hydrothermal (Chapter 2's Win-06-01b) -- recomputed live
    # from Chapter 2's master workbook central ("M") reduction instead of
    # the static compilation snapshot, so this stays in sync with the
    # "treatment as uncertainty" fix (see module docstring).
    df_m = bounds['3']['M']
    step_power_m = D_a2HemMicron(df_m['Temp (C)'] + 273) * (df_m['Minutes'] * 60)
    ax.semilogx(accumulate(step_power_m), df_m['Fi+1'],
                alpha=0.5, marker='o', color='blue', linestyle='--')

    # This chapter's own sulfide step heats, read live from Reduced01_*.xlsx.
    for group_label, (color, marker, samples) in SULFIDE_GROUPS.items():
        for sample, fname in samples:
            steps, temp_c, secs, fim = _load_sulfide_step_history(fname)
            step_power = D_a2HemMicron(temp_c + 273) * secs
            # Accumulate over every step (so later steps' dose isn't
            # understated), then drop the known-bad ones from what's
            # actually drawn -- see MANUAL_STEP_EXCLUSIONS above.
            cum_dose = accumulate(step_power)
            excluded = MANUAL_STEP_EXCLUSIONS.get(fname, set())
            keep = np.array([s not in excluded for s in steps])
            ax.semilogx(cum_dose[keep], fim[keep], alpha=0.6, marker=marker,
                        color=color, linestyle='--')

    legend_elements = [
        mpl.lines.Line2D([0], [0], marker='.', color='red', label='Hematite', markerfacecolor='red'),
        mpl.lines.Line2D([0], [0], marker='.', color='orange', label='Goethite, Vacuum', markerfacecolor='orange'),
        mpl.lines.Line2D([0], [0], marker='o', color='blue', label='Goethite, Hydrothermal', markerfacecolor='blue'),
        mpl.lines.Line2D([0], [0], marker='.', color='teal', label='Zircon', markerfacecolor='teal'),
        mpl.lines.Line2D([0], [0], marker='+', color='hotpink', label='Pyrite', markerfacecolor='hotpink'),
        mpl.lines.Line2D([0], [0], marker='s', color='green', label='Arsenopyrite', markerfacecolor='green'),
        #mpl.lines.Line2D([0], [0], marker='X', color='silver', label='Galena', markerfacecolor='silver'),
        mpl.lines.Line2D([0], [0], color='black', linestyle='--', label='1 $\\mu m$ Single-Crystal Hematite'),
        mpl.lines.Line2D([0], [0], marker='.', color='purple', label='Monazite (phosphate)', markerfacecolor='purple'),

    ]

    # 3-line split (was 2) -- at the larger Chapter-3 TITLE_SIZE (see
    # plot_style.py), the old 2nd line ("Hematite, Goethite, Zircon, and
    # Monazite with Diffusive Time") overran the axes width and collided
    # with the y-axis label.
    ax.set_title('Helium Degassing of Sulfides Compared to\n'
                  'Hematite, Goethite, Zircon,\n'
                  'and Monazite with Diffusive Time')
    ax.set_xlabel(r'Cumulative Diffusive Time $\left(\frac{t}{\tau}\right)$: 1 $\mu m$ Hematite reference')
    ax.set_ylabel(r'$\Sigma F_{He}$ Cumulative Fractional He Yield')
    ax.set_xlim((10 ** -10, 10 ** 4))
    make_grid()
    ax.legend(handles=legend_elements, fontsize=8, loc='upper left')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


make_plot('Fo_Plot_hematite_ref_SulfideMineralComparison.pdf')
