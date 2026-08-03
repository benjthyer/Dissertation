"""
He isotope fractionation and kinetic 3He/4He permeability during tube permeation.
Reads pre-reduced CSVs from reduce_mc_diffcell.py (Cell 090 output).
  111923SmallSIlicaTubeISOTHERMALS_3He_reduced.csv
  111923SmallSIlicaTubeISOTHERMALS_4He_reduced.csv

Outputs:
  Rayleigh_Distillation.pdf
  Kinetic3He4HePermeability.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
apply_style()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

stem = 'data/111923SmallSIlicaTubeISOTHERMALS'
d3 = pd.read_csv(f'{stem}_3He_reduced.csv')
d4 = pd.read_csv(f'{stem}_4He_reduced.csv')

# Total yields and isotope ratio
TY3 = d3['3He measured (pCC@STP)'].sum()
TY4 = d4['4He measured (nCC@STP)'].sum()
Ra  = 1.39E-6   # atmospheric 3He/4He

IR = (TY3 / (1000 * TY4)) / Ra
in_tube_IR = (d3['n0'] / (1000 * d4['n0'])) / Ra

# ---------------------------------------------------------------------------
# Figure 1: Rayleigh distillation (a = 1.1)
# ---------------------------------------------------------------------------
a = 1.1
rayleigh     = IR * ((1 - d4['Fcum']) ** (a - 1))
rayleigh_top = rayleigh * a

measured_ratio = (d3['3He measured (pCC@STP)'] / (1000 * d4['4He measured (nCC@STP)'])) / Ra

fig, ax = plt.subplots()
ax.plot(d4['Fcum'], measured_ratio, 'blue', label='Measured ³He/⁴He (normalised to Ra)')
ax.plot(d4['Fcum'], in_tube_IR, color='r', label='³He/⁴He Inside Tube / Ra')
ax.plot(d4['Fcum'], rayleigh, 'r--')
ax.plot(d4['Fcum'], rayleigh_top, 'b--')
ax.axhline(IR, color='k', linestyle='--', label='Total ³He/⁴He Ratio / Ra')
ax.legend()
ax.set_xlabel('Cumulative Fractional Yield')
ax.set_ylabel('³He/⁴He (Normalised to Atmosphere)')
ax.set_title(f'He Isotope Fractionation and Rayleigh Distillation\na = {a}')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Rayleigh_Distillation.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: Kinetic isotope fractionation of 3He/4He
# ---------------------------------------------------------------------------
TempKelvin = d4['Temp (C)'] + 273

fig, ax = plt.subplots()
sc = ax.scatter(-np.log(1 - d4['Fcum']),
                np.log(in_tube_IR / IR),
                c=TempKelvin)
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('T (K)')
ax.set_xlabel(r'$-\ln(1 - f_{^4\mathrm{He}})$')
ax.set_ylabel(r'$\ln(R / R_0)$ in tube')
ax.set_title('Kinetic Fractionation of ³He/⁴He')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Kinetic3He4HePermeability.pdf'), dpi=300)
plt.close(fig)
