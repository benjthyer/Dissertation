"""
Identical heating steps show decreasing 4He permeability in the encapsulated
water experiment, comparing measured yield to the cooling-model prediction.

Reads: data/MCEmptyTubeData.xlsx  (sheet: H2O Isothermal OD734 ID487)

Outputs:
  ChangingYieldH2Otube.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import make_grid
from plot_style import apply_style
apply_style()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

WaterData = pd.read_excel(
    '../Tables/MCEmptyTubeData.xlsx',
    sheet_name='H2O Isothermal OD734 ID487',
    skiprows=1,
)
identicals = [1, 2, 3, 5, 6, 10, 11, 12, 13, 14, 15, 16, 17]

fig, ax = plt.subplots()
ax.scatter(
    WaterData['cumulative hot time (s)'][identicals] / 3600,
    1 - WaterData['4He measured'][identicals],
    label='4He Measurements, Encapsulated Water, MC',
)
ax.plot(
    [
        np.min(WaterData['cumulative hot time (s)'][identicals] / 3600),
        np.max(WaterData['cumulative hot time (s)'][identicals] / 3600),
    ],
    1 - np.array([0.877168987133026, 0.877168987133026]),
    color='red',
    linewidth=2,
    label='Predicted by Cooling Model\nw/ 4He Permeabilities of Swets et al., 1961',
)
make_grid()
ax.legend(loc='center left')
ax.set_xlabel('Cumulative Hours at 100°C')
ax.set_ylabel(r'Fractional Yield $\left(\frac{m}{n_0}\right)$')
ax.set_title(
    'Identical Steps Show Decreasing Helium-4\nPermeability in Encapsulated Water Experiment'
)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'ChangingYieldH2Otube.pdf'), dpi=300)
plt.close(fig)
