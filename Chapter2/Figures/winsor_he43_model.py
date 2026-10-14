"""
Shared two-domain forward model for the HT-Win-06-01b bulk-normalized
4He/3He spectrum (Shuster & Farley 2004 ratio-evolution framework).

Domains (same activation energy and D0, spherical):
  HRD -- high-retentivity domain, radius a, holds (1 - f_lrd) of the 3He.
  LRD -- low-retentivity domain, radius r * a (size_ratio r < 1), holds f_lrd
         of the 3He. D/a^2 of the LRD = (D/a^2 of the HRD) / r^2 at every T.
By default the LRD holds no radiogenic 4He (lrd_4he=False); pass its own
natural modes to treat it as an ordinary small domain of the same goethite.

Natural kinetics for the HRD: the Stage 1 regression (M) exactly as published
in the Stage 1 cache (D0/a^2, Ea), extrapolated to natural temperatures.

Laboratory: the HRD's lab tau after each step is solved from the MEASURED
cumulative 3He fraction,
    Sigma F3 = f_lrd * F(tau / r^2) + (1 - f_lrd) * F(tau),
so the prediction does not depend on the lab heating schedule.

Concentration profiles are sine-series modes C(x) = sum_k A_k sin(k pi x)/x
(S&F 2004 Eq. 1), exact for piecewise-constant temperature.
"""
import os
import numpy as np
import pandas as pd

from thermochr_utils import (load_stage1_cache, low_signal_HTWin0601b_mask,
                             step_yield_edges_HTWin0601b)

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')

R_CAL = 1.987               # cal/mol/K
SEC_PER_MYR = 3.15576e13
SIGMA_FLOOR = 0.02          # minimum 1-sigma on R_step/R_bulk
T_SURF = 20.0               # deg C

K_MODES = 8000
_k = np.arange(1, K_MODES + 1, dtype=float)
LAM = (_k * np.pi) ** 2
C_UNI = 2 * (-1) ** (_k + 1) / (_k * np.pi)   # modes of a uniform profile (C = 1)
W_INT = (-1) ** (_k + 1) / (_k * np.pi)       # amount / (4 pi a^3) = sum A_k W_k
_K50 = np.arange(1, 51, dtype=float)


# ---------------------------------------------------------------------------
# Sphere basics
# ---------------------------------------------------------------------------
def uniform_F(tau):
    """Cumulative fraction released from an initially uniform sphere."""
    tau = np.atleast_1d(np.asarray(tau, dtype=float))
    short = 6 * np.sqrt(tau / np.pi) - 3 * tau
    long_ = 1 - (6 / np.pi ** 2) * (np.exp(-np.outer(np.minimum(tau, 50.0), (_K50 * np.pi) ** 2))
                                    / _K50 ** 2).sum(axis=1)
    return np.where(tau < 0.1, short, long_)


_LT = np.linspace(-14, 3, 8501)
_F_LT = uniform_F(10 ** _LT)


def hrd_lab_tau(F_total, f_lrd, size_ratio):
    """HRD lab tau reproducing the measured cumulative 3He fractions."""
    F_mix = f_lrd * uniform_F(10 ** _LT / size_ratio ** 2) + (1 - f_lrd) * _F_LT
    return 10 ** np.interp(F_total, F_mix, _LT)


def isothermal_modes(tau_nat):
    """Constant production (1 per unit tau) and diffusion for tau_nat."""
    if np.isinf(tau_nat):
        return C_UNI / LAM
    return C_UNI * (-np.expm1(-LAM * tau_nat)) / LAM


def domain_age(A):
    """4He retained per unit volume / production rate (same time units as A)."""
    return 3.0 * float(A @ W_INT)


# ---------------------------------------------------------------------------
# Kinetics (Stage 1 as published) and thermal paths
# ---------------------------------------------------------------------------
_stage1_cache = load_stage1_cache(os.path.join(DATA_OUTDIR, 'stage1_regression_cache.json'))
STAGE1 = _stage1_cache['M']
EA = STAGE1['Ea_cal_mol']
D0_A2 = STAGE1['D0_a2']


