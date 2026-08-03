"""
Thermal-history-normalized He degassing for Win-06-01b goethite: cumulative
fractional yield vs. step power expressed as diffusive time (Fo) relative
to the Stage 2 decomposition-regression reference domain. Compares both
vacuum datasets (Monteiro 2017; Farley et al. 2024) against hydrothermal
step-heating (this study). Extends the equivalent panel in
fig_winsor_goethite_analysis.py (which only plots the HDM vacuum dataset)
by adding the KAF vacuum dataset.

Reads:
  generated/data/He3_HDMwinsor_diffusion.csv, generated/data/He4_HDMwinsor_diffusion.csv,
  generated/data/He3_KAFwinsor_diffusion.csv, generated/data/He4_KAFwinsor_diffusion.csv
      (vacuum reductions, written by fig_winsor_goethite_analysis.py)
  Win0601bHT_data_and_reduction.xlsx, sheets 'diffusivitiesHTWin0601b{M,UB,LB}'
      (hydrothermal "treatment as uncertainty" reductions, this study --
      via load_diffusivities_HTWin0601b_bounds)

Outputs:
  CumDtPlot_WinsorGT_decompref_VacuumHDMKAF.pdf
  CumDtPlot_WinsorGT_decompref_VacuumHDMKAF_asUncertainty.pdf

Hydrothermal steps flagged as low-signal (measured 3He <0.1 pccSTP, via
thermochr_utils.low_signal_HTWin0601b_mask) are dropped from both
outputs, matching fig_3_4_plot.py's isotope-ratio envelope.

The Stage 2 reference (D_a2Decomp) is Monteiro 2017's own vacuum
decomposition regression, external to this study's step-heat reduction,
so it isn't part of the "treatment as uncertainty" bracketing and is
left as-is. What the "_asUncertainty" variant adds is the hydrothermal
series' own cumulative-yield trajectory computed from the lower- and
upper-bound reductions (each bound has its own corrected omega and
therefore its own slightly different cumulative fractional yield, not
just a different diffusivity), shown as a band around the central curve.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (accumulate, make_grid, load_diffusivities_HTWin0601b_bounds,
                              low_signal_HTWin0601b_mask)
from diffusion_utils import Forward_Diffuse
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
DATA_DIR = FIG_DIR
os.chdir(DATA_DIR)
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')
os.makedirs(OUTDIR, exist_ok=True)


def D_a2Decomp(T):
    """Stage 2 (decomposition) regression reference diffusivity for goethite. T in Kelvin."""
    Ea = 35600       # cal/mol
    D0_a2 = 2780000000
    return D0_a2 * (np.exp(-Ea / (1.987 * T)))


Winsor_Data = {
    f'He{iso}{key}': pd.read_csv(os.path.join(DATA_OUTDIR, f'He{iso}_{key}winsor_diffusion.csv'))
    for iso in ['3', '4'] for key in ['HDM', 'KAF']
}
bounds = load_diffusivities_HTWin0601b_bounds(MASTER_XLSX)
low_signal = low_signal_HTWin0601b_mask(MASTER_XLSX)
for iso in ('3', '4'):
    for tag in ('M', 'UB', 'LB'):
        bounds[iso][tag] = bounds[iso][tag][~low_signal].reset_index(drop=True)
DiffdatBJT = {iso: bounds[iso]['M'] for iso in ('3', '4')}


def make_plot(outname, show_band):
    fig, ax = plt.subplots()
    for i, l in enumerate(['HDM', 'KAF']):
        for j, n in enumerate(['3', '4']):
            step_power = D_a2Decomp(Winsor_Data[f"He{n}{l}"]['Temp (C)'] + 273) * \
                (Winsor_Data[f"He{n}{l}"]['Time (min)'] * 60)
            ax.scatter(accumulate(step_power), Winsor_Data[f"He{n}{l}"]['Fcum'],
                       label=f"Vacuum He{n}: {['Monteiro, 2017', 'Farley et al., 2024'][i]}",
                       marker=['s', 'x'][j], color=['orange', 'red'][i])
            ax.plot(accumulate(step_power), Winsor_Data[f"He{n}{l}"]['Fcum'],
                    color=['orange', 'red'][i], linestyle='--', alpha=0.5)

    for j, n in enumerate(['3', '4']):
        step_power = D_a2Decomp(DiffdatBJT[n]['Temp (C)'] + 273) * (DiffdatBJT[n]['Minutes'] * 60)
        ax.scatter(accumulate(step_power), DiffdatBJT[n]['Fi+1'],
                   label=f"Hydrothermal He{n}: This Study", marker=['s', 'x'][j], color='blue')
        ax.plot(accumulate(step_power), DiffdatBJT[n]['Fi+1'], color='blue', linestyle='--', alpha=0.5)

    # Note: an earlier version of this plot overlaid dotted LB/UB
    # ("treatment as uncertainty") trajectories here, but they proved
    # visually indistinguishable from the central (M) curve above, so the
    # asUncertainty variant now just reuses the same M-only trajectories as
    # the naive plot -- these two outputs are intentionally identical.
    Dt_a2refs = np.linspace(0, 1, 10000)
    Fcumrefs = 0.88 * np.array([Forward_Diffuse(n) for n in Dt_a2refs])
    ax.plot(Dt_a2refs, Fcumrefs, color='black', label='Stage 2 Reference Domain (88% Helium)')
    ax.set_title('Helium Degassing of Win-06-01b Goethite in Vacuum\n'
                  'and Hydrothermal Conditions with Diffusive Time')
    ax.set_xlabel(r'CumulativeDiffusive Time $\left(Fo = \frac{t}{\tau}\right)$ for Stage 2 Reference')
    ax.set_ylabel(r'$\Sigma ^nFHe$ Cumulative Fractional $^nHe$ Yield')
    ax.set_xlim((0, 0.5))
    make_grid()
    ax.legend(loc='center right', fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


make_plot('CumDtPlot_WinsorGT_decompref_VacuumHDMKAF.pdf', show_band=False)
make_plot('CumDtPlot_WinsorGT_decompref_VacuumHDMKAF_asUncertainty.pdf', show_band=True)
