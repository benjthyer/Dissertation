"""
Multi-domain (MDD) extension of winsor_he43_model.py for HT-Win-06-01b.

Domains (all spheres sharing the Stage 1 activation energy and D0):
  HRD     -- holds f_H >= 92.5% of the 3He; D/a^2 = Stage 1 regression as published.
  LRD_j   -- j = 1..N, fraction f_j of the 3He (sum f_j <= 7.5%, delta plot),
             radius r_j * a_HRD, so (D/a^2)_j = (D/a^2)_HRD / r_j^2.
Only the LRD is multi-domain; the HRD stays exactly on the Stage 1 line.

3He fit: apparent ln(D/a^2) of the model's cumulative release, computed with
the same single-sphere inversion as the data (Fechtig & Kalbitzer 1966), is
compared step by step with the apparent ln(D/a^2) of the measured release
(i.e. the Arrhenius / delta plot is fitted directly, as in Lovera et al. 1991
and Farley & Flowers 2012). Uncertainties: half the bounding-method LB-UB
range in ln(D/a^2) (floor SIGMA_LN_FLOOR); steps without bounds get
SIGMA_LN_NOBOUND. objective='cumulative' instead reproduces the relative
cumulative-F misfit used by winsor_he43_model.fit_lrd_from_3he.

4He: every domain carries its own radiogenic 4He from the same thermal
history; the HRD's laboratory tau is solved from the measured cumulative 3He
through the full mixture, so the spectrum prediction is schedule-independent.
"""
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

import winsor_he43_model as M

F_LRD_MAX = M.F_LRD_MAX          # 0.075
SIGMA_LN_FLOOR = 0.05
SIGMA_LN_NOBOUND = 0.25
LOG10_R_BOUNDS = (-6.0, -0.02)   # LRD radius relative to the HRD


# ---------------------------------------------------------------------------
# Inversion of cumulative release to apparent ln(D/a^2) (vectorized)
# ---------------------------------------------------------------------------
def apparent_lnD(F_cum, t_s):
    """Fechtig & Kalbitzer (1966) single-sphere inversion, step by step
    (same branches as thermochr_utils.InvertFrequencyFactor)."""
    F = np.asarray(F_cum, dtype=float)
    Fp = np.r_[0.0, F[:-1]]
    small = (F ** 2 - Fp ** 2) * np.pi / (36 * t_s)
    sF, sFp = np.sqrt(np.clip(1 - np.pi * F / 3, 0, None)), np.sqrt(np.clip(1 - np.pi * Fp / 3, 0, None))
    mid = (1 / (np.pi ** 2 * t_s)) * (-(np.pi ** 2 / 3) * (F - Fp) - 2 * np.pi * (sF - sFp))
    high = np.log(np.clip(1 - Fp, 1e-300, None) / np.clip(1 - F, 1e-300, None)) / (np.pi ** 2 * t_s)
    D = np.where(F <= 0.1, small, np.where(F < 0.9, mid, high))
    return np.log(np.clip(D, 1e-300, None))


# ---------------------------------------------------------------------------
# Domain bookkeeping
# ---------------------------------------------------------------------------
def unpack(theta, n):
    """theta = [logit f_tot, (n-1) weight logits, n log10 r]  ->  (f_j, r_j), sorted by r."""
    f_tot = F_LRD_MAX / (1 + np.exp(-theta[0]))
    w = np.exp(np.r_[0.0, theta[1:n]])
    f = f_tot * w / w.sum()
    r = 10 ** np.asarray(theta[n:2 * n])
    order = np.argsort(r)
    return f[order], r[order]


def mixture_F(tau_hrd, f, r):
    """Cumulative 3He fraction released when the HRD has reached tau_hrd."""
    tau_hrd = np.asarray(tau_hrd, dtype=float)
    out = (1 - f.sum()) * M.uniform_F(tau_hrd)
    for fj, rj in zip(f, r):
        out = out + fj * M.uniform_F(tau_hrd / rj ** 2)
    return out


def hrd_lab_tau(F_total, f, r):
    """HRD lab tau that reproduces the measured cumulative 3He fractions."""
    lt = np.linspace(-14, 3, 8501)
    return 10 ** np.interp(F_total, mixture_F(10 ** lt, f, r), lt)


