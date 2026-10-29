"""
Fully free multi-domain (MDD) model for HT-Win-06-01b.

There is no HRD/LRD distinction: the sample is N spherical domains sharing the
Stage 1 activation energy and frequency factor. Domain j holds a fraction f_j
of the 3He (sum f_j = 1) and has radius r_j * a0, where a0 is the radius of a
reference domain whose D/a0^2 is the Stage 1 regression of the chapter (as
published):

    (D/a^2)_j = (D0/a0^2) exp(-Ea/RT) / r_j^2 .

Step 1 (3He only): f_j and r_j are fitted to the per-step (fractional) and
cumulative 3He yields of the water-saturated experiment, equally weighted
(Farley & Flowers 2012, supplement A2). The six low-signal steps (< 0.1 pccSTP
3He; thermochr_utils.low_signal_HTWin0601b_mask) are excluded from the misfit
and from the Arrhenius chi^2; their gas still counts toward the cumulative
yields and their durations toward the laboratory schedule. Because only ~15% of the 3He was
released before fusion, domains that barely degas in the experiment are
constrained only through their summed fraction; their individual sizes are
bounded by LOG10_R_BOUNDS.

Step 2 (4He/3He): with the domains fixed, every domain grows and loses 4He on
the same thermal history; the reference domain's laboratory tau is solved
from the measured cumulative 3He through the full mixture (schedule
independent), and the spectrum and bulk age are predicted.
"""
import numpy as np
from scipy.optimize import least_squares

import winsor_he43_model as M
import winsor_he43_mdd as D
from thermochr_utils import low_signal_HTWin0601b_mask

LOG10_R_BOUNDS = (-6.0, 3.0)      # r_j = a_j / a0
_LT = np.linspace(-16, 8, 12001)  # log10 tau grid for the lab inversion


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
def unpack(theta, n):
    """theta = [(n-1) fraction logits, n log10 r] -> (f, r), sorted by r."""
    w = np.exp(np.r_[0.0, theta[:n - 1]])
    f = w / w.sum()
    r = 10 ** np.asarray(theta[n - 1:2 * n - 1], dtype=float)
    o = np.argsort(r)
    return f[o], r[o]


def pack(f, r):
    f, r = np.asarray(f, dtype=float), np.asarray(r, dtype=float)
    f = np.clip(f, 1e-12, None)
    return np.r_[np.log(f[1:] / f[0]), np.log10(r)]


def mixture_F(tau0, f, r):
    """Cumulative 3He fraction when the reference domain has reached tau0."""
    tau0 = np.asarray(tau0, dtype=float)
    out = np.zeros_like(tau0)
    for fj, rj in zip(f, r):
        out = out + fj * M.uniform_F(tau0 / rj ** 2)
    return out


def ref_lab_tau(F_total, f, r):
    """Reference-domain lab tau reproducing measured cumulative 3He fractions."""
    Fg = np.maximum.accumulate(mixture_F(10 ** _LT, f, r))
    Fg = Fg + np.arange(Fg.size) * 1e-15          # strictly increasing for interp
    return 10 ** np.interp(F_total, Fg, _LT)


# ---------------------------------------------------------------------------
# Step 1: 3He fit
# ---------------------------------------------------------------------------
def he3_data(spec):
    """3He data with the mask of steps used in the fit (low-signal steps excluded)."""
    d = D.he3_data(spec)
    d['keep'] = ~low_signal_HTWin0601b_mask(M.MASTER_XLSX)
    return d


def residuals(theta, n, d, weighting='absolute'):
    f, r = unpack(theta, n)
    F_mod = mixture_F(d['tau_hrd'], f, r)          # tau_hrd = Stage 1 reference tau
    dF_mod = np.diff(np.r_[0.0, F_mod])
    dF_obs = np.diff(np.r_[0.0, d['F_meas']])
    k = d.get('keep', np.ones(F_mod.size, bool))
    if weighting == 'relative':
        return np.r_[((dF_mod - dF_obs) / dF_obs)[k], ((F_mod - d['F_meas']) / d['F_meas'])[k]]
    return np.r_[(dF_mod - dF_obs)[k], (F_mod - d['F_meas'])[k]]


