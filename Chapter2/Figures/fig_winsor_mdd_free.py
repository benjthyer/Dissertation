"""
Fully free multi-domain (MDD) analysis of HT-Win-06-01b: N = 1..N_MAX domains,
each with a free 3He fraction and size r_j = a_j / a0 relative to the Stage 1
reference domain (winsor_he43_mdd_free.py).

Pipeline for each N:
  1. Domain fractions and sizes fitted to the 3He fractional and cumulative
     yields alone (Farley & Flowers 2012, A2), warm-started from N-1.
  2. Burial-and-exhumation thermal history fitted to the 4He/3He spectrum with
     the domains fixed: crystallization at t_form (20 C) -> peak T_max at t_peak
     -> 20 C by 50 Ma -> present. For each t_form in T_FORMS, (t_peak, T_max)
     are optimized by Nelder-Mead.
  3. chi^2 maps over (t_peak, T_max) at crystallization ages MAP_T_FORMS, with
     isopleths of the predicted bulk He age.

Usage:  python fig_winsor_mdd_free.py [--n-max 10] [--only 3 4] [--stage he3|thermal|maps|plots]
                                      [--recompute] [--plot-only] [--weighting absolute|relative]
Caches: generated/data/mdd_free/<weighting>/N<n>.json and maps_N<n>.csv.

Writes (generated/mdd_free/<weighting>/):
  mdd_free_N<n>.{pdf,png}       eight-panel diagnostic figure per N
  mdd_free_map_N<n>.{pdf,png}   chi^2 maps with He-age isopleths per N
  mdd_free_summary.{pdf,png}    statistics and thermal results against N
  mdd_free_domains.{pdf,png}    domain spectra for all N
  mdd_free_delta.{pdf,png}      delta plots for selected N
  mdd_free_spectra.{pdf,png}    4He/3He fits for selected N
and generated/data/mdd_free/<weighting>/summary.csv, plus LaTeX tables/macros
in ../Writing/mdd_free_report_values.tex.
"""
import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M
import winsor_he43_mdd as D
import winsor_he43_mdd_free as FR

T_FORMS = (180.0, 190.0, 200.0, 210.0)
MAP_T_FORMS = (180.0, 195.0, 210.0)
T_PEAK_STEP, T_PEAK_MIN = 2.5, 55.0
T_MAX_GRID = np.arange(30.0, 90.01, 1.0)
T_EXPOSED_MA = 50.0
MEASURED_AGE = (130.0, 180.0)
AFT_BOX = dict(t=(85.0, 100.0), T=(50.0, 70.0))
STARTS = ((80.0, 61.0), (100.0, 66.0), (65.0, 60.0), (130.0, 70.0))
PLATEAU = (0.04, 0.07)
COMPARE_N = (1, 2, 3, 5, 10)


def _opt(args, name, default):
    return args[args.index(name) + 1] if name in args else default


ARGS = sys.argv[1:]
WEIGHTING = _opt(ARGS, '--weighting', 'absolute')
DATA_DIR = os.path.join(M.DATA_OUTDIR, 'mdd_free', WEIGHTING)
FIG_DIR = os.path.join(M.OUTDIR, 'mdd_free', WEIGHTING)
TEX_VALUES = os.path.join(M.FIG_DIR, '..', 'Writing', 'mdd_free_report_values.tex')


def _path(n):
    return os.path.join(DATA_DIR, f'N{n}.json')


def _map_path(n):
    return os.path.join(DATA_DIR, f'maps_N{n}.csv')


def _load(n):
    return json.load(open(_path(n)))


def _save(n, out):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = _path(n) + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in out.items()}, fh, indent=1)
    os.replace(tmp, _path(n))


def burial_nodes(t_form, T_max, t_peak):
    return [t_form, t_peak, T_EXPOSED_MA, 0.0], [M.T_SURF, T_max, M.T_SURF, M.T_SURF]


def _model(n):
    res = _load(n)
    return res, FR.SpectrumModelFree(M.load_spectrum(), res['f'], res['r'])


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------
def fit_he3(n):
    spec = M.load_spectrum()
    init = None
    if n > 1 and os.path.exists(_path(n - 1)):
        prev = _load(n - 1)
        init = (prev['f'], prev['r'])
    _save(n, FR.fit_domains(spec, n, weighting=WEIGHTING, init=init))


