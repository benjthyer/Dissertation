"""
Helium diffusivity inversions from vacuum step-heat experiments on pyrite
(Rustenburg, natural).  Reads Batch 56.csv and Batch 55_clarity.csv.

Outputs:
  double_natural_pyrite.pdf
  MDDPlot.pdf
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import InvertFrequencyFactor, diffusion_reduction
from plot_style import apply_style
apply_style()

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

Rcal = 1.987

def reduce_batch(filename, total_yield, low_T_RE_threshold=201):
    """Load a Batch CSV and return (TempK, TimeSeconds, lnD_a2, fcum)."""
    DIFFCELL = pd.read_csv(filename)
    try:
        TK = 273 + DIFFCELL['Avg Temp'].to_numpy()
        ts = 60  * DIFFCELL['Time (min)'].to_numpy()
    except KeyError:
        TK = 273 + DIFFCELL['CIT RefNo'].to_numpy()
        ts = 60  * DIFFCELL['Position'].to_numpy()
    Names = DIFFCELL['Name'].tolist()
    Type  = DIFFCELL['Analysis'].tolist()
    He    = DIFFCELL['BC nCC'].to_numpy()

    CB, real_i, real_steps = 0, False, []
    for i, name in enumerate(Names):
        if Type[i] in ('Diff Cell', 'DiffCell'):
            if 'CB' in name:
                CB = He[i]
            elif 'RE' in name or TK[i] < low_T_RE_threshold + 273:
                if real_i is not False:
                    He[real_i] += He[i] - CB
            else:
                He[i] -= CB
                real_i = i
                real_steps.append(i)
    real_steps = np.array(real_steps)

    TK1 = TK[real_steps]
    ts1 = ts[real_steps]
    He1 = He[real_steps]

    Fp, fcum, D_a2, lnD_a2 = 0, [], [], []
    for i, sy in enumerate(He1):
        F  = Fp + sy / total_yield
        ff = InvertFrequencyFactor(t=ts1[i], F=F, Fp=Fp)
        D_a2.append(ff)
        lnD_a2.append(np.log(ff) if ff > 0 else np.nan)
        fcum.append(F)
        Fp = F
    return TK1, ts1, np.array(lnD_a2), np.array(fcum)

TK56, ts56, lnD56, fcum56 = reduce_batch('Batch 56.csv',  total_yield=200)
TK55, ts55, lnD55, fcum55 = reduce_batch('Batch 55_clarity.csv', total_yield=200)

Ctemps = np.array([200, 250, 275, 320, 350, 400, 450, 500, 600, 700])

# Reference lines
D0_ref  = np.exp(20.5)
Ea_ref  = 255000  # J/mol (≈ 255 kJ/mol)
D0_dap  = (10 ** 1.5) / (500 / 1E4) ** 2  # Durango apatite r=500 µm
Ea_dap  = 33000   # cal/mol

# ---------------------------------------------------------------------------
# Figure 1: Double natural pyrite Arrhenius
# ---------------------------------------------------------------------------
fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

ax1.plot(1E4 / TK56, lnD56, linestyle='--', marker='o', color='r',
         label='Vacuum (Batch 56): r = 106 µm')
ax1.plot(1E4 / TK55[5:], lnD55[5:], linestyle=':', marker='d', color='b',
         label='Sulfur-buffered (Batch 55): r = 106 µm')

xlim = ax1.get_xlim()
# Ea = 255 kJ line
ax1.plot(list(xlim),
         [np.log(D0_ref * np.exp(-Ea_ref / (8.314 * 1E4 / x))) for x in xlim],
         color='k', linestyle='-.',
         label=r'$E_a$ = 255 kJ/mol Reference')
# Durango apatite r=500 µm
ax1.plot(list(xlim),
         [np.log(D0_dap * np.exp(-Ea_dap / (Rcal * 1E4 / x))) for x in xlim],
         color='g', linestyle='--',
         label='Durango Apatite r = 500 µm')

ax2.set_xticks(1E4 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (°C)')
ax1.set_xlabel(r'$10^4/T$ (K)')
ax1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
ax1.legend(fontsize=9)
plt.title('He Diffusivity Inversions — Natural Pyrite\nApparent MDD, Ea ≈ 255 kJ')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'double_natural_pyrite.pdf'), dpi=300,
            bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: Delta plot (relative to 255 kJ reference)
# ---------------------------------------------------------------------------
ref_lnD = np.log(D0_ref * np.exp(-Ea_ref / (8.314 * TK55)))
delta   = lnD55 - ref_lnD

fig, ax = plt.subplots(figsize=(3.5, 2.5))
ax.plot(fcum55, delta)
ax.set_ylabel(r'$\Delta = \ln(D/a^2)_\mathrm{meas} - \ln(D/a^2)_\mathrm{ref}$')
ax.set_xlabel('Cumulative Yield')
ax.set_title('Delta Plot Referenced to Ea = 255 kJ Line')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'MDDPlot.pdf'), dpi=300)
plt.close(fig)
