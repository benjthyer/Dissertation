"""
Per-cell loss of the affinity-aware model (Eq. eq:affloss), in units of the
per-phase scale c: u = y_hat/c (prediction), t = y/c (label).

    trusted   (label known):     (u - t)^2 + w_p * relu(min(t, h_p) - u)^2   [hinge only if t > 0]
    untrusted (no label, t=-1):  w_n * relu(u + m)^2 + w_eta * (u + 1)^2

The functional form follows ngibbs.engine.NN_continuous.AffinityModel.affinity_mole_loss;
the weights are those of Table tab:affloss (h_p = 0.03, w_p = 3, m = 0.5, w_n = 0.25,
w_eta = 0.05). Panel (a) is the trusted loss as a heat map over t and u in [-1, 1];
panel (b) is the untrusted loss, which depends on u only, on the same vertical axis.

Writes generated/fig_affinity_loss.pdf (300 dpi). No ngibbs needed.
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm

OUT = Path(__file__).resolve().parent / 'generated' / 'fig_affinity_loss.pdf'
H_P, W_P = 0.03, 3.0          # present-side hinge: margin, weight
MARGIN, W_N = 0.5, 0.25       # untrusted hinge: margin (u > -MARGIN penalised), weight
W_ETA = 0.05                  # untrusted pull toward u = -1
LIM = 1.0
N = 801

plt.rcParams.update({'font.size': 10, 'axes.labelsize': 11, 'xtick.labelsize': 9.5,
                     'ytick.labelsize': 9.5, 'legend.fontsize': 9, 'pdf.fonttype': 42})


def trusted(t, u):
    sq = (u - t) ** 2
    hinge = np.maximum(np.minimum(t, H_P) - u, 0.0) ** 2
    return sq + np.where(t > 0, W_P * hinge, 0.0)


def untrusted(u):
    return W_N * np.maximum(u + MARGIN, 0.0) ** 2 + W_ETA * (u + 1.0) ** 2


t = np.linspace(-LIM, LIM, N)
u = np.linspace(-LIM, LIM, N)
T, U = np.meshgrid(t, u)
L = trusted(T, U)

fig, (ax, bx) = plt.subplots(1, 2, figsize=(5.5, 4.4), sharey=True, layout='constrained',
                             gridspec_kw={'width_ratios': [2.6, 1]})
im = ax.pcolormesh(t, u, L, cmap='viridis', norm=PowerNorm(0.5, vmin=0, vmax=L.max()),
                   shading='auto', rasterized=True)
ax.contour(t, u, L, levels=[0.01, 0.05, 0.2, 0.5, 1, 2, 4], colors='w', linewidths=0.6, alpha=0.8)
ax.plot([-LIM, LIM], [-LIM, LIM], color='w', ls='--', lw=1.0)
ax.axvline(0, color='w', lw=0.6, alpha=0.6)
ax.axhline(0, color='w', lw=0.6, alpha=0.6)
ax.set_xlim(-LIM, LIM)
ax.set_ylim(-LIM, LIM)
ax.set_aspect('equal')
ax.set_xlabel(r'$y/c$')
ax.set_ylabel(r'$\hat y/c$')
ax.set_title('(a) trusted', loc='left', fontsize=10.5)
ax.text(0.5, -0.9, 'present\n(MSE + hinge)', color='w', ha='center', va='bottom', fontsize=8.5)
ax.text(-0.5, 0.9, 'absent\n(MSE)', color='w', ha='center', va='top', fontsize=8.5)
cb = fig.colorbar(im, ax=ax, location='bottom', shrink=0.85, pad=0.02, aspect=30)
cb.set_label('trusted loss')

lu = untrusted(u)
bx.plot(lu, u, color='#1f6fb4', lw=2.0)
bx.axhline(-MARGIN, color='0.5', ls=':', lw=1.0)
bx.axhline(0, color='0.75', lw=0.6)
bx.set_xlim(0, lu.max() * 1.05)
bx.set_xlabel('untrusted loss')
bx.set_title('(b) untrusted', loc='left', fontsize=10.5)
bx.spines[['top', 'right']].set_visible(False)

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=300)
print(f'-> {OUT}')
