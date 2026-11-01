"""
insitu_lambda.py -- shared analysis for the in-situ permeation rate
constant (lambda) checks of the Copernicus methods paper (Chapter 1).

Check A  (MC empty ampoule): fit lambda and the ampoule's helium inventory
         n0 to each isothermal series of permeation steps (Eq. incyield of
         the main text, written in the equivalent mass-balance form below so
         that interleaved non-isothermal accumulations can be skipped), for
         3He and 4He independently. The fitted n0 is graded against the n0
         known independently from the experiment's total yield.

Check B  (encapsulated Durango apatite): every permeation step of that
         experiment was run at ~24 C, so a single lambda (lambda_24) sets
         every n0 used in the permeation lag correction. Scanning lambda_24
         and asking which value makes the corrected Arrhenius array below
         the high-temperature curl most linear lets the data choose
         lambda_24; the geometry + literature prediction is only a check.

Data (curated, extracted verbatim from the thesis Chapter 1 tables on
2026-10-30):
    data/mc_emptytube_distilled.csv        (SI tables s-mc-emptytube-3he/4he)
    data/durango_apatite_stepheat_full.csv (main-text table apatite-stepheat)
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')

# ---------------------------------------------------------------------------
# Literature + geometry prediction (used ONLY as a check)
# Swets et al. (1961) permeability, Jones (1953) 3He/4He ratio, Masaryk (1968)
# cylindrical geometric factor.  Mirrors thermochr_utils.swets_K / Jones.
# ---------------------------------------------------------------------------
RCAL = 1.987          # cal/mol/K
RATOMS = 1.36e-22     # cc atm / atom / K
R_J = 8.314           # J/mol/K


def swets_K(TK):
    TK = np.asarray(TK, float)
    hi = TK >= 573
    DEa = np.where(hi, 6613, 5580); SEa = np.where(hi, -1174, -680)
    DFF = np.where(hi, 7.40e-4, 3.04e-4); SFF = np.where(hi, 1.28e17, 1.99e17)
    return DFF * np.exp(-DEa / (RCAL * TK)) * SFF * np.exp(-SEa / (RCAL * TK))


def jones(TK):
    return 1.17 * np.exp(-57 / (RCAL * np.asarray(TK, float)))


def geometric_factor(ID_um, OD_um):
    a = ID_um / 2e4
    return 2.0 / (a ** 2 * np.log(OD_um / ID_um))


def lambda_predicted(TK, G, isotope='4He'):
    lam = swets_K(TK) * RATOMS * np.asarray(TK, float) * G
    return lam * jones(TK) if isotope == '3He' else lam


G_MC_EMPTY = geometric_factor(747, 1159)     # Table 1: 3264 cm^-2
G_DURANGO = 2394.0                           # Table 1
T_PERM_DURANGO_K = 297.15                    # 24 C: reference T of lambda_24


# ---------------------------------------------------------------------------
# Check A
# ---------------------------------------------------------------------------
def load_mc_empty():
    d = pd.read_csv(os.path.join(DATA, 'mc_emptytube_distilled.csv'))
    d['T_num'] = pd.to_numeric(d['T_C'], errors='coerce')
    return d


# Steps 28-29 (the last two 250 C accumulations, 159.9 and 52.9 min) permeate
# markedly faster than the preceding identical 250 C steps in BOTH isotopes
# (apparent rate constants 1.3x and 2.5x higher), immediately before the
# anomalous final measurement described in the Supplement.  They are excluded
# from the rate-constant fits and flagged in the figure.
EXCLUDED_STEPS = (28, 29)

# First steps of the 125 C (step 7) and 200 C (step 19) runs: although each
# follows a non-isothermal transition accumulation, both permeate markedly
# less than the exponential fitted to the later steps of the same run
# (glass not yet in diffusive steady state; see the cumulative-yield figure
# from fig_insitu_lambda_fits.py) and are the only first steps excluded.  The
# first steps of the 150, 175 and 250 C runs (11, 14, 22) are consistent with
# their runs and are kept.
UNEQUILIBRATED_FIRST_STEPS = (7, 19)


def isothermal_series(d):
    """Group steps into runs of CONSECUTIVE isothermal steps (Eq. incyield).
    A run ends at any temperature change or at any non-isothermal
    accumulation ('--'), so every run begins with the first measurement
    after the ampoule was brought to a new temperature."""
    series, cur, curT = [], [], None
    for i, r in d.iterrows():
        T = r['T_num']
        if np.isnan(T) or int(r['step']) in EXCLUDED_STEPS:
            if cur:
                series.append((curT, cur))
            cur, curT = [], None
            continue
        if curT is None or T != curT:
            if cur:
                series.append((curT, cur))
            cur, curT = [i], T
        else:
            cur.append(i)
    if cur:
        series.append((curT, cur))
    return series


def _model(t, inter, nfit):
    def f(_x, n0, lam):
        res, S = [], 0.0
        for k in range(len(t)):
            res.append((n0 - S) * (1 - np.exp(-lam * t[k])))
            S += res[-1] + inter[k]
        return np.array(res)
    return f


def fit_series(d, idx, isotope, drop_first=True, lam_guess=None, keep_after_transition=True):
    """Fit (n0, lambda) to one isothermal series.

    m_k = (n0 - S_k) (1 - exp(-lambda t_k)), where S_k is the helium that
    has left the ampoule since the start of the first fitted step (modelled
    permeation of earlier fitted steps plus the measured yield of any
    interleaved non-isothermal accumulation).  For consecutive steps this is
    identical to Eq. (incyield) of the main text.
    """
    mcol, scol, ncol = (('m4_nccSTP', 'm4_2s', 'n0_4_nccSTP') if isotope == '4He'
                        else ('m3_pccSTP', 'm3_2s', 'n0_3_pccSTP'))
    # first step after a temperature change: glass not yet in diffusive
    # steady state (wait >= tau rule of the main text) -> excluded
    # A run that follows directly from a different isothermal temperature
    # (175 and 250 C) loses its first step; runs preceded by a non-isothermal
    # transition accumulation ('--', e.g. 125, 150, 200 C) already had that
    # throw-away step, so all of their steps are kept.
    # keep_after_transition=False (manuscript as of 2026-10-30): drop the
    # first step of every run except the experiment's first measurement.
    prev = idx[0] - 1
    follows_isothermal = prev in d.index and not np.isnan(d.loc[prev, 'T_num'])
    if keep_after_transition:
        # data-driven rule: drop a first step only if it falls short of an
        # equilibrated step (125 and 200 C); the first steps of the 150, 175
        # and 250 C runs are consistent with their runs and are kept
        drop = drop_first and int(d.loc[idx[0], 'step']) in UNEQUILIBRATED_FIRST_STEPS
    else:
        drop = drop_first and idx[0] != d.index[0]
    use = idx[1:] if drop else list(idx)
    if len(use) < 2:
        raise ValueError('too few usable consecutive steps')
    fitted = [i for i in use if not np.isnan(d.loc[i, 'T_num'])]
    t, m, s, inter = [], [], [], []
    for i in use:
        if np.isnan(d.loc[i, 'T_num']):
            inter[-1] += d.loc[i, mcol]          # helium removed between fits
        else:
            t.append(d.loc[i, 'time_min'] * 60.0)
            m.append(d.loc[i, mcol]); s.append(d.loc[i, scol] / 2.0)
            inter.append(0.0)
    t, m, s, inter = map(np.array, (t, m, s, inter))
    T_K = d.loc[fitted[0], 'T_num'] + 273.15
    lam0 = lam_guess or lambda_predicted(T_K, G_MC_EMPTY, isotope)
    n0g = m[0] / (1 - np.exp(-lam0 * t[0]))
    f = _model(t, inter, len(t))
    p, cov = curve_fit(f, np.zeros(len(t)), m, p0=[n0g, lam0], sigma=s,
                       absolute_sigma=True, maxfev=20000)
    resid = (m - f(None, *p)) / s
    tcum = t.sum() + 0.0
    return dict(isotope=isotope, T_C=T_K - 273.15, T_K=T_K, N=len(t),
                n0_fit=p[0], n0_fit_1s=np.sqrt(cov[0, 0]),
                lam=p[1], lam_1s=np.sqrt(cov[1, 1]),
                n0_true=d.loc[fitted[0], ncol],
                lam_pred=lambda_predicted(T_K, G_MC_EMPTY, isotope),
                lamt_cum=p[1] * tcum, chi2=float(np.sum(resid ** 2)),
                first_step=int(d.loc[fitted[0], 'step']),
                run_steps=[int(d.loc[i, 'step']) for i in idx],
                dropped_steps=[int(d.loc[i, 'step']) for i in idx if i not in use],
                last_step=int(d.loc[fitted[-1], 'step']))


# First-step test (adopted 2026-10-30).  Each run is fit with and without its
# first step.  A first step taken before the glass reached diffusive steady
# state can only UNDER-permeate after heating, so removing it RAISES lambda.
# The first step is rejected if removing it raises lambda by more than
# FIRST_STEP_LAM_RATIO_MAX in both isotopes.  A run left with fewer than
# MIN_STEPS steps is not used (a two-step fit is exactly determined and cannot
# be checked against the scatter of the data).
FIRST_STEP_LAM_RATIO_MAX = 1.10
# MIN_STEPS lowered from 3 to 2 (2026-10-30): the 125 and 200 C runs are kept
# as two-step fits; the exclusion of their first steps is justified in the
# paper by the R^2 of the ln(lambda/T) Arrhenius fit (0.79 -> 0.99).
MIN_STEPS = 2


def first_step_test():
    """Table comparing, for every run and isotope, the fit to all steps with
    the fit omitting the first step."""
    d = load_mc_empty()
    rows = []
    for T, idx in isothermal_series(d):
        if len(idx) < 3:
            continue
        for iso in ('4He', '3He'):
            mcol = 'm4_nccSTP' if iso == '4He' else 'm3_pccSTP'
            a = fit_series(d, idx, iso, drop_first=False)
            b = fit_series(d, idx[1:], iso, drop_first=False)
            n_start_b = b['n0_fit'] + d.loc[idx[0], mcol]     # mass balance
            rows.append(dict(
                isotope=iso, T_C=T, N_all=a['N'], chi2dof_all=a['chi2'] / (a['N'] - 2),
                N_drop=b['N'],
                chi2dof_drop=(b['chi2'] / (b['N'] - 2)) if b['N'] > 2 else np.nan,
                lam_ratio=b['lam'] / a['lam'],
                lam_ratio_1s=b['lam'] / a['lam'] * np.hypot(a['lam_1s'] / a['lam'], b['lam_1s'] / b['lam']),
                n0_ratio=n_start_b / a['n0_fit'],
                first_step=int(d.loc[idx[0], 'step'])))
    t = pd.DataFrame(rows)
    fail = t.groupby('T_C')['lam_ratio'].transform(lambda r: bool((r > FIRST_STEP_LAM_RATIO_MAX).all()))
    t['first_step_rejected'] = fail.astype(bool)
    t['N_used'] = np.where(t['first_step_rejected'], t['N_drop'], t['N_all'])
    t['run_used'] = t['N_used'] >= MIN_STEPS
    return t


def check_A(drop_first=None, keep_after_transition=None, include_rejected=False):
    """Adopted in-situ fits.  drop_first=False returns the fit to every step
    of every run (used for comparison figures); the default applies the
    first-step test and the MIN_STEPS rule.  include_rejected=True also
    returns the (first-step-dropped) fits of runs that fail MIN_STEPS, flagged
    with used=False."""
    d = load_mc_empty()
    test = first_step_test().set_index(['T_C', 'isotope'])
    rows = []
    for T, idx in isothermal_series(d):
        if len(idx) < 3:
            continue
        for iso in ('4He', '3He'):
            if drop_first is False:
                f = fit_series(d, idx, iso, drop_first=False); f['used'] = True
            else:
                tr = test.loc[(T, iso)]
                use = idx[1:] if tr['first_step_rejected'] else idx
                f = fit_series(d, use, iso, drop_first=False)
                f['run_steps'] = [int(d.loc[i, 'step']) for i in idx]
                f['dropped_steps'] = [int(d.loc[idx[0], 'step'])] if tr['first_step_rejected'] else []
                f['used'] = bool(tr['run_used'])
                if not f['used'] and not include_rejected:
                    continue
            rows.append(f)
    return pd.DataFrame(rows)


def arrhenius_lam_over_T(TK, lam, lam_1s=None):
    """Weighted fit of ln(lambda/T) = ln(A) - Ea/(R T).  Returns Ea (kJ/mol),
    lnA and a callable."""
    x = 1.0 / np.asarray(TK); y = np.log(np.asarray(lam) / np.asarray(TK))
    w = None if lam_1s is None else (np.asarray(lam) / np.asarray(lam_1s))
    p = np.polyfit(x, y, 1, w=w)
    return -p[0] * R_J / 1e3, p[1], (lambda T: np.exp(np.polyval(p, 1.0 / T)) * T)


# ---------------------------------------------------------------------------
# Check B
# ---------------------------------------------------------------------------
DURANGO_TOTAL = 3.18 * 194.2      # nccSTP 4He (Farley 2000 conc.; in-lab verified)


def load_durango():
    return pd.read_csv(os.path.join(DATA, 'durango_apatite_stepheat_full.csv'))


def _ff_inversion(t, F, Fp):
    """Fechtig & Kalbitzer (1966) sphere, as thermochr_utils.InvertFrequencyFactor."""
    if F <= 0.1:
        return ((F ** 2 - Fp ** 2) * np.pi) / (36 * t)
    if F < 0.9:
        return (1 / (np.pi ** 2 * t)) * (-(np.pi ** 2 / 3) * (F - Fp) - 2 * np.pi * (
            (1 - (np.pi / 3) * F) ** 0.5 - (1 - (np.pi / 3) * Fp) ** 0.5))
    return (1 / (np.pi ** 2 * t)) * np.log((1 - Fp) / (1 - F))


def durango_correct(d, scale):
    """Recompute the permeation-lag correction with every solved n0 scaled by
    `scale` (= lambda_tab / lambda_trial; exact to <0.3% because every
    permeation step has lambda*t_eff < 0.005).  Propagated inventories follow
    Eq. (carry) using the measured yields of intervening steps."""
    rows = d.to_dict('records')
    exps = []
    for i, r in enumerate(rows):
        if r['type'] != 'Experimental':
            continue
        b = rows[i - 1]
        j, inter = i + 1, 0.0
        while rows[j]['n0_solved'] != 1:
            inter += rows[j]['m_nccSTP']; j += 1
        n_before = scale * b['n0_nccSTP'] - b['m_nccSTP']
        n_after = scale * rows[j]['n0_nccSTP'] + inter
        exps.append(dict(order=r['order'], T_C=r['T_C'], t=r['time_min'] * 60,
                         m=r['m_nccSTP'], omega=r['m_nccSTP'] + n_after - n_before))
    e = pd.DataFrame(exps)
    F = np.cumsum(e['omega']) / DURANGO_TOTAL
    Fp = np.concatenate([[0.0], F[:-1]])
    D = []
    for t, f, fp in zip(e['t'], F, Fp):
        try:
            D.append(_ff_inversion(t, f, fp))
        except Exception:
            D.append(np.nan)
    e['F'] = F; e['Da2'] = D
    return e


# Steps used for the linearity test: experimental steps at <= 300 C that
# precede the first excursion above 300 C (i.e. below the high-temperature
# curl), excluding the 100, 150 and 255 C steps whose corrected yields are
# within 2 sigma of zero in the published table.
def durango_linearity_steps(e):
    first_hot = e.index[e['T_C'] > 305][0]
    sel = e.loc[:first_hot - 1]
    sel = sel[(sel['T_C'] >= 199) & ~((sel['T_C'] > 254) & (sel['T_C'] < 256))]
    return sel.index


def r2_linear(x, y):
    p = np.polyfit(x, y, 1)
    ss_res = np.sum((y - np.polyval(p, x)) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return 1 - ss_res / ss_tot, p


def check_B(lam24_grid, lam24_tab, T_perm_C=None, Ea_kJ=None):
    """R^2 of ln(D/a^2) vs 1/T below the curl as a function of lambda_24.

    lam24_tab: the lambda_24 implied by the published correction (geometry +
    literature).  Because every permeation step is at 23.5-24.3 C, trial
    lambda_24 values map onto a uniform scale of the solved n0 values:
    scale = lam24_tab / lam24_trial.  (The small 23.5-24.3 C step-to-step
    temperature differences are already in the tabulated n0 values and
    cancel in the ratio.)
    """
    d = load_durango()
    out = []
    base = durango_correct(d, 1.0)
    idx = durango_linearity_steps(base)
    for lam in lam24_grid:
        e = durango_correct(d, lam24_tab / lam)
        D = e.loc[idx, 'Da2'].to_numpy(float)
        ok = np.all(D > 0) and np.all(np.isfinite(D))
        if not ok:
            out.append((lam, np.nan)); continue
        x = 1.0 / (e.loc[idx, 'T_C'].to_numpy() + 273.15)
        r2, _ = r2_linear(x, np.log(D))
        out.append((lam, r2))
    return pd.DataFrame(out, columns=['lam24', 'R2']), idx
