"""
fig_insitu_lambda_rates.py -- per-step apparent rate constant
    lambda_k = -ln(1 - m_k / n_k) / t_k
for every isothermal run of the MC empty-ampoule experiment.  n_k, the
ampoule's inventory at the start of step k, comes ONLY from the in-situ fits:
n_k = fitted n0 - (measured yields of the run's earlier steps), with the
inventory before an excluded first step obtained by adding that step's yield
back (mass balance).  A run in diffusive steady state gives a flat series at
the fitted lambda (horizontal line).

For the 125 and 200 C runs, whose first steps are excluded, both fits are
shown: the adopted fit (first step excluded; red) and the fit including the
first step (grey).

Error bars: 2 sigma from the measured-yield uncertainty only (the fitted n0's
own uncertainty shifts a whole series together and is not shown).
Output: generated/InSituLambdaRates_Grid.pdf
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
fits_all = L.check_A(drop_first=False)
COL = {'4He': ('m4_nccSTP', 'm4_2s'), '3He': ('m3_pccSTP', 'm3_2s')}
ISO = {'4He': r'$^4$He', '3He': r'$^3$He'}


def rates(steps, first_fitted, n0, mcol, scol):
    """Per-step rates with n from the fit's n0 by mass balance."""
    t = d.loc[steps, 'time_min'].to_numpy() * 60.0
    m = d.loc[steps, mcol].to_numpy()
    s = d.loc[steps, scol].to_numpy() / 2.0
    k0 = steps.index(first_fitted)
    cum = np.concatenate([[0.0], np.cumsum(m)])
    n = n0 - (cum[:-1] - cum[k0])          # inventory before each step
    lam = -np.log(1 - m / n) / t
    lam_2s = 2 * s / (t * (n - m))
    return lam, lam_2s


temps = sorted(fits['T_C'].unique())
fig, axes = plt.subplots(len(temps), 2, figsize=(7, 2.3 * len(temps)), squeeze=False)
summary = []
for r, T in enumerate(temps):
    for c, iso in enumerate(('4He', '3He')):
        ax = axes[r, c]
        mcol, scol = COL[iso]
        f = fits[(fits.T_C == T) & (fits.isotope == iso)].iloc[0]
        g = fits_all[(fits_all.T_C == T) & (fits_all.isotope == iso)].iloc[0]
        steps = list(f.run_steps)
        x = np.array(steps)
        if f.dropped_steps:
            lg, eg = rates(steps, steps[0], g.n0_fit, mcol, scol)
            ax.axhline(g.lam * 1e5, color='grey', ls='--', lw=1.5, label='Fit including first step')
            ax.errorbar(x + 0.08, lg * 1e5, yerr=eg * 1e5, fmt='s', color='grey', mfc='lightgrey',
                        capsize=3, ms=5, label='Rates, $n$ from that fit')
        lf, ef = rates(steps, f.first_step, f.n0_fit, mcol, scol)
        keep = np.isin(x, f.dropped_steps, invert=True)
        ax.axhline(f.lam * 1e5, color='r', ls='--', lw=1.5, label='Adopted fit')
        ax.errorbar(x[keep] - 0.08, lf[keep] * 1e5, yerr=ef[keep] * 1e5, fmt='o', color='k',
                    capsize=3, ms=5, label='Rates, $n$ from adopted fit')
        if (~keep).any():
            ax.errorbar(x[~keep] - 0.08, lf[~keep] * 1e5, yerr=ef[~keep] * 1e5, fmt='o', color='k',
                        mfc='white', capsize=3, ms=5, label='Excluded first step')
        ax.set_xticks(x)
        if not f.dropped_steps:            # common +/-6 % window for single-fit runs
            ax.set_ylim(f.lam * 1e5 * 0.94, f.lam * 1e5 * 1.06)
        ax.set_title(f"{T:.0f}°C, {ISO[iso]}", fontsize=10)
        ax.set_ylabel(r'$-\ln(1-m/n)/t$ ($10^{-5}$ s$^{-1}$)', fontsize=8)
        ax.tick_params(labelsize=8); ax.grid(True, alpha=0.4)
        if r == len(temps) - 1:
            ax.set_xlabel('Step number', fontsize=9)
        if f.dropped_steps and c == 0:
            ax.legend(fontsize=6.5, loc='lower right')
        summary.append((T, iso, np.round(lf * 1e5, 3).tolist(),
                        np.round(lg * 1e5, 3).tolist() if f.dropped_steps else None,
                        round(f.lam * 1e5, 3), round(g.lam * 1e5, 3)))
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'InSituLambdaRates_Grid.pdf'), dpi=300)
plt.close(fig)
for row in summary:
    print(row)
