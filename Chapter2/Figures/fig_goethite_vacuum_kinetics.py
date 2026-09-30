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
import json
import importlib.util
import numpy as np
import pandas as pd
import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "gh", HERE / "fig_goethite_hematite_phase_diagram.py")
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
    h.attrs["name"] = "HDM"
    return h


# Fitting window (all steps are still plotted).  Step numbers as in the lab
# files.  KAF: steps 1-4 (70-165 C) are low-T non-conversion He; steps 24+
# (>= 290 C) sit on the hematite plateau.  HM: steps 2-7 (79-179 C) are
# low-T He; step 29+ (338.8 C onward) is on the hematite plateau.
WINDOW_STEPS_BASE = {"KAF": (5, 23), "HDM": (8, 28)}
# Trial (2026-09-29): exclude KAF step 23 (285 C) and HDM steps 27-28 (317 and
# 338 C) and everything after, i.e. no step at or above ~285/317 C is fitted.
# Set USE_TRIAL_WINDOW = False to restore the original 5-23 / 8-28 windows.
WINDOW_STEPS_TRIAL = {"KAF": (5, 22), "HDM": (8, 26)}
USE_TRIAL_WINDOW = True
WINDOW_STEPS = WINDOW_STEPS_TRIAL if USE_TRIAL_WINDOW else WINDOW_STEPS_BASE
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


LOW_SIGNAL_PCC = 0.1   # measured 3He below this is excluded (as in all Ch. 2 plots)


def load_ht(path=None):
    """Hydrothermal run (liquid water), reduced by the BOUNDING METHOD.

    The cumulative 3He released by the sample at the end of step i is bounded
    below by the measured cumulative 3He (residual ampoule inventory n_t = 0)
    and above by the measured cumulative plus n_t,UB (steady-state upper
    bound, Eq. eq:steadystate).  F is the midpoint of those bounds; F_LB and
    F_UB are the bounds.  ln(D/a^2) LB / m / UB are read directly from the
    distilled bounding-method table (Table tab:ch2-distilled-3he), as
    everywhere else in Chapter 2.  'use' marks steps whose bounds are defined
    (lambda t >= 4) and whose measured 3He >= LOW_SIGNAL_PCC; other steps are
    not plotted.
    """
    path = HERE / "data/Win0601bHT_distilled.csv" if path is None else path
    raw = pd.read_csv(path, encoding="utf-8-sig")
    raw.columns = [c.strip() for c in raw.columns]
    tcol = raw.columns[0]
    tot = raw[raw[tcol].astype(str).str.strip() == "Total"]
    tot3 = float(tot["Σ 3He (pccSTP)"].iloc[0])
    tot4 = float(tot["Σ 4He (nccSTP)"].iloc[0])
    d = raw[pd.to_numeric(raw[tcol], errors="coerce").notna()].copy()
    num = lambda c: pd.to_numeric(d[c], errors="coerce").values
    out = pd.DataFrame({"Temp (C)": num(tcol),
                        "Time (h)": num("Minutes") / 60})
    meas = num("3He Measured (pccSTP)")
    s3 = num("Σ 3He (pccSTP)")
    nt = num("ntUB 3He (pccSTP)")
    s4 = num("Σ 4He (nccSTP)")
    out["meas3"] = meas
    out["cum3"] = s3          # includes intervening permeation-step yields
    out["ntUB"] = nt
    out["F_LB"] = s3 / tot3
    out["F_UB"] = (s3 + np.nan_to_num(nt)) / tot3
    out["F"] = (s3 + 0.5 * np.nan_to_num(nt)) / tot3
    for tag in ("LB", "m", "UB"):
        out[f"lnDa2_{tag}"] = num(f"3He ln(d/a^2){tag}")
    out["use"] = np.isfinite(out["lnDa2_m"].values) & (meas >= LOW_SIGNAL_PCC)
    d3, d4 = np.diff(np.r_[0, s3]), np.diff(np.r_[0, s4])
    out["r43"] = (d4 / d3) / (tot4 / tot3)
    out["t_cum"] = out["Time (h)"].cumsum()
    out.attrs["name"] = "HT"
    out.attrs["tot3"] = tot3
    return out


def ht_lnk_bounds(ht, phi):
    """First-order ln k bounds for each hydrothermal step.  The step release
    is bounded by [dSigma - n_t,UB(i-1), dSigma + n_t,UB(i)] (dSigma: change in
    cumulative measured 3He, including intervening permeation-step yields --
    the convention of the table's ln(D/a^2)), applied from the central
    cumulative F before the step."""
    tot = ht.attrs["tot3"]
    S, nt = ht["cum3"].values, np.nan_to_num(ht["ntUB"].values)
    dS = np.diff(np.r_[0, S])
    lo = dS - np.r_[0, nt[:-1]]
    hi = dS + nt
    F0 = np.r_[0, ht["F"].values[:-1]]
    t = ht["Time (h)"].values * 3600
    res = []
    for w in (lo, hi):
        a0 = F0 / (1 - phi)
        a1 = (F0 + np.clip(w, 1e-12, None) / tot) / (1 - phi)
        res.append(np.log(-np.log((1 - a1) / (1 - a0)) / t))
    return res


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


def fit_model(model, df, target="F", use_noLN2=True, window=True,
              phi=None, phi_free=False):
    """Least squares on cumulative target. p = (Ea kJ, lnA, ln s, phi).
    window=True: residuals only for steps inside fit_window (the whole
    schedule is still integrated).

    phi handling: by default phi is free for the reaction models and fixed
    at 0 for D3 and for the water data.  phi=<float> fixes it at that value
    (e.g. the F1 hematite-inherited fraction, so that D3 can be compared on
    the same footing); phi_free=True frees it for D3 as well."""
    diff = (model.startswith("D3") or target == "alpha_w") and not phi_free
    y = df[target].values
    w = fit_window(df) if window else np.ones(len(df), bool)
    nl = df["noLN2"].values if use_noLN2 else None
    fixed = 0.0 if (diff and phi is None) else phi
    best = None
    for Ea0 in (60, 100, 150, 200, 300):
        c0 = -np.log(arrhenius_time(df["Temp (C)"], df["Time (h)"],
                                    Ea0 * 1e3)[-1])
        if fixed is None:
            q0, lb, ub = [Ea0, c0, 0.0, 0.1], [20, -300, -6, 0.0], [600, 300, 3, 0.5]
            full = lambda q: q
        else:
            q0, lb, ub = [Ea0, c0, 0.0], [20, -300, -6], [600, 300, 3]
            full = lambda q, f=fixed: np.r_[q, f]
        r = least_squares(
            lambda q: (predict(model, full(q), df["Temp (C)"], df["Time (h)"], nl)
                       - y)[w],
            q0, bounds=(lb, ub))
        if best is None or r.cost < best.cost:
            best, bfull = r, full
    rms = np.sqrt(2 * best.cost / w.sum())
    return bfull(best.x), rms


