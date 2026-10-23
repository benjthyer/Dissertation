"""
Thermal softplus activation (Eq. eq:smooth) and the centre-downweighting
weight of the presence loss (Eq. eq:sat) against the scaled affinity x = g / Upsilon0.

With Upsilon = a Upsilon0 (Section sec:anneal):
  n_tilde / Upsilon0 = a ln(1 + exp(x / a))           -> max(x, 0) as a -> 0
  c / w              = |tanh(x / a)|                   (BCE weight, Eq. eq:sat)

a -> 0 is drawn with a = 1e-4, the end of the second annealing episode.

Writes generated/fig_thermal_softplus.pdf (300 dpi).
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style

apply_style()

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
A_VALUES = [(1.0, r'$a = 1$'), (0.5, r'$a = 0.5$'), (1e-4, r'$a \to 0$ (ReLU)')]
COLORS = ['#1f77b4', '#ff7f0e', 'k']
X = np.linspace(-5, 5, 4001)


def softplus(z):
    return np.logaddexp(0.0, z)


def n_tilde(x, a):
    return a * softplus(x / a)


fig, (ax_n, ax_s) = plt.subplots(
    2, 1, sharex=True, figsize=(6.4, 6.4),
    gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.08})

for (a, label), color in zip(A_VALUES, COLORS):
    ax_n.plot(X, n_tilde(X, a), color=color, lw=2, label=label)
    ax_s.plot(X, np.abs(np.tanh(X / a)), color=color, lw=2)

ax_n.set_ylabel(r'$\tilde n / \Upsilon_0$')
ax_n.set_xlim(-5, 5)
ax_n.set_ylim(0, 5)
ax_n.axvline(0, color='0.7', lw=0.8, zorder=0)
ax_n.legend(loc='upper left', frameon=False)

ax_s.set_ylabel(r'$|\tanh(g/\Upsilon)|$')
ax_s.set_xlabel(r'$g / \Upsilon_0$')
ax_s.set_ylim(0, 1.05)
ax_s.axvline(0, color='0.7', lw=0.8, zorder=0)

os.makedirs(OUT_DIR, exist_ok=True)
fig.savefig(os.path.join(OUT_DIR, 'fig_thermal_softplus.pdf'),
            dpi=300, bbox_inches='tight')
