"""
Fe-S phase diagram in log f(S2) - T space, after Toulmin & Barton (1964).

Curves
------
1. Liquid-sulfur saturation, computed from first principles:
       2 S(l) = S2(g)      a[S(l)] = 1
       log10 f(S2) = [2 G°_S(l)(T) - G°_S2(g)(T)] / (RT ln 10)
   G° from NASA Glenn 7-coefficient polynomials (McBride, Zehe & Gordon 2002,
   NASA/TP-2002-211556; S(l) = TPIS89 / Gurvich et al. 1989, S2(g) = JANAF 9/77).
   Standard state: ideal S2 gas at 1 bar (T&B used 1 atm; difference 0.006 log units).
   The plot is cut at 1000 °C, below the critical point of sulfur (~1041 °C,
   Rau et al. 1973).

2. Pyrite-pyrrhotite univariant curve, digitized from Toulmin & Barton (1964).

3. (optional) Pyrrhotite composition isopleths from Toulmin & Barton (1964), eq. 8:
       log f(S2) = (70.03 - 85.83 N)(1000/T - 1) + 39.30 sqrt(1 - 0.9981 N) - 11.91
   N = mole fraction FeS in the FeS-S2 system, T in K.

Usage
-----
    python fe_s_fS2_T_diagram.py                      # CSV next to this script
    python fe_s_fS2_T_diagram.py path/to/pypo.csv     # explicit CSV
Writes Fe-S_fS2_T.pdf / .png and S_liquid_saturation_fS2.csv next to this script.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
CSV =  HERE / "data/ToulminBartonPy-Po-Univariant.csv"
SHOW_ISOPLETHS = True
T_CRIT_S_C = 1041.0      # critical temperature of sulfur, °C (≈1314 K)
T_MELT_S_C = 115.21      # lower limit of the NASA S(l) polynomial (388.36 K)

# --------------------------------------------------------------------------
# NASA-7 thermodynamics: [a1..a7] for T < Tmid and T >= Tmid (Tmid = 1000 K)
# --------------------------------------------------------------------------
NASA7 = {
    "S(l)": [[-72.7405684, 0.481222534, -1.07842233e-03, 1.03257728e-06,
              -3.5888449e-10, 8291.34856, 315.269743],
             [3.5007841, 3.816621e-04, -1.55569962e-07, 2.72783689e-11,
              -1.72812554e-15, -590.873035, -15.216727]],
    "S2(g)": [[2.8585754, 5.1758355e-03, -6.5493434e-06, 3.3998643e-09,
               -4.0156766e-13, 1.4412402e+04, 9.89127849],
              [3.9886069, 5.5775051e-04, -5.0189278e-08, -1.5470319e-11,
               2.6661771e-15, 1.4198015e+04, 4.49119159]],
}


def g_over_RT(species, T, Tmid=1000.0):
    """Dimensionless standard Gibbs energy G°/RT (H°/RT - S°/R)."""
    T = np.atleast_1d(np.asarray(T, float))
    lo, hi = (np.array(c) for c in NASA7[species])
    a = np.where((T < Tmid)[:, None], lo, hi)
    h = (a[:, 0] + a[:, 1] * T / 2 + a[:, 2] * T**2 / 3 + a[:, 3] * T**3 / 4
         + a[:, 4] * T**4 / 5 + a[:, 5] / T)
    s = (a[:, 0] * np.log(T) + a[:, 1] * T + a[:, 2] * T**2 / 2
         + a[:, 3] * T**3 / 3 + a[:, 4] * T**4 / 4 + a[:, 6])
    return h - s


def log_fS2_Sliq(T_C):
    """log10 f(S2) in equilibrium with pure liquid sulfur."""
    T = np.asarray(T_C, float) + 273.15
    return (2 * g_over_RT("S(l)", T) - g_over_RT("S2(g)", T)) / np.log(10)


def log_fS2_po(N, T_C):
    """Toulmin & Barton (1964) pyrrhotite equation."""
    T = np.asarray(T_C, float) + 273.15
    return (70.03 - 85.83 * N) * (1000 / T - 1) + 39.30 * np.sqrt(1 - 0.9981 * N) - 11.91


# --------------------------------------------------------------------------
# Digitized py-po univariant curve
# --------------------------------------------------------------------------
df = pd.read_csv(CSV, encoding="utf-8-sig")
df.columns = ["T_C", "N_FeS", "logfS2"]
# Sanity check each digitized point against the T&B pyrrhotite equation
resid = df["logfS2"] - log_fS2_po(df["N_FeS"], df["T_C"])
bad = resid.abs() > 0.5
if bad.any():
    print("WARNING: dropping digitized points inconsistent with T&B eq. (>0.5 log units):")
    print(df[bad].assign(eq_value=log_fS2_po(df["N_FeS"], df["T_C"])[bad]).to_string())
df = df[~bad].sort_values("T_C").reset_index(drop=True)


# Smooth the digitized curve with a quadratic in 1000/T (max misfit ~0.07 log units)
PYPO_FIT = np.polyfit(1000 / (df["T_C"] + 273.15), df["logfS2"], 2)


def pypo(T_C):
    """Smoothed py-po univariant curve, log10 f(S2) at T_C (°C)."""
    return np.polyval(PYPO_FIT, 1000 / (np.asarray(T_C, float) + 273.15))


# Invariant point py + po + S(l) + V
T_inv = brentq(lambda t: log_fS2_Sliq(t)[0] - pypo(t), 650, 800)
f_inv = float(log_fS2_Sliq(T_inv)[0])
print(f"py-po-S(l)-V invariant: {T_inv:.1f} °C, log f(S2) = {f_inv:.2f} "
      f"(T&B: 743 °C)")

# --------------------------------------------------------------------------
# Plot
# --------------------------------------------------------------------------
T_MAX_C = 1000.0         # right-hand limit of the plot, °C
T_S = np.linspace(T_MELT_S_C, T_MAX_C, 600)
fS = log_fS2_Sliq(T_S)
pd.DataFrame({"T_C": T_S, "log10_fS2_bar": fS}).to_csv(
    HERE / "generated/S_liquid_saturation_fS2.csv", index=False, float_format="%.4f")

fig, ax = plt.subplots(figsize=(6.5, 5.2))
xlim, ylim = (300, T_MAX_C), (-14, 3.5)
ax.set(xlim=xlim, ylim=ylim)

# Region above S(l) saturation is inaccessible
ax.fill_between(T_S, fS, ylim[1], color="0.88", lw=0, zorder=0)
ax.plot(T_S, fS, "k-", lw=1.8, zorder=3)

# Experimental conditions: thick red band beneath the S(l) curve, 300-600 °C
T_exp = np.linspace(300, 600, 200)
f_exp = log_fS2_Sliq(T_exp)
ax.plot(T_exp, f_exp, "-", color="red", lw=7, alpha=0.8,
        solid_capstyle="butt", zorder=2)
# Rotate the label to follow the curve (angle in display coordinates)
T_lab = 450.0
p0, p1 = ax.transData.transform([(T_lab - 20, log_fS2_Sliq(T_lab - 20)[0]),
                                 (T_lab + 20, log_fS2_Sliq(T_lab + 20)[0])])
angle = np.degrees(np.arctan2(p1[1] - p0[1], p1[0] - p0[0]))
ax.annotate("Experimental Conditions", (T_lab, log_fS2_Sliq(T_lab)[0]),
            xytext=(0, -9), textcoords="offset points", ha="center", va="top",
            rotation=angle, rotation_mode="anchor", fontsize=8.5, color="red")

# py-po univariant curve (smoothed), from the coldest digitized point to the invariant
T_pp = np.linspace(df["T_C"].iloc[0], T_inv, 400)
ax.plot(T_pp, pypo(T_pp), "k-", lw=1.8)
ax.plot(T_inv, f_inv, "s", mfc="w", mec="k", ms=7, zorder=5)
ax.annotate(f"{T_inv:.0f} °C", (T_inv, f_inv), xytext=(8, -12),
            textcoords="offset points", fontsize=8)

if SHOW_ISOPLETHS:
    Tg = np.linspace(xlim[0], xlim[1], 800)
    upper = np.where(Tg < df["T_C"].iloc[0], np.nan,
                     np.where(Tg <= T_inv, pypo(Tg), log_fS2_Sliq(Tg)))
    N_iso = [0.92, 0.94, 0.96, 0.98, 1.00]
    for N in N_iso:
        y = log_fS2_po(N, Tg)
        y = np.where(y <= upper, y, np.nan)
        ax.plot(Tg, y, "--", color="0.45", lw=0.7)
    # Label the isopleths on the right-hand axis where they meet the plot edge
    ax2 = ax.twinx()
    ax2.set_ylim(ylim)
    y_edge = [log_fS2_po(N, xlim[1]) for N in N_iso]
    keep = [ylim[0] < y < ylim[1] for y in y_edge]
    ax2.set_yticks([y for y, k in zip(y_edge, keep) if k])
    ax2.set_yticklabels([f"{N:.2f}" for N, k in zip(N_iso, keep) if k], fontsize=8)
    ax2.tick_params(direction="in")
    ax2.set_ylabel(r"Pyrrhotite $N_{FeS}$ Isopleths")

ax.text(430, -3.5, "pyrite", fontsize=10, style="italic")
ax.text(600, -9.5, "pyrrhotite", fontsize=10, style="italic")
ax.text(470, 1.5, "S(l) + vapor", fontsize=9, color="0.3")

ax.set(xlabel="Temperature (°C)", ylabel=r"$\log_{10} f_{\mathrm{S_2}}$ (bar)",
       title="Pyrite Stability and Sulfur Fugacity")
ax.tick_params(direction="in", top=True, right=not SHOW_ISOPLETHS)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(HERE / f"generated/Fe-S_fS2_T.{ext}", dpi=300)
print("Saved figure to", HERE)