# ----------------------------------------------------------------------------
def run(conv_T_max=320.0, fname="vacuum_kinetics_KAF_to_HM"):
    """Fit every model to the cumulative KAF 3He release inside the fitting
    window, predict HDM, and fit the KAF water data.  D3 is fitted three
    ways: phi = 0 (pure diffusion, the default), phi fixed at the F1 value
    (same hematite-inherited fraction as the reaction fit), and phi free.
    The same fits are repeated with every step included ('all' columns,
    rms over all steps)."""
    k, h = load_kaf(), load_hm()
    rows, fits = [], {}
    phiF1 = fit_model("F1 first order", k, "F")[0][3]
    variants = [(m, m, {}) for m in MODELS] + [
        ("D3 sphere diffusion, phi = phi(F1)", "D3 sphere diffusion",
         dict(phi=phiF1)),
        ("D3 sphere diffusion, phi free", "D3 sphere diffusion",
         dict(phi_free=True))]
    for lab, m, kw in variants:
        p, rms = fit_model(m, k, "F", **kw)
        pw, rmsw = fit_model(m, k, "alpha_w")
        FH = predict(m, p, h["Temp (C)"], h["Time (h)"])
        sel = fit_window(h)
        pa, rmsa = fit_model(m, k, "F", window=False, **kw)
        FHa = predict(m, pa, h["Temp (C)"], h["Time (h)"])
        fits[lab] = (p, FH)
        rows.append(dict(model=lab, Ea_kJ=p[0], lnA=p[1],
                         noLN2_rate_factor=np.exp(p[2]), phi=p[3],
                         rms_KAF_He=rms,
                         rms_HM_pred=np.sqrt(np.mean((FH[sel] - h["F"][sel])**2)),
                         n_KAF=int(fit_window(k).sum()), n_HM=int(sel.sum()),
                         Ea_water_kJ=pw[0], rms_KAF_water=rmsw,
                         Ea_kJ_all=pa[0], phi_all=pa[3], rms_KAF_He_all=rmsa,
                         rms_HM_pred_all=np.sqrt(np.mean((FHa - h["F"])**2))))
    tab = pd.DataFrame(rows)
    tab.to_csv(OUTDIR / f"{fname}_fits.csv", index=False)

    fig, ax = plt.subplots(2, 2, figsize=(12.5, 9), constrained_layout=True)
    # (a) KAF fit
    a = ax[0, 0]
    a.plot(k["t_cum"], k["F"], "ko", ms=4, label=r"$^3$He, $F$")
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
    c.plot(h["t_cum"], h["F"], "ko", ms=4, label="HDM observed")
    for m in SHOW:
        c.plot(h["t_cum"], fits[m][1], color=COL[m], lw=1.6,
               label=f"{m} (predicted)")
    c.set_title("(c) HDM: out-of-sample prediction from KAF")
    # (d) HM per step
    d = ax[1, 1]
    s = np.arange(len(h))
    d.semilogy(s, h["dF"], "ko", ms=4, label="HDM observed")
    for m in SHOW:
        d.semilogy(s, np.diff(np.r_[0, fits[m][1]]).clip(1e-6), color=COL[m],
                   lw=1.4, drawstyle="steps-mid")
    d.set_ylim(1e-5, 0.3)
    d.set_xlabel("HDM step")
    d.set_ylabel("fraction released per step")
    d.set_title("(d) HDM per step (cycled schedule)")
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
                              include_ht=True, T_min_C=125.0, T_max_C=325.0):
    """Every 3He step of KAF, HDM and the hydrothermal run in two stacked
    representations, in the house Arrhenius style of
    winsor_goethite_Diffusivities_Arrhenius.pdf (fig_decomp_vs_hydrothermal.py):
    (a) first-order rate constants k_i (Eq. eq:gt_stepk) with the joint
    Arrhenius line fitted to KAF + HDM steps inside fit_window (LN2-off steps
    excluded); (b) Fechtig-Kalbitzer D/a^2.  Points of each experiment are
    joined in step order by dashed lines; prograde and retrograde steps are
    not distinguished.  Filled markers: vacuum steps used in the fit; open
    markers: vacuum steps outside the fitting window.  Large pink circles:
    the two KAF steps with the LN2 trap isolated.  Hydrothermal steps are
    bounding-method central values with lower/upper-bound bars (low-signal
    steps excluded).  Steps whose F exceeds 1 - phi have no defined k."""
    import matplotlib as mpl
    from matplotlib.lines import Line2D
    import sys
    sys.path.insert(0, str(HERE))
    from plot_style import apply_style

    k, h = load_kaf(), load_hm()
    line = vacuum_line()
    phi = line["phi"]
    sets = [("Vacuum: Farley et al., 2024 (KAF)", k, "o", "red"),
            ("Vacuum: Monteiro, 2017 (HDM)", h, "s", "orange")]
    if include_ht and (HERE / "data/Win0601bHT_distilled.csv").exists():
        sets.append(("Hydrothermal: this study", load_ht(), "D", "blue"))
    xlim = (1e4 / (T_max_C + 273.15), 1e4 / (T_min_C + 273.15))
    Ctemps = np.array([125, 150, 175, 200, 225, 250, 275, 300, 325])
    Ctemps = Ctemps[(Ctemps >= T_min_C) & (Ctemps <= T_max_C)]
    LN2_COL = "tab:pink"

    with mpl.rc_context():
        # side by side, two 6.4-in-wide panels; fonts scaled per plot_style's
        # convention so they print at the house size when the figure is
        # placed at full text width
        apply_style(scale=1.6)
        fig, ax = plt.subplots(1, 2, figsize=(12.8, 5.9))
        yrange = [[np.inf, -np.inf], [np.inf, -np.inf]]
        for lab, df, mk, col in sets:
            T = df["Temp (C)"].values + 273.15
            x = 1e4 / T
            lk = np.log(first_order_k(df["F"], df["Time (h)"], phi, amax=0.999))
            ld = np.log(fk_Da2(df["F"], df["Time (h)"]))
            ht = df.attrs.get("name") == "HT"
            if ht:
                ld = df["lnDa2_m"].values
                klo, khi = ht_lnk_bounds(df, phi)
                lo = (klo, df["lnDa2_LB"].values)
                hi = (khi, df["lnDa2_UB"].values)
                show = df["use"].values
                fitted = np.ones(len(df), bool)       # drawn filled
            else:
                show = np.ones(len(df), bool)
                nl = df["noLN2"].values if "noLN2" in df else np.zeros(len(df), bool)
                fitted = fit_window(df) & ~nl
            for i_ax, (a_, y) in enumerate(zip(ax, (lk, ld))):
                ok = show & np.isfinite(y)
                # sequential dashed connector (step order), no pro/retro split
                a_.plot(x[ok], y[ok], ls="--", lw=1, color=col, alpha=0.5, zorder=1)
                if ht:
                    a_.errorbar(x[ok], y[ok], yerr=[y[ok] - lo[i_ax][ok],
                                hi[i_ax][ok] - y[ok]], fmt="none", ecolor=col,
                                elinewidth=0.8, alpha=0.5, zorder=2)
                f_ = ok & fitted
                o_ = ok & ~fitted
                a_.plot(x[f_], y[f_], mk, color=col, ms=8, alpha=0.75, ls="",
                        zorder=3)
                a_.plot(x[o_], y[o_], mk, mfc="none", mec=col, ms=8, mew=1.5,
                        alpha=0.9, ls="", zorder=3)
                if not ht and "noLN2" in df:
                    n_ = ok & df["noLN2"].values
                    a_.plot(x[n_], y[n_], "o", ms=20, mfc="none", mec=LN2_COL,
                            mew=2.5, ls="", zorder=4)
                inx = ok & (x >= xlim[0]) & (x <= xlim[1])
                if inx.any():
                    lo_y = np.min(lo[i_ax][inx]) if ht else np.min(y[inx])
                    hi_y = np.max(hi[i_ax][inx]) if ht else np.max(y[inx])
                    yrange[i_ax] = [min(yrange[i_ax][0], lo_y), max(yrange[i_ax][1], hi_y)]
        Ea, sEa, lnA = line["Ea"], line["sEa"], line["lnA"]
        xx = np.linspace(*xlim, 50)
        ax[0].plot(xx, lnA - Ea * 1e3 / R * (xx / 1e4), "k-", lw=1.5, zorder=5)
        for i_ax, a_ in enumerate(ax):
            pad = 0.06 * (yrange[i_ax][1] - yrange[i_ax][0])
            a_.set_ylim(yrange[i_ax][0] - pad, yrange[i_ax][1] + pad)
            a_.set_xlim(xlim)
        ax[0].set_ylabel(r"$\ln k \left(sec^{-1}\right)$")
        ax[1].set_ylabel(r"$ln\left(\frac{D}{a^2}\right) \left(sec^{-1}\right)$")
        for a_ in ax:
            a_.set_xlabel(r"$10^{4}/T$ (K)")
            a_.grid(True, color="0.85", lw=0.8, zorder=0)
            a_.set_axisbelow(True)
        for a_, t_ in zip(ax, ("(a) first-order\nconversion",
                                "(b) volume diffusion\n(sphere)")):
            a_.text(0.97, 0.96, t_, transform=a_.transAxes, ha="right",
                    va="top", fontsize=18)
        for a_ in ax:
            top = a_.twiny()
            top.set_xlim(xlim)
            top.set_xticks(1e4 / (Ctemps[::2] + 273.15))
            top.set_xticklabels(Ctemps[::2])
            top.set_xlabel("Temperature (C)")
        handles = [Line2D([], [], marker=mk, color=col, ls="--", alpha=0.75,
                          label=lab) for lab, _, mk, col in sets]
        handles += [Line2D([], [], marker="o", mfc="none", mec="0.4", ls="",
                           label="outside fitting window"),
                    Line2D([], [], marker="o", ms=12, mfc="none", mec=LN2_COL,
                           mew=2, ls="", label="KAF, LN$_2$ trap isolated"),
                    Line2D([], [], color="k", lw=1.5,
                           label=f"first-order fit: $E_a$ = {Ea:.0f} $\\pm$ {sEa:.0f} kJ/mol")]
        fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=15,
                   frameon=False)
        fig.tight_layout(rect=(0, 0.13, 1, 1), w_pad=2)
        for ext in ("png", "pdf"):
            fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=300)
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
                             (load_hm(), "s", "0.35", "HDM vacuum")]:
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
    lk = step_lnk(ht, phi)[ht["use"].values]
    ht = ht[ht["use"].values].reset_index(drop=True)
    T = ht["Temp (C)"].values
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


