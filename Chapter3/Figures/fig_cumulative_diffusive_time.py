"""
Thermal-history-normalized He degassing compared across minerals: hematite
MDD step-heats (multiple grains) vs. Winsor-06-01b goethite (hydrothermal).
Step power is expressed as diffusive time (Fo) relative to the Stage 2
goethite decomposition-regression reference domain, so spectra from
different minerals/experiments become directly comparable on one x-axis.

Reads:
  data/MDD_Step_heat_compilation.xlsx
  - Sheets whose name contains 'GC' or 'MI' are hematite grains.
  - All other sheets (except 'HT-Win-06-01bBJT') are goethite, vacuum.
  - Sheet 'HT-Win-06-01bBJT' would be goethite, hydrothermal (this study),
    but is a static snapshot that predates the "treatment as uncertainty"
    fix to the permeation-lag correction, so it's skipped here in favor of
    recomputing that one series live from the master workbook (see below).
    Each remaining sheet needs columns: 'T(oC)', 'time (hrs)', 'F3He'.
  Win0601bHT_data_and_reduction.xlsx, sheets 'diffusivitiesHTWin0601b{M,UB,LB}'
      (hydrothermal "treatment as uncertainty" reductions, this study --
      via load_diffusivities_HTWin0601b_bounds)

Outputs:
  Fo_Plot_hematite_ref_HematiteGoethite.pdf
  Fo_Plot_hematite_ref_HematiteGoethite_asUncertainty.pdf

Hydrothermal steps flagged as low-signal (measured 3He <0.1 pccSTP, via
thermochr_utils.low_signal_HTWin0601b_mask) are dropped from both
outputs, matching fig_3_4_plot.py's isotope-ratio envelope.
"""
import os
import sys
import numpy as np
import pandas as pd
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
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
DATA_DIR = FIG_DIR
os.chdir(DATA_DIR)
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)


def D_a2HemMicron(T):
    """Farley, 2018 hematite diffusivity for a 1 micron diffusion domain. T in Kelvin."""
    Ea = 171000  # J/mol
    D0_a2 = np.exp(-0.66) / ((1E-4) ** 2)
    return D0_a2 * (np.exp(-Ea / (8.314 * T)))


def D_a2Decomp(T):
    """Stage 2 (decomposition) regression reference diffusivity for goethite. T in Kelvin."""
    Ea = 35600       # cal/mol
    D0_a2 = 2780000000
    return D0_a2 * (np.exp(-Ea / (1.987 * T)))


hematite_sheets = pd.read_excel(os.path.join(RAW_DATA_DIR, 'MDD_Step_heat_compilation.xlsx'), None)
bounds = load_diffusivities_HTWin0601b_bounds(MASTER_XLSX)
low_signal = low_signal_HTWin0601b_mask(MASTER_XLSX)
for iso in ('3', '4'):
    for tag in ('M', 'UB', 'LB'):
        bounds[iso][tag] = bounds[iso][tag][~low_signal].reset_index(drop=True)

Dt_a2refs = np.logspace(-10, 4, 10000)
Fcumrefs = np.array([Forward_Diffuse(n) for n in Dt_a2refs])


def make_plot(outname, show_band):
    fig, ax = plt.subplots()
    ax.semilogx(Dt_a2refs, Fcumrefs, linestyle='--', color='Black', label='Hematite: 1 micron Domain')

    for label, sheet in hematite_sheets.items():
        if label == 'HT-Win-06-01bBJT':
            continue  # plotted separately below (goethite, hydrothermal), from the live master workbook
        if 'Mz' in label:
            continue  # skip Monazites
        if 'Zr' in label:
            continue  # skip Zircons
        if 'Py' in label:
            continue  # skip Pyrites
        lamps = sheet['T(oC)'][:-1] < 1000
        step_power = D_a2HemMicron(sheet['T(oC)'][:-1][lamps].astype(float) + 273) * \
            (sheet['time (hrs)'][:-1][lamps].astype(float) * 3600)
        color = 'red' if any(tag in label for tag in ['GC', 'MI']) else 'orange'
        ax.semilogx(accumulate(step_power), sheet['F3He'][:-1][lamps].astype(float),
                    alpha=0.5, marker='.', color=color, linestyle='--')

    # Goethite, hydrothermal (this study) -- recomputed live from the master
    # workbook's central ("M") reduction instead of the static compilation
    # snapshot, so this stays in sync with the "treatment as uncertainty" fix.
    df_m = bounds['3']['M']
    step_power_m = D_a2HemMicron(df_m['Temp (C)'] + 273) * (df_m['Minutes'] * 60)
    ax.semilogx(accumulate(step_power_m), df_m['Fi+1'],
                alpha=0.5, marker='o', color='blue', linestyle='--')

    # Note: an earlier version of this plot overlaid dotted LB/UB
    # ("treatment as uncertainty") trajectories here, but they proved
    # visually indistinguishable from the central (M) curve above, so the
    # asUncertainty variant now just reuses the same M-only reference line
    # as the naive plot -- these two outputs are intentionally identical.
    legend_elements = [
        mpl.lines.Line2D([0], [0], marker='.', color='red', label='Hematite', markerfacecolor='red'),
        mpl.lines.Line2D([0], [0], marker='.', color='orange', label='Goethite, Vacuum', markerfacecolor='orange'),
        mpl.lines.Line2D([0], [0], marker='o', color='blue', label='Goethite, Hydrothermal', markerfacecolor='blue'),
        mpl.lines.Line2D([0], [0], color='black', linestyle='--', label='1 $\mu m$ Single-Crystal Hematite'),
    ]

    ax.set_title('Helium Degassing of Polycrystalline\n'
                  'Hematite and Goethite with Diffusive Time')
    ax.set_xlabel(r'Cumulative Diffusive Time $\left(\frac{t}{\tau}\right)$: 1 $\mu m$ Hematite reference')
    ax.set_ylabel(r'$\Sigma F^3He$ Cumulative Fractional $^3He$ Yield')
    ax.set_xlim((10 ** -10, 10 ** 4))
    make_grid()
    ax.legend(handles=legend_elements, fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


make_plot('Fo_Plot_hematite_ref_HematiteGoethite.pdf', show_band=False)
make_plot('Fo_Plot_hematite_ref_HematiteGoethite_asUncertainty.pdf', show_band=True)
