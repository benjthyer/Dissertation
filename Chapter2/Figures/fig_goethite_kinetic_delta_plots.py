"""
Delta plots of the vacuum step heats of Win-06-01b (KAF = Farley et al. 2024;
HDM = Monteiro 2017) for every kinetic model in fig_goethite_vacuum_kinetics.

For a rate law d(alpha)/dt = A exp(-Ea/RT) h(alpha), the integral form
g(alpha) = int_0^alpha d(alpha')/h(alpha') grows by A exp(-Ea/RT) dt in every
step.  So each step gives a model-specific apparent rate constant

    k_i = [g(alpha_i) - g(alpha_(i-1))] / dt_i,   alpha = F / (1 - phi),

that should fall on a single Arrhenius line if the model is right, for any
heating schedule.  (For F1 this is Eq. eq:gt_stepk; for D3 it is the
Fechtig-Kalbitzer D/a^2.)  For each model we fit one joint Arrhenius line to
the KAF + HDM steps in the fitting window (LN2-off steps excluded) and plot

    Delta = ln k_i - ln k_line(T_i)

against cumulative release (left) and against temperature (right).  If the
model's h(alpha) is wrong, both experiments show the same Delta structure as a
function of F, even though their heating schedules differ.  A misfit in the
temperature dependence instead shows up as structure against T.

phi (the 3He fraction inherited by hematite) is taken from each model's own
cumulative fit to KAF (D3: phi free), so every model is judged with its best
plateau.  Outputs: generated/goethite_kinetic_delta_plots.{png,pdf} and
generated/data/goethite_kinetic_delta_plots.csv (per-step Delta) plus a
per-model summary printed to the console.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fig_goethite_vacuum_kinetics as vk  # noqa: E402
from plot_style import apply_style  # noqa: E402

R = vk.R
OUTDIR = vk.OUTDIR
AMAX = 0.999        # alpha above this has no usable increment
LN2_COL = "tab:pink"

# integral forms g(alpha) of the models tested in the SI (Table tab:gt_mech_forms)
G = {
    "R2 contracting cylinder": lambda a: 1 - (1 - a)**0.5,
    "R3 contracting sphere": lambda a: 1 - (1 - a)**(1 / 3),
    "F1 first order": lambda a: -np.log(1 - a),
    "A2 Avrami n=2": lambda a: (-np.log(1 - a))**0.5,
    "A3 Avrami n=3": lambda a: (-np.log(1 - a))**(1 / 3),
    # D3: Fechtig & Kalbitzer (1966) Dt/a^2 for a sphere
    "D3 sphere diffusion": lambda a: np.where(
        a <= 0.85,
        (2 * np.pi - np.pi**2 / 3 * a
         - 2 * np.pi * np.sqrt(np.clip(1 - np.pi * a / 3, 0, None))) / np.pi**2,
        -np.log(np.pi**2 / 6 * np.clip(1 - a, 1e-12, None)) / np.pi**2),
}
SHORT = {"R2 contracting cylinder": "R2", "R3 contracting sphere": "R3",
         "F1 first order": "F1", "A2 Avrami n=2": "A2", "A3 Avrami n=3": "A3",
         "D3 sphere diffusion": "D3"}


def model_phi(model, kaf):
    """phi from the model's own cumulative fit to KAF (D3 with phi free)."""
    p, _ = vk.fit_model(model, kaf, "F", phi_free=model.startswith("D3"))
    return float(p[3])


def step_lnk_model(df, model, phi):
    """ln of the model-specific apparent rate constant for every step."""
    a = np.clip(df["F"].values / (1 - phi), 0, None)
    a0 = np.r_[0, a[:-1]]
    ok = (a < AMAX)
    g = G[model]
    with np.errstate(invalid="ignore", divide="ignore"):
        dg = g(np.clip(a, 0, AMAX)) - g(np.clip(a0, 0, AMAX))
        k = dg / (df["Time (h)"].values * 3600)
        return np.where(ok & (k > 0), np.log(k), np.nan)


