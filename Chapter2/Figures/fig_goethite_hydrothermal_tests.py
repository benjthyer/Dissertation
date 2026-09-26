"""
Could the hydrothermal (liquid-water) 3He release be conversion to hematite
(solid-state OR fluid-mediated dissolution-reprecipitation) rather than
diffusion?  Two discriminants, both independent of the thermodynamic model:

 (a) History dependence: FK D/a^2 through the T cycles (retrograde hysteresis
     = depletion of fast domains; a first-order conversion rate depends only
     on T and on the fraction converted, which is almost unchanged at F<5%).
 (b) The 250 C holds: 3 x 5 h then 171 h.  Each model is calibrated on the
     three 5 h steps and projected through the long step: diffusion slows as
     the front moves inward, first-order conversion does not (alpha << 1).

Everything uses the BOUNDING-METHOD reduction of the hydrothermal run
(data/Win0601bHT_distilled.csv; Table tab:ch2-distilled-3he): ln(D/a^2)
lower bound / central / upper bound from the table, cumulative release
bounded by [measured, measured + n_t,UB] (central = midpoint), and steps
without bounds (lambda t < 4) or with measured 3He < 0.1 pccSTP excluded from
plots, as in every other Chapter 2 figure.

Inputs: data/Win0601bHT_distilled.csv (+ vacuum data via
fig_goethite_vacuum_kinetics.py).  Outputs -> ./generated/
    hydrothermal_hold_projection.{pdf,png}   (Chapter 2 and GCA manuscript)
    data/hydrothermal_tests_summary.json
"""
from pathlib import Path
import importlib.util
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "vk", HERE / "fig_goethite_vacuum_kinetics.py")
vk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vk)
OUTDIR = vk.OUTDIR
MODELS = vk.MODELS
HT_FILE = HERE / "data/Win0601bHT_distilled.csv"


def load_ht():
    return vk.load_ht(HT_FILE)


def kaf_ratio():
    k = vk.load_kaf()
    raw = pd.read_csv(vk.KAF_FILE, skiprows=1, encoding="utf-8-sig")
    raw = raw[pd.to_numeric(raw["Step"], errors="coerce").notna()]
    he4 = pd.to_numeric(raw["4He NCC"]).values
    he3 = pd.to_numeric(raw["3He PCC"]).values
    bulk = he4.sum() / he3.sum()          # includes fusion row
    k["r43"] = (he4[:len(k)] / he3[:len(k)]) / bulk
    return k


def hm_ratio():
    raw = pd.read_csv(vk.HM_FILE, encoding="utf-8-sig")
    h = vk.load_hm()
    he4 = pd.to_numeric(raw["4HeCPS"], errors="coerce").values
    he3 = pd.to_numeric(raw["3HeCPS"], errors="coerce").values
    bulk = np.nansum(he4) / np.nansum(he3)
    h["r43"] = (he4[:len(h)] / he3[:len(h)]) / bulk
    return h


def _fk_Fo(F):
    """Fechtig & Kalbitzer (1966) sphere: cumulative Dt/a^2 from F."""
    F = np.asarray(F, float)
    return np.where(F <= 0.85,
                    (2 * np.pi - np.pi**2 / 3 * F
                     - 2 * np.pi * np.sqrt(np.clip(1 - np.pi * F / 3, 0, None)))
                    / np.pi**2,
                    -np.log(np.pi**2 / 6 * (1 - F)) / np.pi**2)


def _segments(T):
    dT = np.r_[1, np.diff(T)]
    sgn = np.sign(dT)
    for i in range(1, len(sgn)):           # isothermal repeats keep direction
        if sgn[i] == 0:
            sgn[i] = sgn[i - 1]
    return np.cumsum(np.r_[0, sgn[1:] != sgn[:-1]]), sgn >= 0


