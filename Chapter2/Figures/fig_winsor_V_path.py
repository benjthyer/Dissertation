"""
Peak temperature vs predicted (U-Th)/He age for Win-06-01b goethite under a
symmetric "V" thermal history, and the fit of each path to the HT-Win-06-01b
4He/3He spectrum.

Thermal history (one free parameter, T_MAX):
    goethite crystallizes at the surface (T_SURF) at T_START = 200 Ma,
    heats linearly to T_MAX at T_PEAK = 100 Ma (burial), and cools linearly
    back to T_SURF at the present (exhumation) -- equal and opposite slopes.

Natural model: one spherical retentive domain with uniform, constant 4He
production from T_START and the retentive-domain kinetics of
fig_winsor_ratio_tau_inversion.py (Stage 1 Ea and D0/a^2 as published), solved exactly in sine-series modes for piecewise-constant
T (DT_MYR steps).

Predicted He age: 4He retained / production rate. If U and Th are spread
through the aliquot in proportion to volume (as the proton-induced 3He is),
the 7.5% LRD, which holds no 4He, lowers the bulk age by (1 - LRD_FRAC);
that bulk age is the solid curve, and the retentive-domain age is dashed.

Spectrum: each path's 4He profile is degassed through the retentive
domain's lab tau path, solved from the measured cumulative 3He with the 7.5%
LRD. The LRD/retentive diffusivity ratio rho (a lab-only parameter) is
re-optimized for every T_MAX. Same data selection, uncertainties and
R_step/R_bulk definition as fig_winsor_ratio_tau_inversion.py.

Band: +/-1 sigma extrapolation uncertainty of the Stage 1 Arrhenius line,
applied to D/a^2 at each temperature.

Reads:  generated/data/winsor_tau_inversion_summary.json, *_steps.csv
        (run fig_winsor_ratio_tau_inversion.py first)
        generated/data/stage1_regression_cache.json
Writes: generated/winsor_Vpath_Tmax_vs_age.{pdf,png}
        generated/winsor_Vpath_spectrum.{pdf,png}
        generated/data/winsor_Vpath_results.csv, winsor_Vpath_summary.json
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import load_stage1_cache, draw_step_connectors
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_DIR = os.path.join(OUTDIR, 'data')

T_START, T_PEAK, T_SURF = 200.0, 100.0, 20.0   # Ma, Ma, deg C
T_MAX_GRID = np.arange(20.0, 85.01, 0.5)
DT_MYR = 0.5
MEASURED_AGE = (130.0, 180.0)                   # Ma
AFT_RANGE = (50.0, 70.0)                        # deg C, Gibson & Stuwe (2000)
SPECTRUM_T_MAX = (50.0, 60.0, 70.0)
LOG_RHO_GRID = np.arange(0.0, 2.501, 0.05)
R_CAL = 1.987
SEC_PER_MYR = 3.15576e13

C_MAIN = '#2a78d6'
RAMP = ['#86b6ef', '#2a78d6', '#104281']        # light -> dark for 50/60/70 C
INK, MUTED, BOX = '#222222', '#a3a3a3', '#d9d9d9'
FILL_AGE, FILL_AFT = '#e6e6e6', '#fbe3d6'

S = json.load(open(os.path.join(DATA_DIR, 'winsor_tau_inversion_summary.json')))
steps = pd.read_csv(os.path.join(DATA_DIR, 'winsor_tau_inversion_steps.csv'))
LRD_FRAC = S['LRD_frac']
Ea, D0a2 = S['Ea_cal_mol'], S['D0_a2_stage1']   # Stage 1 as published

# --- sphere modes ------------------------------------------------------------
K_MODES = 8000
k = np.arange(1, K_MODES + 1, dtype=float)
lam = (k * np.pi) ** 2
c_uni = 2 * (-1) ** (k + 1) / (k * np.pi)
w_int = (-1) ** (k + 1) / (k * np.pi)


def uniform_F(tau):
    """Cumulative release from a uniform sphere (short-time form; tau < 0.1 here)."""
    tau = np.asarray(tau, dtype=float)
    return 6 * np.sqrt(tau / np.pi) - 3 * tau


_LT = np.linspace(-14, -1, 6001)


def tau_ret_from_F(F_total, rho):
    F_mix = LRD_FRAC * uniform_F(rho * 10 ** _LT) + (1 - LRD_FRAC) * uniform_F(10 ** _LT)
    return 10 ** np.interp(F_total, F_mix, _LT)


# --- kinetics and its extrapolation uncertainty ------------------------------
cache = load_stage1_cache()
s1 = cache['M']
win = steps['F_end'].to_numpy() >= cache['fractional_yield_threshold']
assert win.sum() == s1['n_points']
x_bar = (10000.0 / (steps['Temp_C'].to_numpy()[win] + 273.0)).mean()
sxx_over_n = (s1['intercept_stderr'] / s1['slope_stderr']) ** 2 - x_bar ** 2


def D_a2_per_myr(T_celsius, kin_sigma=0.0):
    T_celsius = np.asarray(T_celsius, dtype=float)
    x = 10000.0 / (T_celsius + 273.0)
    sig = s1['slope_stderr'] * np.sqrt(sxx_over_n + (x - x_bar) ** 2)
    return D0a2 * np.exp(-Ea / (R_CAL * (T_celsius + 273.0)) + kin_sigma * sig) * SEC_PER_MYR


# --- V path forward model ------------------------------------------------------
EDGES = np.arange(T_START, -1e-9, -DT_MYR)           # Ma, decreasing
MID = 0.5 * (EDGES[:-1] + EDGES[1:])


def v_path(T_max, t_ma):
    t_ma = np.asarray(t_ma, dtype=float)
    up = T_SURF + (T_max - T_SURF) * (T_START - t_ma) / (T_START - T_PEAK)
    down = T_SURF + (T_max - T_SURF) * t_ma / T_PEAK
    return np.where(t_ma >= T_PEAK, up, down)


def natural_modes(T_max, kin_sigma=0.0):
    """Modes of the retentive domain's 4He profile today (production = 1 per Myr)."""
    A = np.zeros(K_MODES)
    for Dm in D_a2_per_myr(v_path(T_max, MID), kin_sigma):
        x = lam * Dm * DT_MYR
        A = A * np.exp(-x) + c_uni * DT_MYR * (-np.expm1(-x)) / np.maximum(x, 1e-300)
    return A


