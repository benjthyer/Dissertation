"""
FTCS finite-difference simulation of He concentration profiles in silica glass
tube walls during a temperature step, for two initial conditions:

  1. Zero concentration throughout (cold/clean tube)
  2. Steady-state profile pre-equilibrated at 300°C

Both cases step to T2 = 100°C and run until Fo = {0.01, 0.1, 1.0}.

Outputs:
  FDM_diff_prof_zero_IC.pdf
  FDM_diff_prof_300C_IC.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import swets, Ratoms
from plot_style import apply_style
apply_style()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

Fos    = [0.01, 0.1, 0.25, 1]
colors = ['Red', 'Orange', 'Green', 'Blue', 'Violet']


def tube_FDM(T1, T2, x):
    """
    FTCS finite-difference model for He diffusion across a silica glass wall.

    T1 : float or non-numeric
        Initial condition temperature (°C).  Non-numeric → zero concentration.
    T2 : float
        Final temperature (°C) — sets boundary condition and diffusivity.
    x  : float
        Wall thickness (cm).

    Returns matplotlib Figure.
    """
    D  = swets('D', T2 + 273)
    S2 = swets('S', T2 + 273)
    dx = 1 / 1e4                        # 1 micron
    dt = 0.5 * (dx ** 2) / D            # stability upper bound
    xi = np.arange(0, x, dx)

    c_inner = S2 * Ratoms * (T2 + 273)  # inner BC: glass/gas equilibrium at T2

    t_stops = sorted([(Fo * xi[-1] ** 2) / D for Fo in Fos])

    print(
        f"D = {D:.3e} cm²/s, dx = {dx * 1e4:.2f} µm, "
        f"dt = {dt:.3e} s"
    )

    if isinstance(T1, (int, float)):
        S1 = swets('S', T1 + 273)
        c1 = S1 * Ratoms * (T1 + 273)
        c  = (xi / xi[-1]) * c1         # linear steady-state profile at T1
    else:
        c1 = 0.0
        c  = np.zeros_like(xi)          # zero IC

    fig, ax = plt.subplots()
    ax.plot(xi * 1e4, c, linestyle='--', color='Black',
            label='t = 0 min', alpha=0.5)

    c[-1] = c_inner
    current_t = 0.0
    steps     = 0
    color_idx = 0
    remaining = list(zip(t_stops, Fos))

    delta_c = (D * dt / dx ** 2) * (c[:-2] - 2 * c[1:-1] + c[2:])

    while remaining:
        t_stop, Fo = remaining[0]
        steps     += 1
        current_t += dt
        c[1:-1]   += delta_c
        c[0]       = 0.0       # outer BC: vacuum
        c[-1]      = c_inner   # inner BC: equilibrium
        delta_c    = (D * dt / dx ** 2) * (c[:-2] - 2 * c[1:-1] + c[2:])

        if current_t >= t_stop:
            ax.plot(xi * 1e4, c,
                    color=colors[color_idx], linewidth=2,
                    label=f'Fo = {Fo}, t = {current_t / 60:.1f} min')
            print(f"Fo = {Fo}: t = {current_t / 60:.2f} min, "
                  f"atoms = {np.sum(c):.3e}")
            remaining.pop(0)
            color_idx += 1

    print(f"Simulation finished after {steps} steps")

    # Initial and equilibrium reference lines
    ax.plot(xi * 1e4, (xi / xi[-1]) * c1,
            linestyle='--', color='Black', alpha=0.5)
    ax.plot(xi * 1e4, (xi / xi[-1]) * c_inner,
            linestyle=':', color='Black', alpha=0.8,
            label=f'EQM for T = {T2}°C')

    ax.set_xlabel('Distance from Vacuum (microns)')
    ax.set_ylabel('He Concentration (atoms/mL)')
    ax.set_title(
        f'He Concentration Profile Evolution\nafter {current_t / 60:.1f} min '
        f'at {T2}°C'
    )
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 1: zero initial condition
# ---------------------------------------------------------------------------
fig1 = tube_FDM(T1='zero', T2=100, x=0.02)
fig1.savefig(os.path.join(OUTDIR, 'FDM_diff_prof_zero_IC.pdf'), dpi=300)
plt.close(fig1)

# ---------------------------------------------------------------------------
# Figure 2: steady-state at 300°C initial condition
# ---------------------------------------------------------------------------
fig2 = tube_FDM(T1=300, T2=100, x=0.02)
fig2.savefig(os.path.join(OUTDIR, 'FDM_diff_prof_300C_IC.pdf'), dpi=300)
plt.close(fig2)
