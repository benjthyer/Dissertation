"""
Is vacuum 3He release from Winsor goethite controlled by dehydroxylation
kinetics?  Calibrate on one schedule (KAF, LN2-trapped, with water data),
predict an independent schedule (HM, cycled T, water allowed to accumulate).

Model (per step, constant T, vacuum so the driving-force factor ~ 1):
    x   = A * sum_i  m_i * dt_i * exp(-Ea / R T_i)
    F   = (1 - phi) * alpha_model(x)          [reaction-controlled He]
    F   = sphere_F(x)                          [diffusion, D3; phi = 0]
m_i = s on KAF steps with the LN2 trap off (fitted), 1 otherwise.
phi = fraction of 3He retained through conversion (released later by
      diffusion from hematite / in fusion).

Inputs (same folder as this script):
    Winsor_waterKAF_BJT.csv   (3He PCC column, Pf = water per step, LN2?)
    HM_Win_06_01B.csv         (3HeCPS; last row = 850 C fusion)
Outputs -> ./generated/
"""
from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd
import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "gh", HERE / "goethite_hematite_phase_diagram.py")
gh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gh)
R, OUTDIR, MODELS = gh.R, gh.OUTDIR, gh.EXTENT_MODELS

KAF_FILE = HERE / "data/Winsor_waterKAF_BJT.csv"
HM_FILE = HERE / "data/HM_Win_06_01B.csv"
SHOW = ["F1 first order", "R3 contracting sphere", "D3 sphere diffusion"]
COL = {"F1 first order": "tab:red", "R3 contracting sphere": "tab:orange",
       "D3 sphere diffusion": "tab:blue"}


# ----------------------------------------------------------------------------
def load_kaf(path=KAF_FILE):
    k = pd.read_csv(path, skiprows=1, encoding="utf-8-sig")
    k = k[pd.to_numeric(k["Step"], errors="coerce").notna()].copy()
    for c in ["Step", "Time (h)", "Temp (C)", "Pi", "Pf", "3He PCC"]:
        k[c] = pd.to_numeric(k[c], errors="coerce")
    fus = k[k["Time (h)"] == 0].iloc[0]
    k = k[k["Time (h)"] > 0].copy()
    tot = k["3He PCC"].sum() + fus["3He PCC"]
    k["dF"] = k["3He PCC"] / tot
    k["F"] = k["dF"].cumsum()
    k["alpha_w"] = k["Pf"].cumsum() / k["Pf"].sum()   # water, norm. to 330 C
    k["noLN2"] = k["LN2?"].astype(str).str.strip().str.lower() == "no"
    k["t_cum"] = k["Time (h)"].cumsum()
    k = k.reset_index(drop=True)
    k.attrs["name"] = "KAF"
    return k


def load_hm(path=HM_FILE):
    h = pd.read_csv(path, encoding="utf-8-sig")
    h = h[["Step", "Temp (C)", "Time (h)", "3HeCPS"]].apply(
        pd.to_numeric, errors="coerce")
    fus = h[h["Step"].isna()]
    h = h[h["Step"].notna()].copy()
    tot = h["3HeCPS"].sum() + fus["3HeCPS"].sum()
    h["dF"] = h["3HeCPS"] / tot
    h["F"] = h["dF"].cumsum()
    h["t_cum"] = h["Time (h)"].cumsum()
    h = h.reset_index(drop=True)
    h.attrs["name"] = "HM"
    return h


# Fitting window (all steps are still plotted).  Step numbers as in the lab
# files.  KAF: steps 1-4 (70-165 C) are low-T non-conversion He; steps 24+
# (>= 290 C) sit on the hematite plateau.  HM: steps 2-7 (79-179 C) are
# low-T He; step 29+ (338.8 C onward) is on the hematite plateau.
WINDOW_STEPS = {"KAF": (5, 23), "HM": (8, 28)}
F_MAX = 0.89


def fit_window(df, F_max=F_MAX):
    name = df.attrs.get("name")
    m = df["F"].values < F_max
    if name in WINDOW_STEPS:
        lo, hi = WINDOW_STEPS[name]
        st = df["Step"].values
        m &= st >= lo
        if hi is not None:
            m &= st <= hi
    return m


