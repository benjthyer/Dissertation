"""
Burial-and-exhumation thermal histories for Win-06-01b goethite, tested
against the HT-Win-06-01b 4He/3He spectrum and the (U-Th)/He age.

Thermal history (three free parameters: T_FORM, T_PEAK, T_MAX):
  * the goethite crystallizes at the surface (T_SURF) at t_form, searched over
    180-210 Ma (ferricrete formed before, or within, the Triassic intramontane
    basins and later buried);
  * it heats linearly during burial to T_max at t_peak;
  * it cools linearly back to T_SURF by T_EXPOSED_MA (Paleogene: Paleogene
    sediments in Flinders valleys show basement exposed by then; Mitchell
    et al. 1998) and stays at T_SURF to the present.

Domains: two spheres with the Stage 1 Ea (as published).
  HRD -- Stage 1 D0/a^2 as published.
  LRD -- fraction f of the 3He, radius r * a_HRD. f and r are fitted to the
         measured 3He release alone (winsor_he43_model.fit_lrd_from_3he;
         see fig_winsor_3he_lrd_fit.py), with f <= 7.5% (delta plot), and then
         held fixed. The LRD gets its own 4He from the same thermal history.
The 4He/3He spectrum is therefore fitted with the three thermal parameters only.

Comparison paths (same LRD and kinetics): isothermal holding (tau_nat free)
and the symmetric 200 -> 100 -> 0 Ma "V" (T_max free).

Fit statistic: chi^2 of the bounding-method central (M) ratios with sigma =
half the LB-UB range (floor 0.02); same step selection as fig_3_4_plot.py.
Joint 1-sigma region (3 parameters): chi^2 <= chi^2_min + 3.53 * max(1, reduced chi^2_min).

The (t_form, t_peak, T_max) grid is slow (~10 min single-core); it runs in
parallel and is cached in generated/data/winsor_burial_grid.csv. Pass
--recompute to rebuild it (needed after any change to the model or data).

Reads:  ../Tables/Win0601bHT_data_and_reduction.xlsx, generated/data/stage1_regression_cache.json
Writes: generated/winsor_burial_chi2_map.{pdf,png}
        generated/winsor_burial_spectrum.{pdf,png}
        generated/winsor_burial_tT_paths.{pdf,png}
        generated/data/winsor_burial_grid.csv, winsor_burial_summary.json
        ../Writing/chapter2_thermal_history_values.tex (LaTeX macros for the text)
"""
import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M

T_FORM_GRID = np.arange(180.0, 210.01, 5.0)
T_PEAK_STEP = 2.5
T_PEAK_MIN = 55.0
T_MAX_GRID = np.arange(20.0, 90.01, 1.0)
T_EXPOSED_MA = 50.0
T_SURF = M.T_SURF
DT_MYR = 2.0
MEASURED_AGE = (130.0, 180.0)
AFT_BOX = dict(t=(85.0, 100.0), T=(50.0, 70.0))   # Gibson & Stuwe 2000; Mitchell et al. 1998
MAP_T_FORMS = (180.0, 195.0, 210.0)
V_NODES_T = (200.0, 100.0, 0.0)
GRID_CSV = os.path.join(M.DATA_OUTDIR, 'winsor_burial_grid.csv')
MACRO_TEX = os.path.join(M.FIG_DIR, '..', 'Writing', 'chapter2_thermal_history_values.tex')

# --- model set-up (module level so worker processes inherit it) -------------
spec = M.load_spectrum()
n_fit = spec['n_fit']
lrd = M.fit_lrd_from_3he(spec)
F_LRD, R_LRD = lrd['f_lrd'], lrd['size_ratio']
tau_h = M.hrd_lab_tau(spec['F_end'], F_LRD, R_LRD)
E_H = np.exp(-np.outer(np.r_[0.0, tau_h], M.LAM))
E_L = np.exp(-np.outer(np.r_[0.0, tau_h / R_LRD ** 2], M.LAM))


