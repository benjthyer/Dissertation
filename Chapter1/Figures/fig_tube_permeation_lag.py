"""
Tube permeation lag figures.

Outputs:
  EQNtest.pdf              – numerical vs analytical n(t) comparison
  LagPlot.pdf              – relative permeation lag for 4–48 h steps
  EQM_Timescales_Permeation.pdf – equilibration timescales τ = 5/λ
  FirstOrderDecay.pdf      – e^(−λt) vs λt
  UncertEstLongStep.pdf    – uncertainty estimate for ω ≈ m approximation
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import swets_K, Ratoms, Simulate_Diffusion_Tube_P
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)

# Tube geometry (typical MC blank tube)
OD = 0.1    # cm
ID = 0.06   # cm
G = 2 / (np.log(OD / ID) * (ID / 2) ** 2)

# ---------------------------------------------------------------------------
# Figure 1: numerical simulation vs analytical solution (constant source)
# ---------------------------------------------------------------------------
tsched = [1000, 7200, 7200, 7200, 3600, 7200, 7200, 7200, 7200]  # s
Tsched = [250, 200, 300, 350, 400, 325, 275, 250, 420]            # °C
Rsched = np.array([5, 4, 3, 2, 6, 7, 4, 2, 8]) / 3600

(Fcum, n0, Fstep_apparent, Fcum_apparent,
 n0_ends, t_out, temps, Fsteps) = Simulate_Diffusion_Tube_P(
    P=Rsched, T=Tsched, t=tsched, OD=OD, ID=ID)

n1HT = [0.0]
for i, step in enumerate(Fstep_apparent):
    denom = (Tsched[i] + 273) * tsched[i] * Ratoms * G * swets_K(Tsched[i] + 273)
    n1HT.append(
        (((step - n1HT[-1]) / denom) * (1 - np.exp(-denom))
         + n1HT[-1] * np.exp(-denom))
        / (1 - (1 / denom) * (1 - np.exp(-denom)))
    )

fig, ax = plt.subplots()
sc = ax.scatter(np.arange(len(n0)), n0,
                s=1, c=np.array(temps) - 273, label='Numerical Simulation')
ax.scatter(t_out, n1HT[1:],
           c=np.array(temps)[np.array(t_out) - 1] - 273,
           label='Analytical Solution')
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('Temperature (°C)')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Helium in Tube (arb. units)')
ax.set_title('Permeation Lag — Numerical vs Analytical\n(Constant Offgassing Rate)')
ax.grid(True)
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'EQNtest.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: relative permeation lag for 4, 8, 24, 48-h steps
# ---------------------------------------------------------------------------
def n_p(T, t, G=G):
    K = swets_K(T)
    return (1 / (K * G * T * t * Ratoms)) * (1 - np.exp(-K * G * T * Ratoms * t))

def SS(T, t, G=G):
    K = swets_K(T)
    return 1 / (K * G * T * t * Ratoms)

colors = ['Blue', 'Green', 'Purple', 'Pink']
temps_arr = np.linspace(25, 600, 1000) + 273

fig, ax = plt.subplots()
for i, hours in enumerate([4, 8, 24, 48]):
    sec = hours * 3600
    NP = [n_p(T=T, t=sec) for T in temps_arr]
    ss = [SS(T=T, t=sec) for T in temps_arr]
    ax.plot(temps_arr - 273, NP, label=f'{hours}-h step', color=colors[i])
    ax.plot(temps_arr - 273, ss, linestyle='--', color=colors[i])
ax.plot([25, 600], [0.05, 0.05], 'k--', label='5 % threshold')
ax.set_xlim(25, 600)
ax.set_ylim(0, 1.25)
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('Portion of Yield in Tube')
ax.set_title('Relative Permeation Lag for Typical Silica Tube\n(Constant He Source)')
ax.grid(True)
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'LagPlot.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 3: equilibration timescales τ = 5/λ for several G values
# ---------------------------------------------------------------------------
Gs = [2000, 3000, 4000, 5000, 6000]
cols = ['Blue', 'Green', 'Orange', 'Red', 'Violet']
Ts_arr = np.linspace(200, 500, 500)

fig, ax = plt.subplots()
for i, Gv in enumerate(Gs):
    lams = (Ts_arr + 273) * np.array([swets_K(T + 273) for T in Ts_arr]) * Gv * Ratoms
    tao5 = (5 / lams) / 3600
    ax.plot(Ts_arr, tao5, color=cols[i], label=f'G = {Gv} cm⁻²')
ax.legend()
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('EQM Timescale  t = 5/λ  (hours)')
ax.set_title('Equilibration Timescales for He Permeation (λt = 5)')
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'EQM_Timescales_Permeation.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 4: first-order decay curve e^(−λt) vs λt
# ---------------------------------------------------------------------------
lamt = np.linspace(0, 7, 200)
fig, ax = plt.subplots()
ax.plot(lamt, np.exp(-lamt), color='black')
ax.set_xlabel(r'$\lambda t$')
ax.set_ylabel(r'$e^{-\lambda t}$')
ax.set_title('Timescales for Decay in First-Order Processes')
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'FirstOrderDecay.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 5: upper-bound uncertainty for ω ≈ m approximation
# (Cell 036 — with Jones correction)
# ---------------------------------------------------------------------------
from diffusion_utils import swets_K  # already imported but explicit

OD2 = 0.083
ID2 = 0.054
G2 = 2 / (np.log(OD2 / ID2) * (ID2 / 2) ** 2)
cols5 = ['Blue', 'Green', 'Orange', 'Red', 'Violet']
ts5 = np.linspace(0, 2, 500) * 24 * 3600
omegas5 = ts5
Ts5 = [200, 250, 300, 400, 500]

fig, ax = plt.subplots()
for i, T in enumerate(Ts5):
    K = swets_K(T + 273)
    lam = G2 * K * (T + 273) * Ratoms
    LT = lam * ts5
    # Only plot where LT >= 5 to avoid transient regime
    mask = LT >= 5
    if np.any(mask):
        ax.plot(ts5[mask] / 3600, 100 * (1 / (LT[mask] - 1)),
                linestyle='-', color=cols5[i], label=f'T = {T}°C')
ax.set_xlabel('Time (hours)')
ax.set_ylabel(r'$n_t/m$ Upper Bound (%)')
ax.set_title(r'Uncertainty Estimate for $\omega \approx m$ Approximation')
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'UncertEstLongStep.pdf'), dpi=300)
plt.close(fig)
