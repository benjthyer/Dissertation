"""
Delta plot for Win-06-01b goethite: departure of apparent diffusivity
(ln(D/a^2)) from the Stage 1 regression reference, for vacuum (Monteiro
2017; Farley et al. 2024) and hydrothermal (this study) step-heats,
against cumulative fractional He yield. Extends the equivalent panel in
fig_winsor_goethite_analysis.py (which only plots the hydrothermal delta)
by adding both vacuum datasets and hydrothermal error bars.

Reads:
  generated/data/He3_HDMwinsor_diffusion.csv, generated/data/He4_HDMwinsor_diffusion.csv,
  generated/data/He3_KAFwinsor_diffusion.csv, generated/data/He4_KAFwinsor_diffusion.csv
      (vacuum reductions, written by fig_winsor_goethite_analysis.py)
  Win0601bHT_data_and_reduction.xlsx, sheets 'diffusivitiesHTWin0601b{M,UB,LB}'
      (hydrothermal "treatment as uncertainty" reductions, this study --
      via load_diffusivities_HTWin0601b_bounds)
  Figures/generated/data/stage1_regression_cache.json
      (Stage 1 reference line, derived and cached by prepare_regression_cache.py
      -- run that script first if this one complains it's missing)

Outputs:
  DeltasWinsorGTzoomin_VacuumHydrothermal.pdf
  DeltasWinsorGTzoomin_VacuumHydrothermal_asUncertainty.pdf

Hydrothermal steps flagged as low-signal (measured 3He <0.1 pccSTP, via
thermochr_utils.low_signal_HTWin0601b_mask) are dropped from both
outputs, matching fig_3_4_plot.py's isotope-ratio envelope.

The "_asUncertainty" variant plots the hydrothermal error bars as the
true asymmetric upper/lower bounds from the "treatment as uncertainty"
method instead of a single symmetric +/- term.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (make_grid, load_diffusivities_HTWin0601b_bounds,
                              asymmetric_yerr, load_stage1_cache, D_a2_from_fit,
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
stage1 = load_stage1_cache()
D_a2reg = D_a2_from_fit(stage1['M'])  # central Stage 1 reference, derived from data (see prepare_regression_cache.py)


def make_plot(outname, use_asymmetric):
    fig, ax = plt.subplots()
    ax.hlines(0, 0, 1, color='black', alpha=0.5)
    for i, l in enumerate(['KAF', 'HDM']):
        for j, n in enumerate(['4', '3']):
            refs = np.log(D_a2reg(Winsor_Data[f"He3{l}"]['Temp (C)'] + 273))
            Deltas = Winsor_Data[f"He{n}{l}"]['ln(D/a^2)'] - refs
            ax.plot(Winsor_Data[f"He3{l}"]['Fcum'], Deltas, color=['red', 'orange'][i],
                    linestyle='--', marker=['s', 'o'][j], alpha=0.5,
                    label=f"Vacuum He{n}: {['Farley et al., 2024', 'Monteiro, 2017'][i]}")
    for j, n in enumerate(['4', '3']):
        refs = np.log(D_a2reg(DiffdatBJT[n]['Temp (C)'] + 273))
        Deltas = DiffdatBJT[n]['ln(d/a^2)'] - refs
        yerr = asymmetric_yerr(bounds, n) if use_asymmetric else DiffdatBJT[n]['ln(d/a^2) 2 sigma']
        ax.errorbar(DiffdatBJT['3']['Fi+1'], Deltas, yerr=yerr,
                    marker=['s', 'o'][j], color='blue', markeredgecolor=['pink', 'green'][j],
                    ecolor=['pink', 'green'][j], linestyle='--', label=f'Hydrothermal He{n}: This Study',
                    capsize=5, alpha=[0.8, 0.7][j])

    # Stage 2 reference domain, for context (not currently plotted)
    Dt_a2refs = np.linspace(0, 1, 1000)
    Fcumrefs = 0.89 * np.array([Forward_Diffuse(n) for n in Dt_a2refs])

    ax.set_title('Delta Plot Winsor Goethite, Stage 1 Reference')
    ax.set_ylabel(r'$\Delta$ $\left(ln\left(\frac{D}{a^2}\right)_{measured} - ln\left(\frac{D}{a^2}\right)_{reference}\right)$')
    ax.set_xlabel(r'$\Sigma F^3He$ Cumulative Helium Fractional Yield')
    ax.set_xlim((0, 0.2))
    make_grid()
    ax.legend(loc='upper right')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


make_plot('DeltasWinsorGTzoomin_VacuumHydrothermal.pdf', use_asymmetric=False)
make_plot('DeltasWinsorGTzoomin_VacuumHydrothermal_asUncertainty.pdf', use_asymmetric=True)
