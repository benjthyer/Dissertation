"""
PROTOTYPE: single combined 4He/3He spectrum figure for HT-Win-06-01b goethite,
merging the two spectrum figures of the Ch. 2 paper:
  * Comparative_Ratios_Dtplot_WinsorGT_VacuumHDMKAF.pdf (fig_3_4_plot.py):
        hydrothermal spectrum vs the two vacuum step heats of the same sample
  * ch2_mdd_spectrum_compare_N4.pdf (fig_winsor_mdd_cooling_chapter.py):
        hydrothermal spectrum vs best burial and steady-cooling predictions

Hydrothermal data (black, grey LB-UB boxes), the two vacuum datasets
(Monteiro 2017; Farley et al. 2024; full range, on a two-scale x axis) and the two model predictions, in one panel (the
residuals panel of the original model figure is omitted).
Data/model handling is copied from the two source scripts; caches only
(no refits).

Reads:  data/HM_Win_06_01B.csv, data/Winsor_waterKAF_BJT.csv (vacuum);
        generated/data/mdd_free/absolute/{N4.json,maps_N4.csv,maps_alt_linear_N4.csv}
Output: generated/Ch2_spectra_combined.{pdf,png}
"""
import os
import sys
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M
import winsor_he43_mdd_free as F
from thermochr_utils import (diffusion_reduction, accumulate, step_yield_edges,
                             draw_step_connectors)
from plot_style import apply_style

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(FIG_DIR, 'data')
OUT = os.path.join(FIG_DIR, 'generated')
DATA_DIR = os.path.join(M.DATA_OUTDIR, 'mdd_free', 'absolute')
N_SEL, DT_MYR, T_END = 4, 1.0, 25.0
MEASURED_AGE = (130.0, 180.0)
# Two-scale x axis as in fig_3_4_plot.py: 0-X_BREAK fills the left ZOOM_FRAC of the
# axes, X_BREAK-1 the remainder, so the vacuum Stage 2/3 transition near 0.9 stays visible.
X_BREAK, ZOOM_FRAC = 0.2, 0.7

INK, BOX = '#222222', '#d9d9d9'
C_COOL, C_BUR = '#1baa6b', '#2a78d6'
C_HDM, C_KAF = 'orange', 'red'

# ---------------------------------------------------------------------------
# vacuum datasets (same reduction as fig_3_4_plot.py; no files written)
# ---------------------------------------------------------------------------
def vacuum_spectrum(csv, cols, skiprows=None, nrows=None):
    d = pd.read_csv(os.path.join(RAW, csv), skiprows=skiprows)
    if nrows:
        d = d[:nrows]
    TK, ts = np.array(d['Temp (C)']) + 273, np.array(d['Time (h)']) * 3600
    y = []
    for c in cols:
        y.append(diffusion_reduction(np.array(d[c]).astype(float), TimeSeconds=ts, TempKelvin=TK,
                                     newDiffName=os.path.join(OUT, 'data', '_tmp_diff.csv'))
                 ['He Yield (nCC@STP)'])
        plt.close()
    c3, c4 = accumulate(y[0]), accumulate(y[1])
    ratio = ((y[1] / y[0]) / (c4[-1] / c3[-1])).to_numpy()
    fs, fe = step_yield_edges(c3 / c3[-1])
    return fs, fe, ratio


vac = {'HDM': vacuum_spectrum('HM_Win_06_01B.csv', ['3HeCPS', '4HeCPS']),
       'KAF': vacuum_spectrum('Winsor_waterKAF_BJT.csv', ['3He PCC', '4He NCC'], skiprows=1, nrows=30)}
tmp = os.path.join(OUT, 'data', '_tmp_diff.csv')
if os.path.exists(tmp):
    os.remove(tmp)

# ---------------------------------------------------------------------------
# hydrothermal data and thermal-model predictions (as in
# fig_winsor_mdd_cooling_chapter.py)
# ---------------------------------------------------------------------------
spec = M.load_spectrum()
res = json.load(open(os.path.join(DATA_DIR, f'N{N_SEL}.json')))
SM = F.SpectrumModelFree(spec, res['f'], res['r'])
N_FIT = spec['n_fit']
DOF_COOL, DOF_BUR = N_FIT - 2, N_FIT - 3

g = pd.read_csv(os.path.join(DATA_DIR, f'maps_alt_linear_N{N_SEL}.csv'))
gb = pd.read_csv(os.path.join(DATA_DIR, f'maps_N{N_SEL}.csv'))
age_ok = lambda a: (a >= MEASURED_AGE[0]) & (a <= MEASURED_AGE[1])
gok = g[age_ok(g['bulk_age_Ma'])]
best_ok = gok.loc[gok['chi2'].idxmin()]
bok = gb[age_ok(gb['bulk_age_Ma'])]
bb = bok.loc[bok['chi2'].idxmin()]

