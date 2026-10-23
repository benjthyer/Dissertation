"""
Affinity-aware training activation (Eq. eq:y) in units of the per-phase scale c.

    y/c = g/c                              g >= 0  (present: y is the abundance n)
        = tanh(g/c) + eps * g/c            g <  0  (absent: saturates near -1)

drawn for eps = 0.02 (the training value, ngibbs ACTIVATION_TRAIN_DEFAULTS) over
g/c in [-3, 3], with eps = 0 (the reported signed output) for reference and the
-3c floor applied to the ground-truth labels marked.

Writes generated/fig_affinity_activation.pdf (300 dpi). No ngibbs needed.
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / 'generated' / 'fig_affinity_activation.pdf'
EPS = 0.02
X = np.linspace(-3, 3, 2001)

plt.rcParams.update({'font.size': 10, 'axes.labelsize': 11, 'xtick.labelsize': 9.5,
                     'ytick.labelsize': 9.5, 'legend.fontsize': 9.5, 'pdf.fonttype': 42,
                     'axes.spines.top': False, 'axes.spines.right': False})


def activation(x, eps):
    return np.where(x >= 0, x, np.tanh(x) + eps * x)


fig, ax = plt.subplots(figsize=(4.6, 3.3), layout='constrained')
ax.axhline(0, color='0.75', lw=0.8, zorder=0)
ax.axvline(0, color='0.75', lw=0.8, zorder=0)
ax.axhline(-1, color='0.6', lw=0.8, ls=':', zorder=0)
ax.axvline(-3, color='0.45', lw=1.0, ls='-.', zorder=0)
ax.plot(X, activation(X, 0.0), color='0.45', lw=1.4, ls='--', label=r'$\varepsilon = 0$')
ax.plot(X, activation(X, EPS), color='#1f6fb4', lw=2.0, label=rf'$\varepsilon = {EPS:g}$')
ax.text(-2.9, 2.9, r'label floor, $g = -3c$', ha='left', va='top', fontsize=9, color='0.3')
ax.set_xlim(-3.2, 3)
ax.set_ylim(-1.3, 3)
ax.set_xlabel(r'$g/c$')
ax.set_ylabel(r'$y/c$')
ax.legend(loc='upper left', frameon=False, bbox_to_anchor=(0.02, 0.86))
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=300)
print(f'-> {OUT}')
