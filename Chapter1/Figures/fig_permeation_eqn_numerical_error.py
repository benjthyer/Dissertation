"""
Numerical error in the PREDICTED FRACTIONAL YIELD from the analytical
permeation equation (Eq. permsol: HeF = 1 - exp(-KGRTt)) for silica
glass ampoules, benchmarked against a numerical finite-difference
diffusion-permeation model, across a range of glass/gas volume ratios
and temperatures. (This is error in ^{He}F, NOT error in a predicted
n0 -- see fig_predicting_permeation.py for that error metric.)
Uses the permeation_sim cylindrical FDM class.

Outputs (PDFs + CSV results in this script's directory):
  NumericalEqn3.3ErrMain.pdf / .csv
  NumericalEqn3.3ErrConstLandG.pdf / .csv
  NumericalEqn3.3ErrWavesSettledProfile.pdf / .csv
  NumericalEqn3.3ErrVrVarySettledProfile.pdf / .csv
  SimulatedTubeGeometries.pdf
  SteadyStateProfileDeviation.pdf

Caching
-------
The full FDM sweep (Figures 1-4) takes ~10 minutes because each of the
hundreds of (a, b, T) combinations gets its own time-stepped
permeation_sim run. Each call to run_sim() is transparently cached to
disk (in .sim_cache/, keyed by its physical parameters) via
run_sim_cached(), so a second run of this script reuses every
previously-computed result instantly and only computes points that are
actually new (e.g. if you widen a VR sweep). Pass --no-cache to ignore
the cache and force everything to recompute (e.g. after changing
permeation_sim's underlying model -- see CACHE_VERSION below).
"""
import argparse
import hashlib
import os
import pickle
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
from tqdm.auto import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import (swets, swets_K, Ratoms, permeation_sim,
                              NovTube_blank_cooling)
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(DATA_OUTDIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Disk cache for run_sim(): each result depends only on (a, b, T, simtau_in,
# ntau_in), so results are memoized to disk keyed by those parameters. Bump
# CACHE_VERSION any time run_sim()'s model itself changes (e.g. edits to
# permeation_sim, swets_K, or the FDM integration) to invalidate old,
# now-inconsistent cached results without having to manually clear the cache
# directory.
# ---------------------------------------------------------------------------
CACHE_VERSION = 1
CACHE_DIR = os.path.join(OUTDIR, '.sim_cache')

_argparser = argparse.ArgumentParser(add_help=True)
_argparser.add_argument(
    '--no-cache', action='store_true',
    help='Ignore .sim_cache/ and recompute every simulation from scratch '
         '(overwriting any cached results).')
# parse_known_args so this still works if invoked under a test runner or
# passed extra args by an orchestrator script.
_args, _ = _argparser.parse_known_args()

_cache_stats = {'hits': 0, 'misses': 0}


def _cache_key(a, b, T, simtau_in, ntau_in) -> str:
    raw = f'{CACHE_VERSION}|{a!r}|{b!r}|{T!r}|{simtau_in!r}|{ntau_in!r}'
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()


def run_sim_cached(a, b, T, simtau_in, ntau_in):
    """Cached wrapper around run_sim(); see module docstring."""
    if _args.no_cache:
        _cache_stats['misses'] += 1
        return run_sim(a, b, T, simtau_in, ntau_in)

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, _cache_key(a, b, T, simtau_in, ntau_in) + '.pkl')
    if os.path.exists(cache_path):
        _cache_stats['hits'] += 1
        with open(cache_path, 'rb') as f:
            return pickle.load(f)

    _cache_stats['misses'] += 1
    result = run_sim(a, b, T, simtau_in, ntau_in)
    with open(cache_path, 'wb') as f:
        pickle.dump(result, f)
    return result

G_const = 3500
L_const = 0.0175
Ts3 = np.array([25, 250, 500]) + 273
T_labels = [f'T_{T - 273}C' for T in Ts3]
simtau = 150
ntau = 1
simtau2 = 150
ntau2 = 3

# ---------------------------------------------------------------------------
# Helper: run one permeation_sim series and return (ts, m_M, m_A, tau)
# ---------------------------------------------------------------------------
def run_sim(a, b, T, simtau_in, ntau_in):
    G = 2 / (np.log(b / a) * a ** 2)
    K = swets_K(T)
    tau = 1 / (G * K * Ratoms * T)
    dt = tau / simtau_in
    ts = np.arange(dt, dt * (simtau_in * ntau_in) + 1, dt)
    wb = permeation_sim(a=a, b=b, n0=1, T=T,
                        cooling_func=NovTube_blank_cooling, He=4)
    wb.stabilize_profile()
    m_M, m_A = [], []
    for t in ts:
        wb.hold_T(T, dt)
        m_M.append(wb.out / wb.n0)
        m_A.append(1 - np.exp(-T * swets_K(T) * G * Ratoms * t))
    return ts, np.array(m_M), np.array(m_A), tau, G


# ---------------------------------------------------------------------------
# Figure 1: max error vs VR  (constant G = 3500 cm⁻²)
# ---------------------------------------------------------------------------
VR = np.linspace(0.01, 50, 100)
VP = (VR + 1) ** 0.5
aa_G = (2 / (G_const * np.log(VP))) ** 0.5
bb_G = aa_G * VP

results_fig1 = {'VR': VR}
fig, ax = plt.subplots()
for h, T in enumerate(Ts3):
    maxerr = []
    for i in tqdm(range(len(VR)), desc=f'Fig1 T={T - 273}°C', unit='VR'):
        a, b = aa_G[i], bb_G[i]
        _, m_M, m_A, _, _ = run_sim_cached(a, b, T, simtau, ntau)
        pct = 100 * (m_A - m_M) / m_M
        maxerr.append(float(np.max(pct)))
    results_fig1[T_labels[h]] = maxerr
    ax.plot(VR, maxerr, color=['Blue', 'Gold', 'Red'][h],
            label=f'T = {T - 273}°C')

ax.set_title(r'Max Error in Predicted Fractional Yield ($^{He}F$)' '\n'
             r'Silica Glass Ampoules $(G = 3500\ \mathrm{cm}^{-2})$')
ax.set_xlabel(r'$V_\mathrm{glass}/V_\mathrm{gas}$')
ax.set_ylabel(r'Max % Error in Predicted $^{He}F$')
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'NumericalEqn3.3ErrMain.pdf'), dpi=300)
plt.close(fig)

