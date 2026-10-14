"""
Farley & Flowers (2012)-style multi-domain fits for HT-Win-06-01b, followed by
thermal-history fits to the 4He/3He spectrum, for N = 2..10 LRD domains.

Step 1 -- domain structure from 3He alone (winsor_he43_mdd.fit_lrd_ff):
  * the HRD holds 92.5% of the 3He; with --hrd-mode stage1 (default) it sits
    exactly on the Stage 1 line; with --hrd-mode free its D0/a^2 may scale
    (same Ea);
  * N LRD domains share the Stage 1 Ea and hold exactly 7.5% of the 3He in
    total; their individual fractions and sizes (r_j = a_j / a_HRD <= 1) are free;
  * the target is the per-step (fractional) and cumulative 3He yields, equally
    weighted (Farley & Flowers 2012, supplement A2); --weighting relative
    divides each residual by the observed value instead.
  The Arrhenius and delta plots are consequences of this fit, not targets.
  Each N is warm-started from the N-1 solution plus one new domain.

Step 2 -- thermal history from the 4He/3He spectrum (domains fixed): the
burial path of fig_winsor_burial_path.py (crystallization at t_form at 20 C ->
peak T_max at t_peak -> 20 C by 50 Ma -> present), with t_form in T_FORMS and
(t_peak, T_max) optimized by Nelder-Mead. Every domain carries its own 4He.

Usage:  python fig_winsor_mdd_ff.py [--hrd-mode stage1|free] [--weighting absolute|relative]
                                    [--n-min 2] [--n-max 10] [--only 3 4 ...]
                                    [--recompute] [--plot-only]
Results are cached per N in generated/data/mdd_ff/<hrd-mode>_<weighting>/N<n>.json.

Writes (in generated/mdd_ff/<hrd-mode>_<weighting>/):
  mdd_ff_N<n>.{pdf,png}      eight-panel diagnostic figure for each N
  mdd_ff_summary.{pdf,png}   statistics and thermal results against N
  and generated/data/mdd_ff/<hrd-mode>_<weighting>/summary.csv
"""
import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M
import winsor_he43_mdd as D

T_FORMS = (180.0, 190.0, 200.0, 210.0)
T_EXPOSED_MA = 50.0
MEASURED_AGE = (130.0, 180.0)
AFT_BOX = dict(t=(85.0, 100.0), T=(50.0, 70.0))
STARTS = ((80.0, 61.0), (100.0, 66.0), (65.0, 60.0), (130.0, 70.0))
PLATEAU = (0.04, 0.07)


def _opt(args, name, default):
    return args[args.index(name) + 1] if name in args else default


ARGS = sys.argv[1:]
HRD_MODE = _opt(ARGS, '--hrd-mode', 'stage1')
WEIGHTING = _opt(ARGS, '--weighting', 'absolute')
TAG = f'{HRD_MODE}_{WEIGHTING}'
DATA_DIR = os.path.join(M.DATA_OUTDIR, 'mdd_ff', TAG)
FIG_DIR = os.path.join(M.OUTDIR, 'mdd_ff', TAG)


def _path(n):
    return os.path.join(DATA_DIR, f'N{n}.json')


def _load(n):
    return json.load(open(_path(n)))


def _save(n, out):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(_path(n), 'w') as fh:
        json.dump({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in out.items()}, fh, indent=1)


def burial_nodes(t_form, T_max, t_peak):
    return [t_form, t_peak, T_EXPOSED_MA, 0.0], [M.T_SURF, T_max, M.T_SURF, M.T_SURF]


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------
def fit_he3(n):
    spec = M.load_spectrum()
    init = None
    if os.path.exists(_path(n - 1)):
        prev = _load(n - 1)
        init = (prev['f'], prev['r'], prev['hrd_scale'])
    _save(n, D.fit_lrd_ff(spec, n, hrd_mode=HRD_MODE, weighting=WEIGHTING, init=init))