def load_ht(path=None):
    """Hydrothermal run (liquid water), 3He from the cumulative column."""
    path = HERE / "data/Win0601bHT_distilled.csv" if path is None else path
    raw = pd.read_csv(path, encoding="utf-8-sig")
    raw.columns = [c.strip() for c in raw.columns]
    tcol = raw.columns[0]
    tot = raw[raw[tcol].astype(str).str.strip() == "Total"]
    tot3 = float(tot["Σ 3He (pccSTP)"].iloc[0])
    tot4 = float(tot["Σ 4He (nccSTP)"].iloc[0])
    d = raw[pd.to_numeric(raw[tcol], errors="coerce").notna()].copy()
    out = pd.DataFrame({"Temp (C)": pd.to_numeric(d[tcol]).values,
                        "Time (h)": pd.to_numeric(d["Minutes"]).values / 60})
    s3 = pd.to_numeric(d["Σ 3He (pccSTP)"]).values
    s4 = pd.to_numeric(d["Σ 4He (nccSTP)"]).values
    out["F"] = s3 / tot3
    d3, d4 = np.diff(np.r_[0, s3]), np.diff(np.r_[0, s4])
    out["r43"] = (d4 / d3) / (tot4 / tot3)
    out["t_cum"] = out["Time (h)"].cumsum()
    return out


# ----------------------------------------------------------------------------
def arrhenius_time(T_C, t_h, Ea, mult=None):
    T = np.asarray(T_C, float) + 273.15
    dt = np.asarray(t_h, float) * 3600.0
    if mult is not None:
        dt = dt * mult
    return np.cumsum(dt * np.exp(-Ea / (R * T)))


def predict(model, p, T_C, t_h, noLN2=None):
    Ea, lnA, lns, phi = p
    mult = None if noLN2 is None else np.where(noLN2, np.exp(lns), 1.0)
    x = np.exp(lnA) * arrhenius_time(T_C, t_h, Ea * 1e3, mult)
    return (1 - phi) * MODELS[model](x)


def fit_model(model, df, target="F", use_noLN2=True, window=True):
    """Least squares on cumulative target. p = (Ea kJ, lnA, ln s, phi).
    window=True: residuals only for steps inside fit_window (the whole
    schedule is still integrated)."""
    diff = model.startswith("D3") or target == "alpha_w"
    y = df[target].values
    w = fit_window(df) if window else np.ones(len(df), bool)
    nl = df["noLN2"].values if use_noLN2 else None
    best = None
    for Ea0 in (60, 100, 150, 200, 300):
        c0 = -np.log(arrhenius_time(df["Temp (C)"], df["Time (h)"],
                                    Ea0 * 1e3)[-1])
        p0 = [Ea0, c0, 0.0, 0.0 if diff else 0.1]
        lb = [20, -300, -6, 0.0]
        ub = [600, 300, 3, 1e-9 if diff else 0.5]
        r = least_squares(
            lambda p: (predict(model, p, df["Temp (C)"], df["Time (h)"], nl)
                       - y)[w],
            p0, bounds=(lb, ub))
        if best is None or r.cost < best.cost:
            best = r
    rms = np.sqrt(2 * best.cost / w.sum())
    return best.x, rms