pd.DataFrame(results_fig1).to_csv(
    os.path.join(DATA_OUTDIR, 'NumericalEqn3.3ErrMain.csv'), index=False)

# ---------------------------------------------------------------------------
# Figure 2: constant-L (175 µm) vs constant-G (3500 cm⁻²) on same plot
# ---------------------------------------------------------------------------
VR25 = np.linspace(0.01, 50, 25)
VP25 = (VR25 + 1) ** 0.5
aa_L = L_const / (-1 + VP25)
bb_L = L_const + aa_L
aa_G25 = (2 / (G_const * np.log(VP25))) ** 0.5
bb_G25 = aa_G25 * VP25

results_fig2 = {'VR': VR25}
fig, ax = plt.subplots()
for h, T in enumerate(Ts3):
    # Constant L
    maxerrL = []
    for i in tqdm(range(len(VR25)),
                  desc=f'Fig2 T={T - 273}°C L=const', unit='VR'):
        a, b = aa_L[i], bb_L[i]
        _, m_M, m_A, _, _ = run_sim_cached(a, b, T, simtau, ntau)
        pct = 100 * (m_A - m_M) / m_M
        maxerrL.append(float(np.max(pct)))
    results_fig2[f'{T_labels[h]}_L'] = maxerrL
    ax.plot(VR25, maxerrL, color=['Blue', 'Gold', 'Red'][h],
            label=f'T = {T - 273}°C; L = 175 µm')

    # Constant G
    maxerrG = []
    for i in tqdm(range(len(VR25)),
                  desc=f'Fig2 T={T - 273}°C G=const', unit='VR'):
        a, b = aa_G25[i], bb_G25[i]
        _, m_M, m_A, _, _ = run_sim_cached(a, b, T, simtau, ntau)
        pct = 100 * (m_A - m_M) / m_M
        maxerrG.append(float(np.max(pct)))
    results_fig2[f'{T_labels[h]}_G'] = maxerrG
    ax.scatter(VR25, maxerrG, marker='+',
               color=['Blue', 'Gold', 'Red'][h],
               label=f'T = {T - 273}°C; G = 3500 cm⁻²')