cases = [('burial', [bb['t_form_Ma'], bb['t_peak_Ma'], 50.0, 0.0],
          [M.T_SURF, bb['T_max_C'], M.T_SURF, M.T_SURF], C_BUR,
          f"Burial: {bb['t_form_Ma']:.0f} Ma, peak {bb['T_max_C']:.0f} °C at {bb['t_peak_Ma']:.0f} Ma",
          DOF_BUR),
         ('cooling', [best_ok['t_form_Ma'], 0.0], [best_ok['T_C'], T_END], C_COOL,
          f"Cooling: {best_ok['T_C']:.0f} °C at {best_ok['t_form_Ma']:.0f} Ma → 25 °C", DOF_COOL)]

# ---------------------------------------------------------------------------
apply_style()
fig, ax = plt.subplots(figsize=(6.4, 4.6))
u, Fs, Fe = spec['use'], spec['F_start'], spec['F_end']

handles = []
# vacuum datasets, thin and behind the hydrothermal data
for key, col, lab in [('HDM', C_HDM, 'Vacuum: Monteiro (2017)'), ('KAF', C_KAF, 'Vacuum: Farley et al. (2024)')]:
    fs, fe, r = vac[key]
    ax.hlines(r, fs, fe, color=col, lw=1.6, zorder=2)
    draw_step_connectors(ax, fs, fe, r, color=col, zorder=2)
    handles.append(Line2D([], [], color=col, lw=1.6, label=lab))

# hydrothermal data
for i in np.where(u)[0]:
    ax.fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color=BOX, lw=0, zorder=1)
ax.hlines(spec['R_M'][u], Fs[u], Fe[u], color=INK, lw=2.2, zorder=5)
handles.append(Line2D([], [], color=INK, lw=2.2, label='Water vapor saturated (this work), LB–UB box'))

for z, (key, xs, Ts, col, lab, dof) in enumerate(cases):
    c2, age, p = SM.evaluate(xs, Ts, dt_myr=DT_MYR)
    ax.hlines(p, Fs, Fe, color=col, lw=1.9, zorder=6 + z)
    draw_step_connectors(ax, Fs, Fe, p, color=col, zorder=6 + z)
    handles.append(Line2D([], [], color=col, lw=1.9,
                          label=rf"{lab}; $\chi^2_\nu$ = {c2 / dof:.1f}, He age {age:.0f} Ma"))

fwd = lambda x: np.where(np.asarray(x, float) <= X_BREAK, np.asarray(x, float) / X_BREAK * ZOOM_FRAC,
                         ZOOM_FRAC + (np.asarray(x, float) - X_BREAK) / (1 - X_BREAK) * (1 - ZOOM_FRAC))
inv = lambda y: np.where(np.asarray(y, float) <= ZOOM_FRAC, np.asarray(y, float) / ZOOM_FRAC * X_BREAK,
                         X_BREAK + (np.asarray(y, float) - ZOOM_FRAC) / (1 - ZOOM_FRAC) * (1 - X_BREAK))
ax.set_xscale('function', functions=(fwd, inv))
ax.set_xlim(0, 1)
ticks = [0, 0.05, 0.1, 0.15, 0.2, 0.4, 0.6, 0.8, 1.0]
ax.set_xticks(ticks)
ax.set_xticklabels(['0', '0.05', '0.1', '0.15', '0.2', '0.4', '0.6', '0.8', '1.0'])
gap, run, rise = 0.008, 0.006, 0.018   # double-slash break marks at the scale change (axes fractions)
for y in (0, 1):
    ax.add_patch(plt.Polygon([(ZOOM_FRAC - gap - run, y - rise), (ZOOM_FRAC + gap - run, y - rise),
                              (ZOOM_FRAC + gap + run, y + rise), (ZOOM_FRAC - gap + run, y + rise)],
                             closed=True, transform=ax.transAxes, facecolor='white', edgecolor='none',
                             clip_on=False, zorder=10))
    for dx in (-gap, gap):
        ax.plot([ZOOM_FRAC + dx - run, ZOOM_FRAC + dx + run], [y - rise, y + rise], transform=ax.transAxes,
                color='black', linewidth=1.0, clip_on=False, zorder=11)
ax.set_ylim(0, 1.15)
ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
ax.legend(handles=handles, loc="lower right", fontsize=7)
ax.grid(True, alpha=0.25)
ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUT, f'Ch2_spectra_combined.{ext}'), dpi=200)
print('wrote Ch2_spectra_combined')