# ----------------------------------------------------------------------------
# Water-inhibition rate laws: sensitivity of the hydrothermal prediction to the
# assumed functional form, an empirical bound from the hydrothermal data, and
# Monte Carlo propagation of the calibration uncertainties (added 2026-09-30,
# in response to review).
# ----------------------------------------------------------------------------
# Each law gives the ratio R = k(P_H2O) / k(P_on) of the conversion rate at a
# water pressure P to its rate in the trapped vacuum line (P_on = 1e-8 atm).
# Each is calibrated on the same trap-isolated steps, R(P_off) = s, and then
# applied at water saturation, P = P_sat(T), step by step through the
# hydrothermal schedule:  alpha = 1 - exp(-sum_i k_vac(T_i) R_i dt_i).
#   CNT        ln R = -(C g^3/T)(1/dmu(P)^2 - 1/dmu_on^2)  (g calibrated)
#   Langmuir   R = (1 + K P_on)/(1 + K P)   (site blocking; K calibrated and,
#              for lack of a temperature dependence, held constant)
#   power law  R = (P/P_on)^-n              (n calibrated)
#   linear     R = (1 - exp(-dmu(P)/RT)) / (1 - exp(-dmu_on/RT))  (TST, linear
#              in dmu near equilibrium; no free parameter -- it predicts s ~ 1
#              and cannot reproduce the trap-isolated slowdown)
P_ON_PA = gh.P_VAC / 1.0          # gh.P_VAC is in Pa
RATE_LAWS = ("CNT", "Langmuir", "power")
THERMO_UNC_J = 2.8e3              # +-1.4 kJ per FeOOH (Majzlan 2003) per reaction
N_MC = 4000


