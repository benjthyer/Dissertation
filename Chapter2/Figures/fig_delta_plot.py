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

Each step is drawn spectrum-style, spanning in x from the cumulative
fractional 3He yield at the start of the step to that at the end of the
step (start = end of the previous step, 0 for the first; computed from
the full step series before any step is dropped, so dropped steps leave
gaps). Hydrothermal steps are boxes whose height is the step's
uncertainty range, with a line at the central value; vacuum steps (no
uncertainties) are flat segments at the step's value. Fine vertical
lines join the central values of contiguous steps. Interior gaps left
by excluded hydrothermal steps are bridged for display only: the first
half of each gap at the preceding step's central value, the second half
at the following step's, with no error box over the bridge.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (make_grid, load_diffusivities_HTWin0601b_bounds,
                              asymmetric_yerr, load_stage1_cache, D_a2_from_fit,
                              low_signal_HTWin0601b_mask, step_yield_edges,
                              step_yield_edges_HTWin0601b, draw_step_connectors,
                              bridge_interior_gaps)
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
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
# Start/end cumulative 3He yield of every hydrothermal step, from the full
# series (so a dropped step still advances the next step's start), then
# masked like everything else.
F_start_HT, F_end_HT = step_yield_edges_HTWin0601b(MASTER_XLSX)
F_start_HT, F_end_HT = F_start_HT[~low_signal], F_end_HT[~low_signal]
for iso in ('3', '4'):
    for tag in ('M', 'UB', 'LB'):
        bounds[iso][tag] = bounds[iso][tag][~low_signal].reset_index(drop=True)
DiffdatBJT = {iso: bounds[iso]['M'] for iso in ('3', '4')}
stage1 = load_stage1_cache()
D_a2reg = D_a2_from_fit(stage1['M'])  # central Stage 1 reference, derived from data (see prepare_regression_cache.py)


VAC_COLORS = {'KAF': 'red', 'HDM': 'orange'}
VAC_LABELS = {'KAF': 'Farley et al., 2024', 'HDM': 'Monteiro, 2017'}
VAC_STYLES = {'3': '-', '4': (0, (1.5, 1))}   # 3He solid, 4He dotted
HT_COLORS = {'3': 'blue', '4': 'green'}
LEGEND_FONTSIZE = 8.5   # pt; plot_style default is 11
LEGEND_Y = 3.0          # legend centre, in Delta units


def make_plot(outname, use_asymmetric):
    fig, ax = plt.subplots()
    ax.hlines(0, 0, 1, color='black', alpha=0.5)
    handles = []
    for l in ['KAF', 'HDM']:
        f_start, f_end = step_yield_edges(Winsor_Data[f"He3{l}"]['Fcum'])
        refs = np.log(D_a2reg(Winsor_Data[f"He3{l}"]['Temp (C)'] + 273))
        for n in ['4', '3']:
            Deltas = (Winsor_Data[f"He{n}{l}"]['ln(D/a^2)'] - refs).to_numpy()
            ax.hlines(Deltas, f_start, f_end, color=VAC_COLORS[l],
                      linestyle=VAC_STYLES[n], linewidth=2.2, alpha=0.8, zorder=2)
            draw_step_connectors(ax, f_start, f_end, Deltas, color=VAC_COLORS[l],
                                 alpha=0.8, zorder=2)
            handles.append(Line2D([], [], color=VAC_COLORS[l], linestyle=VAC_STYLES[n],
                                  linewidth=2.2, alpha=0.8,
                                  label=f"Vacuum He{n}: {VAC_LABELS[l]}"))
    for n in ['4', '3']:
        refs = np.asarray(np.log(D_a2reg(DiffdatBJT[n]['Temp (C)'] + 273)))
        Deltas = DiffdatBJT[n]['ln(d/a^2)'].to_numpy() - refs
        if use_asymmetric:
            lower, upper = asymmetric_yerr(bounds, n)
        else:
            lower = upper = DiffdatBJT[n]['ln(d/a^2) 2 sigma'].to_numpy()
        ax.bar(F_start_HT, lower + upper, width=F_end_HT - F_start_HT,
               bottom=Deltas - lower, align='edge', color=HT_COLORS[n], alpha=0.3,
               edgecolor=HT_COLORS[n], linewidth=0.6, zorder=3)
        # Central-value line; interior gaps left by excluded steps are bridged
        # for display only (no error box is drawn over the bridge).
        hs, he, hd = bridge_interior_gaps(F_start_HT, F_end_HT, Deltas)
        ax.hlines(hd, hs, he, color=HT_COLORS[n], linewidth=1.5, zorder=4)
        draw_step_connectors(ax, hs, he, hd, color=HT_COLORS[n], zorder=4)
        handles.append(Patch(facecolor=HT_COLORS[n], edgecolor=HT_COLORS[n], alpha=0.45,
                             label=f'Hydrothermal He{n}: This Study'))

    # Stage 2 reference domain, for context (not currently plotted)
    Dt_a2refs = np.linspace(0, 1, 1000)
    Fcumrefs = 0.89 * np.array([Forward_Diffuse(n) for n in Dt_a2refs])

    ax.set_title('Delta Plot Winsor Goethite, Stage 1 Reference')
    ax.set_ylabel(r'$\Delta$ $\left(ln\left(\frac{D}{a^2}\right)_{measured} - ln\left(\frac{D}{a^2}\right)_{reference}\right)$')
    ax.set_xlabel(r'$\Sigma F^3He$ Cumulative Helium Fractional Yield')
    ax.set_xlim((0, 0.2))
    make_grid()
    # Smaller legend tucked against the right edge in the empty band between
    # Delta = 0 (hydrothermal 3He) and ~6 (vacuum plateaus), so it covers no
    # data: anchored at x = right axes edge, y = LEGEND_Y (data units).
    ax.legend(handles=handles, loc='center right', fontsize=LEGEND_FONTSIZE,
              bbox_to_anchor=(1.0, LEGEND_Y), bbox_transform=ax.get_yaxis_transform(),
              handlelength=1.8, labelspacing=0.3, borderpad=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


make_plot('DeltasWinsorGTzoomin_VacuumHydrothermal.pdf', use_asymmetric=False)
make_plot('DeltasWinsorGTzoomin_VacuumHydrothermal_asUncertainty.pdf', use_asymmetric=True)
