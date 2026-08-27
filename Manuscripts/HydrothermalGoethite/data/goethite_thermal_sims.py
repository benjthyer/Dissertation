"""
Forward finite-difference cylindrical permeation simulations of the Win-06-01b
goethite tube geometry, across a 5x3 grid of hold temperatures (90/95/100/105/110 C)
and hold durations (120/150/180 min). Each grid cell fits a (lambda, n0)
permeation model to the simulated 3-step-heat sequence (FirstOrdInversion1).
This uses the solubility and diffusivity of Swets et al., 1961 with 3He scaled 
by values reported by Jones, 1953. The purpose of this script is to assess the 
extent to which the ampoule's permeation during cooling time affects the fit rate constants.

Outputs:
  goethite_diff_sims/*.csv          - per-combination sim step records
  SimulatedFirstOrderLambdaFits.csv
      - T_C, T_K, hold_min, lam for all 12 grid cells; 
        which is plotted alongside the actual experimental fits


"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy
from tqdm import tqdm

Ratoms = 1.36E-22   # cc atm / atom / K (gas constant in units used in literature)
Rcal = 1.987


OUTDIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(OUTDIR, 'goethite_diff_sims'), exist_ok=True)

Ts = np.array([90, 95, 100, 105, 110])+273 # C-> K
times = np.array([120,150,180])*60 # minutes -> seconds


a = 0.053 / 2
b = 0.081 / 2
G = 2 / (np.log(b / a) * a ** 2)

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


def goethite_cooling(T, dt):
    """Parameterized cooling rate fit to real Watlow temperature records for Ht-Win-06-01b goethite ampoule"""
    x = T - (273 + 24)
    dTdt = -(9.23081E-6 * x ** 2) - (7.74304E-4 * x)
    return T + dTdt * dt


def forward_permeate(t, lamb, n0):
    """Eq for yield due to permeation given rate constant and time.  t in seconds, lamb in s^-1"""
    return n0 * (1 - np.exp(-lamb * t))


def forward_permeate1(t, lamb, n0):
    """
    Eq for yield due to permeation given rate constant and starting and ending time. t in seconds, lamb in s^-1
    t is [start, end]
    """
    return (n0 * (1 - np.exp(-lamb * t[1]))) - (n0 * (1 - np.exp(-lamb * t[0])))


def FirstOrdInv(t, He, sigma, covout=False, plot=True):
    """
    Exponential fit for cold-permeation time series; returns (lambda, n0).
    Fits step-wise yields with uncertainties.
    """
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

def accumulate(v):
    vnew = [v[0]]
    for vnext in v[1:]:
        vnew.append(vnext + vnew[-1])
    return np.array(vnew)

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
        self.nglass = self.nt / ( # Eq. 1.35 of BJT's dissertation
            1 + (((self.S * 2 * Ratoms * self.T / (self.a ** 2 * np.log(self.a / self.b)))
                  * ((0.5 * self.a ** 2 * (np.log(self.b / self.a) + 0.5)) - self.b ** 2 / 4)) ** -1))
        self.ngas = self.nt - self.nglass
        self.h = 1
        self.c = (self.S * self.ngas * Ratoms * self.T / (np.pi * self.a ** 2 * self.h)) * (
            np.log(self.r / self.b) / np.log(self.a / self.b)) # Eq. 1.32 of BJT's dissertation
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



Tall = []
tall = []
naive_errors = []
informed_errors = []
lambda_errors = []
sim_lambdas = []  # T_C, T_K, hold_min, lam -- cached below 
sim_records = []  # per-combination raw (t, He) step records, for the fit-quality
       

for T in Ts:
    for t in times:
        Tall.append(T)
        tall.append(t)
        tRecords = []
        print(f"Simming 3 sequential {int(T-273)}C steps {int(t/60)}min")
        goethite_tube = permeation_sim(a=a,b=b,n0=1,cooling_func=goethite_cooling,He=3,EQMshortcut=False, T = 300+273.15)
        goethite_tube.cool(15*60)
        goethite_tube.pump()
        n0_ans = goethite_tube.n0
        HeRecords = []
        for r in range(3):
            goethite_tube.hold_T(T=T, t=t)
            goethite_tube.cool(15*60)
            HeRec = goethite_tube.out
            tRecords.append(t)
            HeRecords.append(HeRec)
            goethite_tube.pump()
        (lam ,n0), covmat = FirstOrdInv(np.array(tRecords), np.array(HeRecords), sigma=np.array(HeRecords)*0.1, covout=True, plot=True)
        naive_errors.append(100*(n0-n0_ans)/n0_ans)
        F = 1-np.exp(-lam*t)
        final_n0 = HeRec+goethite_tube.nt
        informed_errors.append(100*((HeRec/F)-(final_n0))/final_n0)
        swetK = swets('K', T=T)#*Jones('K', T=T)
        calcK = lam/(G*Ratoms*T)
        lambda_errors.append(100*(calcK-swetK)/swetK)
        sim_lambdas.append({'T_C': T - 273, 'T_K': T, 'hold_min': t / 60, 'lam': lam})
        sim_records.append({'T_C': T - 273, 'hold_min': t / 60,
                             't': np.array(tRecords), 'He': np.array(HeRecords),
                             'lam': lam, 'n0': n0})
        print(f"Fitted parameters for {int(T-273)}C {int(t/60)}min: lambda = {lam:.3e}, n0 = {n0:.3e}")
        print(f"Covariance matrix: {covmat}")

        goethite_tube.generate_report(os.path.join(OUTDIR, 'goethite_diff_sims', f'{int(T-273)}C_{int(t/60)}min_cooling_NoSS_lam{lam:.3e}_n0{n0:.3e}'))


        goethite_tube = permeation_sim(a=a,b=b,n0=1,cooling_func=goethite_cooling,He=3,EQMshortcut=False, T = 300+273.15)
        goethite_tube.cool(15*60)
        goethite_tube.pump()
        for r in range(3):
            goethite_tube.hold_T(T=T, t=t)
            goethite_tube.pump()
        goethite_tube.generate_report(os.path.join(OUTDIR, 'goethite_diff_sims', f'{int(T-273)}C_{int(t/60)}min_hot_only_NoSS'))


sim_df = pd.DataFrame(sim_lambdas)
sim_df.to_csv('SimulatedFirstOrderLambdaFits.csv', index=False)