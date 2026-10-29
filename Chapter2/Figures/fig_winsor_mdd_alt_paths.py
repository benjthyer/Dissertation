"""
Alternative thermal histories for HT-Win-06-01b with the adopted N = 4 free
domain structure (cached in generated/data/mdd_free/absolute/N4.json), to test
whether the burial-heating solution is unique.

Two-parameter path families, each gridded in (crystallization age, temperature):
  isothermal : T(t) = T_iso from t_form to the present
  linear     : T falls linearly from T0 at t_form to 25 C at the present

For every grid node the 4He/3He spectrum chi^2 (same data, sigma and steps as
the burial analysis) and the bulk He age are computed. Posterior paths are
drawn from the gridded posterior p ~ exp(-(chi^2 - chi^2_min) / (2 s)),
s = max(1, reduced chi^2_min), jittered within grid cells.

Outputs
  generated/data/mdd_free/absolute/maps_alt_{isothermal,linear}_N4.csv
  generated/data/mdd_free/absolute/alt_paths_summary_N4.csv
  generated/mdd_free/absolute/chapter/ch2_mdd_alt_paths_N4.{pdf,png}
  generated/mdd_free/absolute/chapter/ch2_mdd_alt_spectra_N4.{pdf,png}

Usage: python fig_winsor_mdd_alt_paths.py [--recompute] [--plot-only] [--jobs 2]
"""
import os
import sys
import json
from multiprocessing import Pool

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M
import winsor_he43_mdd_free as F
from thermochr_utils import draw_step_connectors
from plot_style import apply_style

ARGS = sys.argv[1:]
N_SEL = 4
DATA_DIR = os.path.join(M.DATA_OUTDIR, 'mdd_free', 'absolute')
OUT = os.path.join(M.OUTDIR, 'mdd_free', 'absolute', 'chapter')
os.makedirs(OUT, exist_ok=True)

T_END_LINEAR = 25.0
T_FORM_GRID = np.arange(50.0, 500.01, 5.0)
FAMILIES = {
    'isothermal': dict(T_grid=np.arange(0.0, 70.01, 1.0), label='Isothermal hold',
                       ylabel=r'Hold temperature, $T_\mathrm{iso}$ (°C)', ylim=(0, 70)),
    'linear': dict(T_grid=np.arange(25.0, 120.01, 1.0), label='Linear cooling to 25 °C',
                   ylabel=r'Initial temperature, $T_0$ (°C)', ylim=(25, 120)),
}
T_FORM_STEP, T_STEP = 5.0, 1.0
MEASURED_AGE = (130.0, 180.0)
GEOL_T_FORM = (180.0, 210.0)       # crystallization window used for the burial analysis
PLATEAU = (0.04, 0.07)
N_PATHS = 300
DT_MYR = 1.0

INK, MUTED, BOX = '#222222', '#8a8a8a', '#d9d9d9'
C_MOD, C_OUT = '#2a78d6', '#b4b4b4'
C_FAM = {'burial': '#2a78d6', 'isothermal': '#eb6834', 'linear': '#1baa6b'}
CHI_COLORS = ['#104281', '#256abf', '#5598e7', '#9ec5f4', '#cde2fb', '#f3f6fa']
STROKE = [pe.withStroke(linewidth=3.2, foreground=INK)]

spec = M.load_spectrum()
N_FIT = spec['n_fit']
res = json.load(open(os.path.join(DATA_DIR, f'N{N_SEL}.json')))
SM = F.SpectrumModelFree(spec, res['f'], res['r'])


def nodes(family, t_form, T):
    if family == 'isothermal':
        return [t_form, 0.0], [T, T]
    return [t_form, 0.0], [T, T_END_LINEAR]


def _eval(args):
    family, t_form, T = args
    c2, age, _ = SM.evaluate(*nodes(family, t_form, T), dt_myr=DT_MYR)
    return dict(t_form_Ma=t_form, T_C=T, chi2=c2, bulk_age_Ma=age)


def compute(family, jobs, t_forms):
    items = [(family, tf, T) for tf in t_forms for T in FAMILIES[family]['T_grid']]
    with Pool(jobs) as p:
        rows = p.map(_eval, items, chunksize=20)
    return pd.DataFrame(rows)