ax.set_title(r'Max Error in Predicted Fractional Yield ($^{He}F$):''\n''Constant L vs Constant G')
ax.set_xlabel(r'$V_\mathrm{glass}/V_\mathrm{gas}$')
ax.set_ylabel(r'Max % Error in Predicted $^{He}F$')
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'NumericalEqn3.3ErrConstLandG.pdf'), dpi=300)
plt.close(fig)

pd.DataFrame(results_fig2).to_csv(
    os.path.join(DATA_OUTDIR, 'NumericalEqn3.3ErrConstLandG.csv'), index=False)

# ---------------------------------------------------------------------------
# Figure 3: time-resolved error for experimental tube dimensions at 100 °C
# ---------------------------------------------------------------------------
aa_exp = np.array([0.063, 0.0747, 0.0529, 0.0487, 0.085]) / 2
bb_exp = np.array([0.096, 0.1159, 0.0835, 0.0734, 0.135]) / 2
names = ['Empty Quad', 'Empty MC', 'Sulfur MC', 'Water MC', 'DAp Quad']
colmap = plt.cm.plasma
T_100 = 100 + 273

records_fig3 = []   # long-format rows: (tube, t_over_tau, err_pct)
fig, ax = plt.subplots()
for j, i in enumerate(tqdm([3, 0, 1, 2, 4], desc='Fig3 tubes', unit='tube')):
    a, b = aa_exp[i], bb_exp[i]
    Vgas = np.pi * a ** 2
    Vglass = np.pi * b ** 2 - Vgas
    ts, m_M, m_A, tau, G = run_sim_cached(a, b, T_100, simtau2, ntau2)
    pct = 100 * (m_A - m_M) / m_M
    t_norm = ts / tau
    ax.plot(t_norm, pct,
            color=colmap(np.linspace(0, 1, 5)[j]),
            label=(names[i]
                   + r': $V_\mathrm{glass}/V_\mathrm{gas}$ = '
                   + f'{Vglass / Vgas:.2f}'))
    for t_n, p in zip(t_norm, pct):
        records_fig3.append({'tube': names[i], 't_over_tau': t_n, 'err_pct': p})

ax.set_title(r'Error in Predicted Fractional Yield ($^{He}F$)''\nExperimental Tubes at 100°C (Settled Profile)')
ax.set_xlabel(r'$t / \tau_P$')
ax.set_ylabel(r'% Error in Predicted $^{He}F$')
ax.legend(loc='lower center', fontsize=10)
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'NumericalEqn3.3ErrWavesSettledProfile.pdf'), dpi=300)
plt.close(fig)

pd.DataFrame(records_fig3).to_csv(
    os.path.join(DATA_OUTDIR, 'NumericalEqn3.3ErrWavesSettledProfile.csv'), index=False)

# ---------------------------------------------------------------------------
# Figure 4: time-resolved error for discrete VR values at 100 °C (G const)
# ---------------------------------------------------------------------------
VR_disc = np.array([0.1, 1.5, 2.5, 5, 10, 20])
VP_disc = (VR_disc + 1) ** 0.5
aa_d = (2 / (G_const * np.log(VP_disc))) ** 0.5
bb_d = aa_d * VP_disc
colmap2 = plt.cm.viridis
T_100 = 373   # 100 °C in K

records_fig4 = []   # long-format: (VR, t_over_tau, err_pct)
fig, ax = plt.subplots()
for i in tqdm(range(len(VR_disc)), desc='Fig4 VR values', unit='VR'):
    V = VR_disc[i]
    a, b = aa_d[i], bb_d[i]
    ts, m_M, m_A, tau, G = run_sim_cached(a, b, T_100, simtau2, ntau2)
    pct = 100 * (m_A - m_M) / m_M
    t_norm = ts / tau
    ax.plot(t_norm, pct,
            color=colmap2(np.linspace(0, 1, 6)[i]),
            label=(r'$V_\mathrm{glass}/V_\mathrm{gas}$ = ' + f'{V}'))
    for t_n, p in zip(t_norm, pct):
        records_fig4.append({'VR': V, 't_over_tau': t_n, 'err_pct': p})

