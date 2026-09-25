"""
Could the hydrothermal (liquid-water) 3He release be conversion to hematite
(solid-state OR fluid-mediated dissolution-reprecipitation) rather than
diffusion?  Two discriminants, all independent of the thermodynamic model:

 (a) Arrhenius: FK D/a^2 through the T cycles (retrograde hysteresis =
     depletion of fast domains; a surface/interface-controlled reaction at
     F < 5% has almost no memory of its history).
 (b) The 250 C holds: 3 x 5 h then 171 h.  Diffusion predicts the release rate
     falls roughly as t^-1/2; interface-controlled conversion at alpha ~0.1
     predicts a nearly constant rate.

Inputs (same folder): Win0601bHT_distilled.csv, Winsor_waterKAF_BJT.csv,
HM_Win_06_01B.csv.  Outputs -> ./generated/
"""
from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "vk", HERE / "goethite_vacuum_kinetics.py")
vk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vk)
OUTDIR = vk.OUTDIR
HT_FILE = HERE / "data/Win0601bHT_distilled.csv"


def _load_ht_unused(path=HT_FILE):
    raw = pd.read_csv(path, encoding="utf-8-sig")
    raw.columns = [c.strip() for c in raw.columns]
    tcol = raw.columns[0]
    tot = raw[raw[tcol].astype(str).str.strip() == "Total"]
    tot3 = float(tot["Σ 3He (pccSTP)"].iloc[0])
    tot4 = float(tot["Σ 4He (nccSTP)"].iloc[0])
    d = raw[pd.to_numeric(raw[tcol], errors="coerce").notna()].copy()
    out = pd.DataFrame({
        "Temp (C)": pd.to_numeric(d[tcol]).values,
        "Time (h)": pd.to_numeric(d["Minutes"]).values / 60,
    })
    s3 = pd.to_numeric(d["Σ 3He (pccSTP)"]).values
    s4 = pd.to_numeric(d["Σ 4He (nccSTP)"]).values
    out["F"] = s3 / tot3
    d3, d4 = np.diff(np.r_[0, s3]), np.diff(np.r_[0, s4])
    out["r43"] = (d4 / d3) / (tot4 / tot3)
    out["t_cum"] = out["Time (h)"].cumsum()
    return out


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


def hold_test(ht, T_hold=250.0):
    """Calibrate on the short steps at T_hold immediately before the long one;
    predict F at the end of the long step for diffusion and for a constant-
    rate interface reaction (R3, alpha << 1)."""
    idx = np.where(ht["Temp (C)"].values == T_hold)[0]
    long_i = idx[np.argmax(ht["Time (h)"].values[idx])]
    short = [i for i in idx if i < long_i and i >= long_i - 3]
    F, t = ht["F"].values, ht["Time (h)"].values
    # diffusion: mean FK D/a^2 over the short steps
    Da = np.nanmean(vk.fk_Da2(F, t)[short])
    Fo0 = vk.fk_Da2(np.r_[F[long_i - 1]], [1 / 3600])[0]   # Dt/a^2 at start
    Fo_end = Fo0 + Da * t[long_i] * 3600
    F_diff = vk.gh.sphere_F(np.r_[Fo_end])[0]
    # constant-rate reaction: dF/dt from the last short step, x (1-a)^(2/3)
    rate = (F[short[-1]] - F[short[-1] - 1]) / t[short[-1]]
    F_rxn = F[long_i - 1] + rate * t[long_i] * (1 - F[long_i - 1])**(2 / 3)
    return dict(F_start=F[long_i - 1], F_obs=F[long_i], F_diffusion=F_diff,
                F_constant_rate=F_rxn, hours=t[long_i], i=long_i, short=short)


def make_figure(fname="hydrothermal_diffusion_vs_conversion"):
    ht = load_ht()
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.9), constrained_layout=True)

    # (a) Arrhenius with cycle colouring
    a = ax[0]
    x = 1e4 / (ht["Temp (C)"] + 273.15)
    y = np.log(vk.fk_Da2(ht["F"], ht["Time (h)"]))
    dT = np.r_[1, np.diff(ht["Temp (C)"].values)]
    seg = np.cumsum(np.r_[0, (np.sign(dT[1:]) != np.sign(dT[:-1])) &
                          (dT[1:] != 0)])
    cmap = plt.cm.viridis(np.linspace(0, 0.9, seg.max() + 1))
    for sgi in range(seg.max() + 1):
        m = seg == sgi
        up = dT[m].mean() >= 0
        a.plot(x[m], y[m], "o-" if up else "s--", color=cmap[sgi], ms=5,
               mfc=cmap[sgi] if up else "white",
               label=f"{'prograde' if up else 'retrograde'} {sgi + 1}")
    a.set_xlabel(r"10$^4$/T (K$^{-1}$)")
    a.set_ylabel(r"ln $D/a^2$ (s$^{-1}$)")
    a.set_title("(a) hydrothermal: FK $D/a^2$ through T cycles")
    a.legend(fontsize=7)

    # (b) 250 C hold test
    c = ax[1]
    r = hold_test(ht)
    i0 = r["short"][0] - 1
    tt = ht["t_cum"].values - ht["t_cum"].values[i0]
    c.plot(tt[i0:r["i"] + 1], ht["F"].values[i0:r["i"] + 1], "ko", ms=5,
           label="observed")
    t_end = tt[r["i"]]
    t_start = tt[r["i"] - 1]
    for key, col, lab in [("F_diffusion", "tab:blue", "diffusion (FK, D/a² from 5 h steps)"),
                          ("F_constant_rate", "tab:red", "interface reaction (constant rate)")]:
        c.plot([t_start, t_end], [r["F_start"], r[key]], color=col, lw=1.8,
               label=f"{lab}: F = {r[key]:.3f}")
    c.set_xlabel("time since first 250 °C step (h)")
    c.set_ylabel(r"$F$")
    c.set_title(f"(b) 250 °C hold: observed F = {r['F_obs']:.3f}")
    c.legend(fontsize=8)
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    return fig, r


if __name__ == "__main__":
    fig, r = make_figure()
    print({k: (round(v, 4) if isinstance(v, float) else v)
           for k, v in r.items()})