# ----------------------------------------------------------------------------
def run(conv_T_max=320.0, fname="vacuum_kinetics_KAF_to_HM"):
    k, h = load_kaf(), load_hm()
    rows, fits = [], {}
    for m in MODELS:
        p, rms = fit_model(m, k, "F")
        pw, rmsw = fit_model(m, k, "alpha_w")
        FH = predict(m, p, h["Temp (C)"], h["Time (h)"])
        sel = fit_window(h)
        fits[m] = (p, FH)
        rows.append(dict(model=m, Ea_kJ=p[0], lnA=p[1],
                         noLN2_rate_factor=np.exp(p[2]), phi=p[3],
                         rms_KAF_He=rms,
                         rms_HM_pred=np.sqrt(np.mean((FH[sel] - h["F"][sel])**2)),
                         Ea_water_kJ=pw[0], rms_KAF_water=rmsw))
    tab = pd.DataFrame(rows)
    tab.to_csv(OUTDIR / f"{fname}_fits.csv", index=False)

    fig, ax = plt.subplots(2, 2, figsize=(12.5, 9), constrained_layout=True)
    # (a) KAF fit
    a = ax[0, 0]
    a.plot(k["t_cum"], k["F"], "ko", ms=4, label=r"$^3$He, $F$")
    phiF1 = fits["F1 first order"][0][3]
    a.plot(k["t_cum"], (1 - phiF1) * k["alpha_w"], "s", mfc="none",
           color="tab:green", ms=5, label=r"water, $(1-\phi)\,\alpha_w$")
    for m in SHOW:
        p = fits[m][0]
        a.plot(k["t_cum"], predict(m, p, k["Temp (C)"], k["Time (h)"],
                                   k["noLN2"].values),
               color=COL[m], lw=1.6, label=f"{m} (Ea {p[0]:.0f} kJ/mol)")
    for t in k.loc[k["noLN2"], "t_cum"]:
        a.axvspan(t - 1, t, color="tab:purple", alpha=0.15, lw=0)
    a.text(0.02, 0.97, "purple: LN$_2$ trap off", transform=a.transAxes,
           va="top", fontsize=8, color="tab:purple")
    a.set_title("(a) KAF: calibration (fit to $^3$He)")
    # (b) water vs He
    b = ax[0, 1]
    b.plot(k["alpha_w"], k["F"] / (1 - phiF1), "o-", color="0.3", ms=4)
    b.scatter(k.loc[k["noLN2"], "alpha_w"],
              k.loc[k["noLN2"], "F"] / (1 - phiF1), s=60, facecolor="none",
              edgecolor="tab:purple", zorder=3, label="LN$_2$ off")
    for i, r_ in k.iterrows():
        b.annotate(f"{r_['Temp (C)']:.0f}", (r_["alpha_w"],
                   r_["F"] / (1 - phiF1)), fontsize=6, color="0.5",
                   xytext=(3, -8), textcoords="offset points")
    b.plot([0, 1], [0, 1], "k--", lw=0.8)
    b.set_xlabel(r"water released, $\alpha_w$ (norm. to 330 °C)")
    b.set_ylabel(r"$F/(1-\phi)$, $^3$He")
    b.set_title("(b) KAF: does He track dehydroxylation?")
    b.legend(fontsize=8)
    # (c) HM prediction, cumulative
    c = ax[1, 0]
    c.plot(h["t_cum"], h["F"], "ko", ms=4, label="HM observed")
    for m in SHOW:
        c.plot(h["t_cum"], fits[m][1], color=COL[m], lw=1.6,
               label=f"{m} (predicted)")
    c.set_title("(c) HM: out-of-sample prediction from KAF")
    # (d) HM per step
    d = ax[1, 1]
    s = np.arange(len(h))
    d.semilogy(s, h["dF"], "ko", ms=4, label="HM observed")
    for m in SHOW:
        d.semilogy(s, np.diff(np.r_[0, fits[m][1]]).clip(1e-6), color=COL[m],
                   lw=1.4, drawstyle="steps-mid")
    d.set_ylim(1e-5, 0.3)
    d.set_xlabel("HM step")
    d.set_ylabel("fraction released per step")
    d.set_title("(d) HM per step (cycled schedule)")
    for axx in (a, c):
        axx.set_xlabel("cumulative heating time (h)")
        axx.set_ylabel(r"cumulative $^3$He fraction $F$")
        axx.set_ylim(0, 1.02)
        axx.legend(fontsize=7, loc="lower right")
        tw = axx.twinx()
        df_ = k if axx is a else h
        tw.step(df_["t_cum"], df_["Temp (C)"], where="pre", color="0.75",
                lw=1)
        tw.set_ylabel("T (°C)", color="0.5")
        tw.tick_params(colors="0.5")
    d2 = d.twinx()
    d2.plot(s, h["Temp (C)"], color="0.75", lw=1)
    d2.set_ylabel("T (°C)", color="0.5")
    d2.tick_params(colors="0.5")
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return tab, fig


def predict_schedule(T_C, t_h, model="F1 first order"):
    """Calibrate on KAF 3He, return (alpha, F) after each step of any vacuum
    (LN2-trapped) schedule.  F excludes the post-conversion hematite tail."""
    p, _ = fit_model(model, load_kaf(), "F")
    F = predict(model, p, T_C, t_h)
    return F / (1 - p[3]), F


# ----------------------------------------------------------------------------
# Arrhenius diagnostics: reaction rate constant vs diffusion D/a^2, per step
# ----------------------------------------------------------------------------
# A first-order (Mampel: each grain converts once nucleated) reaction gives a
# single line of ln k vs 1/T for BOTH schedules, including retrograde steps.
# Single-domain diffusion gives a single line of ln(D/a^2) vs 1/T.
# Whichever representation collapses KAF + HM onto one line is the better
# description of the controlling process.

