"""
Helium solubility and glass/gas partitioning in fused silica.

Outputs:
  glass_solubility.pdf        – solubility Arrhenius: models vs data
  Helium_Partitioning.pdf     – glass/gas concentration ratio vs T
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import swets_S, swets_D, Ratoms
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

# Literature overlay data (if present) lives in Figures/data/
DATA_DIR = os.path.join(FIG_DIR, 'data')

Ts = np.linspace(-50, 1050, 10000) + 273
NDgas = 1 / (Ratoms * Ts)          # atoms/cc at 1 atm
Sswets = np.array([swets_S(T) for T in Ts])

# Constant molar partitioning reference
NDglass_STP = swets_S(273)
Ss_const = NDglass_STP * (273 / Ts)

Ctemps = np.array([-50, 0, 100, 200, 300, 600])

# ---------------------------------------------------------------------------
# Figure 1: solubility Arrhenius
# ---------------------------------------------------------------------------
fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

ax1.plot(1000 / Ts, np.log(Ss_const), color='black', linewidth=1,
         label='Constant Molar Partitioning (glass/gas = 0.026)')
ax1.plot(1000 / Ts, np.log(Sswets), color='pink',
         label='Swets et al. (1961) model')

# Load external data if available
shack_path = os.path.join(DATA_DIR, 'shacklefordHeSolubility.csv')
swets_path = os.path.join(DATA_DIR, 'swetsHeSolubility.csv')
if os.path.exists(shack_path):
    import pandas as pd
    shack = pd.read_csv(shack_path, header=None).to_numpy()
    ax1.scatter(1000 / shack[:, 0], np.log(1E17 * shack[:, 1]),
                label='Shackelford et al. (1972) data', zorder=5)
if os.path.exists(swets_path):
    import pandas as pd
    swdat = pd.read_csv(swets_path).to_numpy()
    ax1.scatter(1000 / (swdat[:, 0] + 273), np.log(swdat[:, 3]),
                color='pink', label='Swets et al. (1961) data', zorder=5)

ax2.set_xticks(1E3 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (°C)')
ax1.set_xlabel(r'$10^3/T$ (K$^{-1}$)')
ax1.set_ylabel(r'$\ln(S)$ (atoms cm$^{-3}$ atm$^{-1}$)')
ax1.grid(True)
ax1.legend()
ax1.set_title('Helium Solubility in Silica Glass')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'glass_solubility.pdf'), dpi=300,
            bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: glass/gas concentration partitioning ratio vs T
# ---------------------------------------------------------------------------
Ts2 = np.linspace(0, 300, 400) + 273
NDgas2 = 1 / (Ratoms * Ts2)
NDglass2 = np.array([swets_S(T) for T in Ts2])

fig, ax = plt.subplots()
ax.plot(Ts2 - 273, NDglass2 / NDgas2)
ax.set_title('Glass/Gas Partitioning of Helium\n(Swets et al. 1961)')
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel(r'$C^{He}_{glass}$ /$C^{He}_{gas}$')
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Helium_Partitioning.pdf'), dpi=300)
plt.close(fig)