def fit_thermal(n):
    from scipy.optimize import minimize
    spec = M.load_spectrum()
    res = _load(n)
    sm = D.SpectrumModel(spec, np.asarray(res['f']), np.asarray(res['r']), res['hrd_scale'])
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


def run_fits(n_values, recompute):
    for n in sorted(n_values):                       # 3He: sequential (warm starts)
        if recompute or not os.path.exists(_path(n)):
            fit_he3(n)
    todo = [n for n in n_values if 'thermal' not in _load(n)]
    if todo:                                         # 4He/3He: parallel
        from multiprocessing import Pool
        with Pool(min(len(todo), os.cpu_count() or 1)) as pool:
            pool.map(fit_thermal, todo)


def best_thermal(res, age_consistent=True):
    th = res['thermal']
    if age_consistent:
        th = [t for t in th if MEASURED_AGE[0] <= t['bulk_age_Ma'] <= MEASURED_AGE[1]] or th
    return min(th, key=lambda t: t['chi2'])


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def make_plots(results):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from thermochr_utils import draw_step_connectors
    from plot_style import apply_style
    os.makedirs(FIG_DIR, exist_ok=True)
    INK, MUTED, BOX, C_MOD, C_REF, C_AFT = '#222222', '#8a8a8a', '#d9d9d9', '#2a78d6', '#eb6834', '#eb6834'
    TF_RAMP = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab']
    spec = M.load_spectrum()
    d = D.he3_data(spec)
    steps = np.arange(1, spec['F_end'].size + 1)
    dF_obs = spec['dF3']
    low = ~np.isfinite(spec['R_LB']) | ~spec['use']
    x_arr = 10000.0 / (spec['T_C'] + 273.0)
    Fs, Fe, u = spec['F_start'], spec['F_end'], spec['use']

    rows = []
    for n, r in sorted(results.items()):
        bt, bu = best_thermal(r, True), best_thermal(r, False)
        rows.append(dict(n_lrd=n, hrd_scale=r['hrd_scale'], rms_yield=r['rms_yield'], bic=r['bic'], aic=r['aic'],
                         k=r['k'], arrhenius_chi2_nu=r['arrhenius_chi2_nu'],
                         spec_chi2_nu_age_ok=bt['chi2_nu'], t_form=bt['t_form_Ma'], t_peak=bt['t_peak_Ma'],
                         T_max=bt['T_max_C'], age=bt['bulk_age_Ma'],
                         spec_chi2_nu_any=bu['chi2_nu'], any_t_form=bu['t_form_Ma'], any_age=bu['bulk_age_Ma'],
                         f_j=' '.join(f'{x:.4f}' for x in r['f']), r_j=' '.join(f'{x:.4g}' for x in r['r'])))
    summ = pd.DataFrame(rows)
    os.makedirs(DATA_DIR, exist_ok=True)
    summ.to_csv(os.path.join(DATA_DIR, 'summary.csv'), index=False)
    print(summ[['n_lrd', 'hrd_scale', 'rms_yield', 'bic', 'arrhenius_chi2_nu', 'spec_chi2_nu_age_ok',
                't_form', 't_peak', 'T_max', 'age']].round(4).to_string(index=False))

    # ---- one diagnostic figure per N ----
    apply_style(scale=1.25)
    for n, r in sorted(results.items()):
        f, rr, s = np.asarray(r['f']), np.asarray(r['r']), r['hrd_scale']
        Fm = np.asarray(r['model_F'])
        dFm = np.diff(np.r_[0.0, Fm])
        fig, ax = plt.subplots(2, 4, figsize=(21, 9.5))
        a = ax.ravel()
        # (a) fractional yields
        a[0].plot(steps, dF_obs, 'o', color=INK, ms=6, mec='white', zorder=3)
        a[0].plot(steps[low], dF_obs[low], 'o', mfc='white', mec=INK, ms=6, zorder=4)
        a[0].plot(steps, dFm, color=C_MOD, lw=1.5, marker='D', ms=4, zorder=5)
        a[0].set_yscale('log')
        a[0].set_xlabel('Step')
        a[0].set_ylabel(r'Fraction of $^3$He in step')
        a[0].set_title('(a) Fractional yields (fitted)')
        # (b) cumulative yields
        a[1].plot(steps, spec['F_end'], 'o', color=INK, ms=6, mec='white', zorder=3)
        a[1].plot(steps, Fm, color=C_MOD, lw=1.5, marker='D', ms=4, zorder=4)
        a[1].set_xlabel('Step')
        a[1].set_ylabel(r'Cumulative $^3$He fraction')
        a[1].set_title('(b) Cumulative yields (fitted)')
        # (c) Arrhenius
        xr = np.array([x_arr.min() - 0.15, x_arr.max() + 0.15])
        a[2].plot(xr, np.log(M.D0_A2) - M.EA * xr / (M.R_CAL * 1e4), color=C_REF, lw=1.3, ls='--')
        if abs(s - 1) > 1e-6:
            a[2].plot(xr, np.log(s * M.D0_A2) - M.EA * xr / (M.R_CAL * 1e4), color=C_REF, lw=1.3, ls=':')
        a[2].plot(x_arr, d['lnD'], color=MUTED, lw=0.6)
        a[2].errorbar(x_arr, d['lnD'], yerr=d['sigma'], fmt='o', ms=5, color=INK, mec='white', elinewidth=0.8)
        a[2].plot(x_arr, r['model_lnD'], color=C_MOD, lw=1.2, marker='D', ms=4)
        a[2].set_xlabel(r'$10^4/T$ (K$^{-1}$)')
        a[2].set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
        a[2].set_title(rf"(c) Arrhenius (consequence), $\chi^2_\nu$ = {r['arrhenius_chi2_nu']:.2f}")
        # (d) delta plot
        a[3].axvspan(*PLATEAU, color='#f1f1f1', lw=0)
        a[3].axhline(0, color=C_REF, lw=1.3, ls='--')
        a[3].errorbar(spec['F_end'], d['lnD'] - d['lnD_stage1'], yerr=d['sigma'], fmt='o', ms=5, color=INK,
                      mec='white', elinewidth=0.8)
        a[3].plot(Fm, np.asarray(r['model_lnD']) - d['lnD_stage1'], color=C_MOD, lw=1.5, marker='D', ms=4)
        a[3].set_xlim(0, 0.16)
        a[3].set_xlabel(r'$\Sigma F_{^3\mathrm{He}}$')
        a[3].set_ylabel(r'$\Delta\ln(D/a^2)$ from Stage 1')
        a[3].set_title('(d) Delta plot (consequence)')
        # (e) domain spectrum
        a[4].vlines(np.log10(rr), 0, 100 * f, color=C_MOD, lw=6)
        a[4].axvline(0, color=C_REF, lw=1.3, ls='--')
        a[4].text(-0.1, 0.97, f'HRD {100 * (1 - f.sum()):.1f}%', transform=a[4].get_xaxis_transform(),
                  ha='right', va='top', color=C_REF, fontsize=11)
        a[4].set_xlim(-6.2, 0.4)
        a[4].set_ylim(0, max(100 * f.max() * 1.25, 1))
        a[4].set_xlabel(r'$\log_{10}(a_j/a_\mathrm{HRD})$')
        a[4].set_ylabel(r'% of $^3$He')
        a[4].set_title(f'(e) LRD domains: {n} (total {100 * f.sum():.1f}%)')
        # (f) 4He/3He spectrum
        bt, bu = best_thermal(r, True), best_thermal(r, False)
        a[5].axvspan(*PLATEAU, color='#f1f1f1', lw=0)
        for i in np.where(u)[0]:
            a[5].fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0)
        a[5].hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=3)
        p = np.asarray(bt['pred'])
        a[5].hlines(p, Fs, Fe, color=C_MOD, lw=1.8, zorder=4)
        draw_step_connectors(a[5], Fs, Fe, p, color=C_MOD, zorder=4)
        if bu is not bt:
            a[5].hlines(np.asarray(bu['pred']), Fs, Fe, color=MUTED, lw=1.2, linestyles='--', zorder=3)
        a[5].set_xlim(0, 0.16)
        a[5].set_ylim(0, 1.2)
        a[5].set_xlabel(r'$\Sigma F_{^3\mathrm{He}}$')
        a[5].set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
        a[5].set_title(rf"(f) $^4$He/$^3$He, $\chi^2_\nu$ = {bt['chi2_nu']:.2f}")
        # (g) thermal paths
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
        # (h) summary text
        a[7].axis('off')
        lines = [f"N = {n} LRD domains ({HRD_MODE}, {WEIGHTING} weighting)",
                 f"HRD: {100 * (1 - f.sum()):.1f}% of 3He, D0/a2 = {s:.3f} x Stage 1",
                 "LRD domains (fraction %, a/a_HRD):"]
        lines += [f"   {100 * fj:6.3f}%   {rj:.3g}" for fj, rj in zip(f, rr)]
        lines += ["", f"RMS yield misfit: {r['rms_yield']:.2e}", f"BIC: {r['bic']:.1f}   (k = {r['k']})",
                  "", "Best burial path with He age 130-180 Ma:",
                  f"   {bt['t_form_Ma']:.0f} Ma -> {bt['T_max_C']:.1f} C at {bt['t_peak_Ma']:.1f} Ma",
                  f"   He age {bt['bulk_age_Ma']:.0f} Ma; spectrum chi2_nu {bt['chi2_nu']:.2f}"]
        a[7].text(0.0, 1.0, '\n'.join(lines), va='top', ha='left', family='monospace', fontsize=11,
                  transform=a[7].transAxes)
        fig.tight_layout()
        for ext in ('pdf', 'png'):
            fig.savefig(os.path.join(FIG_DIR, f'mdd_ff_N{n}.{ext}'), dpi=150)
        plt.close(fig)

    # ---- summary across N ----
    apply_style(scale=1.1)
    fig, ax = plt.subplots(2, 3, figsize=(15, 8.5))
    specs = [('rms_yield', 'RMS yield misfit (fitted)'), ('bic', 'BIC (yield fit)'),
             ('arrhenius_chi2_nu', r'Arrhenius $\chi^2_\nu$ (consequence)'),
             ('spec_chi2_nu_age_ok', r'$^4$He/$^3$He $\chi^2_\nu$ (best age-consistent path)'),
             ('T_max', r'Best $T_\mathrm{max}$ (°C)'), ('t_peak', r'Best $t_\mathrm{peak}$ (Ma)')]
    for a, (col, lab) in zip(ax.ravel(), specs):
        a.plot(summ['n_lrd'], summ[col], color=C_MOD, lw=2, marker='o', ms=7, mec='white')
        a.set_title(lab, fontsize=13)
        a.set_xlabel('Number of LRD domains')
        a.set_xticks(summ['n_lrd'])
    fig.suptitle(f'Multi-domain LRD (7.5% of $^3$He), HRD {HRD_MODE}, {WEIGHTING} yield weighting', fontsize=14)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIG_DIR, f'mdd_ff_summary.{ext}'), dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    n_min = int(_opt(ARGS, '--n-min', 2))
    n_max = int(_opt(ARGS, '--n-max', 10))
    only = [int(a) for a in ARGS[ARGS.index('--only') + 1:] if a.isdigit()] if '--only' in ARGS else None
    if '--plot-only' not in ARGS:
        run_fits(only or list(range(n_min, n_max + 1)), '--recompute' in ARGS)
    results = {n: _load(n) for n in range(n_min, n_max + 1)
               if os.path.exists(_path(n)) and 'thermal' in _load(n)}
    make_plots(results)
