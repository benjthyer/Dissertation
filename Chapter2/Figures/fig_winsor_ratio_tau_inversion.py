"""
Inversion of the HT-Win-06-01b bulk-normalized 4He/3He spectrum for the
natural diffusion time tau_nat (= integral of (D/a^2) dt in nature) of the
retentive goethite domain, in the ratio-evolution framework of Shuster &
Farley (2004).

Model
-----
* Proton-induced 3He is uniform. LRD_FRAC (7.5%) of total 3He sits in a
  low-retentivity domain (LRD) holding no radiogenic 4He; the other 92.5% of
  the 3He and ALL radiogenic 4He sit in one spherical retentive domain.
* Nature: uniform, constant 4He production with diffusion at constant
  temperature (zero concentration at the domain edge) since He retention
  began, so the 4He profile depends on one number, tau_nat.
* Lab: both domains are spheres with the same activation energy; the LRD's
  D/a^2 is RHO times the retentive domain's at every temperature, so
  tau_LRD = RHO * tau_ret throughout the experiment. The retentive domain's lab
  tau after each step is solved from the MEASURED cumulative 3He fraction:
        Sigma F3(step end) = LRD_FRAC * F(RHO * tau_ret) + (1 - LRD_FRAC) * F(tau_ret).
  This makes the model independent of the heating schedule and of the lab
  Arrhenius law (S&F 2004 sec. 5.3). Tying lab tau to the Stage 1 line and the
  heating schedule instead fit far worse (reduced chi^2 15-44), because
  step-by-step kinetic or permeation-lag mismatches enter the ratio directly.
* Profiles are carried as sine-series modes C(x) = sum_k A_k sin(k pi x)/x
  (S&F 2004 Eq. 1), exact for piecewise-constant conditions.
* Model R_step/R_bulk = (fraction of total 4He released in the step) /
  (fraction of total 3He released in the step).
* Free parameters: tau_nat and RHO. Fit: weighted least squares against the
  bounding-method central (M) ratios, sigma = half the LB-UB range (floor
  SIGMA_FLOOR). Steps are excluded as in fig_3_4_plot.py (no permeation-lag
  bound, or 3He < 0.1 pccSTP). The 1-sigma interval on tau_nat is profiled
  over RHO, with delta chi^2 = max(1, reduced chi^2).
* Kinetics used to convert tau_nat to time: the Stage 1 Ea, with D0/a^2
  re-referenced to the retentive domain by regressing ln(d tau_ret / dt)
  over the Stage 1 window (cumulative 3He >= the cache threshold) with Ea fixed.
  The time conversion uses the Stage 1 D0/a^2 as published; the
  retentive-domain re-referenced value is reported in the summary JSON only
  (it shifts temperatures by ~1 deg C). Natural diffusion is assumed to follow the same
  (water-saturated) Arrhenius law and domain size as in the lab.
  Isothermal holding time: t = tau_nat / (D/a^2)(T).

Reads:  ../Tables/Win0601bHT_data_and_reduction.xlsx (DistilledBoundingMethod)
        generated/data/stage1_regression_cache.json
Writes: generated/winsor_ratio_tau_fit.{pdf,png}
        generated/winsor_tau_isothermal_tT.{pdf,png}
        generated/data/winsor_tau_inversion_steps.csv
        generated/data/winsor_tau_inversion_summary.json
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (load_stage1_cache, low_signal_HTWin0601b_mask,
                             step_yield_edges_HTWin0601b, draw_step_connectors)
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')
os.makedirs(DATA_OUTDIR, exist_ok=True)

LRD_FRAC = 0.075            # fraction of total 3He in the 4He-free LRD
R_CAL = 1.987               # cal/mol/K (Stage 1 cache is in cal/mol)
SEC_PER_MYR = 3.15576e13
SIGMA_FLOOR = 0.02          # minimum 1-sigma on R/Rbulk
AGE_EARTH_MA = 4567.0
LOG_TAU_GRID = np.arange(-7.0, -0.999, 0.02)
LOG_RHO_GRID = np.arange(0.0, 4.001, 0.05)

C_FIT, C_ALT, C_REF = '#2a78d6', '#eb6834', '#8a8a8a'
INK, MUTED, BOX = '#222222', '#a3a3a3', '#d9d9d9'

# ---------------------------------------------------------------------------
# Sphere solutions, x = r/a in [0, 1]
# ---------------------------------------------------------------------------
K_MODES = 8000              # >> 1/(pi sqrt(smallest tau increment)) here
k = np.arange(1, K_MODES + 1, dtype=float)
lam = (k * np.pi) ** 2
c_uni = 2 * (-1) ** (k + 1) / (k * np.pi)   # modes of a uniform profile (C = 1)
w_int = (-1) ** (k + 1) / (k * np.pi)       # amount in domain / (4 pi a^3) = sum A_k w_k
_k50 = np.arange(1, 51, dtype=float)


def uniform_F(tau):
    """Cumulative fraction released from an initially uniform sphere
    (short-time form, exact to exponentially small terms, below tau = 0.1)."""
    tau = np.atleast_1d(np.asarray(tau, dtype=float))
    short = 6 * np.sqrt(tau / np.pi) - 3 * tau
    long_ = 1 - (6 / np.pi ** 2) * (np.exp(-np.outer(tau, (_k50 * np.pi) ** 2)) / _k50 ** 2).sum(axis=1)
    return np.where(tau < 0.1, short, long_)


def ingrowth_modes(tau_nat):
    """Modes after uniform production (P = 1 per unit tau) with diffusion for
    tau_nat; tau_nat = 0 is quantitative retention, inf is steady state."""
    if np.isinf(tau_nat):
        return c_uni / lam
    if tau_nat == 0:
        return c_uni.copy()
    return c_uni * (-np.expm1(-lam * tau_nat)) / lam


def retained_fraction(tau_nat):
    """4He in the domain / 4He produced (= He age / holding time)."""
    return 3 * np.dot(ingrowth_modes(tau_nat), w_int) / tau_nat


_LT_LOOKUP = np.linspace(-14, 1, 6001)
_F_LOOKUP = uniform_F(10 ** _LT_LOOKUP)


def tau_ret_from_F(F_total, rho):
    """Retentive-domain lab tau reproducing the measured cumulative 3He."""
    F_mix = LRD_FRAC * uniform_F(rho * 10 ** _LT_LOOKUP) + (1 - LRD_FRAC) * _F_LOOKUP
    return 10 ** np.interp(F_total, F_mix, _LT_LOOKUP)


def step_F4(tau_nat, tau_cum):
    """Fraction of the retentive domain's 4He released in each lab step."""
    E = np.exp(-np.outer(np.r_[0.0, tau_cum], lam))
    N = E @ (ingrowth_modes(tau_nat) * w_int)
    return -np.diff(N) / N[0]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