def fit_thermal(n):
    from scipy.optimize import minimize
    res, sm = _model(n)
    n_fit = sm.spec['n_fit']
    thermal = []
    for tf in T_FORMS:
        def cost(v):
            tp, Tm = v
            if not (T_PEAK_MIN <= tp <= tf - 2.5 and 20.0 <= Tm <= 100.0):
                return 1e9
            return sm.evaluate(*burial_nodes(tf, Tm, tp))[0]
        best = min((minimize(cost, x0, method='Nelder-Mead',
                             options={'xatol': 0.1, 'fatol': 0.01, 'maxiter': 300})
                    for x0 in STARTS if x0[0] < tf - 2.5), key=lambda o: o.fun)
        tp, Tm = map(float, best.x)
        A = sm.modes(*burial_nodes(tf, Tm, tp))
        p = sm.predict(A)
        thermal.append(dict(t_form_Ma=tf, t_peak_Ma=tp, T_max_C=Tm, chi2=M.chi2(sm.spec, p),
                            chi2_nu=M.chi2(sm.spec, p) / (n_fit - 3), bulk_age_Ma=sm.bulk_age(A),
                            domain_ages_Ma=sm.domain_ages(A).tolist(), pred=p.tolist()))
    res = _load(n)
    res['thermal'] = thermal
    _save(n, res)


def compute_maps(n):
    _, sm = _model(n)
    rows = []
    for tf in MAP_T_FORMS:
        for tp in np.arange(T_PEAK_MIN, tf - T_PEAK_STEP + 1e-9, T_PEAK_STEP):
            for Tm in T_MAX_GRID:
                c, age, _ = sm.evaluate(*burial_nodes(tf, Tm, tp))
                rows.append((tf, tp, Tm, c, age))
    pd.DataFrame(rows, columns=['t_form_Ma', 't_peak_Ma', 'T_max_C', 'chi2', 'bulk_age_Ma']
                 ).to_csv(_map_path(n), index=False)


def _pool_map(func, items):
    if not items:
        return
    from multiprocessing import Pool
    with Pool(min(len(items), os.cpu_count() or 1)) as pool:
        pool.map(func, items)


def run(n_values, recompute, stages):
    if 'he3' in stages:
        for n in sorted(n_values):
            if recompute or not os.path.exists(_path(n)):
                fit_he3(n)
    if 'thermal' in stages:
        _pool_map(fit_thermal, [n for n in n_values if recompute or 'thermal' not in _load(n)])
    if 'maps' in stages:
        _pool_map(compute_maps, [n for n in sorted(n_values, reverse=True)
                                 if recompute or not os.path.exists(_map_path(n))])


def best_thermal(res, age_consistent=True):
    th = res['thermal']
    if age_consistent:
        th = [t for t in th if MEASURED_AGE[0] <= t['bulk_age_Ma'] <= MEASURED_AGE[1]] or th
    return min(th, key=lambda t: t['chi2'])


