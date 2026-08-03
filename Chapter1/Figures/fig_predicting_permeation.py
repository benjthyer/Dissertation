"""
Predicting He permeation for experimental silica glass ampoules:
compares the PREDICTED INITIAL HELIUM CONTENT (n0^P), computed by
solving the fractional-yield permeation equation (Eq. permsol/
n0informed: HeF = m/n0 = 1 - exp(-KGRTt)) or a forward diffusion model,
against the true/measured n0. (This is error in predicted n0, NOT
error in the predicted fractional yield HeF itself -- see
fig_permeation_eqn_numerical_error.py for that error metric.)

Reads: plotableEmptyTubes.xlsx  (sheets: one per tube type)

Outputs:
  PredictingPermeation_predicted_vs_measured.pdf   (nt/n0 parity plot)
  PredictingPermeation_error_vs_fraction.pdf        (% error vs step size)
  Histograms4He.pdf
  Histograms3He.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style, BASE_FIGWIDTH_IN, LABEL_SIZE
apply_style()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

predDat = pd.read_excel('data/plotableEmptyTubes.xlsx', sheet_name=None)
labels  = ['Empty Ampoule, Quad', 'Empty Ampoule, MC',
           'Encapsulated Sulfur, MC', 'Encapsulated Water, MC']
markers = ['s', 'd', 'P', 'X']
vmin, vmax = 24, 300

# ---------------------------------------------------------------------------
# Figure 1: predicted n_t/n_0 vs measured n_t/n_0 (first two tube types only)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1], color='black')
for i, (table_name, table) in enumerate(predDat.items()):
    #if i >= 2:
    #    break
    for j, He in enumerate(['4', '3']):
        if i == 0 and j == 1:
            continue  # Quad has no 3He column
        marker = mpl.markers.MarkerStyle(markers[i], fillstyle=['bottom', 'top'][j])
        sc = ax.scatter(
            table[f'{He}He P nt/n0'], table[f'{He}He M nt/n0'],
            c=table['T'], cmap='viridis', vmin=vmin, vmax=vmax,
            marker=marker, edgecolors='black', linewidths=1, s=100,
            label=f'{He}He, {labels[i]}')
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('T (°C)')
ax.set_xlim([0, 1])
ax.set_ylim([0, 1])
ax.grid(True)
ax.legend()
ax.set_xlabel(r'Predicted $n_t/n_0 = e^{-KGRTt}$')
ax.set_ylabel(r'Measured $n_t/n_0$')
ax.set_title('Predicting He Permeation in Silica Glass Ampoules')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PredictingPermeation_predicted_vs_measured.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: % error vs predicted fractional yield (all tube types)
# ---------------------------------------------------------------------------
legend_handles = []
fig, ax = plt.subplots()
ax.axhline(0, color='black')
for i, (table_name, table) in enumerate(predDat.items()):
    for j, He in enumerate(['4', '3']):
        if i == 0 and j == 1:
            continue
        norm  = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        cmap  = mpl.cm.viridis
        x     = 1 - table[f'{He}He P nt/n0']
        y     = table[f'{He}He M% err']
        m     = mpl.markers.MarkerStyle(markers[i], fillstyle=['bottom', 'top'][j])
        # White base gives the unfilled half a background and provides the full outline
        ax.scatter(x, y, facecolors='white', edgecolors='black', linewidths=0.7,
                   marker=mpl.markers.MarkerStyle(markers[i]), s=50, zorder=2)
        # Color half-fill on top, no edge (base layer already provides it)
        ax.scatter(x, y, c=table['T'], cmap='viridis',
                   vmin=vmin, vmax=vmax, marker=m, s=50,
                   edgecolors='none', zorder=3)
        legend_handles.append(Line2D(
            [0], [0], marker=m, color='none',
            markerfacecolor=cmap(norm((vmin + vmax) / 2)),
            markeredgecolor='black',
            markersize=7, label=f'{He}He, {labels[i]}'))

cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap='viridis'), ax=ax)
cbar.set_ticks([25, 50, 75, 100, 125, 150, 200, 250, 300])
cbar.set_ticklabels([f'{t}°C' for t in [25, 50, 75, 100, 125, 150, 200, 250, 300]])
cbar.set_label('Temperature (°C)')
ax.grid(True)
ax.legend(handles=legend_handles)
ax.set_xlabel(r'Predicted Fractional Yield $m/n_0 = 1 - e^{-KGRTt}$')
ax.set_ylabel(r'$\frac{n_0^P - n_0}{n_0} \times 100$ (percent)')
ax.set_title(r'Predicting $n_0$ with Literature Permeability Values''\n'r'For Varied Fractional Yield ($^{He}F$)')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PredictingPermeation_error_vs_fraction.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 3: 4He error histograms (all four tube types)
# ---------------------------------------------------------------------------
# These two histogram figures are built wider than the default figsize
# (8 in vs the 6.4 in baseline), so bump the font sizes proportionally
# to compensate for the extra shrinkage when placed at the same final
# printed width as every other figure -- see plot_style.py.
wide_scale = 8 / BASE_FIGWIDTH_IN
apply_style(scale=wide_scale)
bins4  = np.linspace(-10, 40, 18)
colors = ['red', 'green', 'orange', 'blue']
fig, axes = plt.subplots(4, 1, sharex=True, figsize=(8, 10))
for i, (table_name, table) in enumerate(predDat.items()):
    errs = table['4He M% err']
    if i == 1:
        errs = errs.iloc[:-1]
    mean = np.mean(errs)
    sd2  = np.std(errs) * 2
    axes[i].hist(errs, bins=bins4, color=colors[i], zorder=2)
    axes[i].axvspan(mean - sd2, mean + sd2, color=colors[i], alpha=0.2)
    axes[i].axvspan(mean - sd2/2, mean + sd2/2, color=colors[i], alpha=0.4)
    axes[i].axvline(0, color='black', linewidth=3, zorder=4)
    for xv in [-10, 10, 20, 30, 40]:
        axes[i].axvline(xv, linestyle='--', color='black', alpha=0.5)
    axes[i].set_title(f'{labels[i]}: mean = {mean:.1f}%, ±{sd2:.1f}% (2σ)')
    axes[i].yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, integer=True))
plt.xlabel(r'% Difference in Predicted and Measured $n_0$ $\left(\frac{n_0^P - n_0}{n_0} \times 100\right)$')
fig.supylabel('Measurement Count', fontsize=LABEL_SIZE * wide_scale)
fig.suptitle('Predicting 4He $n_0$ with Literature Permeability Values')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Histograms4He.pdf'), dpi=300, bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 4: 3He error histograms (MC tube types only)
# ---------------------------------------------------------------------------
bins3 = np.linspace(-20, 45, 18)
colors3 = ['green', 'orange', 'blue']
fig, axes = plt.subplots(3, 1, sharex=True, figsize=(8, 8))
k = 0
for i, (table_name, table) in enumerate(predDat.items()):
    if i == 0:
        continue
    errs = table['3He M% err']
    if i == 1:
        errs = errs.iloc[:-1]
    mean = np.mean(errs)
    sd2  = np.std(errs) * 2
    axes[k].hist(errs, bins=bins3, color=colors3[k], zorder=2)
    axes[k].axvspan(mean - sd2, mean + sd2, color=colors3[k], alpha=0.2)
    axes[k].axvspan(mean - sd2/2, mean + sd2/2, color=colors3[k], alpha=0.4)
    axes[k].axvline(0, color='black', linewidth=3, zorder=4)
    for xv in [-20, -10, 10, 20, 30, 40]:
        axes[k].axvline(xv, linestyle='--', color='black', alpha=0.5)
    axes[k].set_title(f'{labels[i]}: mean = {mean:.1f}%, ±{sd2:.1f}% (2σ)')
    axes[k].yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, integer=True))
    k += 1
plt.xlabel(r'% Difference in Predicted and Measured $n_0$ $\left(\frac{n_0^P - n_0}{n_0} \times 100\right)$')
fig.supylabel('Measurement Count', fontsize=LABEL_SIZE * wide_scale)
fig.suptitle('Predicting 3He $n_0$ with Literature Permeability Values')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Histograms3He.pdf'), dpi=300, bbox_inches='tight')
plt.close(fig)