def load_or_compute(family, jobs, recompute):
    """Load the cached grid and compute only the crystallization ages it lacks."""
    path = os.path.join(DATA_DIR, f'maps_alt_{family}_N{N_SEL}.csv')
    old = pd.read_csv(path) if os.path.exists(path) and not recompute else None
    have = set() if old is None else set(np.round(old['t_form_Ma'], 6))
    todo = [tf for tf in T_FORM_GRID if round(tf, 6) not in have]
    if todo:
        new = compute(family, jobs, todo)
        old = new if old is None else pd.concat([old, new], ignore_index=True)
        old = old.sort_values(['t_form_Ma', 'T_C']).reset_index(drop=True)
        old.to_csv(path, index=False)
    return old[old['t_form_Ma'].isin(T_FORM_GRID)].reset_index(drop=True)


def best(df, age_ok=False, t_window=None):
    g = df
    if age_ok:
        g = g[(g['bulk_age_Ma'] >= MEASURED_AGE[0]) & (g['bulk_age_Ma'] <= MEASURED_AGE[1])]
    if t_window is not None:
        g = g[(g['t_form_Ma'] >= t_window[0]) & (g['t_form_Ma'] <= t_window[1])]
    return None if g.empty else g.loc[g['chi2'].idxmin()]


def save(fig, name, **kw):
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(OUT, f'{name}.{ext}'), dpi=200, **kw)
    plt.close(fig)


