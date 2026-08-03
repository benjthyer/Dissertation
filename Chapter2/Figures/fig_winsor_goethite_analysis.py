"""
Winsor-06-01b Goethite Diffusivity Analysis.

Reads:
  Win0601bHT_data_and_reduction.xlsx, sheet 'diffusivitiesHTWin0601b'
      (hydrothermal reduction, this study -- via load_diffusivities_HTWin0601b)
  data/HM_Win_06_01B.csv, data/Winsor_waterKAF_BJT.csv
      (vacuum step-heat data, Monteiro 2017 / Farley et al. 2024)

Outputs (all PDFs, dpi=300):
  Comparative_Ratios_Dtplot_WinsorGT.pdf
  CumDtPlot_WinsorGT_decompref.pdf
  RatioDtPlot_WinsorGT.pdf
  Fo_Plot_stage_2_ref_AllGoe.pdf
  DeltasWinsorGTzoomin.pdf
  winsor_goethite_Big_Diffusivities.pdf
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (diffusion_reduction, accumulate, make_grid,
                              InvertFrequencyFactor, load_diffusivities_HTWin0601b)
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

def Forward_Diffuse(Dt_a2):
    Bt = np.pi ** 2 * Dt_a2
    F = (6 / np.pi ** 1.5) * Bt ** 0.5
    if F > 0.1:
        F = 1 - (6 / np.pi ** 2) * np.exp(-Bt)
    if F < 0.9:
        F = (6 / np.pi ** 1.5) * Bt ** 0.5 - (3 / np.pi ** 2) * Bt
    return F

# ---------------------------------------------------------------------------
# Diffusion parameters for reference lines
# ---------------------------------------------------------------------------
def D_a2reg(T):
    return 17623836.64 * np.exp(-38033.18815 / (1.987 * T))

def D_a2Decomp(T):
    return 2780000000 * np.exp(-35600 / (1.987 * T))

R = 1.987

# ---------------------------------------------------------------------------
# Load Winsor vacuum data (HDM = Monteiro 2017, KAF = Farley et al. 2024)
# ---------------------------------------------------------------------------
DiffdatBJT = load_diffusivities_HTWin0601b(MASTER_XLSX)

Diffdat = pd.read_csv(os.path.join(RAW_DATA_DIR, 'HM_Win_06_01B.csv'))
TempK_HDM   = np.array(Diffdat['Temp (C)']) + 273
TimeS_HDM   = np.array(Diffdat['Time (h)']) * 3600
Winsor_Data = {}
for i, col in enumerate(['3HeCPS', '4HeCPS']):
    iso = ['3', '4'][i]
    Winsor_Data[f'He{iso}HDM'] = diffusion_reduction(
        np.array(Diffdat[col]).astype(float),
        TimeSeconds=TimeS_HDM, TempKelvin=TempK_HDM,
        newDiffName=os.path.join(DATA_OUTDIR, f'He{iso}_HDMwinsor_diffusion.csv'))
    plt.close()

Diffdat1 = pd.read_csv(os.path.join(RAW_DATA_DIR, 'Winsor_waterKAF_BJT.csv'), skiprows=1).iloc[:30]
TempK_KAF = np.array(Diffdat1['Temp (C)']) + 273
TimeS_KAF = np.array(Diffdat1['Time (h)']) * 3600
for i, col in enumerate(['3He PCC', '4He NCC']):
    iso = ['3', '4'][i]
    Winsor_Data[f'He{iso}KAF'] = diffusion_reduction(
        np.array(Diffdat1[col]).astype(float),
        TimeSeconds=TimeS_KAF, TempKelvin=TempK_KAF,
        newDiffName=os.path.join(DATA_OUTDIR, f'He{iso}_KAFwinsor_diffusion.csv'))
    plt.close()

# Cumulative 3He and 4He for HDM
cum3HM = accumulate(np.array(Diffdat['3HeCPS']).astype(float))
cum4HM = accumulate(np.array(Diffdat['4HeCPS']).astype(float))

AG5 = DiffdatBJT['3']['He Corrected'].to_numpy()
AH5 = DiffdatBJT['3']['He Corrected 2 sigma'].to_numpy()
AI5 = DiffdatBJT['4']['He Corrected'].to_numpy()
AJ5 = DiffdatBJT['4']['He Corrected 2 sigma'].to_numpy()
R_val   = 1000 * AI5 / AG5
Rbulk   = R_val / (1000 * 145.8 / 146.1)
Rerr    = 2 * ((AH5 * 1000 * AI5 / (2 * AG5 ** 2)) ** 2
               + (1000 * AJ5 / (AG5 * 2)) ** 2) ** 0.5
Rbulkerr = Rerr / (1000 * 145.8 / 146.1)
lowerr  = (Rbulkerr < 0.15) & (Rbulk > 0)

# ---------------------------------------------------------------------------
# Figure 1: 3He/4He ratio vs cumulative 3He yield
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
ax.errorbar(accumulate(AG5)[lowerr] / 146.1, Rbulk[lowerr],
            yerr=Rbulkerr[lowerr], marker='o', color='Blue',
            linestyle='', label='Hydrothermal, This Work')
for iso, col, lab in [('3', 'orange', 'Vacuum (HDM)'), ('4', 'orange', None)]:
    sub = Winsor_Data[f'He{iso}HDM']
    frac = accumulate(np.array(sub['He Yield (nCC@STP)']))[:-1] / cum3HM[-1]
    ratio = (sub['He Yield (nCC@STP)'].iloc[:-1].to_numpy()
             / Winsor_Data['He4HDM']['He Yield (nCC@STP)'].iloc[:-1].to_numpy()
             / (cum4HM[-1] / cum3HM[-1]))
    if iso == '3':
        ax.scatter(frac, ratio, color=col, label=lab, marker='s')
ax.set_xlabel(r'Cumulative $\Sigma^3He$ Yield')
ax.set_ylabel(r'$^3$He/$^4$He Ratio (Normalised to Bulk)')
ax.set_title('Comparative He Isotope Ratios — Win-06-01b Goethite')
ax.legend()
make_grid()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Comparative_Ratios_Dtplot_WinsorGT.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: Cumulative Dt plot (reference to decomposition domain)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
for iso, label in [('3', 'Vacuum 3He: Monteiro, 2017'), ('4', 'Vacuum 4He: Monteiro, 2017')]:
    sp = D_a2Decomp(Winsor_Data[f'He{iso}HDM']['Temp (C)'] + 273) * \
         (Winsor_Data[f'He{iso}HDM']['Time (min)'] * 60)
    ax.scatter(accumulate(sp), Winsor_Data[f'He{iso}HDM']['Fcum'],
               label=label, marker=['s', 'x'][['3', '4'].index(iso)],
               color='orange')
for iso in ['3', '4']:
    sp = D_a2Decomp(DiffdatBJT[iso]['Temp (C)'] + 273) * (DiffdatBJT[iso]['Minutes'] * 60)
    ax.scatter(accumulate(sp), DiffdatBJT[iso]['Fi+1'],
               label=f'Hydrothermal {iso}He: This Study',
               marker=['s', 'x'][['3', '4'].index(iso)], color='blue')
Dt_refs = np.linspace(0, 1, 10000)
ax.plot(Dt_refs, 0.88 * np.array([Forward_Diffuse(d) for d in Dt_refs]),
        color='black', label='Stage 2 Ref Domain (88%)')
ax.set_xlim(0, 0.5)
ax.set_xlabel(r'Reference Fourier Number $Fo = Dt/a^2$')
ax.set_ylabel(r'Cumulative Fractional $^n$He Yield')
ax.set_title('Thermal History-Normalised He Degassing\nWin-06-01b Goethite')
ax.legend(loc='center right', fontsize=8)
make_grid()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'CumDtPlot_WinsorGT_decompref.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 3: 3He/4He ratio vs Dt (Fo number)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
sp3 = D_a2Decomp(Winsor_Data['He3HDM']['Temp (C)'] + 273) * \
      (Winsor_Data['He3HDM']['Time (min)'] * 60)
ratio_HM = (Winsor_Data['He4HDM']['He Yield (nCC@STP)'].to_numpy()
            / Winsor_Data['He3HDM']['He Yield (nCC@STP)'].to_numpy()) / (cum4HM[-1] / cum3HM[-1])
ax.scatter(accumulate(sp3), ratio_HM, label='Vacuum (HDM)', color='orange', marker='s')
ax.set_xlabel(r'Reference Fourier Number $Fo = Dt/a^2$')
ax.set_ylabel(r'$^4$He/$^3$He Ratio (Normalised to Bulk)')
ax.set_title('He Isotope Ratio vs Fourier Number — Win-06-01b')
ax.legend()
make_grid()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'RatioDtPlot_WinsorGT.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 4: Fo plot — fractional yield vs Fo for all datasets
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
for iso, lab in [('3', 'Hydrothermal 3He'), ('4', 'Hydrothermal 4He')]:
    sp = D_a2Decomp(DiffdatBJT[iso]['Temp (C)'] + 273) * (DiffdatBJT[iso]['Minutes'] * 60)
    ax.scatter(accumulate(sp), DiffdatBJT[iso]['Fi+1'],
               marker=['s', 'x'][['3', '4'].index(iso)], label=lab, color='blue', zorder=5)
for iso in ['3', '4']:
    sp = D_a2Decomp(Winsor_Data[f'He{iso}HDM']['Temp (C)'] + 273) * \
         (Winsor_Data[f'He{iso}HDM']['Time (min)'] * 60)
    ax.scatter(accumulate(sp), Winsor_Data[f'He{iso}HDM']['Fcum'],
               marker=['s', 'x'][['3', '4'].index(iso)], color='orange',
               label=f'Vacuum {iso}He (HDM)')
ax.plot(np.linspace(0, 1, 1000),
        0.88 * np.array([Forward_Diffuse(d) for d in np.linspace(0, 1, 1000)]),
        'k-', label='Stage 2 Ref (88%)')
ax.set_xlim(0, 0.5)
ax.set_xlabel(r'$Fo = Dt/a^2$')
ax.set_ylabel(r'Cumulative Fractional Yield')
ax.set_title('Stage 2 Fo Plot — Win-06-01b Goethite')
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Fo_Plot_stage_2_ref_AllGoe.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 5: Delta plot (Δln(D/a²) vs cumulative yield)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots()
ax.axhline(0, color='black', alpha=0.5)
for iso, lab, col in [('3', '3He', 'blue'), ('4', '4He', 'red')]:
    bjt = DiffdatBJT[iso]
    ref_lnD = np.log(D_a2reg(bjt['Temp (C)'] + 273))
    delta = bjt['ln(d/a^2)'] - ref_lnD
    ax.scatter(bjt['Fi+1'], delta, label=f'Hydrothermal {lab}', color=col,
               marker=['s', 'x'][['3', '4'].index(iso)])
ax.set_xlabel(r'Cumulative Fractional Yield')
ax.set_ylabel(r'$\Delta \ln(D/a^2)$ (measured – Stage 1 reference)')
ax.set_title('Delta Plot — Win-06-01b Goethite (Zoomed)')
ax.legend()
ax.set_xlim(0, 1)
make_grid()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'DeltasWinsorGTzoomin.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 6: Main Arrhenius plot (all datasets)
# ---------------------------------------------------------------------------
xlim = [1E4 / (500 + 273), 1E4 / (70 + 273)]
Ctemps = np.array([75, 100, 150, 200, 250, 300, 350, 400, 450])

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()

# Stage 2 reference line
ax1.plot(xlim, np.log(2780000000 * np.exp(-np.array(xlim) * 3.5600 / R)),
         color='brown', label='Stage 2 Ref: Ea = 149 kJ/mol')

for i, lab in enumerate(['Monteiro, 2017', 'Farley et al., 2024']):
    key = ['HDM', 'KAF'][i]
    col = ['orange', 'red'][i]
    for j, iso in enumerate(['4', '3']):
        sub = Winsor_Data[f'He{iso}{key}']
        ax1.plot(sub['10^4/T'], sub['ln(D/a^2)'], linestyle=':', color=col, alpha=0.5)
        ax1.scatter(sub['10^4/T'], sub['ln(D/a^2)'],
                    marker=['s', 'x'][j], color=col, alpha=0.5,
                    label=f'Vacuum {iso}He: {lab}')

for j, iso in enumerate(['3', '4']):
    bjt = DiffdatBJT[iso]
    ax1.plot(bjt['10000/TK'], bjt['ln(d/a^2)'], linestyle='--', color='blue', alpha=0.7)
    ax1.scatter(bjt['10000/TK'], bjt['ln(d/a^2)'],
                marker=['+', 'o'][j], color='blue',
                label=f'Hydrothermal {iso}He: This Work')

ax1.set_xlim(xlim)
ax2.set_xticks(1E4 / (Ctemps + 273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (°C)')
ax1.set_xlabel(r'$10^4/T$ (K)')
ax1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
ax1.legend(fontsize=7)
plt.title('He Diffusivities — Win-06-01b Goethite')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'winsor_goethite_Big_Diffusivities.pdf'), dpi=300)
plt.close(fig)
