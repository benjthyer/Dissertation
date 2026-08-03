"""
Forward finite-difference cylindrical permeation simulations of the Win-06-01b
goethite tube geometry, across a 5x3 grid of hold temperatures (90/95/100/105/110 C)
and hold durations (120/150/180 min). Each grid cell fits a (lambda, n0)
permeation model to the simulated 3-step-heat sequence (KenColdInversion1),
the same model used to fit the actual naive-bracketed isothermal sequences in
fig_naive_isothermal_fits.py, so the two lambda populations are directly
comparable.

Outputs:
  goethite_diff_sims/*.csv          - per-combination sim step records
  data/goethite_thermal_sim_lambdas.csv
      - T_C, T_K, hold_min, lam for all 12 grid cells; read by
        fig_naive_isothermal_fits.py to overlay these simulated fits on
        NaiveLambda_Arrhenius.pdf alongside the actual experimental fits
  GoethiteThermalSimFits_Grid.pdf   - per-combination fit-quality diagnostic
                                       (cumulative He vs. cumulative *held*
                                       time, with the fitted lambda/n0 curve),
                                       one panel per T/hold-duration cell
  goethite_n0_grid_errors.pdf       - naive vs. informed n0 error heatmaps

This script is comparatively expensive (finite-difference PDE solve x 12
grid cells) and is deliberately NOT part of run_all_figures.py -- rerun it
manually if the tube geometry (a, b) or simulation code changes.
"""
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from diffusion_utils import (goethite_cooling, swets, permeation_sim, Jones, KenColdInversion1,
                              forward_permeate, accumulate)
from thermochr_utils import Ratoms
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(os.path.join(OUTDIR, 'goethite_diff_sims'), exist_ok=True)

Ts = np.array([90, 95, 100, 105, 110])+273 # C-> K
times = np.array([120,150,180])*60 # minutes -> seconds


# a, b are the (mean) tube ID/OD *diameters* (cm) -- same measurements as
# fig_naive_isothermal_fits.py's ID_cm/OD_cm (mean of two independent
# measurements: ID ~ [0.0505, 0.054], OD ~ [0.0787, 0.0832]). permeation_sim
# takes a/b as the inner/outer *radius* (see its docstring in
# diffusion_utils.py, and the original prototyping notebook's convention,
# e.g. `a = 0.054/2`), so both are halved here before use -- an earlier
# version of this script passed the raw diameters straight through as
# radii, silently doubling the modeled wall thickness (b-a) and therefore
# the diffusive path length, which suppressed the fitted lambda/K by
# roughly (2x)^2 = 4x (consistent with the simulated K values plotting
# noticeably below the actual experimental fits on NaiveLambda_Arrhenius.pdf).
a = 0.05225 / 2
b = 0.08095 / 2
G = 2 / (np.log(b / a) * a ** 2)

Tall = []
tall = []
naive_errors = []
informed_errors = []
lambda_errors = []
sim_lambdas = []  # T_C, T_K, hold_min, lam -- cached below so fig_naive_isothermal_fits.py
                  # can overlay these simulated permeability fits on the Arrhenius plot
sim_records = []  # per-combination raw (t, He) step records, for the fit-quality
                  # diagnostic grid plotted below (GoethiteThermalSimFits_Grid.pdf)

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
        (lam ,n0), covmat = KenColdInversion1(np.array(tRecords), np.array(HeRecords), sigma=np.array(HeRecords)*0.1, covout=True, plot=True)
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


# ---------------------------------------------------------------------------
# Cache the simulated (T, hold_min) -> lambda fits so fig_naive_isothermal_fits.py
# can overlay them on NaiveLambda_Arrhenius.pdf alongside the actual experimental
# fits, without needing to re-run this (much more expensive) simulation script.
# ---------------------------------------------------------------------------
sim_df = pd.DataFrame(sim_lambdas)
sim_df.to_csv(os.path.join(FIG_DIR, 'data', 'goethite_thermal_sim_lambdas.csv'), index=False)

