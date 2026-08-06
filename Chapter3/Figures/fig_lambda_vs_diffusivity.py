"""
Per-experiment Arrhenius plots for apparent 3He diffusivity and apparent
3He rate constant (lambda), plus a diffusivity-vs-rate-constant comparison
plot with a linear regression and points colored by cumulative fractional
3He yield (Fim).

Reads the plot-ready cache built by Chapter3/Tables/build_plotable_cache.py
(run that script first if plotable_sulfides_cache.pkl is missing or stale).

Outputs, per sample -> Chapter3/Figures/generated/lambdaVdiff/:
    <sample>_diffusivity_arrhenius.pdf
    <sample>_lambda_arrhenius.pdf
    <sample>_diff_vs_lambda.pdf
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from plot_style import apply_style, diffusivity_errorbar
apply_style()

CACHE_PKL = os.path.join(SCRIPT_DIR, '..', 'Tables', 'plotable_sulfides_cache.pkl')
OUTDIR = os.path.join(SCRIPT_DIR, 'generated', 'lambdaVdiff')
os.makedirs(OUTDIR, exist_ok=True)

Ctemps = np.array([100, 150, 200, 250, 300, 350, 400, 500, 600])


def _num(df, col):
    """Coerce a cache column to float, turning stray Excel formula-error
    strings (e.g. '#NUM!') and Nones into NaN."""
    return pd.to_numeric(df[col], errors='coerce').to_numpy(dtype=float)


def _safe_name(sample):
    return sample.replace(' ', '_').replace('/', '_')


def _add_temp_axis(ax1):
    ax2 = ax1.twiny()
    xlim = ax1.get_xlim()
    ax2.set_xticks(1e4 / (Ctemps + 273))
    ax2.set_xlim(xlim)
    ax2.set_xticklabels(Ctemps)
    ax2.set_xlabel('Temperature (°C)')
    return ax2


def _log_bounds(center, lb, ub):
    """Asymmetric log-space error magnitudes from raw (non-log) LB/center/UB
    values. A non-positive bound means "consistent with zero" (physically
    unconstrained on that side) and can't be logged, so it's left as NaN --
    matplotlib's errorbar simply skips drawing that whisker."""
    ln_center = np.log(center)
    lower = np.where(lb > 0, ln_center - np.log(np.where(lb > 0, lb, np.nan)), np.nan)
    upper = np.where(ub > 0, np.log(np.where(ub > 0, ub, np.nan)) - ln_center, np.nan)
    return np.clip(np.vstack([lower, upper]), 0, None)


