"""
Partial retention plots (He age vs isothermal holding time) for apatite
and goethite.

Outputs:
  PRP_apatite.pdf                       – Durango apatite (a = 150 µm)
  PRP_goethite_winsor.pdf               – Winsor goethite (isotropic diffusion)
  PRP_goethite_winsor_asUncertainty.pdf – same reference line, derived from
                                           the measured (M) Stage 1 regression
                                           only (an LB/UB band was tried but
                                           was visually indistinguishable, so
                                           this output is intentionally
                                           identical to PRP_goethite_winsor.pdf)
  PRP_goethite_bassal.pdf     – Goethite defect-free He channel (Bassal 2022)

The Winsor goethite curve's D0/Ea used to be hardcoded copies of a
one-off Excel regression. They're now read from
Figures/generated/data/stage1_regression_cache.json, written by
prepare_regression_cache.py (run that first if this script complains
it's missing) -- see that script's docstring for why.
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import wolfEQ, wolfEQM, make_grid
from thermochr_utils import load_stage1_cache
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)
stage1 = load_stage1_cache()

ts_log = 10 ** np.linspace(4, 9, 100)   # years
Ts_C = np.array([25, 50, 75, 100])       # °C

# ---------------------------------------------------------------------------
# Figure 1: Durango apatite (Farley 2000 parameters)
# ---------------------------------------------------------------------------
D0 = 10 ** 1.5    # cm^2/s
a = 150 / 1E4    # cm
Ea = 33000        # cal/mol  (R = 1.987)
Ts_K = Ts_C + 273

fig, ax = plt.subplots()
for T in Ts_K:
    D_a2 = (D0 / a ** 2) * np.exp(-Ea / (1.987 * T))
    Heage = [wolfEQ(t=t, D_a2=D_a2) for t in ts_log]
    ax.loglog(ts_log, Heage, label=f'{T - 273}°C')
make_grid()
ax.set_xlabel('Isothermal Holding Time (years)')
ax.set_ylabel('He Age (years)')
ax.set_title('Durango Partial He Retention Plot (a = 150 µm)')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PRP_apatite.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: Winsor goethite (isotropic, Dodson-style parameters)
# ---------------------------------------------------------------------------
D0_a2_win = stage1['M']['D0_a2']   # s^-1, central Stage 1 regression (see prepare_regression_cache.py)
Ea_win = stage1['M']['Ea_cal_mol']  # cal/mol

fig, ax = plt.subplots()
for T in Ts_K:
    D_a2 = D0_a2_win * np.exp(-Ea_win / (1.987 * T))
    Heage = [wolfEQ(t=t, D_a2=D_a2) for t in ts_log]
    ax.loglog(ts_log, Heage, label=f'{T - 273}°C')
make_grid()
ax.set_xlabel('Isothermal Holding Time (years)')
ax.set_ylabel('He Age (years)')
ax.set_title('Winsor Goethite He Retention Plot')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PRP_goethite_winsor.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2b: "treatment as uncertainty" companion. An earlier version of
# this plot shaded a band spanning the lower-bound/upper-bound Stage 1
# regressions, but that band proved visually indistinguishable from the
# central curve -- so, per instruction, this reference line (like the
# others) is derived from the measured (M) value only, and this output is
# intentionally identical to PRP_goethite_winsor.pdf.
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
for T in Ts_K:
    D_a2 = D0_a2_win * np.exp(-Ea_win / (1.987 * T))
    Heage = [wolfEQ(t=t, D_a2=D_a2) for t in ts_log]
    ax.loglog(ts_log, Heage, label=f'{T - 273}°C')
    eqmage, eqtime = wolfEQM(D_a2)
    print(f'At {T - 273}°C, equilibrium He age = {eqmage:.2f} yr, time to equilibrate = {eqtime:.2f} yr')
make_grid()
ax.set_xlabel('Isothermal Holding Time (years)')
ax.set_ylabel('He Age (years)')
ax.set_title('Winsor Goethite Helium Retention Plot')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PRP_goethite_winsor_asUncertainty.pdf'), dpi=300)
plt.close(fig)

D_a2 = D0_a2_win * np.exp(-Ea_win / (1.987 * (273.15 + 40)))
eqmage, eqtime = wolfEQM(D_a2)

Heage_100Ma_40C = wolfEQ(t=1E8, D_a2=D_a2)

print(f'Winsor goethite equilibrium He age at 40C: {eqmage:.2f} yr, and times to equilibrate (years): {eqtime:.2f}')
print(f"Winsor t/t0 at 100 Ma 40C: {Heage_100Ma_40C/1E8:.3f}")
# ---------------------------------------------------------------------------
# Figure 3: Goethite defect-free He channel (Bassal et al. 2022)
# ---------------------------------------------------------------------------
D0_bas = 13.4E-4   # cm^2/s
Ea_bas = 0.43 * 96485  # J/mol  (use R = 8.314)
a_bas = 100 / 1E4   # cm

ts_short = np.linspace(1 / 365, 1, 100)   # years (sub-annual to 1 yr)

fig, ax = plt.subplots()
for T in Ts_K:
    D_a2 = (D0_bas / a_bas ** 2) * np.exp(-Ea_bas / (8.314 * T))
    Heage = [wolfEQ(t=t, D_a2=D_a2) for t in ts_short]
    ax.loglog(ts_short, Heage, label=f'{T - 273}°C')
make_grid()
ax.set_xlabel('Isothermal Holding Time (years)')
ax.set_ylabel('He Age (years)')
ax.set_title('Defect-Free He Channel Diffusion in Goethite\n'
             'Retention Plot a = 100 µm (Bassal et al. 2022)')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PRP_goethite_bassal.pdf'), dpi=300)
plt.close(fig)
