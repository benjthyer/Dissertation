"""
fig_schematic_demo.py -- DRAFT of one panel of the permeation-lag schematic:
an encapsulated zircon-like crystal releasing helium (omega) into a sealed
silica ampoule whose helium inventory n(t) permeates out of the wall into the
measured reservoir (m).  All elements are vector (no photo).

Output: generated/Schematic_MiddlePanel_demo.{pdf,svg,png}
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, FancyArrowPatch

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
C_OMEGA, C_M, C_HE, C_GLASS = '#e08a1e', '#2b6cb0', '#7a7a7a', '#5a6b7a'
rng = np.random.default_rng(3)

fig, ax = plt.subplots(figsize=(5.2, 2.6))
ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.set_aspect('equal'); ax.axis('off')

# ---- ampoule: outer and inner outlines (glass wall between them)
x0, y0, w, h, wall = 1.0, 1.2, 7.6, 1.8, 0.28
ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle='round,pad=0,rounding_size=0.9',
                            fc='#eef3f7', ec=C_GLASS, lw=1.6, zorder=1))
ax.add_patch(FancyBboxPatch((x0 + wall, y0 + wall), w - 2 * wall, h - 2 * wall,
                            boxstyle='round,pad=0,rounding_size=0.65',
                            fc='white', ec=C_GLASS, lw=1.0, zorder=2))
# sealed tip at the right end
ax.add_patch(Polygon([[x0 + w - 0.05, y0 + h / 2 - 0.12], [x0 + w + 0.35, y0 + h / 2],
                      [x0 + w - 0.05, y0 + h / 2 + 0.12]], closed=True,
                     fc='#eef3f7', ec=C_GLASS, lw=1.2, zorder=1))

# ---- zircon-like crystal: prism with pyramidal terminations
cx0, cx1, cy0, cy1, tip = 2.0, 4.6, y0 + wall + 0.12, y0 + h - wall - 0.12, 0.45
cyc = (cy0 + cy1) / 2
crystal = [[cx0, cyc], [cx0 + tip, cy0], [cx1 - tip, cy0], [cx1, cyc], [cx1 - tip, cy1], [cx0 + tip, cy1]]
ax.add_patch(Polygon(crystal, closed=True, fc='#f6e7c8', ec='#8a6d3b', lw=1.4, zorder=3))
for xe in (cx0 + tip, cx1 - tip):                       # prism edges
    ax.plot([xe, xe], [cy0, cy1], color='#8a6d3b', lw=0.8, zorder=4)

# ---- helium in the ampoule gas space, n(t)
gx0, gx1 = cx1 + 0.25, x0 + w - wall - 0.35
gy0, gy1 = y0 + wall + 0.15, y0 + h - wall - 0.15
placed = 0
while placed < 24:
    px, py = rng.uniform(gx0, gx1), rng.uniform(gy0, gy1)
    if px < gx0 + 1.05 and abs(py - (cyc + 0.05)) < 0.22:     # omega arrow
        continue
    if abs(px - (gx0 + 2.0)) < 0.18:                            # m arrow
        continue
    ax.add_patch(Circle((px, py), 0.07, fc=C_HE, ec='none', zorder=4)); placed += 1
ax.text((gx0 + gx1) / 2, y0 - 0.45, r'$n(t)$', ha='center', va='top', fontsize=14, color='#444')
ax.annotate('', xy=((gx0 + gx1) / 2, y0 + wall + 0.05), xytext=((gx0 + gx1) / 2, y0 - 0.4),
            arrowprops=dict(arrowstyle='-', color='#888', lw=0.8, ls=':'))

# ---- omega: crystal -> ampoule gas
ax.add_patch(FancyArrowPatch((cx1 - 0.15, cyc + 0.05), (gx0 + 0.9, cyc + 0.05),
                             arrowstyle='-|>', mutation_scale=16, lw=2.2, color=C_OMEGA, zorder=6))
ax.text((cx1 + gx0 + 0.9) / 2 - 0.15, y0 - 0.45, r'$\omega$', color=C_OMEGA, fontsize=15,
        ha='center', va='top', zorder=7)
ax.annotate('', xy=((cx1 + gx0 + 0.9) / 2 - 0.15, cyc - 0.08), xytext=((cx1 + gx0 + 0.9) / 2 - 0.15, y0 - 0.42),
            arrowprops=dict(arrowstyle='-', color=C_OMEGA, lw=0.8, ls=':'))

# ---- m: ampoule gas -> through the wall -> measured
mx = gx0 + 2.0
ax.add_patch(FancyArrowPatch((mx, gy1 - 0.1), (mx, y0 + h + 1.05),
                             arrowstyle='-|>', mutation_scale=16, lw=2.2, color=C_M, zorder=6))
ax.text(mx - 0.25, y0 + h + 0.75, r'$m$', color=C_M, fontsize=15, ha='right', va='center')
for _ in range(9):                                       # permeated, measurable helium
    ax.add_patch(Circle((mx + rng.uniform(0.35, 2.4), y0 + h + rng.uniform(0.35, 1.0)), 0.07,
                        fc=C_M, ec='none', alpha=0.8, zorder=4))
ax.text(mx + 1.4, y0 + h + 1.35, 'vacuum (measured)', fontsize=9, color=C_M, ha='center', va='center')

fig.tight_layout()
for ext in ('pdf', 'svg', 'png'):
    fig.savefig(os.path.join(OUT, f'Schematic_MiddlePanel_demo.{ext}'), dpi=300, bbox_inches='tight')
print('ok')
