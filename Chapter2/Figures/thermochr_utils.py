"""
Thermochreduction utility functions and constants.
Farley Lab Group, Caltech.  Ben J. Thyer, 2022–2025.

All pure functions — no external data reads.  Import and call as needed.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import scipy.optimize
import scipy.interpolate
import os
from datetime import datetime
from molmass import Formula

plt.rcParams.update({"text.usetex": False, "font.family": "DejaVu Sans"})

# ---------------------------------------------------------------------------
# Radioactive decay constants (1/year)
# ---------------------------------------------------------------------------
lam_U238 = 1.55135895e-10
lam_U235 = 9.84584063e-10
lam_Th232 = np.log(2) / 1.405E10
lam_Sm147 = np.log(2) / 1.0625E11
Av = 6.0221408E23

# ---------------------------------------------------------------------------
# Silica glass transport properties (Swets et al. 1961)
# ---------------------------------------------------------------------------
Rcal = 1.987        # cal / mol / K
RccATM = 82.06      # cc atm / mol / K
Ratoms = 1.36E-22   # cc atm / atom / K


def swets_K(T, D_out=False):
    """Permeability (or diffusivity) of He in fused silica.
    T in Kelvin.  Returns K in atoms/cm/s/atm; set D_out=True for D in cm²/s."""
    if T >= 573:
        DEa, SEa, DFF, SFF = 6613, -1174, 7.40E-4, 1.28E17
    else:
        DEa, SEa, DFF, SFF = 5580, -680, 3.04E-4, 1.99E17
    D = DFF * np.exp(-DEa / (Rcal * T))
    if D_out:
        return D
    S = SFF * np.exp(-SEa / (Rcal * T))
    return D * S


def swets(L, T):
    """He permeability / diffusivity / solubility of fused silica.
    L in {'D','S','K'}, T in Kelvin."""
    if T >= 573:
        DEa, SEa, DFF, SFF = 6613, -1174, 7.40E-4, 1.28E17
    else:
        DEa, SEa, DFF, SFF = 5580, -680, 3.04E-4, 1.99E17
    D = DFF * np.exp(-DEa / (Rcal * T))
    S = SFF * np.exp(-SEa / (Rcal * T))
    K = D * S
    tag = L.upper()
    if tag == 'D':
        return D
    if tag == 'S':
        return S
    if tag == 'K':
        return K
    raise ValueError("L must be one of 'D', 'S', 'K'")


def Jones(T):
    """3He/4He permeability ratio correction (Jones, 1953).  T in Kelvin."""
    return 1.17 * np.exp(-57 / (Rcal * T))


def tube_permeate2(T, t, ID, OD, He='4He'):
    """Fractional He remaining (n_t/n_0) after time t in a silica ampoule.
    Lengths (ID, OD) in cm, T in Kelvin, t in seconds."""
    K = swets_K(T)
    if He == '3He':
        K *= Jones(T)
    return np.exp(-(K * Ratoms * T * 2 * t) / (np.log(OD / ID) * ((ID / 2) ** 2)))


# ---------------------------------------------------------------------------
# Fechtig & Kalbitzer (1966) diffusivity inversion
# ---------------------------------------------------------------------------

def InvertFrequencyFactor(t, F, Fp):
    """D/a² from step F and previous F_p.  t in seconds.
    Returns 0 if F rounds to 1."""
    if np.round(F, 3) == 1:
        return 0
    if F <= 0.1:
        return ((F ** 2 - Fp ** 2) * np.pi) / (36 * t)
    elif F < 0.9:
        return (1 / (np.pi ** 2 * t)) * (
            -(np.pi ** 2 / 3) * (F - Fp)
            + (-2 * np.pi) * ((1 - (np.pi / 3) * F) ** 0.5
                              - (1 - (np.pi / 3) * Fp) ** 0.5)
        )
    elif F < 1:
        return (1 / (np.pi ** 2 * t)) * np.log((1 - Fp) / (1 - F))
    raise ValueError(f'F={F} out of range (0–1); t={t/60:.1f} min')


# ---------------------------------------------------------------------------
# He production and age functions
# ---------------------------------------------------------------------------

def isotope_fraction(symbol, mass_number):
    """Natural abundance fraction of one isotope, via
    molmass.Formula(symbol).spectrum()[mass_number] -- wrapped because
    molmass's return type for that changed across versions in a way
    that silently breaks either direct access style depending which is
    installed: older molmass (e.g. 2021.6.18) returns a plain
    [mass, fraction] list (fraction at index 1), while newer molmass
    returns a SpectrumEntry object with a .fraction attribute that is
    NOT subscriptable (indexing it raises TypeError). Different
    environments used on this project pin different molmass versions,
    so hardcoding either form breaks the other -- this checks which one
    it got at call time instead of assuming."""
    entry = Formula(symbol).spectrum()[mass_number]
    return entry.fraction if hasattr(entry, 'fraction') else entry[1]


def He_forward(U_mol, Th_mol, Sm_mol, t):
    """He produced (nccSTP) from U/Th/Sm in moles after time t in years."""
    U_at = U_mol * Av
    Th_at = Th_mol * Av
    Sm_at = Sm_mol * Av
    He_at = (
        8 * (1 - 1 / 137.88) * U_at * (np.exp(lam_U238 * t) - 1)
        + 7 * (U_at / 137.88) * (np.exp(lam_U235 * t) - 1)
        + 6 * Th_at * (np.exp(lam_Th232 * t) - 1)
        + Sm_at * isotope_fraction('Sm', 147) * (np.exp(lam_Sm147 * t) - 1)
    )
    return (He_at / 6.0221E23) * 22.71 * 1E12


def He_residual(t, He_ncc, U_mol, Th_mol, Sm_mol):
    return He_ncc - He_forward(U_mol, Th_mol, Sm_mol, t)


def He_derivative(t, U_mol, Th_mol, Sm_mol):
    U_at = U_mol * Av
    Th_at = Th_mol * Av
    Sm_at = Sm_mol * Av
    val = (
        8 * (1 - 1 / 137.88) * U_at * lam_U238 * np.exp(lam_U238 * t)
        + 7 * (U_at / 137.88) * lam_U235 * np.exp(lam_U235 * t)
        + 6 * Th_at * lam_Th232 * np.exp(lam_Th232 * t)
        + Sm_at * isotope_fraction('Sm', 147) * lam_Sm147 * np.exp(lam_Sm147 * t)
    )
    return -(val / 6.0221E23) * 22.71 * 1E12


def iterative_solver(func, ans, epsilon=0, bounds=(-1E15, 1E15), verbose=True, **kwargs):
    """Newton-like bisection solver for an unknown keyword argument."""
    epsilon = np.abs(epsilon) or np.abs(np.mean(ans) / 1E6)
    unknown = next(k for k, v in kwargs.items() if isinstance(v, str))
    test_X = np.linspace(bounds[0], bounds[1], 100)
    error = epsilon * 2
    iterations = 0
    while np.abs(error) > epsilon:
        test_ans = []
        for x in test_X:
            kwargs[unknown] = x
            test_ans.append(func(**kwargs))
        test_ans = np.array(test_ans)
        nan_ind = np.isnan(test_ans)
        test_X = test_X[~nan_ind]
        test_ans = test_ans[~nan_ind]
        winner_ind = np.argmin(np.abs(test_ans - ans))
        if winner_ind in (0, len(test_X) - 1):
            test_X = np.linspace(-1E15, 1E15, 100)
            continue
        error = test_ans[winner_ind] - ans
        winner = test_X[winner_ind]
        test_X = np.linspace(test_X[winner_ind - 1], test_X[winner_ind + 1], 100)
        iterations += 1
    if verbose:
        print(f"Solved: {unknown} = {winner} (err = {abs(100*error/ans):.4f}%, {iterations} iters)")
    return winner


def He_Age(inputArray):
    """(U-Th-Sm)/He age with propagated 2σ uncertainties.
    inputArray = [He, He_2s, U, U_2s, Th, Th_2s, Sm, Sm_2s] (moles / ncc)."""
    auto_input = {
        'He': [inputArray[0], inputArray[1]],
        'U':  [inputArray[2], inputArray[3]],
        'Th': [inputArray[4], inputArray[5]],
        'Sm': [inputArray[6], inputArray[7]],
    }
    if np.sum(inputArray[3:]) == 0:
        return np.array([0, 0])
    t_ans = iterative_solver(He_forward, ans=auto_input['He'][0], t='x',
                             U_mol=auto_input['U'][0], Th_mol=auto_input['Th'][0],
                             Sm_mol=auto_input['Sm'][0], epsilon=auto_input['He'][0] / 1E7,
                             verbose=False, bounds=(-1E6, 5E9))
    errors = []
    for key in auto_input:
        for sign in [+1, -1]:
            auto_input[key][0] += sign * auto_input[key][1]
            t_pm = iterative_solver(He_forward, ans=auto_input['He'][0], t='x',
                                    U_mol=auto_input['U'][0], Th_mol=auto_input['Th'][0],
                                    Sm_mol=auto_input['Sm'][0], epsilon=auto_input['He'][0] / 1E7,
                                    verbose=False, bounds=(-1E6, 5E9))
            errors.append(np.abs(t_ans - t_pm))
            auto_input[key][0] -= sign * auto_input[key][1]
    return np.array([t_ans, np.sqrt(np.sum(np.array(errors) ** 2) / 2)])


def MC_Age(inputArray, n=1000, verbose=False):
    """Monte-Carlo (U-Th-Sm)/He age.  Returns [mean_age_Ma, 2sigma_Ma]."""
    Hev  = np.random.normal(inputArray[0], inputArray[1] / 2, n)
    Uv   = np.random.normal(inputArray[2], inputArray[3] / 2, n)
    Thv  = np.random.normal(inputArray[4], inputArray[5] / 2, n)
    Smv  = np.random.normal(inputArray[6], inputArray[7] / 2, n)
    ages = []
    for i in range(n):
        He, U, Th, Sm = max(Hev[i], 0), max(Uv[i], 0), max(Thv[i], 0), max(Smv[i], 0)
        He_m = He / (22.71 * 1E12)
        eU = U + 0.24 * Th
        guess_t = He_m / (eU * lam_U238) if eU > 0 else 1E6
        age = scipy.optimize.newton(
            lambda t: He_residual(t, He, U, Th, Sm),
            guess_t,
            fprime=lambda t: He_derivative(t, U, Th, Sm),
            tol=1E-5, maxiter=400)
        ages.append(age)
    return np.array([np.mean(ages) / 1E6, 2 * np.std(ages) / 1E6])


# ---------------------------------------------------------------------------
# Alpha recoil retention
# ---------------------------------------------------------------------------

def Ft(R, S, X):
    """Alpha recoil retention factor (Farley et al. 1996, Eqn 3).
    R: grain radius (µm, scalar or array), S: stopping distances array
    (µm, length 4: 238U/235U/232Th/147Sm), X: [U, Th, Sm] elemental
    abundances (atoms or moles).

    Two corrections vs. the original version of this function (fixed
    2026 -- see Chapter3/Figures/fig_alpha_stopping_distances.py, which
    first surfaced both while modeling sub-stopping-distance apatite
    inclusions):

    1. The alpha-weight normalization now sums the SAME four terms used
       in the numerator (previously the normalizing "total" used the
       full elemental Sm abundance X[2], while the Sm term actually
       being weighted used only the 147Sm-decaying fraction of it --
       two different quantities for what should be the same term, so
       the weights didn't sum to 1). Harmless wherever Sm's contribution
       is small relative to U/Th, which is why this went unnoticed --
       every existing caller (recoil_correct(), used for real dated
       grains via reduce_quad.py) is unaffected in proportion to how
       small that Sm term already was for those grains.
    2. R < S is now handled explicitly per isotope rather than left to
       the bare polynomial. Farley (1996)'s cubic form
       1 - (3/4)(S/R) + (1/16)(S/R)^3 is exact only for R >= S; for
       R < S it doesn't just dip negative, it diverges (the cubic term
       dominates and blows up positive as R -> 0), since the polynomial
       was derived as a surface-correction term under R >= S and was
       never meant to extrapolate below it. Every existing caller uses
       real mineral grain radii (tens to hundreds of microns) that are
       always >= the ~15-22 um stopping distances involved, so this
       branch was never exercised before and changes nothing for them --
       it only matters for new callers modeling deliberately sub-
       stopping-distance grains/inclusions, where R < S means every
       decay's alpha track exits the grain regardless of direction, so
       retention for that isotope is exactly zero.

    Returns a scalar if R is scalar, else an array the same shape as R.
    """
    R_arr = np.asarray(R, dtype=float)
    S = np.asarray(S, dtype=float)
    alpha_weights = np.array([8 * X[0], 7 * X[0] / 137.88, 6 * X[1],
                              isotope_fraction('Sm', 147) * X[2]])
    weights = alpha_weights / alpha_weights.sum()

    if R_arr.ndim == 0:
        ratio = S / R_arr
        ft_per_isotope = np.where(R_arr >= S, 1 - (3 / 4) * ratio + (1 / 16) * ratio ** 3, 0.0)
        return float(np.sum(ft_per_isotope * weights))
    ratio = S / R_arr[:, None]
    ft_per_isotope = np.where(R_arr[:, None] >= S, 1 - (3 / 4) * ratio + (1 / 16) * ratio ** 3, 0.0)
    return ft_per_isotope @ weights


def recoil_correct(r, inputArray, alpha_stopping_distances, a_phase):
    """Monte-Carlo Ft correction.  r = [radius_um, 2sigma_um].
    Returns [Ft, Ft_2s, He_corr, He_corr_2s, age, age_2s]."""
    abund = {k: [inputArray[i * 2], inputArray[i * 2 + 1]]
             for i, k in enumerate(['He', 'U', 'Th', 'Sm'])}
    fts = []
    rs  = np.random.normal(r[0], r[1] / 2, 500)
    Us  = np.random.normal(abund['U'][0],  abund['U'][1]  / 2, 500)
    Ths = np.random.normal(abund['Th'][0], abund['Th'][1] / 2, 500)
    Sms = np.random.normal(abund['Sm'][0], abund['Sm'][1] / 2, 500)
    Hes = np.random.normal(abund['He'][0], abund['He'][1] / 2, 500)
    S = np.array(alpha_stopping_distances.loc[a_phase])
    for i in range(500):
        fts.append(Ft(R=rs[i], S=S, X=np.array([Us[i], Ths[i], Sms[i]])))
    Hes_corr = Hes / np.array(fts)
    ageInput = inputArray.copy()
    ageInput[0] = np.mean(Hes_corr)
    ageInput[1] = np.std(Hes_corr) * 2
    return np.append([np.mean(fts), np.std(fts) * 2,
                      np.mean(Hes_corr), np.std(Hes_corr) * 2], He_Age(ageInput))


def MDD_diffusive_loss_correct(GDC, inputArray):
    """Apply MDD diffusive-loss correction (Shuster et al. 2005)."""
    newInput = inputArray.copy()
    correction = (inputArray[0] * GDC['FvLRD']
                  + (inputArray[0] / (1 - GDC['HRD_deficit']) - inputArray[0]))
    newInput[0] += correction
    newInput[1] += correction
    return np.append(newInput[:2], He_Age(newInput))


# ---------------------------------------------------------------------------
# Isotope dilution / normal-solution standardization
# ---------------------------------------------------------------------------

def isotope_dilution(Nb, Ra, Rb, Rab):
    """Reverse isotope dilution.  Returns Na (same units as Nb).
    Accepts scalar or equal-length array arguments."""
    def _make_iter(x):
        try:
            return list(x)
        except TypeError:
            return [x]

    Nbs, Ras, Rbs, Rabs = map(_make_iter, [Nb, Ra, Rb, Rab])
    max_len = max(len(Nbs), len(Ras), len(Rbs), len(Rabs))
    pad = lambda v: v * max_len if len(v) == 1 else v
    Nbs, Ras, Rbs, Rabs = map(pad, [Nbs, Ras, Rbs, Rabs])
    ans = []
    for Nbi, Rai, Rbi, Rabi in zip(Nbs, Ras, Rbs, Rabs):
        T1 = 1 if np.isinf(Rbi) else (Rbi - Rabi)
        T4 = 1 if np.isinf(Rbi) else (1 + Rbi)
        T3 = 1 if np.isinf(Rai) else (1 + Rai)
        T2 = -1 if np.isinf(Rai) else (Rabi - Rai)
        ans.append(Nbi * (T1 / T2) * (T3 / T4))
    return np.array(ans)


def mass_multiplier(Formula_obj, normEl):
    """Phase mass (mg) per mole of normalising element."""
    for element_data in Formula_obj.composition():
        if element_data[0] == normEl:
            stoich = float(element_data[1])
    return 1000 * Formula_obj.mass / stoich


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def outlier_stats(vector):
    """Mean and SD after 2σ outlier rejection; ignores NaN."""
    vector = np.array(vector, dtype=float)
    vector = vector[~np.isnan(vector)]
    x, s = np.mean(vector), np.std(vector)
    mask = (vector > x - 2 * s) & (vector < x + 2 * s)
    xn, sn = np.mean(vector[mask]), np.std(vector[mask])
    comment = 'Outlier Corrected ' if xn != x else ''
    return xn, sn, comment


def pull_number(string):
    """Extract a float from a mixed string."""
    return float(''.join(c for c in string if c in '1234567890.'))


def remove_spaces(string):
    return string.replace(' ', '')


# ---------------------------------------------------------------------------
# Timestamp utilities
# ---------------------------------------------------------------------------

def _parse_time(stri):
    for fmt in ['%m/%d/%Y  %I:%M %p', '%m/%d/%Y  %H:%M:%S',
                '%m/%d/%Y  %H:%M', '%m/%d/%Y  %I:%M:%S %p']:
        try:
            return datetime.strptime(stri, fmt)
        except ValueError:
            pass
    raise ValueError(f"Could not parse timestamp: {stri!r}")


def extract_timesMC(dates):
    """Per-step durations (seconds) from MC timestamp strings."""
    times = []
    oldtime = None
    for stri in dates:
        t = _parse_time(stri)
        if oldtime is None:
            oldtime = t
        else:
            times.append((t - oldtime).total_seconds())
            oldtime = t
    return np.array(times)


def extract_times_from0(dates):
    """Elapsed seconds from the first MC timestamp."""
    times = []
    firsttime = None
    for stri in dates:
        t = _parse_time(stri)
        if firsttime is None:
            firsttime = t
        else:
            times.append((t - firsttime).total_seconds())
    return np.array(times)


def extract_times(dates):
    """Cold-blank step durations from Diff Cell timestamp strings
    (skips every other timestamp, which is the 'open' event)."""
    times = []
    oldtime = None
    closeT = False
    for stri in dates[1:]:
        try:
            t = datetime.strptime(stri[1:-1], '%m/%d/%Y %I:%M:%S %p')
        except ValueError:
            continue
        if oldtime is None:
            oldtime = t
        elif closeT:
            times.append((t - oldtime).total_seconds())
            oldtime = t
            closeT = False
        else:
            closeT = True
    return np.array(times)


# ---------------------------------------------------------------------------
# First-order inversion utilities
# ---------------------------------------------------------------------------

def accumulate(v):
    vnew = [v[0]]
    for vnext in v[1:]:
        vnew.append(vnext + vnew[-1])
    return np.array(vnew)


def forward_permeate(t, lamb, n0):
    return n0 * (1 - np.exp(-lamb * t))


def KenColdInversion(t, He, plot=False):
    """Fit exponential decay to cold-blank permeation series.
    Returns (lambda, n0)."""
    cumHe = accumulate(He)
    cumt = accumulate(t)
    lamb0 = 6E-5
    out, _ = scipy.optimize.curve_fit(
        forward_permeate, cumt, cumHe,
        p0=[lamb0, He[0] / (1 - np.exp(-lamb0 * t[0]))])
    if plot:
        longt = np.linspace(0, cumt[-1], 500)
        plt.plot(longt, forward_permeate(longt, *out))
        plt.scatter(cumt, cumHe)
    return out[0], out[1]


# ---------------------------------------------------------------------------
# Diffusion reduction pipeline helper
# ---------------------------------------------------------------------------

def diffusion_reduction(HeVec, TimeSeconds, TempKelvin=None,
                        newDiffName='manual_diffusion.csv',
                        cumHe='A', total_yield='A'):
    """D/a² inversion from step-heating He yields.
    Returns reduced DataFrame and saves to CSV."""
    if total_yield == 'A':
        total_yield = np.sum(HeVec)
    fcum, D_a2, lnD_a2 = [], [], []
    Fp = 0
    for i, step_yield in enumerate(HeVec):
        Fp_i = cumHe[i] / total_yield if cumHe != 'A' else Fp
        F = Fp_i + step_yield / total_yield
        ff = InvertFrequencyFactor(t=TimeSeconds[i], F=F, Fp=Fp_i)
        D_a2.append(ff)
        lnD_a2.append(np.log(ff) if ff > 0 else np.nan)
        fcum.append(F)
        Fp = F

    if TempKelvin is not None and np.sum(TempKelvin):
        data = [(TempKelvin - 273).tolist(), (TimeSeconds / 60).tolist(),
                HeVec, fcum, D_a2, lnD_a2, (10000 / TempKelvin).tolist()]
        columns = ['Temp (C)', 'Time (min)', 'He Yield (nCC@STP)',
                   'Fcum', 'D/a^2 ', 'ln(D/a^2)', '10^4/T']
    else:
        data = [(TimeSeconds / 60).tolist(), HeVec, fcum, D_a2, lnD_a2]
        columns = ['Time (min)', 'He Yield (nCC@STP)', 'Fcum', 'D/a^2 ', 'ln(D/a^2)']

    df = pd.DataFrame({col: data[i] for i, col in enumerate(columns)})
    df.to_csv(newDiffName)
    return df


# ---------------------------------------------------------------------------
# Win-06-01b hydrothermal diffusivity reduction (master workbook)
# ---------------------------------------------------------------------------

def load_diffusivities_HTWin0601b(xlsx_path, sheet_name='diffusivitiesHTWin0601bM'):
    """Read the 3He and 4He step-heat diffusivity reductions for the
    Win-06-01b hydrothermal experiment from one of the master workbook's
    per-bound sheets ('diffusivitiesHTWin0601bM'/'...UB'/'...LB' -- this
    study's own reduction, as opposed to the vacuum datasets reduced by
    diffusion_reduction()).

    NOTE: the workbook used to have a single 'diffusivitiesHTWin0601b'
    sheet with a symmetric propagated-2-sigma column. It has since been
    split into three sheets (M = central/measured, UB = upper bound, LB
    = lower bound) implementing the "treatment as uncertainty" method,
    where the upper/lower bounds on the permeation-lag correction are
    carried through explicitly instead of propagating a single symmetric
    error term. There is no longer a per-point symmetric sigma column in
    any of these sheets -- use load_diffusivities_HTWin0601b_bounds()
    below to get the true asymmetric LB/M/UB triplet.

    The sheet stores each isotope as its own block of columns, with
    labels split across two header rows (a merged-cell layout): the
    isotope name and most column labels sit on the block's first row,
    while 'Step'/'Temp'/'Minutes'/'Seconds' are two rows below it, and
    the 34 step rows start immediately after that. A trailing 'Rest'
    summary row follows each block and is dropped. Columns are therefore
    picked by position rather than parsed from the sheet, and given
    clean names here.

    Returns {'3': df, '4': df}, each with columns 'Temp (C)', 'Minutes',
    'He Corrected' (pccSTP for 3He, nccSTP for 4He), 'Fi+1', '10000/TK',
    'ln(d/a^2)'. If sheet_name is the default 'M' sheet, an additional
    'ln(d/a^2) 2 sigma' column is attached, derived as the symmetric
    half-width (UB - LB) / 2 of the explicit bounds, purely so that older
    callers expecting a single symmetric error term keep working. New
    code that wants the true asymmetric bounds should call
    load_diffusivities_HTWin0601b_bounds() instead."""
    sheet = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None)

    def _block(top_row, n_steps=34):
        data = sheet.iloc[top_row + 3: top_row + 3 + n_steps]
        return pd.DataFrame({
            'Temp (C)': data[1].astype(float).to_numpy(),
            'Minutes': data[2].astype(float).to_numpy(),
            'He Corrected': data[3].astype(float).to_numpy(),
            'Fi+1': data[8].astype(float).to_numpy(),
            '10000/TK': data[14].astype(float).to_numpy(),
            'ln(d/a^2)': data[15].astype(float).to_numpy(),
        })

    result = {'3': _block(0), '4': _block(42)}

    if sheet_name == 'diffusivitiesHTWin0601bM':
        try:
            lb = load_diffusivities_HTWin0601b(xlsx_path, 'diffusivitiesHTWin0601bLB')
            ub = load_diffusivities_HTWin0601b(xlsx_path, 'diffusivitiesHTWin0601bUB')
            for iso in ('3', '4'):
                result[iso]['ln(d/a^2) 2 sigma'] = (
                    (ub[iso]['ln(d/a^2)'].to_numpy() - lb[iso]['ln(d/a^2)'].to_numpy()) / 2
                )
                result[iso]['He Corrected 2 sigma'] = (
                    (ub[iso]['He Corrected'].to_numpy() - lb[iso]['He Corrected'].to_numpy()) / 2
                )
        except Exception:
            pass

    return result


def load_diffusivities_HTWin0601b_bounds(xlsx_path):
    """Read the central (M), upper-bound (UB), and lower-bound (LB)
    "treatment as uncertainty" reductions together.

    Returns {'3': {'M': df, 'LB': df, 'UB': df}, '4': {...}}, where each
    df has the same columns as load_diffusivities_HTWin0601b's return
    value (Temp (C), Minutes, He Corrected, Fi+1, 10000/TK, ln(d/a^2)).
    Row i is the same experimental step across all three of M/LB/UB, so
    asymmetric bounds can be read off directly by isotope and row.
    """
    out = {'3': {}, '4': {}}
    for tag, sheet in [('M', 'diffusivitiesHTWin0601bM'),
                       ('LB', 'diffusivitiesHTWin0601bLB'),
                       ('UB', 'diffusivitiesHTWin0601bUB')]:
        d = load_diffusivities_HTWin0601b(xlsx_path, sheet)
        for iso in ('3', '4'):
            out[iso][tag] = d[iso]
    return out


def load_diffusivities_HTWin0601b_naive(xlsx_path, exclude_steps=(11, 12)):
    """Read the 3He step-heat diffusivity reduction for HT-Win-06-01b from
    the master workbook's 'diffusivitiesHTWin0601bNaive' sheet: D/a^2 (and
    its own directly-propagated 2-sigma uncertainty) computed from the
    na\"ive/informed bracketing (permeation-step) method's n_t/n_0 values,
    as opposed to the UB/LB/M "treatment as uncertainty" bounds read by
    load_diffusivities_HTWin0601b_bounds(). This is the direct-measurement
    counterpart used to check the bounding-method Stage 1 regression
    (\\S\\ref{sec:discussion-bounding-direct} in the manuscript).

    Only 3He is returned: 4He permeation-step signals were blank-level
    throughout the experiment, so 4He is reduced exclusively by the
    bounding method and has no naive-method diffusivity counterpart (the
    workbook sheet's own 4He block, present for internal bookkeeping only,
    is not read here for that reason).

    exclude_steps drops steps 11 and 12 (Temp/Minutes 195/1106 and
    185/740) by default. Those two steps' n_0 values were the only ones in
    the experiment determined across the He30413/He30418 permeation
    sequence, which cooled to room temperature and continued permeating
    for far longer than the ~26-minute cooling window used for every other
    step in the dataset, and so needed a separate, one-off room-temperature
    permeability (a "long cool" correction) not used anywhere else in this
    reduction. Rather than mix a differently-derived correction into an
    otherwise uniform dataset, these two steps are dropped; pass
    exclude_steps=() to include them.

    Returns a dict {'3': df} with the same columns as
    load_diffusivities_HTWin0601b (Temp (C), Minutes, He Corrected, Fi+1,
    10000/TK, ln(d/a^2), ln(d/a^2) 2 sigma), so it drops in with
    fit_reference_line() and the existing Arrhenius-plot helpers. 'He
    Corrected' here is the na\"ive/informed-bracketing-derived n_t, not the
    raw measured value used by the bounding-method sheets."""
    sheet = pd.read_excel(xlsx_path, sheet_name='diffusivitiesHTWin0601bNaive', header=None)
    data = sheet.iloc[3: 3 + 34]

    step = data[0].astype(float).to_numpy()
    temp_C = data[1].astype(float).to_numpy()
    d_a2 = data[17].astype(float).to_numpy()
    d_a2_2sig = data[18].astype(float).to_numpy()

    df = pd.DataFrame({
        'Temp (C)': temp_C,
        'Minutes': data[2].astype(float).to_numpy(),
        'He Corrected': data[3].astype(float).to_numpy(),
        'Fi+1': data[8].astype(float).to_numpy(),
        '10000/TK': 10000.0 / (temp_C + 273.0),
        'ln(d/a^2)': np.log(d_a2),
        'ln(d/a^2) 2 sigma': d_a2_2sig / d_a2,
    })

    if exclude_steps:
        df = df[~np.isin(step, exclude_steps)].reset_index(drop=True)

    return {'3': df}


def low_signal_HTWin0601b_mask(xlsx_path, threshold=0.1):
    """Boolean mask (34 steps, same row order as load_diffusivities_HTWin0601b_bounds's
    per-isotope dataframes) flagging HT-Win-06-01b step-heat analyses whose
    measured 3He signal is too low (< threshold pccSTP) for a reliable
    diffusivity or isotope-ratio determination, e.g. Temp/Minutes 205/520,
    195/1106, 185/740, 175/920, 200/260, and 210/520 at the default 0.1
    pccSTP threshold. Read from the master workbook's
    DistilledUncertaintyTreatment sheet ('3He Measured (pccSTP)' column),
    which shares the same step order as the diffusivitiesHTWin0601b{M,UB,LB}
    sheets (verified by Temp/Minutes match) but is not itself split by bound,
    so this one mask applies to all three.

    True = low-signal (exclude); use `~mask` to select the reliable steps."""
    sheet = pd.read_excel(xlsx_path, sheet_name='DistilledUncertaintyTreatment', header=0)
    sheet = sheet[pd.to_numeric(sheet.iloc[:, 0], errors='coerce').notna()]
    he3_measured = pd.to_numeric(sheet.iloc[:, 3], errors='coerce').to_numpy()
    return he3_measured < threshold


def asymmetric_yerr(bounds, iso, column='ln(d/a^2)'):
    """Build a matplotlib-ready asymmetric yerr array (2, N) -- distances
    below and above the central value -- from a load_diffusivities_HTWin0601b_bounds()
    result for one isotope and one column. Negative spans (which
    shouldn't occur once the LB/UB bug is fixed, but are clipped
    defensively) are floored at 0."""
    m = bounds[iso]['M'][column].to_numpy()
    lb = bounds[iso]['LB'][column].to_numpy()
    ub = bounds[iso]['UB'][column].to_numpy()
    lower = np.clip(m - lb, 0, None)
    upper = np.clip(ub - m, 0, None)
    return np.vstack([lower, upper])


def fit_reference_line(temp_C, ln_D_a2, frac_yield, threshold=0.07):
    """Fit a Stage-1-style Arrhenius reference line (ln(D/a^2) vs 10000/T)
    to the high-cumulative-yield tail of a step-heat dataset, selected
    reproducibly by a fractional-yield threshold (default: the last
    steps with cumulative fractional yield >= 7%, matching the plateau
    used historically for Win-06-01b-HT) rather than a hardcoded row
    count, so the fit re-derives itself if the underlying data changes.

    Returns a dict: slope, intercept (of ln(D/a^2) vs 10000/T), r2,
    n_points, Ea_cal_mol, D0_a2 (so callers can reconstitute
    D0_a2 * exp(-Ea / (R T)) if preferred over the linear form), plus
    1-sigma standard errors slope_stderr, intercept_stderr (both directly
    from scipy.stats.linregress) and their propagated equivalents
    Ea_cal_mol_stderr, D0_a2_stderr. D0_a2 = exp(intercept) so its
    stderr uses the standard delta-method approximation
    D0_a2 * intercept_stderr; like the point estimates themselves, this
    ignores the slope/intercept covariance, so treat Ea and D0 stderrs
    as marginal, not jointly consistent, uncertainties. Ea_kJ_mol and
    Ea_kJ_mol_stderr are the same Ea_cal_mol/Ea_cal_mol_stderr values
    converted via the thermochemical calorie (1 cal = 4.184 J), included
    for convenience since the dissertation text reports Ea in kJ/mol.
    """
    import scipy.stats

    temp_C = np.asarray(temp_C, dtype=float)
    ln_D_a2 = np.asarray(ln_D_a2, dtype=float)
    frac_yield = np.asarray(frac_yield, dtype=float)

    mask = np.isfinite(temp_C) & np.isfinite(ln_D_a2) & np.isfinite(frac_yield) & (frac_yield >= threshold)
    if mask.sum() < 2:
        raise ValueError(f"Fewer than 2 points at or above fractional-yield threshold {threshold}")

    x = 10000.0 / (temp_C[mask] + 273.0)
    y = ln_D_a2[mask]
    fit = scipy.stats.linregress(x, y)

    R = 1.987  # cal/(mol K)
    CAL_TO_J = 4.184
    Ea_cal_mol = -fit.slope * 10000.0 * R
    D0_a2 = np.exp(fit.intercept)
    Ea_cal_mol_stderr = fit.stderr * 10000.0 * R
    D0_a2_stderr = D0_a2 * fit.intercept_stderr

    return dict(slope=float(fit.slope), intercept=float(fit.intercept),
                r2=float(fit.rvalue ** 2), n_points=int(mask.sum()),
                Ea_cal_mol=float(Ea_cal_mol), D0_a2=float(D0_a2),
                slope_stderr=float(fit.stderr), intercept_stderr=float(fit.intercept_stderr),
                Ea_cal_mol_stderr=float(Ea_cal_mol_stderr), D0_a2_stderr=float(D0_a2_stderr),
                Ea_kJ_mol=float(Ea_cal_mol * CAL_TO_J / 1000.0),
                Ea_kJ_mol_stderr=float(Ea_cal_mol_stderr * CAL_TO_J / 1000.0),
                threshold=float(threshold))


def dodson_closure_temperature(Ea_cal_mol, D0_a2, cooling_rate_C_per_Myr, A=55.0,
                                T_guess_K=346.0, tol=1e-9, max_iter=200):
    """Dodson (1973) closure temperature, solved by fixed-point iteration
    of Tc = (Ea/R) / ln(A*R*Tc^2*(D0/a^2) / (Ea*dT/dt)) until Tc changes
    by less than tol (K) between iterations, starting from T_guess_K.

    Reproduces the calculation done by hand in the master workbook's
    diffusivitiesHTWin0601bM sheet (cells Z26:AD35) -- validated against
    it: that sheet's two manual iterations from a 346 K guess (Ea =
    38145.7 cal/mol, D0/a2 = 1.821e7 /s, A=55, 10 C/Myr) give Tc = 99.84
    degC; iterating to convergence here gives 99.87 degC, i.e. the two
    manual steps were already almost fully converged.

    Parameters
    ----------
    Ea_cal_mol, D0_a2 : activation energy (cal/mol) and D0/a^2 (1/s), e.g.
        from fit_reference_line()'s output.
    cooling_rate_C_per_Myr : cooling rate dT/dt, in degC per Myr (matches
        the workbook's convention; converted internally to K/s).
    A : dimensionless geometry factor (Dodson 1973): 55 for a sphere
        (the workbook's value, and the default here), 27 for a cylinder,
        8.7 for a plane sheet.
    T_guess_K : starting guess for the iteration (K); the fixed point is
        insensitive to this for any physically reasonable starting value.

    Returns
    -------
    Tc_C : closure temperature in degrees C.
    """
    R = 1.987  # cal/(mol K)
    dTdt_K_per_s = cooling_rate_C_per_Myr / (1e6 * 365 * 24 * 60 * 60)

    Tc = float(T_guess_K)
    for _ in range(max_iter):
        Tc_new = (Ea_cal_mol / R) / np.log(A * R * Tc ** 2 * D0_a2 / (Ea_cal_mol * dTdt_K_per_s))
        if abs(Tc_new - Tc) < tol:
            Tc = Tc_new
            break
        Tc = Tc_new
    else:
        raise RuntimeError(f"dodson_closure_temperature did not converge after {max_iter} iterations")

    return Tc - 273.0


def dodson_closure_temperature_stderr(Ea_cal_mol, D0_a2, Ea_cal_mol_stderr, D0_a2_stderr,
                                       cooling_rate_C_per_Myr, A=55.0, T_guess_K=346.0,
                                       rel_step=1e-4):
    """1-sigma standard error on dodson_closure_temperature(), propagated from
    Ea_cal_mol_stderr and D0_a2_stderr (e.g. fit_reference_line()'s
    Ea_cal_mol_stderr, D0_a2_stderr) via the delta method: dTc/dEa and
    dTc/dD0_a2 are estimated by central finite differences of
    dodson_closure_temperature() itself (Tc has no closed form in Ea,
    D0_a2, so this differentiates the numerical solver rather than an
    algebraic derivative), then combined in quadrature. Like the Ea/D0
    stderrs it consumes, this ignores their mutual covariance, so treat
    the result as a marginal, not jointly consistent, uncertainty -- and
    note it's a genuinely different quantity from the LB/UB bound-to-bound
    spread, which instead reflects differences in data-reduction
    treatment, not the regression's own statistical uncertainty.
    """
    dEa = Ea_cal_mol * rel_step
    dTc_dEa = (dodson_closure_temperature(Ea_cal_mol + dEa, D0_a2, cooling_rate_C_per_Myr, A, T_guess_K)
               - dodson_closure_temperature(Ea_cal_mol - dEa, D0_a2, cooling_rate_C_per_Myr, A, T_guess_K)) / (2 * dEa)

    dD0 = D0_a2 * rel_step
    dTc_dD0 = (dodson_closure_temperature(Ea_cal_mol, D0_a2 + dD0, cooling_rate_C_per_Myr, A, T_guess_K)
               - dodson_closure_temperature(Ea_cal_mol, D0_a2 - dD0, cooling_rate_C_per_Myr, A, T_guess_K)) / (2 * dD0)

    return float(np.hypot(dTc_dEa * Ea_cal_mol_stderr, dTc_dD0 * D0_a2_stderr))


def dodson_closure_temperature_stderr_interceptonly(Ea_cal_mol, D0_a2, D0_a2_stderr,
                                                      cooling_rate_C_per_Myr, A=55.0, T_guess_K=346.0,
                                                      rel_step=1e-4):
    """1-sigma standard error on dodson_closure_temperature(), considering
    ONLY the uncertainty in D0_a2 (the regression intercept term) and
    holding Ea_cal_mol (the slope term) fixed at its central value --
    i.e. the simplified sensitivity manuscript text describes ("considering
    only uncertainty in the intercept (D0/a^2) term"), as distinct from
    dodson_closure_temperature_stderr()'s full joint slope+intercept
    propagation. Uses the same delta-method finite-difference approach
    (differentiating the numerical Dodson solver) restricted to the
    D0_a2 direction only.
    """
    dD0 = D0_a2 * rel_step
    dTc_dD0 = (dodson_closure_temperature(Ea_cal_mol, D0_a2 + dD0, cooling_rate_C_per_Myr, A, T_guess_K)
               - dodson_closure_temperature(Ea_cal_mol, D0_a2 - dD0, cooling_rate_C_per_Myr, A, T_guess_K)) / (2 * dD0)

    return float(abs(dTc_dD0 * D0_a2_stderr))


def load_stage1_cache(cache_path=None):
    """Load the Stage 1 reference-line regression cache written by
    prepare_regression_cache.py. Returns {'M': {...}, 'LB': {...}, 'UB': {...},
    'naive': {...}, 'fractional_yield_threshold': ..., 'isotope': '3He'}, each
    of the M/LB/UB/naive entries having the same keys as fit_reference_line()'s
    return value (slope, intercept, r2, n_points, Ea_cal_mol, D0_a2,
    slope_stderr, intercept_stderr, Ea_cal_mol_stderr, D0_a2_stderr,
    Ea_kJ_mol, Ea_kJ_mol_stderr, Tc_C -- see dodson_closure_temperature()).
    'naive' is the na\"ive/informed bracketing (permeation-step) method's own
    fit (no LB/UB split; see load_diffusivities_HTWin0601b_naive), the
    direct-measurement check on the M/LB/UB bounding-method fits.

    Raises FileNotFoundError with a clear message if the cache hasn't
    been generated yet -- run prepare_regression_cache.py first."""
    import json
    if cache_path is None:
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated', 'data', 'stage1_regression_cache.json')
    if not os.path.exists(cache_path):
        raise FileNotFoundError(
            f"{cache_path} not found -- run prepare_regression_cache.py first "
            "to derive and cache the Stage 1 reference line.")
    with open(cache_path) as f:
        return json.load(f)


def D_a2_from_fit(fit):
    """Return a D/a^2(T) closure (T in Kelvin) from a fit_reference_line()-style
    dict (as stored per-bound in the Stage 1 cache)."""
    D0_a2 = fit['D0_a2']
    Ea = fit['Ea_cal_mol']
    R = 1.987
    return lambda T: D0_a2 * np.exp(-Ea / (R * np.asarray(T, dtype=float)))


# ---------------------------------------------------------------------------
# Nonfunc helper (returns constant function)
# ---------------------------------------------------------------------------

class Nonfunc:
    """Callable that returns a constant value broadcast to the shape of its argument."""
    def __init__(self, value):
        self.v = value

    def __call__(self, vec=1):
        return np.ones_like(np.asarray(vec, dtype=float)) * self.v


# ---------------------------------------------------------------------------
# MC He Mass-Spectrometer Sensitivity Reducer
# ---------------------------------------------------------------------------

class MCHeReducer:
    """Maps raw MC signals to He abundances using bracketing standards.

    STD_name: CSV file with standard analyses (same format as MC output).
    STD4 = 157.50 nccSTP 4He, STD3 = 3.57 pccSTP 3He assumed for all standards.
    """
    STD4 = 157.50   # nccSTP
    STD3 = 3.57     # pccSTP

    def __init__(self, STD_name):
        self.std = pd.read_csv(STD_name, header=None).to_numpy()
        seen = set()
        clean = []
        for z, row in enumerate(self.std):
            if row[0] not in seen:
                seen.add(row[0])
                clean.append(z)
        self.std = self.std[clean]
        self.t0 = _parse_time(self.std[0, 2])
        self.Dt = np.append(0, extract_times_from0(self.std[:, 2]))
        order = np.argsort(self.Dt)
        self.std = self.std[order]
        self.Dt = self.Dt[order]
        self.sens4 = self.STD4 / self.std[:, 6].astype(float)
        self.sens3 = self.STD3 / self.std[:, 4].astype(float)
        self.x = np.linspace(0, self.Dt[-1], 2000)
        inds = np.arange(len(self.sens4))
        self.sigma4 = [np.std(self.sens4[np.argsort(np.abs(inds - i))][:5]) for i in inds]
        self.sigma3 = [np.std(self.sens3[np.argsort(np.abs(inds - i))][:5]) for i in inds]
        self.model4 = scipy.interpolate.pchip_interpolate(self.Dt, self.sens4, self.x)
        self.model3 = scipy.interpolate.pchip_interpolate(self.Dt, self.sens3, self.x)
        self.model4sigma = scipy.interpolate.pchip_interpolate(self.Dt, self.sigma4, self.x)
        self.model3sigma = scipy.interpolate.pchip_interpolate(self.Dt, self.sigma3, self.x)

    def reduce(self, DIFFCELL, form='%m/%d/%Y  %I:%M %p',
               plot=False, sens_out=False, uncertainties=False):
        self.analyses = DIFFCELL
        self.AnalDT = extract_times_from0(
            np.append(self.t0.strftime(form), self.analyses[:, 2]))
        self.sensIND = np.array([np.argmin(np.abs(self.x - tim))
                                 for tim in self.AnalDT])
        self.Anal3He = (self.model3[self.sensIND]
                        * self.analyses[:, 4].astype(float))
        self.Anal4He = (self.model4[self.sensIND]
                        * self.analyses[:, 6].astype(float))
        out = [self.Anal3He, self.Anal4He]
        if uncertainties:
            out += [
                self.Anal3He * (self.model3sigma[self.sensIND]
                                / self.model3[self.sensIND]),
                self.Anal4He * (self.model4sigma[self.sensIND]
                                / self.model4[self.sensIND]),
            ]
        if sens_out:
            out += [self.model3[self.sensIND], self.model4[self.sensIND]]
        return out


# ---------------------------------------------------------------------------
# Plotting helper
# ---------------------------------------------------------------------------

def make_grid(minors=True):
    """Add light major/minor gridlines to the current axes."""
    ax = plt.gca()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_coords = [xt.get_position()[0] for xt in ax.get_xticklabels()[1:-1]]
    y_coords = [yt.get_position()[1] for yt in ax.get_yticklabels()[1:-1]]
    if minors:
        plt.vlines(ax.get_xticks(minor=True), *ylim, linestyle='-', color='black', alpha=0.05)
        plt.hlines(ax.get_yticks(minor=True), *xlim, linestyle='-', color='black', alpha=0.05)
    plt.vlines(x_coords, *ylim, linestyle='--', color='black', alpha=0.2)
    plt.hlines(y_coords, *xlim, linestyle='--', color='black', alpha=0.2)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