def _kinetic_sigma_terms(spec):
    """x_bar and Sxx/n of the Stage 1 regression, for its extrapolation error."""
    win = spec['F_end'] >= _stage1_cache['fractional_yield_threshold']
    assert win.sum() == STAGE1['n_points'], 'Stage 1 window does not match the cache'
    x_bar = (10000.0 / (spec['T_C'][win] + 273.0)).mean()
    return x_bar, (STAGE1['intercept_stderr'] / STAGE1['slope_stderr']) ** 2 - x_bar ** 2


def D_a2_per_myr(T_celsius, kin_sigma=0.0, spec=None):
    """HRD D/a^2 in 1/Myr; kin_sigma shifts ln(D/a^2) by that many 1-sigma
    extrapolation errors of the Stage 1 line (needs spec)."""
    T_celsius = np.asarray(T_celsius, dtype=float)
    lnD = np.log(D0_A2) - EA / (R_CAL * (T_celsius + 273.0))
    if kin_sigma:
        x_bar, sxx_n = _kinetic_sigma_terms(spec)
        x = 10000.0 / (T_celsius + 273.0)
        lnD = lnD + kin_sigma * STAGE1['slope_stderr'] * np.sqrt(sxx_n + (x - x_bar) ** 2)
    return np.exp(lnD) * SEC_PER_MYR


def path_T(t_nodes_ma, T_nodes_c, t_ma):
    """Piecewise-linear temperature path through (t, T) nodes (t in Ma)."""
    order = np.argsort(t_nodes_ma)
    return np.interp(t_ma, np.asarray(t_nodes_ma, float)[order], np.asarray(T_nodes_c, float)[order])


def path_modes(t_nodes_ma, T_nodes_c, dt_myr=0.5, size_ratio=1.0, kin_sigma=0.0, spec=None):
    """Present-day 4He modes (production 1 per Myr) for a domain of relative
    size `size_ratio` that formed at the oldest node."""
    t0 = float(np.max(t_nodes_ma))
    edges = np.arange(t0, -1e-9, -dt_myr)
    if edges[-1] > 0:
        edges = np.r_[edges, 0.0]
    mids = 0.5 * (edges[:-1] + edges[1:])
    steps = edges[:-1] - edges[1:]
    D = D_a2_per_myr(path_T(t_nodes_ma, T_nodes_c, mids), kin_sigma, spec) / size_ratio ** 2
    # merge consecutive steps at the same temperature (exact for constant D)
    keep = np.r_[True, ~np.isclose(D[1:], D[:-1], rtol=1e-12, atol=0)]
    group = np.cumsum(keep) - 1
    D, steps = D[keep], np.bincount(group, weights=steps)
    A = np.zeros(K_MODES)
    for Dm, h in zip(D, steps):
        x = LAM * Dm * h
        A = A * np.exp(-x) + C_UNI * h * (-np.expm1(-x)) / np.maximum(x, 1e-300)
    return A


def bulk_age(A_hrd, f_lrd, A_lrd=None):
    """Bulk He age, assuming U and Th are distributed by volume like the 3He."""
    age_lrd = 0.0 if A_lrd is None else domain_age(A_lrd)
    return (1 - f_lrd) * domain_age(A_hrd) + f_lrd * age_lrd