def fk_Da2(F, t_h):
    """Fechtig & Kalbitzer (1966) sphere: per-step D/a^2 (1/s)."""
    F = np.clip(np.asarray(F, float), 0, 0.9999)
    x = np.where(F <= 0.85,
                 (2 * np.pi - np.pi**2 / 3 * F
                  - 2 * np.pi * np.sqrt(np.clip(1 - np.pi * F / 3, 0, None)))
                 / np.pi**2,
                 -np.log(np.pi**2 / 6 * (1 - F)) / np.pi**2)
    return np.diff(np.r_[0, x]) / (np.asarray(t_h) * 3600)


def first_order_k(F, t_h, phi, amax=0.98):
    a = np.asarray(F, float) / (1 - phi)
    a0 = np.r_[0, a[:-1]]
    k = -np.log((1 - np.clip(a, 0, amax)) / (1 - np.clip(a0, 0, amax)))
    k = k / (np.asarray(t_h) * 3600)
    return np.where((a < amax) & (k > 0), k, np.nan)


def _prograde(df):
    return np.r_[True, np.diff(df["Temp (C)"].values) >= -0.5]


def arrhenius_fit(x_invT, lnk):
    """OLS ln k = lnA - (Ea/R)(1/T). Returns Ea (kJ/mol), sigma, lnA, sigma."""
    (m, c), cov = np.polyfit(x_invT, lnk, 1, cov=True)
    return -m * R / 1e3, np.sqrt(cov[0, 0]) * R / 1e3, c, np.sqrt(cov[1, 1])


def step_lnk(df, phi):
    return np.log(first_order_k(df["F"], df["Time (h)"], phi, amax=0.999))


def vacuum_line(return_points=False):
    """Joint OLS Arrhenius line through first-order ln k of KAF + HM steps in
    fit_window, excluding LN2-off steps.  phi from the cumulative F1 fit."""
    k, h = load_kaf(), load_hm()
    phi = fit_model("F1 first order", k, "F")[0][3]
    X, Y, per = [], [], {}
    for df in (k, h):
        T = df["Temp (C)"].values + 273.15
        lk = step_lnk(df, phi)
        nl = df["noLN2"].values if "noLN2" in df else np.zeros(len(df), bool)
        u = fit_window(df) & ~nl & np.isfinite(lk)
        X.append(1 / T[u]); Y.append(lk[u])
        per[df.attrs["name"]] = arrhenius_fit(1 / T[u], lk[u])
    Ea, sEa, lnA, slnA = arrhenius_fit(np.concatenate(X), np.concatenate(Y))
    out = dict(Ea=Ea, sEa=sEa, lnA=lnA, slnA=slnA, phi=phi, per=per,
               n=sum(len(x) for x in X))
    return (out, (X, Y)) if return_points else out


def lnk_vac(T_C, line=None):
    line = vacuum_line() if line is None else line
    T = np.asarray(T_C, float) + 273.15
    return line["lnA"] - line["Ea"] * 1e3 / (R * T)


