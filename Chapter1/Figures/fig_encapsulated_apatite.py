"""
Correcting permeation lag in the encapsulated Durango apatite step-heat.
Reads: apatite_tube_plotables.csv

Output: encapsulated_DApErr.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
apply_style()
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

ApatiteDat = pd.read_csv('data/apatite_tube_plotables.csv')
plotable = ApatiteDat['2s'] < 2
Ctemps = np.array([100, 150, 200, 250, 300, 400])
xlim = [1E4 / (420 + 273), 1E4 / (80 + 273)]

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

ax1.plot(xlim,
         np.log(((10**1.5) / 0.015**2)
                * np.exp(-33000 / (1.987 * (273 + np.array([420, 80]))))),
         color='green', label='Farley, 2000 Durango, r = 150 µm')
ax1.errorbar(ApatiteDat['10000/TK'], ApatiteDat['UncCor'],
             yerr=ApatiteDat['U2s'], marker='s', capsize=5,
             color='red', alpha=0.6, linestyle=':',
             label='Uncorrected Apparent Diffusivities')
ax1.errorbar(ApatiteDat['10000/TK'][plotable],
             ApatiteDat['Cor ln(d/a^2)'][plotable],
             yerr=ApatiteDat['2s'][plotable],
             capsize=5, alpha=0.6, marker='o', color='blue', linestyle=':',
             label='Corrected Apparent Diffusivities')

ax1.set_xlim(xlim)
ax2.set_xticks(1E4 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (°C)')
ax1.set_xlabel(r'$10^4/T$ (K)')
ax1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
ax1.legend()
plt.title('Permeation Lag in Encapsulated Durango Apatite')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'encapsulated_DApErr.pdf'), dpi=300)
plt.close(fig)
