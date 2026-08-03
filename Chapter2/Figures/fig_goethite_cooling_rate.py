"""
Goethite tube cooling-rate fit: dT/dt vs. T, discrete values calculated from
the Watlow temperature record cooling curves for the Winsor Goethite
experiment (Cooling_Rate sheet of the master workbook) vs. the quadratic
dT/dt(T) curve used by goethite_cooling() in diffusion_utils.py (that
quadratic was originally fit to these same points in Microsoft Excel; it is
not re-fit here, only evaluated against the data for comparison and R^2).

Output: goethite_cooling_rate_fit.pdf
"""
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from diffusion_utils import goethite_cooling
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

data = pd.read_excel(MASTER_XLSX, sheet_name='Cooling_Rate').dropna(subset=['T'])
T_data = data['T'].to_numpy(dtype=float)
dTdt_data = data['dTdt'].to_numpy(dtype=float)


def dTdt_model(T_C):
    """Evaluate diffusion_utils.goethite_cooling's dT/dt (°C/s) at T_C (°C)."""
    T_K = T_C + 273
    return goethite_cooling(T_K, dt=1.0) - T_K


dTdt_pred = dTdt_model(T_data)
ss_res = np.sum((dTdt_data - dTdt_pred) ** 2)
ss_tot = np.sum((dTdt_data - np.mean(dTdt_data)) ** 2)
r2 = 1 - ss_res / ss_tot
print(f"n = {len(T_data)} points, R^2 (model vs. data) = {r2:.4f}")

T_curve = np.linspace(T_data.min(), T_data.max(), 500)

fig, ax = plt.subplots()
ax.scatter(T_data, dTdt_data, s=10, color='black', alpha=0.4, label='Watlow record (discrete dT/dt)')
ax.plot(T_curve, dTdt_model(T_curve), color='red', linestyle='--',
        label=r'$dT/dt = -9.23\times10^{-6}(T-24)^2 - 7.74\times10^{-4}(T-24)$')
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('dT/dt (°C/s)')
ax.set_title(f'Goethite Tube Cooling Rate Fit\n$R^2$ = {r2:.4f}, n = {len(T_data)}')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'goethite_cooling_rate_fit.pdf'), dpi=300)
plt.close(fig)