sheet = pd.read_excel(MASTER_XLSX, sheet_name='DistilledBoundingMethod', header=0)
steps = sheet[pd.to_numeric(sheet.iloc[:, 0], errors='coerce').notna()].reset_index(drop=True)
T_C = steps.iloc[:, 0].astype(float).to_numpy()
dt_s = steps['Minutes'].astype(float).to_numpy() * 60.0
R_M = pd.to_numeric(steps['4/3 Hem / 4/3 bulk'], errors='coerce').to_numpy()
R_LB = pd.to_numeric(steps['4/3 HeLB / 4/3 bulk'], errors='coerce').to_numpy()
R_UB = pd.to_numeric(steps['4/3HeUB / 4/3 bulk'], errors='coerce').to_numpy()
F_start, F_end = step_yield_edges_HTWin0601b(MASTER_XLSX)
dF3 = F_end - F_start
low_signal = low_signal_HTWin0601b_mask(MASTER_XLSX)
use = ~low_signal & np.isfinite(R_LB) & np.isfinite(R_UB) & np.isfinite(R_M)
sigma = np.maximum(0.5 * (R_UB - R_LB), SIGMA_FLOOR)
n_fit = int(use.sum())

# ---------------------------------------------------------------------------
# Fit (tau_nat, rho)
# ---------------------------------------------------------------------------
def predict(log_tau, log_rho):
    return step_F4(10 ** log_tau, tau_ret_from_F(F_end, 10 ** log_rho)) / dF3


def chi2(log_tau, log_rho):
    p = predict(log_tau, log_rho)
    return float(np.sum(((p[use] - R_M[use]) / sigma[use]) ** 2))


chi_grid = np.empty((LOG_RHO_GRID.size, LOG_TAU_GRID.size))
for i, lr in enumerate(LOG_RHO_GRID):
    tau_cum = tau_ret_from_F(F_end, 10 ** lr)
    E = np.exp(-np.outer(np.r_[0.0, tau_cum], lam))
    for j, lt in enumerate(LOG_TAU_GRID):
        N = E @ (ingrowth_modes(10 ** lt) * w_int)
        p = -np.diff(N) / N[0] / dF3
        chi_grid[i, j] = np.sum(((p[use] - R_M[use]) / sigma[use]) ** 2)

i0, j0 = np.unravel_index(np.argmin(chi_grid), chi_grid.shape)
opt = minimize(lambda v: chi2(*v), x0=[LOG_TAU_GRID[j0], LOG_RHO_GRID[i0]],
               method='Nelder-Mead', options={'xatol': 1e-4, 'fatol': 1e-6})
