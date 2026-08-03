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

def He_forward(U_mol, Th_mol, Sm_mol, t):
    """He produced (nccSTP) from U/Th/Sm in moles after time t in years."""
    U_at = U_mol * Av
    Th_at = Th_mol * Av
    Sm_at = Sm_mol * Av
    He_at = (
        8 * (1 - 1 / 137.88) * U_at * (np.exp(lam_U238 * t) - 1)
        + 7 * (U_at / 137.88) * (np.exp(lam_U235 * t) - 1)
        + 6 * Th_at * (np.exp(lam_Th232 * t) - 1)
        + Sm_at * Formula('Sm').spectrum()[147][1] * (np.exp(lam_Sm147 * t) - 1)
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
        + Sm_at * Formula('Sm').spectrum()[147][1] * lam_Sm147 * np.exp(lam_Sm147 * t)
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
    R: grain radius (µm), S: stopping distances array (µm, length 4),
    X: [U, Th, Sm] abundances (atoms or moles)."""
    total = 8 * X[0] + 7 * X[0] / 137.88 + 6 * X[1] + X[2]
    weights = np.array([8 * X[0], 7 * X[0] / 137.88, 6 * X[1],
                        Formula('Sm').spectrum()[147][1] * X[2]]) / total
    fts = 1 - (3 / 4) * (S / R) + (1 / 16) * (S / R) ** 3
    return np.sum(fts * weights)


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
