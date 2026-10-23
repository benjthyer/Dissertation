"""
Independent check that the 4He/3He forward model degasses the NON-UNIFORM
natural 4He profile in the laboratory (not a uniform one).

The production model (winsor_he43_mdd_free.SpectrumModelFree) carries each
domain's present-day 4He profile as sine-series amplitudes A_k,
    C(x) = sum_k A_k sin(k pi x) / x ,
and degasses it in the lab by decaying every mode by exp(-k^2 pi^2 tau_lab).
Here the same problem is solved with no sine series at all: a conservative
finite-volume discretization on spherical shells, C = 0 at the surface,
integrated exactly in time (generalized symmetric eigenproblem of the FV
operator). Natural history and lab schedule are identical in both.

Outputs (generated/mdd_free/absolute/chapter/):
  ch2_check_nonuniform_N4.{pdf,png}   profiles, release, spectrum comparison
"""
import json
import os

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import eigh

import winsor_he43_model as M
import winsor_he43_mdd as D
import winsor_he43_mdd_free as F

FIG = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(FIG, 'generated', 'data', 'mdd_free', 'absolute')
OUT = os.path.join(FIG, 'generated', 'mdd_free', 'absolute', 'chapter')
os.makedirs(OUT, exist_ok=True)

NX = 2000                      # finite-volume shells (uniform)
T_FORM, T_PEAK, T_MAX, T_EXP = 190.0, 74.0, 60.0, 50.0


class FVSphere:
    """dC/dtau = laplacian C on the unit sphere, C(1) = 0, source P."""
    def __init__(self, nx=NX):
        s = np.linspace(0, 1, nx + 1)
        e = s
        self.xc = 0.5 * (e[1:] + e[:-1])
        V = (e[1:] ** 3 - e[:-1] ** 3) / 3.0                 # shell volume / 4pi
        K = np.zeros((nx, nx))
        for i in range(nx - 1):                                # interior faces
            g = e[i + 1] ** 2 / (self.xc[i + 1] - self.xc[i])
            K[i, i] += g; K[i + 1, i + 1] += g
            K[i, i + 1] -= g; K[i + 1, i] -= g
        K[-1, -1] += e[-1] ** 2 / (e[-1] - self.xc[-1])        # C = 0 at x = 1
        self.V = V
        self.lam, self.Phi = eigh(K, np.diag(V))               # Phi^T V Phi = I
        self.one = self.Phi.T @ V                              # projection of C = 1

    def to_modal(self, C):
        return self.Phi.T @ (self.V * C)

    def amount(self, c):                                       # 3 * int x^2 C dx
        return 3.0 * (self.V @ (self.Phi @ c))

    def grow(self, c, tau, p):
        """Exact step: dc/dtau = -lam c + p*one over reduced time tau."""
        x = self.lam * tau
        return c * np.exp(-x) + p * self.one * (-np.expm1(-x)) / self.lam


def fv_natural(fv, Dm_list, h_list, r):
    c = np.zeros(NX)
    for Dm, h in zip(Dm_list, h_list):
        c = fv.grow(c, Dm * h / r ** 2, r ** 2 / Dm)           # P = 1 per Myr = r^2/D per unit tau
    return c


