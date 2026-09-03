"""
Measured 4He and 3He permeabilities of empty silica glass ampoules (Quad and
MC) vs 10000/T, compared to Swets et al. (1961) and Jones (1953) predictions.

Reads:
  data/EmptyTubeQuad1.xlsx
  data/plotableEmptyTubes.xlsx  (sheet: MC Measured)

Outputs:
  PermeabilityMeasurements.jpg
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import Jones
from plot_style import apply_style, LEGEND_SIZE
apply_style()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

TubeDat = pd.read_excel('../Tables/EmptyTubeQuad.xlsx', skiprows=1)
predDat = pd.read_excel('data/plotableEmptyTubes.xlsx', sheet_name=None)

Ctemps  = np.array([25, 50, 75, 100, 150, 200, 300])
xliminp = [20, 320]
xlim    = [1e4 / (273 + xliminp[1]), 1e4 / (273 + xliminp[0])]

MCDat  = predDat['MC Measured']
isreal = np.isnan(MCDat['4He ln(K)']) == False

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

ax1.scatter(
    TubeDat['10000/T(K)'][3:], TubeDat['ln(K)'][3:],
    marker='o', color='blue',
    label='Measured 4He Permeabilities, Quad', zorder=2, alpha=0.7,
)
ax1.scatter(
    MCDat['10000/T'][isreal][:-1], MCDat['4He ln(K)'][isreal][:-1],
    marker='*', color='blue',
    label='Measured 4He Permeabilities, MC', zorder=4, alpha=0.7,
)
ax1.scatter(
    MCDat['10000/T'][isreal][:-1], MCDat['3He ln(K)'][isreal][:-1],
    marker='*', color='red',
    label='Measured 3He Permeabilities, MC', zorder=3, alpha=0.7,
)
ax1.plot(
    xlim,
    np.log(
        (0.000304 * 199000000000000000)
        * np.exp(-(5580 - 680) / (1.987 * (np.flip(xliminp) + 273)))
    ),
    label='Swets et al., 1961 4He Permeabilities',
    color='blue', zorder=0, alpha=0.7,
)
ax1.plot(
    xlim,
    np.log(
        Jones(np.flip(xliminp) + 273)
        * (0.000304 * 199000000000000000)
        * np.exp(-(5580 - 680) / (1.987 * (np.flip(xliminp) + 273)))
    ),
    label='Swets et al., 1961 and Jones, 1953\n3He Permeabilities',
    color='red', zorder=1, alpha=0.7,
)

ax1.set_xlim(xlim)
ax2.set_xticks(1e4 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (C)')
ax1.set_xlabel(r'$\frac{10000}{T^{ }(K)}$')
ax1.set_ylabel(r'ln(K) $\left(\frac{atoms}{s⁡*cm*atm}\right)$')
ax1.grid(True)
ax1.legend(fontsize=LEGEND_SIZE * 0.75)  # crowded legend, kept smaller than the standard size
plt.title('Measured Helium Permeability of Empty Silica Glass Ampoules')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PermeabilityMeasurements.pdf'), dpi=300)
plt.close(fig)
