"""
fig_schematic_sequence.py -- DRAFT schematics of permeation lag in a sealed
silica ampoule, drawn entirely as vector outlines and stacked vertically in
time order (each row is one step; time runs downward).

Notation: n_i is the helium in the ampoule at the END of step i (so step i
starts with n_{i-1}); m_i is the helium measured for step i; omega_i is the
helium released by the crystal during step i; (lambda t)_i is the step's
permeation rate constant times its duration.

  Schematic_Sequence3   cold - warm - cold, one equation per step
  Schematic_Sequence5   cold - warm - cold - warm - cold (permeation step
                        method): each cold step gives the inventories at both
                        of its ends, n_{i-1} = m_i / (1 - e^{-(lambda t)_i}) and
                        n_i = m_i / (e^{(lambda t)_i} - 1); each warm step then
                        gives omega_i = m_i + n_i - n_{i-1}
  Schematic_Bounding3   warm - warm - warm, long steps (bounding method):
                        n_i <= n_i^UB = m_i / ((lambda t)_i - 1), so
                        m_i - n_{i-1}^UB <= omega_i <= m_i + n_i^UB

Colours are tied to quantities: omega orange, m blue, ampoule helium grey.
The ampoule interior is tinted by step temperature.
Outputs: generated/<name>.{pdf,svg,png}
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, FancyArrowPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUT, exist_ok=True)
C_OMEGA, C_M, C_HE, C_GLASS, C_TXT = '#e08a1e', '#2b6cb0', '#6f6f6f', '#5a6b7a', '#333333'
TINT = {'cold': '#e3eefa', 'warm': '#fbe3dc'}
LABEL_COLOR = {'cold': '#2f6aa3', 'warm': '#b5452e'}
W, H, WALL = 6.6, 1.5, 0.24          # ampoule size (axis units)
EQ_FS = 12


def ampoule(ax, x0, y0, temp, n_dots, m_dots, rng, label, step):
    """Draw one step with the ampoule's lower-left corner at (x0, y0)."""
    yc = y0 + H / 2
    omega_on = temp == 'warm'
    ax.add_patch(FancyBboxPatch((x0, y0), W, H, boxstyle='round,pad=0,rounding_size=0.75',
                                fc='#f3f6f9', ec=C_GLASS, lw=1.5, zorder=1))
    ax.add_patch(FancyBboxPatch((x0 + WALL, y0 + WALL), W - 2 * WALL, H - 2 * WALL,
                                boxstyle='round,pad=0,rounding_size=0.53',
                                fc=TINT[temp], ec=C_GLASS, lw=0.9, zorder=2))
    cx0, cx1, tip = x0 + 0.75, x0 + 2.75, 0.38                   # zircon-like crystal
    cy0, cy1 = y0 + WALL + 0.12, y0 + H - WALL - 0.12
    ax.add_patch(Polygon([[cx0, yc], [cx0 + tip, cy0], [cx1 - tip, cy0], [cx1, yc],
                          [cx1 - tip, cy1], [cx0 + tip, cy1]], closed=True,
                         fc='#f6e7c8', ec='#8a6d3b', lw=1.2, zorder=3))
    for xe in (cx0 + tip, cx1 - tip):
        ax.plot([xe, xe], [cy0, cy1], color='#8a6d3b', lw=0.7, zorder=4)
    gx0, gx1 = cx1 + 0.25, x0 + W - WALL - 0.45                  # ampoule helium
    gy0, gy1 = y0 + WALL + 0.12, y0 + H - WALL - 0.12
    placed = 0
    while placed < n_dots:
        px, py = rng.uniform(gx0, gx1), rng.uniform(gy0, gy1)
        if omega_on and px < gx0 + 1.15:
            continue
        if px > gx1 - 0.9 and abs(py - yc) < 0.18:
            continue
        ax.add_patch(Circle((px, py), 0.065, fc=C_HE, ec='none', zorder=4))
        placed += 1
    if omega_on:
        ax.add_patch(FancyArrowPatch((cx1 - 0.12, yc), (gx0 + 0.9, yc), arrowstyle='-|>',
                                     mutation_scale=14, lw=2.0, color=C_OMEGA, zorder=6))
        ax.text(cx1 + 0.55, cy1 + 0.02, rf'$\omega_{{{step}}}$', color=C_OMEGA, fontsize=13,
                ha='center', va='top', zorder=7)
    ax.add_patch(FancyArrowPatch((gx1 - 0.7, yc), (x0 + W + 1.1, yc), arrowstyle='-|>',
                                 mutation_scale=14, lw=1.4 + 0.25 * m_dots ** 0.8, color=C_M, zorder=6))
    ax.text(x0 + W + 0.55, yc + 0.12, rf'$m_{{{step}}}$', color=C_M, fontsize=13, ha='center', va='bottom')
    placed = 0
    while placed < m_dots:
        px, py = rng.uniform(x0 + W + 1.3, x0 + W + 2.4), rng.uniform(yc - 0.5, yc + 0.5)
        ax.add_patch(Circle((px, py), 0.065, fc=C_M, ec='none', alpha=0.85, zorder=4))
        placed += 1
    ax.text(x0 + 0.15, y0 + H + 0.08, label, ha='left', va='bottom', fontsize=10.5,
            color=LABEL_COLOR[temp])
    return yc