def model_line(model, phi, kaf, hdm):
    """Joint OLS Arrhenius line through the fitted steps of KAF + HDM."""
    X, Y, per = [], [], {}
    for df in (kaf, hdm):
        T = df["Temp (C)"].values + 273.15
        lk = step_lnk_model(df, model, phi)
        nl = df["noLN2"].values if "noLN2" in df else np.zeros(len(df), bool)
        u = vk.fit_window(df) & ~nl & np.isfinite(lk)
        X.append(1 / T[u]); Y.append(lk[u])
        per[df.attrs["name"]] = vk.arrhenius_fit(1 / T[u], lk[u])
    Ea, sEa, lnA, slnA = vk.arrhenius_fit(np.concatenate(X), np.concatenate(Y))
    return dict(Ea=Ea, sEa=sEa, lnA=lnA, slnA=slnA, per=per)


def deltas(model, kaf, hdm, phi=None):
    phi = model_phi(model, kaf) if phi is None else phi
    line = model_line(model, phi, kaf, hdm)
    rows = []
    for df in (kaf, hdm):
        T = df["Temp (C)"].values
        lk = step_lnk_model(df, model, phi)
        d = lk - (line["lnA"] - line["Ea"] * 1e3 / (R * (T + 273.15)))
        F0 = np.r_[0, df["F"].values[:-1]]
        nl = df["noLN2"].values if "noLN2" in df else np.zeros(len(df), bool)
        w = vk.fit_window(df)
        for i in range(len(df)):
            rows.append(dict(model=model, experiment=df.attrs["name"],
                             step=int(df["Step"].iloc[i]), T_C=T[i],
                             F_start=F0[i], F_end=df["F"].iloc[i],
                             delta=d[i], fitted=bool(w[i] and not nl[i]),
                             noLN2=bool(nl[i])))
    out = pd.DataFrame(rows)
    fw = out[out.fitted & np.isfinite(out.delta)]
    stats = dict(model=model, phi=phi, Ea=line["Ea"], sEa=line["sEa"],
                 Ea_KAF=line["per"]["KAF"][0], Ea_HDM=line["per"]["HDM"][0],
                 rms_all=float(np.sqrt(np.mean(fw.delta**2))),
                 rms_KAF=float(np.sqrt(np.mean(fw[fw.experiment == "KAF"].delta**2))),
                 rms_HDM=float(np.sqrt(np.mean(fw[fw.experiment == "HDM"].delta**2))))
    # shared structure: correlate KAF and HDM Delta, both interpolated onto a
    # common F grid inside the range covered by both fitting windows
    k_, h_ = (fw[fw.experiment == e].sort_values("F_end") for e in ("KAF", "HDM"))
    xk, xh = 0.5 * (k_.F_start + k_.F_end), 0.5 * (h_.F_start + h_.F_end)
    lo, hi = max(xk.min(), xh.min()), min(xk.max(), xh.max())
    if hi > lo:
        grid = np.linspace(lo, hi, 40)
        dk, dh = np.interp(grid, xk, k_.delta), np.interp(grid, xh, h_.delta)
        stats["r_KAF_HDM_vs_F"] = float(np.corrcoef(dk, dh)[0, 1])
    return out, stats


