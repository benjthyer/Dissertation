"""
fig_bounding_titanite_sim.py -- illustration of the bounding method.

Forward simulation of a single isothermal hold at 350 C of an encapsulated,
retentive phase: titanite, spherical diffusion domain of radius a = 150 um,
D0 = 60 cm^2/s, Ea = 44.6 kcal/mol (Reiners and Farley, 1999), in a silica
ampoule with outer/inner diameter 1.0/0.8 mm (G from Masaryk, 1968; helium
permeability of Swets et al., 1961, as in thermochr_utils.swets_K).

Reservoirs (all as fractions of the crystal's total helium):
  omega(t)  cumulative helium released by the crystal (spherical volume
            diffusion, isothermal, homogeneous initial distribution)
  n(t)      helium in the ampoule:  dn/dt = d(omega)/dt - lambda n
            (first-order, steady-state permeation, main-text Eq. permode)
  m(t)      cumulative helium permeated (measured) = n0 + omega - n
The ampoule starts the hold holding inherited helium n0 = f n_ss(t_ref),
where n_ss(t) = (d omega/dt)/lambda is the quasi-steady inventory and
t_ref = 5/lambda; panel (a) f = 0.5, panel (b) f = 10 (deliberately
provocative: m then exceeds omega throughout).

The figure shows only observable or bounded quantities: omega, m, n and the
upper bound on the ampoule's inventory from the measured m alone,
n_UB = m/(lambda t - 1) (main-text Eq. steadystate), drawn for lambda t > 4.
(The simulation still checks the derived bounds on omega and prints them.)

Output: generated/BoundingMethodTitaniteSim.{pdf,png}
        generated/data/bounding_titanite_sim_n0x*.csv
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
import insitu_lambda as L

apply_style()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(os.path.join(OUT, 'data'), exist_ok=True)

# ---------------------------------------------------------------- parameters
T_C = 350.0
TK = T_C + 273.15
D0, EA_CAL = 60.0, 44.6e3              # cm^2/s, cal/mol (Reiners and Farley, 1999)
A_CM = 150e-4                          # 150 um radius
OD_UM, ID_UM = 1000.0, 800.0
LT_MIN_UB = 4.0                        # n_UB drawn only for lambda t > 4
N0_FACTORS = (0.0, 10.0)               # n0 = factor * n_ss(t_ref); one panel each
T_END = 30 * 86400.0                   # s

D_a2 = D0 * np.exp(-EA_CAL / (1.987 * TK)) / A_CM ** 2          # s^-1
G = L.geometric_factor(ID_UM, OD_UM)
lam = float(L.lambda_predicted(TK, G))                          # s^-1


def F_sphere(t):
    """Fractional loss from a sphere (Crank, 1975): short-time form for
    D t/a^2 < 0.1 (all of this simulation), series otherwise."""
    x = D_a2 * np.atleast_1d(np.asarray(t, float))
    out = 6 / np.sqrt(np.pi) * np.sqrt(x) - 3 * x
    big = x >= 0.1
    if big.any():
        k = np.arange(1, 200)[:, None]
        out[big] = 1 - 6 / np.pi ** 2 * np.sum(np.exp(-k ** 2 * np.pi ** 2 * x[big]) / k ** 2, axis=0)
    return out


def dF_dt(t):
    """Release rate (short-time form, valid here since D t/a^2 << 0.1)."""
    x = D_a2 * np.asarray(t, float)
    return D_a2 * (3 / np.sqrt(np.pi * x) - 3)


t = np.concatenate([[0.0], np.logspace(0, np.log10(T_END), 6000)])   # s
omega = F_sphere(t)
t_ref = 5 / lam
n_ss = dF_dt(np.maximum(t, 1e-9)) / lam
lt = lam * t


def simulate(n0_factor):
    """n(t), m(t) and the bounds on omega for an inherited n0 = factor * n_ss(t_ref)."""
    n0 = n0_factor * float(dF_dt(t_ref) / lam)
    n = np.empty_like(t)
    n[0] = n0
    for k in range(len(t) - 1):          # exact exponential integrator
        dt = t[k + 1] - t[k]
        dw = omega[k + 1] - omega[k]
        e = np.exp(-lam * dt)
        n[k + 1] = n[k] * e + dw * (1 - e) / (lam * dt)
    m = n0 + omega - n
    upper = np.full_like(t, np.nan)
    upper[lt > 1] = m[lt > 1] * (1 + 1 / (lt[lt > 1] - 1))
    lower = m - n0
    ok = lt >= 5
    print(f'--- n0 = {n0_factor} n_ss(5/lambda) = {n0:.3e}: upper bound violated for lambda t >= 5: '
          f'{bool(np.any(omega[ok] > upper[ok] * (1 + 1e-9)))}; lower violated: {bool(np.any(omega < lower - 1e-15))}')
    for d_ in (5, 20, 100, 1000):
        k = np.searchsorted(lt, d_)
        print(f'lambda t = {d_:5d}: t = {t[k] / 3600:7.1f} h, (upper - omega)/omega = '
              f'{(upper[k] - omega[k]) / omega[k]:.3f}, (m - omega)/omega = {(m[k] - omega[k]) / omega[k]:+.3f}')
    pd.DataFrame(dict(t_s=t, lam_t=lt, omega=omega, n=n, m=m, n_ss=n_ss, omega_upper=upper,
                      omega_lower=lower)).to_csv(
        os.path.join(OUT, 'data', f'bounding_titanite_sim_n0x{n0_factor:g}.csv'), index=False)
    return n0, n, m, upper, lower


print(f'D/a2 = {D_a2:.3e} s^-1; G = {G:.0f} cm^-2; lambda = {lam:.3e} s^-1 '
      f'(1/lambda = {1 / lam / 60:.1f} min)')
print(f'omega at 1/lambda, 5/lambda, 1 d, 30 d = {F_sphere(1 / lam)[0]:.2e}, {F_sphere(5 / lam)[0]:.2e}, '
      f'{F_sphere(86400)[0]:.2e}, {F_sphere(T_END)[0]:.2e}')

# ---------------------------------------------------------------- figure
th = t / 3600
sel = th > 0
band = sel & (lt >= 5)
pre = sel & (lt > 1) & (lt < 5)
fig, axes = plt.subplots(2, 1, figsize=(6.4, 9.6), sharex=True)
for ax, factor, tag in zip(axes, N0_FACTORS, ('(a)', '(b)')):
    n0, n, m, upper, lower = simulate(factor)
    nub = np.full_like(t, np.nan)
    show = sel & (lt > LT_MIN_UB)
    nub[show] = m[show] / (lt[show] - 1)                    # Eq. (steadystate): n <= m/(lambda t - 1)
    ax.plot(th[sel], omega[sel], color='#e08a1e', lw=2.4, label=r'$\omega$ (released by titanite)')
    ax.plot(th[sel], m[sel], color='tab:blue', lw=2.0, label=r'$m$ (measured)')
    ax.plot(th[sel], n[sel], color='#6f6f6f', lw=2.0, label=r'$n$ (in ampoule)')
    ax.plot(th, nub, color='#6f6f6f', lw=1.6, ls='--',
            label=r'$n^{UB} = m/(\lambda t - 1)$, $\lambda t > %g$' % LT_MIN_UB)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(1 / 60, T_END / 3600)
    ax.set_ylim(1e-6, 0.1)
    ax.set_ylabel('Helium (fraction of crystal total)')
    ax.text(0.97, 0.05, f'{tag}  $n_0 = {factor:g}\\,n_{{ss}}(5/\\lambda)$' if factor != 0 else f'{tag}  $n_0 = 0$', transform=ax.transAxes,
            ha='right', va='bottom', fontsize=12)
    ax.grid(True, which='major', alpha=0.4)
axes[0].legend(fontsize=8.5, loc='upper left')
axes[0].set_title('Simulated Helium Release of Encapsulated Titanite\n(a = 150 µm) Held at 350 °C', fontsize=15)
axes[1].set_xlabel('Time at 350 °C (h)')
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUT, f'BoundingMethodTitaniteSim.{ext}'), dpi=300)
print('ok')