def make_arrhenius_comparison(fname="arrhenius_reaction_vs_diffusion",
                              include_ht=True):
    """ln k (first-order, nucleation-limited) and ln D/a^2 for every step of
    KAF, HM and (optionally) the hydrothermal run.  Arrhenius line fitted to
    KAF + HM steps inside fit_window, excluding LN2-off steps.  Steps whose F
    exceeds 1 - phi have no defined k and are absent from the left panel."""
    k, h = load_kaf(), load_hm()
    line = vacuum_line()
    phi = line["phi"]
    sets = [("KAF vacuum", k, "o", "k"), ("HM vacuum", h, "s", "0.35")]
    if include_ht and (HERE / "data/Win0601bHT_distilled.csv").exists():
        sets.append(("hydrothermal (liquid)", load_ht(), "^", "tab:blue"))

    fig, ax = plt.subplots(1, 2, figsize=(13, 5.4), constrained_layout=True)
    fitX, fitY, per = [], [], {}
    for lab, df, mk, col in sets:
        T = df["Temp (C)"].values + 273.15
        x = 1e4 / T
        lk = np.log(first_order_k(df["F"], df["Time (h)"], phi, amax=0.999))
        ld = np.log(fk_Da2(df["F"], df["Time (h)"]))
        up = _prograde(df)
        vac = "vacuum" in lab
        win = fit_window(df) if vac else np.zeros(len(df), bool)
        nl = df["noLN2"].values if "noLN2" in df else np.zeros(len(df), bool)
        use = win & ~nl & np.isfinite(lk)
        for a_, y in zip(ax, (lk, ld)):
            if vac:
                inn, out = use, ~use & ~nl
                a_.plot(x[inn & up], y[inn & up], mk, color=col, ms=5,
                        label=f"{lab}, fitted")
                a_.plot(x[inn & ~up], y[inn & ~up], mk, mfc="tab:cyan",
                        mec=col, ms=6, label=f"{lab}, retrograde, fitted")
                a_.plot(x[out], y[out], mk, mfc="none", mec=col, ms=5,
                        alpha=0.7, label=f"{lab}, not fitted")
                if nl.any():
                    a_.plot(x[nl], y[nl], "o", ms=11, mfc="none",
                            mec="tab:purple", label="KAF, LN$_2$ off (not fitted)")
            else:
                a_.plot(x[up], y[up], "^", color=col, ms=6,
                        label=f"{lab}, prograde")
                a_.plot(x[~up], y[~up], "v", color=col, mfc="white", ms=6,
                        label=f"{lab}, retrograde")
    Ea, sEa, lnA = line["Ea"], line["sEa"], line["lnA"]
    per = {f"{kk} vacuum": vv for kk, vv in line["per"].items()}
    xx = np.linspace(17.0, 23.0, 50)
    ax[0].plot(xx, lnA - Ea * 1e3 / R * (xx / 1e4), "r-", lw=1.5,
               label=f"fit KAF+HM: Ea = {Ea:.0f} ± {sEa:.0f} kJ/mol")
    for (lab, (e, se, c, _)), ls in zip(per.items(), ("--", ":")):
        ax[0].plot(xx, c - e * 1e3 / R * (xx / 1e4), "r", ls=ls, lw=0.9,
                   label=f"{lab} only: {e:.0f} ± {se:.0f} kJ/mol")
    ax[0].set_ylabel(r"ln $k$ (s$^{-1}$), first order: "
                     r"$k = -\ln[(1-\alpha_i)/(1-\alpha_{i-1})]/\Delta t$")
    ax[1].set_ylabel(r"ln $D/a^2$ (s$^{-1}$), Fechtig-Kalbitzer sphere")
    ax[0].set_title(rf"Reaction representation ($\alpha = F/(1-\phi)$, "
                    rf"$\phi$ = {phi:.3f})")
    ax[1].set_title("Diffusion representation")
    for a_ in ax:
        a_.set_xlabel(r"10$^4$/T (K$^{-1}$)")
        a_.set_xlim(16.8, 29.5)
        sec = a_.secondary_xaxis("top", functions=(
            lambda x: 1e4 / np.maximum(x, 1e-9) - 273.15,
            lambda c: 1e4 / (c + 273.15)))
        sec.set_xlabel("T (°C)")
    h_, l_ = ax[0].get_legend_handles_labels()
    uniq = dict(zip(l_, h_))
    ax[0].legend(uniq.values(), uniq.keys(), fontsize=6.5, loc="upper right")
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig, line


# ----------------------------------------------------------------------------
# Translating the vacuum kinetics to water saturation (nucleation control)
# ----------------------------------------------------------------------------
# If grains convert once a hematite nucleus forms (first-order / Mampel), the
# fitted k is a nucleation rate:  k = A exp(-Ea/RT) exp(-dG*/kT), with
# dG* = 16 pi g^3 V^2 / (3 dmu^2).  Same sample, same internal interface =>
# same gamma_eff; only dmu changes:
#   k_sat / k_vac = exp(-(C g^3 / T) (1/dmu_sat^2 - 1/dmu_vac^2)),
#   C = 16 pi V_hem^2 / (3 k_B).
# gamma_eff is calibrated from the LN2-off steps, where raising P_H2O slowed
# the isothermal rate by factor s:  ln(1/s) = (C g^3/T)(1/dmu_off^2 - 1/dmu_on^2).
# P_H2O during those steps is not known, so gamma_eff is given as a function
# of the assumed value.  Assumes the mobility term (A, Ea) is unchanged, i.e.
# the same solid-state mechanism; fluid-mediated dissolution-reprecipitation
# is NOT captured.

