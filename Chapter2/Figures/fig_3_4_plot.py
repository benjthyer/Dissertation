"""
Bulk-normalized 4He/3He spectra for Win-06-01b goethite: hydrothermal
step-heating (this study) compared with both vacuum datasets (Monteiro
2017; Farley et al. 2024) against cumulative fractional 3He yield.
Extends the equivalent panel in fig_winsor_goethite_analysis.py (which
only plots the HDM vacuum dataset) by adding the KAF vacuum dataset.
Recomputes the vacuum diffusivity reductions independently (re-writing
He{3,4}_{HDM,KAF}winsor_diffusion.csv, matching the output of
fig_winsor_goethite_analysis.py) so this script can run standalone.

The hydrothermal series is plotted as a shaded LB-UB envelope read
directly from the master workbook's 'DistilledUncertaintyTreatment'
sheet (that sheet's own bulk-normalized 4/3He LB/M/UB columns and its
own cumulative fractional 3He yield column), rather than recomputed from
the per-isotope diffusivitiesHTWin0601b{M,UB,LB} sheets. Steps are
excluded from the envelope if either: the sheet has no permeation-lag
bound yet (too little cumulative signal to bracket -- shown as '--' in
the workbook, true only for the earliest steps); or the measured 3He
signal for that step is below 0.1 pccSTP (too low-signal for a reliable
ratio -- these are the noisy/spiky points).

Reads:
  Win0601bHT_data_and_reduction.xlsx, sheet 'DistilledUncertaintyTreatment'
      (hydrothermal "treatment as uncertainty" bulk-normalized ratio
      bounds and cumulative fractional 3He yield, this study)
  data/HM_Win_06_01B.csv            (vacuum, Monteiro 2017)
  data/Winsor_waterKAF_BJT.csv      (vacuum, Farley et al. 2024)

Outputs:
  Comparative_Ratios_Dtplot_WinsorGT_VacuumHDMKAF.pdf
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import diffusion_reduction, accumulate, make_grid, low_signal_HTWin0601b_mask
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(FIG_DIR, 'data')
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
DATA_DIR = FIG_DIR
os.chdir(DATA_DIR)
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(DATA_OUTDIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Vacuum reductions (HDM = Monteiro 2017, KAF = Farley et al. 2024)
# ---------------------------------------------------------------------------
Diffdat = pd.read_csv(os.path.join(RAW_DATA_DIR, 'HM_Win_06_01B.csv'))
TempKelvin = np.array(Diffdat['Temp (C)']) + 273
TimeSeconds = np.array(Diffdat['Time (h)']) * 3600

Winsor_Data = {}
for i, name in enumerate(['3HeCPS', '4HeCPS']):
    iso = ['3', '4'][i]
    Winsor_Data[f'He{iso}HDM'] = diffusion_reduction(
        np.array(Diffdat[name]).astype(float), TimeSeconds=TimeSeconds,
        TempKelvin=TempKelvin, newDiffName=os.path.join(DATA_OUTDIR, f'He{iso}_HDMwinsor_diffusion.csv'))
    plt.close()

Diffdat1 = pd.read_csv(os.path.join(RAW_DATA_DIR, 'Winsor_waterKAF_BJT.csv'), skiprows=1)[:30]
TempKelvin = np.array(Diffdat1['Temp (C)']) + 273
TimeSeconds = np.array(Diffdat1['Time (h)']) * 3600
for i, name in enumerate(['3He PCC', '4He NCC']):
    iso = ['3', '4'][i]
    Winsor_Data[f'He{iso}KAF'] = diffusion_reduction(
        np.array(Diffdat1[name]).astype(float), TimeSeconds=TimeSeconds,
        TempKelvin=TempKelvin, newDiffName=os.path.join(DATA_OUTDIR, f'He{iso}_KAFwinsor_diffusion.csv'))
    plt.close()

# ---------------------------------------------------------------------------
# Hydrothermal 4He/3He ratio envelope, bulk-normalized -- read directly from
# the DistilledUncertaintyTreatment sheet's own LB/M/UB columns and its own
# cumulative fractional 3He yield column (see module docstring).
# ---------------------------------------------------------------------------
distilled = pd.read_excel(MASTER_XLSX, sheet_name='DistilledUncertaintyTreatment', header=0)
# Drop the trailing 'Total' summary row (its Temp cell is text, not a number).
distilled = distilled[pd.to_numeric(distilled.iloc[:, 0], errors='coerce').notna()]

F3He = pd.to_numeric(distilled.iloc[:, 23], errors='coerce').to_numpy()
Rbulk_lb = pd.to_numeric(distilled.iloc[:, 24], errors='coerce').to_numpy()
Rbulk_m = pd.to_numeric(distilled.iloc[:, 25], errors='coerce').to_numpy()
Rbulk_ub = pd.to_numeric(distilled.iloc[:, 26], errors='coerce').to_numpy()

# Earliest steps have no permeation-lag bound yet (too little cumulative
# signal to bracket -- shown as '--' in the workbook); exclude those, along
# with any step flagged as low-signal (measured 3He <0.1 pccSTP, shared
# across every hydrothermal plot -- see thermochr_utils.low_signal_HTWin0601b_mask)
# -- these are the noisy/spiky points in the envelope.
low_signal = low_signal_HTWin0601b_mask(MASTER_XLSX)
have_bounds = (np.isfinite(Rbulk_lb) & np.isfinite(Rbulk_m) & np.isfinite(Rbulk_ub)
               & ~low_signal)


def make_plot(outname):
    fig, ax = plt.subplots()

    cum3HM = accumulate(Winsor_Data['He3HDM']['He Yield (nCC@STP)'])
    cum4HM = accumulate(Winsor_Data['He4HDM']['He Yield (nCC@STP)'])
    ratio_HM = (Winsor_Data['He4HDM']['He Yield (nCC@STP)'] / Winsor_Data['He3HDM']['He Yield (nCC@STP)']) \
        / (cum4HM[-1] / cum3HM[-1])
    ax.plot(cum3HM / cum3HM[-1], ratio_HM, color='Orange')
    ax.scatter(cum3HM / cum3HM[-1], ratio_HM, color='Orange', label='In Vacuum: Monteiro, 2017')

    cum3KF = accumulate(Winsor_Data['He3KAF']['He Yield (nCC@STP)'])
    cum4KF = accumulate(Winsor_Data['He4KAF']['He Yield (nCC@STP)'])
    ratio_KF = (Winsor_Data['He4KAF']['He Yield (nCC@STP)'] / Winsor_Data['He3KAF']['He Yield (nCC@STP)']) \
        / (cum4KF[-1] / cum3KF[-1])
    ax.plot(cum3KF / cum3KF[-1], ratio_KF, color='Red')
    ax.scatter(cum3KF / cum3KF[-1], ratio_KF, color='Red', label='In Vacuum: Farley et al., 2024')

    ax.fill_between(F3He[have_bounds], Rbulk_lb[have_bounds], Rbulk_ub[have_bounds],
                         color='Blue', alpha=0.25, linewidth=0, zorder=1)
    ax.plot(F3He[have_bounds], Rbulk_m[have_bounds], color='Blue', marker = 'o', markersize=3,
            label='Hydrothermal, This Work', zorder=2)

    make_grid()
    ax.set_title(r'Bulk-Normalized $^4He/^3He$ for Win-06-01b Goethite')
    ax.set_xlabel(r'$\Sigma F^3He$')
    ax.set_ylabel(r'$\left(^4He/^3He\right)_N$')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, outname), dpi=300)
    plt.close(fig)


make_plot('Comparative_Ratios_Dtplot_WinsorGT_VacuumHDMKAF.pdf')
