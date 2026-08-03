import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from diffusion_utils import goethite_cooling, swets, permeation_sim, Jones, KenColdInversion1
from thermochr_utils import Ratoms
from plot_style import apply_style

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(os.path.join(OUTDIR, 'goethite_diff_sims'), exist_ok=True)

Ts = np.array([85, 95,105,115])+273 # C-> K
times = np.array([120,150,180])*60 # minutes -> seconds

a = 0.05225
b = 0.08095
G = 2/(np.log(b/a)*((a/2)**2))

Tall = []
tall = []
naive_errors = []
informed_errors = []
lambda_errors = []

for T in Ts:
    for t in times:
        Tall.append(T)
        tall.append(t)
        tRecords = []
        print(f"Simming 3 sequential {int(T-273.15)}C steps {int(t/60)}min")
        goethite_tube = permeation_sim(a=a,b=b,n0=1,cooling_func=goethite_cooling,He=4,EQMshortcut=False, T = 300+273.15)
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
        naive_errors.append(100*(n0_ans-n0)/n0_ans)
        F = 1-np.exp(-lam*t)
        final_n0 = HeRec+goethite_tube.nt
        informed_errors.append(100*((HeRec/F)-(final_n0))/final_n0)
        swetK = swets('K', T=T)*Jones('K', T=T)
        calcK = lam/(G*Ratoms*T)
        lambda_errors.append(100*(swetK-calcK)/swetK)
        print(f"Fitted parameters for {int(T-273.15)}C {int(t/60)}min: lambda = {lam:.3e}, n0 = {n0:.3e}")
        print(f"Covariance matrix: {covmat}")
        
        goethite_tube.generate_report(os.path.join(OUTDIR, 'goethite_diff_sims', f'{int(T-273.15)}C_{int(t/60)}min_cooling_NoSS_lam{lam:.3e}_n0{n0:.3e}'))


        goethite_tube = permeation_sim(a=a,b=b,n0=1,cooling_func=goethite_cooling,He=3,EQMshortcut=False, T = 300+273.15)
        goethite_tube.cool(15*60)
        goethite_tube.pump()
        for r in range(3):
            goethite_tube.hold_T(T=T, t=t)
            goethite_tube.pump()
        goethite_tube.generate_report(os.path.join(OUTDIR, 'goethite_diff_sims', f'{int(T-273.15)}C_{int(t/60)}min_hot_only_NoSS4'))


# ---------------------------------------------------------------------------
# Grid-error heatmaps: naive n0 error, informed n0 error, and permeability
# (Swets K vs. fitted K) error, each across the 4x3 temperature x hold-time grid
# ---------------------------------------------------------------------------
apply_style()

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

# Each grid is a different quantity (n0 fit error vs. permeability error, on
# very different scales), so each panel is normalized to its own max |error|
# rather than sharing one colorbar -- otherwise the smaller-magnitude n0
# panels would wash out to near-white next to the ~70%-error K panel.
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
fig.suptitle('Goethite Thermal-Perturbation Simulation Errors\nAcross 4×3 Temperature-Time Grid')
fig.savefig(os.path.join(OUTDIR, 'goethite_grid_errors4.pdf'), dpi=300)
plt.close(fig)