# ---------------------------------------------------------------------------
# 3He fit
# ---------------------------------------------------------------------------
def he3_data(spec):
    """Apparent ln(D/a^2) of the measured release and its uncertainty."""
    sheet = pd.read_excel(M.MASTER_XLSX, sheet_name='DistilledBoundingMethod', header=0)
    sheet = sheet[pd.to_numeric(sheet.iloc[:, 0], errors='coerce').notna()].reset_index(drop=True)
    lb = pd.to_numeric(sheet['3He ln(d/a^2)LB'], errors='coerce').to_numpy()
    ub = pd.to_numeric(sheet['3He ln(d/a^2)UB'], errors='coerce').to_numpy()
    t_s = spec['minutes'] * 60.0
    sig = 0.5 * (ub - lb)
    sig = np.where(np.isfinite(sig), np.maximum(sig, SIGMA_LN_FLOOR), SIGMA_LN_NOBOUND)
    return dict(t_s=t_s, lnD=apparent_lnD(spec['F_end'], t_s), sigma=sig,
                tau_hrd=M.hrd_lab_tau_from_schedule(spec), F_meas=spec['F_end'],
                lnD_stage1=np.log(M.D0_A2) - M.EA / (M.R_CAL * (spec['T_C'] + 273.0)))


def he3_residuals(theta, n, d, objective='arrhenius'):
    f, r = unpack(theta, n)
    F_mod = mixture_F(d['tau_hrd'], f, r)
    if objective == 'cumulative':
        return (F_mod - d['F_meas']) / d['F_meas']
    return (apparent_lnD(F_mod, d['t_s']) - d['lnD']) / d['sigma']


def pack(f, r):
    """Inverse of unpack: (f_j, r_j) -> theta (first domain is the weight reference)."""
    f, r = np.asarray(f, dtype=float), np.asarray(r, dtype=float)
    f_tot = min(f.sum(), F_LRD_MAX * (1 - 1e-9))
    return np.r_[np.log(f_tot / (F_LRD_MAX - f_tot)), np.log(f[1:] / f[0]), np.log10(r)]


def fit_lrd_mdd(spec, n, objective='arrhenius', n_starts=60, seed=0, init=None,
                n_random_with_init=8):
    """Fit n LRD domains to the 3He release. Returns a dict with f, r,
    chi2, dof, aic, bic and the model cumulative release.

    init=(f_prev, r_prev) from an (n-1)-domain fit warm-starts the search
    (Farley & Flowers-style: add one domain at a time): the previous
    solution plus a new small domain trialled at sizes spanning the allowed
    range, plus n_random_with_init random starts. Because the new domain can
    take a negligible fraction, the fit cannot get worse than n-1 domains."""
    d = he3_data(spec)
    rng = np.random.default_rng(seed)
    lo = np.r_[-12.0, np.full(n - 1, -12.0), np.full(n, LOG10_R_BOUNDS[0])]
    hi = np.r_[12.0, np.full(n - 1, 12.0), np.full(n, LOG10_R_BOUNDS[1])]
    starts = []
    if init is not None and len(init[0]) == n - 1:
        f0, r0 = np.asarray(init[0], float), np.asarray(init[1], float)
        for lr_new in np.linspace(LOG10_R_BOUNDS[0] + 0.5, LOG10_R_BOUNDS[1] - 0.05, 12):
            for share in (0.05, 0.3):
                f_new = share * f0.sum()
                starts.append(pack(np.r_[f0 * (1 - share), f_new], np.r_[r0, 10 ** lr_new]))
        n_rand = n_random_with_init
    else:
        n_rand = n_starts
    for _ in range(n_rand):
        starts.append(np.r_[rng.uniform(-3, 4), rng.uniform(-3, 3, n - 1),
                            np.sort(rng.uniform(-4.5, -0.2, n))])
    best = None
    for x0 in starts:
        x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)
        try:
            res = least_squares(he3_residuals, x0, bounds=(lo, hi), args=(n, d, objective),
                                method='trf', x_scale='jac', max_nfev=4000)
        except Exception:
            continue
        if best is None or res.cost < best.cost:
            best = res
    f, r = unpack(best.x, n)
    resid = he3_residuals(best.x, n, d, objective)
    chi2 = float(np.sum(resid ** 2))
    k, n_obs = 2 * n, resid.size
    F_mod = mixture_F(d['tau_hrd'], f, r)
    return dict(n_lrd=n, objective=objective, f=f, r=r, f_total=float(f.sum()),
                chi2=chi2, dof=n_obs - k, chi2_nu=chi2 / (n_obs - k),
                bic=chi2 + k * np.log(n_obs), aic=chi2 + 2 * k,
                model_F=F_mod, model_lnD=apparent_lnD(F_mod, d['t_s']), theta=best.x)


