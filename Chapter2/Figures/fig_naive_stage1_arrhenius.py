"""
Win-06-01b goethite Arrhenius plot: 3He diffusivities from the na\"ive/
informed bracketing (permeation-step) method, with that method's own
Stage 1 regression, plotted against the same vacuum step-heating
comparison data (Monteiro 2017; Farley et al. 2024) used by
fig_decomp_vs_hydrothermal.py's plot_zoom(). This is the direct-
measurement counterpart to fig:ch2-arrhenius-zoom (the bounding-method
regression), used to check it in \\S\\ref{complete-degas-test}-adjacent
discussion in Chapter 2 and \\S\\ref{sec:discussion-bounding-direct} in
the manuscript.

Only 3He is plotted: 4He permeation-step signals were blank-level
throughout the experiment, so 4He has no naive-method diffusivity
counterpart (see load_diffusivities_HTWin0601b_naive).

Reads:
  generated/data/He3_HDMwinsor_diffusion.csv, generated/data/He3_KAFwinsor_diffusion.csv
      (vacuum reductions, written by fig_winsor_goethite_analysis.py)
  Win0601bHT_data_and_reduction.xlsx, sheet 'diffusivitiesHTWin0601bNaive'
      (via load_diffusivities_HTWin0601b_naive)
  Figures/generated/data/stage1_regression_cache.json, 'naive' key
      (written by prepare_regression_cache.py -- run that first if this
      script complains it's missing)

Outputs:
  winsor_goethite_Diffusivities_Arrhenius_Zoomin_naive.pdf

Two steps (Temp/Minutes 195/1106 and 185/740) are excluded by
load_diffusivities_HTWin0601b_naive's default -- see that function's
docstring for why (the one-off "long cool"/K_cold correction they alone
required).
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import load_diffusivities_HTWin0601b_naive, load_stage1_cache
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
    f'He3{key}': pd.read_csv(os.path.join(DATA_OUTDIR, f'He3_{key}winsor_diffusion.csv'))
    for key in ['HDM', 'KAF']
}
naive = load_diffusivities_HTWin0601b_naive(MASTER_XLSX)['3']
stage1 = load_stage1_cache()
fit = stage1['naive']

Ctemps = np.array([75, 100, 150, 200, 250, 300, 350, 400, 450])

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

xlim = [1E4 / (273 + 275), 1E4 / (273 + 150)]
Ea_kJmol = fit['Ea_cal_mol'] * 4.184 / 1000
print(f"Stage 1 reference line (naive/informed bracketing): Ea = {Ea_kJmol:.1f} kJ/mol, "
      f"intercept = {fit['intercept']:.2f}, R^2 = {fit['r2']:.3f}, n = {fit['n_points']}")
ax1.plot(xlim, (fit['slope'] * np.array(xlim)) + fit['intercept'],
         label=f"Stage 1 Reference: Ea {Ea_kJmol:.0f} kJ/mol", color='green', alpha=0.5)

for i, l in enumerate(['HDM', 'KAF']):
    sub = Winsor_Data[f'He3{l}']
    ax1.plot(sub['10^4/T'], sub['ln(D/a^2)'], alpha=0.5, color=['orange', 'red'][i], linestyle=':')
    ax1.scatter(sub['10^4/T'], sub['ln(D/a^2)'],
                label=f"Vacuum He3: {['Monteiro, 2017', 'Farley et al., 2024'][i]}",
                marker='x', color=['orange', 'red'][i], alpha=0.5)

ax1.plot(naive['10000/TK'], naive['ln(d/a^2)'], linestyle='--', color='blue', alpha=0.5)
ax1.errorbar(naive['10000/TK'], naive['ln(d/a^2)'], yerr=naive['ln(d/a^2) 2 sigma'],
             markeredgecolor='green', ecolor='green', capsize=5,
             marker='o', color='blue', alpha=0.5,
             label='Hydrothermal He3: Permeation-Step Method', linestyle='')

ax1.set_xlim(xlim)
ax1.set_ylim([-32, -17])
ax2.set_xticks(1E4 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (C)')
ax1.set_xlabel(r'$\frac{10000}{T^{ }(K)}$')
ax1.set_ylabel(r'$ln\left(\frac{D}{a^2}\right) \left(sec^{-1}\right)$')
ax1.legend(loc='lower left', fontsize=8)
plt.title('Win-06-01b Goethite He Diffusivities\n(Permeation-Step Method)')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'winsor_goethite_Diffusivities_Arrhenius_Zoomin_naive.pdf'), dpi=300)
plt.close(fig)
print(f"Wrote {os.path.join(OUTDIR, 'winsor_goethite_Diffusivities_Arrhenius_Zoomin_naive.pdf')}")
