"""
Sanity check: evolution of the He concentration profile in a silica ampoule
over several permeation timescales at constant temperature, starting from
the raw idealized (unrelaxed) analytic profile that permeation_sim.__init__
sets up -- i.e. deliberately skipping the stabilize_profile() pre-relaxation
step used to generate Fig. Ah (SteadyStateProfileDeviation.pdf).

This checks whether/how quickly the profile settles into a self-similar
decaying shape (the quasi-static assumption discussed in the manuscript --
that (1/C(r))*(dC(r)/dt) becomes spatially uniform) when starting from the
ideal steady-state shape with NO artificial pre-relaxation, at constant
temperature, over 5 permeation timescales (tau = 1/lambda = 1/(K(T)*G*R*T)).

The t/tau = 0 curve is exactly the idealized analytic log profile (that is
what permeation_sim.__init__ sets self.c to); later curves show how the
FDM-simulated profile departs from -- or returns to -- that same shape.

Output (in this script's directory):
  ProfileEvolution_NoRelax.pdf
  ProfileEvolution_NoRelax.csv
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import swets_K, Ratoms, permeation_sim, NovTube_blank_cooling

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(DATA_OUTDIR, exist_ok=True)

# --- Ampoule geometry: same VR = 150 case used in fig_permeation_eqn_numerical_error.py
#     (Figure 6 / Fig. Ah), so this is directly comparable to that figure's panel. ---
L_const = 0.0175          # wall thickness, cm (175 micron), matches other figures in this family
VR = 150                  # glass/gas volume ratio -- representative of ampoules in this work
VP = (VR + 1) ** 0.5
a = L_const / (-1 + VP)
b = L_const + a

T = 273 + 100              # constant temperature (K); 100 deg C, matches Fig. Ah

K = swets_K(T)
G = 2 / (a ** 2 * np.log(b / a))
tau = 1 / (G * K * Ratoms * T)   # permeation timescale, seconds

n_snapshots = 6                   # t/tau = 0, 1, 2, 3, 4, 5
colmap = plt.cm.viridis

# permeation_sim.__init__ already sets self.c to the idealized analytic log
# profile -- we deliberately do NOT call wb.stabilize_profile() here, since
# that is the pre-relaxation step used for Fig. Ah that we want to skip.
wb = permeation_sim(a=a, b=b, n0=1, T=T, cooling_func=NovTube_blank_cooling, He=4)

fig, ax = plt.subplots()
records = []

for i in range(n_snapshots):
    c_over_cgas = wb.c / (wb.ngas / (wb.h * np.pi * wb.a ** 2))
    style = '--' if i == 0 else '-'
    ax.plot(1E4 * (wb.r - wb.a), c_over_cgas, style,
            color=colmap(i / (n_snapshots - 1)),
            marker='o', markersize=3,
            label=(fr'$t/\tau_P$ = {i} (ideal profile, no relaxation)' if i == 0
                   else fr'$t/\tau_P$ = {i}'))
    for rr, cc in zip(wb.r, c_over_cgas):
        records.append({'t_over_tau': i, 'r_um': 1E4 * (rr - wb.a), 'C_over_Cgas': cc})
    if i < n_snapshots - 1:
        wb.hold_T(T, tau, verbose=True)

ax.set_title('Evolution of He Concentration Profile, No Initial Relaxation\n'
             fr'$V_\mathrm{{glass}}/V_\mathrm{{gas}}$ = {VR}, $T$ = {T-273:.0f}$\degree$C, '
             fr'$\tau_P$ = {tau/60:.1f} min')
ax.set_xlabel('Distance from Inner Wall (µm)')
ax.set_ylabel(r'$C/C_\mathrm{gas}$')
ax.legend(fontsize=8)
ax.grid()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'ProfileEvolution_NoRelax.pdf'), dpi=300)
plt.close(fig)

pd.DataFrame(records).to_csv(os.path.join(DATA_OUTDIR, 'ProfileEvolution_NoRelax.csv'), index=False)
print(f"tau (permeation timescale) = {tau:.1f} s = {tau/60:.2f} min")
print("Done -- wrote ProfileEvolution_NoRelax.pdf and .csv")
