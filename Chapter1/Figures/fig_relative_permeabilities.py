"""
Measured 3He/4He permeability ratio (K3/K4) of silica glass ampoules vs
temperature, with Jones (1953) model curve and shaded regions for the
encapsulated-water and encapsulated-sulfur experiments.

Reads:
  data/EmptyTubeQuad1.xlsx
  data/plotableEmptyTubes.xlsx  (sheets: MC Measured, MC Sulfur, MC Water)

Outputs:
  Relative_Permeabilities.jpg
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import Jones
from plot_style import apply_style
apply_style()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

predDat = pd.read_excel('data/plotableEmptyTubes.xlsx', sheet_name=None)

Ctemps  = np.array([25, 50, 75, 100, 150, 200, 300])
xliminp = [20, 320]
xlim    = [1e4 / (273 + xliminp[1]), 1e4 / (273 + xliminp[0])]

MCDat  = predDat['MC Measured']
isreal = np.isnan(MCDat['4He ln(K)']) == False

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

waterpoly = Polygon(
    np.array([
        [10000 / (24 + 273), 1.0786e+00 - 1.8912e-01],
        [10000 / (24 + 273), 1.0786e+00 + 1.8912e-01],
        [10000 / (100 + 273), 1.0786e+00 + 1.8912e-01],
        [10000 / (100 + 273), 1.0786e+00 - 1.8912e-01],
    ]),
    color='blue', alpha=0.2, label='Encapsulated Water',
)
sulfurpoly = Polygon(
    np.array([
        [10000 / (24 + 273), 1.04953e+00 - 8.41327e-02],
        [10000 / (24 + 273), 1.04953e+00 + 8.41327e-02],
        [10000 / (150 + 273), 1.04953e+00 + 8.41327e-02],
        [10000 / (150 + 273), 1.04953e+00 - 8.41327e-02],
    ]),
    color='orange', alpha=0.4, label='Encapsulated Sulfur',
)
ax1.add_patch(waterpoly)
ax1.add_patch(sulfurpoly)

ax1.scatter(
    MCDat['10000/T'][isreal][:-1],
    MCDat['K3/4'][isreal][:-1],
    marker='s', edgecolor='black', color='green',
    label='Empty Tube', zorder=2, alpha=0.7,
)
ax1.plot(xlim, Jones(np.flip(xliminp) + 273), label='Jones, 1953', color='red', zorder=1, alpha=0.7)
ax1.plot(xlim, [1, 1], linestyle='--', color='black')

ax1.set_xlim(xlim)
ax2.set_xticks(1e4 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (C)')
ax1.set_xlabel(r'$\frac{10000}{T^{ }(K)}$')
ax1.set_ylabel(r'$\frac{K\left(^3He\right)}{K\left(^4He\right)}$')
ax1.legend(loc='lower left')
ax1.grid(True)
plt.title('Measured 3He/4He Permeability of Silica Glass')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Relative_Permeabilities.pdf'), dpi=300)
plt.close(fig)