def predict(A_hrd, A_lrd):
    N = (1 - F_LRD) * (E_H @ (A_hrd * M.W_INT)) + F_LRD * (E_L @ (A_lrd * M.W_INT))
    return (-np.diff(N) / N[0]) / spec['dF3']


def evaluate(t_nodes, T_nodes):
    A = M.path_modes(t_nodes, T_nodes, dt_myr=DT_MYR)
    A_l = M.path_modes(t_nodes, T_nodes, dt_myr=DT_MYR, size_ratio=R_LRD)
    p = predict(A, A_l)
    return M.chi2(spec, p), M.bulk_age(A, F_LRD, A_l), p


def burial_nodes(t_form, T_max, t_peak):
    return [t_form, t_peak, T_EXPOSED_MA, 0.0], [T_SURF, T_max, T_SURF, T_SURF]


def grid_for_t_form(t_form):
    rows = []
    for tp in np.arange(T_PEAK_MIN, t_form - T_PEAK_STEP + 1e-9, T_PEAK_STEP):
        for Tm in T_MAX_GRID:
            c, age, _ = evaluate(*burial_nodes(t_form, Tm, tp))
            rows.append((t_form, tp, Tm, c, age))
    return rows


def main(recompute=False):
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    import matplotlib.patheffects as pe
    STROKE = [pe.withStroke(linewidth=3.2, foreground='#222222')]
    from thermochr_utils import draw_step_connectors
    from plot_style import apply_style

    INK, MUTED, BOX = '#222222', '#a3a3a3', '#d9d9d9'
    C_BEST, C_V, C_ISO, C_AFT = '#2a78d6', '#eb6834', '#1baf7a', '#eb6834'
    CHI_LEVELS = [0, 2.5, 3, 5, 10, 20, 1e9]
    CHI_COLORS = ['#104281', '#256abf', '#5598e7', '#9ec5f4', '#cde2fb', '#f3f6fa']

    # --- grid (cached) ---
    if recompute or not os.path.exists(GRID_CSV):
        from multiprocessing import Pool
        with Pool() as pool:
            rows = [r for chunk in pool.map(grid_for_t_form, T_FORM_GRID) for r in chunk]
        pd.DataFrame(rows, columns=['t_form_Ma', 't_peak_Ma', 'T_max_C', 'chi2', 'bulk_age_Ma']
                     ).to_csv(GRID_CSV, index=False)
    grid = pd.read_csv(GRID_CSV)
    dof = n_fit - 3
    grid['chi2_nu'] = grid['chi2'] / dof
    ib = int(grid['chi2'].idxmin())
    best = grid.loc[ib]
    thr = best['chi2'] + 3.53 * max(1.0, best['chi2_nu'])
    in1 = grid[grid['chi2'] <= thr]
    age_ok = (grid['bulk_age_Ma'] >= MEASURED_AGE[0]) & (grid['bulk_age_Ma'] <= MEASURED_AGE[1])
    in1_age = grid[(grid['chi2'] <= thr) & age_ok]
    best_age = grid.loc[grid['chi2'].where(age_ok).idxmin()]
    prof_tform = grid.groupby('t_form_Ma')['chi2'].min() / dof

    # --- comparison paths ---
    iso = []
    for lt in np.arange(-5.0, 0.0, 0.01):
        A = M.isothermal_modes(10 ** lt)
        A_l = R_LRD ** 2 * M.isothermal_modes(10 ** lt / R_LRD ** 2)   # same production per real time
        p = predict(A, A_l)
        iso.append((M.chi2(spec, p), lt, p))
    iso_chi, iso_lt, iso_pred = min(iso, key=lambda x: x[0])
    v_res = [(*evaluate(list(V_NODES_T), [T_SURF, Tm, T_SURF]), Tm) for Tm in np.arange(20.0, 90.01, 0.5)]
    v_chi, v_age, v_pred, v_Tm = min(v_res, key=lambda x: x[0])
    _, _, pred_best_age = evaluate(*burial_nodes(best_age['t_form_Ma'], best_age['T_max_C'], best_age['t_peak_Ma']))

    def rng(df, col):
        return [float(df[col].min()), float(df[col].max())]

    summary = dict(
        T_exposed_Ma=T_EXPOSED_MA, T_surface_C=T_SURF, n_fit=n_fit, dof=dof,
        stage1_D0_a2=M.D0_A2, stage1_Ea_cal_mol=M.EA,
        lrd_from_3He={k: v for k, v in lrd.items() if k != 'model_F'},
        burial_best=dict(t_form_Ma=float(best['t_form_Ma']), t_peak_Ma=float(best['t_peak_Ma']),
                         T_max_C=float(best['T_max_C']), chi2_nu=float(best['chi2_nu']),
                         bulk_age_Ma=float(best['bulk_age_Ma'])),
        burial_1sig={c: rng(in1, c) for c in ('t_form_Ma', 't_peak_Ma', 'T_max_C', 'bulk_age_Ma')},
        burial_best_age_consistent=dict(t_form_Ma=float(best_age['t_form_Ma']), t_peak_Ma=float(best_age['t_peak_Ma']),
                                        T_max_C=float(best_age['T_max_C']), chi2_nu=float(best_age['chi2_nu']),
                                        bulk_age_Ma=float(best_age['bulk_age_Ma'])),
        burial_1sig_age_consistent={c: rng(in1_age, c) for c in ('t_form_Ma', 't_peak_Ma', 'T_max_C', 'bulk_age_Ma')},
        chi2_nu_profile_t_form={str(int(k)): float(v) for k, v in prof_tform.items()},
        isothermal_best=dict(log10_tau_nat=float(iso_lt), chi2_nu=float(iso_chi / (n_fit - 1))),
        V_best=dict(T_max_C=float(v_Tm), chi2_nu=float(v_chi / (n_fit - 1)), bulk_age_Ma=float(v_age)),
    )
    json.dump(summary, open(os.path.join(M.DATA_OUTDIR, 'winsor_burial_summary.json'), 'w'), indent=2)
    print(json.dumps(summary, indent=1))

    # --- LaTeX macros for the text ---
    a1 = summary['burial_1sig_age_consistent']
    macros = {
        'ChTwoStageOneLnDzeroAtwo': f"{np.log(M.D0_A2):.2f}",
        'ChTwoLRDfrac': f"{100 * F_LRD:.1f}",
        'ChTwoLRDsize': f"{R_LRD:.4f}",
        'ChTwoLRDmisfit': f"{100 * lrd['rms_rel_misfit']:.0f}",
        'ChTwoSingleDomainMisfit': f"{100 * lrd['rms_rel_misfit_single_domain']:.0f}",
        'ChTwoBurialNfit': f"{n_fit}",
        'ChTwoBurialTmaxLo': f"{a1['T_max_C'][0]:.0f}", 'ChTwoBurialTmaxHi': f"{a1['T_max_C'][1]:.0f}",
        'ChTwoBurialTpeakLo': f"{a1['t_peak_Ma'][0]:.1f}", 'ChTwoBurialTpeakHi': f"{a1['t_peak_Ma'][1]:.1f}",
        'ChTwoBurialTformLo': f"{a1['t_form_Ma'][0]:.0f}", 'ChTwoBurialTformHi': f"{a1['t_form_Ma'][1]:.0f}",
        'ChTwoBurialBestTmax': f"{best_age['T_max_C']:.0f}", 'ChTwoBurialBestTpeak': f"{best_age['t_peak_Ma']:.1f}",
        'ChTwoBurialBestTform': f"{best_age['t_form_Ma']:.0f}", 'ChTwoBurialBestAge': f"{best_age['bulk_age_Ma']:.0f}",
        'ChTwoBurialBestChi': f"{best_age['chi2_nu']:.1f}",
        'ChTwoBurialGlobalChi': f"{best['chi2_nu']:.1f}",
        'ChTwoBurialChiTformLo': f"{prof_tform.min():.2f}", 'ChTwoBurialChiTformHi': f"{prof_tform.max():.2f}",
        'ChTwoVTmax': f"{v_Tm:.0f}", 'ChTwoVChi': f"{v_chi / (n_fit - 1):.1f}", 'ChTwoVAge': f"{v_age:.0f}",
        'ChTwoIsoChi': f"{iso_chi / (n_fit - 1):.0f}",
    }
    with open(MACRO_TEX, 'w', encoding='utf-8') as fh:
        fh.write('% Auto-generated by Chapter2/Figures/fig_winsor_burial_path.py -- do not edit by hand.\n')
        for k, v in macros.items():
            fh.write(f'\\newcommand{{\\{k}}}{{{v}}}\n')

    # --- Figure 1: chi^2 maps at three crystallization ages ---
    width = 13.0
    apply_style(scale=1.1)
    fig, axes = plt.subplots(1, len(MAP_T_FORMS), figsize=(width, 4.6), sharey=True)
    cmap = ListedColormap(CHI_COLORS)
    norm = BoundaryNorm(CHI_LEVELS, cmap.N)
    for ax, tf in zip(axes, MAP_T_FORMS):
        g = grid[np.isclose(grid['t_form_Ma'], tf)]
        tps = np.sort(g['t_peak_Ma'].unique())
        P = g.pivot(index='T_max_C', columns='t_peak_Ma', values='chi2_nu').loc[:, tps]
        AG = g.pivot(index='T_max_C', columns='t_peak_Ma', values='bulk_age_Ma').loc[:, tps]
        C1 = g.pivot(index='T_max_C', columns='t_peak_Ma', values='chi2').loc[:, tps]
        TP, TM = np.meshgrid(tps, P.index.to_numpy())
        pc = ax.pcolormesh(TP, TM, P.to_numpy(), cmap=cmap, norm=norm, shading='nearest', rasterized=True)
        cs = ax.contour(TP, TM, AG.to_numpy(), levels=list(MEASURED_AGE), colors=INK, linewidths=1.2, linestyles='--')
        ax.clabel(cs, fmt=lambda v: f'{v:.0f} Ma', fontsize=9)
        if (C1.to_numpy() <= thr).any():
            c1 = ax.contour(TP, TM, C1.to_numpy(), levels=[thr], colors='white', linewidths=1.6)
            c1.set_path_effects(STROKE)
        ax.add_patch(Rectangle((AFT_BOX['t'][0], AFT_BOX['T'][0]), np.diff(AFT_BOX['t'])[0],
                               np.diff(AFT_BOX['T'])[0], fill=False, ec=C_AFT, lw=1.8, zorder=4))
        j = g['chi2'].idxmin()
        ax.plot(g.loc[j, 't_peak_Ma'], g.loc[j, 'T_max_C'], 'D', color='white', mec=INK, ms=7, zorder=5)
        ax.set_xlim(205, T_PEAK_MIN)
        ax.set_ylim(T_MAX_GRID.min(), T_MAX_GRID.max())
        ax.set_title(rf'Crystallized at {tf:.0f} Ma ($\chi^2_\nu$ = {g["chi2_nu"].min():.2f})', fontsize=12)
    axes[0].set_ylabel(r'Peak temperature, $T_\mathrm{max}$ (°C)')
    axes[len(axes) // 2].set_xlabel('Time of peak temperature (Ma)')
    cb = fig.colorbar(pc, ax=axes, ticks=[1.25, 2.75, 4, 7.5, 15, 30], pad=0.015, fraction=0.025)
    cb.ax.set_yticklabels(['<2.5', '2.5–3', '3–5', '5–10', '10–20', '>20'])
    cb.set_label(r'Reduced $\chi^2$ ($^4$He/$^3$He spectrum)')
    axes[0].legend(handles=[Line2D([], [], color='white', lw=1.6, path_effects=STROKE, label=r'Joint 1$\sigma$ region'),
                            Line2D([], [], color=INK, lw=1.2, ls='--', label='Predicted He age'),
                            Line2D([], [], color=C_AFT, lw=1.8, label='AFT peak window')],
                   loc='upper left', fontsize=9)
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(M.OUTDIR, f'winsor_burial_chi2_map.{ext}'), dpi=200, bbox_inches='tight')
    plt.close(fig)
    apply_style()

    # --- Figure 2: spectrum ---
    u = spec['use']
    Fs, Fe = spec['F_start'], spec['F_end']
    fig, ax = plt.subplots()
    for i in np.where(u)[0]:
        ax.fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0, zorder=1)
    ax.hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=3)
    for pred, col, lw, ls in [(iso_pred, C_ISO, 1.3, '--'), (v_pred, C_V, 1.3, '--'), (pred_best_age, C_BEST, 2.0, '-')]:
        ax.hlines(pred, Fs, Fe, color=col, lw=lw, linestyles=ls, zorder=4)
        if ls == '-':
            draw_step_connectors(ax, Fs, Fe, pred, color=col, zorder=4)
    ax.set_xlim(0, 0.16)
    ax.set_ylim(0, 1.2)
    ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
    ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
    ax.set_title('HT-Win-06-01b: thermal-history fits', fontsize=14)
    ax.legend(handles=[Line2D([], [], color=INK, lw=2.2, label='Data (M), LB–UB box'),
                       Line2D([], [], color=C_BEST, lw=2.0,
                              label=rf"Burial: {best_age['t_form_Ma']:.0f}→{best_age['t_peak_Ma']:.0f} Ma, "
                                    rf"{best_age['T_max_C']:.0f} °C; $\chi^2_\nu$ = {best_age['chi2_nu']:.1f}"),
                       Line2D([], [], color=C_V, lw=1.3, ls='--',
                              label=rf"V (200–100–0 Ma): {v_Tm:.0f} °C; $\chi^2_\nu$ = {v_chi / (n_fit - 1):.1f}"),
                       Line2D([], [], color=C_ISO, lw=1.3, ls='--',
                              label=rf"Isothermal; $\chi^2_\nu$ = {iso_chi / (n_fit - 1):.0f}")],
              loc='lower right', fontsize=9)
    ax.text(0.003, 1.15, rf'LRD from $^3$He: {F_LRD:.1%} of $^3$He, $a_\mathrm{{LRD}}/a_\mathrm{{HRD}}$ = {R_LRD:.4f}',
            fontsize=9.5, va='top', color='#444444')
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(M.OUTDIR, f'winsor_burial_spectrum.{ext}'), dpi=200)
    plt.close(fig)

    # --- Figure 3: accepted t-T paths ---
    fig, ax = plt.subplots()
    tt = np.linspace(0, 210, 300)
    for df, col, lw, a in [(in1, MUTED, 0.6, 0.35), (in1_age, C_BEST, 0.7, 0.45)]:
        for _, r in df.iterrows():
            ax.plot(tt, M.path_T(*burial_nodes(r['t_form_Ma'], r['T_max_C'], r['t_peak_Ma']), tt),
                    color=col, lw=lw, alpha=a)
    ax.plot(tt, M.path_T(*burial_nodes(best_age['t_form_Ma'], best_age['T_max_C'], best_age['t_peak_Ma']), tt),
            color=INK, lw=2.0)
    ax.add_patch(Rectangle((AFT_BOX['t'][0], AFT_BOX['T'][0]), np.diff(AFT_BOX['t'])[0],
                           np.diff(AFT_BOX['T'])[0], fill=False, ec=C_AFT, lw=1.8))
    ax.set_xlim(210, 0)
    ax.set_ylim(10, 90)
    ax.set_xlabel('Time (Ma)')
    ax.set_ylabel('Temperature (°C)')
    ax.set_title(r'Burial paths within 1$\sigma$ of the spectrum', fontsize=14)
    ax.legend(handles=[Line2D([], [], color=INK, lw=2.0, label='Best fit with He age 130–180 Ma'),
                       Line2D([], [], color=C_BEST, lw=1.0, label=r'1$\sigma$, He age 130–180 Ma'),
                       Line2D([], [], color=MUTED, lw=1.0, label=r'1$\sigma$, He age > 180 Ma'),
                       Line2D([], [], color=C_AFT, lw=1.8, label='AFT peak window')],
              loc='upper left', fontsize=9.5)
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(M.OUTDIR, f'winsor_burial_tT_paths.{ext}'), dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    main(recompute='--recompute' in sys.argv)
