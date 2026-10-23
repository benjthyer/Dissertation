"""
Signed phase-abundance target along the HeFESTo Htz_transition transect
(20-25 GPa, 10 MPa steps): labels built from HeFESTo's own phase affinities
vs. labels built affinity-free by extrapolating dn/dP through zero.

    g = n                    phase present
    g = -k * A               phase absent, affinity route  (k = |dn/dP| / |dA/dP|)
    g = -|dn/dP| * d         phase absent, extrapolation route (d = distance to boundary)
    y = h(max(g, -3c)),  h(g) = g (g >= 0),  c * tanh(g / c) (g < 0)
    c = clip(median|dn/dP| * DP, max(n) / 5, max(n)),  DP = 0.25 GPa

Plotted as y/c so the panels share one axis.

Input: affinity_transect.csv (written from Htz_transition's qout/fort.99), with
columns P, T and n_<phase>, A_<phase> (kJ/mol-atom, HeFESTo sign: positive =
undersaturated) and F_<phase> (0 present, 1 minimised affinity, 3 not evaluated).

Usage (defaults: generated/affinity_transect.csv -> generated/fig_affinity_vs_extrapolation.pdf):
    python fig_affinity_vs_extrapolation.py [path/to/affinity_transect.csv] [out.pdf]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_style import apply_style  # noqa: E402

HERE = Path(__file__).resolve().parent
CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'generated' / 'affinity_transect.csv'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / 'generated' / 'fig_affinity_vs_extrapolation.pdf'

PHASES = ['garnet', 'gamma-iron', 'akimotoite']
DP = 0.25            # GPa, pressure window that sets c
CLIP = 3.0           # labels clipped at g = -CLIP * c
FIGSIZE = (6.4, 5.4)   # default width (scale = 1 in plot_style); slightly taller for title + legend

BLUE, ORANGE, GREY = '#2a78d6', '#eb6834', '#a3a29c'


def h(g, c):
    g = np.maximum(g, -CLIP * c)
    return np.where(g >= 0, g, c * np.tanh(g / c))


def crossings(P, n, F, A):
    """Per saturation crossing: present-side slope s, |dA/dP| and boundary P*
    (from the affinity), plus the boundary placed from the present side only."""
    pres = F == 0
    out = []
    for i in np.where(pres[1:] != pres[:-1])[0]:
        entering = pres[i + 1]
        p0, p1 = (i + 1, i + 2) if entering else (i, i - 1)          # nearest present rows
        step = (lambda j: j - 1) if entering else (lambda j: j + 1)   # walk into the absent side
        ab, j = [], step(p0)
        while 0 <= j < len(P) and len(ab) < 3:
            if F[j] == 1:
                ab.append(j)
            j = step(j)
        ab = np.array(sorted(ab))
        dadp = abs(np.polyfit(P[ab], A[ab], 1)[0])
        s = abs(n[p1] - n[p0]) / abs(P[p1] - P[p0])
        # affinity-free boundary: extrapolate n to zero, clamped to the bracketing step
        direction = np.sign(P[p1] - P[p0])
        p_star = P[p0] - direction * n[p0] / s
        lo, hi = sorted((P[p0], P[p0] - direction * abs(P[1] - P[0])))
        out.append(dict(s=s, dadp=dadp, p_star=float(np.clip(p_star, lo, hi))))
    return out


def targets(df, phase):
    P = df['P'].to_numpy()
    n = df[f'n_{phase}'].to_numpy()
    A = df[f'A_{phase}'].to_numpy()
    F = df[f'F_{phase}'].to_numpy()
    cr = crossings(P, n, F, A)

    k = np.median([x['s'] / x['dadp'] for x in cr])
    s_med = np.median([x['s'] for x in cr])
    c = float(np.clip(s_med * DP, n.max() / 5, n.max()))

    g_aff = np.where(F == 0, n, np.where(F == 1, -k * A, np.nan))
    g_ext = n.astype(float).copy()
    for j in np.where(F != 0)[0]:
        d, s = min((abs(P[j] - x['p_star']), x['s']) for x in cr)
        g_ext[j] = -s * d
    return P, h(g_aff, c) / c, h(g_ext, c) / c, c


def main():
    apply_style()
    df = pd.read_csv(CSV)

    fig, axes = plt.subplots(1, len(PHASES), figsize=FIGSIZE, sharex=True, sharey=True)
    for ax, phase in zip(axes, PHASES):
        P, y_aff, y_ext, c = targets(df, phase)
        ax.axhline(0, color=GREY, lw=0.8, zorder=0)
        ax.axhline(-1, color=GREY, lw=0.8, ls=':', zorder=0)
        ax.plot(P, y_aff, color=BLUE, lw=2.4, label='y/c from scaled affinities')
        ax.plot(P, y_ext, color=ORANGE, lw=1.8, ls=(0, (4, 2)),
                label='y/c from extrapolated dn/dP')
        # Two-line panel titles: three panels share 6.4 in at the style's title size.
        ax.set_title(f'{phase.capitalize()}\n(c={c:.3f})')
        ax.spines[['top', 'right']].set_visible(False)

    axes[0].set_ylabel('y/c')
    axes[0].set_xlim(df['P'].min(), df['P'].max())
    axes[0].xaxis.set_major_locator(MultipleLocator(2))
    fig.supxlabel('P (GPa)', fontsize=plt.rcParams['axes.labelsize'], y=0.015)

    handles, labels = axes[0].get_legend_handles_labels()
    # Two lines: at the style's suptitle size the one-line title is wider than 6.4 in.
    fig.suptitle('HeFESTo Computed Phase\nAbundances and Affinities', y=0.995)
    fig.legend(handles, labels, loc='upper center', ncol=1, frameon=False,
               bbox_to_anchor=(0.5, 0.865))
    fig.subplots_adjust(top=0.615, bottom=0.14, left=0.13, right=0.98, wspace=0.12)
    fig.savefig(OUT, dpi=300)
    print(f'wrote {OUT}')


if __name__ == '__main__':
    main()
