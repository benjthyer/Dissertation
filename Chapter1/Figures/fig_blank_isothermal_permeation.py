"""
Blank isothermal permeation fits for 3He and 4He in silica tubes.
Reads: 111923SmallSIlicaTubeISOTHERMALS.csv + STD_nov.csv

Outputs (one PDF per temperature per isotope):
  Blanks/3He_111923IsothermalT{T}C.pdf
  Blanks/4He_111923IsothermalT{T}C.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
apply_style()
from thermochr_utils import (swets_K, Jones, tube_permeate2, Ratoms,
                              accumulate, forward_permeate, KenColdInversion,
                              MCHeReducer)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')

os.makedirs(os.path.join(OUTDIR, 'Blanks'), exist_ok=True)

OD = 0.1159     # cm
ID = 0.0747     # cm
G  = 2 / (np.log(OD / ID) * (ID / 2) ** 2)

reducer = MCHeReducer('data/STD_nov.csv')
DATA = pd.read_csv('data/111923SmallSIlicaTubeISOTHERMALS.csv').to_numpy()
He3, He4 = reducer.reduce(DATA)
DATA[:, 4] = He3
DATA[:, 6] = He4

t, He3_step, He4_step, T = [], [], [], None

for r in range(np.shape(DATA)[0]):
    if DATA[r, 3] == 0:
        if not len(t):
            continue
        # Fit and plot this isotherm
        t_arr  = np.array(t)
        He3_a  = np.array(He3_step)
        He4_a  = np.array(He4_step)
        tot3   = np.sum(He3_a)
        tot4   = np.sum(He4_a)
        t_long = np.linspace(0, np.max(accumulate(t_arr)), 400)
        name   = f'111923IsothermalT{T - 273:.0f}C'

        K4      = swets_K(T)
        K3      = K4 * Jones(T)
        n3mod   = He3_a[0] / (1 - tube_permeate2(t=t_arr[0], T=T, OD=OD, ID=ID, He='3He'))
        n4mod   = He4_a[0] / (1 - tube_permeate2(t=t_arr[0], T=T, OD=OD, ID=ID, He='4He'))
        lam3mod = G * K3 * T * Ratoms
        lam4mod = G * K4 * T * Ratoms

        try:
            lam3fit, n3fit = KenColdInversion(t_arr, He3_a, plot=False)
            lam4fit, n4fit = KenColdInversion(t_arr, He4_a, plot=False)
        except Exception:
            t, He3_step, He4_step = [], [], []
            T = DATA[r + 1, 3] + 273 if r + 1 < len(DATA) else None
            continue

        for iso, He_a, tot, lam_mod, n0_mod, lam_fit, n0_fit, ylabel in [
            ('3He', He3_a, tot3, lam3mod, n3mod, lam3fit, n3fit, 'Cumulative Yield (pcc)'),
            ('4He', He4_a, tot4, lam4mod, n4mod, lam4fit, n4fit, 'Cumulative Yield (ncc)'),
        ]:
            err_mod = -(tot - n0_mod) / tot * 100
            err_fit = -(tot - n0_fit) / tot * 100
            fig, ax = plt.subplots()
            ax.scatter(accumulate(t_arr), accumulate(He_a), zorder=5)
            ax.plot(t_long, forward_permeate(t_long, lam_mod, n0_mod),
                    label=f'Swets Model: n0={n0_mod:.1f}, err={err_mod:.1f}%')
            ax.plot(t_long, forward_permeate(t_long, lam_fit, n0_fit),
                    label=f'Fit: n0={n0_fit:.1f}, err={err_fit:.1f}%')
            ax.set_title(f'{iso} Isothermal Permeation: T = {T - 273:.0f}°C')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel(ylabel)
            ax.grid(True)
            ax.legend()
            fig.tight_layout()
            fname = os.path.join(OUTDIR, 'Blanks', f'{iso}_{name}.pdf')
            fig.savefig(fname, dpi=300)
            plt.close(fig)
            print(f'Saved {fname}')

        t, He3_step, He4_step = [], [], []
    else:
        t.append(DATA[r, 8])
        He3_step.append(DATA[r, 4])
        He4_step.append(DATA[r, 6])
        T = DATA[r, 3] + 273