# ---------------------------------------------------------------------------
# Data and spectrum prediction
# ---------------------------------------------------------------------------
def load_spectrum():
    sheet = pd.read_excel(MASTER_XLSX, sheet_name='DistilledBoundingMethod', header=0)
    rows = sheet[pd.to_numeric(sheet.iloc[:, 0], errors='coerce').notna()].reset_index(drop=True)
    R_M = pd.to_numeric(rows['4/3 Hem / 4/3 bulk'], errors='coerce').to_numpy()
    R_LB = pd.to_numeric(rows['4/3 HeLB / 4/3 bulk'], errors='coerce').to_numpy()
    R_UB = pd.to_numeric(rows['4/3HeUB / 4/3 bulk'], errors='coerce').to_numpy()
    F_start, F_end = step_yield_edges_HTWin0601b(MASTER_XLSX)
    low = low_signal_HTWin0601b_mask(MASTER_XLSX)
    use = ~low & np.isfinite(R_LB) & np.isfinite(R_UB) & np.isfinite(R_M)
    return dict(T_C=rows.iloc[:, 0].astype(float).to_numpy(),
                minutes=rows['Minutes'].astype(float).to_numpy(),
                F_start=F_start, F_end=F_end, dF3=F_end - F_start,
                R_M=R_M, R_LB=R_LB, R_UB=R_UB,
                sigma=np.maximum(0.5 * (R_UB - R_LB), SIGMA_FLOOR),
                use=use, n_fit=int(use.sum()))


def predict_spectrum(spec, A_hrd, f_lrd, size_ratio, A_lrd=None):
    """Model R_step/R_bulk for every step."""
    tau_h = hrd_lab_tau(spec['F_end'], f_lrd, size_ratio)
    E_h = np.exp(-np.outer(np.r_[0.0, tau_h], LAM))
    N = (1 - f_lrd) * (E_h @ (A_hrd * W_INT))
    if A_lrd is not None:
        E_l = np.exp(-np.outer(np.r_[0.0, tau_h / size_ratio ** 2], LAM))
        N = N + f_lrd * (E_l @ (A_lrd * W_INT))
    return (-np.diff(N) / N[0]) / spec['dF3']


def chi2(spec, pred):
    u = spec['use']
    return float(np.sum(((pred[u] - spec['R_M'][u]) / spec['sigma'][u]) ** 2))


# ---------------------------------------------------------------------------
# LRD from the 3He release alone
# ---------------------------------------------------------------------------
F_LRD_MAX = 0.075           # delta plot: LRD holds <= 7.5% of the 3He


def hrd_lab_tau_from_schedule(spec):
    """HRD lab tau after each step from the Stage 1 line and the heating schedule."""
    D = D0_A2 * np.exp(-EA / (R_CAL * (spec['T_C'] + 273.0)))
    return np.cumsum(D * spec['minutes'] * 60.0)


def fit_lrd_from_3he(spec, f_max=F_LRD_MAX):
    """Fit the LRD fraction f and size ratio r = a_LRD/a_HRD (same Ea and D0)
    to the measured cumulative 3He release, with the HRD on the Stage 1 line.
    Minimizes the relative misfit in cumulative 3He fraction over all steps.
    Returns dict(f_lrd, size_ratio, rms_rel_misfit, rms_rel_misfit_single_domain)."""
    from scipy.optimize import minimize
    tau = hrd_lab_tau_from_schedule(spec)
    F_meas = spec['F_end']

    def model(f, r):
        return f * uniform_F(tau / r ** 2) + (1 - f) * uniform_F(tau)

    def cost(v):
        f, r = f_max / (1 + np.exp(-v[0])), 10 ** v[1]
        if r >= 1:
            return 1e9
        return float(np.sum(((model(f, r) - F_meas) / F_meas) ** 2))

    best = min((minimize(cost, x0, method='Nelder-Mead', options={'xatol': 1e-6, 'fatol': 1e-10})
                for x0 in ([0, -1], [2, -0.5], [-2, -2], [1, -1.5], [0, -2.5])),
               key=lambda o: o.fun)
    f, r = f_max / (1 + np.exp(-best.x[0])), 10 ** best.x[1]
    single = float(np.sum(((uniform_F(tau) - F_meas) / F_meas) ** 2))
    return dict(f_lrd=float(f), size_ratio=float(r),
                rms_rel_misfit=float(np.sqrt(best.fun / F_meas.size)),
                rms_rel_misfit_single_domain=float(np.sqrt(single / F_meas.size)),
                model_F=model(f, r))
