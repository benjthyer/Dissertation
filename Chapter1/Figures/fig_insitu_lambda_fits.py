"""
fig_insitu_lambda_fits.py -- cumulative yield against cumulative time for
every isothermal run of the MC empty-ampoule experiment, with the in-situ
rate-constant fits of insitu_lambda.check_A() (Chapter 2 SI analogue:
PermeationStepFits_Grid.pdf).

Hollow grey points are first steps excluded from the fits.  For each such
run, the grey dashed curve is the fit we would get if that first step were
included; its misfit to the later steps shows that the excluded step was not
yet in diffusive steady state.

Output: generated/InSituLambdaFits_Grid.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
import insitu_lambda as L

apply_style(scale=7 / 6.4)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
d = L.load_mc_empty().set_index('step')
fits = L.check_A(include_rejected=True)
fits_all = L.check_A(drop_first=False)   # every step of every run
temps = sorted(fits['T_C'].unique())
fig, axes = plt.subplots(len(temps), 2, figsize=(7, 2.3 * len(temps)), squeeze=False)
COL = {'4He': ('m4_nccSTP', 'nccSTP'), '3He': ('m3_pccSTP', 'pccSTP')}
ISO = {'4He': r'$^4$He', '3He': r'$^3$He'}
for r, T in enumerate(temps):
    for c, iso in enumerate(('4He', '3He')):
        ax = axes[r, c]
        f = fits[(fits.T_C == T) & (fits.isotope == iso)].iloc[0]
        mcol, unit = COL[iso]
        steps = f.run_steps
        t = d.loc[steps, 'time_min'].to_numpy() / 60.0
        m = d.loc[steps, mcol].to_numpy()
        tc = np.concatenate([[0], np.cumsum(t)]); mc = np.concatenate([[0], np.cumsum(m)])
        nd = len(f.dropped_steps)
        t0, m0 = tc[nd], mc[nd]
        tt = np.linspace(t0, tc[-1], 200)
        ax.plot(tt, m0 + f.n0_fit * (1 - np.exp(-f.lam * (tt - t0) * 3600)), 'r--', lw=1.5,
                label='Adopted fit')
        if nd:
            g = fits_all[(fits_all.T_C == T) & (fits_all.isotope == iso)].iloc[0]
            ta = np.linspace(0, tc[-1], 200)
            ax.plot(ta, g.n0_fit * (1 - np.exp(-g.lam * ta * 3600)), color='grey', ls='--', lw=1.5,
                    label='Fit including first step')
            ax.scatter(tc[1], mc[1], facecolors='white', edgecolors='grey', s=45, zorder=5,
                       label='Excluded first step')
            ax.text(0.97, 0.06, f'with first step: λ {100 * (g.lam / f.lam - 1):+.0f}%, '
                    f'χ²/dof = {g.chi2 / (g.N - 2):.0f}', transform=ax.transAxes,
                    ha='right', fontsize=8, color='grey')
        ax.scatter(tc[nd + 1:], mc[nd + 1:], color='k', s=30, zorder=6, label='Fitted steps')
        ax.set_xlim(0, tc[-1] * 1.04); ax.set_ylim(0, mc[-1] * 1.12)
        ax.set_title(f"{T:.0f}°C, {ISO[iso]}: λ = {f.lam:.2e} s$^{{-1}}$", fontsize=10)
        ax.set_ylabel(f'$m_{{cum}}$ ({unit})', fontsize=9)
        ax.tick_params(labelsize=8); ax.grid(True, alpha=0.4)
        if r == len(temps) - 1:
            ax.set_xlabel('Cumulative time (h)', fontsize=9)
        if r == 0 and c == 0:
            ax.legend(fontsize=7, loc='upper left')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'InSituLambdaFits_Grid.pdf'), dpi=300)
plt.close(fig)
print('wrote InSituLambdaFits_Grid.pdf')