def _psat_pa(T):
    return CP.PropsSI("P", "T", T, "Q", 0, "Water")


def _dmu(T, P_pa, delta=0.0):
    """Bulk driving force (J/mol Fe2O3) with the thermodynamic offset delta
    (J per reaction, added to Delta G_r, i.e. subtracted from dmu)."""
    return _dmu_bulk(T, P_pa) - delta


def calibrate_law(law, T_C, s, P_off_pa, delta=0.0):
    """Return the law's free parameter from one trap-isolated step."""
    T = T_C + 273.15
    if law == "CNT":
        m_on, m_off = _dmu(T, P_ON_PA, delta), _dmu(T, P_off_pa, delta)
        return (np.log(1 / s) * T / (C_NUC * (1 / m_off**2 - 1 / m_on**2)))**(1 / 3)
    if law == "Langmuir":
        return (1 / s - 1) / (P_off_pa - P_ON_PA / s)
    if law == "power":
        return np.log(1 / s) / np.log(P_off_pa / P_ON_PA)
    raise ValueError(law)


_SCHED_CACHE = {}


def _sat_terms(T_C):
    """Cached P_sat (Pa) and bulk driving forces at saturation and in the
    trapped line, for each temperature (J/mol Fe2O3, no thermodynamic offset)."""
    key = tuple(np.round(np.atleast_1d(np.asarray(T_C, float)), 6))
    if key not in _SCHED_CACHE:
        T = np.array(key) + 273.15
        ps = np.array([_psat_pa(t) * (1 + 1e-6) for t in T])
        ms = np.array([_dmu(t, p) for t, p in zip(T, ps)])
        mv = np.array([_dmu(t, P_ON_PA) for t in T])
        _SCHED_CACHE[key] = (T, ps, ms, mv)
    return _SCHED_CACHE[key]


def ln_ratio_sat(law, par, T_C, delta=0.0):
    """ln(k_sat/k_vac) at water saturation for each temperature."""
    T, ps, ms, mv = _sat_terms(T_C)
    if law == "CNT":
        ms, mv = ms - delta, mv - delta
        with np.errstate(divide="ignore"):
            return np.where(ms > 0, -(C_NUC * par**3 / T) * (1 / ms**2 - 1 / mv**2),
                            -np.inf)
    if law == "Langmuir":
        return np.log((1 + par * P_ON_PA) / (1 + par * ps))
    if law == "power":
        return -par * np.log(ps / P_ON_PA)
    raise ValueError(law)


def log10_alpha_law(law, par, T_C, t_h, line, delta=0.0):
    """log10 of the predicted hydrothermal conversion alpha (exact first-order
    form, evaluated in log space so that vanishing values do not underflow)."""
    terms = (lnk_vac(T_C, line) + np.log(np.asarray(t_h, float) * 3600)
             + ln_ratio_sat(law, par, T_C, delta))
    m = terms.max()
    lnx = m + np.log(np.exp(terms - m).sum())          # ln(sum k dt)
    x = np.exp(lnx)
    return float(np.log10(-np.expm1(-x)) if x > 1e-12 else lnx / np.log(10))


def linear_law_s(T_C, P_off_pa):
    """Trap-off slowdown predicted by a law linear in dmu (no free parameter)."""
    T = T_C + 273.15
    f = lambda P: -np.expm1(-_dmu(T, P) / (R * T))
    return f(P_off_pa) / f(P_ON_PA)


def empirical_bounds(line, phi, detect_alpha=0.01):
    """Suppression factors R (uniform over the schedule) that (a) keep
    conversion below detect_alpha, and (b) would convert just enough goethite
    to supply ALL of the observed 3He release (alpha_obs = F/(1-phi)); any
    larger R is excluded by the data."""
    ht = load_ht()
    S = np.sum(np.exp(lnk_vac(ht["Temp (C)"], line)) * ht["Time (h)"] * 3600)
    a_obs = float(ht["F"].iloc[-1]) / (1 - phi)
    return dict(sum_kdt=S, alpha_obs=a_obs,
                log10R_detect=np.log10(-np.log(1 - detect_alpha) / S),
                log10R_obs=np.log10(-np.log(1 - a_obs) / S),
                log10R_obs_nuc=None)


def trap_off_s_variants(phi_F1=None, phi_R3=None):
    """Trap-isolated slowdown s for each trap-off step under several
    reductions: first-order (F1) and contracting-sphere (R3) step rate
    constants, each against the mean of the two trapped neighbours and
    against each neighbour alone.  Returns {T_C: [s values]}."""
    k = load_kaf()
    if phi_F1 is None:
        phi_F1 = fit_model("F1 first order", k, "F")[0][3]
    if phi_R3 is None:
        phi_R3 = fit_model("R3 contracting sphere", k, "F")[0][3]
    t = k["Time (h)"].values * 3600
    a1 = np.clip(k["F"].values / (1 - phi_F1), 0, 0.999)
    kF1 = -np.log((1 - a1) / (1 - np.r_[0, a1[:-1]])) / t
    a3 = np.clip(k["F"].values / (1 - phi_R3), 0, 0.999)
    g3 = 1 - (1 - a3)**(1 / 3)
    kR3 = np.diff(np.r_[0, g3]) / t
    out = {}
    for i in np.where(k["noLN2"].values)[0]:
        T = float(k["Temp (C)"].iloc[i])
        nb = [j for j in (i - 1, i + 1) if 0 <= j < len(k)
              and k["Temp (C)"].iloc[j] == T and not k["noLN2"].iloc[j]]
        vals = []
        for kk in (kF1, kR3):
            vals += [kk[i] / np.mean(kk[nb])] + [kk[i] / kk[j] for j in nb]
        out[T] = vals
    return out


