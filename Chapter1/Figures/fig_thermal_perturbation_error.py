"""
Error in the PREDICTED FRACTIONAL YIELD (HeF) from the fractional-yield
permeation equation (Eq. permsol) after a thermal perturbation (stepping
from T1 to T2) -- i.e. the relative disequilibrium excess/deficit of
Eq. s7-1b in the supplement, normalized to the expected permeate amount
-- and the equilibrium fraction of He within the glass wall. (This is
error in ^{He}F, NOT error in a predicted n0.)

Outputs:
  Thermal_Perturbation_Error.pdf  – relative error vs time at several T1/T2
  PercentHeInGlass.pdf            – % of ampoule He in glass at EQM vs T
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import swets, Ratoms
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)

# Tube geometry
a0 = 0.03   # cm  (inner radius)
b0 = 0.05   # cm  (outer radius)
G = 2 / (a0 ** 2 * np.log(b0 / a0))
H = -G * Ratoms * (0.5 * a0 ** 2 * (np.log(b0 / a0) + 0.5) - b0 ** 2 / 4)

T1s = np.array([200, 300]) + 273
T2s = np.array([80, 100, 120]) + 273

colors = ['Green', 'Orange', 'Red']
lines = ['-', '--', ':']

# ---------------------------------------------------------------------------
# Figure 1: relative error after thermal perturbation (linear profile approx)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
for i, T1 in enumerate(T1s):
    S1 = swets('S', T1)
    for j, T2 in enumerate(T2s):
        ts = np.linspace([60, 45, 30][j], 180, 500) * 60
        S2 = swets('S', T2)
        lam = T2 * Ratoms * G * swets('K', T2)
        expterm = np.exp(-lam * ts)
        Err = 100 * ((1 / (1 / (H * T1 * S1) + 1))
                     - (1 / (1 / (H * T2 * S2) + 1))) / (1 - expterm)
        ax.plot(ts / 60, Err, color=colors[i],
                label=f'T1 = {T1 - 273}°C; T2 = {T2 - 273}°C',
                linestyle=lines[j])
ax.legend()
ax.set_xlabel('Time (minutes)')
ax.set_ylabel(r'Relative Error in Predicted $^{He}F$ (%)')
ax.set_title(r'Error in Predicted Fractional Yield ($^{He}F$)'+'\nAfter Thermal Perturbation')
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Thermal_Perturbation_Error.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: fraction of ampoule He within glass at EQM vs T
# ---------------------------------------------------------------------------
Ts_range = np.linspace(0, 300, 500) + 273
Ss = np.array([swets('S', T) for T in Ts_range])

aa = np.array([0.027, 0.03, 0.04, 0.05])
bb = aa * np.exp(2 / (G * aa ** 2))
Vglass_Vgas = (bb ** 2 - aa ** 2) / aa ** 2
Ds_eff = (2 * Ratoms / aa ** 2) * ((bb ** 3 - 3 * aa ** 2 * bb + 2 * aa ** 3) / (6 * (bb - aa)))

clrs = ['Red', 'Black', 'Green', 'Blue']
fig, ax = plt.subplots()
for i, D in enumerate(Ds_eff):
    frac_in_glass = 100 * (1 / (1 / (D * Ts_range * Ss) + 1))
    ax.plot(Ts_range - 273, frac_in_glass, color=clrs[i],
            label=f'Glass/Gas Vol = {Vglass_Vgas[i]:.1f}')
ax.legend(loc='best')
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('He in Glass at EQM (%)')
ax.set_title(f'Portion of Ampoule He Within Glass\nat EQM (G = {G:.1f})')
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PercentHeInGlass.pdf'), dpi=300)
plt.close(fig)
