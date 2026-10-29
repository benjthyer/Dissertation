"""
Schematic deformation history of the sheared magnetite pegmatoid of field
photo 60 (Chapter 5), digitized from the author's three pencil sketches
(2026-10-27). Coordinates are traced in each sketch's own pixel frame
(x right, y down, ~1500 x 2000 px photos of the sketches); each panel keeps
the orientation it was drawn in.
Sketch photos: Figures/source/photo60_sketches/photo60_sketch_event{1_lens,2_sigmoid,3_fault}.jpg
(pixelated parts of the sketch photos are neighbouring drawings, ignored).

Order of events (left to right):
  1. Mafic pegmatitic melt accumulates in lenses in migmatized sediment
  2. Synmagmatic plastic deformation produces sigmoid geometry
  3. Post-magmatic brittle failure along annealed fault

Output: Chapter5/Figures/generated/photo60_deformation_schematic.pdf
Run from anywhere:  python3 Chapter5/Figures/fig_photo60_deformation.py
Requires matplotlib and scipy.
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, Polygon
import numpy as np
from scipy.interpolate import splev, splprep

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'generated', 'photo60_deformation_schematic.pdf')

# --- fonts: Latin Modern (the thesis font) if matplotlib can find it --------------
for f in font_manager.findSystemFonts():
    if os.path.basename(f).lower().startswith('lmroman10-'):
        font_manager.fontManager.addfont(f)
if any(f.name == 'Latin Modern Roman' for f in font_manager.fontManager.ttflist):
    plt.rcParams['font.family'] = 'Latin Modern Roman'
else:
    plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 9
plt.rcParams['pdf.fonttype'] = 3   # Type 3: LM Roman is an OTF/CFF font, which Type 42 embeds badly

INK = '#262626'          # pencil lines
LAYER = '#5a5a5a'        # migmatite layering
FAINT = '#9a9a9a'        # lightly drawn lines in the sketches
PEG = '#c98a4b'          # pegmatoid fill (rusty, as in photo 60)
PEG_ALPHA = 0.55


def smooth(pts, n=200, s=None):
    """Smooth open curve through traced points."""
    pts = np.asarray(pts, float)
    k = min(3, len(pts) - 1)
    tck, _ = splprep(pts.T, s=len(pts) * 40 if s is None else s, k=k)
    x, y = splev(np.linspace(0, 1, n), tck)
    return np.column_stack([x, y])


def line(ax, pts, color=INK, lw=1.3, ls='-', s=None, z=3):
    c = smooth(pts, s=s)
    ax.plot(c[:, 0], c[:, 1], color=color, lw=lw, ls=ls, solid_capstyle='round',
            zorder=z)
    return c


def body(ax, edge_a, edge_b, fill=PEG, alpha=PEG_ALPHA, color=INK, lw=1.3, z=2):
    """Lens bounded by two edges that share their end points (sharp tips)."""
    a = line(ax, edge_a, color=color, lw=lw, z=z + 1)
    b = line(ax, edge_b, color=color, lw=lw, z=z + 1)
    ax.add_patch(Polygon(np.vstack([a, b[::-1]]), closed=True, fc=fill, ec='none',
                         alpha=alpha, zorder=z))


def shear_arrow(ax, tail, head, color=INK):
    ax.add_patch(FancyArrowPatch(tail, head, arrowstyle='-|>', mutation_scale=11,
                                 lw=1.3, color=color, zorder=5,
                                 shrinkA=0, shrinkB=0))


def panel(ax, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(ylim[1], ylim[0])      # image coordinates: y down
    ax.set_aspect('equal')
    ax.axis('off')


# ----------------------------------------------------------------------------------
# Event 1 (third sketch): pegmatitic lens in layered migmatite
def event1(ax):
    upper = [(430, 710), (560, 775), (700, 850), (850, 950), (1000, 1070),
             (1140, 1240), (1235, 1380), (1268, 1460), (1260, 1510)]
    lower = [(430, 710), (470, 840), (520, 950), (620, 1070), (760, 1200),
             (900, 1325), (1020, 1415), (1130, 1485), (1260, 1510)]
    body(ax, upper, lower)
    # migmatite layering wrapping the lens
    line(ax, [(805, 690), (840, 730), (880, 800), (960, 860), (1060, 920),
              (1150, 990), (1215, 1060), (1255, 1075)], color=LAYER, lw=1.1)
    line(ax, [(300, 1090), (370, 1140), (470, 1230), (570, 1330), (670, 1420),
              (770, 1490), (860, 1560), (905, 1650), (920, 1720)], color=LAYER, lw=1.1)
    line(ax, [(230, 1280), (290, 1340), (390, 1395), (480, 1490), (580, 1590),
              (660, 1655), (740, 1720)], color=LAYER, lw=1.1)
    line(ax, [(360, 940), (400, 1040), (480, 1140), (580, 1230), (680, 1320),
              (770, 1410)], color=FAINT, lw=0.8)
    line(ax, [(150, 1110), (230, 1180), (320, 1270), (420, 1360), (520, 1450)],
         color=FAINT, lw=0.8)
    panel(ax, (120, 1330), (640, 1800))


# Event 2 (first sketch): sigmoid. Made point-symmetric (180-degree rotation
# about its centre) at the author's request, so the top tapers to the same
# smooth "shark fin" as the bottom instead of the flat top drawn in the sketch.
SIG_C = np.array([765.0, 1040.0])
SIG_EDGE = [(840, 525), (760, 610), (660, 710), (580, 800), (540, 880),
            (528, 960), (555, 1040), (640, 1110), (740, 1170), (805, 1240),
            (815, 1320), (770, 1430), (690, 1555)]


def event2(ax):
    left = np.array(SIG_EDGE, float)
    right = 2 * SIG_C - left            # the other edge, rotated by 180 degrees
    a = line(ax, left, z=3)
    b = line(ax, right[::-1], z=3)
    ax.add_patch(Polygon(np.vstack([a, b[::-1]]), closed=True, fc=PEG, ec='none',
                         alpha=PEG_ALPHA, zorder=2))
    shear_arrow(ax, (345, 715), (715, 385))
    shear_arrow(ax, (1185, 1365), (815, 1695))
    panel(ax, (300, 1200), (340, 1740))


# Event 3 (second sketch): sigmoid truncated by a fault, offset fragment
def event3(ax):
    fault = np.array([(150, 665), (1420, 1615)])
    ax.plot(fault[:, 0], fault[:, 1], color=INK, lw=1.4, ls=(0, (6, 3)), zorder=4)
    left = [(450, 905), (390, 990), (372, 1090), (400, 1180), (470, 1250),
            (560, 1330), (660, 1430), (750, 1540), (775, 1640), (745, 1730),
            (715, 1790)]
    right = [(955, 1240), (948, 1330), (930, 1450), (895, 1560), (835, 1680),
             (765, 1760), (715, 1790)]
    a = line(ax, left)
    b = line(ax, right)
    ax.add_patch(Polygon(np.vstack([[(450, 905)], a, b[::-1], [(955, 1240)]]),
                         closed=True, fc=PEG, ec='none', alpha=PEG_ALPHA, zorder=2))
    # displaced fragment across the fault (drawn lightly in the sketch)
    frag_out = [(1150, 1095), (1225, 1150), (1290, 1260), (1318, 1380),
                (1300, 1480), (1275, 1545)]
    frag_in = [(1150, 1095), (1165, 1200), (1150, 1300), (1118, 1395)]
    c = line(ax, frag_out, color=FAINT, lw=1.2)
    d = line(ax, frag_in, color=FAINT, lw=1.2)
    ax.add_patch(Polygon(np.vstack([d, [(1275, 1545)], c[::-1]]), closed=True,
                         fc=PEG, ec='none', alpha=0.3, zorder=2))
    # shear arrows parallel to the fault
    shear_arrow(ax, (900, 470), (1290, 720))
    shear_arrow(ax, (520, 1600), (200, 1385))
    panel(ax, (140, 1440), (420, 1830))


LABELS = [
    'Mafic pegmatitic melt\naccumulates in lenses in\nmigmatized sediment',
    'Synmagmatic plastic\ndeformation produces\nsigmoid geometry',
    'Post-magmatic brittle\nfailure along\nannealed fault',
]


def main():
    fig = plt.figure(figsize=(5.5, 2.75))   # \textwidth = 5.5 in
    w, gap, x0, y0, h = 0.285, 0.0575, 0.0, 0.30, 0.69
    axes = [fig.add_axes([x0 + i * (w + gap), y0, w, h]) for i in range(3)]
    for ax, draw in zip(axes, (event1, event2, event3)):
        draw(ax)
    for i, (ax, lab) in enumerate(zip(axes, LABELS)):
        fig.text(x0 + i * (w + gap) + w / 2, y0 - 0.03, f'({i + 1}) ' + lab,
                 ha='center', va='top', linespacing=1.25)
    for i in range(2):
        xa = x0 + (i + 1) * w + i * gap + 0.008
        xb = x0 + (i + 1) * (w + gap) - 0.008
        fig.add_artist(FancyArrowPatch((xa, y0 + h / 2), (xb, y0 + h / 2),
                                       transform=fig.transFigure,
                                       arrowstyle='simple,head_width=7,head_length=7,tail_width=2.6',
                                       color='#7a7a7a', lw=0))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, bbox_inches='tight', pad_inches=0.02)
    fig.savefig(OUT.replace('.pdf', '.png'), dpi=200, bbox_inches='tight', pad_inches=0.02)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