def plot_diffusivity_arrhenius(df, sample):
    tk = df['10000/TK'].to_numpy(dtype=float)
    ln_d = df['ln(d/a^2)'].to_numpy(dtype=float)
    lb, ub = _num(df, 'LB_dln(d/a^2)'), _num(df, 'UB_dln(d/a^2)')

    fig, ax1 = plt.subplots()
    # Own low-alpha connecting line (chronological step order) so it stays
    # continuous across any ghosted (unconstrained-LB) points -- see
    # diffusivity_errorbar's docstring.
    ax1.plot(tk, ln_d, linestyle=':', color='tab:blue', alpha=0.4, zorder=1)
    diffusivity_errorbar(ax1, tk, ln_d, lb, ub, 'tab:blue', 'o', normal_alpha=0.7)
    _add_temp_axis(ax1)
    ax1.set_xlabel(r'$10^4/T$ (K)')
    ax1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
    ax1.grid(alpha=0.3)
    ax1.set_title(f'{sample}: Apparent 3He Diffusivity')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, f'{_safe_name(sample)}_diffusivity_arrhenius.pdf'),
                dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_lambda_arrhenius(df, sample):
    lam_m = _num(df, 'lambdaM')
    lam_lb = _num(df, 'lambdaLB')
    lam_ub = _num(df, 'lambdaUB')
    valid = np.isfinite(lam_m) & (lam_m > 0)
    if not valid.any():
        print(f"  no lambda data for '{sample}' -- skipping lambda Arrhenius plot")
        return

    tk = df['10000/TK'].to_numpy(dtype=float)[valid]
    ln_lam = np.log(lam_m[valid])
    yerr = _log_bounds(lam_m[valid], lam_lb[valid], lam_ub[valid])

    fig, ax1 = plt.subplots()
    ax1.errorbar(tk, ln_lam, yerr=yerr, marker='o', capsize=4, alpha=0.7,
                 linestyle=':', color='tab:red')
    _add_temp_axis(ax1)
    ax1.set_xlabel(r'$10^4/T$ (K)')
    ax1.set_ylabel(r'$\ln(\lambda)$ (s$^{-1}$)')
    ax1.grid(alpha=0.3)
    ax1.set_title(f'{sample}: Apparent 3He Rate Constant')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, f'{_safe_name(sample)}_lambda_arrhenius.pdf'),
                dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_diff_vs_lambda(df, sample):
    lam_m = _num(df, 'lambdaM')
    lam_lb = _num(df, 'lambdaLB')
    lam_ub = _num(df, 'lambdaUB')
    ln_d = df['ln(d/a^2)'].to_numpy(dtype=float)
    d_lb, d_ub = _num(df, 'LB_dln(d/a^2)'), _num(df, 'UB_dln(d/a^2)')
    fim = df['Fim'].to_numpy(dtype=float)

    valid = np.isfinite(lam_m) & (lam_m > 0) & np.isfinite(ln_d)
    if valid.sum() < 2:
        print(f"  fewer than 2 paired diffusivity/lambda points for '{sample}' -- "
              f"skipping comparison plot")
        return

    ln_lam = np.log(lam_m[valid])
    xerr = _log_bounds(lam_m[valid], lam_lb[valid], lam_ub[valid])
    y = ln_d[valid]
    yerr = np.clip(np.vstack([d_lb[valid], d_ub[valid]]), 0, None)
    c = fim[valid]

    fig, ax = plt.subplots()
    ax.errorbar(ln_lam, y, xerr=xerr, yerr=yerr, fmt='none', ecolor='0.6',
                elinewidth=0.8, capsize=3, alpha=0.6, zorder=1)
    # Normalized per-sample (rather than a fixed 0-1 scale) since Fim's range
    # varies hugely between experiments -- some span the full 0-1 course of
    # the step-heat, others (e.g. long irradiations) only ever reach a few
    # percent, and a fixed scale would wash those out to a single color.
    sc = ax.scatter(ln_lam, y, c=c, cmap='viridis', vmin=c.min(), vmax=c.max(),
                     s=40, edgecolor='k', linewidth=0.4, zorder=2)
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label(r'Cumulative $^3$He Yield, $F_i$')

    fit = scipy.stats.linregress(ln_lam, y)
    xfit = np.linspace(ln_lam.min(), ln_lam.max(), 50)
    ax.plot(xfit, fit.intercept + fit.slope * xfit, color='black', linestyle='--',
            label=f'slope = {fit.slope:.3f}, R² = {fit.rvalue ** 2:.3f}')

    ax.set_xlabel(r'$\ln(\lambda)$ (s$^{-1}$)')
    ax.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    ax.set_title(f'{sample}: Diffusivity vs. Rate Constant')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, f'{_safe_name(sample)}_diff_vs_lambda.pdf'),
                dpi=300, bbox_inches='tight')
    plt.close(fig)


def main():
    if not os.path.exists(CACHE_PKL):
        raise FileNotFoundError(
            f"{CACHE_PKL} not found -- run Chapter3/Tables/build_plotable_cache.py first.")
    cache = pd.read_pickle(CACHE_PKL)
    for sample, df in cache.groupby('sample', sort=False):
        print(f"Plotting '{sample}' ({len(df)} rows)...")
        plot_diffusivity_arrhenius(df, sample)
        plot_lambda_arrhenius(df, sample)
        plot_diff_vs_lambda(df, sample)
    print(f"Wrote figures to {OUTDIR}")


if __name__ == '__main__':
    main()