def history_test(ht):
    """Test 1.  (i) Offsets of the first-cycle retrograde steps, and of later
    steps at the same temperatures, from a line through the first prograde
    sweep (fitted separately to the LB, central and UB values).
    'conservative' = UB of the step minus the LB line, i.e. the smallest drop
    allowed by the bounds.  (ii) Retrograde vs prograde agreement in the last
    temperature cycle (steps at the same T)."""
    T = ht["Temp (C)"].values
    ok = ht["use"].values
    seg, up = _segments(T)
    x = 1e4 / (T + 273.15)
    first = ok & (seg == seg[ok][0]) & up
    lines = {k: np.polyfit(x[first], ht[f"lnDa2_{k}"].values[first], 1)
             for k in ("LB", "m", "UB")}
    i_last_first = np.where(first)[0].max()
    Tfirst = (T[first].min(), T[first].max())
    rows = []
    for i in np.where(ok)[0]:
        if i <= i_last_first or not (Tfirst[0] <= T[i] <= Tfirst[1]):
            continue
        if seg[i] > seg[i_last_first] + 2:       # first two cycles only
            continue
        rows.append(dict(step=int(i + 1), T=float(T[i]),
                         retrograde=bool(not up[i]),
                         offset_central=float(ht["lnDa2_m"].values[i]
                                              - np.polyval(lines["m"], x[i])),
                         offset_conservative=float(
                             ht["lnDa2_UB"].values[i] - np.polyval(lines["LB"], x[i]))))
    segs_ok = sorted(set(seg[ok]))
    retro = [s_ for s_ in segs_ok if not up[np.where(seg == s_)[0][0]]
             and (s_ + 1) in segs_ok]
    r_seg = retro[-1]
    p_seg = r_seg + 1
    pairs = []
    for i in np.where(ok & (seg == r_seg))[0]:
        j = np.where(ok & (seg == p_seg) & (T == T[i]))[0]
        if len(j):
            j = j[0]
            m_i, m_j = ht["lnDa2_m"].values[[i, j]]
            overlap = (ht["lnDa2_LB"].values[i] <= ht["lnDa2_UB"].values[j] and
                       ht["lnDa2_LB"].values[j] <= ht["lnDa2_UB"].values[i])
            pairs.append(dict(T=float(T[i]), retro_step=int(i + 1),
                              pro_step=int(j + 1),
                              diff_central=float(m_i - m_j),
                              bounds_overlap=bool(overlap)))
    return dict(first_sweep_T=Tfirst, first_cycle=rows, last_cycle=pairs)


# g(alpha) for each model: x = g(alpha) grows linearly in time at fixed T
G_INV = {
    "F1 first order": lambda a: -np.log(1 - a),
    "R2 contracting cylinder": lambda a: 1 - np.sqrt(1 - a),
    "R3 contracting sphere": lambda a: 1 - (1 - a)**(1 / 3),
    "A2 Avrami n=2": lambda a: np.sqrt(-np.log(1 - a)),
    "A3 Avrami n=3": lambda a: (-np.log(1 - a))**(1 / 3),
}