KB = 1.380649e-23
C_NUC = 16 * np.pi * gh.V_HEM**2 / (3 * KB)


def _dmu_bulk(T, P):
    return -gh.dG_bulk(T, P)


def trap_off_suppression(k=None, phi=None):
    """Isothermal first-order k on each LN2-off step vs mean of its
    trapped neighbours at the same T.  Returns list of (T_C, s)."""
    if k is None:
        k = load_kaf()
    if phi is None:
        phi = fit_model("F1 first order", k, "F")[0][3]
    kr = first_order_k(k["F"], k["Time (h)"], phi)
    out = []
    for i in np.where(k["noLN2"].values)[0]:
        T = k["Temp (C)"].iloc[i]
        nb = [j for j in (i - 1, i + 1) if 0 <= j < len(k)
              and k["Temp (C)"].iloc[j] == T and not k["noLN2"].iloc[j]]
        out.append((T, kr[i] / np.nanmean(kr[nb])))
    return out


def gamma_from_suppression(T_C, s, P_off_bar, P_on=None):
    T = T_C + 273.15
    P_on = gh.P_VAC if P_on is None else P_on
    m_on, m_off = _dmu_bulk(T, P_on), _dmu_bulk(T, P_off_bar * 1e5)
    return (np.log(1 / s) * T / (C_NUC * (1 / m_off**2 - 1 / m_on**2)))**(1 / 3)


def saturated_rate_factor(T_C, gamma_eff, P_vac=None):
    """k_sat / k_vac at water saturation (P = P_sat), same gamma_eff."""
    T = np.atleast_1d(np.asarray(T_C, float)) + 273.15
    P_vac = gh.P_VAC if P_vac is None else P_vac
    out = []
    for t in T:
        ps = CP.PropsSI("P", "T", t, "Q", 0, "Water")
        ms, mv = _dmu_bulk(t, ps * (1 + 1e-6)), _dmu_bulk(t, P_vac)
        out.append(0.0 if ms <= 0 else
                   np.exp(-(C_NUC * gamma_eff**3 / t) * (1 / ms**2 - 1 / mv**2)))
    return np.array(out)


def predict_hydrothermal(T_C, t_h, gamma_eff, line=None):
    """First-order conversion extent after each step of a water-saturated
    schedule: k_sat(T) = k_vac(T) * saturated_rate_factor(T, gamma_eff),
    k_vac from the vacuum Arrhenius line."""
    line = vacuum_line() if line is None else line
    fac = saturated_rate_factor(T_C, gamma_eff)
    kv = np.exp(lnk_vac(T_C, line))
    return 1 - np.exp(-np.cumsum(kv * fac * np.asarray(t_h) * 3600))


def synthetic_degeneracy_test(true_model="R3 contracting sphere", Ea=150e3,
                               fname="synthetic_degeneracy_test"):
    """Generate a noiseless vacuum release curve from one mechanism on (i) a
    monotonic 1 h schedule 150-390 C and (ii) a cycled schedule with long
    isothermal holds; fit every mechanism with Ea and A free.  Shows that a
    single schedule does not discriminate mechanisms."""
    rows = []
    scheds = {
        "monotonic": (np.arange(150, 400, 15), np.full(17, 1.0)),
        "cycled": (np.r_[np.arange(150, 300, 15), 200, 215, 230,
                         np.arange(300, 400, 15), 250, 250, 250],
                   np.r_[np.full(10, .5), .5, .5, .5, np.full(7, .5), 2, 2, 2]),
    }
    for sname, (T, t) in scheds.items():
        I = arrhenius_time(T, t, Ea)
        A = 0.9 / I[-1]
        F = MODELS[true_model](A * I)
        df = pd.DataFrame({"Temp (C)": T, "Time (h)": t, "F": F,
                           "condition": "vacuum", "Step": np.arange(len(T))})
        for m in MODELS:
            best = None
            for Ea0 in (40, 80, 150, 250, 400):
                c0 = -np.log(arrhenius_time(T, t, Ea0 * 1e3)[-1])
                r = least_squares(
                    lambda p: MODELS[m](np.exp(p[1]) * arrhenius_time(
                        T, t, p[0] * 1e3)) - F, [Ea0, c0],
                    bounds=([20, -300], [600, 300]))
                if best is None or r.cost < best.cost:
                    best = r
            rows.append(dict(schedule=sname, model=m, Ea_kJ=best.x[0],
                             rms_F=np.sqrt(2 * best.cost / F.size)))
    tab = pd.DataFrame(rows)
    tab.to_csv(OUTDIR / f"{fname}.csv", index=False)
    return tab


