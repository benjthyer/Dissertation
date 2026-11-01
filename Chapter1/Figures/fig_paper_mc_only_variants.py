"""
fig_paper_mc_only_variants.py -- Copernicus-paper versions of three SI
figures with the atmosphere-equilibrated (quadrupole) empty ampoule removed.

The thesis keeps the original figures (fig_predicting_permeation.py and
fig_permeability_measurements.py, which include that experiment); this
script reuses their plotting code unchanged except for skipping the
'Quad Measured' data, and writes separate *_MC.pdf files so the thesis
figures are not overwritten.

Outputs (generated/):
  Histograms4He_MC.pdf
  PredictingPermeation_error_vs_fraction_MC.pdf
  PermeabilityMeasurements_MC.pdf
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style, BASE_FIGWIDTH_IN, LABEL_SIZE
from thermochr_utils import Jones
apply_style()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

predDat = pd.read_excel('data/plotableEmptyTubes.xlsx', sheet_name=None)
predDat.pop('Quad Measured')                       # <- the only change
labels = ['Empty Ampoule, MC', 'Encapsulated Sulfur, MC', 'Encapsulated Water, MC']
markers = ['d', 'P', 'X']
vmin, vmax = 24, 300

# ---- % error vs predicted fractional yield (fig_predicting_permeation Fig. 2)
legend_handles = []
fig, ax = plt.subplots()
ax.axhline(0, color='black')
norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
cmap = mpl.cm.viridis
for i, (table_name, table) in enumerate(predDat.items()):
    for j, He in enumerate(['4', '3']):
        x = 1 - table[f'{He}He P nt/n0']
        y = table[f'{He}He M% err']
        m = mpl.markers.MarkerStyle(markers[i], fillstyle=['bottom', 'top'][j])
        ax.scatter(x, y, facecolors='white', edgecolors='black', linewidths=0.7,
                   marker=mpl.markers.MarkerStyle(markers[i]), s=50, zorder=2)
        ax.scatter(x, y, c=table['T'], cmap='viridis', vmin=vmin, vmax=vmax,
                   marker=m, s=50, edgecolors='none', zorder=3)
        legend_handles.append(Line2D([0], [0], marker=m, color='none',
                                     markerfacecolor=cmap(norm((vmin + vmax) / 2)),
                                     markeredgecolor='black', markersize=7,
                                     label=f'{He}He, {labels[i]}'))
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
fig.savefig(os.path.join(OUTDIR, 'PredictingPermeation_error_vs_fraction_MC.pdf'), dpi=300)
plt.close(fig)

# ---- 4He error histograms (fig_predicting_permeation Fig. 3), MC ampoules only
wide_scale = 8 / BASE_FIGWIDTH_IN
apply_style(scale=wide_scale)
bins4 = np.linspace(-10, 40, 18)
colors = ['green', 'orange', 'blue']
fig, axes = plt.subplots(3, 1, sharex=True, figsize=(8, 8))
for i, (table_name, table) in enumerate(predDat.items()):
    errs = table['4He M% err']
    if i == 0:
        errs = errs.iloc[:-1]
    mean = np.mean(errs)
    sd2 = np.std(errs) * 2
    axes[i].hist(errs, bins=bins4, color=colors[i], zorder=2)
    axes[i].axvspan(mean - sd2, mean + sd2, color=colors[i], alpha=0.2)
    axes[i].axvspan(mean - sd2 / 2, mean + sd2 / 2, color=colors[i], alpha=0.4)
    axes[i].axvline(0, color='black', linewidth=3, zorder=4)
    axes[i].set_axisbelow(True)
    axes[i].grid(True)
    axes[i].set_title(f'{labels[i]}: mean = {mean:.1f}%, ±{sd2:.1f}% (2σ)')
    axes[i].yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, integer=True))
plt.xlabel(r'% Difference in Predicted and Measured $n_0$ $\left(\frac{n_0^P - n_0}{n_0} \times 100\right)$')
fig.supylabel('Measurement Count', fontsize=LABEL_SIZE * wide_scale)
fig.suptitle('Predicting 4He $n_0$ with Literature Permeability Values')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Histograms4He_MC.pdf'), dpi=300, bbox_inches='tight')
plt.close(fig)

# ---- permeabilities vs literature (fig_permeability_measurements), MC only
apply_style()
Ctemps = np.array([25, 50, 75, 100, 150, 200, 300])
xliminp = [20, 320]
xlim = [1e4 / (273 + xliminp[1]), 1e4 / (273 + xliminp[0])]
MCDat = predDat['MC Measured']
isreal = np.isnan(MCDat['4He ln(K)']) == False
fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()
ax1.scatter(MCDat['10000/T'][isreal][:-1], MCDat['4He ln(K)'][isreal][:-1],
            marker='*', color='blue', label='Measured 4He Permeabilities, MC', zorder=4, alpha=0.7)
ax1.scatter(MCDat['10000/T'][isreal][:-1], MCDat['3He ln(K)'][isreal][:-1],
            marker='*', color='red', label='Measured 3He Permeabilities, MC', zorder=3, alpha=0.7)
swetsK = (0.000304 * 199000000000000000) * np.exp(-(5580 - 680) / (1.987 * (np.flip(xliminp) + 273)))
ax1.plot(xlim, np.log(swetsK), label='Swets et al., 1961 4He Permeabilities',
         color='blue', zorder=0, alpha=0.7)
ax1.plot(xlim, np.log(Jones(np.flip(xliminp) + 273) * swetsK),
         label='Swets et al., 1961 and Jones, 1953\n3He Permeabilities', color='red', zorder=1, alpha=0.7)
ax1.set_xlim(xlim)
ax2.set_xticks(1e4 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (C)')
ax1.set_xlabel(r'$\frac{10000}{T^{ }(K)}$')
ax1.set_ylabel(r'ln(K) $\left(\frac{atoms}{s \cdot cm \cdot atm}\right)$')
ax1.legend()
ax1.grid(True)
plt.title('Measured Helium Permeability of Empty Silica Glass Ampoules')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PermeabilityMeasurements_MC.pdf'), dpi=300)
plt.close(fig)
print('wrote MC-only variants')