def rate_law_table(line, sup=None):
    """Deterministic calibration grid (as in the text: two steps x two
    apparatus volumes x end-of-step or half pressure) for every law:
    free parameter, k_sat/k_vac at 250 C, and log10 alpha for the schedule."""
    ht = load_ht()
    sup = dict(trap_off_suppression() if sup is None else sup)
    Pw = trap_off_pressures()
    rows = []
    for T_C, s_ in sup.items():
        for V, P_end in zip(V_APPARATUS_mL, Pw[T_C]):
            for pf in (1.0, 0.5):
                P = P_end * pf
                for law in RATE_LAWS:
                    par = calibrate_law(law, T_C, s_, P)
                    rows.append(dict(
                        law=law, T_C=T_C, s=s_, V_mL=V, P_frac=pf, P_off_Pa=P,
                        par=par,
                        log10_R250=float(ln_ratio_sat(law, par, 250.0)[0] / np.log(10)),
                        log10_alpha=float(log10_alpha_law(
                            law, par, ht["Temp (C)"], ht["Time (h)"], line))))
                rows.append(dict(law="linear", T_C=T_C, s=s_, V_mL=V, P_frac=pf,
                                 P_off_Pa=P, par=np.nan,
                                 s_pred=float(linear_law_s(T_C, P))))
    tab = pd.DataFrame(rows)
    tab.to_csv(OUTDIR / "hydrothermal_rate_law_sensitivity.csv", index=False)
    return tab


def rate_law_monte_carlo(line, n=N_MC, seed=20260930):
    """Propagate the calibration uncertainties into log10 alpha for each law.
    Sampled: the trap-off step (230 or 240 C); s from its reduction range
    (F1/R3, neighbour mean or either neighbour; log-uniform between the
    extremes); apparatus volume (log-uniform 190-600 mL); time-averaged
    pressure fraction (uniform 0.5-1 of the end-of-step value); and, for CNT
    only, a common offset of Delta G_r (uniform +-2.8 kJ per reaction), which
    shifts every driving force together."""
    rng = np.random.default_rng(seed)
    ht = load_ht()
    sv = trap_off_s_variants()
    temps = sorted(sv)
    out = {law: [] for law in RATE_LAWS}
    out["gamma"] = []
    for _ in range(n):
        T_C = temps[rng.integers(len(temps))]
        lo, hi = np.log(min(sv[T_C])), np.log(max(sv[T_C]))
        s_ = np.exp(rng.uniform(lo, hi))
        V = np.exp(rng.uniform(*np.log(V_APPARATUS_mL))) * 1e-6
        n_w = TRAP_OFF_WATER_MG[T_C] * 1e-3 / 18.015
        P = n_w * R * 298.15 / V * rng.uniform(0.5, 1.0)
        delta = rng.uniform(-THERMO_UNC_J, THERMO_UNC_J)
        for law in RATE_LAWS:
            d = delta if law == "CNT" else 0.0
            par = calibrate_law(law, T_C, s_, P, d)
            if law == "CNT":
                out["gamma"].append(par)
            out[law].append(log10_alpha_law(law, par, ht["Temp (C)"],
                                            ht["Time (h)"], line, d))
    res = {}
    for key, v in out.items():
        v = np.asarray(v, float)
        res[key] = dict(p2_5=float(np.percentile(v, 2.5)),
                        p50=float(np.percentile(v, 50)),
                        p97_5=float(np.percentile(v, 97.5)))
    res["s_variants"] = {str(k): [float(x) for x in v] for k, v in sv.items()}
    return res


def cnt_scales(gamma, T_C=250.0):
    """Critical radius (nm) and formula units in the critical nucleus, and the
    barrier (k_B T), in vacuum and at saturation."""
    T = T_C + 273.15
    fu = gh.V_HEM / 6.02214076e23
    out = {}
    for tag, P in (("vac", P_ON_PA), ("sat", _psat_pa(T) * (1 + 1e-6))):
        m = _dmu(T, P)
        r = 2 * gamma * gh.V_HEM / m
        out[tag] = dict(r_nm=r * 1e9, n_fu=(4 / 3 * np.pi * r**3) / fu,
                        barrier_kBT=C_NUC * gamma**3 / (T * m**2))
    return out


# ----------------------------------------------------------------------------
# Statistics cache + LaTeX macros for Chapter 2
# ----------------------------------------------------------------------------
# Every kinetic-fit statistic quoted in Chapter 2 (main text and SI) is read
# from Chapter2/Writing/chapter2_kinetics_values.tex, written here, so the
# text cannot drift from the fits.  Do not edit that file by hand; re-run
# this script (or run_all_figures.py).
MACRO_PATH = HERE.parent / "Writing" / "chapter2_kinetics_values.tex"
CACHE_PATH = OUTDIR / "data" / "goethite_kinetics_cache.json"
KB_J, H_J = 1.380649e-23, 6.62607015e-34


def residual_stats(line=None):
    """rms of the vacuum first-order residuals (log10 units) in the fitting
    window, and the offsets of the two trap-isolated KAF steps."""
    line = vacuum_line() if line is None else line
    phi = line["phi"]
    out = {}
    for df in (load_kaf(), load_hm()):
        T = df["Temp (C)"].values
        d = (step_lnk(df, phi) - lnk_vac(T, line)) / np.log(10)
        w = fit_window(df)
        nl = df["noLN2"].values if "noLN2" in df else np.zeros(len(df), bool)
        out[df.attrs["name"]] = float(np.sqrt(np.nanmean(d[w & ~nl]**2)))
        if nl.any():
            out["trap_offsets"] = [float(x) for x in d[nl]]
    return out


def _f(x, nd):
    return f"{x:.{nd}f}"


def _sig(x, sf=2):
    """Round to sf significant figures and print without trailing exponent."""
    if x == 0:
        return "0"
    e = int(np.floor(np.log10(abs(x))))
    nd = max(sf - e - 1, 0)
    return f"{round(x, nd):.{nd}f}"


def _sci(x, sf=2):
    e = int(np.floor(np.log10(abs(x))))
    return f"{x / 10**e:.{sf - 1}f}\\times10^{{{e}}}"


def _win_temps(df):
    """'Tlo--Thi' (deg C, rounded) of the steps inside the fitting window."""
    T = df["Temp (C)"].values[fit_window(df)]
    return f"{T.min():.0f}--{T.max():.0f}"


