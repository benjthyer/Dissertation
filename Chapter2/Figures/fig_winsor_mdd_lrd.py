"""
Multi-domain LRD for HT-Win-06-01b: how many LRD domains do the 3He data
support, and what does each choice imply for the thermal history?

For N = 1..N_MAX LRD domains (winsor_he43_mdd.fit_lrd_mdd):
  * the HRD holds >= 92.5% of the 3He and sits on the Stage 1 line (as published);
  * N LRD domains (same Ea and D0, free radii and fractions, total <= 7.5%)
    are fitted to the apparent ln(D/a^2) of every step (Arrhenius/delta plot);
  * with those domains fixed, the burial-and-exhumation history of
    fig_winsor_burial_path.py (crystallization t_form -> peak T_max at t_peak ->
    20 C by 50 Ma) is fitted to the 4He/3He spectrum: for each t_form in
    T_FORMS, (t_peak, T_max) are optimized by Nelder-Mead from several starts.
Statistics are reported for you to judge over-fitting: reduced chi^2, AIC and
BIC of the 3He fit (k = 2N parameters, 34 steps), and the spectrum reduced
chi^2 of the best thermal fit (age-consistent and unconstrained).

The 3He fits run in order of N, each warm-started from the N-1 solution
plus one new domain (Farley & Flowers 2012 added domains one at a time); the
thermal fits then run in parallel. Results are cached in
generated/data/mdd/N<n>.json; pass --recompute to refit everything,
--n-max K to change the largest N (default 10), --only n1 n2 ... to fit just
those N, and --plot-only to skip fitting.

Writes: generated/winsor_mdd_model_selection.{pdf,png}
        generated/winsor_mdd_delta_compare.{pdf,png}
        generated/winsor_mdd_spectrum_compare.{pdf,png}
        generated/winsor_mdd_domains.{pdf,png}
        generated/mdd/arrhenius_N<n>.{pdf,png}   (one per N)
        generated/data/mdd/N<n>.json, generated/data/winsor_mdd_summary.csv
"""
import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M
import winsor_he43_mdd as D

N_MAX_DEFAULT = 10
T_FORMS = (180.0, 190.0, 200.0, 210.0)
T_EXPOSED_MA = 50.0
MEASURED_AGE = (130.0, 180.0)
STARTS = ((80.0, 61.0), (100.0, 66.0), (65.0, 60.0), (130.0, 70.0))
MDD_DATA = os.path.join(M.DATA_OUTDIR, 'mdd')
MDD_FIGS = os.path.join(M.OUTDIR, 'mdd')
COMPARE_N = (1, 2, 3, 5, 10)


def burial_nodes(t_form, T_max, t_peak):
    return [t_form, t_peak, T_EXPOSED_MA, 0.0], [M.T_SURF, T_max, M.T_SURF, M.T_SURF]


def _path(n):
    return os.path.join(MDD_DATA, f'N{n}.json')


def _save(n, out):
    os.makedirs(MDD_DATA, exist_ok=True)
    with open(_path(n), 'w') as fh:
        json.dump({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in out.items()}, fh, indent=1)


def fit_he3(n):
    """3He fit with n LRD domains, warm-started from the cached (n-1)-domain fit."""
    spec = M.load_spectrum()
    init = None
    if n > 1 and os.path.exists(_path(n - 1)):
        prev = json.load(open(_path(n - 1)))
        init = (prev['f'], prev['r'])
    _save(n, D.fit_lrd_mdd(spec, n, init=init))


def fit_thermal(n):
    """Burial-path fit to the 4He/3He spectrum with the cached n-domain LRD."""
    from scipy.optimize import minimize
    spec = M.load_spectrum()
    res = json.load(open(_path(n)))
    sm = D.SpectrumModel(spec, np.asarray(res['f']), np.asarray(res['r']))
    thermal = []
    for tf in T_FORMS:
        def cost(v):
            tp, Tm = v
            if not (55.0 <= tp <= tf - 2.5 and 20.0 <= Tm <= 100.0):
                return 1e9
            return sm.evaluate(*burial_nodes(tf, Tm, tp))[0]
        best = min((minimize(cost, x0, method='Nelder-Mead',
                             options={'xatol': 0.1, 'fatol': 0.01, 'maxiter': 300})
                    for x0 in STARTS if x0[0] < tf - 2.5), key=lambda o: o.fun)
        tp, Tm = map(float, best.x)
        chi, age, pred = sm.evaluate(*burial_nodes(tf, Tm, tp))
        thermal.append(dict(t_form_Ma=tf, t_peak_Ma=tp, T_max_C=Tm, chi2=chi,
                            chi2_nu=chi / (spec['n_fit'] - 3), bulk_age_Ma=age, pred=pred.tolist()))
    res['thermal'] = thermal
    _save(n, res)