# ---------------------------------------------------------------------------
# Plots and report values
# ---------------------------------------------------------------------------
def make_plots(results):
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    import matplotlib.patheffects as pe
    from thermochr_utils import draw_step_connectors
    from plot_style import apply_style

    os.makedirs(FIG_DIR, exist_ok=True)
    INK, MUTED, BOX, C_MOD, C_REF, C_AFT = '#222222', '#8a8a8a', '#d9d9d9', '#2a78d6', '#eb6834', '#eb6834'
    RAMP5 = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b']
    TF_RAMP = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab']
    CHI_LEVELS = [0, 1.5, 2, 3, 5, 10, 1e9]
    CHI_COLORS = ['#104281', '#256abf', '#5598e7', '#9ec5f4', '#cde2fb', '#f3f6fa']
    STROKE = [pe.withStroke(linewidth=3.2, foreground=INK)]
    spec = M.load_spectrum()
    d = D.he3_data(spec)
    n_fit = spec['n_fit']
    steps = np.arange(1, spec['F_end'].size + 1)
    low = ~np.isfinite(spec['R_LB']) | ~spec['use']
    x_arr = 10000.0 / (spec['T_C'] + 273.0)
    Fs, Fe, u = spec['F_start'], spec['F_end'], spec['use']
    ns = sorted(results)
    lnD_ref = d['lnD_stage1']

    # ---- summary table ----
    rows = []
    for n in ns:
        r = results[n]
        bt, bu = best_thermal(r, True), best_thermal(r, False)
        main = int(np.argmax(r['f']))
        rows.append(dict(n=n, k=r['k'], rms_yield=r['rms_yield'], bic=r['bic'], aic=r['aic'],
                         arrhenius_chi2_nu=r['arrhenius_chi2_nu'],
                         f_main=r['f'][main], r_main=r['r'][main],
                         f_fast=float(sum(fj for fj, rj in zip(r['f'], r['r']) if rj < 0.1)),
                         spec_chi2_nu=bt['chi2_nu'], t_form=bt['t_form_Ma'], t_peak=bt['t_peak_Ma'],
                         T_max=bt['T_max_C'], age=bt['bulk_age_Ma'],
                         spec_chi2_nu_any=bu['chi2_nu'], any_t_form=bu['t_form_Ma'], any_t_peak=bu['t_peak_Ma'],
                         any_T_max=bu['T_max_C'], any_age=bu['bulk_age_Ma'],
                         f_j=' '.join(f'{x:.5f}' for x in r['f']), r_j=' '.join(f'{x:.4g}' for x in r['r'])))
    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(DATA_DIR, 'summary.csv'), index=False)
    print(summ[['n', 'rms_yield', 'bic', 'arrhenius_chi2_nu', 'f_main', 'r_main', 'f_fast', 'spec_chi2_nu',
                't_form', 't_peak', 'T_max', 'age']].round(4).to_string(index=False))

    # ---- map statistics (joint 1-sigma per N over the mapped t_forms) ----
    map_stats = {}
    for n in ns:
        if os.path.exists(_map_path(n)):
            g = pd.read_csv(_map_path(n))
            g['chi2_nu'] = g['chi2'] / (n_fit - 3)
            cmin = g['chi2'].min()
            thr = cmin + 3.53 * max(1.0, cmin / (n_fit - 3))
            ok = g[g['chi2'] <= thr]
            ok_age = ok[(ok['bulk_age_Ma'] >= MEASURED_AGE[0]) & (ok['bulk_age_Ma'] <= MEASURED_AGE[1])]
            map_stats[n] = dict(grid=g, thr=thr, ok=ok, ok_age=ok_age)

    # ---- per-N diagnostic figure ----
    apply_style(scale=1.25)
    for n in ns:
        r = results[n]
        f, rr = np.asarray(r['f']), np.asarray(r['r'])
        Fm = np.asarray(r['model_F'])
        fig, ax = plt.subplots(2, 4, figsize=(21, 9.5))
        a = ax.ravel()
        a[0].plot(steps, spec['dF3'], 'o', color=INK, ms=6, mec='white', zorder=3)
        a[0].plot(steps[low], spec['dF3'][low], 'o', mfc='white', mec=INK, ms=6, zorder=4)
        a[0].plot(steps, np.diff(np.r_[0.0, Fm]), color=C_MOD, lw=1.5, marker='D', ms=4, zorder=5)
        a[0].set_yscale('log')
        a[0].set_xlabel('Step')
        a[0].set_ylabel(r'Fraction of $^3$He in step')
        a[0].set_title('(a) Fractional yields (fitted)')
        a[1].plot(steps, spec['F_end'], 'o', color=INK, ms=6, mec='white', zorder=3)
        a[1].plot(steps, Fm, color=C_MOD, lw=1.5, marker='D', ms=4, zorder=4)
        a[1].set_xlabel('Step')
        a[1].set_ylabel(r'Cumulative $^3$He fraction')
        a[1].set_title('(b) Cumulative yields (fitted)')
        xr = np.array([x_arr.min() - 0.15, x_arr.max() + 0.15])
        a[2].plot(xr, np.log(M.D0_A2) - M.EA * xr / (M.R_CAL * 1e4), color=C_REF, lw=1.3, ls='--')
        a[2].plot(x_arr, d['lnD'], color=MUTED, lw=0.6)
        a[2].errorbar(x_arr, d['lnD'], yerr=d['sigma'], fmt='o', ms=5, color=INK, mec='white', elinewidth=0.8)
        a[2].plot(x_arr, r['model_lnD'], color=C_MOD, lw=1.2, marker='D', ms=4)
        a[2].set_xlabel(r'$10^4/T$ (K$^{-1}$)')
        a[2].set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
        a[2].set_title(rf"(c) Arrhenius (consequence), $\chi^2_\nu$ = {r['arrhenius_chi2_nu']:.2f}")
        a[3].axvspan(*PLATEAU, color='#f1f1f1', lw=0)
        a[3].axhline(0, color=C_REF, lw=1.3, ls='--')
        a[3].errorbar(spec['F_end'], d['lnD'] - lnD_ref, yerr=d['sigma'], fmt='o', ms=5, color=INK,
                      mec='white', elinewidth=0.8)
        a[3].plot(Fm, np.asarray(r['model_lnD']) - lnD_ref, color=C_MOD, lw=1.5, marker='D', ms=4)
        a[3].set_xlim(0, 0.16)
        a[3].set_xlabel(r'$\Sigma F_{^3\mathrm{He}}$')
        a[3].set_ylabel(r'$\Delta\ln(D/a^2)$ from Stage 1')
        a[3].set_title('(d) Delta plot (consequence)')
        a[4].vlines(np.log10(rr), 1e-4, f, color=C_MOD, lw=6)
        a[4].axvline(0, color=C_REF, lw=1.3, ls='--')
        a[4].set_yscale('log')
        a[4].set_ylim(1e-4, 1.5)
        a[4].set_xlim(-6.2, 3.2)
        a[4].set_xlabel(r'$\log_{10}(r/r_0)$')
        a[4].set_ylabel(r'Fraction of $^3$He')
        a[4].set_title(f'(e) Domain spectrum, N = {n}')
        bt, bu = best_thermal(r, True), best_thermal(r, False)
        a[5].axvspan(*PLATEAU, color='#f1f1f1', lw=0)
        for i in np.where(u)[0]:
            a[5].fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0)
        a[5].hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=3)
        p = np.asarray(bt['pred'])
        a[5].hlines(p, Fs, Fe, color=C_MOD, lw=1.8, zorder=4)
        draw_step_connectors(a[5], Fs, Fe, p, color=C_MOD, zorder=4)
        a[5].set_xlim(0, 0.16)
        a[5].set_ylim(0, 1.2)
        a[5].set_xlabel(r'$\Sigma F_{^3\mathrm{He}}$')
        a[5].set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
        a[5].set_title(rf"(f) $^4$He/$^3$He, $\chi^2_\nu$ = {bt['chi2_nu']:.2f}")
        tt = np.linspace(0, 210, 300)
        for th, col in zip(r['thermal'], TF_RAMP):
            a[6].plot(tt, M.path_T(*burial_nodes(th['t_form_Ma'], th['T_max_C'], th['t_peak_Ma']), tt),
                      color=col, lw=1.4, label=f"{th['t_form_Ma']:.0f} Ma: $\\chi^2_\\nu$ {th['chi2_nu']:.2f}, "
                                               f"age {th['bulk_age_Ma']:.0f}")
        a[6].plot(tt, M.path_T(*burial_nodes(bt['t_form_Ma'], bt['T_max_C'], bt['t_peak_Ma']), tt),
                  color=INK, lw=2.2)
        a[6].add_patch(Rectangle((AFT_BOX['t'][0], AFT_BOX['T'][0]), 15, 20, fill=False, ec=C_AFT, lw=1.6))
        a[6].set_xlim(210, 0)
        a[6].set_ylim(10, 90)
        a[6].set_xlabel('Time (Ma)')
        a[6].set_ylabel('Temperature (°C)')
        a[6].set_title('(g) Best burial path per crystallization age')
        a[6].legend(fontsize=9, loc='upper left')
        a[7].axis('off')
        lines = [f"N = {n} free domains ({WEIGHTING} yield weighting)",
                 "Domains (fraction of 3He, r/r0, fraction degassed in lab):"]
        lines += [f"  {fj:8.5f}  {rj:9.4g}  {qj:5.3f}" for fj, rj, qj in zip(f, rr, r['frac_degassed_in_lab'])]
        lines += ["", f"RMS yield misfit: {r['rms_yield']:.2e}", f"BIC: {r['bic']:.1f}   (k = {r['k']})",
                  "", "Best burial path with He age 130-180 Ma:",
                  f"  {bt['t_form_Ma']:.0f} Ma -> {bt['T_max_C']:.1f} C at {bt['t_peak_Ma']:.1f} Ma",
                  f"  He age {bt['bulk_age_Ma']:.0f} Ma; spectrum chi2_nu {bt['chi2_nu']:.2f}"]
        a[7].text(0.0, 1.0, '\n'.join(lines), va='top', ha='left', family='monospace', fontsize=10.5,
                  transform=a[7].transAxes)
        fig.tight_layout()
        for ext in ('pdf', 'png'):
            fig.savefig(os.path.join(FIG_DIR, f'mdd_free_N{n}.{ext}'), dpi=150)
        plt.close(fig)

    # ---- per-N chi^2 maps with He-age isopleths ----
    apply_style(scale=1.1)
    cmap, norm = ListedColormap(CHI_COLORS), BoundaryNorm(CHI_LEVELS, len(CHI_COLORS))
    for n, ms in map_stats.items():
        g, thr = ms['grid'], ms['thr']
        fig, axes = plt.subplots(1, len(MAP_T_FORMS), figsize=(13, 4.6), sharey=True)
        for ax, tf in zip(axes, MAP_T_FORMS):
            gg = g[np.isclose(g['t_form_Ma'], tf)]
            tps = np.sort(gg['t_peak_Ma'].unique())
            piv = lambda col: gg.pivot(index='T_max_C', columns='t_peak_Ma', values=col).loc[:, tps].to_numpy()
            TP, TM = np.meshgrid(tps, np.sort(gg['T_max_C'].unique()))
            pc = ax.pcolormesh(TP, TM, piv('chi2_nu'), cmap=cmap, norm=norm, shading='nearest', rasterized=True)
            cs = ax.contour(TP, TM, piv('bulk_age_Ma'), levels=list(MEASURED_AGE), colors=INK,
                            linewidths=1.2, linestyles='--')
            ax.clabel(cs, fmt=lambda v: f'{v:.0f} Ma', fontsize=9)
            C1 = piv('chi2')
            if (C1 <= thr).any():
                c1 = ax.contour(TP, TM, C1, levels=[thr], colors='white', linewidths=1.6)
                c1.set_path_effects(STROKE)
            ax.add_patch(Rectangle((AFT_BOX['t'][0], AFT_BOX['T'][0]), 15, 20, fill=False, ec=C_AFT, lw=1.8))
            j = gg['chi2'].idxmin()
            ax.plot(gg.loc[j, 't_peak_Ma'], gg.loc[j, 'T_max_C'], 'D', color='white', mec=INK, ms=7, zorder=5)
            ax.set_xlim(205, T_PEAK_MIN)
            ax.set_title(rf'Crystallized at {tf:.0f} Ma ($\chi^2_\nu$ = {gg["chi2_nu"].min():.2f})', fontsize=12)
        axes[0].set_ylabel(r'Peak temperature, $T_\mathrm{max}$ (°C)')
        axes[len(axes) // 2].set_xlabel('Time of peak temperature (Ma)')
        cb = fig.colorbar(pc, ax=axes, ticks=[0.75, 1.75, 2.5, 4, 7.5, 15], pad=0.015, fraction=0.025)
        cb.ax.set_yticklabels(['<1.5', '1.5–2', '2–3', '3–5', '5–10', '>10'])
        cb.set_label(r'Reduced $\chi^2$ ($^4$He/$^3$He)')
        axes[0].legend(handles=[Line2D([], [], color='white', lw=1.6, path_effects=STROKE, label=r'Joint 1$\sigma$'),
                                Line2D([], [], color=INK, lw=1.2, ls='--', label='Predicted He age'),
                                Line2D([], [], color=C_AFT, lw=1.8, label='AFT peak window')],
                       loc='upper left', fontsize=9)
        fig.suptitle(f'N = {n} free domains', fontsize=13, y=1.0)
        for ext in ('pdf', 'png'):
            fig.savefig(os.path.join(FIG_DIR, f'mdd_free_map_N{n}.{ext}'), dpi=170, bbox_inches='tight')
        plt.close(fig)

    # ---- summary across N ----
    apply_style(scale=1.1)
    fig, ax = plt.subplots(2, 3, figsize=(15, 8.5))
    specs = [('rms_yield', 'RMS yield misfit (fitted)'), ('bic', 'BIC (yield fit)'),
             ('arrhenius_chi2_nu', r'Arrhenius $\chi^2_\nu$ (consequence)'),
             ('spec_chi2_nu', r'$^4$He/$^3$He $\chi^2_\nu$ (best age-consistent path)'),
             ('T_max', r'Best $T_\mathrm{max}$ (°C)'), ('t_peak', r'Best $t_\mathrm{peak}$ (Ma)')]
    for a, (col, lab) in zip(ax.ravel(), specs):
        a.plot(summ['n'], summ[col], color=C_MOD, lw=2, marker='o', ms=7, mec='white')
        a.set_title(lab, fontsize=13)
        a.set_xlabel('Number of domains, N')
        a.set_xticks(summ['n'])
    for nn, ms in map_stats.items():                 # 1-sigma ranges from the maps
        lo_T, hi_T = ms['ok_age']['T_max_C'].agg(['min', 'max']) if len(ms['ok_age']) else (np.nan, np.nan)
        lo_t, hi_t = ms['ok_age']['t_peak_Ma'].agg(['min', 'max']) if len(ms['ok_age']) else (np.nan, np.nan)
        ax[1, 1].vlines(nn, lo_T, hi_T, color=C_MOD, lw=6, alpha=0.25)
        ax[1, 2].vlines(nn, lo_t, hi_t, color=C_MOD, lw=6, alpha=0.25)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIG_DIR, f'mdd_free_summary.{ext}'), dpi=170)
    plt.close(fig)

    # ---- domain spectra for all N ----
    apply_style()
    fig, ax = plt.subplots()
    for n in ns:
        r = results[n]
        ax.scatter(np.log10(r['r']), np.full(len(r['r']), n), s=15 + 380 * np.sqrt(np.asarray(r['f'])),
                   color=C_MOD, alpha=0.7, edgecolor='white', lw=0.8, zorder=3)
    ax.axvline(0, color=C_REF, lw=1.4, ls='--')
    ax.text(0.08, ns[-1] + 0.55, 'Stage 1 reference', color=C_REF, fontsize=9)
    ax.set_xlim(-6.2, 3.2)
    ax.set_ylim(0.3, ns[-1] + 1.0)
    ax.set_yticks(ns)
    ax.set_xlabel(r'$\log_{10}(r/r_0)$')
    ax.set_ylabel('Number of domains, N')
    ax.set_title(r'Domain spectra (area $\propto\sqrt{f}$)', fontsize=13)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIG_DIR, f'mdd_free_domains.{ext}'), dpi=200)
    plt.close(fig)

    # ---- delta plots and spectra for selected N ----
    cmp_n = [n for n in COMPARE_N if n in results]
    ramp = dict(zip(cmp_n, RAMP5[-len(cmp_n):]))
    fig, ax = plt.subplots()
    ax.axvspan(*PLATEAU, color='#f3f3f3', lw=0, zorder=0)
    ax.axhline(0, color=C_REF, lw=1.4, ls='--', zorder=1)
    ax.errorbar(spec['F_end'], d['lnD'] - lnD_ref, yerr=d['sigma'], fmt='o', ms=5, color=INK, mec='white',
                mew=0.7, elinewidth=0.9, zorder=3)
    for n in cmp_n:
        r = results[n]
        ax.plot(r['model_F'], np.asarray(r['model_lnD']) - lnD_ref, color=ramp[n], lw=1.6, zorder=4)
    ax.set_xlim(0, 0.16)
    ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
    ax.set_ylabel(r'$\Delta\ln(D/a^2)$ from Stage 1 line')
    ax.set_title('Delta plot: free multi-domain fits', fontsize=14)
    ax.legend(handles=[Line2D([], [], color=INK, marker='o', ls='none', label='Data')] +
              [Line2D([], [], color=ramp[n], lw=1.6, label=rf"N = {n}, Arrhenius $\chi^2_\nu$ = "
                                                        rf"{results[n]['arrhenius_chi2_nu']:.2f}")
               for n in cmp_n], loc='upper right', fontsize=9.5)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIG_DIR, f'mdd_free_delta.{ext}'), dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots()
    ax.axvspan(*PLATEAU, color='#f3f3f3', lw=0, zorder=0)
    for i in np.where(u)[0]:
        ax.fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0, zorder=1)
    ax.hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=3)
    handles = [Line2D([], [], color=INK, lw=2.2, label='Data (M), LB–UB box')]
    for n in cmp_n:
        bt = best_thermal(results[n], True)
        p = np.asarray(bt['pred'])
        ax.hlines(p, Fs, Fe, color=ramp[n], lw=1.6, zorder=4)
        draw_step_connectors(ax, Fs, Fe, p, color=ramp[n], zorder=4)
        handles.append(Line2D([], [], color=ramp[n], lw=1.6,
                              label=rf"N = {n}: {bt['t_form_Ma']:.0f}→{bt['t_peak_Ma']:.0f} Ma, "
                                    rf"{bt['T_max_C']:.0f} °C; $\chi^2_\nu$ = {bt['chi2_nu']:.1f}"))
    ax.set_xlim(0, 0.16)
    ax.set_ylim(0, 1.2)
    ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
    ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
    ax.set_title('Burial-path fits, free multi-domain models', fontsize=14)
    ax.legend(handles=handles, loc='lower right', fontsize=8.5)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIG_DIR, f'mdd_free_spectra.{ext}'), dpi=200)
    plt.close(fig)

    write_report_values(summ, map_stats, results)