def hold_projection(ht=None, T_hold=250.0, n_short=3, phi=None, npts=400,
                    col="F"):
    """Calibrate each model on the n_short short steps at T_hold that precede
    the long step (x = g(alpha) linear in t through the start point), then
    project F through the long step.  D3 uses the Fechtig-Kalbitzer Fourier
    number as x (alpha = F).  col selects the bounding-method series: "F"
    (central), "F_LB" or "F_UB".  Returns dict of results and curves."""
    ht = load_ht() if ht is None else ht
    phi = vk.vacuum_line()["phi"] if phi is None else phi
    T, t, F = ht["Temp (C)"].values, ht["Time (h)"].values, ht[col].values
    idx = np.where(T == T_hold)[0]
    i_long = idx[np.argmax(t[idx])]
    short = list(range(i_long - n_short, i_long))
    assert all(T[i] == T_hold for i in short)
    i0 = short[0] - 1                                   # step before holds
    tt = np.r_[0, np.cumsum(t[short[0]:i_long + 1])]   # h since hold start
    Fobs = np.r_[F[i0], F[short[0]:i_long + 1]]
    t_cal, F_cal = tt[:n_short + 1], Fobs[:n_short + 1]
    tc = np.linspace(0, tt[-1], npts)
    out = {"t_obs": tt, "F_obs": Fobs, "t_curve": tc, "models": {},
           "F0": float(Fobs[0]), "F_long_start": float(Fobs[-2]),
           "F_end_obs": float(Fobs[-1])}

    def fit_line(x):
        # x(t) = x0 + r t, least squares with x0 fixed at the start point
        r = np.sum((x - x[0]) * t_cal) / np.sum(t_cal**2)
        return x[0], r

    Fo = _fk_Fo(F_cal)                                  # cumulative Dt/a2
    x0, r = fit_line(Fo)
    Fc = vk.gh.sphere_F(x0 + r * tc)
    out["models"]["D3 sphere diffusion"] = dict(curve=Fc, F_end=float(Fc[-1]),
                                               rate=r / 3600)
    for m, g in G_INV.items():
        a_cal = F_cal / (1 - phi)
        x0, r = fit_line(g(a_cal))
        Fc = (1 - phi) * MODELS[m](x0 + r * tc)
        out["models"][m] = dict(curve=Fc, F_end=float(Fc[-1]), rate=r / 3600)
    for m, d in out["models"].items():
        d["overprediction"] = float((d["F_end"] - out["F_long_start"]) /
                                    (out["F_end_obs"] - out["F_long_start"]))
    return out


def make_hold_figure(fname="hydrothermal_hold_projection"):
    """Chapter 2: single panel, the 250 C holds with first-order and diffusion
    projections calibrated on the three 5 h steps (bounding-method central
    values; shaded bands from the lower- and upper-bound series)."""
    ht = load_ht()
    r = {c: hold_projection(ht, col=c) for c in ("F", "F_LB", "F_UB")}
    c = r["F"]
    fig, ax = plt.subplots(figsize=(6.5, 4.8), constrained_layout=True)
    ax.errorbar(c["t_obs"], c["F_obs"],
                yerr=[c["F_obs"] - r["F_LB"]["F_obs"], r["F_UB"]["F_obs"] - c["F_obs"]],
                fmt="ko", ms=6, capsize=2, label="observed (bounding method)",
                zorder=3)
    for m, col, lab in [("F1 first order", "tab:red", "first-order conversion"),
                        ("D3 sphere diffusion", "tab:blue", "volume diffusion (sphere)")]:
        lo = r["F_LB"]["models"][m]["curve"]
        hi = r["F_UB"]["models"][m]["curve"]
        ax.fill_between(c["t_curve"], np.minimum(lo, hi), np.maximum(lo, hi),
                        color=col, alpha=0.15, lw=0)
        mm = c["models"][m]
        ax.plot(c["t_curve"], mm["curve"], color=col, lw=2,
                label=f"{lab}: F = {mm['F_end']:.3f}")
    ax.axvspan(0, c["t_obs"][3], color="0.92", zorder=0)
    ax.text(c["t_obs"][3] / 2, c["F_obs"][-1], "calibration\n(3 × 5 h)",
            ha="center", va="top", fontsize=8, color="0.4")
    ax.set_xlabel("time at 250 °C (h)")
    ax.set_ylabel(r"cumulative $^3$He fraction $F$")
    ax.legend(fontsize=8, loc="lower right")
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig, r


if __name__ == "__main__":
    ht = load_ht()
    _, proj = make_hold_figure()
    summ = dict(history=history_test(ht),
                hold_projection={c: {m: {k: v for k, v in d.items() if k != "curve"}
                                     for m, d in p["models"].items()}
                                 | {"F0": p["F0"], "F_long_start": p["F_long_start"],
                                    "F_end_obs": p["F_end_obs"]}
                                 for c, p in proj.items()})
    (OUTDIR / "data").mkdir(exist_ok=True)
    with open(OUTDIR / "data" / "hydrothermal_tests_summary.json", "w") as f:
        json.dump(summ, f, indent=1, default=float)
    print(json.dumps(summ["hold_projection"], indent=1, default=float))
