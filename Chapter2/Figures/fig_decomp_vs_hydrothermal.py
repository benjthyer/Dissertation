"""
Win-06-01b goethite Arrhenius plot: apparent He diffusivities from vacuum
step-heating (Monteiro 2017; Farley et al. 2024) compared with hydrothermal
step-heating (this study), against the Stage 2 decomposition-regression
reference line. Refines the equivalent Arrhenius panel in
fig_winsor_goethite_analysis.py with a fixed y-range and a manually
reordered legend for publication.

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
  winsor_goethite_Diffusivities_Arrhenius.pdf
  winsor_goethite_Diffusivities_Arrhenius_asUncertainty.pdf
  winsor_goethite_Diffusivities_Arrhenius_Zoomin.pdf
  winsor_goethite_Diffusivities_Arrhenius_Zoomin_asUncertainty.pdf

Hydrothermal steps flagged as low-signal (measured 3He <0.1 pccSTP, via
thermochr_utils.low_signal_HTWin0601b_mask) are dropped from all four
outputs, matching fig_3_4_plot.py's isotope-ratio envelope.

The Zoomin "_asUncertainty" variant plots the hydrothermal data's error
bars as the true asymmetric upper/lower bounds from the "treatment as
uncertainty" method (explicit permeation-lag bracketing) instead of a
single symmetric +/- term (here, (UB-LB)/2, for visual comparison). In
the full-range plot, hydrothermal points are instead shown at half the
usual marker size with no error bars at all (for legibility at that
scale), so winsor_goethite_Diffusivities_Arrhenius.pdf and its
_asUncertainty companion are intentionally identical.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (load_diffusivities_HTWin0601b_bounds, asymmetric_yerr,
                              load_stage1_cache, low_signal_HTWin0601b_mask)
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
DATA_DIR = FIG_DIR
os.chdir(DATA_DIR)
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')
os.makedirs(OUTDIR, exist_ok=True)


def detect_segments(x):
    """
    Detects segments of monotonic behavior in x, including both ascending and descending breaks.

    Parameters:
        x (np.ndarray): The x data to analyze.

    Returns:
        list of np.ndarray: A list of indices for each monotonic segment, including breaks.
    """
    direction = np.sign(np.diff(x))  # Determine the direction of changes (+1, 0, -1)
    segment_breaks = np.where(direction[:-1] != direction[1:])[0] + 1

    # Include breaks at the start and end of x
    breaks = np.concatenate(([0], segment_breaks, [len(x)]))

    # Create segments, including breaks
    segments = [np.arange(breaks[i], breaks[i + 1]) for i in range(len(breaks) - 1)]
    return segments


Winsor_Data = {
    f'He{iso}{key}': pd.read_csv(os.path.join(DATA_OUTDIR, f'He{iso}_{key}winsor_diffusion.csv'))
    for iso in ['3', '4'] for key in ['HDM', 'KAF']
}
bounds = load_diffusivities_HTWin0601b_bounds(MASTER_XLSX)
low_signal = low_signal_HTWin0601b_mask(MASTER_XLSX)
for iso in ('3', '4'):
    for tag in ('M', 'UB', 'LB'):
        bounds[iso][tag] = bounds[iso][tag][~low_signal].reset_index(drop=True)
DiffdatBJT = {iso: bounds[iso]['M'] for iso in ('3', '4')}  # central values, same role as before
stage1 = load_stage1_cache()

Ctemps = np.array([75, 100, 150, 200, 250, 300, 350, 400, 450])


def plot_full(outname, use_asymmetric):
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twiny()

    xlim = [1E4 / (273 + 500), 1E4 / (273 + 70)]
    ax1.plot(xlim, np.log(2780000000 * np.exp(-np.array(xlim) * 3.5600 / 1.987)),
              label='Stage 2 Reference: Ea 149 kJ/mol', color='brown')

    for i, l in enumerate(['HDM', 'KAF']):
        for j, n in enumerate(['4', '3']):
            ax1.plot(Winsor_Data[f"He{n}{l}"]['10^4/T'], Winsor_Data[f"He{n}{l}"]['ln(D/a^2)'],
                      alpha=0.5, color=['orange', 'red'][i], linestyle=':')
            ax1.scatter(Winsor_Data[f"He{n}{l}"]['10^4/T'], Winsor_Data[f"He{n}{l}"]['ln(D/a^2)'],
                        label=f"Vacuum He{n}: {['Monteiro, 2017', 'Farley et al., 2024'][i]}",
                        marker=['s', 'x'][j], color=['orange', 'red'][i], alpha=0.5)

    # Hydrothermal points: plotted at half the usual marker size and with no
    # error bars (both the naive and asUncertainty variants -- the per-point
    # bracketing is visible in the Zoomin panel's error bars instead).
    for j, n in enumerate(['4', '3']):
        ax1.plot(DiffdatBJT[n]['10000/TK'], DiffdatBJT[n]['ln(d/a^2)'], linestyle='--', color='blue', alpha=0.5)
        ax1.plot(DiffdatBJT[n]['10000/TK'], DiffdatBJT[n]['ln(d/a^2)'],
                 marker=['s', 'x'][j], color='blue', alpha=0.5, linestyle='', markersize=3,
                 label=f'Hydrothermal He{n}: This Study')

    handles, labels = ax1.get_legend_handles_labels()
    order = [0, 6, 5, 2, 1, 4, 3]  # Reference line first, then vacuum/hydrothermal pairs
    handles = [handles[i] for i in order]
    labels = [labels[i] for i in order]
    ax1.set_xlim(xlim)
    ax1.set_ylim([-35, -9])
    ax2.set_xticks(1E4 / (Ctemps + 273))
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticklabels(Ctemps)
    ax2.set_xlabel('Temperature (C)')
    ax1.set_xlabel(r'$\frac{10000}{T^{ }(K)}$')
    ax1.set_ylabel(r'$ln\left(\frac{D}{a^2}\right) \left(sec^{-1}\right)$')
    ax1.legend(handles, labels, loc='lower left', fontsize=8)
    plt.title('Win-06-01b Goethite Apparent Helium Diffusivities')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


def plot_zoom(outname, use_asymmetric, fit):
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twiny()

    xlim = [1E4 / (273 + 275), 1E4 / (273 + 150)]
    print(fit.keys())
    Ea_kJmol = fit['Ea_cal_mol'] * 4.184 / 1000
    print(f"Stage 1 reference line: Ea = {Ea_kJmol:.1f} kJ/mol, intercept = {fit['intercept']:.2f}, with R^2 of {fit['r2']:.3f}")
    ax1.plot(xlim, (fit['slope'] * np.array(xlim)) + fit['intercept'],
             label=f"Stage 1 Reference: Ea {Ea_kJmol:.0f} kJ/mol", color='green', alpha=0.5)

    for i, l in enumerate(['HDM', 'KAF']):
        for j, n in enumerate(['4', '3']):
            ax1.plot(Winsor_Data[f"He{n}{l}"]['10^4/T'], Winsor_Data[f"He{n}{l}"]['ln(D/a^2)'],
                      alpha=0.5, color=['orange', 'red'][i], linestyle=':')
            ax1.scatter(Winsor_Data[f"He{n}{l}"]['10^4/T'], Winsor_Data[f"He{n}{l}"]['ln(D/a^2)'],
                        label=f"Vacuum He{n}: {['Monteiro, 2017', 'Farley et al., 2024'][i]}",
                        marker=['s', 'x'][j], color=['orange', 'red'][i], alpha=0.5)

    for j, n in enumerate(['4', '3']):
        yerr = asymmetric_yerr(bounds, n) if use_asymmetric else DiffdatBJT[n]['ln(d/a^2) 2 sigma']
        ax1.plot(DiffdatBJT[n]['10000/TK'], DiffdatBJT[n]['ln(d/a^2)'], linestyle='--', color='blue', alpha=0.5)
        ax1.errorbar(DiffdatBJT[n]['10000/TK'], DiffdatBJT[n]['ln(d/a^2)'],
                    yerr=yerr, markeredgecolor=['pink', 'green'][j], ecolor=['pink', 'green'][j], capsize=5,
                    marker=['s', 'o'][j], color='blue', alpha=0.5, label=f'Hydrothermal He{n}: This Study', linestyle='')

    handles, labels = ax1.get_legend_handles_labels()
    order = [0, 6, 5, 2, 1, 4, 3]  # Reference line first, then vacuum/hydrothermal pairs
    handles = [handles[i] for i in order]
    labels = [labels[i] for i in order]
    ax1.set_xlim(xlim)
    ax1.set_ylim([-32, -17])
    ax2.set_xticks(1E4 / (Ctemps + 273))
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticklabels(Ctemps)
    ax2.set_xlabel('Temperature (C)')
    ax1.set_xlabel(r'$\frac{10000}{T^{ }(K)}$')
    ax1.set_ylabel(r'$ln\left(\frac{D}{a^2}\right) \left(sec^{-1}\right)$')
    ax1.legend(handles, labels, loc='lower left', fontsize=8)
    plt.title('Win-06-01b Goethite Apparent Helium Diffusivities')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


plot_full('winsor_goethite_Diffusivities_Arrhenius.pdf', use_asymmetric=False)
plot_full('winsor_goethite_Diffusivities_Arrhenius_asUncertainty.pdf', use_asymmetric=True)

plot_zoom('winsor_goethite_Diffusivities_Arrhenius_Zoomin.pdf', use_asymmetric=False, fit=stage1['M'])
plot_zoom('winsor_goethite_Diffusivities_Arrhenius_Zoomin_asUncertainty.pdf', use_asymmetric=True, fit=stage1['M'])