# ---------------------------------------------------------------------------
# 4He: natural profiles for all domains at once, and the lab spectrum
# ---------------------------------------------------------------------------
def path_modes_multi(t_nodes_ma, T_nodes_c, size_ratios, dt_myr=2.0, hrd_scale=1.0):
    """Present-day 4He modes (production 1 per Myr) for domains of relative
    radius size_ratios (HRD = 1), all with the same thermal history.
    hrd_scale multiplies the HRD's Stage 1 D0/a^2 (1 = as published)."""
    size_ratios = np.atleast_1d(np.asarray(size_ratios, dtype=float))
    t0 = float(np.max(t_nodes_ma))
    edges = np.arange(t0, -1e-9, -dt_myr)
    if edges[-1] > 0:
        edges = np.r_[edges, 0.0]
    mids = 0.5 * (edges[:-1] + edges[1:])
    steps = edges[:-1] - edges[1:]
    D = hrd_scale * M.D_a2_per_myr(M.path_T(t_nodes_ma, T_nodes_c, mids))
    keep = np.r_[True, ~np.isclose(D[1:], D[:-1], rtol=1e-12, atol=0)]
    group = np.cumsum(keep) - 1
    D, steps = D[keep], np.bincount(group, weights=steps)
    scale = (1.0 / size_ratios ** 2)[:, None]
    A = np.zeros((size_ratios.size, M.K_MODES))
    for Dm, h in zip(D, steps):
        x = M.LAM[None, :] * (Dm * h) * scale
        A = A * np.exp(-x) + M.C_UNI[None, :] * h * (-np.expm1(-x)) / np.maximum(x, 1e-300)
    return A


class SpectrumModel:
    """Lab response of the HRD + LRD_j assemblage for fixed (f, r)."""
    def __init__(self, spec, f, r, hrd_scale=1.0):
        self.spec = spec
        self.hrd_scale = hrd_scale
        self.fracs = np.r_[1 - np.sum(f), f]
        self.ratios = np.r_[1.0, r]
        tau_h = hrd_lab_tau(spec['F_end'], np.asarray(f), np.asarray(r))
        self.E = [np.exp(-np.outer(np.r_[0.0, tau_h / q ** 2], M.LAM)) for q in self.ratios]

    def predict(self, A):
        N = sum(fj * (E @ (Aj * M.W_INT)) for fj, E, Aj in zip(self.fracs, self.E, A))
        return (-np.diff(N) / N[0]) / self.spec['dF3']

    def bulk_age(self, A):
        return float(sum(fj * M.domain_age(Aj) for fj, Aj in zip(self.fracs, A)))

    def evaluate(self, t_nodes, T_nodes, dt_myr=2.0):
        A = path_modes_multi(t_nodes, T_nodes, self.ratios, dt_myr, self.hrd_scale)
        p = self.predict(A)
        return M.chi2(self.spec, p), self.bulk_age(A), p


# ===========================================================================
# Farley & Flowers (2012, supplement A2)-style fit: domain fractions AND sizes
# free within an LRD assemblage of FIXED total fraction, fitted to the 3He
# fractional and cumulative yields only (equally weighted).
# ===========================================================================
F_LRD_FIXED = 0.075              # total LRD fraction (HRD = 92.5%)
LOG10_S_BOUNDS = (-2.0, 1.0)     # HRD D0/a^2 relative to Stage 1 (hrd_mode='free')
LOG10_R_BOUNDS_FF = (-6.0, 0.0)  # LRD radius relative to the HRD; r = 1 is HRD-sized


def unpack_ff(theta, n, f_total=F_LRD_FIXED, hrd_mode='stage1'):
    """theta = [(n-1) weight logits, n log10 r, (log10 s if hrd_mode == 'free')]
    -> (f_j, r_j sorted by r, s)."""
    w = np.exp(np.r_[0.0, theta[:n - 1]])
    f = f_total * w / w.sum()
    r = 10 ** np.asarray(theta[n - 1:2 * n - 1])
    s = 10 ** theta[2 * n - 1] if hrd_mode == 'free' else 1.0
    order = np.argsort(r)
    return f[order], r[order], float(s)


def pack_ff(f, r, s=1.0, hrd_mode='stage1'):
    f, r = np.asarray(f, dtype=float), np.asarray(r, dtype=float)
    th = np.r_[np.log(f[1:] / f[0]), np.log10(r)]
    return np.r_[th, np.log10(s)] if hrd_mode == 'free' else th