def fit_domains(spec, n, weighting='absolute', init=None, n_starts=60,
                n_random_with_init=10, seed=0):
    """Fit n free domains (fractions and sizes) to the 3He yields.
    init=(f_prev, r_prev) from an (n-1)-domain fit warm-starts the search by
    adding one domain at a range of sizes (Farley & Flowers: add domains one
    at a time); the fit therefore cannot get worse with n."""
    d = he3_data(spec)
    rng = np.random.default_rng(seed)
    lo = np.r_[np.full(n - 1, -15.0), np.full(n, LOG10_R_BOUNDS[0])]
    hi = np.r_[np.full(n - 1, 15.0), np.full(n, LOG10_R_BOUNDS[1])]
    starts = []
    if init is not None and len(init[0]) == n - 1:
        f0, r0 = np.asarray(init[0], float), np.asarray(init[1], float)
        for lr_new in np.linspace(LOG10_R_BOUNDS[0] + 0.5, LOG10_R_BOUNDS[1] - 0.5, 15):
            for share in (0.01, 0.1):
                starts.append(pack(np.r_[f0 * (1 - share), share], np.r_[r0, 10 ** lr_new]))
        n_rand = n_random_with_init
    else:
        n_rand = n_starts
    for _ in range(n_rand):
        starts.append(np.r_[rng.uniform(-4, 4, n - 1), np.sort(rng.uniform(-4.5, 2.0, n))])
    best = None
    for x0 in starts:
        x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)
        if n == 1:
            x0 = np.atleast_1d(x0)
        try:
            res = least_squares(residuals, x0, bounds=(lo, hi), args=(n, d, weighting),
                                method='trf', x_scale='jac', max_nfev=5000)
        except Exception:
            continue
        if best is None or res.cost < best.cost:
            best = res
    f, r = unpack(best.x, n)
    resid = residuals(best.x, n, d, weighting)
    ss = float(np.sum(resid ** 2))
    n_obs, k = resid.size, 2 * n - 1
    F_mod = mixture_F(d['tau_hrd'], f, r)
    lnD_mod = D.apparent_lnD(F_mod, d['t_s'])
    kk = d['keep']
    chi2_arr = float(np.sum(((lnD_mod - d['lnD']) / d['sigma'])[kk] ** 2))
    tau_end = d['tau_hrd'][-1]
    released = np.array([M.uniform_F(tau_end / rj ** 2)[0] for rj in r])
    return dict(n=n, f=f, r=r, weighting=weighting, sum_sq=ss, n_obs=n_obs, k=k,
                rms_yield=float(np.sqrt(ss / n_obs)),
                bic=float(n_obs * np.log(ss / n_obs) + k * np.log(n_obs)),
                aic=float(n_obs * np.log(ss / n_obs) + 2 * k),
                arrhenius_chi2=chi2_arr, arrhenius_chi2_nu=chi2_arr / (int(kk.sum()) - k), n_arrhenius=int(kk.sum()),
                frac_degassed_in_lab=released,
                model_F=F_mod, model_lnD=lnD_mod)


# ---------------------------------------------------------------------------
# Step 2: 4He/3He spectrum for a fixed domain set
# ---------------------------------------------------------------------------
class SpectrumModelFree:
    def __init__(self, spec, f, r):
        self.spec = spec
        self.f = np.asarray(f, dtype=float)
        self.r = np.asarray(r, dtype=float)
        tau0 = ref_lab_tau(spec['F_end'], self.f, self.r)
        self.E = [np.exp(-np.outer(np.r_[0.0, tau0 / rj ** 2], M.LAM)) for rj in self.r]

    def modes(self, t_nodes, T_nodes, dt_myr=2.0):
        return D.path_modes_multi(t_nodes, T_nodes, self.r, dt_myr)

    def predict(self, A):
        N = sum(fj * (E @ (Aj * M.W_INT)) for fj, E, Aj in zip(self.f, self.E, A))
        return (-np.diff(N) / N[0]) / self.spec['dF3']

    def bulk_age(self, A):
        return float(sum(fj * M.domain_age(Aj) for fj, Aj in zip(self.f, A)))

    def domain_ages(self, A):
        return np.array([M.domain_age(Aj) for Aj in A])

    def evaluate(self, t_nodes, T_nodes, dt_myr=2.0):
        A = self.modes(t_nodes, T_nodes, dt_myr)
        p = self.predict(A)
        return M.chi2(self.spec, p), self.bulk_age(A), p
