"""
Timescale ratios and equilibration times for helium in silica ampoules.

Outputs:
  VRvsRtau.pdf        – τ_D / τ_P ratio vs glass/gas volume ratio
  EQM_timescales.pdf  – time to establish EQM He profile in glass wall
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import swets, swets_D, Ratoms, make_grid
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Figure 1: diffusion/permeation timescale ratio vs VR
# ---------------------------------------------------------------------------
VR = np.linspace(0.01, 20, 200)
VP = (VR + 1) ** 0.5

Ts = np.array([25, 250, 500]) + 273
colors = ['blue', 'orange', 'red']

fig, ax = plt.subplots()
for i, T in enumerate(Ts):
    S = swets('S', T)
    tauR = S * Ratoms * T * VR * ((-1 + VP) / (1 + VP)) * (2 / np.log(VP))
    ax.loglog(VR, tauR, label=f'T = {T - 273}°C', color=colors[i])
make_grid()
ax.legend()
ax.set_xlabel(r'Glass/Gas Volume Ratio $V_\mathrm{glass/gas}$')
ax.set_ylabel(r'Diffusion/Permeation Timescale Ratio $\tau_D/\tau_P$')
ax.set_title('Relative Timescales: He Diffusion and Permeation\nin Silica Glass Ampoules')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'VRvsRtau.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: time to establish EQM He profile in glass for several wall thicknesses
# ---------------------------------------------------------------------------
Ts_range = np.linspace(80, 120, 200)
Ls = np.array([0.015, 0.02, 0.025, 0.03])   # cm
Ds = np.array([swets_D(T + 273) for T in Ts_range])

fig, ax = plt.subplots()
clrs = ['Red', 'Orange', 'Green', 'Blue']
for j, L in enumerate(Ls):
    tau_min = (L ** 2 / Ds) / 60
    ax.plot(Ts_range, tau_min, color=clrs[j],
            label=f'L = {int(L * 1E4)} µm')
make_grid()
ax.set_title('Timescales to Establish EQM He Profile in Glass')
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('Time (minutes)')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'EQM_timescales.pdf'), dpi=300)
plt.close(fig)