def retentive_age(A):
    return 3 * float(A @ w_int)      # Ma, for production of 1 per Myr


# --- spectrum data -------------------------------------------------------------
F_start, F_end = steps['F_start'].to_numpy(), steps['F_end'].to_numpy()
dF3 = F_end - F_start
R_M, R_LB, R_UB = (steps[c].to_numpy() for c in ('R_M', 'R_LB', 'R_UB'))
sigma = steps['sigma'].to_numpy()
use = steps['used_in_fit'].to_numpy().astype(bool)
n_fit = int(use.sum())
E_by_rho = {lr: np.exp(-np.outer(np.r_[0.0, tau_ret_from_F(F_end, 10 ** lr)], lam))
            for lr in LOG_RHO_GRID}


def spectrum(A, lr):
    N = E_by_rho[lr] @ (A * w_int)
    return -np.diff(N) / N[0] / dF3


def best_spectrum_fit(A):
    best = None
    for lr in LOG_RHO_GRID:
        p = spectrum(A, lr)
        chi = float(np.sum(((p[use] - R_M[use]) / sigma[use]) ** 2))
        if best is None or chi < best[0]:
            best = (chi, lr, p)
    return best


# --- sweep ---------------------------------------------------------------------
rows = []
pred_store = {}
for Tm in T_MAX_GRID:
    A = natural_modes(Tm)
    age_ret = retentive_age(A)
    chi, lr, p = best_spectrum_fit(A)
    rows.append(dict(T_max_C=Tm, age_retentive_Ma=age_ret,
                     age_bulk_Ma=(1 - LRD_FRAC) * age_ret,
                     age_bulk_kin_minus_Ma=(1 - LRD_FRAC) * retentive_age(natural_modes(Tm, -1.0)),
                     age_bulk_kin_plus_Ma=(1 - LRD_FRAC) * retentive_age(natural_modes(Tm, +1.0)),
                     chi2=chi, log10_rho=lr))
    pred_store[round(Tm, 2)] = p
res = pd.DataFrame(rows)
res.to_csv(os.path.join(DATA_DIR, 'winsor_Vpath_results.csv'), index=False)

dof = n_fit - 2
i_best = int(res['chi2'].idxmin())
chi_min = res['chi2'][i_best]
dchi = max(1.0, chi_min / dof)
ok = res['T_max_C'][res['chi2'] <= chi_min + dchi]
T_best, T_lo, T_hi = float(res['T_max_C'][i_best]), float(ok.min()), float(ok.max())
age_at = lambda T: float(np.interp(T, res['T_max_C'], res['age_bulk_Ma']))
in_age = res['T_max_C'][(res['age_bulk_Ma'] >= MEASURED_AGE[0]) & (res['age_bulk_Ma'] <= MEASURED_AGE[1])]
summary = dict(
    T_start_Ma=T_START, T_peak_Ma=T_PEAK, T_surface_C=T_SURF, LRD_frac=LRD_FRAC,
    spectrum_best_T_max_C=T_best, spectrum_T_max_1sig_C=[T_lo, T_hi],
    spectrum_chi2_nu=chi_min / dof, spectrum_log10_rho=float(res['log10_rho'][i_best]),
    isothermal_fit_chi2_nu=S['chi2_nu'],
    bulk_age_at_best_Ma=age_at(T_best), bulk_age_at_1sig_Ma=[age_at(T_hi), age_at(T_lo)],
    T_max_range_matching_measured_age_C=[float(in_age.min()), float(in_age.max())],
    bulk_age_no_heating_Ma=age_at(T_SURF),
)
json.dump(summary, open(os.path.join(DATA_DIR, 'winsor_Vpath_summary.json'), 'w'), indent=2)
print(json.dumps(summary, indent=1))