def write_report_values(summ, map_stats, results):
    """LaTeX table rows and a few macros for the report."""
    lines = ['% Auto-generated by Chapter2/Figures/fig_winsor_mdd_free.py -- do not edit by hand.']
    rows = []
    for _, s in summ.iterrows():
        n = int(s['n'])
        ms = map_stats.get(n)
        if ms is not None and len(ms['ok_age']):
            Trng = f"{ms['ok_age']['T_max_C'].min():.0f}--{ms['ok_age']['T_max_C'].max():.0f}"
            trng = f"{ms['ok_age']['t_peak_Ma'].min():.1f}--{ms['ok_age']['t_peak_Ma'].max():.1f}"
        else:
            Trng = trng = '--'
        rows.append(f"{n} & {int(s['k'])} & {1e4 * s['rms_yield']:.2f} & {s['bic']:.1f} & "
                    f"{s['arrhenius_chi2_nu']:.2f} & {100 * s['f_fast']:.1f} & {s['r_main']:.2f} & "
                    f"{s['spec_chi2_nu']:.2f} & {s['t_form']:.0f} & {s['t_peak']:.1f} & {s['T_max']:.1f} & "
                    f"{s['age']:.0f} & {Trng} & {trng} \\\\")
    lines.append('\\newcommand{\\MDDFreeTableRows}{%')
    lines += rows
    lines.append('}')
    best_bic = summ.loc[summ['bic'].idxmin()]
    best_spec = summ.loc[summ['spec_chi2_nu'].idxmin()]
    macros = dict(MDDFreeBestBicN=f"{int(best_bic['n'])}", MDDFreeBestSpecN=f"{int(best_spec['n'])}",
                  MDDFreeBestSpecChi=f"{best_spec['spec_chi2_nu']:.2f}",
                  MDDFreeTmaxMin=f"{summ['T_max'].min():.0f}", MDDFreeTmaxMax=f"{summ['T_max'].max():.0f}",
                  MDDFreeTpeakMin=f"{summ['t_peak'].min():.0f}", MDDFreeTpeakMax=f"{summ['t_peak'].max():.0f}",
                  MDDFreeNmax=f"{int(summ['n'].max())}")
    for k, v in macros.items():
        lines.append(f'\\newcommand{{\\{k}}}{{{v}}}')
    with open(TEX_VALUES, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    n_max = int(_opt(ARGS, '--n-max', 10))
    only = [int(a) for a in ARGS[ARGS.index('--only') + 1:] if a.isdigit()] if '--only' in ARGS else None
    n_values = only or list(range(1, n_max + 1))
    stage = _opt(ARGS, '--stage', 'all')
    stages = {'he3', 'thermal', 'maps'} if stage == 'all' else {stage}
    if '--plot-only' not in ARGS and stage != 'plots':
        run(n_values, '--recompute' in ARGS, stages)
    if stage in ('all', 'plots') or '--plot-only' in ARGS:
        results = {n: _load(n) for n in range(1, n_max + 1)
                   if os.path.exists(_path(n)) and 'thermal' in _load(n)}
        make_plots(results)