def make_rate_law_figure(tab, mc, bounds, fname="hydrothermal_rate_law_sensitivity"):
    """Predicted hydrothermal conversion for each water-inhibition law:
    deterministic calibration grid (thick bars) and Monte Carlo 95% range
    (thin bars), against the empirical bounds from the hydrothermal data."""
    from plot_style import apply_style
    with plt.rc_context():
        apply_style(scale=0.125 * 9.0 / 1.0)
        fig, ax = plt.subplots(figsize=(9.0, 4.2), constrained_layout=True)
        labels = {"CNT": "nucleation\n(CNT, $\\gamma^3/\\Delta\\mu^2$)",
                  "Langmuir": "site blocking\n(Langmuir)",
                  "power": "power law\n($P^{-n}$)"}
        for y, law in enumerate(RATE_LAWS[::-1]):
            d = tab[tab.law == law]["log10_alpha"]
            ax.plot([mc[law]["p2_5"], mc[law]["p97_5"]], [y, y], color="0.3",
                    lw=1.5, solid_capstyle="butt")
            ax.plot([d.min(), d.max()], [y, y], color="tab:blue", lw=9,
                    solid_capstyle="butt")
            ax.plot(mc[law]["p50"], y, "o", color="white", mec="k", ms=7, zorder=3)
        a_det = np.log10(0.01)
        a_obs = np.log10(bounds["alpha_obs"])
        ax.axvline(a_det, color="tab:green", ls="--", lw=1.5)
        ax.axvline(a_obs, color="tab:red", ls="-", lw=1.5)
        ax.text(a_det - 0.8, 2.45, "1% conversion", color="tab:green",
                ha="right", va="center", fontsize="small")
        ax.annotate("all observed $^3$He\nfrom conversion", xy=(a_obs, 0.45),
                    xytext=(a_det - 3.0, 0.45), color="tab:red", ha="right",
                    va="center", fontsize="small",
                    arrowprops=dict(arrowstyle="->", color="tab:red", lw=1.2))
        ax.axvspan(a_obs, 0.5, color="tab:red", alpha=0.08)
        from matplotlib.lines import Line2D
        ax.legend(handles=[
            Line2D([], [], color="tab:blue", lw=9, label="calibration grid"),
            Line2D([], [], color="0.3", lw=1.5, marker="o", mfc="white", mec="k",
                   label="Monte Carlo median, 95%")],
            loc="lower left", fontsize="small", handlelength=1.6)
        ax.set_yticks(range(len(RATE_LAWS)))
        ax.set_yticklabels([labels[l] for l in RATE_LAWS[::-1]])
        ax.set_ylim(-0.8, 2.8)
        ax.set_xlim(-72, 2)
        ax.set_xlabel(r"predicted hydrothermal conversion, $\log_{10}\alpha$")
        for ext in ("png", "pdf"):
            fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=300)
    return fig


def rate_law_macros(line, sup):
    """Macros for the rate-law sensitivity, the empirical bounds, the Monte
    Carlo propagation and the CNT length scales (Chapter 2 nucleation section
    and SI)."""
    tab = rate_law_table(line, sup)
    mc = rate_law_monte_carlo(line)
    bd = empirical_bounds(line, line["phi"])
    make_rate_law_figure(tab, mc, bd)
    g = lambda law, c: tab[tab.law == law][c]
    M = {"ChTwoKinSumKdt": _f(bd["sum_kdt"], 0),
         "ChTwoKinLogRDetect": _f(bd["log10R_detect"], 1),
         "ChTwoKinLogRObs": _f(bd["log10R_obs"], 1),
         "ChTwoKinLinearS": _f(g("linear", "s_pred").min(), 3),
         "ChTwoKinNMC": str(N_MC)}
    for law, tag in (("CNT", "CNT"), ("Langmuir", "Lang"), ("power", "Pow")):
        r, a = g(law, "log10_R250"), g(law, "log10_alpha")
        M[f"ChTwoKin{tag}LogRLo"] = _f(r.min(), 1)
        M[f"ChTwoKin{tag}LogRHi"] = _f(r.max(), 1)
        M[f"ChTwoKin{tag}LogAlphaLo"] = _f(a.min(), 1)
        M[f"ChTwoKin{tag}LogAlphaHi"] = _f(a.max(), 1)
        M[f"ChTwoKinMC{tag}Lo"] = _f(mc[law]["p2_5"], 1)
        M[f"ChTwoKinMC{tag}Mid"] = _f(mc[law]["p50"], 1)
        M[f"ChTwoKinMC{tag}Hi"] = _f(mc[law]["p97_5"], 1)
    pw = g("power", "log10_alpha")
    M["ChTwoKinPowAlphaLo"] = _f(10**pw.min(), 2)
    M["ChTwoKinPowAlphaHi"] = _f(10**pw.max(), 2)
    M["ChTwoKinMCPowAlphaLo"] = _f(10**mc["power"]["p2_5"], 2)
    M["ChTwoKinLangKLo"] = _sig(g("Langmuir", "par").min())
    M["ChTwoKinLangKHi"] = _sig(g("Langmuir", "par").max())
    M["ChTwoKinPowNLo"] = _f(g("power", "par").min(), 2)
    M["ChTwoKinPowNHi"] = _f(g("power", "par").max(), 2)
    M["ChTwoKinGammaLo"] = _f(g("CNT", "par").min(), 2)
    M["ChTwoKinGammaHi"] = _f(g("CNT", "par").max(), 2)
    M["ChTwoKinMCGammaLo"] = _f(mc["gamma"]["p2_5"], 2)
    M["ChTwoKinMCGammaHi"] = _f(mc["gamma"]["p97_5"], 2)
    sv = mc["s_variants"]
    M["ChTwoKinSLowRange"] = f"{min(sv['230.0']):.2f}--{max(sv['230.0']):.2f}"
    M["ChTwoKinSHighRange"] = f"{min(sv['240.0']):.2f}--{max(sv['240.0']):.2f}"
    lo, hi = cnt_scales(GAMMA_CAL[0]), cnt_scales(GAMMA_CAL[2])
    for tag, key, nd in (("Rstar", "r_nm", 2), ("Nfu", "n_fu", 2), ("Bar", "barrier_kBT", 1)):
        for ph, PH in (("vac", "Vac"), ("sat", "Sat")):
            v0, v1 = lo[ph][key], hi[ph][key]
            if ph == "sat" and tag != "Rstar":
                M[f"ChTwoKin{tag}{PH}"] = f"{v0:.0f}--{v1:.0f}"
            elif ph == "sat":
                M[f"ChTwoKin{tag}{PH}"] = f"{v0:.1f}--{v1:.1f}"
            else:
                M[f"ChTwoKin{tag}{PH}"] = f"{v0:.{nd}f}--{v1:.{nd}f}"
    return M, dict(table=tab.to_dict(orient="records"), monte_carlo=mc, bounds=bd)