def make_figure(models=tuple(G), fname="goethite_kinetic_delta_plots"):
    kaf, hdm = vk.load_kaf(), vk.load_hm()
    sets = [("Vacuum: Farley et al., 2024 (KAF)", "KAF", "o", "red"),
            ("Vacuum: Monteiro, 2017 (HDM)", "HDM", "s", "orange")]
    all_rows, summary = [], []
    with mpl.rc_context():
        apply_style(scale=1.6)
        fig, axes = plt.subplots(len(models), 2, figsize=(12.8, 3.4 * len(models)),
                                 sharex="col", sharey="row")
        for r, model in enumerate(models):
            d, st = deltas(model, kaf, hdm)
            all_rows.append(d); summary.append(st)
            for lab, name, mk, col in sets:
                e = d[d.experiment == name]
                ok = np.isfinite(e.delta.values)
                xF = 0.5 * (e.F_start.values + e.F_end.values)
                for c, x in ((0, xF), (1, e.T_C.values)):
                    ax = axes[r, c]
                    ax.plot(x[ok], e.delta.values[ok], ls="--", lw=1, color=col,
                            alpha=0.5, zorder=1)
                    f_ = ok & e.fitted.values
                    o_ = ok & ~e.fitted.values
                    ax.plot(x[f_], e.delta.values[f_], mk, color=col, ms=7,
                            alpha=0.75, ls="", zorder=3)
                    ax.plot(x[o_], e.delta.values[o_], mk, mfc="none", mec=col,
                            ms=7, mew=1.5, alpha=0.9, ls="", zorder=3)
                    n_ = ok & e.noLN2.values
                    ax.plot(x[n_], e.delta.values[n_], "o", ms=16, mfc="none",
                            mec=LN2_COL, mew=2.2, ls="", zorder=4)
                    if c == 0:
                        # step extent in F, as in the chapter's delta plots
                        ax.hlines(e.delta.values[ok], e.F_start.values[ok],
                                  e.F_end.values[ok], color=col, lw=1.2,
                                  alpha=0.6, zorder=2)
            for c in (0, 1):
                ax = axes[r, c]
                ax.axhline(0, color="k", lw=1.2, zorder=0)
                ax.grid(True, color="0.85", lw=0.8, zorder=0)
                ax.set_axisbelow(True)
            rtxt = (f", $r$ = {st['r_KAF_HDM_vs_F']:.2f}"
                    if "r_KAF_HDM_vs_F" in st else "")
            axes[r, 0].text(0.02, 0.95,
                            f"{SHORT[model]}: $E_a$ = {st['Ea']:.0f} kJ/mol, "
                            f"$\\phi$ = {st['phi']:.3f}\nrms $\\Delta$ = "
                            f"{st['rms_all']:.2f}{rtxt}",
                            transform=axes[r, 0].transAxes, ha="left", va="top",
                            fontsize="small",
                            bbox=dict(fc="white", ec="none", alpha=0.8))
            axes[r, 0].set_ylabel(r"$\Delta\ln k$")
        axes[-1, 0].set_xlabel(r"cumulative $^3$He released, $F$")
        axes[-1, 1].set_xlabel("Temperature (°C)")
        axes[0, 0].set_xlim(0, 1)
        axes[0, 1].set_xlim(125, 350)   # conversion window; later steps have no defined k
        lim = np.nanpercentile(np.abs(pd.concat(all_rows).query("fitted").delta), 99)
        for r in range(len(models)):
            axes[r, 0].set_ylim(-max(2.0, 1.6 * lim), max(2.0, 1.6 * lim))
        handles = [Line2D([], [], marker=mk, color=col, ls="--", alpha=0.75,
                          label=lab) for lab, _, mk, col in sets]
        handles += [Line2D([], [], marker="o", mfc="none", mec="0.4", ls="",
                           label="outside fitting window"),
                    Line2D([], [], marker="o", ms=12, mfc="none", mec=LN2_COL,
                           mew=2, ls="", label="KAF, LN$_2$ trap isolated")]
        fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False)
        fig.tight_layout(rect=(0, 0.06, 1, 1), h_pad=0.6, w_pad=1.0)
        for ext in ("png", "pdf"):
            fig.savefig(OUTDIR / f"{fname}.{ext}", dpi=200)
    rows = pd.concat(all_rows, ignore_index=True)
    (OUTDIR / "data").mkdir(exist_ok=True)
    rows.to_csv(OUTDIR / "data" / f"{fname}.csv", index=False)
    summary = pd.DataFrame(summary)
    summary.to_csv(OUTDIR / "data" / f"{fname}_summary.csv", index=False)
    return fig, rows, summary


if __name__ == "__main__":
    _, _, summ = make_figure()
    with pd.option_context("display.width", 200, "display.precision", 3):
        print(summ.to_string(index=False))