# --- Figure 1: T_max vs predicted He age ---------------------------------------
fig, ax = plt.subplots()
ax.axvspan(*MEASURED_AGE, color=FILL_AGE, lw=0, zorder=0)
ax.axhspan(*AFT_RANGE, color=FILL_AFT, lw=0, zorder=0)
ax.fill_betweenx(res['T_max_C'], res['age_bulk_kin_minus_Ma'], res['age_bulk_kin_plus_Ma'],
                 color=C_MAIN, alpha=0.15, lw=0, zorder=1)
ax.plot(res['age_bulk_Ma'], res['T_max_C'], color=C_MAIN, lw=2.0, zorder=3)
ax.plot(res['age_retentive_Ma'], res['T_max_C'], color=C_MAIN, lw=1.2, ls='--', zorder=2)
ax.errorbar(age_at(T_best), T_best, yerr=[[T_best - T_lo], [T_hi - T_best]], fmt='D',
            color=INK, ms=7, mec='white', mew=1.2, capsize=3, zorder=5)
ax.text(MEASURED_AGE[0] + 2, 22, 'Measured\nHe age', fontsize=10, color='#555555', va='bottom')
ax.text(3, AFT_RANGE[0] + 1.0, 'AFT: cooled from 50–70 °C\nafter ~85 Ma', fontsize=10,
        color='#7a4a33', va='bottom')
ax.set_xlim(0, 205)
ax.set_ylim(20, 85)
ax.set_xlabel('Predicted (U–Th)/He age (Ma)')
ax.set_ylabel(r'Peak temperature at 100 Ma, $T_\mathrm{max}$ (°C)')
ax.set_title('V-shaped burial path: peak temperature vs He age', fontsize=14)
handles = [Line2D([], [], color=C_MAIN, lw=2.0, label='Bulk age (7.5% LRD holds no $^4$He)'),
           Line2D([], [], color=C_MAIN, lw=1.2, ls='--', label='Retentive domain only'),
           Line2D([], [], color=INK, marker='D', ls='none', ms=7,
                  label=rf'$^4$He/$^3$He spectrum fit, {T_best:.0f} °C ($\pm1\sigma$)')]
ax.legend(handles=handles, loc='lower left', fontsize=9.5)
# inset: the thermal path
ins = ax.inset_axes([0.1, 0.66, 0.32, 0.27])
tt = np.linspace(0, T_START, 201)
ins.plot(tt, v_path(T_best, tt), color=INK, lw=1.5)
ins.set_xlim(T_START, 0)
ins.set_ylim(10, T_best + 10)
ins.set_xticks([200, 100, 0])
ins.set_yticks([T_SURF, round(T_best)])
ins.tick_params(labelsize=8)
ins.set_xlabel('Ma', fontsize=8, labelpad=1)
ins.set_ylabel('°C', fontsize=8, labelpad=1)
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUTDIR, f'winsor_Vpath_Tmax_vs_age.{ext}'), dpi=200)
plt.close(fig)

# --- Figure 2: spectrum predictions for representative paths --------------------
fig, ax = plt.subplots()
for i in np.where(use)[0]:
    ax.fill_between([F_start[i], F_end[i]], R_LB[i], R_UB[i], color=BOX, lw=0, zorder=1)
ax.hlines(R_M[use], F_start[use], F_end[use], color=INK, lw=2.2, zorder=3)
handles = [Line2D([], [], color=INK, lw=2.2, label='Data (M), LB–UB box')]
for Tm, col in zip(SPECTRUM_T_MAX, RAMP):
    p = pred_store[round(Tm, 2)]
    chi = float(res.loc[np.isclose(res['T_max_C'], Tm), 'chi2'].iloc[0])
    ax.hlines(p, F_start, F_end, color=col, lw=1.8, zorder=4)
    draw_step_connectors(ax, F_start, F_end, p, color=col, zorder=4)
    handles.append(Line2D([], [], color=col, lw=1.8,
                          label=rf'$T_\mathrm{{max}}$ = {Tm:.0f} °C, $\chi^2_\nu$ = {chi / dof:.1f}'))
iso = steps['pred_best'].to_numpy()
ax.hlines(iso, F_start, F_end, color=MUTED, lw=1.3, linestyles='--', zorder=2)
handles.append(Line2D([], [], color=MUTED, lw=1.3, ls='--',
                      label=rf'Isothermal best fit, $\chi^2_\nu$ = {S["chi2_nu"]:.1f}'))
ax.set_xlim(0, 0.16)
ax.set_ylim(0, 1.2)
ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
ax.set_title('HT-Win-06-01b: V-shaped burial paths', fontsize=14)
ax.legend(handles=handles, loc='lower right', fontsize=9.5)
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUTDIR, f'winsor_Vpath_spectrum.{ext}'), dpi=200)
plt.close(fig)
