"""
Compare the two independent 3He step-heat diffusivity reductions for
HT-Win-06-01b: ln(D/a^2) from the na\"ive/informed bracketing
(permeation-step) method against ln(D/a^2) from the bounding method's
central (M) "treatment as uncertainty" bound. This is the diffusivity-
level counterpart to fig_nt_vs_ntss_comparison.py's ampoule-inventory
comparison, referenced alongside it in \\S\\ref{complete-degas-test}-
adjacent discussion in Chapter 2 and \\S\\ref{sec:discussion-bounding-direct}
in the manuscript.

Both axes carry uncertainty: x from asymmetric_yerr() (the bounding
method's own LB/UB "treatment as uncertainty" spread around M), y from
the permeation-step method's directly-propagated 2-sigma on D/a^2 (see
load_diffusivities_HTWin0601b_naive).

Steps excluded from the plot:
  - The two steps (Temp/Minutes 195/1106 and 185/740) excluded by
    load_diffusivities_HTWin0601b_naive's default (see that function's
    docstring): their na\"ive-method n0 depended on the one-off "long
    cool"/K_cold correction, so they are not on a consistent footing
    with the rest of the dataset for this comparison.
  - Steps flagged low-signal (measured 3He < 0.1 pccSTP, via
    thermochr_utils.low_signal_HTWin0601b_mask), same exclusion used in
    fig_nt_vs_ntss_comparison.py and fig_decomp_vs_hydrothermal.py.

Reads:
  Win0601bHT_data_and_reduction.xlsx, sheets 'diffusivitiesHTWin0601b{M,UB,LB}'
      and 'diffusivitiesHTWin0601bNaive'

Outputs:
  generated/Winsor_diffusivity_naive_vs_bounding.pdf
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (load_diffusivities_HTWin0601b_bounds, load_diffusivities_HTWin0601b_naive,
                              low_signal_HTWin0601b_mask, asymmetric_yerr)
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

EXCLUDE_STEPS = (11, 12)  # see load_diffusivities_HTWin0601b_naive docstring

# --- Load both reductions at full 34-step length (no exclusion yet) so the
# two datasets stay row-aligned by step, then apply the same exclusion mask
# to both. ---
bounds = load_diffusivities_HTWin0601b_bounds(MASTER_XLSX)
naive_full = load_diffusivities_HTWin0601b_naive(MASTER_XLSX, exclude_steps=())['3']
low_signal = low_signal_HTWin0601b_mask(MASTER_XLSX)

step = np.arange(1, 35)
excluded_for_kcold = np.isin(step, EXCLUDE_STEPS)
keep = (~low_signal) & (~excluded_for_kcold)
print(f"Excluding {(~keep).sum()} of 34 steps from the comparison "
      f"({(low_signal & excluded_for_kcold).sum()} step(s) excluded on both grounds): "
      f"{list(step[~keep])}")

x = bounds['3']['M']['ln(d/a^2)'].to_numpy()[keep]
xerr = asymmetric_yerr(bounds, '3')[:, keep]
y = naive_full['ln(d/a^2)'].to_numpy()[keep]
yerr = naive_full['ln(d/a^2) 2 sigma'].to_numpy()[keep]

fig, ax = plt.subplots()
lo = min(np.nanmin(x - xerr[0]), np.nanmin(y - yerr)) - 0.5
hi = max(np.nanmax(x + xerr[1]), np.nanmax(y + yerr)) + 0.5
lims = (lo, hi)
ax.plot(lims, lims, linestyle='--', color='black', alpha=0.4, zorder=1,
        label='1:1')
ax.errorbar(x, y, xerr=xerr, yerr=yerr, fmt='o', color='blue',
            ecolor='black', alpha=0.7, capsize=3, markeredgecolor='black',
            markersize=6, zorder=2)

ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_aspect('equal')
ax.set_xlabel(r'$\ln(D/a^2)$ (sec$^{-1}$)''\nbounding method')
ax.set_ylabel(r'$\ln(D/a^2)$ (sec$^{-1}$)''\npermeation-step method')
ax.set_title('Win-06-01b Goethite $^3$He Diffusivities\nMethod Comparison')
ax.grid(True, which='both', linestyle='-', color='black', alpha=0.1)

legend_elems = [Line2D([0], [0], linestyle='--', color='black', alpha=0.4, label='1:1'),
                Line2D([0], [0], marker='o', linestyle='None', markerfacecolor='blue',
                       markeredgecolor='black', markersize=8, label='HT-Win-06-01b step')]
ax.legend(handles=legend_elems, loc='upper left')

fig.tight_layout()
outpath = os.path.join(OUTDIR, 'Winsor_diffusivity_naive_vs_bounding.pdf')
fig.savefig(outpath, dpi=300)
plt.close(fig)
print(f"Wrote {outpath}")