lt_best, lr_best = map(float, opt.x)
chi_min = float(opt.fun)
dof = n_fit - 2
chi2_nu = chi_min / dof
dchi = max(1.0, chi2_nu)
prof_tau = chi_grid.min(axis=0)               # profiled over rho
ok_tau = LOG_TAU_GRID[prof_tau <= chi_min + dchi]
lt_lo, lt_hi = float(ok_tau.min()), float(ok_tau.max())
prof_rho = chi_grid.min(axis=1)
ok_rho = LOG_RHO_GRID[prof_rho <= chi_min + dchi]
lr_lo, lr_hi = float(ok_rho.min()), float(ok_rho.max())


def best_rho_for(lt):
    j = int(np.argmin(np.abs(LOG_TAU_GRID - lt)))
    return float(LOG_RHO_GRID[np.argmin(chi_grid[:, j])])


tau_best = 10 ** lt_best
tau_ret_best = tau_ret_from_F(F_end, 10 ** lr_best)
pred_best = predict(lt_best, lr_best)
pred_lo = predict(lt_lo, best_rho_for(lt_lo))
pred_hi = predict(lt_hi, best_rho_for(lt_hi))
pred_no_loss = predict(-12.0, lr_best)        # 4He uniform: LRD dilution only
f_ret = float(retained_fraction(tau_best))
F_LRD_end = float(uniform_F(10 ** lr_best * tau_ret_best[-1])[0])
F_ret_end = float(uniform_F(tau_ret_best[-1])[0])

# ---------------------------------------------------------------------------
# Kinetics for the time conversion
# ---------------------------------------------------------------------------
stage1_cache = load_stage1_cache()
s1 = stage1_cache['M']
Ea = s1['Ea_cal_mol']
win = F_end >= stage1_cache['fractional_yield_threshold']
assert win.sum() == s1['n_points'], 'Stage 1 window does not match the cache'
x_win = 10000.0 / (T_C[win] + 273.0)
dtau_ret = np.diff(np.r_[0.0, tau_ret_best])
lnD_ret = np.log(dtau_ret[win] / dt_s[win])
lnD0a2_ret = float(np.mean(lnD_ret + Ea / (R_CAL * (T_C[win] + 273.0))))
free_slope, free_int = np.polyfit(x_win, lnD_ret, 1)
x_bar = x_win.mean()
sxx_over_n = (s1['intercept_stderr'] / s1['slope_stderr']) ** 2 - x_bar ** 2

KINETICS = {
    'stage1': dict(D0_a2=s1['D0_a2'], color=C_FIT,
                   label=r'Stage 1 $E_a$ and $D_0/a^2$ (as published)'),
}


def D_a2(T_celsius, D0_a2):
    return D0_a2 * np.exp(-Ea / (R_CAL * (np.asarray(T_celsius, dtype=float) + 273.0)))


def sigma_lnD(T_celsius):
    """1-sigma extrapolation uncertainty of the Stage 1 line at T."""
    x = 10000.0 / (np.asarray(T_celsius, dtype=float) + 273.0)
    return s1['slope_stderr'] * np.sqrt(sxx_over_n + (x - x_bar) ** 2)


# ---------------------------------------------------------------------------
# Figure 1: spectrum and best fit
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
for i in np.where(use)[0]:
    ax.fill_between([F_start[i], F_end[i]], R_LB[i], R_UB[i], color=BOX, lw=0, zorder=1)
ax.hlines(R_M[use], F_start[use], F_end[use], color=INK, lw=2.2, zorder=3)
excl = ~use & np.isfinite(R_M) & (R_M < 1.25)
ax.hlines(R_M[excl], F_start[excl], F_end[excl], color=MUTED, lw=1.6,
          linestyles=(0, (2, 1.5)), zorder=2)
for i in range(len(F_start)):
    ax.fill_between([F_start[i], F_end[i]], min(pred_lo[i], pred_hi[i]),
                    max(pred_lo[i], pred_hi[i]), color=C_FIT, alpha=0.18, lw=0, zorder=2)
ax.hlines(pred_best, F_start, F_end, color=C_FIT, lw=2.0, zorder=4)
draw_step_connectors(ax, F_start, F_end, pred_best, color=C_FIT, zorder=4)
ax.hlines(pred_no_loss, F_start, F_end, color=C_REF, lw=1.3, linestyles='--', zorder=2)
ax.set_xlim(0, 0.16)
ax.set_ylim(0, 1.2)
ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
ax.set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
ax.set_title(r'HT-Win-06-01b: inversion for natural $\tau$')
handles = [Line2D([], [], color=INK, lw=2.2, label='Data (M), LB–UB box'),
           Line2D([], [], color=MUTED, lw=1.6, ls=(0, (2, 1.5)), label='Excluded steps'),
           Line2D([], [], color=C_FIT, lw=2.0,
                  label=rf'Best fit, $\tau_\mathrm{{nat}}$ = {tau_best:.1e} ($\pm1\sigma$)'),
           Line2D([], [], color=C_REF, lw=1.3, ls='--', label='No natural loss (LRD dilution only)')]