def log10_alpha_hydrothermal(T_C, t_h, gamma_eff, line=None):
    """log10 of predicted conversion (alpha << 1 limit, alpha ~ sum k dt),
    evaluated in log space so vanishing values do not underflow."""
    line = vacuum_line() if line is None else line
    T_C = np.asarray(T_C, float)
    T = T_C + 273.15
    lnfac = []
    for t in T:
        ps = CP.PropsSI("P", "T", t, "Q", 0, "Water")
        ms, mv = _dmu_bulk(t, ps * (1 + 1e-6)), _dmu_bulk(t, gh.P_VAC)
        lnfac.append(-np.inf if ms <= 0 else
                     -(C_NUC * gamma_eff**3 / t) * (1 / ms**2 - 1 / mv**2))
    terms = lnk_vac(T_C, line) + np.log(np.asarray(t_h) * 3600) + np.array(lnfac)
    m = terms.max()
    return (m + np.log(np.exp(terms - m).sum())) / np.log(10)


def predict_vacuum_first_order(T_C, t_h, line=None):
    line = vacuum_line() if line is None else line
    kv = np.exp(lnk_vac(T_C, line))
    return 1 - np.exp(-np.cumsum(kv * np.asarray(t_h) * 3600))


GAMMA_CAL = (0.14, 0.16, 0.19)   # J/m2: low, central, high (trap-off steps,
                                 # 190-600 mL volume, end/half-step P_H2O)


def make_delta_plot(fname="first_order_delta_lnk", gammas=GAMMA_CAL):
    """log10 k_obs - log10 k_pred.  Vacuum steps: k_pred from the vacuum
    line.  Hydrothermal steps: k_pred = vacuum line x saturated nucleation
    factor (gamma_eff central, bars = calibrated range).  Grey: hydrothermal
    against the dry line (no water correction), for reference."""
    line = vacuum_line()
    phi = line["phi"]
    L10 = np.log(10)
    fig, ax = plt.subplots(figsize=(12, 5.4), constrained_layout=True)
    for df, mk, col, lab in [(load_kaf(), "o", "k", "KAF vacuum"),
                             (load_hm(), "s", "0.35", "HM vacuum")]:
        T = df["Temp (C)"].values
        d = (step_lnk(df, phi) - lnk_vac(T, line)) / L10
        w = fit_window(df)
        nl = df["noLN2"].values if "noLN2" in df else np.zeros(len(df), bool)
        ax.plot(T[w & ~nl], d[w & ~nl], mk, color=col, ms=5,
                label=f"{lab} (fitted)")
        ax.plot(T[~w & ~nl], d[~w & ~nl], mk, mfc="none", mec=col, ms=5,
                label=f"{lab} (not fitted)")
        if nl.any():
            ax.plot(T[nl], d[nl], "o", ms=10, mfc="none", mec="tab:purple",
                    label="KAF, LN$_2$ off")
    ht = load_ht()
    T = ht["Temp (C)"].values
    lk = step_lnk(ht, phi)
    dry = (lk - lnk_vac(T, line)) / L10
    lo, mid, hi = [(lk - lnk_vac(T, line) - np.log(np.clip(
        saturated_rate_factor(T, g), 1e-300, None))) / L10 for g in gammas]
    up = _prograde(ht)
    ax.errorbar(T, mid, yerr=[mid - lo, hi - mid], fmt="none",
                ecolor="tab:blue", elinewidth=0.8, alpha=0.6)
    ax.plot(T[up], mid[up], "^", color="tab:blue", ms=6,
            label=rf"hydrothermal vs wet prediction ($\gamma_{{eff}}$ = "
                  rf"{gammas[1]}; bars {gammas[0]}-{gammas[2]} J/m$^2$)")
    ax.plot(T[~up], mid[~up], "v", color="tab:blue", mfc="white", ms=6)
    ax.plot(T, dry, "^", color="0.7", ms=4,
            label="hydrothermal vs dry line (no water correction)")
    ax.axhline(0, color="r", lw=1)
    ax.set_yscale("symlog", linthresh=2)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel(r"$\Delta\log_{10} k$ = log$_{10}k_{obs}$ - "
                  r"log$_{10}k_{pred}$ (orders of magnitude)")
    ax.set_title(f"First-order residuals; vacuum line Ea = "
                 f"{line['Ea']:.0f} ± {line['sEa']:.0f} kJ/mol")
    ax.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(1.01, 1))
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig


