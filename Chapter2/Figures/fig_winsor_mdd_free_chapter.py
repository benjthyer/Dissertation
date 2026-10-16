"""
Chapter figures for the free multi-domain analysis of HT-Win-06-01b, focused
on one domain structure (default N = 4). Reads the cached fits written by
fig_winsor_mdd_free.py (generated/data/mdd_free/<weighting>/N<n>.json and
maps_N<n>.csv); no fitting is done here.

Figures (generated/mdd_free/<weighting>/chapter/):
  ch2_mdd_delta_N<n>        delta plot, data and the N-domain model
  ch2_mdd_spectrum_N<n>     4He/3He spectrum and the best age-consistent burial path
  ch2_mdd_map_paths_N<n>    top: reduced chi^2 maps (colour scale set by this model's
                            chi^2 distribution) with He-age isopleths; bottom: burial
                            paths drawn from the gridded posterior, one column per
                            assumed crystallization age (180, 195, 210 Ma)
  ch2_mdd_3he_fits_N1-5     supplementary: fractional yields, cumulative yields,
                            Arrhenius and delta plots for N = 1..5 (5 x 4 grid)

Posterior paths: for each assumed crystallization age the (t_peak, T_max) grid
defines p ~ exp(-(chi^2 - chi^2_min) / (2 s)), s = max(1, reduced chi^2_min)
(the same inflation used for the 1-sigma region). N_PATHS cells are drawn with
replacement and jittered uniformly within their grid cell. With two free
parameters on a dense grid this is equivalent to MCMC sampling of the posterior.

Usage: python fig_winsor_mdd_free_chapter.py [--n 4] [--weighting absolute]
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import matplotlib.patheffects as pe

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M
import winsor_he43_mdd as D
from thermochr_utils import draw_step_connectors
from plot_style import apply_style


def _opt(args, name, default):
    return args[args.index(name) + 1] if name in args else default


ARGS = sys.argv[1:]
N_SEL = int(_opt(ARGS, '--n', 4))
WEIGHTING = _opt(ARGS, '--weighting', 'absolute')
DATA_DIR = os.path.join(M.DATA_OUTDIR, 'mdd_free', WEIGHTING)
OUT = os.path.join(M.OUTDIR, 'mdd_free', WEIGHTING, 'chapter')
os.makedirs(OUT, exist_ok=True)

MAP_T_FORMS = (180.0, 195.0, 210.0)
T_EXPOSED_MA = 50.0
MEASURED_AGE = (130.0, 180.0)
AFT_BOX = dict(t=(85.0, 100.0), T=(50.0, 70.0))
PLATEAU = (0.04, 0.07)
N_PATHS = 300
T_PEAK_STEP, T_MAX_STEP = 2.5, 1.0
SUPP_N = (1, 2, 3, 4, 5)

INK, MUTED, BOX = '#222222', '#8a8a8a', '#d9d9d9'
C_MOD, C_REF, C_AFT, C_OUT = '#2a78d6', '#eb6834', '#eb6834', '#b4b4b4'
CHI_COLORS = ['#104281', '#256abf', '#5598e7', '#9ec5f4', '#cde2fb', '#f3f6fa']
STROKE = [pe.withStroke(linewidth=3.2, foreground=INK)]

spec = M.load_spectrum()
d = D.he3_data(spec)
N_FIT = spec['n_fit']
DOF = N_FIT - 3


def load(n):
    return json.load(open(os.path.join(DATA_DIR, f'N{n}.json')))


def burial_nodes(t_form, T_max, t_peak):
    return [t_form, t_peak, T_EXPOSED_MA, 0.0], [M.T_SURF, T_max, M.T_SURF, M.T_SURF]


def best_age_consistent(res):
    th = [t for t in res['thermal'] if MEASURED_AGE[0] <= t['bulk_age_Ma'] <= MEASURED_AGE[1]] or res['thermal']
    return min(th, key=lambda t: t['chi2'])


def save(fig, name, **kw):
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(OUT, f'{name}.{ext}'), dpi=200, **kw)
    plt.close(fig)


res = load(N_SEL)
lnD_ref = d['lnD_stage1']

# ---------------------------------------------------------------------------
# Delta plot, N_SEL only
# ---------------------------------------------------------------------------
apply_style()
fig, ax = plt.subplots()
ax.axvspan(*PLATEAU, color='#f3f3f3', lw=0, zorder=0)
ax.axhline(0, color=C_REF, lw=1.4, ls='--', zorder=1)
ax.errorbar(spec['F_end'], d['lnD'] - lnD_ref, yerr=d['sigma'], fmt='o', ms=5, color=INK,
            mec='white', mew=0.7, elinewidth=0.9, zorder=3)
ax.plot(res['model_F'], np.asarray(res['model_lnD']) - lnD_ref, color=C_MOD, lw=1.8,
        marker='D', ms=4, zorder=4)
ax.set_xlim(0, 0.16)
ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
ax.set_ylabel(r'$\Delta\ln(D/a^2)$ from Stage 1 line')
ax.set_title(f'Delta plot: {N_SEL}-domain model', fontsize=14)
ax.legend(handles=[Line2D([], [], color=INK, marker='o', ls='none', label='Data'),
                   Line2D([], [], color=C_MOD, marker='D', ms=4, lw=1.8,
                          label=rf"Model, Arrhenius $\chi^2_\nu$ = {res['arrhenius_chi2_nu']:.2f}"),
                   Line2D([], [], color=C_REF, lw=1.4, ls='--', label='Stage 1 reference')],
          loc='upper right', fontsize=10)
fig.tight_layout()
save(fig, f'ch2_mdd_delta_N{N_SEL}')

# ---------------------------------------------------------------------------
# 4He/3He spectrum, N_SEL only
# ---------------------------------------------------------------------------
bt = best_age_consistent(res)
u, Fs, Fe = spec['use'], spec['F_start'], spec['F_end']
fig, ax = plt.subplots()
ax.axvspan(*PLATEAU, color='#f3f3f3', lw=0, zorder=0)
for i in np.where(u)[0]:
    ax.fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0, zorder=1)
ax.hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=3)
p = np.asarray(bt['pred'])
ax.hlines(p, Fs, Fe, color=C_MOD, lw=1.9, zorder=4)
draw_step_connectors(ax, Fs, Fe, p, color=C_MOD, zorder=4)
ax.set_xlim(0, 0.16)
ax.set_ylim(0, 1.2)
ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
ax.set_title(f'$^4$He/$^3$He: {N_SEL}-domain model', fontsize=14)
ax.legend(handles=[Line2D([], [], color=INK, lw=2.2, label='Data (M), LB–UB box'),
                   Line2D([], [], color=C_MOD, lw=1.9,
                          label=rf"Burial {bt['t_form_Ma']:.0f}→{bt['t_peak_Ma']:.0f} Ma, "
                                rf"{bt['T_max_C']:.0f} °C; $\chi^2_\nu$ = {bt['chi2_nu']:.1f}")],
          loc='lower right', fontsize=10)
fig.tight_layout()
save(fig, f'ch2_mdd_spectrum_N{N_SEL}')

# ---------------------------------------------------------------------------
# chi^2 maps (rescaled to this model) + posterior burial paths
# ---------------------------------------------------------------------------
g = pd.read_csv(os.path.join(DATA_DIR, f'maps_N{N_SEL}.csv'))
g['chi2_nu'] = g['chi2'] / DOF
cmin = g['chi2'].min()
s_infl = max(1.0, cmin / DOF)
thr = cmin + 3.53 * s_infl
nu_min = cmin / DOF
# colour bins in reduced chi^2 anchored to this model's minimum
edges = np.r_[0.0, np.round(nu_min + np.array([0.3, 0.8, 1.8, 3.8, 6.8]), 1), 1e9]
labels = [f'<{edges[1]:g}'] + [f'{a:g}–{b:g}' for a, b in zip(edges[1:-2], edges[2:-1])] + [f'>{edges[-2]:g}']
cmap, norm = ListedColormap(CHI_COLORS), BoundaryNorm(edges, len(CHI_COLORS))

apply_style(scale=1.1)
fig, axes = plt.subplots(2, 3, figsize=(13, 9.0), sharex=True, sharey='row')
rng = np.random.default_rng(1)
tt = np.linspace(0, 210, 300)
summary = []
for col, tf in enumerate(MAP_T_FORMS):
    gg = g[np.isclose(g['t_form_Ma'], tf)].reset_index(drop=True)
    tps = np.sort(gg['t_peak_Ma'].unique())
    Tms = np.sort(gg['T_max_C'].unique())
    piv = lambda c: gg.pivot(index='T_max_C', columns='t_peak_Ma', values=c).loc[:, tps].to_numpy()
    TP, TM = np.meshgrid(tps, Tms)
    ax = axes[0, col]
    pc = ax.pcolormesh(TP, TM, piv('chi2_nu'), cmap=cmap, norm=norm, shading='nearest', rasterized=True)
    cs = ax.contour(TP, TM, piv('bulk_age_Ma'), levels=list(MEASURED_AGE), colors=INK, linewidths=1.2,
                    linestyles='--')
    ax.clabel(cs, fmt=lambda v: f'{v:.0f} Ma', fontsize=9)
    C1 = piv('chi2')
    if (C1 <= thr).any():
        c1 = ax.contour(TP, TM, C1, levels=[thr], colors='white', linewidths=1.6)
        c1.set_path_effects(STROKE)
    ax.add_patch(Rectangle((AFT_BOX['t'][0], AFT_BOX['T'][0]), 15, 20, fill=False, ec=C_AFT, lw=1.8, zorder=4))
    j = gg['chi2'].idxmin()
    ax.plot(gg.loc[j, 't_peak_Ma'], gg.loc[j, 'T_max_C'], 'D', color='white', mec=INK, ms=7, zorder=5)
    ax.set_xlim(210, 0)
    ax.set_ylim(30, 90)
    ax.set_title(rf'Crystallized at {tf:.0f} Ma ($\chi^2_\nu$ = {gg["chi2_nu"].min():.2f})', fontsize=12)

    # posterior samples of (t_peak, T_max) for this crystallization age
    w = np.exp(-(gg['chi2'] - gg['chi2'].min()) / (2 * s_infl))
    w = w / w.sum()
    idx = rng.choice(len(gg), size=N_PATHS, p=w)
    ax2 = axes[1, col]
    ages = gg.loc[idx, 'bulk_age_Ma'].to_numpy()
    ok = (ages >= MEASURED_AGE[0]) & (ages <= MEASURED_AGE[1])
    for k, i in enumerate(idx):
        tp = gg.loc[i, 't_peak_Ma'] + rng.uniform(-T_PEAK_STEP / 2, T_PEAK_STEP / 2)
        Tm = gg.loc[i, 'T_max_C'] + rng.uniform(-T_MAX_STEP / 2, T_MAX_STEP / 2)
        tp = min(tp, tf - 1.0)
        ax2.plot(tt, M.path_T(*burial_nodes(tf, Tm, tp), tt), color=C_MOD if ok[k] else C_OUT,
                 lw=0.6, alpha=0.25, zorder=2 if ok[k] else 1)
    ax2.plot(tt, M.path_T(*burial_nodes(tf, gg.loc[j, 'T_max_C'], gg.loc[j, 't_peak_Ma']), tt),
             color=INK, lw=2.0, zorder=4)
    ax2.add_patch(Rectangle((AFT_BOX['t'][0], AFT_BOX['T'][0]), 15, 20, fill=False, ec=C_AFT, lw=1.8, zorder=5))
    ax2.set_ylim(10, 90)
    ax2.set_title(f'He age 130–180 Ma: {100 * ok.mean():.0f}% of paths', fontsize=11)
    summary.append(dict(t_form=tf, frac_age_ok=float(ok.mean()),
                        T_max_p16=float(np.percentile(gg.loc[idx, 'T_max_C'], 16)),
                        T_max_p84=float(np.percentile(gg.loc[idx, 'T_max_C'], 84)),
                        t_peak_p16=float(np.percentile(gg.loc[idx, 't_peak_Ma'], 16)),
                        t_peak_p84=float(np.percentile(gg.loc[idx, 't_peak_Ma'], 84))))
axes[0, 0].set_ylabel(r'Peak temperature, $T_\mathrm{max}$ (°C)')
axes[1, 0].set_ylabel('Temperature (°C)')
axes[1, 1].set_xlabel('Time (Ma); upper row: time of peak temperature')
cb = fig.colorbar(pc, ax=axes[0, :], ticks=0.5 * (np.r_[nu_min - 0.3, edges[1:-1]] + np.r_[edges[1:-1], edges[-2] + 3]),
                  pad=0.015, fraction=0.025)
cb.ax.set_yticklabels(labels)
cb.set_label(r'Reduced $\chi^2$ ($^4$He/$^3$He)')
axes[0, 0].legend(handles=[Line2D([], [], color='white', lw=1.6, path_effects=STROKE, label=r'Joint 1$\sigma$'),
                           Line2D([], [], color=INK, lw=1.2, ls='--', label='Predicted He age'),
                           Line2D([], [], color=C_AFT, lw=1.8, label='AFT peak window')],
                  loc='lower left', fontsize=9)
axes[1, 0].legend(handles=[Line2D([], [], color=INK, lw=2.0, label='Best fit'),
                           Line2D([], [], color=C_MOD, lw=1.2, label='Posterior path, He age 130–180 Ma'),
                           Line2D([], [], color=C_OUT, lw=1.2, label='Posterior path, other He age')],
                  loc='upper left', fontsize=9)
fig.subplots_adjust(right=0.88, hspace=0.18, wspace=0.12)
cb.ax.set_position([0.9, axes[0, 2].get_position().y0, 0.018, axes[0, 2].get_position().height])
save(fig, f'ch2_mdd_map_paths_N{N_SEL}', bbox_inches='tight')
pd.DataFrame(summary).to_csv(os.path.join(DATA_DIR, f'posterior_paths_N{N_SEL}.csv'), index=False)
print(pd.DataFrame(summary).round(2).to_string(index=False))

# ---------------------------------------------------------------------------
# Supplementary 5 x 4 grid: 3He fits for N = 1..5
# ---------------------------------------------------------------------------
apply_style(scale=0.8)
steps = np.arange(1, spec['F_end'].size + 1)
low = ~np.isfinite(spec['R_LB']) | ~spec['use']
x_arr = 10000.0 / (spec['T_C'] + 273.0)
xr = np.array([x_arr.min() - 0.15, x_arr.max() + 0.15])
fig, axes = plt.subplots(len(SUPP_N), 4, figsize=(12.5, 15.5), sharex='col')
for row, n in enumerate(SUPP_N):
    r = load(n)
    Fm = np.asarray(r['model_F'])
    a = axes[row]
    a[0].plot(steps, spec['dF3'], 'o', color=INK, ms=4, mec='white', mew=0.5, zorder=3)
    a[0].plot(steps[low], spec['dF3'][low], 'o', mfc='white', mec=INK, ms=4, zorder=4)
    a[0].plot(steps, np.diff(np.r_[0.0, Fm]), color=C_MOD, lw=1.2, marker='D', ms=2.5, zorder=5)
    a[0].set_yscale('log')
    a[0].set_ylabel(f'N = {n}\n\n' + r'Fraction of $^3$He in step', fontsize=10)
    a[1].plot(steps, spec['F_end'], 'o', color=INK, ms=4, mec='white', mew=0.5, zorder=3)
    a[1].plot(steps, Fm, color=C_MOD, lw=1.2, marker='D', ms=2.5, zorder=4)
    a[1].set_ylabel(r'Cumulative $^3$He fraction', fontsize=10)
    a[1].text(0.04, 0.93, f"RMS {r['rms_yield']:.1e}\nBIC {r['bic']:.0f}", transform=a[1].transAxes,
              va='top', fontsize=8.5, color='#444444')
    a[2].plot(xr, np.log(M.D0_A2) - M.EA * xr / (M.R_CAL * 1e4), color=C_REF, lw=1.1, ls='--')
    a[2].plot(x_arr, d['lnD'], color=MUTED, lw=0.5)
    a[2].errorbar(x_arr, d['lnD'], yerr=d['sigma'], fmt='o', ms=3.5, color=INK, mec='white', mew=0.5,
                  elinewidth=0.7)
    a[2].plot(x_arr, r['model_lnD'], color=C_MOD, lw=1.0, marker='D', ms=2.5)
    a[2].set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)', fontsize=10)
    a[2].text(0.96, 0.93, rf"$\chi^2_\nu$ = {r['arrhenius_chi2_nu']:.2f}", transform=a[2].transAxes,
              ha='right', va='top', fontsize=9, color='#444444')
    a[3].axvspan(*PLATEAU, color='#f1f1f1', lw=0)
    a[3].axhline(0, color=C_REF, lw=1.1, ls='--')
    a[3].errorbar(spec['F_end'], d['lnD'] - lnD_ref, yerr=d['sigma'], fmt='o', ms=3.5, color=INK,
                  mec='white', mew=0.5, elinewidth=0.7)
    a[3].plot(Fm, np.asarray(r['model_lnD']) - lnD_ref, color=C_MOD, lw=1.2, marker='D', ms=2.5)
    a[3].set_xlim(0, 0.16)
    a[3].set_ylabel(r'$\Delta\ln(D/a^2)$', fontsize=10)
for a, t in zip(axes[0], ['Fractional yields (fitted)', 'Cumulative yields (fitted)',
                          'Arrhenius (consequence)', 'Delta plot (consequence)']):
    a.set_title(t, fontsize=11)
axes[-1, 0].set_xlabel('Step')
axes[-1, 1].set_xlabel('Step')
axes[-1, 2].set_xlabel(r'$10^4/T$ (K$^{-1}$)')
axes[-1, 3].set_xlabel(r'$\Sigma F_{^3\mathrm{He}}$')
fig.tight_layout(h_pad=1.0, w_pad=1.0)
save(fig, 'ch2_mdd_3he_fits_N1-5')