def write_kinetics_macros(tab, line, sup, resid, synth):
    t = tab.set_index("model")
    F1, R2, R3 = (t.loc[m] for m in ("F1 first order", "R2 contracting cylinder",
                                      "R3 contracting sphere"))
    D3 = t.loc["D3 sphere diffusion"]
    D3p = t.loc["D3 sphere diffusion, phi = phi(F1)"]
    D3f = t.loc["D3 sphere diffusion, phi free"]
    T250 = 250 + 273.15
    k250 = np.exp(line["lnA"] - line["Ea"] * 1e3 / (R * T250))
    n_grain = (np.pi * 1e-6**3 / 6) / (gh.V_GOE / 6.02214076e23)
    ceiling = np.log(n_grain * KB_J * T250 / H_J / k250)
    ht_ = load_ht()
    t_ht = ht_["Time (h)"].sum() * 3600
    # detectability: ln(sum_i k_vac(T_i) dt_i / 0.01) over the actual schedule
    detect = np.log(np.sum(np.exp(lnk_vac(ht_["Temp (C)"], line))
                           * ht_["Time (h)"] * 3600) / 0.01)
    la = {g: log10_alpha_hydrothermal(ht_["Temp (C)"], ht_["Time (h)"], g, line)
          for g in (0.084,) + GAMMA_CAL}
    F_end = float(ht_["F"].iloc[-1])
    alpha_perm = 10**la[0.084]
    e_ = int(np.floor(np.log10(alpha_perm)))
    alpha_perm_s = f"{round(alpha_perm / 10**e_):.0f}\\times10^{{{e_}}}"
    M_rl, rl_cache = rate_law_macros(line, sup)
    sup = dict(sup)
    M = {
        # cumulative F1 fit to KAF (fitting window)
        "ChTwoKinFOneEa": _f(F1.Ea_kJ, 1), "ChTwoKinFOneLnA": _f(F1.lnA, 2),
        "ChTwoKinPhi": _f(F1.phi, 3), "ChTwoKinS": _f(F1.noLN2_rate_factor, 2),
        "ChTwoKinFOneRmsKAF": _sig(F1.rms_KAF_He), "ChTwoKinFOneRmsHDM": _sig(F1.rms_HM_pred),
        "ChTwoKinNKAF": str(int(F1.n_KAF)), "ChTwoKinNHDM": str(int(F1.n_HM)),
        "ChTwoKinWinKAF": "{}--{}".format(*WINDOW_STEPS["KAF"]),
        "ChTwoKinWinHDM": "{}--{}".format(*WINDOW_STEPS["HDM"]),
        "ChTwoKinWinKAFT": _win_temps(load_kaf()), "ChTwoKinWinHDMT": _win_temps(load_hm()),
        # D3: phi = 0, phi = phi(F1), phi free
        "ChTwoKinDThreeEa": _f(D3.Ea_kJ, 0),
        "ChTwoKinDThreeRmsKAF": _sig(D3.rms_KAF_He), "ChTwoKinDThreeRmsHDM": _sig(D3.rms_HM_pred),
        "ChTwoKinDThreeRmsRatio": _f(D3.rms_KAF_He / F1.rms_KAF_He, 1),
        "ChTwoKinDThreePhiEa": _f(D3p.Ea_kJ, 0),
        "ChTwoKinDThreePhiRmsKAF": _sig(D3p.rms_KAF_He), "ChTwoKinDThreePhiRmsHDM": _sig(D3p.rms_HM_pred),
        "ChTwoKinDThreePhiRmsRatio": _f(D3p.rms_KAF_He / F1.rms_KAF_He, 1),
        "ChTwoKinDThreePhiS": _f(D3p.noLN2_rate_factor, 2),
        "ChTwoKinDThreeFreeEa": _f(D3f.Ea_kJ, 0), "ChTwoKinDThreeFreePhi": _f(D3f.phi, 3),
        "ChTwoKinDThreeFreeRmsKAF": _sig(D3f.rms_KAF_He), "ChTwoKinDThreeFreeRmsHDM": _sig(D3f.rms_HM_pred),
        # KAF water
        "ChTwoKinWaterEa": _f(F1.Ea_water_kJ, 1), "ChTwoKinWaterRms": _sig(F1.rms_KAF_water),
        # all steps included
        "ChTwoKinAllFOneEa": _f(F1.Ea_kJ_all, 1), "ChTwoKinAllPhi": _f(F1.phi_all, 3),
        "ChTwoKinAllFOneRmsKAF": _sig(F1.rms_KAF_He_all), "ChTwoKinAllFOneRmsHDM": _sig(F1.rms_HM_pred_all),
        "ChTwoKinAllRThreeEa": _f(R3.Ea_kJ_all, 1), "ChTwoKinAllRThreeRmsKAF": _sig(R3.rms_KAF_He_all),
        "ChTwoKinAllRThreeRmsHDM": _sig(R3.rms_HM_pred_all),
        "ChTwoKinAllRTwoEa": _f(R2.Ea_kJ_all, 1), "ChTwoKinAllRTwoRmsKAF": _sig(R2.rms_KAF_He_all),
        "ChTwoKinAllRTwoRmsHDM": _sig(R2.rms_HM_pred_all),
        "ChTwoKinAllDThreeEa": _f(D3.Ea_kJ_all, 1), "ChTwoKinAllDThreeRmsKAF": _sig(D3.rms_KAF_He_all),
        "ChTwoKinAllDThreeRmsHDM": _sig(D3.rms_HM_pred_all),
        "ChTwoKinAllDThreePhiRmsKAF": _sig(D3p.rms_KAF_He_all),
        "ChTwoKinAllDThreePhiRmsHDM": _sig(D3p.rms_HM_pred_all),
        # joint Arrhenius line through the step rate constants
        "ChTwoKinLineEa": _f(line["Ea"], 1), "ChTwoKinLineEaErr": _f(line["sEa"], 1),
        "ChTwoKinLineLnA": _f(line["lnA"], 2), "ChTwoKinLineLnAErr": _f(line["slnA"], 2),
        "ChTwoKinLineN": str(int(line["n"])),
        "ChTwoKinKAFEa": _f(line["per"]["KAF"][0], 1), "ChTwoKinKAFEaErr": _f(line["per"]["KAF"][1], 1),
        "ChTwoKinHDMEa": _f(line["per"]["HDM"][0], 1), "ChTwoKinHDMEaErr": _f(line["per"]["HDM"][1], 1),
        "ChTwoKinKTwoFifty": _sci(k250), "ChTwoKinConvPerHour": _f(100 * (1 - np.exp(-k250 * 3600)), 0),
        "ChTwoKinCeiling": _f(ceiling, 0), "ChTwoKinDetect": _f(detect, 0),
        # phi-dependent quantities for the hydrothermal translation
        "ChTwoKinPhiPct": _f(100 * F1.phi, 0), "ChTwoKinOneMinusPhi": _f(1 - F1.phi, 3),
        # truncated (not rounded) to match the "14.7%" total 3He yield quoted in the text
        "ChTwoKinHTFEnd": _f(np.floor(F_end * 1000) / 1000, 3),
        "ChTwoKinHTAlphaObs": _f(np.floor(F_end * 1000) / 1000 / (1 - F1.phi), 2),
        "ChTwoKinLogAlphaLow": _f(la[GAMMA_CAL[0]], 1), "ChTwoKinLogAlphaMid": _f(la[GAMMA_CAL[1]], 1),
        "ChTwoKinLogAlphaHigh": _f(la[GAMMA_CAL[2]], 1), "ChTwoKinAlphaPermissive": alpha_perm_s,
        # trap-isolated steps and residuals
        "ChTwoKinTrapSuppLow": _f(sup[230.0], 2), "ChTwoKinTrapSuppHigh": _f(sup[240.0], 2),
        "ChTwoKinResidRmsKAF": _f(resid["KAF"], 2), "ChTwoKinResidRmsHDM": _f(resid["HDM"], 2),
        "ChTwoKinTrapResidLow": _f(-resid["trap_offsets"][0], 2),
        "ChTwoKinTrapResidHigh": _f(-resid["trap_offsets"][1], 2),
    }
    M.update(M_rl)
    # model-fit table rows (SI Table tab:gt_mech_fits)
    short = {"R2 contracting cylinder": "R2", "R3 contracting sphere": "R3",
             "F1 first order": "F1", "A2 Avrami n=2": "A2", "A3 Avrami n=3": "A3",
             "D3 sphere diffusion": "D3, $\\phi=0$",
             "D3 sphere diffusion, phi = phi(F1)": "D3, $\\phi=\\phi_{\\mathrm{F1}}$",
             "D3 sphere diffusion, phi free": "D3, $\\phi$ free"}
    rows = []
    for m, r in t.iterrows():
        lb = "$^{a}$" if r.Ea_kJ <= 20.0001 else ""
        lbw = "$^{a}$" if r.Ea_water_kJ <= 20.0001 else ""
        lnA = _f(r.lnA, 2)
        lnA = f"${lnA}$" if r.lnA < 0 else lnA
        water = "---" if "," in m else _f(r.Ea_water_kJ, 1) + lbw
        rows.append(f"{short[m]} & {_f(r.Ea_kJ, 1)}{lb} & {lnA} & {_f(r.phi, 3)} & "
                    f"{_f(r.noLN2_rate_factor, 2)} & {_f(r.rms_KAF_He, 4)} & "
                    f"{_f(r.rms_HM_pred, 4)} & {water} \\\\")
    M["ChTwoKinMechFitRows"] = "\n".join(rows)
    # synthetic degeneracy table rows (SI Table tab:gt_synth)
    sy = synth.pivot(index="model", columns="schedule")
    srows = []
    for m in ["R2 contracting cylinder", "F1 first order", "A2 Avrami n=2",
              "A3 Avrami n=3", "D3 sphere diffusion", "R3 contracting sphere"]:
        name = short[m].replace(", $\\phi=0$", "") + (" (true)" if m.startswith("R3") else "")
        srows.append(f"{name} & {_f(sy.loc[m, ('Ea_kJ', 'monotonic')], 1)} & "
                     f"{_f(sy.loc[m, ('rms_F', 'monotonic')], 4)} & "
                     f"{_f(sy.loc[m, ('Ea_kJ', 'cycled')], 1)} & "
                     f"{_f(sy.loc[m, ('rms_F', 'cycled')], 4)} \\\\")
    M["ChTwoKinSynthRows"] = "\n".join(srows)
    hdr = ("% =============================================================\n"
           "%  chapter2_kinetics_values.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.\n"
           "%  Written by Chapter2/Figures/fig_goethite_vacuum_kinetics.py\n"
           "%  (write_kinetics_macros) from the kinetic fits to the vacuum step heats\n"
           "%  (KAF = Farley et al. 2024; HDM = Monteiro et al. 2017). Statistics cache:\n"
           "%  Figures/generated/data/goethite_kinetics_cache.json.\n"
           "%  Rerun that script (or run_all_figures.py) after any change to the data\n"
           "%  or fitting code.\n"
           "% =============================================================\n")
    body = "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" if "Rows" not in k else
                   f"\\newcommand{{\\{k}}}{{%\n{v}}}\n" for k, v in M.items())
    MACRO_PATH.write_text(hdr + body, encoding="utf-8")
    CACHE_PATH.parent.mkdir(exist_ok=True)
    cache = dict(fits=tab.to_dict(orient="records"),
                 arrhenius_line={k: v for k, v in line.items() if k != "per"},
                 arrhenius_per_experiment={k: list(v) for k, v in line["per"].items()},
                 k250=k250, ceiling_kBT=ceiling, detect_kBT=detect,
                 trap_suppression=sup, residuals=resid,
                 synthetic=synth.to_dict(orient="records"),
                 rate_laws=rl_cache, macros=M)
    CACHE_PATH.write_text(json.dumps(cache, indent=1, default=float))
    return M


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
    synth = synthetic_degeneracy_test()
    M = write_kinetics_macros(tab, arr, sup, residual_stats(arr), synth)
    print(f"wrote {len(M)} macros to {MACRO_PATH}")
    with pd.option_context("display.width", 200):
        print(tab.round(4).to_string(index=False))