# Water pressure with the trap off (upper bounds): ideal gas at 298 K, water
# mass evolved in the step, apparatus volume 190-600 mL.
TRAP_OFF_WATER_MG = {230.0: 0.027, 240.0: 0.016}
V_APPARATUS_mL = (190.0, 600.0)


def trap_off_pressures(T_gas=298.15):
    out = {}
    for T_C, mg in TRAP_OFF_WATER_MG.items():
        n = mg * 1e-3 / 18.015
        out[T_C] = [n * R * T_gas / (V * 1e-6) for V in V_APPARATUS_mL]  # Pa
    return out


def make_hydrothermal_translation(fname="hydrothermal_translation"):
    sup = trap_off_suppression()
    Pw = trap_off_pressures()
    Poff = np.logspace(-5, -1, 40)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    lo = min(min(v) for v in Pw.values()) / 2 / 1e5
    hi = max(max(v) for v in Pw.values()) / 1e5
    ax[0].axvspan(lo, hi, color="0.9", zorder=0,
                  label="volume-constrained range")
    for T_C, s_ in sup:
        g = [gamma_from_suppression(T_C, s_, P) for P in Poff]
        ax[0].semilogx(Poff, g, lw=2,
                       label=f"{T_C:.0f} °C, rate ×{s_:.2f} with trap off")
    ax[0].set_xlabel(r"assumed $P_{H_2O}$ with LN$_2$ trap off (bar)")
    ax[0].set_ylabel(r"calibrated $\gamma_{eff}$ (J/m$^2$)")
    ax[0].set_title(r"(a) $\gamma_{eff}$ from the trap-off steps")
    ax[0].legend(fontsize=8)
    Tg = np.linspace(100, 370, 150)
    for g, ls in zip(GAMMA_CAL, ("--", "-", ":")):
        f = saturated_rate_factor(Tg, g)
        ax[1].semilogy(Tg, np.clip(f, 1e-300, None), "k", ls=ls,
                       label=rf"$\gamma_{{eff}}$ = {g} J/m$^2$")
    ax[1].semilogy(Tg, np.clip(saturated_rate_factor(Tg, 0.084), 1e-300,
                               None), color="0.6", lw=1,
                   label=r"$\gamma_{eff}$ = 0.084 (assumes 0.1 bar)")
    ax[1].set_ylim(1e-60, 2)
    ax[1].axvspan(150, 250, color="0.92", zorder=0)
    ax[1].set_xlabel("Temperature (°C)")
    ax[1].set_ylabel(r"$k_{sat}/k_{vac}$")
    ax[1].set_title("(b) predicted slowdown at water saturation")
    ax[1].legend(fontsize=8)
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig, sup, Pw


if __name__ == "__main__":
    tab, _ = run()
    _, arr = make_arrhenius_comparison()
    print("Arrhenius (ln k) fit:", arr)
    make_delta_plot()
    ht = load_ht()
    for g in (0.084,) + GAMMA_CAL:
        la = log10_alpha_hydrothermal(ht["Temp (C)"], ht["Time (h)"], g)
        print(f"HT schedule, gamma={g}: log10 predicted alpha = {la:.1f}")
    print("HT schedule, vacuum kinetics:",
          predict_vacuum_first_order(ht["Temp (C)"], ht["Time (h)"])[-1],
          " observed apparent alpha:", ht["F"].iloc[-1] / (1 - arr["phi"]))
    _, sup, Pw = make_hydrothermal_translation()
    print("trap-off suppression:", sup)
    for T_C, s_ in sup:
        for P in Pw[T_C]:
            print(f"  {T_C} C: P_end = {P:.1f} Pa -> gamma = "
                  f"{gamma_from_suppression(T_C, s_, P / 1e5):.3f}; "
                  f"P/2 -> {gamma_from_suppression(T_C, s_, P / 2e5):.3f}")
    synthetic_degeneracy_test()
    with pd.option_context("display.width", 160):
        print(tab.round(4).to_string(index=False))