def yield_residuals(theta, n, d, f_total=F_LRD_FIXED, hrd_mode='stage1', weighting='absolute'):
    """Residuals of fractional (per-step) and cumulative 3He yields, equally
    weighted (Farley & Flowers 2012, A2). weighting='absolute' uses the yields
    as fractions of total 3He; 'relative' divides each by the observed value."""
    f, r, s = unpack_ff(theta, n, f_total, hrd_mode)
    F_mod = mixture_F(s * d['tau_hrd'], f, r)
    dF_mod = np.diff(np.r_[0.0, F_mod])
    dF_obs = np.diff(np.r_[0.0, d['F_meas']])
    if weighting == 'relative':
        return np.r_[(dF_mod - dF_obs) / dF_obs, (F_mod - d['F_meas']) / d['F_meas']]
    return np.r_[dF_mod - dF_obs, F_mod - d['F_meas']]


def fit_lrd_ff(spec, n, f_total=F_LRD_FIXED, hrd_mode='stage1', weighting='absolute',
               init=None, n_starts=40, n_random_with_init=8, seed=0):
    """Fit n LRD domains (free fractions and sizes, total f_total) to the 3He
    fractional + cumulative yields. hrd_mode='stage1' pins the HRD to the
    Stage 1 line; 'free' lets the HRD's D0/a^2 scale by s (same Ea).
    Returns f, r, s, misfit statistics and the model release."""
    d = he3_data(spec)
    rng = np.random.default_rng(seed)
    k = 2 * n - 1 + (1 if hrd_mode == 'free' else 0)
    lo = np.r_[np.full(n - 1, -12.0), np.full(n, LOG10_R_BOUNDS_FF[0])]
    hi = np.r_[np.full(n - 1, 12.0), np.full(n, LOG10_R_BOUNDS_FF[1])]
    if hrd_mode == 'free':
        lo, hi = np.r_[lo, LOG10_S_BOUNDS[0]], np.r_[hi, LOG10_S_BOUNDS[1]]
    starts = []
    if init is not None and len(init[0]) == n - 1:
        f0, r0, s0 = np.asarray(init[0], float), np.asarray(init[1], float), init[2]
        for lr_new in np.linspace(LOG10_R_BOUNDS_FF[0] + 0.5, LOG10_R_BOUNDS_FF[1] - 0.05, 12):
            for share in (0.05, 0.3):
                starts.append(pack_ff(np.r_[f0 * (1 - share), share * f0.sum()],
                                      np.r_[r0, 10 ** lr_new], s0, hrd_mode))
        n_rand = n_random_with_init
    else:
        n_rand = n_starts
    for _ in range(n_rand):
        x0 = np.r_[rng.uniform(-3, 3, n - 1), np.sort(rng.uniform(-4.5, -0.05, n))]
        if hrd_mode == 'free':
            x0 = np.r_[x0, rng.uniform(-0.5, 0.2)]
        starts.append(x0)
    best = None
    for x0 in starts:
        x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)
        try:
            res = least_squares(yield_residuals, x0, bounds=(lo, hi),
                                args=(n, d, f_total, hrd_mode, weighting),
                                method='trf', x_scale='jac', max_nfev=4000)
        except Exception:
            continue
        if best is None or res.cost < best.cost:
            best = res
    f, r, s = unpack_ff(best.x, n, f_total, hrd_mode)
    resid = yield_residuals(best.x, n, d, f_total, hrd_mode, weighting)
    ss = float(np.sum(resid ** 2))
    n_obs = resid.size
    F_mod = mixture_F(s * d['tau_hrd'], f, r)
    lnD_mod = apparent_lnD(F_mod, d['t_s'])
    chi2_arr = float(np.sum(((lnD_mod - d['lnD']) / d['sigma']) ** 2))
    return dict(n_lrd=n, f=f, r=r, hrd_scale=s, f_total=float(f.sum()), hrd_mode=hrd_mode,
                weighting=weighting, sum_sq=ss, n_obs=n_obs, k=k,
                rms_yield=float(np.sqrt(ss / n_obs)),
                bic=n_obs * np.log(ss / n_obs) + k * np.log(n_obs),     # Gaussian, unknown variance
                aic=n_obs * np.log(ss / n_obs) + 2 * k,
                arrhenius_chi2_nu=chi2_arr / (d['lnD'].size - k),
                model_F=F_mod, model_lnD=lnD_mod)