# ---------------------------------------------------------------------------
# Diagnostic grid: per-combination lambda/n0 fit quality, one panel per T/hold
# -duration cell (5x3), mirroring fig_naive_isothermal_fits.py's Figure 1 grid
# for the actual experimental sequences. Each panel's x-axis is cumulative
# *held* time only -- cooling periods contribute no time to the fit's x-axis,
# even though the He that diffuses out during cooling is folded into the
# yield of the held step that precedes it (tRecords/HeRecords above already
# do this: tRecords logs only each rep's hold duration `t`, while HeRecords
# captures self.out after both hold_T *and* the following cool()). The
# overlay curve uses the same (lam, n0) the fit returned, evaluated with the
# ordinary continuous model (forward_permeate) at that same held-time-only
# cumulative axis -- consistent with the segment-difference model
# (forward_permeate1) KenColdInversion1 actually fit against.
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(len(Ts), len(times), figsize=(11, 16))
for rec, ax in zip(sim_records, axes.flat):
    cumt = accumulate(rec['t'])
    cumHe = accumulate(rec['He'])
    longt = np.linspace(0, cumt[-1], 500)
    ax.plot(longt, forward_permeate(longt, rec['lam'], rec['n0']), color='red', linestyle='--', label='Fit')
    ax.scatter(cumt, cumHe, color='black', zorder=5)
    ax.set_title(f"{rec['T_C']:.0f}°C, {rec['hold_min']:.0f} min\n"
                 f"λ={rec['lam']:.3e} s⁻¹, n0={rec['n0']:.4f}", fontsize=9)
    ax.set_xlabel('Cumulative Held Time (s)')
    ax.set_ylabel('Cumulative Simulated ³He ($n_0$ units)')
fig.suptitle('Goethite Thermal-Perturbation Sim: Per-Combination λ/n0 Fits\n'
             '(x-axis: held time only; cooling-period He counted with preceding step)')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'GoethiteThermalSimFits_Grid.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Grid-error heatmaps: naive n0 error, informed n0 error, and permeability
# (Swets K vs. fitted K) error, each across the 5x3 temperature x hold-time
# grid (apply_style() already called at import time, above, so it also
# covers the diagnostic grid plotted just before this)
# ---------------------------------------------------------------------------

n_T, n_t = len(Ts), len(times)
naive_grid = np.array(naive_errors).reshape(n_T, n_t)
informed_grid = np.array(informed_errors).reshape(n_T, n_t)
lambda_grid = np.array(lambda_errors).reshape(n_T, n_t)

T_labels = [f'{int(T - 273)}°C' for T in Ts]
t_labels = [f'{int(t / 60)} min' for t in times]

panels = [
    (naive_grid, 'Naive $n_0$ Error (%)'),
    (informed_grid, 'Informed $n_0$ Error (%)'),
    (lambda_grid, 'Permeability Error (%)\n(Swets $K$ vs. Fitted $K$)'),
]

cmap = mpl.colors.LinearSegmentedColormap.from_list(
    'diverging_blue_red', ['#2a78d6', '#f0efec', '#e34948'])

# The permeability error is a different quantity, ~5-10x larger in magnitude
# than the n0 errors (naive/informed overestimate n0 by a few-to-teens of
# percent; the naive method overestimates permeability by ~60-70%), so each
# panel is normalized to its own max |error| rather than sharing one
# colorbar -- otherwise the two n0 panels would wash out to near-white next
# to the much larger-magnitude K panel.
fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), constrained_layout=True)
for ax, (grid, title) in zip(axes, panels):
    vmax = np.max(np.abs(grid))
    norm = mpl.colors.Normalize(vmin=-vmax, vmax=vmax)
    im = ax.imshow(grid, cmap=cmap, norm=norm, aspect='auto')
    ax.set_xticks(range(n_t))
    ax.set_xticklabels(t_labels)
    ax.set_yticks(range(n_T))
    ax.set_yticklabels(T_labels)
    ax.set_title(title)
    for i in range(n_T):
        for j in range(n_t):
            val = grid[i, j]
            txt_color = 'white' if abs(val) / vmax > 0.55 else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                    color=txt_color, fontsize=10)
    ax.set_xticks(np.arange(-0.5, n_t, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_T, 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=1.5)
    ax.tick_params(which='minor', bottom=False, left=False)
    fig.colorbar(im, ax=ax, orientation='horizontal', fraction=0.05, pad=0.1,
                 label='Relative Error (%)')

axes[0].set_ylabel('Hold Temperature')
fig.supxlabel('Hold Duration')
fig.suptitle(f'Goethite Thermal-Perturbation Simulation Errors\n'
             f'Across {n_T}×{n_t} Temperature-Time Grid')
fig.savefig(os.path.join(OUTDIR, 'goethite_n0_grid_errors.pdf'), dpi=300)
plt.close(fig)

