"""
Bulk-normalized 4He/3He spectra for Win-06-01b goethite: hydrothermal
step-heating (this study) compared with both vacuum datasets (Monteiro
2017; Farley et al. 2024) against cumulative fractional 3He yield.
Extends the equivalent panel in fig_winsor_goethite_analysis.py (which
only plots the HDM vacuum dataset) by adding the KAF vacuum dataset.
Recomputes the vacuum diffusivity reductions independently (re-writing
He{3,4}_{HDM,KAF}winsor_diffusion.csv, matching the output of
fig_winsor_goethite_analysis.py) so this script can run standalone.

Each step is drawn spectrum-style, spanning in x from the cumulative
fractional 3He yield at the start of the step to that at the end of the
step (start = end of the previous step, 0 for the first; computed from
the full step series before any step is dropped, so dropped steps leave
gaps). Vacuum steps (no uncertainties) are flat segments at the step's
ratio; fine vertical lines join the central values of contiguous steps
(not across gaps). The x axis changes scale at Sigma F3He = 0.2 (marked
with a double slash): 0-0.2 fills the left two-thirds, 0.2-1 the right
third. Hydrothermal steps are drawn at the central (M) ratio only (the
LB-UB error boxes were removed at Ken's request); interior gaps
left by excluded steps are bridged for display, the first half of each
gap at the preceding step's value and the second half at the following
step's. Values are read directly from the master
workbook's 'DistilledBoundingMethod' sheet (formerly named
'DistilledUncertaintyTreatment'; its own bulk-normalized 4/3He LB/M/UB
columns, and its Sigma 3He column divided by that column's 'Total' row
for the cumulative yields -- the sheet's own 'F 3He' column holds each
step's *starting* yield), rather than recomputed from the per-isotope
diffusivitiesHTWin0601b{M,UB,LB} sheets. Steps are excluded if either: the sheet has no permeation-lag
bound yet (too little cumulative signal to bracket -- shown as '--' in
the workbook, true only for the earliest steps); or the measured 3He
signal for that step is below 0.1 pccSTP (too low-signal for a reliable
ratio -- these are the noisy/spiky points).

Reads:
  Win0601bHT_data_and_reduction.xlsx, sheet 'DistilledBoundingMethod'
      (hydrothermal "treatment as uncertainty" bulk-normalized ratio
      bounds and cumulative fractional 3He yield, this study)
  data/HM_Win_06_01B.csv            (vacuum, Monteiro 2017)
  data/Winsor_waterKAF_BJT.csv      (vacuum, Farley et al. 2024)

Outputs:
  Comparative_Ratios_Dtplot_WinsorGT_VacuumHDMKAF.pdf
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (diffusion_reduction, accumulate, make_grid, low_signal_HTWin0601b_mask,
                              step_yield_edges, step_yield_edges_HTWin0601b,
                              draw_step_connectors, bridge_interior_gaps)
from matplotlib.lines import Line2D
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(FIG_DIR, 'data')
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
DATA_DIR = FIG_DIR
os.chdir(DATA_DIR)
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(DATA_OUTDIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Vacuum reductions (HDM = Monteiro 2017, KAF = Farley et al. 2024)
# ---------------------------------------------------------------------------
Diffdat = pd.read_csv(os.path.join(RAW_DATA_DIR, 'HM_Win_06_01B.csv'))
TempKelvin = np.array(Diffdat['Temp (C)']) + 273
TimeSeconds = np.array(Diffdat['Time (h)']) * 3600

Winsor_Data = {}
for i, name in enumerate(['3HeCPS', '4HeCPS']):
    iso = ['3', '4'][i]
    Winsor_Data[f'He{iso}HDM'] = diffusion_reduction(
        np.array(Diffdat[name]).astype(float), TimeSeconds=TimeSeconds,
        TempKelvin=TempKelvin, newDiffName=os.path.join(DATA_OUTDIR, f'He{iso}_HDMwinsor_diffusion.csv'))
    plt.close()

Diffdat1 = pd.read_csv(os.path.join(RAW_DATA_DIR, 'Winsor_waterKAF_BJT.csv'), skiprows=1)[:30]
TempKelvin = np.array(Diffdat1['Temp (C)']) + 273
TimeSeconds = np.array(Diffdat1['Time (h)']) * 3600
for i, name in enumerate(['3He PCC', '4He NCC']):
    iso = ['3', '4'][i]
    Winsor_Data[f'He{iso}KAF'] = diffusion_reduction(
        np.array(Diffdat1[name]).astype(float), TimeSeconds=TimeSeconds,
        TempKelvin=TempKelvin, newDiffName=os.path.join(DATA_OUTDIR, f'He{iso}_KAFwinsor_diffusion.csv'))
    plt.close()

# ---------------------------------------------------------------------------
# Hydrothermal 4He/3He ratios, bulk-normalized -- read directly from the
# DistilledBoundingMethod sheet's own LB/M/UB columns (by header name), with
# each step's start/end cumulative fractional 3He yield (see module docstring).
# ---------------------------------------------------------------------------
distilled = pd.read_excel(MASTER_XLSX, sheet_name='DistilledBoundingMethod', header=0)
# Drop the trailing 'Total' summary row (its Temp cell is text, not a number).
distilled = distilled[pd.to_numeric(distilled.iloc[:, 0], errors='coerce').notna()]

F_start_HT, F_end_HT = step_yield_edges_HTWin0601b(MASTER_XLSX)
Rbulk_lb = pd.to_numeric(distilled['4/3 HeLB / 4/3 bulk'], errors='coerce').to_numpy()
Rbulk_m = pd.to_numeric(distilled['4/3 Hem / 4/3 bulk'], errors='coerce').to_numpy()
Rbulk_ub = pd.to_numeric(distilled['4/3HeUB / 4/3 bulk'], errors='coerce').to_numpy()
# Sanity check: the sheet's own 'F 3He' column is each step's starting yield.
_F_sheet = pd.to_numeric(distilled['F 3He'], errors='coerce').to_numpy()
assert np.allclose(_F_sheet[np.isfinite(_F_sheet)], F_start_HT[np.isfinite(_F_sheet)], atol=1e-6)

# Earliest steps have no permeation-lag bound yet (too little cumulative
# signal to bracket -- shown as '--' in the workbook); exclude those, along
# with any step flagged as low-signal (measured 3He <0.1 pccSTP, shared
# across every hydrothermal plot -- see thermochr_utils.low_signal_HTWin0601b_mask)
# -- these are the noisy/spiky points in the envelope.
low_signal = low_signal_HTWin0601b_mask(MASTER_XLSX)
have_bounds = (np.isfinite(Rbulk_lb) & np.isfinite(Rbulk_m) & np.isfinite(Rbulk_ub)
               & ~low_signal)


# ---------------------------------------------------------------------------
# Two-scale x axis: Sigma F3He 0-X_BREAK fills the left ZOOM_FRAC of the
# axes (to focus on the hydrothermal steps); X_BREAK-1 is compressed into
# the remainder for context. Piecewise-linear, so steps that straddle the
# break stay continuous. The scale change is marked with a double slash
# on the top and bottom spines.
# ---------------------------------------------------------------------------
X_BREAK = 0.2
ZOOM_FRAC = 2 / 3


def _fwd(x):
    x = np.asarray(x, dtype=float)
    return np.where(x <= X_BREAK, x / X_BREAK * ZOOM_FRAC,
                    ZOOM_FRAC + (x - X_BREAK) / (1 - X_BREAK) * (1 - ZOOM_FRAC))


def _inv(y):
    y = np.asarray(y, dtype=float)
    return np.where(y <= ZOOM_FRAC, y / ZOOM_FRAC * X_BREAK,
                    X_BREAK + (y - ZOOM_FRAC) / (1 - ZOOM_FRAC) * (1 - X_BREAK))


def apply_broken_x_scale(ax):
    ax.set_xscale('function', functions=(_fwd, _inv))
    ax.set_xlim(0, 1)
    ticks = [0, 0.05, 0.1, 0.15, 0.2, 0.4, 0.6, 0.8, 1.0]
    ax.set_xticks(ticks)
    ax.set_xticklabels(['0', '0.05', '0.1', '0.15', '0.2', '0.4', '0.6', '0.8', '1.0'])
    ax.set_xticks(list(np.arange(0.025, X_BREAK, 0.05)) + list(np.arange(0.3, 1.0, 0.2)),
                  minor=True)
    # Double-slash break marks on both spines at the scale change.
    gap, run, rise = 0.008, 0.006, 0.018   # axes-fraction units
    for y in (0, 1):
        ax.add_patch(plt.Polygon([(ZOOM_FRAC - gap - run, y - rise), (ZOOM_FRAC + gap - run, y - rise),
                                  (ZOOM_FRAC + gap + run, y + rise), (ZOOM_FRAC - gap + run, y + rise)],
                                 closed=True, transform=ax.transAxes, facecolor='white',
                                 edgecolor='none', clip_on=False, zorder=10))
        for dx in (-gap, gap):
            ax.plot([ZOOM_FRAC + dx - run, ZOOM_FRAC + dx + run], [y - rise, y + rise],
                    transform=ax.transAxes, color='black', linewidth=1.0,
                    clip_on=False, zorder=11)


def make_plot(outname):
    fig, ax = plt.subplots()
    handles = []

    for key, color, label in [('HDM', 'Orange', 'In Vacuum: Monteiro, 2017'),
                              ('KAF', 'Red', 'In Vacuum: Farley et al., 2024')]:
        y3 = Winsor_Data[f'He3{key}']['He Yield (nCC@STP)']
        y4 = Winsor_Data[f'He4{key}']['He Yield (nCC@STP)']
        cum3, cum4 = accumulate(y3), accumulate(y4)
        ratio = ((y4 / y3) / (cum4[-1] / cum3[-1])).to_numpy()
        f_start, f_end = step_yield_edges(cum3 / cum3[-1])
        ax.hlines(ratio, f_start, f_end, color=color, linewidth=2.2, zorder=2)
        draw_step_connectors(ax, f_start, f_end, ratio, color=color, zorder=2)
        handles.append(Line2D([], [], color=color, linewidth=2.2, label=label))

    # Hydrothermal: central (M) ratio only, no LB-UB error boxes. Interior
    # gaps left by excluded steps are bridged for a clean visual (see
    # thermochr_utils.bridge_interior_gaps) -- display only, not data.
    ok = have_bounds
    hs, he, hm = bridge_interior_gaps(F_start_HT[ok], F_end_HT[ok], Rbulk_m[ok])
    ax.hlines(hm, hs, he, color='Blue', linewidth=2.2, zorder=4)
    draw_step_connectors(ax, hs, he, hm, color='Blue', zorder=4)
    handles.append(Line2D([], [], color='Blue', linewidth=2.2, label='Hydrothermal, This Work'))

    apply_broken_x_scale(ax)
    make_grid()
    ax.set_title(r'Bulk-Normalized $^4He/^3He$ for Win-06-01b Goethite', pad=10)
    ax.set_xlabel(r'$\Sigma F^3He$')
    ax.set_ylabel(r'$\left(^4He/^3He\right)_N$')
    ax.legend(handles=handles, loc='lower right')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


make_plot('Comparative_Ratios_Dtplot_WinsorGT_VacuumHDMKAF.pdf')