def load_or_fit(n_values, recompute):
    """3He fits run in order of n (each warm-starts from n-1); the thermal
    fits then run in parallel."""
    for n in sorted(n_values):
        if recompute or not os.path.exists(_path(n)):
            fit_he3(n)
    todo = [n for n in n_values if 'thermal' not in json.load(open(_path(n)))]
    if todo:
        from multiprocessing import Pool
        with Pool(min(len(todo), os.cpu_count() or 1)) as pool:
            pool.map(fit_thermal, todo)
    return {n: json.load(open(_path(n))) for n in range(1, max(n_values) + 1) if os.path.exists(_path(n))}


def best_thermal(res, age_consistent=True):
    th = res['thermal']
    if age_consistent:
        ok = [t for t in th if MEASURED_AGE[0] <= t['bulk_age_Ma'] <= MEASURED_AGE[1]]
        th = ok or th
    return min(th, key=lambda t: t['chi2'])


def make_plots(results):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from thermochr_utils import draw_step_connectors
    from plot_style import apply_style
    apply_style()
    os.makedirs(MDD_FIGS, exist_ok=True)
    INK, MUTED, BOX, C_REF = '#222222', '#8a8a8a', '#d9d9d9', '#eb6834'
    RAMP = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b']   # light -> dark, N increasing
    spec = M.load_spectrum()
    d = D.he3_data(spec)
    ns = sorted(results)
    cmp_n = [n for n in COMPARE_N if n in results]
    ramp = dict(zip(cmp_n, RAMP[-len(cmp_n):] if len(cmp_n) < len(RAMP) else RAMP))

    # summary table
    rows = []
    for n in ns:
        r = results[n]
        bt, bu = best_thermal(r, True), best_thermal(r, False)
        rows.append(dict(n_lrd=n, f_total=r['f_total'], he3_chi2=r['chi2'], he3_dof=r['dof'],
                         he3_chi2_nu=r['chi2_nu'], he3_aic=r['aic'], he3_bic=r['bic'],
                         spec_chi2_nu_best=bu['chi2_nu'], best_t_form=bu['t_form_Ma'],
                         best_t_peak=bu['t_peak_Ma'], best_T_max=bu['T_max_C'], best_age=bu['bulk_age_Ma'],
                         spec_chi2_nu_age_ok=bt['chi2_nu'], age_ok_t_form=bt['t_form_Ma'],
                         age_ok_t_peak=bt['t_peak_Ma'], age_ok_T_max=bt['T_max_C'], age_ok_age=bt['bulk_age_Ma'],
                         f_j=' '.join(f'{x:.4f}' for x in r['f']), r_j=' '.join(f'{x:.4g}' for x in r['r'])))
    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(M.DATA_OUTDIR, 'winsor_mdd_summary.csv'), index=False)
    print(summ[['n_lrd', 'f_total', 'he3_chi2_nu', 'he3_bic', 'spec_chi2_nu_age_ok',
                'age_ok_t_form', 'age_ok_t_peak', 'age_ok_T_max', 'age_ok_age']].round(3).to_string(index=False))

    # --- model selection ---
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.0))
    for ax, col, lab in zip(axes, ['he3_chi2_nu', 'he3_bic', 'spec_chi2_nu_age_ok'],
                            [r'$^3$He fit: reduced $\chi^2$', r'$^3$He fit: BIC',
                             r'$^4$He/$^3$He fit: reduced $\chi^2$']):
        ax.plot(summ['n_lrd'], summ[col], color='#2a78d6', lw=2, marker='o', ms=7, mec='white')
        ax.set_xlabel('Number of LRD domains')
        ax.set_title(lab, fontsize=13)
        ax.set_xticks(ns)
    axes[2].text(0.98, 0.95, 'best burial path with\nHe age 130–180 Ma', transform=axes[2].transAxes,
                 ha='right', va='top', fontsize=10, color='#555555')
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(M.OUTDIR, f'winsor_mdd_model_selection.{ext}'), dpi=200)
    plt.close(fig)

    # --- delta plot comparison ---
    fig, ax = plt.subplots()
    ax.axvspan(0.04, 0.07, color='#f3f3f3', lw=0, zorder=0)
    ax.axhline(0, color=C_REF, lw=1.4, ls='--', zorder=1)
    dd = d['lnD'] - d['lnD_stage1']
    ax.errorbar(spec['F_end'], dd, yerr=d['sigma'], fmt='o', ms=5, color=INK, mec='white', mew=0.7,
                elinewidth=0.9, zorder=3)
    for n in cmp_n:
        r = results[n]
        ax.plot(r['model_F'], np.asarray(r['model_lnD']) - d['lnD_stage1'], color=ramp[n], lw=1.6, zorder=4)
    ax.set_xlim(0, 0.16)
    ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
    ax.set_ylabel(r'$\Delta\ln(D/a^2)$ from Stage 1 line')
    ax.set_title('Delta plot: multi-domain LRD fits', fontsize=14)
    ax.legend(handles=[Line2D([], [], color=INK, marker='o', ls='none', label='Data')] +
              [Line2D([], [], color=ramp[n], lw=1.6,
                      label=rf"{n} LRD domain{'s' if n > 1 else ''}, $\chi^2_\nu$ = {results[n]['chi2_nu']:.2f}")
               for n in cmp_n], loc='upper right', fontsize=9.5)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(M.OUTDIR, f'winsor_mdd_delta_compare.{ext}'), dpi=200)
    plt.close(fig)

    # --- 4He/3He spectrum comparison ---
    u, Fs, Fe = spec['use'], spec['F_start'], spec['F_end']
    fig, ax = plt.subplots()
    ax.axvspan(0.04, 0.07, color='#f3f3f3', lw=0, zorder=0)
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
    ax.set_title('Burial-path fits with multi-domain LRD', fontsize=14)
    ax.legend(handles=handles, loc='lower right', fontsize=8.5)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(M.OUTDIR, f'winsor_mdd_spectrum_compare.{ext}'), dpi=200)
    plt.close(fig)

    # --- domain spectra ---
    fig, ax = plt.subplots()
    for n in ns:
        r = results[n]
        ax.scatter(np.log10(r['r']), np.full(len(r['r']), n), s=30000 * np.asarray(r["f"]),
                   color='#2a78d6', alpha=0.75, edgecolor='white', lw=0.8, zorder=3)
        ax.text(0.15, n, f"{100 * r['f_total']:.1f}%", va='center', fontsize=9, color='#555555')
    ax.axvline(0, color=C_REF, lw=1.4, ls='--')
    ax.text(-0.05, ns[-1] + 0.6, 'HRD', color=C_REF, ha='right', fontsize=10)
    ax.set_xlim(-6.2, 0.9)
    ax.set_ylim(0.3, ns[-1] + 1.0)
    ax.set_yticks(ns)
    ax.set_xlabel(r'$\log_{10}(a_\mathrm{LRD}/a_\mathrm{HRD})$')
    ax.set_ylabel('Number of LRD domains')
    ax.set_title('LRD domain spectra (area ∝ $^3$He fraction)', fontsize=13)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(M.OUTDIR, f'winsor_mdd_domains.{ext}'), dpi=200)
    plt.close(fig)

    # --- one Arrhenius plot per N ---
    x = 10000.0 / (spec['T_C'] + 273.0)
    for n in ns:
        r = results[n]
        fig, ax = plt.subplots()
        xr = np.array([x.min() - 0.15, x.max() + 0.15])
        ax.plot(xr, np.log(M.D0_A2) - M.EA * xr / (M.R_CAL * 1e4), color=C_REF, lw=1.4, ls='--', zorder=1)
        ax.plot(x, d['lnD'], color=MUTED, lw=0.6, zorder=1)
        ax.errorbar(x, d['lnD'], yerr=d['sigma'], fmt='o', ms=5, color=INK, mec='white', mew=0.7,
                    elinewidth=0.9, zorder=3)
        ax.plot(x, r['model_lnD'], color='#2a78d6', lw=1.2, marker='D', ms=4, zorder=4)
        ax.set_xlabel(r'$10^4/T$ (K$^{-1}$)')
        ax.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
        ax.set_title(rf"{n} LRD domain{'s' if n > 1 else ''} ({100 * r['f_total']:.1f}% of $^3$He), "
                     rf"$\chi^2_\nu$ = {r['chi2_nu']:.2f}", fontsize=12)
        ax.legend(handles=[Line2D([], [], color=INK, marker='o', ls='none', label='Data'),
                           Line2D([], [], color='#2a78d6', marker='D', ms=4, lw=1.2, label='Model'),
                           Line2D([], [], color=C_REF, lw=1.4, ls='--', label='Stage 1 line (HRD)')],
                  loc='lower left', fontsize=10)
        fig.tight_layout()
        for ext in ('pdf', 'png'):
            fig.savefig(os.path.join(MDD_FIGS, f'arrhenius_N{n}.{ext}'), dpi=200)
        plt.close(fig)


if __name__ == '__main__':
    args = sys.argv[1:]
    n_max = int(args[args.index('--n-max') + 1]) if '--n-max' in args else N_MAX_DEFAULT
    only = [int(a) for a in args[args.index('--only') + 1:] if a.isdigit()] if '--only' in args else None
    n_values = only or list(range(1, n_max + 1))
    if '--plot-only' not in args:
        load_or_fit(n_values, '--recompute' in args)
    results = {n: json.load(open(_path(n))) for n in range(1, n_max + 1)
               if os.path.exists(_path(n)) and 'thermal' in json.load(open(_path(n)))}
    make_plots(results)
