"""
Winsor-06-01b money plot: 3He diffusivity inversions from hydrothermal
step-heat experiments (MC) compared with vacuum (Monteiro, 2017).

Reads: Win0601bHT_data_and_reduction.xlsx, sheet 'diffusivitiesHTWin0601b'
           (hydrothermal reduction, this study -- via load_diffusivities_HTWin0601b)
       generated/data/He3_HDMwinsor_diffusion.csv  (written by fig_winsor_goethite_analysis.py)

Output: winsor_goethite_moneyplot.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import load_diffusivities_HTWin0601b
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
DATA_DIR = FIG_DIR
os.chdir(DATA_DIR)
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

Rcal = 1.987

# Hydrothermal MC data (this study)
bjt = load_diffusivities_HTWin0601b(MASTER_XLSX)['3']
big_yields = bjt['He Corrected'] >= 0.1
small_yields = bjt['He Corrected'] < 0.1

# Vacuum HDM data (Monteiro, 2017)
hdm = pd.read_csv(os.path.join(FIG_DIR, 'generated', 'data', 'He3_HDMwinsor_diffusion.csv')).iloc[:-1]

# Regression reference (Stage 1)
ref_D0_a2 = 52430550.28
ref_Ea    = 38851.811
min_T = 1E4 / (350 + 273)
max_T = 1E4 / (100 + 273)
T_range = [min_T, max_T]
lnD_range = [np.log(ref_D0_a2 * np.exp(-ref_Ea / (Rcal * 1E4 / T)))
             for T in T_range]

Ctemps = np.array([150, 175, 200, 225, 250])

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

ax1.plot(bjt['10000/TK'], bjt['ln(d/a^2)'], linestyle='--', color='grey')
ax1.scatter(bjt['10000/TK'][big_yields], bjt['ln(d/a^2)'][big_yields],
            color='blue', marker='*', label='Hydrothermal (This Work)')
ax1.scatter(bjt['10000/TK'][small_yields], bjt['ln(d/a^2)'][small_yields],
            color='blue', s=10, label='< 0.1 pccSTP Yield')

ax1.plot(hdm['10^4/T'], hdm['ln(D/a^2)'], linestyle='--', color='grey')
ax1.scatter(hdm['10^4/T'], hdm['ln(D/a^2)'],
            color='red', marker='x', label='Vacuum, Monteiro, 2017')

ax1.set_xlim([min_T, max_T])
ax2.set_xticks(1E4 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (°C)')
ax1.set_xlabel(r'$10^4/T$ (K)')
ax1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
ax1.legend(fontsize=9)
plt.title('³He Diffusivity Inversions — Win-06-01b Goethite\nHydrothermal and High Vacuum')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'winsor_goethite_moneyplot.pdf'), dpi=300)
plt.close(fig)