ax.legend(handles=handles, loc='lower right', fontsize=9.5)
ax.text(0.003, 1.15, rf'LRD = {LRD_FRAC:.1%} of $^3$He; $\rho$ = {10 ** lr_best:.0f}; '
                     rf'$\chi^2_\nu$ = {chi2_nu:.2f}', fontsize=10, va='top', color='#444444')
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUTDIR, f'winsor_ratio_tau_fit.{ext}'), dpi=200)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: isothermal holding time needed to reach tau_nat
# ---------------------------------------------------------------------------
T_plot = np.linspace(0, 120, 481)
sig_lntau = 0.5 * np.log(10) * (lt_hi - lt_lo)
fig, ax = plt.subplots()
summary_T = {}
for key, kin in KINETICS.items():
    ln_t = np.log(tau_best) - np.log(D_a2(T_plot, kin['D0_a2'])) - np.log(SEC_PER_MYR)
    sig = np.sqrt(sig_lntau ** 2 + sigma_lnD(T_plot) ** 2)
    ax.fill_between(T_plot, np.exp(ln_t - sig), np.exp(ln_t + sig), color=kin['color'], alpha=0.15, lw=0)
    ax.plot(T_plot, np.exp(ln_t), color=kin['color'], lw=2.0, label=kin['label'])
    summary_T[key] = {f'T_C_for_t_{name}': float(np.interp(np.log(val), ln_t[::-1], T_plot[::-1]))
                      for name, val in [('1Ma', 1), ('10Ma', 10), ('100Ma', 100), ('AgeEarth', AGE_EARTH_MA)]}
ax.axhline(AGE_EARTH_MA, color=MUTED, lw=1, ls=':')
ax.text(2, AGE_EARTH_MA * 1.3, 'Age of Earth', ha='left', va='bottom', color='#555555', fontsize=10)
ax.set_yscale('log')
ax.set_xlim(0, 120)
ax.set_ylim(1e-2, 1e6)
ax.set_xlabel('Isothermal holding temperature (°C)')
ax.set_ylabel('Holding time (Ma)')
ax.set_title(rf'Time to reach $\tau_\mathrm{{nat}}$ = {tau_best:.1e} (He age $\approx$ {f_ret:.2f} $t$)', fontsize=13)
ax.legend(loc='upper right', fontsize=10)
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(OUTDIR, f'winsor_tau_isothermal_tT.{ext}'), dpi=200)
plt.close(fig)

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
pd.DataFrame({'Temp_C': T_C, 'Minutes': dt_s / 60, 'F_start': F_start, 'F_end': F_end,
              'R_M': R_M, 'R_LB': R_LB, 'R_UB': R_UB, 'sigma': sigma, 'used_in_fit': use,
              'tau_ret_lab_end': tau_ret_best, 'pred_best': pred_best,
              'pred_lo': pred_lo, 'pred_hi': pred_hi, 'pred_no_natural_loss': pred_no_loss}
             ).to_csv(os.path.join(DATA_OUTDIR, 'winsor_tau_inversion_steps.csv'), index=False)

summary = dict(
    LRD_frac=LRD_FRAC, sigma_floor=SIGMA_FLOOR, n_fit=n_fit, dof=dof,
    log10_tau_nat=lt_best, log10_tau_nat_1sig=[lt_lo, lt_hi],
    log10_rho=lr_best, log10_rho_1sig=[lr_lo, lr_hi],
    chi2=chi_min, chi2_nu=chi2_nu,
    chi2_steady_state_rhobest=chi2(np.inf, lr_best),
    retained_fraction=f_ret, deficit_fraction=1 - f_ret,
    F_LRD_degassed_at_end=F_LRD_end, F_ret_degassed_at_end=F_ret_end,
    tau_ret_lab_end=float(tau_ret_best[-1]),
    Ea_cal_mol=Ea, D0_a2_stage1=s1['D0_a2'], D0_a2_retentive=float(np.exp(lnD0a2_ret)),
    retentive_free_fit_Ea_cal_mol=float(-free_slope * 10000 * R_CAL),
    **{f'{k_}_{kk}': v for k_, d in summary_T.items() for kk, v in d.items()},
)
with open(os.path.join(DATA_OUTDIR, 'winsor_tau_inversion_summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=1))
