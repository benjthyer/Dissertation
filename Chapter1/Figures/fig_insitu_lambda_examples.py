"""
fig_insitu_lambda_examples.py -- example in-situ rate-constant fits for the
empty ampoule (main-text figure): cumulative yield against cumulative time
for the 175 and 250 C runs, 4He and 3He (2 x 2); all steps of both runs are fit.

(The plotting code still handles runs with an excluded first step.)
Output: generated/InSituLambdaFits_Examples.{pdf,png}
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
import insitu_lambda as L

apply_style()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
d = L.load_mc_empty().set_index('step')
fits = L.check_A(include_rejected=True)
fits_all = L.check_A(drop_first=False)
COL = {'4He': ('m4_nccSTP', 'nccSTP'), '3He': ('m3_pccSTP', 'pccSTP')}
ISO = {'4He': r'$^4$He', '3He': r'$^3$He'}

fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.0))
for r, T in enumerate((175.0, 250.0)):
    for c, iso in enumerate(('4He', '3He')):
        ax = axes[r, c]
        f = fits[(fits.T_C == T) & (fits.isotope == iso)].iloc[0]
        mcol, unit = COL[iso]
        steps = list(f.run_steps)
        t = d.loc[steps, 'time_min'].to_numpy() / 60.0
        m = d.loc[steps, mcol].to_numpy()
        tc = np.concatenate([[0], np.cumsum(t)]); mc = np.concatenate([[0], np.cumsum(m)])
        nd = len(f.dropped_steps)
        t0, m0 = tc[nd], mc[nd]
        tt = np.linspace(t0, tc[-1], 200)
        ax.plot(tt, m0 + f.n0_fit * (1 - np.exp(-f.lam * (tt - t0) * 3600)), 'r--', lw=1.8,
                label='Fit', zorder=3)
        if nd:
            g = fits_all[(fits_all.T_C == T) & (fits_all.isotope == iso)].iloc[0]
            ta = np.linspace(0, tc[-1], 200)
            ax.plot(ta, g.n0_fit * (1 - np.exp(-g.lam * ta * 3600)), color='grey', ls='--', lw=1.4,
                    label='Fit including first step', zorder=2)
            ax.scatter(tc[1], mc[1], facecolors='white', edgecolors='grey', s=50, zorder=5,
                       label='Excluded first step')
        ax.scatter(tc[nd + 1:], mc[nd + 1:], color='k', s=34, zorder=6, label='Fitted steps')
        ax.set_xlim(0, tc[-1] * 1.04); ax.set_ylim(0, mc[-1] * 1.12)
        ax.set_title(f"{T:.0f} °C, {ISO[iso]}:  λ = {f.lam:.2e} s$^{{-1}}$", fontsize=11)
        ax.set_ylabel(f'$m_{{cum}}$ ({unit})', fontsize=11)
        ax.tick_params(labelsize=9); ax.grid(True, alpha=0.4)
        if r == 1:
            ax.set_xlabel('Cumulative time (h)', fontsize=11)
        if r == 0 and c == 0:
            ax.legend(fontsize=8, loc='upper left')
        ax.text(0.97, 0.05, '(' + 'abcd'[2 * r + c] + ')', transform=ax.transAxes, ha='right', fontsize=11)
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUT, f'InSituLambdaFits_Examples.{ext}'), dpi=300)
print('ok')