ax.set_title(r'Error in Predicted Fractional Yield ($^{He}F$)''\n''$(G = 3500\ \mathrm{cm}^{-2})$ at 100°C')
ax.set_xlabel(r'$t / \tau_P$')
ax.set_ylabel(r'% Error in Predicted $^{He}F$')
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'NumericalEqn3.3ErrVrVarySettledProfile.pdf'), dpi=300)
plt.close(fig)

pd.DataFrame(records_fig4).to_csv(
    os.path.join(DATA_OUTDIR, 'NumericalEqn3.3ErrVrVarySettledProfile.csv'), index=False)

# ---------------------------------------------------------------------------
# Figure 5: ampoule geometries (constant-L vs constant-G)  — no CSV needed
# ---------------------------------------------------------------------------
VR_geo = np.linspace(0.01, 50, 100)
VP_geo = (VR_geo + 1) ** 0.5
aa_Lgeo = L_const / (-1 + VP_geo)
bb_Lgeo = L_const + aa_Lgeo
aa_Ggeo = (2 / (G_const * np.log(VP_geo))) ** 0.5
bb_Ggeo = aa_Ggeo * VP_geo

fig, ax = plt.subplots()
sc1 = ax.scatter(1E4 * aa_Lgeo[2:], 1E4 * bb_Lgeo[2:],
                 marker='x', c=VR_geo[2:], label='L = 175 µm')
ax.scatter(1E4 * aa_Ggeo[2:], 1E4 * bb_Ggeo[2:],
           marker='*', c=VR_geo[2:], label=r'G = 3500 cm$^{-2}$')
cbar = plt.colorbar(sc1, ax=ax)
cbar.set_label(r'$V_\mathrm{glass}/V_\mathrm{gas}$')
ax.grid()
ax.legend()
ax.set_title('Ampoule Geometries at Constant L and G')
ax.set_xlabel(r'Inner Radius $a$ (µm)')
ax.set_ylabel(r'Outer Radius $b$ (µm)')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'SimulatedTubeGeometries.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 6: ideal vs true steady-state He concentration profiles
# ---------------------------------------------------------------------------
VR_prof = np.array([0.1, 1.5, 10, 100])
VP_prof = (VR_prof + 1) ** 0.5
aa_p = L_const / (-1 + VP_prof)
bb_p = L_const + aa_p
T_prof = 273 + 100
colmap3 = plt.cm.plasma

fig, ax = plt.subplots()
for i in tqdm(range(len(VR_prof)), desc='Fig6 profiles', unit='VR'):
    V = VR_prof[i]
    a, b = aa_p[i], bb_p[i]
    G = 2 / (a ** 2 * np.log(b / a))
    wb = permeation_sim(a=a, b=b, n0=1, T=T_prof,
                        cooling_func=NovTube_blank_cooling, He=4)
    ax.scatter(1E4 * (wb.r - wb.a),
               wb.c / (wb.ngas / (wb.h * np.pi * wb.a ** 2)),
               color=colmap3(np.linspace(0, 1, 6)[i]), alpha=0.7, marker='+')
    wb.stabilize_profile()
    ax.plot(1E4 * (wb.r - wb.a),
            wb.c / (wb.ngas / (wb.h * np.pi * wb.a ** 2)),
            color=colmap3(np.linspace(0, 1, 6)[i]), alpha=0.7,
            label=(r'$V_\mathrm{glass}/V_\mathrm{gas}$ = '+ f'{V}'))

ax.legend()
ax.set_title('Ideal and True EQM He Concentration Profiles\n'
             'For 175 µm Silica Ampoules at 100°C')
ax.set_ylabel(r'$C/C_\mathrm{gas}$')
ax.set_xlabel('Distance from Inner Wall (µm)')
ax.grid()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'SteadyStateProfileDeviation.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Cache summary (Figures 1-4 only; Figures 5-6 don't call run_sim_cached)
# ---------------------------------------------------------------------------
_hits, _misses = _cache_stats['hits'], _cache_stats['misses']
print(f'run_sim cache: {_hits} hit(s), {_misses} miss(es) computed and cached '
      f'to {CACHE_DIR}')
if _args.no_cache:
    print('(--no-cache was set: every result above was recomputed from scratch.)')
