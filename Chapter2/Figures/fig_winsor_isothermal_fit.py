"""
First-order exponential fit to Winsor 3He isothermal step-heating data at 250°C.

Output:
  WinsorFirstOrderFit.pdf
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import FirstOrdInversion, accumulate, forward_permeate
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)

# Hardcoded isothermal 250 °C data from Winsor sample
tg = np.array([300, 300, 300, 10250]) * 60    # seconds
Heg = np.array([0.402737006, 0.376896744, 0.373085304, 8.576210633])

lam, n0fit = FirstOrdInversion(tg, Heg, plot=False)

cumt = accumulate(tg)
longt = np.linspace(0, cumt[-1], 500)

fig, ax = plt.subplots()
ax.plot(longt, forward_permeate(longt, lam, n0fit), label='Exponential Fit')
ax.scatter(cumt, accumulate(Heg), zorder=5, label='Observed (Winsor, 250°C)')
ax.set_title(
    f'Winsor Isothermals at 250°C\n'
    f'Fit: Total = {n0fit:.2f} pcc ³He,  λ = {lam:.3e} s⁻¹')
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Cumulative ³He Yield (pcc)')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'WinsorFirstOrderFit.pdf'), dpi=300)
plt.close(fig)
