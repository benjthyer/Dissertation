"""
Figures and LaTeX values for the Win-06-01b MDD / thermal-history report and
Chapter 2. Reads caches only (no fitting):
  generated/data/mdd_free/absolute/N<n>.json              3He domain fits (fig_winsor_mdd_free.py --stage he3)
  generated/data/mdd_free/absolute/maps_N4.csv             burial chi^2 grid (fig_winsor_mdd_free.py --stage maps --only 4)
  generated/data/mdd_free/absolute/maps_alt_{isothermal,linear}_N4.csv  (fig_winsor_mdd_alt_paths.py)

The 3He inversion and the thermal-history inversion are kept separate:
Table 1 (\\MDDDomainTableRows) describes the domain fits for N = 1..10;
Table 2 (\\MDDThermalTableRows) the thermal histories fitted with the adopted
N = 4 structure. Low-signal steps (< 0.1 pccSTP 3He) are neither fitted nor
plotted in the Arrhenius and delta plots.

Figures (generated/mdd_free/absolute/chapter/):
  ch2_mdd_domains           domain spectra, N = 1..10
  ch2_mdd_arrh_delta_N4     Arrhenius and delta plots with the N = 4 model
  ch2_mdd_3he_fits_N1-5     supplementary 5 x 4 grid
  ch2_mdd_heatmaps_N4       chi^2 maps, burial (t_form = 195 Ma) and linear cooling, shared colour scale
  ch2_mdd_spectrum_compare_N4  4He/3He spectrum with the best age-consistent burial and cooling paths
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
import winsor_he43_mdd_free as F
from thermochr_utils import draw_step_connectors
from plot_style import apply_style

N_SEL, N_MAX = 4, 10
DATA_DIR = os.path.join(M.DATA_OUTDIR, 'mdd_free', 'absolute')
OUT = os.path.join(M.OUTDIR, 'mdd_free', 'absolute', 'chapter')
TEX = os.path.join(M.FIG_DIR, '..', 'Writing', 'mdd_free_report_values.tex')
os.makedirs(OUT, exist_ok=True)

MEASURED_AGE = (130.0, 180.0)
AFT_BOX = dict(t=(85.0, 100.0), T=(50.0, 70.0))
MAP_T_FORM = 195.0
BURIAL_T_FORMS = (180.0, 195.0, 210.0)
T_END_LINEAR = 25.0
DT_MYR = 1.0
SUPP_N = (1, 2, 3, 4, 5)

INK, MUTED = '#222222', '#8a8a8a'
C_MOD, C_REF, C_AFT = '#2a78d6', '#eb6834', '#eb6834'
C_BUR, C_COOL, BOX = '#2a78d6', '#1baa6b', '#d9d9d9'
CHI_COLORS = ['#104281', '#256abf', '#5598e7', '#9ec5f4', '#cde2fb', '#f3f6fa']
STROKE = [pe.withStroke(linewidth=3.2, foreground=INK)]

spec = M.load_spectrum()
d = F.he3_data(spec)
KEEP = d['keep']
N_FIT = spec['n_fit']
DOF = N_FIT - 2                       # every thermal family has two free parameters
x_arr = 10000.0 / (spec['T_C'] + 273.0)
lnD_ref = d['lnD_stage1']


def load(n):
    return json.load(open(os.path.join(DATA_DIR, f'N{n}.json')))


def save(fig, name, **kw):
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(OUT, f'{name}.{ext}'), dpi=200, **kw)
    plt.close(fig)


def age_ok(a):
    return (a >= MEASURED_AGE[0]) & (a <= MEASURED_AGE[1])


def burial_nodes(t_form, T_max, t_peak):
    return [t_form, t_peak, 50.0, 0.0], [M.T_SURF, T_max, M.T_SURF, M.T_SURF]


def cooling_nodes(t_form, T0):
    return [t_form, 0.0], [T0, T_END_LINEAR]


results = {n: load(n) for n in range(1, N_MAX + 1)}
res4 = results[N_SEL]


# ---------------------------------------------------------------------------
# Table 1: 3He domain inversion
# ---------------------------------------------------------------------------
dom_rows = []
for n, r in results.items():
    f, rr = np.asarray(r['f']), np.asarray(r['r'])
    main = int(np.argmax(f))
    dom_rows.append(f"{n} & {2 * n - 1} & {1e4 * r['rms_yield']:.2f} & "
                    f"{r['arrhenius_chi2_nu']:.2f} & {100 * f[rr < 0.1].sum():.1f} & {100 * f[main]:.1f} & "
                    f"{rr[main]:.2f} \\\\")

# ---------------------------------------------------------------------------
# Table 2: thermal histories with the N = 4 domains
# ---------------------------------------------------------------------------
gb = pd.read_csv(os.path.join(DATA_DIR, f'maps_N{N_SEL}.csv'))
gi = pd.read_csv(os.path.join(DATA_DIR, f'maps_alt_isothermal_N{N_SEL}.csv'))
gl = pd.read_csv(os.path.join(DATA_DIR, f'maps_alt_linear_N{N_SEL}.csv'))


def summarize(g, tcol, Tcol):
    """Best age-consistent cell (or best overall, flagged); 1-sigma ranges of the age-consistent cells within
    Delta chi^2 = 2.30 max(1, chi^2_nu) of that best fit. thr is the unconstrained 1-sigma level (map contour)."""
    cmin = g['chi2'].min()
    thr = cmin + 2.30 * max(1.0, cmin / DOF)
    ok = g[age_ok(g['bulk_age_Ma'])]
    flag = ok.empty
    b = (g if flag else ok).loc[(g if flag else ok)['chi2'].idxmin()]
    # ranges: age-consistent cells within 1 sigma of the best age-consistent fit
    thr_ok = b['chi2'] + 2.30 * max(1.0, b['chi2'] / DOF)
    sig = ok[ok['chi2'] <= thr_ok]
    rng = lambda c, fmt: '--' if sig.empty else (f"{sig[c].min():{fmt}}--{sig[c].max():{fmt}}")
    return dict(best=b, flag=flag, thr=thr, cmin=cmin,
                t_rng=rng(tcol, '.0f') if tcol else '--', T_rng=rng(Tcol, '.0f'),
                n_sig=len(sig))


th_rows, th_vals = [], {}
s = summarize(gi, 't_form_Ma', 'T_C'); b = s['best']
th_vals['iso'] = s
th_rows.append(f"Isothermal hold & {b['t_form_Ma']:.0f} & -- & {b['T_C']:.0f} & {b['chi2'] / DOF:.1f} & "
               f"{b['bulk_age_Ma']:.0f} & {s['t_rng']} & -- & {s['T_rng']} \\\\")
for tf in BURIAL_T_FORMS:
    g = gb[np.isclose(gb['t_form_Ma'], tf)].reset_index(drop=True)
    s = summarize(g, 't_peak_Ma', 'T_max_C'); b = s['best']
    th_vals[f'bur{tf:.0f}'] = s
    dag = '$^{\\dagger}$' if s['flag'] else ''
    th_rows.append(f"Burial & {tf:.0f} & {b['t_peak_Ma']:.0f} & {b['T_max_C']:.0f} & {b['chi2'] / DOF:.2f} & "
                   f"{b['bulk_age_Ma']:.0f}{dag} & fixed & {s['t_rng'].replace('--', '--', 1)} & {s['T_rng']} \\\\")
s = summarize(gl, 't_form_Ma', 'T_C'); b = s['best']
th_vals['lin'] = s
th_rows.append(f"Linear cooling & {b['t_form_Ma']:.0f} & {b['t_form_Ma']:.0f} & {b['T_C']:.0f} & "
               f"{b['chi2'] / DOF:.2f} & {b['bulk_age_Ma']:.0f} & {s['t_rng']} & {s['t_rng']} & {s['T_rng']} \\\\")

lin_global = gl.loc[gl['chi2'].idxmin()]
iso_ridge = gi.loc[gi.groupby('t_form_Ma')['chi2'].idxmin()]
macros = dict(
    MDDFreeNmax=f'{N_MAX}',
    MDDNfit=f'{N_FIT}', MDDNkeep=f'{int(KEEP.sum())}', MDDNsteps=f'{KEEP.size}',
    MDDLinGlobalChi=f"{lin_global['chi2'] / DOF:.2f}", MDDLinGlobalT=f"{lin_global['T_C']:.0f}",
    MDDLinGlobalTform=f"{lin_global['t_form_Ma']:.0f}", MDDLinGlobalAge=f"{lin_global['bulk_age_Ma']:.0f}",
    MDDIsoChi=f"{gi['chi2'].min() / DOF:.1f}",
)
with open(TEX, 'w', encoding='utf-8') as fh:
    fh.write('% Auto-generated by Figures/fig_winsor_mdd_report.py -- do not edit by hand\n')
    fh.write('\\newcommand{\\MDDDomainTableRows}{%\n' + '\n'.join(dom_rows) + '\n}\n')
    fh.write('\\newcommand{\\MDDThermalTableRows}{%\n' + '\n'.join(th_rows[-1:] + th_rows[1:-1] + th_rows[:1]) + '\n}\n')
    for k, v in macros.items():
        fh.write(f'\\newcommand{{\\{k}}}{{{v}}}\n')

# ---------------------------------------------------------------------------
# Domain spectra
# ---------------------------------------------------------------------------
apply_style()
fig, ax = plt.subplots()
for n, r in results.items():
    ax.scatter(np.log10(r['r']), np.full(len(r['r']), n), s=15 + 380 * np.sqrt(np.asarray(r['f'])),
               color=C_MOD, alpha=0.7, edgecolor='white', lw=0.8, zorder=3)
ax.axvline(0, color=C_REF, lw=1.4, ls='--')
ax.text(0.08, N_MAX + 0.55, 'Stage 1 reference', color=C_REF, fontsize=9)
ax.set_xlim(-6.2, 3.2); ax.set_ylim(0.3, N_MAX + 1.0)
ax.set_yticks(range(1, N_MAX + 1))
ax.set_xlabel(r'$\log_{10}(r/r_0)$'); ax.set_ylabel('Number of domains, N')
ax.set_title(r'Domain spectra (area $\propto\sqrt{f}$)', fontsize=13)
fig.tight_layout()
save(fig, 'ch2_mdd_domains')

# ---------------------------------------------------------------------------
# Arrhenius + delta, N = 4
# ---------------------------------------------------------------------------
xr = np.array([x_arr.min() - 0.15, x_arr.max() + 0.15])
k = KEEP
apply_style(scale=1.5)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.6), layout='constrained')
a1.plot(xr, np.log(M.D0_A2) - M.EA * xr / (M.R_CAL * 1e4), color=C_REF, lw=1.4, ls='--', zorder=1)
a1.errorbar(x_arr[k], d['lnD'][k], yerr=d['sigma'][k], fmt='o', ms=8, color=INK, mec='white', mew=0.9,
            elinewidth=1.5, zorder=3)
a1.plot(x_arr[k], np.asarray(res4['model_lnD'])[k], color=C_MOD, lw=0.8, alpha=0.45, zorder=2)
a1.plot(x_arr[k], np.asarray(res4['model_lnD'])[k], 'D', color=C_MOD, ms=7, zorder=4)
a1.set_xlabel(r'$10^4/T$ (K$^{-1}$)')
a1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
a1.set_title('(a) Arrhenius plot', fontsize=19, loc='left')
a2.axhline(0, color=C_REF, lw=1.4, ls='--', zorder=1)
a2.errorbar(spec['F_end'][k], (d['lnD'] - lnD_ref)[k], yerr=d['sigma'][k], fmt='o', ms=8, color=INK,
            mec='white', mew=0.9, elinewidth=1.5, zorder=3)
a2.plot(np.asarray(res4['model_F'])[k], (np.asarray(res4['model_lnD']) - lnD_ref)[k], color=C_MOD, lw=1.4,
        marker='D', ms=6.5, zorder=4)
a2.set_xlim(0, 0.16)
a2.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
a2.set_ylabel(r'$\Delta\ln(D/a^2)$ from Stage 1 line')
a2.set_title('(b) Delta plot', fontsize=19, loc='left')
a2.legend(handles=[Line2D([], [], color=INK, marker='o', ls='none', label='Data'),
                   Line2D([], [], color=C_MOD, marker='D', ms=6.5, lw=1.4,
                          label=rf"{N_SEL}-domain model ($\chi^2_\nu$ = {res4['arrhenius_chi2_nu']:.2f})"),
                   Line2D([], [], color=C_REF, lw=1.4, ls='--', label='Stage 1 reference')],
          loc='upper right', fontsize=14)
save(fig, f'ch2_mdd_arrh_delta_N{N_SEL}')

# ---------------------------------------------------------------------------
# Supplementary 5 x 4
# ---------------------------------------------------------------------------
apply_style(scale=0.8)
steps = np.arange(1, spec['F_end'].size + 1)
fig, axes = plt.subplots(len(SUPP_N), 4, figsize=(12.5, 15.5), sharex='col')
for row, n in enumerate(SUPP_N):
    r = results[n]
    Fm = np.asarray(r['model_F'])
    a = axes[row]
    a[0].plot(steps[k], spec['dF3'][k], 'o', color=INK, ms=4, mec='white', mew=0.5, zorder=3)
    a[0].plot(steps[~k], spec['dF3'][~k], 'o', mfc='white', mec=MUTED, ms=4, zorder=2)
    a[0].plot(steps, np.diff(np.r_[0.0, Fm]), color=C_MOD, lw=1.2, marker='D', ms=2.5, zorder=5)
    a[0].set_yscale('log')
    a[0].set_ylabel(f'N = {n}\n\n' + r'Fraction of $^3$He in step', fontsize=10)
    a[1].plot(steps[k], spec['F_end'][k], 'o', color=INK, ms=4, mec='white', mew=0.5, zorder=3)
    a[1].plot(steps[~k], spec['F_end'][~k], 'o', mfc='white', mec=MUTED, ms=4, zorder=2)
    a[1].plot(steps, Fm, color=C_MOD, lw=1.2, marker='D', ms=2.5, zorder=4)
    a[1].set_ylabel(r'Cumulative $^3$He fraction', fontsize=10)
    a[1].text(0.04, 0.93, f"RMS {r['rms_yield']:.1e}", transform=a[1].transAxes,
              va='top', fontsize=8.5, color='#444444')
    a[2].plot(xr, np.log(M.D0_A2) - M.EA * xr / (M.R_CAL * 1e4), color=C_REF, lw=1.1, ls='--')
    a[2].errorbar(x_arr[k], d['lnD'][k], yerr=d['sigma'][k], fmt='o', ms=3.5, color=INK, mec='white',
                  mew=0.5, elinewidth=0.7)
    a[2].plot(x_arr[k], np.asarray(r['model_lnD'])[k], color=C_MOD, lw=1.0, marker='D', ms=2.5)
    a[2].set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)', fontsize=10)
    a[2].text(0.96, 0.93, rf"$\chi^2_\nu$ = {r['arrhenius_chi2_nu']:.2f}", transform=a[2].transAxes,
              ha='right', va='top', fontsize=9, color='#444444')
    a[3].axhline(0, color=C_REF, lw=1.1, ls='--')
    a[3].errorbar(spec['F_end'][k], (d['lnD'] - lnD_ref)[k], yerr=d['sigma'][k], fmt='o', ms=3.5, color=INK,
                  mec='white', mew=0.5, elinewidth=0.7)
    a[3].plot(Fm[k], (np.asarray(r['model_lnD']) - lnD_ref)[k], color=C_MOD, lw=1.2, marker='D', ms=2.5)
    a[3].set_xlim(0, 0.16)
    a[3].set_ylabel(r'$\Delta\ln(D/a^2)$', fontsize=10)
for a, t in zip(axes[0], ['Fractional yields (fitted)', 'Cumulative yields (fitted)',
                          'Arrhenius (consequence)', 'Delta plot (consequence)']):
    a.set_title(t, fontsize=11)
axes[-1, 0].set_xlabel('Step'); axes[-1, 1].set_xlabel('Step')
axes[-1, 2].set_xlabel(r'$10^4/T$ (K$^{-1}$)'); axes[-1, 3].set_xlabel(r'$\Sigma F_{^3\mathrm{He}}$')
fig.tight_layout(h_pad=1.0, w_pad=1.0)
save(fig, 'ch2_mdd_3he_fits_N1-5')

# ---------------------------------------------------------------------------
# chi^2 maps: burial (t_form = 195 Ma) and linear cooling, shared colour scale
# ---------------------------------------------------------------------------
gb195 = gb[np.isclose(gb['t_form_Ma'], MAP_T_FORM)].reset_index(drop=True)
panels = [
    dict(g=gb195, x='t_peak_Ma', y='T_max_C', s=th_vals[f'bur{MAP_T_FORM:.0f}'],
         title=f'Burial, crystallized at {MAP_T_FORM:.0f} Ma', xlabel=r'Time of peak temperature, $t_\mathrm{peak}$ (Ma)',
         ylabel=r'Peak temperature, $T_\mathrm{max}$ (°C)', xlim=(MAP_T_FORM, 50), ylim=(30, 90), aft=True),
    dict(g=gl, x='t_form_Ma', y='T_C', s=th_vals['lin'],
         title='Linear cooling to 25 °C', xlabel=r'Crystallization age, $t_\mathrm{form}$ (Ma)',
         ylabel=r'Temperature at crystallization, $T_0$ (°C)', xlim=(320, 50), ylim=(40, 120), aft=False),
]
nu_min = min(p['g']['chi2'].min() for p in panels) / DOF
edges = np.r_[0.0, np.round(nu_min + np.array([0.3, 0.8, 1.8, 3.8, 6.8]), 1), 1e9]
labels = [f'<{edges[1]:g}'] + [f'{a:g}–{b:g}' for a, b in zip(edges[1:-2], edges[2:-1])] + [f'>{edges[-2]:g}']
ticks = 0.5 * (np.r_[nu_min - 0.3, edges[1:-1]] + np.r_[edges[1:-1], edges[-2] + 3])
cmap, norm = ListedColormap(CHI_COLORS), BoundaryNorm(edges, len(CHI_COLORS))
apply_style(scale=1.4)
fig, axes = plt.subplots(1, 2, figsize=(13.5, 7.0), layout='constrained')
for ax, p in zip(axes, panels):
    g = p['g']
    xs, ys = np.sort(g[p['x']].unique()), np.sort(g[p['y']].unique())
    piv = lambda c: g.pivot(index=p['y'], columns=p['x'], values=c).loc[ys, xs].to_numpy()
    X, Y = np.meshgrid(xs, ys)
    pc = ax.pcolormesh(X, Y, piv('chi2') / DOF, cmap=cmap, norm=norm, shading='nearest', rasterized=True)
    cs = ax.contour(X, Y, piv('bulk_age_Ma'), levels=list(MEASURED_AGE), colors=INK, linewidths=1.2,
                    linestyles='--', zorder=3)
    ax.clabel(cs, fmt=lambda v: f'{v:.0f} Ma', fontsize=15)
    j = g['chi2'].idxmin()
    ax.plot(g.loc[j, p['x']], g.loc[j, p['y']], 'D', color='white', mec=INK, ms=11, zorder=6)
    b = p['s']['best']
    if not p['s']['flag'] and (b[p['x']] != g.loc[j, p['x']] or b[p['y']] != g.loc[j, p['y']]):
        ax.plot(b[p['x']], b[p['y']], '*', color='white', mec=INK, ms=20, zorder=6)
    ax.set_xlim(*p['xlim']); ax.set_ylim(*p['ylim'])
    ax.set_xlabel(p['xlabel']); ax.set_ylabel(p['ylabel'])
    ax.set_title(rf"{p['title']}" + "\n" + rf"(min $\chi^2_\nu$ = {g['chi2'].min() / DOF:.2f})", fontsize=18)
cb = fig.colorbar(pc, ax=axes, pad=0.01, fraction=0.04, ticks=ticks)
cb.ax.set_yticklabels(labels, fontsize=15)
cb.set_label(r'Reduced $\chi^2$ ($^4$He/$^3$He)')
axes[0].legend(handles=[Line2D([], [], color=INK, lw=1.2, ls='--', label='Predicted He age'),
                        Line2D([], [], marker='D', color='white', mec=INK, ls='none', label='Best fit'),
                        Line2D([], [], marker='*', color='white', mec=INK, ms=17, ls='none',
                               label='Best fit, He age 130–180 Ma')],
               loc='lower left', fontsize=14)
save(fig, f'ch2_mdd_heatmaps_N{N_SEL}', bbox_inches='tight')

# ---------------------------------------------------------------------------
# Spectrum: best age-consistent burial (195 Ma) and cooling paths
# ---------------------------------------------------------------------------
SM = F.SpectrumModelFree(spec, res4['f'], res4['r'])
bb, bl = th_vals[f'bur{MAP_T_FORM:.0f}']['best'], th_vals['lin']['best']
cases = [(burial_nodes(MAP_T_FORM, bb['T_max_C'], bb['t_peak_Ma']), C_BUR,
          rf"Burial: {MAP_T_FORM:.0f} Ma, peak {bb['T_max_C']:.0f} °C at {bb['t_peak_Ma']:.0f} Ma"),
         (cooling_nodes(bl['t_form_Ma'], bl['T_C']), C_COOL,
          rf"Linear cooling: {bl['T_C']:.0f} °C at {bl['t_form_Ma']:.0f} Ma → 25 °C")]
apply_style(scale=1.4)
fig, ax = plt.subplots(figsize=(9.0, 7.0), layout='constrained')
u, Fs, Fe = spec['use'], spec['F_start'], spec['F_end']
for i in np.where(u)[0]:
    ax.fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0, zorder=1)
ax.hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=3)
handles = [Line2D([], [], color=INK, lw=2.2, label='Data (M), LB–UB box')]
for z, (nd, col, lab) in enumerate(cases):
    c2, age, pr = SM.evaluate(*nd, dt_myr=DT_MYR)
    ax.hlines(pr, Fs, Fe, color=col, lw=1.9, zorder=4 + z)
    draw_step_connectors(ax, Fs, Fe, pr, color=col, zorder=4 + z)
    handles.append(Line2D([], [], color=col, lw=1.9, label=rf"{lab}" + "\n" + rf"$\chi^2_\nu$ = {c2 / DOF:.1f}, He age {age:.0f} Ma"))
ax.set_xlim(0, 0.16); ax.set_ylim(0, 1.15)
ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
ax.legend(handles=handles, loc='lower right', fontsize=14)
save(fig, f'ch2_mdd_spectrum_compare_N{N_SEL}')

print(open(TEX).read())
for key, s in th_vals.items():
    print(key, s['best'].to_dict(), 'flag', s['flag'], 'cmin_nu', round(s['cmin'] / DOF, 2), 'n_sig', s['n_sig'])
print('N4 domains', res4['f'], res4['r'])
print('iso ridge', iso_ridge[['t_form_Ma', 'T_C', 'chi2']].iloc[::10].to_string())