def main():
    spec = M.load_spectrum()
    res = json.load(open(os.path.join(DATA, 'N4.json')))
    f, r = np.array(res['f']), np.array(res['r'])
    t_nodes, T_nodes = [T_FORM, T_PEAK, T_EXP, 0.0], [M.T_SURF, T_MAX, M.T_SURF, M.T_SURF]

    # --- production model (sine series)
    sm = F.SpectrumModelFree(spec, f, r)
    A = sm.modes(t_nodes, T_nodes)
    pred_series = sm.predict(A)

    # --- same natural history, piecewise-constant D/a^2 as in path_modes_multi
    edges = np.arange(T_FORM, -1e-9, -2.0)
    edges = np.r_[edges, 0.0] if edges[-1] > 0 else edges
    mids = 0.5 * (edges[:-1] + edges[1:])
    Dm = M.D_a2_per_myr(M.path_T(t_nodes, T_nodes, mids))
    h = edges[:-1] - edges[1:]

    fv = FVSphere()
    tau0 = F.ref_lab_tau(spec['F_end'], f, r)
    taus = np.r_[0.0, tau0]
    N4 = np.zeros(taus.size); N3 = np.zeros(taus.size); N4_uni = np.zeros(taus.size)
    profiles = []
    for fj, rj, Aj in zip(f, r, A):
        c = fv_natural(fv, Dm, h, rj)
        profiles.append((fv.xc, fv.Phi @ c, Aj))
        c_uni = fv.amount(c) * fv.one                         # same 4He, uniform profile
        for i, t in enumerate(taus):
            dec = np.exp(-fv.lam * t / rj ** 2)
            N4[i] += fj * fv.amount(c * dec)
            N4_uni[i] += fj * fv.amount(c_uni * dec)
            N3[i] += fj * fv.amount(fv.one * dec)
    dF3_fv = -np.diff(N3) / N3[0]
    pred_fv = (-np.diff(N4) / N4[0]) / spec['dF3']
    pred_uni = (-np.diff(N4_uni) / N4_uni[0]) / spec['dF3']

    u = spec['use']
    print('max |series - FV| in R/Rbulk (fitted steps):', np.max(np.abs(pred_series - pred_fv)[u]))
    print('max |dF3 FV - dF3 measured|:', np.max(np.abs(dF3_fv - spec['dF3'])))
    print('chi2 series, FV, uniform-4He:',
          M.chi2(spec, pred_series), M.chi2(spec, pred_fv), M.chi2(spec, pred_uni))
    print('domain 4He retention (FV):',
          [round(fv.amount(fv_natural(fv, Dm, h, rj)) / (T_FORM), 4) for rj in r])

    # --- figure
    plt.rcParams.update({'font.size': 10})
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    cols = ['#9aa5b1', '#6b7a8f', '#c77d2e', '#1f4e79']
    x = np.linspace(1e-4, 1, 400)
    S = np.sin(np.outer(x, np.arange(1, M.K_MODES + 1) * np.pi)) / x[:, None]
    for (xc, Cfv, Aj), rj, cl in zip(profiles, r, cols):
        norm = 1.0 / T_FORM                                   # C / (P * t_form)
        ax[0].plot(x, (S @ Aj) * norm, color=cl, lw=2, label=f'r/r$_0$ = {rj:.2g}')
        ax[0].plot(xc[::12], Cfv[::12] * norm, 'o', ms=3, mfc='none', color=cl)
    ax[0].set_xlabel('Radial position x = ρ/a')
    ax[0].set_ylabel(r'$^4$He / (P $t_\mathrm{form}$)')
    ax[0].set_title('Natural $^4$He profiles (lines: series, o: FV)')
    ax[0].legend(fontsize=8)

    ax[1].plot(np.r_[0, spec['F_end']], np.r_[0, np.cumsum(-np.diff(N4) / N4[0])], color='#1f4e79', lw=2,
               label=r'$^4$He, natural profile')
    ax[1].plot(np.r_[0, spec['F_end']], np.r_[0, np.cumsum(-np.diff(N4_uni) / N4_uni[0])], color='#c77d2e',
               lw=2, ls='--', label=r'$^4$He, if uniform')
    ax[1].plot([0, 0.16], [0, 0.16], color='k', lw=1, ls=':', label=r'$^3$He (uniform)')
    ax[1].set_xlim(0, 0.16); ax[1].set_ylim(0, 0.16)
    ax[1].set_xlabel(r'Cumulative $^3$He fraction'); ax[1].set_ylabel('Cumulative release')
    ax[1].set_title('Lab release, same lab τ schedule')
    ax[1].legend(fontsize=8)

    Fs, Fe = spec['F_start'], spec['F_end']
    for i in np.where(u)[0]:
        ax[2].fill_between([Fs[i], Fe[i]], spec['R_LB'][i], spec['R_UB'][i], color='#d9d9d9', lw=0)
    ax[2].hlines(spec['R_M'][u], Fs[u], Fe[u], color='k', lw=2, label='Data')
    ax[2].hlines(pred_series, Fs, Fe, color='#1f4e79', lw=2.4, label='Series (production)')
    ax[2].hlines(pred_fv, Fs, Fe, color='#7fb3e0', lw=1.0, label='FV (independent)')
    ax[2].hlines(pred_uni, Fs, Fe, color='#c77d2e', lw=1.5, ls='--', label='Uniform $^4$He (wrong)')
    ax[2].set_xlim(0, 0.16); ax[2].set_ylim(0, 1.2)
    ax[2].set_xlabel(r'Cumulative $^3$He fraction'); ax[2].set_ylabel(r'$R_\mathrm{step}/R_\mathrm{bulk}$')
    ax[2].set_title('Spectrum, burial 190→74 Ma, 60 °C')
    ax[2].legend(fontsize=8, loc='lower right')
    fig.tight_layout()
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(OUT, f'ch2_check_nonuniform_N4.{ext}'), dpi=200)


if __name__ == '__main__':
    main()
