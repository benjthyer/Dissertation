"""
Goethite = hematite + water equilibrium as a function of T, P_H2O and grain size.

    2 alpha-FeOOH  =  alpha-Fe2O3  +  H2O(fluid)

Equilibrium:  dG_bulk(T, P) + dG_surf(d) = 0
  dG > 0  -> goethite stable (high P_H2O side)
  dG < 0  -> hematite + H2O stable

Thermodynamic data
------------------
Hematite, goethite: DfH, S from the MAP refinement of Majzlan et al. (2003b,
    Am. Mineral. 88:855, Table 5; default = Voigt & Will brackets).
Goethite Cp: Berman-Brown fit from Majzlan et al. (2003b, Table 5).
    Smooth through the Neel transition (~375 K); extrapolated above ~400 K.
Hematite Cp: Maier-Kelley fit (Kelley 1960, as tabulated in Robie & Hemingway
    compilations), valid 298-950 K.  Majzlan used Berman (1988) instead;
    swap in if you want exact parity.
Molar volumes: goethite 20.881 cm3 (Majzlan 2003a), hematite 30.274 cm3.
    Solids treated as incompressible with no thermal expansion.
Water: IAPWS-95 via CoolProp (liquid, vapor, supercritical; valid to 1 GPa).

Surface energies (Navrotsky et al. 2008, Table 1), J/m^2:
    hydrated:  hematite 0.75, goethite 0.60
    anhydrous: hematite 1.90, goethite 0.91
Surface area basis:
    "equal_area" : both phases have the same surface area per mole Fe,
                   A_Fe = 6 V_goe / d  (basis of Navrotsky Fig. 2; reproduces
                   the ~100 K shift quoted for 10 nm).  Physically: pseudomorphic
                   dehydration preserving the goethite grain envelope.
    "equal_diameter": both phases are spheres of diameter d.

Energies: apparent Gibbs energy (Berman convention), G = H - TS with
H = DfH(298) + int Cp dT, S = S298 + int Cp/T dT. Element terms cancel.

Author: Claude for B.  (Chapter 2 workspace)
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.optimize import brentq
import CoolProp.CoolProp as CP

TR = 298.15          # K
PR = 1.0e5           # Pa (1 bar)
R = 8.314462618
ATM = 101325.0
P_VAC = 1e-8 * ATM   # Pa, "water absent" / vacuum step-heating condition

OUTDIR = Path(__file__).resolve().parent / "generated"
OUTDIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
DATASETS = {
    # (DfH hem, S hem, DfH goe, S goe)  J/mol, J/mol/K
    "MAP_VW":  (-825.8e3, 87.4, -561.4e3, 59.5),
    "MAP_BB":  (-825.5e3, 87.4, -561.9e3, 59.2),
    "calorim": (-826.2e3, 87.4, -560.7e3, 59.7),   # acid-solution goethite
}
DATASET = "MAP_VW"

V_GOE = 20.881e-6    # m3/mol FeOOH
V_HEM = 30.274e-6    # m3/mol Fe2O3

# Goethite Cp (Berman-Brown): k0 + k1 T^-0.5 + k2 T^-2 + k3 T^-3
K_GOE = (133.8765, -738.5577, -2177657.0, 216512400.0)
# Hematite Cp (Maier-Kelley): a + bT + cT^-2
MK_HEM = (98.28, 77.82e-3, -14.85e5)

GAMMA = {  # J/m2
    "hydrated":  {"hem": 0.75, "goe": 0.60},
    "anhydrous": {"hem": 1.90, "goe": 0.91},
}

# Water reference, IAPWS-95 liquid at 298.15 K, 1 bar
DFH_W, S_W = -285.83e3, 69.95
H_W_REF = CP.PropsSI("Hmolar", "T", TR, "P", PR, "Water")
S_W_REF = CP.PropsSI("Smolar", "T", TR, "P", PR, "Water")


# ----------------------------------------------------------------------------
# Gibbs energies
# ----------------------------------------------------------------------------
def _berman_int(T, k):
    k0, k1, k2, k3 = k
    dH = (k0 * (T - TR) + 2 * k1 * (np.sqrt(T) - np.sqrt(TR))
          - k2 * (1 / T - 1 / TR) - 0.5 * k3 * (T**-2 - TR**-2))
    dS = (k0 * np.log(T / TR) - 2 * k1 * (T**-0.5 - TR**-0.5)
          - 0.5 * k2 * (T**-2 - TR**-2) - (k3 / 3) * (T**-3 - TR**-3))
    return dH, dS


def _mk_int(T, c):
    a, b, cc = c
    dH = a * (T - TR) + 0.5 * b * (T**2 - TR**2) - cc * (1 / T - 1 / TR)
    dS = a * np.log(T / TR) + b * (T - TR) - 0.5 * cc * (T**-2 - TR**-2)
    return dH, dS


def G_solids(T, P, dataset=DATASET):
    """G(hematite) - 2 G(goethite), J, solids incompressible."""
    hH, hS, gH, gS = DATASETS[dataset]
    dHh, dSh = _mk_int(T, MK_HEM)
    dHg, dSg = _berman_int(T, K_GOE)
    Gh = hH + dHh - T * (hS + dSh) + V_HEM * (P - PR)
    Gg = gH + dHg - T * (gS + dSg) + V_GOE * (P - PR)
    return Gh - 2 * Gg


def G_water(T, P):
    try:
        h = CP.PropsSI("Hmolar", "T", T, "P", P, "Water")
        s = CP.PropsSI("Smolar", "T", T, "P", P, "Water")
    except ValueError:                      # exactly on saturation: nudge
        if abs(P / CP.PropsSI('P', 'T', T, 'Q', 0, 'Water') - 1) > 1e-6:
            raise
        P *= 1 + 1e-9
        h = CP.PropsSI("Hmolar", "T", T, "P", P, "Water")
        s = CP.PropsSI("Smolar", "T", T, "P", P, "Water")
    return (DFH_W + h - H_W_REF) - T * (S_W + s - S_W_REF)


def dG_bulk(T, P, dataset=DATASET):
    return G_solids(T, P, dataset) + G_water(T, P)


def dG_surf(d_nm, surface="hydrated", basis="equal_area"):
    """Surface contribution to dG_r (J per reaction as written)."""
    if d_nm is None:
        return 0.0
    d = d_nm * 1e-9
    g = GAMMA[surface]
    if basis == "equal_area":
        A_Fe = 6 * V_GOE / d                     # m2 per mol Fe
        return 2 * A_Fe * (g["hem"] - g["goe"])
    elif basis == "equal_diameter":
        return g["hem"] * 6 * V_HEM / d - 2 * g["goe"] * 6 * V_GOE / d
    raise ValueError(basis)


# ----------------------------------------------------------------------------
# Equilibrium curve
# ----------------------------------------------------------------------------
LOGP_MIN, LOGP_MAX = -12.0, 4.0   # bar; IAPWS-95 in CoolProp valid to 1 GPa


def equilibrium_logP(T, shift, dataset=DATASET):
    """log10 P_H2O (bar) where dG_bulk + shift = 0, or NaN."""
    f = lambda lp: dG_bulk(T, 10**lp * 1e5, dataset) + shift
    hi = LOGP_MAX
    while True:                 # stay below the ice melting curve at high P
        try:
            b = f(hi)
            break
        except ValueError:
            hi -= 0.02
    a = f(LOGP_MIN)
    if np.sign(a) == np.sign(b):
        return np.nan
    return brentq(f, LOGP_MIN, hi, xtol=1e-6)


def curve(T_arr, shift, dataset=DATASET):
    return np.array([equilibrium_logP(T, shift, dataset) for T in T_arr])


def saturation_curve(T_arr):
    Tc = CP.PropsSI("Tcrit", "Water")
    out = np.full_like(T_arr, np.nan)
    m = T_arr < Tc
    out[m] = [np.log10(CP.PropsSI("P", "T", T, "Q", 0, "Water") / 1e5)
              for T in T_arr[m]]
    return out


# ----------------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------------
SIZES = [None, 1000, 100, 10]          # nm; None = bulk (1 nm ~ one unit cell: dropped)
COLORS = {None: "k", 1000: "#1b9e77", 100: "#7570b3", 10: "#d95f02", 1: "#e7298a"}
LABEL = lambda d: "bulk" if d is None else f"{d} nm"
DG_UNC = 2.8e3   # J per reaction (+-1.4 kJ per FeOOH, Majzlan 2003b)


def make_figure(basis="equal_area", fname="goethite_hematite_Ph2o_T",
                T_C=np.linspace(0.5, 500, 300)):
    T = T_C + 273.15
    sat = saturation_curve(T)
    bulk_lo = curve(T, -DG_UNC)
    bulk_hi = curve(T, +DG_UNC)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True,
                             constrained_layout=True)
    for ax, surface in zip(axes, ["hydrated", "anhydrous"]):
        ax.plot(T_C, bulk_lo, color="0.6", lw=0.9, ls="-.",
                label=r"bulk $\pm$1.4 kJ/mol FeOOH")
        ax.plot(T_C, bulk_hi, color="0.6", lw=0.9, ls="-.")
        ax.plot(T_C, sat, color="tab:blue", ls=":", lw=1.2,
                label="H$_2$O saturation")
        for d in SIZES:
            sh = dG_surf(d, surface, basis)
            y = curve(T, sh)
            off = "" if np.isfinite(y).any() else " [off scale]"
            ls = "-"
            ax.plot(T_C, y, color=COLORS[d], ls=ls, lw=1.8,
                    label=f"{LABEL(d)}  ($\\Delta G_{{surf}}$ = {sh/1e3:+.1f} kJ){off}")
        ax.set_title(f"{surface} surfaces ({basis.replace('_', ' ')})")
        ax.set_xlabel("Temperature (°C)")
        ax.set_xlim(T_C[0], T_C[-1])
        ax.set_ylim(LOGP_MIN, LOGP_MAX)
        ax.text(0.04, 0.95, r"$\alpha$-FeOOH", transform=ax.transAxes,
                va="top", fontsize=11)
        ax.text(0.96, 0.05, r"$\alpha$-Fe$_2$O$_3$ + H$_2$O",
                transform=ax.transAxes, ha="right", fontsize=11)
        ax.legend(fontsize=7.5, loc="lower center", bbox_to_anchor=(0.62, 0.1))
        sec = ax.secondary_xaxis("top", functions=(lambda c: c + 273.15,
                                                   lambda k: k - 273.15))
        sec.set_xlabel("Temperature (K)")
    axes[0].set_ylabel(r"log $P_{\mathrm{H_2O}}$ (bar)")
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}_{basis}.{ext}", dpi=200)
    return fig


# ----------------------------------------------------------------------------
# Nucleation driving force:  relative barrier ~ 1 / dmu^2
# ----------------------------------------------------------------------------
# dmu = -dG_r  (J per mol Fe2O3 formed); dmu > 0 means hematite + H2O favored.
# Classical nucleation: dG* = 16 pi gamma^3 v^2 / (3 dmu^2).  Only dmu varies
# here; the nucleus interfacial energy and molar volume are held fixed, so
# 1/dmu^2 is a RELATIVE barrier.  Where dmu <= 0 goethite is stable and
# there is no driving force for hematite nucleation (masked).

def dmu(T, P_solid, P_h2o, d_nm=None, surface="hydrated", basis="equal_area",
        dataset=DATASET):
    return -(G_solids(T, P_solid, dataset) + G_water(T, P_h2o)
             + dG_surf(d_nm, surface, basis))


def inv_dmu2(x):
    """1/dmu^2 in (kJ/mol)^-2, NaN where goethite is stable."""
    x = np.asarray(x, float) / 1e3
    return np.where(x > 0, 1.0 / np.maximum(x, 1e-12)**2, np.nan)


def psat_bar(T):
    """Saturation pressure (bar); for T >= Tc returns Pc (condensed-fluid limit)."""
    Tc = CP.PropsSI("Tcrit", "Water")
    if T >= Tc:
        return CP.PropsSI("pcrit", "Water") / 1e5
    return CP.PropsSI("P", "T", T, "Q", 0, "Water") / 1e5


CLIM = (1e-5, 1e0)   # (kJ/mol)^-2 colour limits: dmu from ~300 kJ down to 1 kJ


def make_dmu_maps(T_C=np.linspace(1, 500, 220), logP=np.linspace(-8, 4, 220),
                  fname="nucleation_invdmu2_PT_bulk"):
    """Bulk (no surface terms).
    Left:  water-saturated, P_H2O = P_total. Condensed water requires
           P >= P_sat (T < Tc) or P >= P_c (T >= Tc); below that is forbidden.
    Right: water absent. Solids at P_total, released H2O at 1e-8 atm.
    """
    from matplotlib.colors import LogNorm
    T = T_C + 273.15
    Z_sat = np.full((logP.size, T.size), np.nan)
    Z_dry = np.full_like(Z_sat, np.nan)
    forbidden = np.zeros_like(Z_sat, bool)
    Gw_vac = np.array([G_water(t, P_VAC) for t in T])
    for j, t in enumerate(T):
        ps = psat_bar(t)
        for i, lp in enumerate(logP):
            P = 10**lp * 1e5
            Z_dry[i, j] = -(G_solids(t, P) + Gw_vac[j])
            if lp < np.log10(ps):
                forbidden[i, j] = True
                continue
            try:
                Z_sat[i, j] = -dG_bulk(t, P)
            except ValueError:              # ice stability field at high P
                pass
    Z_sat, Z_dry = inv_dmu2(Z_sat), inv_dmu2(Z_dry)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5), sharey=True,
                             constrained_layout=True)
    norm = LogNorm(*CLIM)
    for ax, Z, title in zip(axes, [Z_sat, Z_dry],
                            ["water saturated ($P_{H_2O}=P$)",
                             "water absent ($P_{H_2O}$ = 10$^{-8}$ atm)"]):
        ax.set_facecolor("0.93")    # masked = goethite stable (or ice)
        pc = ax.pcolormesh(T_C, logP, np.clip(Z, *CLIM), norm=norm,
                           cmap="viridis", shading="auto")
        ax.set_title(f"Bulk, {title}")
        ax.set_xlabel("Temperature (°C)")
    axes[0].contourf(T_C, logP, forbidden.astype(float), levels=[0.5, 1.5],
                     colors="none", hatches=["////"])
    axes[0].contour(T_C, logP, forbidden.astype(float), levels=[0.5],
                    colors="k", linewidths=1)
    axes[0].text(300, -5, "forbidden:\nno condensed water\n($P < P_{sat}$)",
                 ha="center", fontsize=9,
                 bbox=dict(fc="white", ec="none", alpha=0.8))
    axes[0].text(20, 3.5, "goethite\nstable", fontsize=9, va="top")
    axes[0].set_ylabel(r"log $P$ (bar)")
    axes[1].set_ylabel(r"log $P_{\mathrm{solids}}$ (bar)")
    axes[1].yaxis.set_tick_params(labelleft=True)
    cb = fig.colorbar(pc, ax=axes, shrink=0.9,
                      label=r"$1/\Delta\mu^2$  ((kJ/mol)$^{-2}$), relative nucleation barrier")
    cb.ax.text(0.5, 1.02, "clipped", transform=cb.ax.transAxes, ha="center",
               fontsize=7)
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig


def make_dmu_vs_T(fname="nucleation_invdmu2_vs_T"):
    """Saturated: P = P_sat(T), hydrated surfaces, up to Tc.
       Vacuum:    P_H2O = P_solid = 1e-8 atm, anhydrous surfaces."""
    Tc = CP.PropsSI("Tcrit", "Water")
    T_sat = np.linspace(273.2, Tc - 0.05, 400)
    T_vac = np.linspace(273.2, 773.15, 400)
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    for d, lw in [(None, 2.2), (10, 1.6)]:
        ps = np.array([CP.PropsSI("P", "T", t, "Q", 0, "Water") for t in T_sat])
        y_sat = inv_dmu2([dmu(t, p, p * (1 + 1e-6), d, "hydrated")
                          for t, p in zip(T_sat, ps)])
        y_vac = inv_dmu2([dmu(t, P_VAC, P_VAC, d, "anhydrous") for t in T_vac])
        lab = LABEL(d)
        ax.plot(T_sat - 273.15, y_sat, color="tab:blue", lw=lw,
                ls="-" if d is None else "--",
                label=f"{lab}, water saturated (hydrated $\\gamma$)")
        ax.plot(T_vac - 273.15, y_vac, color="tab:red", lw=lw,
                ls="-" if d is None else "--",
                label=f"{lab}, 10$^{{-8}}$ atm (anhydrous $\\gamma$)")
    ax.set_yscale("log")
    ax.set_ylim(1e-5, 1e1)
    ax.set_xlim(0, 500)
    ax.axvline(Tc - 273.15, color="0.6", lw=0.8, ls=":")
    ax.text(Tc - 273.15 + 4, 3, "$T_c$", color="0.4", fontsize=9)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel(r"$1/\Delta\mu^2$  ((kJ/mol Fe$_2$O$_3$)$^{-2}$)")
    ax.set_title("Relative barrier to hematite nucleation")
    ax.legend(fontsize=8)
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig


# ----------------------------------------------------------------------------
# Barrier ratio, saturated vs vacuum, at equal T
# ----------------------------------------------------------------------------
# dG*_sat / dG*_vac = (dmu_vac / dmu_sat)^2 * (gamma_sat / gamma_vac)^3
# Prefactors, T and molar volume cancel.  The interfacial-energy ratio is
# bracketed: 1 (same internal goethite|hematite interface in both cases) to
# (0.75/1.90)^3 ~ 1/16 (free hematite surface, hydrated vs anhydrous).

def make_barrier_ratio(fname="nucleation_barrier_ratio_vs_T",
                       exp_range_C=(150, 250)):
    Tc = CP.PropsSI("Tcrit", "Water")
    T = np.linspace(274.15, Tc - 0.05, 500)
    ps = np.array([CP.PropsSI("P", "T", t, "Q", 0, "Water") for t in T])
    g_ratio3 = (GAMMA["hydrated"]["hem"] / GAMMA["anhydrous"]["hem"])**3
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    ax.axvspan(*exp_range_C, color="0.92", zorder=0)
    ax.text(np.mean(exp_range_C), 1.6, "hydrothermal\nruns", ha="center",
            fontsize=8, color="0.4")
    for d, col in [(None, "k"), (10, "#d95f02")]:
        m_sat = np.array([dmu(t, p, p * (1 + 1e-6), d, "hydrated")
                          for t, p in zip(T, ps)])
        m_vac = np.array([dmu(t, P_VAC, P_VAC, d, "anhydrous") for t in T])
        ok = m_sat > 0
        hi = np.where(ok, (m_vac / np.where(ok, m_sat, 1))**2, np.nan)
        lo = hi * g_ratio3
        Tc_ = T - 273.15
        ax.fill_between(Tc_, lo, hi, color=col, alpha=0.18, lw=0)
        ax.plot(Tc_, hi, color=col, lw=2,
                label=f"{LABEL(d)}: same interface ($\\gamma$ ratio = 1)")
        ax.plot(Tc_, lo, color=col, lw=1, ls="--",
                label=f"{LABEL(d)}: free surfaces ($\\gamma$ ratio$^3$ = 1/16)")
        if not ok.all():
            T0 = Tc_[~ok].max()
            ax.axvline(T0, color=col, lw=0.8, ls=":")
            ax.text(T0 - 3, 2e4, f"{LABEL(d)} goethite stable\nat saturation",
                    color=col, fontsize=8, ha="right", va="top")
    ax.axhline(1, color="0.5", lw=0.8)
    ax.set_yscale("log")
    ax.set_ylim(0.5, 3e4)
    ax.set_xlim(0, Tc - 273.15)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel(r"$\Delta G^*_{\mathrm{sat}}\,/\,\Delta G^*_{\mathrm{vac}}$")
    ax.set_title("Hematite nucleation barrier: water-saturated vs 10$^{-8}$ atm")
    ax.legend(fontsize=8, loc="upper right")
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig


# ----------------------------------------------------------------------------
# Cumulative decomposition index for a step-heating schedule
# ----------------------------------------------------------------------------
# Nucleation-limited (heterogeneous CNT):
#   dI/dt = exp(-Ea/RT) * exp(-dG*/kT),   dG* = 16 pi g^3 V^2 / (3 dmu^2)
#   g = gamma_eff: an EFFECTIVE (heterogeneous, wetting-reduced) interfacial
#   energy.  Free-surface values (0.75-1.9 J/m2) give barriers of 10^3-10^4 kT,
#   i.e. no nucleation ever; real nucleation is heterogeneous, so gamma_eff
#   ~0.1-0.2 J/m2 is the plausible range.  Treat it as the one free parameter
#   (calibrate on the vacuum run's dehydration step if it shows one).
# Growth/reaction-limited (TST-type, linear in dmu near equilibrium):
#   dI/dt = exp(-Ea/RT) * (1 - exp(-dmu/RT))
# I has units of seconds ("effective time at unit rate"); ratios between
# schedules are meaningful, absolute values are not.

KB, NA = 1.380649e-23, 6.02214076e23


def step_dmu(T, condition, d_nm=None, P_h2o_bar=None):
    """dmu for one step. condition: 'vacuum' or 'saturated'."""
    if condition == "vacuum":
        P = P_VAC if P_h2o_bar is None else P_h2o_bar * 1e5
        return dmu(T, P, P, d_nm, "anhydrous")
    ps = CP.PropsSI("P", "T", T, "Q", 0, "Water")
    P = ps * (1 + 1e-6) if P_h2o_bar is None else max(P_h2o_bar * 1e5, ps)
    return dmu(T, P, P, d_nm, "hydrated")


def decomposition_rate(T, mu, mode="nucleation", gamma_eff=0.15, Ea=0.0):
    mob = np.exp(-Ea / (R * T))
    if mu <= 0:
        return 0.0
    if mode == "nucleation":
        dGstar = 16 * np.pi * gamma_eff**3 * V_HEM**2 / (3 * mu**2)  # J/nucleus
        return mob * np.exp(-dGstar / (KB * T))
    if mode == "growth":
        return mob * (1 - np.exp(-mu / (R * T)))
    raise ValueError(mode)


def cumulative_index(T_C, dt_s, condition, d_nm=None, P_h2o_bar=None, **kw):
    """Cumulative index after each step (array, same length as T_C)."""
    T = np.asarray(T_C, float) + 273.15
    P = [None] * len(T) if P_h2o_bar is None else P_h2o_bar
    rates = [decomposition_rate(t, step_dmu(t, condition, d_nm, p), **kw)
             for t, p in zip(T, P)]
    return np.cumsum(np.asarray(rates) * np.asarray(dt_s, float))


def fourier_number(T_C, dt_s, D0_a2, Ea_He):
    """Cumulative Dt/a^2 from an Arrhenius fit (D0/a^2 in 1/s, Ea in J/mol)."""
    T = np.asarray(T_C, float) + 273.15
    return np.cumsum(D0_a2 * np.exp(-Ea_He / (R * T)) * np.asarray(dt_s))


def sphere_F(Fo, nmax=200):
    n = np.arange(1, nmax + 1)[:, None]
    Fo = np.atleast_1d(Fo)[None, :]
    return 1 - (6 / np.pi**2) * np.sum(np.exp(-n**2 * np.pi**2 * Fo) / n**2, 0)


def load_schedule(path):
    """CSV columns: T_C, duration_s, He3 (per step, any units), condition
    ('vacuum' | 'saturated'); optional P_H2O_bar; optional F (cumulative
    fraction of TOTAL He3, incl. fusion -- use when the schedule does not
    exhaust the sample).  One file per experiment."""
    import pandas as pd
    df = pd.read_csv(path)
    if "F" not in df:
        df["F"] = df["He3"].cumsum() / df["He3"].sum()
    return df


def make_he_vs_index(experiments, d_nm=None, gamma_eff=0.15, Ea_decomp=0.0,
                     nuc_xmin=1e-30, fname="He3_vs_decomposition_index"):
    """experiments: {label: path_to_csv}.  Two panels:
    F vs nucleation index (log), F vs growth index (linear)."""
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8), sharey=True,
                             constrained_layout=True)
    for lab, path in experiments.items():
        df = load_schedule(path)
        cond = df["condition"].iloc[0]
        P = df["P_H2O_bar"].values if "P_H2O_bar" in df else None
        col = "tab:red" if cond == "vacuum" else "tab:blue"
        for ax, mode in zip(axes, ["nucleation", "growth"]):
            I = cumulative_index(df["T_C"], df["duration_s"], cond, d_nm, P,
                                 mode=mode, gamma_eff=gamma_eff, Ea=Ea_decomp)
            ax.plot(np.maximum(I, 1e-300), df["F"], "o-", color=col, ms=4,
                    label=lab)
    axes[0].set_xlabel(f"cumulative nucleation index (s), "
                       f"$\\gamma_{{eff}}$ = {gamma_eff} J/m$^2$")
    axes[1].set_xlabel("cumulative growth index (s)")
    axes[0].set_ylabel(r"cumulative $^3$He fraction")
    axes[0].set_xscale("log")
    axes[0].set_xlim(left=nuc_xmin)
    axes[0].set_axisbelow(True)
    axes[0].grid(True, which="major", color="0.85", lw=0.6)
    axes[0].axvline(1, color="0.2", ls="--", lw=1, zorder=1)
    axes[1].set_xlim(left=0)
    for ax in axes:
        ax.legend(fontsize=8)
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig


# ----------------------------------------------------------------------------
# Reaction extent from the growth index:  g(alpha) = A * I_growth
# ----------------------------------------------------------------------------
# Solid-state kinetics: d(alpha)/dt = A exp(-Ea/RT) h(dmu) f(alpha), so for any
# heating schedule  g(alpha) = int_0^alpha d(a)/f(a) = A * I,  with
#   I = sum_i dt_i exp(-Ea/RT_i) (1 - exp(-dmu_i/RT_i))    (growth index, s)
# Each mechanism has its own alpha(x), x = A*I.  Sphere diffusion (the He
# model) is included on the same footing, so the only difference between
# "He released by diffusion" and "He released as goethite converts" is the
# SHAPE alpha(x) and the fitted Ea.  In vacuum h(dmu) ~ 1, so the growth index
# is just an Arrhenius-weighted time, like a Fourier number.
# Hypothesis being tested: F(3He) ~ alpha (uniform 3He, released on conversion).

EXTENT_MODELS = {
    "R2 contracting cylinder": lambda x: 1 - np.clip(1 - x, 0, None)**2,
    "R3 contracting sphere":   lambda x: 1 - np.clip(1 - x, 0, None)**3,
    "F1 first order":          lambda x: 1 - np.exp(-x),
    "A2 Avrami n=2":           lambda x: 1 - np.exp(-x**2),
    "A3 Avrami n=3":           lambda x: 1 - np.exp(-x**3),
    "D3 sphere diffusion":     lambda x: sphere_F(x),
}
# low-alpha log-log slope d ln(alpha)/d ln(x):  D3 -> 0.5,  R/F1 -> 1,  An -> n


def fit_extent(df, model, Ea_grid=np.linspace(40e3, 300e3, 53), d_nm=None):
    """Best (Ea, A, rms) for alpha_model(A*I) vs observed F, least squares."""
    from scipy.optimize import minimize_scalar
    cond = df["condition"].iloc[0]
    P = df["P_H2O_bar"].values if "P_H2O_bar" in df else None
    F = df["F"].values
    f = EXTENT_MODELS[model]
    best = (np.nan, np.nan, np.inf)
    for Ea in Ea_grid:
        I = cumulative_index(df["T_C"], df["duration_s"], cond, d_nm, P,
                             mode="growth", Ea=Ea)
        if I[-1] <= 0:
            continue
        # scale so x spans O(1): search lnA around -ln(I_end)
        c0 = -np.log(I[-1])
        res = minimize_scalar(lambda lnA: np.sum((F - f(np.exp(lnA) * I))**2),
                              bounds=(c0 - 25, c0 + 25), method="bounded")
        rms = np.sqrt(res.fun / F.size)
        if rms < best[2]:
            best = (Ea, np.exp(res.x), rms)
    return best


def make_extent_test(path, label=None, d_nm=None,
                     models=tuple(EXTENT_MODELS),
                     fname="He3_extent_model_test"):
    """Left: F vs best-fit x = A*I for each model, with model curves.
    Right: log F vs log I at each model's best Ea (low-F slope diagnostic).
    Also writes a CSV table of fits."""
    import pandas as pd
    df = load_schedule(path)
    cond = df["condition"].iloc[0]
    P = df["P_H2O_bar"].values if "P_H2O_bar" in df else None
    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), constrained_layout=True)
    x_th = np.linspace(0, 3, 400)
    cols = plt.cm.tab10(np.arange(len(models)))
    for c, m in zip(cols, models):
        Ea, A, rms = fit_extent(df, m, d_nm=d_nm)
        rows.append(dict(model=m, Ea_kJ=Ea / 1e3, A_per_s=A, rms_F=rms))
        I = cumulative_index(df["T_C"], df["duration_s"], cond, d_nm, P,
                             mode="growth", Ea=Ea)
        axes[0].plot(A * I, df["F"], "o", color=c, ms=4)
        axes[0].plot(x_th, EXTENT_MODELS[m](x_th), color=c, lw=1.4,
                     label=f"{m}: Ea={Ea/1e3:.0f} kJ, rms={rms:.3f}")
        axes[1].loglog(A * I, df["F"], "o-", color=c, ms=3, lw=0.8)
    xg = np.logspace(-4, 0, 10)
    for slope, ls in [(0.5, ":"), (1, "--"), (2, "-.")]:
        axes[1].loglog(xg, 0.5 * xg**slope, color="0.4", ls=ls, lw=0.8,
                       label=f"slope {slope}")
    axes[0].set_xlim(0, 3)
    axes[0].set_ylim(0, 1.02)
    axes[0].set_xlabel(r"$x = A\,I_{growth}$")
    axes[0].set_ylabel(r"cumulative $^3$He fraction $F$ (as $\alpha$)")
    axes[0].legend(fontsize=7)
    axes[1].set_xlabel(r"$x = A\,I_{growth}$ (each model's best $E_a$)")
    axes[1].set_ylabel(r"$F$")
    axes[1].set_title("low-F slope: 0.5 diffusion, 1 interface, n Avrami",
                      fontsize=9)
    axes[1].legend(fontsize=7)
    fig.suptitle(label or str(path))
    stem = f"{fname}_{Path(path).stem}"
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{stem}.{ext}", dpi=200)
    pd.DataFrame(rows).to_csv(OUTDIR / f"{stem}_fits.csv", index=False)
    return fig, pd.DataFrame(rows)


def make_pt_hydrated(sizes=(None, 100, 10), basis="equal_area",
                     fname="goethite_hematite_Ph2o_T_hydrated",
                     T_C=np.linspace(0.5, 400, 300)):
    """Main-text P-T diagram: hydrated surfaces only."""
    T = T_C + 273.15
    fig, ax = plt.subplots(figsize=(6.5, 5), constrained_layout=True)
    ax.plot(T_C, curve(T, -DG_UNC), color="0.6", lw=0.9, ls="-.",
            label=r"bulk, $\pm$1.4 kJ/mol FeOOH")
    ax.plot(T_C, curve(T, DG_UNC), color="0.6", lw=0.9, ls="-.")
    ax.plot(T_C, saturation_curve(T), color="tab:blue", ls=":", lw=1.2,
            label="H$_2$O liquid-vapor")
    for d in sizes:
        sh = dG_surf(d, "hydrated", basis)
        ax.plot(T_C, curve(T, sh), color=COLORS[d], lw=2,
                label=f"{LABEL(d)} ($\\Delta G_{{surf}}$ = {sh/1e3:+.2f} kJ)")
    ax.set_xlim(T_C[0], T_C[-1])
    ax.set_ylim(-6, LOGP_MAX)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel(r"log $P_{\mathrm{H_2O}}$ (bar)")
    ax.text(0.04, 0.95, r"$\alpha$-FeOOH", transform=ax.transAxes, va="top")
    ax.text(0.96, 0.05, r"$\alpha$-Fe$_2$O$_3$ + H$_2$O",
            transform=ax.transAxes, ha="right")
    ax.legend(fontsize=8, loc="center right")
    sec = ax.secondary_xaxis("top", functions=(lambda c: c + 273.15,
                                               lambda k: k - 273.15))
    sec.set_xlabel("Temperature (K)")
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig


def make_basis_sensitivity(sizes=(None, 1000, 100, 10),
                           fname="size_basis_sensitivity",
                           T_C=np.linspace(0.5, 400, 300)):
    """Supplement: hydrated surfaces, equal area per Fe vs equal diameter."""
    T = T_C + 273.15
    sat = saturation_curve(T)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True,
                             constrained_layout=True)
    for ax, basis, ttl in zip(axes, ("equal_area", "equal_diameter"),
                              ("(a) equal surface area per Fe",
                               "(b) equal particle diameter")):
        ax.plot(T_C, sat, color="tab:blue", ls=":", lw=1.2,
                label="H$_2$O liquid-vapor")
        for d in sizes:
            sh = dG_surf(d, "hydrated", basis)
            ax.plot(T_C, curve(T, sh), color=COLORS[d], lw=1.8,
                    label=f"{LABEL(d)} ($\\Delta G_{{surf}}$ = {sh/1e3:+.2f} kJ)")
        ax.set_title(ttl)
        ax.set_xlabel("Temperature (°C)")
        ax.set_xlim(T_C[0], T_C[-1])
        ax.set_ylim(-6, LOGP_MAX)
        ax.legend(fontsize=7.5, loc="lower right")
    axes[0].set_ylabel(r"log $P_{\mathrm{H_2O}}$ (bar)")
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig


if __name__ == "__main__":
    # Quick diagnostics
    for ds in DATASETS:
        g = dG_bulk(TR, PR, ds)   # water liquid at 1 bar
        print(f"{ds:8s} dG_r(298 K, 1 bar, liquid) = {g/1e3:+.2f} kJ/rxn "
              f"({-g/2e3:+.2f} kJ per FeOOH, >0 = goethite metastable)")
    for surf in GAMMA:
        for basis in ("equal_area", "equal_diameter"):
            print(surf, basis, {LABEL(d): round(dG_surf(d, surf, basis)/1e3, 2)
                                for d in SIZES})
    for basis in ("equal_area", "equal_diameter"):
        make_figure(basis)
    make_dmu_maps()
    make_dmu_vs_T()
    make_barrier_ratio()
    make_pt_hydrated()
    make_basis_sensitivity()
    # make_he_vs_index({'vacuum': 'vac.csv', 'hydrothermal': 'hyd.csv'},
    #                  gamma_eff=0.15)
    # make_extent_test('vac.csv', label='vacuum step heat')
