"""
Diffusive equilibration timescales for fused silica glass walls.

Output:
  diffusive_EQM_fused_silica.pdf
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import swets_D
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)

H = np.array([0.01, 0.015, 0.02, 0.03])   # wall thicknesses in cm
Ts = np.linspace(0, 200, 1000) + 273
Ds = np.array([swets_D(T) for T in Ts])

fig, ax = plt.subplots()
for h in H:
    tau_min = (h ** 2 / Ds) / 60
    ax.plot(Ts - 273, tau_min, label=f'Wall thickness = {h * 1E4:.0f} µm')

ax.set_xlabel('Temperature (°C)')
ax.set_ylabel(r'Time to Diffusive EQM $\tau$ (min)')
ax.set_title('Diffusive EQM Timescales for Fused Silica')
ax.set_ylim(0, 200)
ax.legend()
fig.tight_layout()
plt.grid()
fig.savefig(os.path.join(OUTDIR, 'diffusive_EQM_fused_silica.pdf'), dpi=300)
plt.close(fig)