def main():
    jobs = int(ARGS[ARGS.index('--jobs') + 1]) if '--jobs' in ARGS else 2
    maps = {fam: load_or_compute(fam, jobs, '--recompute' in ARGS) for fam in FAMILIES}
    dof = N_FIT - 2

    # burial reference (3 parameters per crystallization age; grid from fig_winsor_mdd_free.py)
    gb = pd.read_csv(os.path.join(DATA_DIR, f'maps_N{N_SEL}.csv'))
    bb = best(gb.rename(columns={'T_max_C': 'T_C'}), age_ok=True)

    # ---------------- summary table ----------------
    rows = []
    for fam, df in maps.items():
        for tag, kw in [('global', {}), ('age 130-180 Ma', dict(age_ok=True)),
                        ('age ok, t_form 180-210', dict(age_ok=True, t_window=GEOL_T_FORM))]:
            b = best(df, **kw)
            if b is None:
                rows.append(dict(family=fam, constraint=tag)); continue
            rows.append(dict(family=fam, constraint=tag, t_form_Ma=b['t_form_Ma'], T_C=b['T_C'],
                             chi2=b['chi2'], chi2_nu=b['chi2'] / dof, bulk_age_Ma=b['bulk_age_Ma']))
    rows.append(dict(family='burial (ref.)', constraint='age 130-180 Ma', t_form_Ma=bb['t_form_Ma'],
                     T_C=bb['T_C'], chi2=bb['chi2'], chi2_nu=bb['chi2'] / (N_FIT - 3),
                     bulk_age_Ma=bb['bulk_age_Ma'], t_peak_Ma=bb['t_peak_Ma']))

    # ---------------- maps + posterior paths ----------------
    def colour_scale(nu_min):
        edges = np.r_[0.0, np.round(nu_min + np.array([0.3, 0.8, 1.8, 3.8, 6.8]), 1), 1e9]
        labels = ([f'<{edges[1]:g}'] + [f'{a:g}–{b:g}' for a, b in zip(edges[1:-2], edges[2:-1])]
                  + [f'>{edges[-2]:g}'])
        ticks = 0.5 * (np.r_[nu_min - 0.3, edges[1:-1]] + np.r_[edges[1:-1], edges[-2] + 3])
        return edges, labels, ticks, ListedColormap(CHI_COLORS), BoundaryNorm(edges, len(CHI_COLORS))

    apply_style(scale=1.1)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.8))
    rng = np.random.default_rng(1)
    tt = np.linspace(0, T_FORM_GRID.max(), 600)
    post = []
    for col, (fam, df) in enumerate(maps.items()):
        cfg = FAMILIES[fam]
        tfs, Ts = np.sort(df['t_form_Ma'].unique()), np.sort(df['T_C'].unique())
        piv = lambda c: df.pivot(index='T_C', columns='t_form_Ma', values=c).loc[Ts, tfs].to_numpy()
        TF, TT = np.meshgrid(tfs, Ts)
        cmin = df['chi2'].min()
        s = max(1.0, cmin / dof)
        thr = cmin + 2.30 * s                       # joint 1 sigma, 2 parameters
        ax = axes[0, col]
        edges, labels, ticks, cmap, norm = colour_scale(cmin / dof)
        pc = ax.pcolormesh(TF, TT, piv('chi2') / dof, cmap=cmap, norm=norm, shading='nearest', rasterized=True)
        ax.add_patch(plt.Rectangle((GEOL_T_FORM[0], cfg['ylim'][0]), np.diff(GEOL_T_FORM)[0],
                                   np.diff(cfg['ylim'])[0], fill=False, ec=MUTED, hatch='///', lw=0.8, zorder=2))
        cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.05, ticks=ticks)
        cb.ax.set_yticklabels(labels, fontsize=8.5)
        cb.set_label(r'Reduced $\chi^2$', fontsize=9, labelpad=2)
        cs = ax.contour(TF, TT, piv('bulk_age_Ma'), levels=list(MEASURED_AGE), colors=INK,
                        linewidths=1.2, linestyles='--', zorder=3)
        ax.clabel(cs, fmt=lambda v: f'{v:.0f} Ma', fontsize=9)
        c1 = ax.contour(TF, TT, piv('chi2'), levels=[thr], colors='white', linewidths=1.6, zorder=4)
        c1.set_path_effects(STROKE)
        b = best(df)
        ax.plot(b['t_form_Ma'], b['T_C'], 'D', color='white', mec=INK, ms=7, zorder=5)
        ax.set_xlim(T_FORM_GRID.max(), 0)
        ax.set_ylim(*cfg['ylim'])
        ax.set_xlabel('Crystallization age, $t_\\mathrm{form}$ (Ma)')
        ax.set_ylabel(cfg['ylabel'])
        ax.set_title(rf"{cfg['label']} (min $\chi^2_\nu$ = {cmin / dof:.2f})", fontsize=12)

        w = np.exp(-(df['chi2'] - cmin) / (2 * s)); w = w / w.sum()
        idx = rng.choice(len(df), size=N_PATHS, p=w)
        ages = df.loc[idx, 'bulk_age_Ma'].to_numpy()
        ok = (ages >= MEASURED_AGE[0]) & (ages <= MEASURED_AGE[1])
        ax2 = axes[1, col]
        tf_s = df.loc[idx, 't_form_Ma'].to_numpy() + rng.uniform(-T_FORM_STEP / 2, T_FORM_STEP / 2, N_PATHS)
        T_s = df.loc[idx, 'T_C'].to_numpy() + rng.uniform(-T_STEP / 2, T_STEP / 2, N_PATHS)
        for k in range(N_PATHS):
            n_t, n_T = nodes(fam, tf_s[k], T_s[k])
            m = tt <= tf_s[k]
            ax2.plot(tt[m], np.interp(tt[m], n_t[::-1], n_T[::-1]), color=C_MOD if ok[k] else C_OUT,
                     lw=0.6, alpha=0.25, zorder=2 if ok[k] else 1)
        n_t, n_T = nodes(fam, b['t_form_Ma'], b['T_C'])
        ax2.plot(n_t, n_T, color=INK, lw=2.0, zorder=4)
        ax2.set_xlim(T_FORM_GRID.max(), 0)
        ax2.set_ylim(0, 120)
        ax2.set_xlabel('Time (Ma)')
        ax2.set_ylabel('Temperature (°C)')
        ax2.set_title(f'He age 130–180 Ma: {100 * ok.mean():.0f}% of paths', fontsize=11)
        q = lambda a, p: float(np.percentile(a, p))
        post.append(dict(family=fam, frac_age_ok=float(ok.mean()),
                         t_form_p16=q(tf_s, 16), t_form_p50=q(tf_s, 50), t_form_p84=q(tf_s, 84),
                         T_p16=q(T_s, 16), T_p50=q(T_s, 50), T_p84=q(T_s, 84),
                         age_p16=q(ages, 16), age_p84=q(ages, 84)))
    axes[0, 0].legend(handles=[Line2D([], [], color='white', lw=1.6, path_effects=STROKE, label=r'Joint 1$\sigma$'),
                               Line2D([], [], color=INK, lw=1.2, ls='--', label='Predicted He age'),
                               plt.Rectangle((0, 0), 1, 1, fc='none', ec=MUTED, hatch='///',
                                             label='180–210 Ma window')],
                      loc='lower left', fontsize=9)
    axes[1, 0].legend(handles=[Line2D([], [], color=INK, lw=2.0, label='Best fit'),
                               Line2D([], [], color=C_MOD, lw=1.2, label='He age 130–180 Ma'),
                               Line2D([], [], color=C_OUT, lw=1.2, label='Other He age')],
                      loc='upper right', fontsize=9)
    fig.subplots_adjust(hspace=0.32, wspace=0.42)
    save(fig, f'ch2_mdd_alt_paths_N{N_SEL}', bbox_inches='tight')

    # ---------------- spectra: best age-consistent fit of each family ----------------
    apply_style()
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    u, Fs, Fe = spec['use'], spec['F_start'], spec['F_end']
    ax.axvspan(*PLATEAU, color='#f3f3f3', lw=0, zorder=0)
    for i in np.where(u)[0]:
        ax.fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0, zorder=1)
    ax.hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=3)
    handles = [Line2D([], [], color=INK, lw=2.2, label='Data (M), LB–UB box')]
    burial_nodes = ([bb['t_form_Ma'], bb['t_peak_Ma'], 50.0, 0.0], [M.T_SURF, bb['T_C'], M.T_SURF, M.T_SURF])
    cases = [('burial', burial_nodes,
              rf"Burial {bb['t_form_Ma']:.0f}→{bb['t_peak_Ma']:.0f} Ma, {bb['T_C']:.0f} °C",
              bb['chi2'] / (N_FIT - 3))]
    for fam in FAMILIES:
        b = best(maps[fam], age_ok=True)
        lab = (rf"Isothermal {b['T_C']:.0f} °C since {b['t_form_Ma']:.0f} Ma" if fam == 'isothermal'
               else rf"Linear {b['T_C']:.0f}→25 °C since {b['t_form_Ma']:.0f} Ma")
        cases.append((fam, nodes(fam, b['t_form_Ma'], b['T_C']), lab, b['chi2'] / dof))
    for z, (fam, nd, lab, nu) in enumerate(cases):
        c2, age, p = SM.evaluate(*nd, dt_myr=DT_MYR)
        ax.hlines(p, Fs, Fe, color=C_FAM[fam], lw=1.8, zorder=4 + z)
        draw_step_connectors(ax, Fs, Fe, p, color=C_FAM[fam], zorder=4 + z)
        handles.append(Line2D([], [], color=C_FAM[fam], lw=1.8,
                              label=rf"{lab}; $\chi^2_\nu$ = {nu:.1f}, He age {age:.0f} Ma"))
    ax.set_xlim(0, 0.16); ax.set_ylim(0, 1.2)
    ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
    ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
    ax.set_title('Best age-consistent fit of each path family (N = 4)', fontsize=13)
    ax.legend(handles=handles, loc='lower right', fontsize=8.5)
    fig.tight_layout()
    save(fig, f'ch2_mdd_alt_spectra_N{N_SEL}')

    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(DATA_DIR, f'alt_paths_summary_N{N_SEL}.csv'), index=False)
    pd.DataFrame(post).to_csv(os.path.join(DATA_DIR, f'alt_paths_posterior_N{N_SEL}.csv'), index=False)
    with pd.option_context('display.width', 200):
        print(summ.round(2).to_string(index=False))
        print(pd.DataFrame(post).round(1).to_string(index=False))


if __name__ == '__main__':
    main()