def figure(name, seq, gap_eqs=None, right_eqs=None, left_eqs=None, top_eq=None, seed=7):
    """seq: list of (temp, n_dots, m_dots).  gap_eqs[i] is written in the gap
    between rows i and i+1 beside a grey carry arrow; right_eqs / left_eqs are
    written beside each row (None to skip); top_eq goes above the first row."""
    rng = np.random.default_rng(seed)
    nrow = len(seq)
    gap = 1.25 if gap_eqs else 0.95
    left = 5.4 if left_eqs else 0.0
    x0 = left + 0.3
    top = 0.9 if top_eq else 0.45
    height = nrow * H + (nrow - 1) * gap + 0.6 + top
    right = x0 + W + 2.8 + (4.8 if right_eqs else 0.2)
    fig, ax = plt.subplots(figsize=(right * 0.55, height * 0.55))
    ax.set_xlim(0, right)
    ax.set_ylim(-0.3, height - 0.3)
    ax.set_aspect('equal')
    ax.axis('off')
    ycs = []
    for i, (temp, n_dots, m_dots) in enumerate(seq):
        y0 = height - 0.6 - top - (i + 1) * H - i * gap
        kind = 'Permeation' if temp == 'cold' else 'Experimental'
        ycs.append(ampoule(ax, x0, y0, temp, n_dots, m_dots, rng, f'{kind} Step {i + 1}', i + 1))
        if right_eqs and right_eqs[i]:
            ax.text(x0 + W + 2.9, ycs[-1], right_eqs[i], ha='left', va='center', fontsize=EQ_FS, color=C_TXT)
        if left_eqs and left_eqs[i]:
            ax.text(x0 - 0.3, ycs[-1], left_eqs[i], ha='right', va='center', fontsize=EQ_FS - 0.5, color=C_TXT)
    xa = x0 + W * 0.62
    if gap_eqs:
        for i in range(nrow - 1):
            ax.annotate('', xy=(xa, ycs[i + 1] + H / 2 - 0.02), xytext=(xa, ycs[i] - H / 2 + 0.02),
                        arrowprops=dict(arrowstyle='-|>', color=C_HE, lw=1.2))
            ax.text(xa + 0.2, (ycs[i] + ycs[i + 1]) / 2, gap_eqs[i], ha='left', va='center',
                    fontsize=EQ_FS - 0.5, color=C_TXT)
    if top_eq:
        ax.annotate('', xy=(xa, ycs[0] + H / 2 - 0.02), xytext=(xa, ycs[0] + H / 2 + 0.85),
                    arrowprops=dict(arrowstyle='-|>', color=C_HE, lw=1.2))
        ax.text(xa + 0.2, ycs[0] + H / 2 + 0.45, top_eq, ha='left', va='center',
                fontsize=EQ_FS - 0.5, color=C_TXT)
    fig.tight_layout()
    for ext in ('pdf', 'svg', 'png'):
        fig.savefig(os.path.join(OUT, f'{name}.{ext}'), dpi=300, bbox_inches='tight')
    plt.close(fig)


def lt(i):
    return rf'(\lambda t)_{{{i}}}'


# ---- 3-step: one equation per step (permeation step method in brief)
figure('Schematic_Sequence3',
       [('cold', 9, 2), ('warm', 22, 8), ('cold', 15, 3)],
       right_eqs=[rf'$n_1 = \dfrac{{m_1}}{{e^{{{lt(1)}}} - 1}}$',
                  r'$\omega_2 = m_2 + n_2 - n_1$',
                  rf'$n_2 = \dfrac{{m_3}}{{1 - e^{{-{lt(3)}}}}}$'])

# ---- 5-step: permeation step method
gap5 = [rf'$n_1 = \dfrac{{m_1}}{{e^{{{lt(1)}}} - 1}}$',
        rf'$n_2 = \dfrac{{m_3}}{{1 - e^{{-{lt(3)}}}}}$',
        rf'$n_3 = \dfrac{{m_3}}{{e^{{{lt(3)}}} - 1}}$',
        rf'$n_4 = \dfrac{{m_5}}{{1 - e^{{-{lt(5)}}}}}$']
figure('Schematic_Sequence5',
       [('cold', 9, 2), ('warm', 22, 8), ('cold', 15, 3), ('warm', 26, 9), ('cold', 18, 3)],
       gap_eqs=gap5,
       right_eqs=[None, r'$\omega_2 = m_2 + n_2 - n_1$', None, r'$\omega_4 = m_4 + n_4 - n_3$', None])

# ---- bounding method: three long warm steps
gapB = [rf'$n_1 \leq n_1^{{UB}} = \dfrac{{m_1}}{{{lt(1)} - 1}}$',
        rf'$n_2 \leq n_2^{{UB}} = \dfrac{{m_2}}{{{lt(2)} - 1}}$']
leftB = [rf'$m_{i} - n_{{{i - 1}}}^{{UB}} \leq \omega_{i} \leq m_{i} + n_{i}^{{UB}}$' for i in (1, 2, 3)]
figure('Schematic_Bounding3',
       [('warm', 7, 14), ('warm', 6, 12), ('warm', 6, 11)],
       gap_eqs=gapB, left_eqs=leftB,
       top_eq=r'$n_0 \leq n_0^{UB}$  (from the preceding step)', seed=11)
print('ok')
