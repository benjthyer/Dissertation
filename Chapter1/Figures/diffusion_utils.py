"""
Core utility functions, constants, and classes for helium diffusion simulations.
Ben Thyer, 2023–2025
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import scipy
import os
from datetime import datetime
from tqdm.auto import tqdm

Rcal = 1.987
Ratoms = 1.3621E-22


# ---------------------------------------------------------------------------
# Silica glass transport properties
# ---------------------------------------------------------------------------

def swets(L, T):
    """Returns permeability (K), diffusivity (D), or solubility (S) of fused
    silica for helium.  L in {'D','S','K'}, T in Kelvin.
    Units: mol/cm/s/atm (K), cm^2/s (D), atoms/cc/atm (S)."""
    if T >= 600:
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


def swets_K(T):
    """Permeability of fused silica, atoms·cm/s/atm.  T in Kelvin."""
    return swets('K', T)


def swets_S(T):
    """Solubility of helium in fused silica, atoms/cc/atm.  T in Kelvin."""
    if T >= 574:
        DEa, SEa, DFF, SFF = 6613, -1174, 7.40E-4, 1.28E17
    else:
        DEa, SEa, DFF, SFF = 5580, -680, 3.04E-4, 1.99E17
    D = DFF * np.exp(-DEa / (Rcal * T))
    S = SFF * np.exp(-SEa / (Rcal * T))
    return S


def swets_D(T):
    """Diffusivity of helium in fused silica, cm^2/s.  T in Kelvin."""
    if T >= 573:
        DEa, DFF = 6613, 7.40E-4
    else:
        DEa, DFF = 5580, 3.04E-4
    return DFF * np.exp(-DEa / (Rcal * T))


def Jones(L, T):
    """3He vs 4He correction factors for silica (Jones et al.).
    L in {'K','S','D'}, T in Kelvin."""
    tag = L.upper()
    if tag == 'K':
        return 1.17 * np.exp(-57 / (Rcal * T))
    if tag == 'S':
        return 1.003 * np.exp(-6 / (Rcal * T))
    if tag == 'D':
        return 1.167 * np.exp(-51 / (Rcal * T))
    raise ValueError("L must be one of 'D', 'S', 'K'")


def tube_permeate2(T, t, ID, OD):
    """Fractional He remaining after time t in a silica tube.
    Lengths in cm (inner/outer diameter), T in Kelvin, t in seconds.
    Returns n/n0."""
    K = swets_K(T)
    return np.exp(-(K * Ratoms * T * 2 * t) / (np.log(OD / ID) * ((ID / 2) ** 2)))


# ---------------------------------------------------------------------------
# Fechtig & Kalbitzer (1966) diffusion inversion / forward model
# ---------------------------------------------------------------------------

def Forward_Diffuse(Dt_a2):
    """Cumulative fractional yield F for a given Dt/a^2.
    Eqns 4a-c, Fechtig & Kalbitzer 1966."""
    Bt = np.pi ** 2 * Dt_a2
    F = (6 / np.pi ** 1.5) * Bt ** 0.5          # small-yield approx
    if F > 0.1:
        F = 1 - (6 / np.pi ** 2) * np.exp(-Bt)  # high-yield approx
    if F < 0.9:
        F = (6 / np.pi ** 1.5) * Bt ** 0.5 - (3 / np.pi ** 2) * Bt  # mid
    return F


def Forward_Diffuse_deriv(t, D, a):
    """Cumulative yield and dF/dt.  Eqns 4a-c, Fechtig & Kalbitzer 1966."""
    Bt = np.pi ** 2 * D * t / (a ** 2)
    F = (6 / np.pi ** 1.5) * Bt ** 0.5
    dfdt = (6 / np.pi ** 1.5) * 0.5 * t ** (-0.5) * ((np.pi ** 2 * D / a ** 2) ** 0.5)
    if F > 0.1:
        F = 1 - (6 / np.pi ** 2) * np.exp(-Bt)
        dfdt = (6 / np.pi ** 2) * np.exp(-Bt)
    if F < 0.9:
        F = (6 / np.pi ** 1.5) * Bt ** 0.5 - (3 / np.pi ** 2) * Bt
        dfdt = ((6 / np.pi ** 1.5) * 0.5 * t ** (-0.5) * ((np.pi ** 2 * D / a ** 2) ** 0.5)
                - np.pi ** 2 * D / a ** 2)
    return F, dfdt


def InvertFrequencyFactor(t, F, Fp):
    """Single-step D/a^2 inversion.  t in seconds, F and Fp cumulative yields.
    Eqns 5a-c, Fechtig & Kalbitzer 1966."""
    if F <= 0.1:
        return ((F ** 2 - Fp ** 2) * np.pi) / (36 * t)
    elif F < 0.9:
        return (1 / (np.pi ** 2 * t)) * (
            (-(np.pi ** 2) / 3) * (F - Fp)
            + (-2 * np.pi) * ((1 - (np.pi / 3) * F) ** 0.5
                              - (1 - (np.pi / 3) * Fp) ** 0.5)
        )
    elif F <= 1:
        return (1 / (np.pi ** 2 * t)) * np.log((1 - Fp) / (1 - F))
    else:
        raise ValueError('F must be within 0–1')


def InvertFrequencyFactor1(ts, Fs):
    """Vector version of InvertFrequencyFactor.  Returns list of D/a^2."""
    Fs = np.array(Fs)
    Fps = np.array([0] + Fs[:-1].tolist())
    return [InvertFrequencyFactor(t=ts[i], F=Fs[i], Fp=Fps[i]) for i in range(len(Fs))]


def Simulate_Diffusion(D0_a2, Ea, T, t, R=8.314):
    """Forward diffusion model.  Returns cumulative fractional yield array.
    T in °C, t in minutes, D0_a2 in s^-1, Ea in J/mol."""
    if np.shape(T) != np.shape(t) or T.ndim != 1:
        raise ValueError('T and t must be 1-D arrays of equal length')
    Dt_a2 = 0
    Fcum = []
    seconds = t * 60
    for i, sec in enumerate(seconds):
        K = 273 + T[i]
        Dt_a2 += D0_a2 * np.exp(-Ea / (R * K)) * sec
        Fcum.append(Forward_Diffuse(Dt_a2))
    return Fcum


def Simulate_MDD_diffusion(D0, Ea, T, t, a, v, R=8.314):
    """Multi-domain diffusion forward model.
    D0 in cm^2/s, a in cm (radii array), v = fractional volumes, T in °C, t in min."""
    if np.shape(a) != np.shape(v) or a.ndim != 1:
        raise ValueError('a and v must be 1-D arrays of equal length')
    if np.shape(T) != np.shape(t) or T.ndim != 1:
        raise ValueError('T and t must be 1-D arrays of equal length')
    old_sum = np.sum(v)
    v_new = v / old_sum if old_sum != 1 else v
    D0_a2 = D0 / (a ** 2)
    Fcum_array = np.zeros((len(T), len(a)))
    for col, domain in enumerate(D0_a2):
        Fcum_array[:, col] = Simulate_Diffusion(domain, Ea, T, t, R)
    return np.sum(Fcum_array * v_new.reshape(1, -1), axis=1)


def GaussianPDF(sigma):
    return (1 / (2 * np.pi)) * np.exp(-0.5 * sigma ** 2)


# ---------------------------------------------------------------------------
# Helium age / partial retention
# ---------------------------------------------------------------------------

def wolfEQ(t, D_a2):
    """Helium age (years) given isothermal holding time t (years) and D/a^2 (s^-1),
    accounting for concomitant production and diffusive loss."""
    ts = t * (365.25 * 24 * 3600)
    sumterm = sum(
        (6 / (np.pi ** 4 * n ** 4)) * np.exp(-(n ** 2) * np.pi ** 2 * ts * D_a2)
        for n in np.arange(255) + 1
    )
    age = ((D_a2 ** -1) * (1 / 15 - sumterm)) / (365.25 * 24 * 3600)
    return min(age, t)


# ---------------------------------------------------------------------------
# First-order (Single Jump Model) kinetics
# ---------------------------------------------------------------------------

def Forward_SJM(k0, Ea, T, t, R=8.314):
    """First-order Single Jump Model.  Returns residual fraction array.
    T in °C, t in seconds, k0 in s^-1."""
    if np.shape(T) != np.shape(t) or T.ndim != 1:
        raise ValueError('T and t must be 1-D arrays of equal length')
    F = [1]
    for i, sec in enumerate(t):
        K = T[i] + 273
        d = k0 * np.exp(-Ea / (R * K))
        F.append(F[-1] * np.exp(-d * sec))
    return F


# ---------------------------------------------------------------------------
# Tube-encapsulated-mineral forward models
# ---------------------------------------------------------------------------

def Simulate_Diffusion_Tube(D0, a, Ea, T, t, OD, ID, R=1.987):
    """Forward model for a mineral grain diffusing He into a silica tube.
    T in °C, t in seconds, D0 in cm^2/s, a = grain radius in cm,
    OD/ID = tube outer/inner diameter in cm.
    Returns (Fcum, n0, Fstep_apparent, Fcum_apparent, n0_ends, t_out, temps, Fsteps)."""
    G = 2 / (np.log(OD / ID) * ((ID / 2) ** 2))
    n0, n0_ends, Fstep_apparent, Fcum, Fcum_apparent = [], [], [], [], []
    Fcum_apparentP = 0
    FP = 0
    Dt_a2 = 0
    n0P = 0
    t_out, t_outP = [], 0
    temps, Fsteps = [], []

    for j, tstep in enumerate(t):
        Tk = T[j] + 273
        D = D0 * np.exp(-Ea / (R * Tk))
        outF = 0
        for _ in np.arange(tstep):
            Dt_a2 += D / (a ** 2)
            F_step = Forward_Diffuse(Dt_a2) - FP
            n0.append(F_step + n0P)
            FP += F_step
            Fcum.append(FP)
            n_n0 = tube_permeate2(T=Tk, t=1, ID=ID, OD=OD)
            out = n0[-1] * (1 - n_n0)
            n0[-1] -= out
            outF += out
            Fsteps.append(out)
            n0P = n0[-1]
            temps.append(Tk)
        n0_ends.append(n0P)
        Fstep_apparent.append(outF)
        Fcum_apparent.append(outF + Fcum_apparentP)
        Fcum_apparentP = Fcum_apparent[-1]
        t_out.append(t_outP + tstep)
        t_outP = t_out[-1]

    return Fcum, n0, Fstep_apparent, Fcum_apparent, n0_ends, t_out, temps, Fsteps


def Simulate_Diffusion_Tube_P(P, T, t, OD, ID, R=1.987):
    """Like Simulate_Diffusion_Tube but with prescribed per-step He release rates P."""
    G = 2 / (np.log(OD / ID) * ((ID / 2) ** 2))
    n0, n0_ends, Fstep_apparent, Fcum, Fcum_apparent = [], [], [], [], []
    Fcum_apparentP = 0
    FP = 0
    n0P = 0
    t_out, t_outP = [], 0
    temps, Fsteps = [], []

    for j, tstep in enumerate(t):
        Tk = T[j] + 273
        outF = 0
        F_step = P[j]
        for _ in np.arange(tstep):
            n0.append(F_step + n0P)
            FP += F_step
            Fcum.append(FP)
            n_n0 = tube_permeate2(T=Tk, t=1, ID=ID, OD=OD)
            out = n0[-1] * (1 - n_n0)
            n0[-1] -= out
            outF += out
            Fsteps.append(out)
            n0P = n0[-1]
            temps.append(Tk)
        n0_ends.append(n0P)
        Fstep_apparent.append(outF)
        Fcum_apparent.append(outF + Fcum_apparentP)
        Fcum_apparentP = Fcum_apparent[-1]
        t_out.append(t_outP + tstep)
        t_outP = t_out[-1]

    return Fcum, n0, Fstep_apparent, Fcum_apparent, n0_ends, t_out, temps, Fsteps


# ---------------------------------------------------------------------------
# Finite-difference concentration profile models
# ---------------------------------------------------------------------------

def tube_FDM(T1, T2, x):
    """Planar-slab FDM diffusion profile in silica glass.
    T1/T2 in °C (initial/final), x = slab thickness in cm.
    Plots Fo snapshots; call plt.savefig() afterwards."""
    Fos = [0.01, 0.1, 1]
    colors = ['Red', 'Orange', 'Green', 'Blue', 'Violet']
    D = swets('D', T2 + 273)
    S2 = swets('S', T2 + 273)
    dx = 1 / 1E4
    dt = 0.5 * dx ** 2 / D
    xi = np.arange(0, x, dx)
    c_inner = S2 * Ratoms * (T2 + 273)

    t_stops = sorted([(Fo * xi[-1] ** 2) / D for Fo in Fos])
    t_stop = t_stops.pop(0)

    if isinstance(T1, (int, float)):
        S1 = swets('S', T1 + 273)
        c1 = S1 * Ratoms * (T1 + 273)
        c = (xi / xi[-1]) * c1
    else:
        c = np.zeros_like(xi)
        c1 = 0

    plt.plot(xi * 1E4, c, linestyle='--', color='Black', label='t = 0 min', alpha=0.5)
    c[-1] = c_inner
    current_t = 0
    steps = 0
    color_count = 0
    delta_c = (D * dt / dx ** 2) * (c[:-2] - 2 * c[1:-1] + c[2:])
    while t_stops or t_stop:
        steps += 1
        current_t += dt
        c[1:-1] += delta_c
        c[0] = 0
        c[-1] = c_inner
        delta_c = (D * dt / dx ** 2) * (c[:-2] - 2 * c[1:-1] + c[2:])
        if current_t >= t_stop:
            plt.plot(xi * 1E4, c, color=colors[color_count], linewidth=2,
                     label=f'Fo = {Fos[color_count]}, t = {round(current_t / 60, 1)} min')
            if t_stops:
                t_stop = t_stops.pop(0)
            else:
                break
            color_count += 1
    plt.plot(xi * 1E4, (xi / xi[-1]) * c_inner, linestyle=':', color='Black',
             label=f'EQM for T = {T2}°C', alpha=0.8)
    plt.xlabel('Distance from Vacuum (µm)')
    plt.ylabel('He Concentration (atoms/mL)')
    plt.title(f'He Concentration Profile at {T2}°C')
    plt.legend()


def tube_cylinder_FDM(T1, T2, a, b):
    """Cylindrical FDM diffusion profile in a silica ampoule.
    T1/T2 in °C, a/b = inner/outer radius in cm."""
    Fos = [0.01, 0.1, 1]
    colors = ['Red', 'Orange', 'Green', 'Blue', 'Violet']
    D = swets('D', T2 + 273)
    S2 = swets('S', T2 + 273)
    dr = (b - a) / 100
    dt = 0.5 * dr ** 2 / D
    r = np.arange(a, b + dr, dr)
    ngas = 100
    h = 1
    c2 = (S2 * ngas * Ratoms * (T2 + 273) / (np.pi * a ** 2 * h)) * (np.log(r / b) / np.log(a / b))
    c_inner = S2 * ngas * Ratoms * (T2 + 273) / (np.pi * a ** 2 * h)

    t_stops = sorted([(Fo * (b - a) ** 2) / D for Fo in Fos])
    t_stop = t_stops.pop(0)

    if isinstance(T1, (int, float)):
        S1 = swets('S', T1 + 273)
        c = (S1 * ngas * Ratoms * (T1 + 273) / (np.pi * a ** 2 * h)) * (np.log(r / b) / np.log(a / b))
        c1 = c.copy()
    else:
        c = np.zeros_like(r)
        c1 = np.zeros_like(r)

    plt.plot(r * 1E4, c / (ngas / (np.pi * a ** 2 * h)), linestyle='--', color='Black',
             label=f'EQM for T = {T1}°C', alpha=0.5)
    c[0] = c_inner
    current_t = 0
    steps = 0
    color_count = 0
    firstderiv = (c[2:] - c[:-2]) / (2 * dr)
    delta_c = D * dt * ((c[:-2] - 2 * c[1:-1] + c[2:]) / dr ** 2 + (1 / r[1:-1]) * firstderiv)
    while t_stops or t_stop:
        steps += 1
        current_t += dt
        c[1:-1] += delta_c
        c[0] = c_inner
        c[-1] = 0
        firstderiv = (c[2:] - c[:-2]) / (2 * dr)
        delta_c = D * dt * ((c[:-2] - 2 * c[1:-1] + c[2:]) / dr ** 2 + (1 / r[1:-1]) * firstderiv)
        if current_t >= t_stop:
            plt.plot(r * 1E4, c / (ngas / (np.pi * a ** 2 * h)), color=colors[color_count],
                     linewidth=2, label=f'Fo = {Fos[color_count]}, t = {round(current_t / 60, 1)} min')
            if t_stops:
                t_stop = t_stops.pop(0)
            else:
                break
            color_count += 1
    plt.plot(r * 1E4, c2 / (ngas / (np.pi * a ** 2 * h)), linestyle=':', color='Black',
             label=f'EQM for T = {T2}°C', alpha=0.8)
    plt.xlabel('r (µm)')
    plt.ylabel('He Concentration Ratio (Glass/Gas)')
    plt.title(f'He Concentration Profile at {T2}°C')
    plt.legend()


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


def forward_permeate1(t, lamb, n0):
    return (n0 * (1 - np.exp(-lamb * t[1]))) - (n0 * (1 - np.exp(-lamb * t[0])))


def FirstOrdInversion(t, He, plot=False):
    """Fit exponential decay to yield time series; returns (lambda, n0)."""
    cumHe = accumulate(He)
    cumt = accumulate(t)
    lamb0 = 6E-6
    out, _ = scipy.optimize.curve_fit(forward_permeate, cumt, cumHe,
                                      p0=[lamb0, 1])
    if plot:
        longt = np.linspace(0, cumt[-1], 500)
        plt.plot(longt, forward_permeate(longt, *out))
        plt.scatter(cumt, cumHe)
    return out[0], out[1]


def KenColdInversion(t, He, covout=False, plot=True):
    """Exponential fit for cold-permeation time series; returns (lambda, n0)."""
    cumHe = accumulate(He)
    cumt = accumulate(t)
    lamb0 = 6E-5
    out, covmat = scipy.optimize.curve_fit(forward_permeate, cumt, cumHe,
                                           p0=[lamb0, He[0] / (1 - np.exp(-lamb0 * t[0]))])
    if plot:
        longt = np.linspace(0, cumt[-1], 500)
        plt.plot(longt, forward_permeate(longt, *out))
        plt.scatter(cumt, cumHe)
    if covout:
        return (out[0], out[1]), covmat
    return out[0], out[1]


def KenColdInversion1(t, He, sigma, covout=False, plot=True):
    """Like KenColdInversion but fits step-wise yields with uncertainties."""
    lamb0 = 6E-5
    cumHe = [0] + accumulate(He).tolist()
    cumt = [0] + accumulate(t).tolist()
    tinput = [[cumt[i], cumt[i + 1]] for i in range(len(cumt) - 1)]
    out, covmat = scipy.optimize.curve_fit(forward_permeate1, np.array(tinput).T, He,
                                           sigma=sigma,
                                           p0=[lamb0, He[0] / (1 - np.exp(-lamb0 * t[0]))])
    if plot:
        longt = np.linspace(0, cumt[-1], 500)
        plt.plot(longt, forward_permeate(longt, *out))
        plt.scatter(cumt, cumHe)
    if covout:
        return (out[0], out[1]), covmat
    return out[0], out[1]


# ---------------------------------------------------------------------------
# Diffusion-reduction pipeline
# ---------------------------------------------------------------------------

def diffusion_reduction(HeVec, TimeSeconds, TempKelvin=None,
                        newDiffName='manual_diffusion.csv'):
    """Compute D/a^2 inversions from a step-heating yield vector."""
    total_yield = np.sum(HeVec)
    fcum, D_a2, lnD_a2 = [], [], []
    Fp = 0
    for i, step_yield in enumerate(HeVec):
        F = Fp + step_yield / total_yield
        ff = InvertFrequencyFactor(t=TimeSeconds[i], F=F, Fp=Fp)
        D_a2.append(ff)
        lnD_a2.append(np.log(ff))
        fcum.append(F)
        Fp = F

    if TempKelvin is not None and np.sum(TempKelvin):
        data = [(TempKelvin - 273).tolist(), (TimeSeconds / 60).tolist(),
                HeVec, fcum, D_a2, lnD_a2, (10000 / TempKelvin).tolist()]
        columns = ['Temp (C)', 'Time (min)', 'He Yield (nCC@STP)', 'Fcum',
                   'D/a^2 ', 'ln(D/a^2)', '10^4/T']
        min_T = np.min(10000 / TempKelvin[:-1])
        max_T = np.max(10000 / TempKelvin[:-1])
        plt.plot(10000 / TempKelvin[:-1], np.array(lnD_a2)[:-1],
                 linestyle='--', marker='o', color='b',
                 label='Simulated Encapsulated Apatite')
        plt.title(f"Diffusivity Inversion for Total Yield = {total_yield} ncc's")
        ref_D0_a2 = [(10 ** 1.5) / ((150 / 10000) ** 2)]
        ref_Ea = [33000]
        ref_names = ['True Diffusivity of Apatite (a=150 µm)']
        R = 1.98
        for i, D0_a2 in enumerate(ref_D0_a2):
            Ea = ref_Ea[i]
            T_range = [min_T, max_T]
            lnD_min = np.log(D0_a2 * np.exp(-Ea / ((10000 / min_T) * R)))
            lnD_max = np.log(D0_a2 * np.exp(-Ea / ((10000 / max_T) * R)))
            plt.plot(T_range, [lnD_min, lnD_max], label=ref_names[i])
    else:
        data = [(TimeSeconds / 60).tolist(), HeVec, fcum, D_a2, lnD_a2]
        columns = ['Time (min)', 'He Yield (nCC@STP)', 'Fcum', 'D/a^2 ', 'ln(D/a^2)']

    df = pd.DataFrame({col: data[i] for i, col in enumerate(columns)})
    df.to_csv(newDiffName)
    return df


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def pull_number(string):
    """Extract a float from a string containing mixed characters."""
    assert isinstance(string, str)
    return float(''.join(c for c in string if c in '1234567890.'))


def extract_times_from0(dates, form='%m/%d/%Y  %I:%M %p'):
    """Convert MC timestamp strings to elapsed seconds from first entry."""
    times = []
    firsttime = None
    for stri in dates:
        for fmt in [form, '%m/%d/%Y  %H:%M:%S', '%m/%d/%Y  %H:%M',
                    '%m/%d/%Y  %I:%M:%S %p']:
            try:
                time = datetime.strptime(stri, fmt)
                break
            except ValueError:
                continue
        if firsttime is None:
            firsttime = time
        else:
            times.append((time - firsttime).total_seconds())
    return np.array(times)


def extract_timesMC(dates, form='%m/%d/%Y  %I:%M %p'):
    """Convert MC timestamp strings to per-step durations in seconds."""
    times = []
    oldtime = None
    for stri in dates:
        for fmt in [form, '%m/%d/%Y  %H:%M:%S', '%m/%d/%Y  %H:%M',
                    '%m/%d/%Y  %I:%M:%S %p']:
            try:
                time = datetime.strptime(stri, fmt)
                break
            except ValueError:
                continue
        if oldtime is None:
            oldtime = time
        else:
            times.append((time - oldtime).total_seconds())
            oldtime = time
    return np.array(times)


def make_grid(minors=True):
    """Add major/minor gridlines to the current axes."""
    ax = plt.gca()
    x_texts = ax.get_xticklabels()[1:-1]
    y_texts = ax.get_yticklabels()[1:-1]
    x_coords = [xt.get_position()[0] for xt in x_texts]
    y_coords = [yt.get_position()[1] for yt in y_texts]
    ylim = ax.get_ylim()
    xlim = ax.get_xlim()
    if minors:
        plt.vlines(ax.get_xticks(minor=True), *ylim, linestyle='-', color='Black', alpha=0.05)
        plt.hlines(ax.get_yticks(minor=True), *xlim, linestyle='-', color='Black', alpha=0.05)
    plt.vlines(x_coords, *ylim, linestyle='--', color='Black', alpha=0.2)
    plt.hlines(y_coords, *xlim, linestyle='--', color='Black', alpha=0.2)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)


# ---------------------------------------------------------------------------
# Cooling-rate functions for permeation_sim
# ---------------------------------------------------------------------------

def sulfur_blank_cooling(T, dt):
    x = T - (273 + 24)
    dTdt = -(4.2911E-6 * x ** 2) - (1.8754E-3 * x)
    return T + dTdt * dt


def isoTwater_blank_cooling(T, dt):
    x = T - (273 + 24)
    dTdt = -(3.6006E-5 * x ** 2) - (4.4616E-4 * x)
    return T + dTdt * dt


def NovTube_blank_cooling(T, dt):
    x = T - (273 + 24)
    dTdt = -(2.21847E-5 * x ** 2) - (1.08220E-3 * x)
    return T + dTdt * dt


def goethite_cooling(T, dt):
    x = T - (273 + 24)
    dTdt = -(9.23081E-6 * x ** 2) - (7.74304E-4 * x)
    return T + dTdt * dt


# ---------------------------------------------------------------------------
# Cylindrical FDM permeation simulator
# ---------------------------------------------------------------------------

class permeation_sim:
    """Finite-difference cylindrical model for He permeation through a silica
    ampoule.  a/b = inner/outer radius (cm), n0 = initial He atoms,
    cooling_func(T, dt) returns new T after dt seconds, He = isotope (3 or 4)."""

    def __init__(self, a, b, n0, cooling_func, T=24 + 273, He=4, EQMshortcut=False):
        self.a = a
        self.b = b
        self.n0 = n0
        self.nt = n0
        self.He = str(He)
        self.cooling_func = cooling_func
        self.dr = (self.b - self.a) / 25
        self.G = 2 / (np.log(self.b / self.a) * self.a ** 2)
        self.r = np.arange(self.a, self.b, self.dr)
        if round(self.r[-1], 4) != round(self.b, 4):
            self.r = np.append(self.r, self.b)
        self.T = T
        self.S = swets('S', self.T)
        self.D = swets('D', self.T)
        self.K = swets('K', self.T)
        if self.He == '3':
            self.S *= Jones('S', self.T)
            self.D *= Jones('D', self.T)
            self.K *= Jones('K', self.T)
        self.nglass = self.nt / (
            1 + (((self.S * 2 * Ratoms * self.T / (self.a ** 2 * np.log(self.a / self.b)))
                  * ((0.5 * self.a ** 2 * (np.log(self.b / self.a) + 0.5)) - self.b ** 2 / 4)) ** -1))
        self.ngas = self.nt - self.nglass
        self.h = 1
        self.c = (self.S * self.ngas * Ratoms * self.T / (np.pi * self.a ** 2 * self.h)) * (
            np.log(self.r / self.b) / np.log(self.a / self.b))
        self.out = 0
        self.reportmatrix = np.array([['Initial', self.T - 273, 0, 0, self.n0, self.nt, 0]])
        self.dt = 0.5 * self.dr ** 2 / self.D
        self.firstderiv = (self.c[2:] - self.c[:-2]) / (2 * self.dr)
        self.J = -self.D * self.firstderiv * self.dt * np.pi * self.r[1:-1] * 2 * self.h
        self.EQMshortcut = EQMshortcut

    def record_sim(self, Type, T, t, m, n0, nt):
        appK = np.log(nt / n0) / (-self.G * t * Ratoms * T)
        self.reportmatrix = np.append(
            self.reportmatrix,
            np.array([[Type, T - 273, t / 60, m, n0, nt, appK]]), 0)

    def hold_T(self, T, t, record=True, verbose=False):
        self.T = T
        self.t_count = 0
        self.t_remain = t
        self.D = swets('D', self.T)
        self.S = swets('S', self.T)
        self.K = swets('K', self.T)
        if self.He == '3':
            self.D *= Jones('D', self.T)
            self.S *= Jones('S', self.T)
            self.K *= Jones('K', self.T)
        self.t_EQM = t + 60 if not self.EQMshortcut else ((self.b - self.a) ** 2) / self.D
        print(f"EQM: {self.t_EQM}s out of {t} s")
        self.dt = 0.5 * self.dr ** 2 / self.D
        if verbose:
            _pbar = tqdm(total=int(self.t_EQM / self.dt) + 1,
                         desc=f'hold @ {T - 273:.0f}°C', unit='step', leave=False)
        while self.t_remain > 0 and self.t_count < self.t_EQM:
            if self.t_remain < self.dt:
                self.dt = self.t_remain
            self.t_count += self.dt
            self.t_remain -= self.dt
            self.c_inner = self.S * self.ngas * Ratoms * self.T / (np.pi * self.a ** 2 * self.h)
            self.inxs = self.c[0] - self.c_inner
            self.c[0] = self.c_inner
            self.ngas += self.inxs * 2 * np.pi * self.a * self.dr * self.h
            self.firstderiv = (self.c[2:] - self.c[:-2]) / (2 * self.dr)
            self.delta_c = (self.D * self.dt) * (
                (self.c[:-2] - 2 * self.c[1:-1] + self.c[2:]) / self.dr ** 2
                + (1 / self.r[1:-1]) * self.firstderiv)
            self.dout = (-self.D * ((self.c[-1] - self.c[-3]) / (2 * self.dr)
                                    + (self.c[-1] - 2 * self.c[-2] + self.c[-3]) / self.dr)
                         * self.dt * np.pi * self.b * 2 * self.h)
            self.dngas = (-self.D * ((self.c[2] - self.c[0]) / (2 * self.dr)
                                     - (self.c[0] - 2 * self.c[1] + self.c[2]) / self.dr)
                          * self.dt * np.pi * self.a * 2 * self.h)
            self.out += self.dout
            self.ngas -= self.dngas
            self.c[1:-1] += self.delta_c
            if verbose:
                _pbar.update(1)
        if verbose:
            _pbar.close()
        total = (self.out + self.ngas
                 + np.sum(self.c * self.dr * self.h * self.r * 2 * np.pi))
        self.c /= total / self.n0
        self.out /= total / self.n0
        self.ngas /= total / self.n0
        self.nt = self.n0 - self.out
        if self.t_remain > 0:
            print(f"Steady State concentration profile reached on {int(T-273.15)}C {int(t/60)}min step")
            EQMR = np.exp(-self.G * self.T * Ratoms * self.K * self.t_remain)
            permout = self.nt * (1 - EQMR)
            self.out += permout
            self.nt *= EQMR
            self.nglass = self.nt / (
                1 + (((self.S * 2 * Ratoms * self.T / (self.a ** 2 * np.log(self.a / self.b)))
                      * ((0.5 * self.a ** 2 * (np.log(self.b / self.a) + 0.5))
                         - self.b ** 2 / 4)) ** -1))
            self.ngas = self.nt - self.nglass
            self.c = (self.S * self.ngas * Ratoms * self.T / (np.pi * self.a ** 2 * self.h)) * (
                np.log(self.r / self.b) / np.log(self.a / self.b))
        if record:
            self.record_sim('Hold T', T=self.T, t=self.t_count + self.t_remain,
                            m=self.n0 - self.nt, n0=self.n0, nt=self.nt)

    def cool(self, t, record=True, verbose=False):
        self.t_count = 0
        self.m = 0
        self.t_remain = t
        if verbose:
            _pbar = tqdm(desc='cooling', unit='step', leave=False)
        while self.t_remain > 0 and self.T > 273 + 24.5:
            self.dt = 0.5 * self.dr ** 2 / self.D
            if self.t_remain < self.dt:
                self.dt = self.t_remain
            self.T = self.cooling_func(self.T, self.dt)
            self.D = swets('D', self.T)
            self.S = swets('S', self.T)
            self.K = swets('K', self.T)
            if self.He == '3':
                self.D *= Jones('D', self.T)
                self.S *= Jones('S', self.T)
                self.K *= Jones('K', self.T)
            self.t_count += self.dt
            self.t_remain -= self.dt
            self.c_inner = self.S * self.ngas * Ratoms * self.T / (np.pi * self.a ** 2 * self.h)
            self.inxs = self.c[0] - self.c_inner
            self.c[0] = self.c_inner
            self.ngas += self.inxs * 2 * np.pi * self.a * self.dr * self.h
            self.firstderiv = (self.c[2:] - self.c[:-2]) / (2 * self.dr)
            self.delta_c = (self.D * self.dt) * (
                (self.c[:-2] - 2 * self.c[1:-1] + self.c[2:]) / self.dr ** 2
                + (1 / self.r[1:-1]) * self.firstderiv)
            self.dout = (-self.D * ((self.c[-1] - self.c[-3]) / (2 * self.dr)
                                    + (self.c[-1] - 2 * self.c[-2] + self.c[-3]) / self.dr)
                         * self.dt * np.pi * self.b * 2 * self.h)
            self.dngas = (-self.D * ((self.c[2] - self.c[0]) / (2 * self.dr)
                                     - (self.c[0] - 2 * self.c[1] + self.c[2]) / self.dr)
                          * self.dt * np.pi * self.a * 2 * self.h)
            self.out += self.dout
            self.m += self.dout
            self.ngas -= self.dngas
            if verbose:
                _pbar.update(1)
        if verbose:
            _pbar.close()
        total = (self.out + self.ngas
                 + np.sum(self.c * self.dr * self.h * self.r * 2 * np.pi))
        self.c /= total / self.n0
        self.out /= total / self.n0
        self.ngas /= total / self.n0
        self.nt = self.n0 - self.out
        if self.t_remain > 0:
            simT = self.t_count
            recnt = self.nt
            self.hold_T(T=273 + 24, t=self.t_remain, record=False)
            self.m += recnt - self.nt
            self.t_remain += simT
        if record:
            self.record_sim('Cooling', T=self.T, t=self.t_count + self.t_remain,
                            m=self.m, n0=self.n0, nt=self.nt)
            
    def pump(self, n0 = 1):
        self.n0 = self.nt
        self.m = 0
        self.out = 0

    def generate_report(self, name='ampoule_permeation_out'):
        columns = ['Type', 'T (K)', 't(minutes)', 'm', 'n0', 'nt', 'Apparent K']
        df = pd.DataFrame({col: self.reportmatrix[:, i] for i, col in enumerate(columns)})
        df.to_csv(name + '.csv')

    def reset(self, n0, T):
        self.n0 = n0
        self.nt = n0
        self.T = T
        self.S = swets('S', self.T)
        if self.He == '3':
            self.S *= Jones('S', self.T)
        self.nglass = self.nt / (
            1 + (((self.S * 2 * Ratoms * self.T / (self.a ** 2 * np.log(self.a / self.b)))
                  * ((0.5 * self.a ** 2 * (np.log(self.b / self.a) + 0.5))
                     - self.b ** 2 / 4)) ** -1))
        self.ngas = self.nt - self.nglass
        self.c = (self.S * self.ngas * Ratoms * self.T / (np.pi * self.a ** 2 * self.h)) * (
            np.log(self.r / self.b) / np.log(self.a / self.b))
        self.out = 0

    def stabilize_profile(self):
        tauD = (self.b - self.a) ** 2 / self.D
        self.hold_T(self.T, tauD, verbose=True)
        self.c /= self.nt / self.n0
        self.nglass = np.sum(self.c * self.dr * self.h * self.r * 2 * np.pi)
        self.nt = self.n0
        self.ngas = self.nt - self.nglass
        self.out = 0


# ---------------------------------------------------------------------------
# Mass-spectrometer He reduction
# ---------------------------------------------------------------------------

class MCHeReducer:
    """Maps MC signals to He abundances using bracketing standards."""

    def __init__(self, STD_name, form='%m/%d/%Y  %I:%M %p'):
        self.std = pd.read_csv(STD_name, header=None).to_numpy()
        self.STD4 = 157.50   # nccSTP
        self.STD3 = 3.57     # pccSTP
        self.exist_ID = []
        clean_rows = []
        for z, std in enumerate(self.std):
            if std[0] not in self.exist_ID:
                self.exist_ID.append(std[0])
                clean_rows.append(z)
        self.std = self.std[clean_rows]
        for fmt in [form, '%m/%d/%Y  %H:%M:%S', '%m/%d/%Y  %H:%M',
                    '%m/%d/%Y  %I:%M:%S %p']:
            try:
                self.t0 = datetime.strptime(self.std[0, 2], fmt)
                break
            except ValueError:
                continue
        self.Dt = np.append(0, extract_times_from0(self.std[:, 2]))
        self.std = self.std[np.argsort(self.Dt)]
        self.Dt = np.sort(self.Dt)
        self.sens4 = self.STD4 / self.std[:, 6]
        self.sens3 = self.STD3 / self.std[:, 4]
        self.x = np.linspace(0, self.Dt[-1], 2000)
        self.inds = np.arange(len(self.sens4))
        self.sigma4 = [np.std(self.sens4[np.argsort(np.abs(self.inds - i))][:5])
                       for i in self.inds]
        self.sigma3 = [np.std(self.sens3[np.argsort(np.abs(self.inds - i))][:5])
                       for i in self.inds]
        self.model4 = scipy.interpolate.pchip_interpolate(self.Dt, self.sens4, self.x)
        self.model3 = scipy.interpolate.pchip_interpolate(self.Dt, self.sens3, self.x)
        self.model4sigma = scipy.interpolate.pchip_interpolate(
            self.Dt, np.array(self.sigma4), self.x)
        self.model3sigma = scipy.interpolate.pchip_interpolate(
            self.Dt, np.array(self.sigma3), self.x)

    def reduce(self, DIFFCELL, form='%m/%d/%Y  %I:%M %p', plot=False,
               sens_out=False, uncertainties=False):
        self.analyses = DIFFCELL
        self.AnalDT = extract_times_from0(
            np.append(self.t0.strftime(form), self.analyses[:, 2]), form=form)
        self.sensIND = [np.argmin(np.abs(self.x - tim)) for tim in self.AnalDT]
        self.sensIND = np.array(self.sensIND)
        self.Anal3He = (self.model3[self.sensIND] * self.analyses[:, 4]).astype('float')
        self.Anal4He = self.model4[self.sensIND] * self.analyses[:, 6].astype('float')
        outlist = [self.Anal3He, self.Anal4He]
        if uncertainties:
            outlist += [
                self.Anal3He * (self.model3sigma[self.sensIND] / self.model3[self.sensIND]),
                self.Anal4He * (self.model4sigma[self.sensIND] / self.model4[self.sensIND])]
        if sens_out:
            outlist += [self.model3[self.sensIND], self.model4[self.sensIND]]
        return outlist
