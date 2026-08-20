"""
Fraction of ampoule He within the glass wall at EQM — 3He vs 4He comparison.

Output: PercentHeInGlassIsotopesGoeth.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import swets, Ratoms, make_grid
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)

Rcal = 1.987

def S3_4(T):
    """3He/4He solubility ratio (Jones, 1953)."""
    return 1.003 * np.exp(6 / (T * Rcal))

# Goethite tube geometry (OD 830 µm, ID 540 µm, per Cell 094)
a = 0.052 / 2   # cm  inner radius
b = 0.081 / 2   # cm  outer radius
G = 2 / (a ** 2 * np.log(b / a))
D = (2 * Ratoms / a ** 2) * ((b ** 3 - 3 * a ** 2 * b + 2 * a ** 3) / (6 * (b - a)))

Ts = np.linspace(24, 250, 500) + 273
Ss = np.array([swets('S', T) for T in Ts])

fig, ax = plt.subplots()
ax.plot(Ts - 273, 100 * (1 / (1 / (D * Ts * Ss) + 1)),       label='4He in tube')
ax.plot(Ts - 273, 100 * (1 / (1 / (D * Ts * Ss * S3_4(Ts)) + 1)), label='3He in tube')
ax.legend()
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('He Within Glass at EQM (%)')
ax.set_title('Portion of Ampoule He Within Glass at EQM\n(Goethite Tube Geometry, Constant G)')
make_grid()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'PercentHeInGlassIsotopesGoeth.pdf'), dpi=300)
plt.close(fig)
