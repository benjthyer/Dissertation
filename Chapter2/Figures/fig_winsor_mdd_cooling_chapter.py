"""
Chapter/report figures for the steady (linear) cooling solution of
HT-Win-06-01b with the adopted N = 4 free domains, and its comparison with the
burial solution. Reads caches only:
  generated/data/mdd_free/absolute/N4.json             domain structure
  generated/data/mdd_free/absolute/maps_N4.csv         burial grid (fig_winsor_mdd_free.py)
  generated/data/mdd_free/absolute/maps_alt_linear_N4.csv  cooling grid (fig_winsor_mdd_alt_paths.py)

Figures (generated/mdd_free/absolute/chapter/):
  ch2_mdd_cooling_map_paths_N4   left: reduced chi^2 of linear cooling paths
                                 (T0 at t_form -> 25 C today) with He-age isopleths;
                                 right: posterior paths
  ch2_mdd_spectrum_compare_N4    4He/3He spectrum with the best age-consistent burial
                                 and cooling paths, and normalized residuals
Table: generated/data/mdd_free/absolute/cooling_posterior_N4.csv

Usage: python fig_winsor_mdd_cooling_chapter.py
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

N_SEL = 4
DATA_DIR = os.path.join(M.DATA_OUTDIR, 'mdd_free', 'absolute')
OUT = os.path.join(M.OUTDIR, 'mdd_free', 'absolute', 'chapter')
os.makedirs(OUT, exist_ok=True)

T_END = 25.0
MEASURED_AGE = (130.0, 180.0)
GEOL_T_FORM = (180.0, 210.0)
AFT_BOX = dict(t=(85.0, 100.0), T=(50.0, 70.0))
PLATEAU = (0.04, 0.07)
N_PATHS = 300
T_FORM_STEP, T_STEP = 5.0, 1.0
DT_MYR = 1.0

INK, MUTED, BOX = '#222222', '#8a8a8a', '#d9d9d9'
C_COOL, C_BUR, C_OUT, C_AFT = '#1baa6b', '#2a78d6', '#b4b4b4', '#eb6834'
CHI_COLORS = ['#104281', '#256abf', '#5598e7', '#9ec5f4', '#cde2fb', '#f3f6fa']
STROKE = [pe.withStroke(linewidth=3.2, foreground=INK)]

spec = M.load_spectrum()
N_FIT = spec['n_fit']
res = json.load(open(os.path.join(DATA_DIR, f'N{N_SEL}.json')))
SM = F.SpectrumModelFree(spec, res['f'], res['r'])
DOF_COOL, DOF_BUR = N_FIT - 2, N_FIT - 3


def cooling_nodes(t_form, T0):
    return [t_form, 0.0], [T0, T_END]


def burial_nodes(t_form, T_max, t_peak):
    return [t_form, t_peak, 50.0, 0.0], [M.T_SURF, T_max, M.T_SURF, M.T_SURF]


def age_ok(a):
    return (a >= MEASURED_AGE[0]) & (a <= MEASURED_AGE[1])


def save(fig, name, **kw):
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(OUT, f'{name}.{ext}'), dpi=200, **kw)
    plt.close(fig)


g = pd.read_csv(os.path.join(DATA_DIR, f'maps_alt_linear_N{N_SEL}.csv'))
gb = pd.read_csv(os.path.join(DATA_DIR, f'maps_N{N_SEL}.csv'))
cmin = g['chi2'].min()
s_infl = max(1.0, cmin / DOF_COOL)
thr = cmin + 2.30 * s_infl
best_all = g.loc[g['chi2'].idxmin()]
gok = g[age_ok(g['bulk_age_Ma'])]
best_ok = gok.loc[gok['chi2'].idxmin()]
gw = gok[(gok['t_form_Ma'] >= GEOL_T_FORM[0]) & (gok['t_form_Ma'] <= GEOL_T_FORM[1])]
best_win = gw.loc[gw['chi2'].idxmin()]
bok = gb[age_ok(gb['bulk_age_Ma'])]
bb = bok.loc[bok['chi2'].idxmin()]

# ---------------------------------------------------------------------------
# posterior: unconditional and conditioned on the measured He age
# ---------------------------------------------------------------------------
rng = np.random.default_rng(1)
w = np.exp(-(g['chi2'] - cmin) / (2 * s_infl)).to_numpy()


def draw(weights, n):
    idx = rng.choice(len(g), size=n, p=weights / weights.sum())
    tf = g['t_form_Ma'].to_numpy()[idx] + rng.uniform(-T_FORM_STEP / 2, T_FORM_STEP / 2, n)
    T0 = g['T_C'].to_numpy()[idx] + rng.uniform(-T_STEP / 2, T_STEP / 2, n)
    return idx, tf, T0


idx, tf_s, T0_s = draw(w, N_PATHS)
ages = g['bulk_age_Ma'].to_numpy()[idx]
ok = age_ok(ages)
idx_c, tf_c, T0_c = draw(w * age_ok(g['bulk_age_Ma']).to_numpy(), 4000)
q = lambda a: (float(np.percentile(a, 16)), float(np.percentile(a, 50)), float(np.percentile(a, 84)))
T90_c = T_END + (T0_c - T_END) * 90.0 / tf_c
rate_c = (T0_c - T_END) / tf_c
post = dict(frac_age_ok=float(ok.mean()),
            t_form_all=q(tf_s), T0_all=q(T0_s),
            t_form_ageok=q(tf_c), T0_ageok=q(T0_c), T90_ageok=q(T90_c), rate_ageok=q(rate_c),
            age_ageok=q(g['bulk_age_Ma'].to_numpy()[idx_c]))
pd.DataFrame([{k: (np.round(v, 2) if isinstance(v, tuple) else v) for k, v in post.items()}]).to_csv(
    os.path.join(DATA_DIR, f'cooling_posterior_N{N_SEL}.csv'), index=False)

# ---------------------------------------------------------------------------
# map + paths
# ---------------------------------------------------------------------------
nu_min = cmin / DOF_COOL
edges = np.r_[0.0, np.round(nu_min + np.array([0.3, 0.8, 1.8, 3.8, 6.8]), 1), 1e9]
labels = [f'<{edges[1]:g}'] + [f'{a:g}–{b:g}' for a, b in zip(edges[1:-2], edges[2:-1])] + [f'>{edges[-2]:g}']
ticks = 0.5 * (np.r_[nu_min - 0.3, edges[1:-1]] + np.r_[edges[1:-1], edges[-2] + 3])
cmap, norm = ListedColormap(CHI_COLORS), BoundaryNorm(edges, len(CHI_COLORS))

apply_style(scale=1.1)
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.4), gridspec_kw=dict(width_ratios=[1.12, 1]))
tfs, Ts = np.sort(g['t_form_Ma'].unique()), np.sort(g['T_C'].unique())
piv = lambda c: g.pivot(index='T_C', columns='t_form_Ma', values=c).loc[Ts, tfs].to_numpy()
TF, TT = np.meshgrid(tfs, Ts)
pc = ax.pcolormesh(TF, TT, piv('chi2') / DOF_COOL, cmap=cmap, norm=norm, shading='nearest', rasterized=True)
ax.add_patch(Rectangle((GEOL_T_FORM[0], 25), np.diff(GEOL_T_FORM)[0], 95, fill=False, ec=MUTED,
                       hatch='///', lw=0.8, zorder=2))
cs = ax.contour(TF, TT, piv('bulk_age_Ma'), levels=list(MEASURED_AGE), colors=INK, linewidths=1.2,
                linestyles='--', zorder=3)
ax.clabel(cs, fmt=lambda v: f'{v:.0f} Ma', fontsize=9)
c1 = ax.contour(TF, TT, piv('chi2'), levels=[thr], colors='white', linewidths=1.6, zorder=4)
c1.set_path_effects(STROKE)
ax.plot(best_all['t_form_Ma'], best_all['T_C'], 'D', color='white', mec=INK, ms=7, zorder=5)
ax.plot(best_ok['t_form_Ma'], best_ok['T_C'], '*', color='white', mec=INK, ms=13, zorder=5)
ax.set_xlim(320, 50)
ax.set_ylim(40, 120)
ax.set_xlabel(r'Crystallization age, $t_\mathrm{form}$ (Ma)')
ax.set_ylabel(r'Temperature at crystallization, $T_0$ (°C)')
ax.set_title(rf'Linear cooling to 25 °C (min $\chi^2_\nu$ = {nu_min:.2f})', fontsize=12)
cb = fig.colorbar(pc, ax=ax, pad=0.02, fraction=0.05, ticks=ticks)
cb.ax.set_yticklabels(labels, fontsize=9)
cb.set_label(r'Reduced $\chi^2$ ($^4$He/$^3$He)', fontsize=10)
ax.legend(handles=[Line2D([], [], color='white', lw=1.6, path_effects=STROKE, label=r'Joint 1$\sigma$'),
                   Line2D([], [], color=INK, lw=1.2, ls='--', label='Predicted He age'),
                   Rectangle((0, 0), 1, 1, fc='none', ec=MUTED, hatch='///', label='180–210 Ma'),
                   Line2D([], [], marker='D', color='white', mec=INK, ls='none', label='Best fit'),
                   Line2D([], [], marker='*', color='white', mec=INK, ms=11, ls='none',
                          label='Best fit, He age 130–180 Ma')],
          loc='lower left', fontsize=8.5)

tt = np.linspace(0, 320, 400)
for k in range(N_PATHS):
    m = tt <= tf_s[k]
    ax2.plot(tt[m], np.interp(tt[m], [0.0, tf_s[k]], [T_END, T0_s[k]]), color=C_COOL if ok[k] else C_OUT,
             lw=0.6, alpha=0.3, zorder=2 if ok[k] else 1)
ax2.plot(*cooling_nodes(best_ok['t_form_Ma'], best_ok['T_C']), color=INK, lw=2.0, zorder=4)
ax2.plot(*cooling_nodes(best_all['t_form_Ma'], best_all['T_C']), color=INK, lw=1.4, ls='--', zorder=4)
ax2.plot(*burial_nodes(bb['t_form_Ma'], bb['T_max_C'], bb['t_peak_Ma']), color=C_BUR, lw=1.6, ls=':', zorder=4)
ax2.add_patch(Rectangle((AFT_BOX['t'][0], AFT_BOX['T'][0]), 15, 20, fill=False, ec=C_AFT, lw=1.8, zorder=5))
ax2.set_xlim(320, 0)
ax2.set_ylim(0, 120)
ax2.set_xlabel('Time (Ma)')
ax2.set_ylabel('Temperature (°C)')
ax2.set_title(f'Posterior paths; He age 130–180 Ma: {100 * ok.mean():.0f}%', fontsize=12)
ax2.legend(handles=[Line2D([], [], color=INK, lw=2.0, label='Best fit, He age 130–180 Ma'),
                    Line2D([], [], color=INK, lw=1.4, ls='--', label='Best fit (He age too young)'),
                    Line2D([], [], color=C_COOL, lw=1.2, label='Posterior, He age 130–180 Ma'),
                    Line2D([], [], color=C_OUT, lw=1.2, label='Posterior, other He age'),
                    Line2D([], [], color=C_BUR, lw=1.6, ls=':', label='Best burial path'),
                    Line2D([], [], color=C_AFT, lw=1.8, label='AFT peak window')],
           loc='upper left', fontsize=8.5)
fig.tight_layout()
save(fig, f'ch2_mdd_cooling_map_paths_N{N_SEL}')

# ---------------------------------------------------------------------------
# spectrum: burial vs cooling, with normalized residuals
# ---------------------------------------------------------------------------
cases = [('burial', burial_nodes(bb['t_form_Ma'], bb['T_max_C'], bb['t_peak_Ma']), C_BUR,
          rf"Burial: {bb['t_form_Ma']:.0f} Ma, peak {bb['T_max_C']:.0f} °C at {bb['t_peak_Ma']:.0f} Ma",
          DOF_BUR),
         ('cooling', cooling_nodes(best_ok['t_form_Ma'], best_ok['T_C']), C_COOL,
          rf"Cooling: {best_ok['T_C']:.0f} °C at {best_ok['t_form_Ma']:.0f} Ma → 25 °C", DOF_COOL)]
apply_style()
fig, (ax, axr) = plt.subplots(2, 1, figsize=(7.5, 7.0), sharex=True, gridspec_kw=dict(height_ratios=[2.6, 1]))
u, Fs, Fe = spec['use'], spec['F_start'], spec['F_end']
for a in (ax, axr):
    a.axvspan(*PLATEAU, color='#f3f3f3', lw=0, zorder=0)
for i in np.where(u)[0]:
    ax.fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0, zorder=1)
ax.hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=3)
handles = [Line2D([], [], color=INK, lw=2.2, label='Data (M), LB–UB box')]
axr.axhline(0, color=INK, lw=0.8)
contrib = {}
Fmid = 0.5 * (Fs + Fe)
for z, (key, nd, col, lab, dof) in enumerate(cases):
    c2, age, p = SM.evaluate(*nd, dt_myr=DT_MYR)
    ax.hlines(p, Fs, Fe, color=col, lw=1.9, zorder=4 + z)
    draw_step_connectors(ax, Fs, Fe, p, color=col, zorder=4 + z)
    rz = (p - spec['R_M']) / spec['sigma']
    axr.plot(Fmid[u], rz[u], 'o-' if key == 'cooling' else 's-', color=col, ms=4, lw=0.9, zorder=3 + z)
    contrib[key] = dict(total=float(np.sum(rz[u] ** 2)), first6=float(np.sum(rz[u][:6] ** 2)),
                        plateau=float(np.sum(rz[u & (Fmid >= PLATEAU[0]) & (Fmid <= PLATEAU[1])] ** 2)),
                        last=float(np.sum(rz[u][-2:] ** 2)), age=age)
    handles.append(Line2D([], [], color=col, lw=1.9,
                          label=rf"{lab}; $\chi^2_\nu$ = {c2 / dof:.1f}, He age {age:.0f} Ma"))
ax.set_xlim(0, 0.16)
ax.set_ylim(0, 1.15)
ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
ax.legend(handles=handles, loc='lower right', fontsize=8.5)
axr.set_ylabel(r'(model − data)/$\sigma$')
axr.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
fig.tight_layout(h_pad=0.4)
save(fig, f'ch2_mdd_spectrum_compare_N{N_SEL}')

print('best cooling (global):', best_all.to_dict(), 'chi2nu', best_all['chi2'] / DOF_COOL)
print('best cooling (age ok):', best_ok.to_dict(), 'chi2nu', best_ok['chi2'] / DOF_COOL)
print('best cooling (age ok, 180-210):', best_win.to_dict(), 'chi2nu', best_win['chi2'] / DOF_COOL)
print('best burial (age ok):', bb.to_dict(), 'chi2nu', bb['chi2'] / DOF_BUR)
print('posterior:', json.dumps(post, indent=1))
print('chi2 contributions:', json.dumps(contrib, indent=1))
