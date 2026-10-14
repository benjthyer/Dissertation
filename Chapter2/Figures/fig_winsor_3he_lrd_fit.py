"""
Two-domain (LRD + HRD) fit to the HT-Win-06-01b 3He release, shown as an
Arrhenius plot and as a delta plot.

Model (winsor_he43_model.fit_lrd_from_3he): the HRD follows the Stage 1
Arrhenius line exactly as published; the LRD has the same Ea and D0 but a
smaller radius r * a, so its D/a^2 is larger by 1/r^2. The LRD fraction f
(<= 7.5%, from the delta plot) and r are fitted to the measured cumulative 3He
fractions using the actual heating schedule. Apparent model diffusivities are
obtained by applying the same single-sphere inversion used for the data
(Fechtig & Kalbitzer 1966) to the model's cumulative release.

Data: bounding-method central ln(D/a^2) with LB-UB bounds
('DistilledBoundingMethod' sheet). Steps with 3He < 0.1 pccSTP or no lag
bound are drawn hollow, as elsewhere in this chapter.

Writes: generated/winsor_3he_lrd_arrhenius.{pdf,png}
        generated/winsor_3he_lrd_delta.{pdf,png}
        generated/data/winsor_3he_lrd_fit.csv
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M
from thermochr_utils import InvertFrequencyFactor
from plot_style import apply_style
apply_style()

INK, MUTED = '#222222', '#8a8a8a'
C_MODEL, C_REF = '#2a78d6', '#eb6834'

spec = M.load_spectrum()
lrd = M.fit_lrd_from_3he(spec)
t_s = spec['minutes'] * 60.0
x = 10000.0 / (spec['T_C'] + 273.0)


def apparent_lnD(F_cum):
    Fp = np.r_[0.0, F_cum[:-1]]
    return np.log([InvertFrequencyFactor(t=t_s[i], F=F_cum[i], Fp=Fp[i]) for i in range(F_cum.size)])


sheet = pd.read_excel(M.MASTER_XLSX, sheet_name='DistilledBoundingMethod', header=0)
sheet = sheet[pd.to_numeric(sheet.iloc[:, 0], errors='coerce').notna()].reset_index(drop=True)
lnD_m = pd.to_numeric(sheet['3He ln(d/a^2)m'], errors='coerce').to_numpy()
lnD_lb = pd.to_numeric(sheet['3He ln(d/a^2)LB'], errors='coerce').to_numpy()
lnD_ub = pd.to_numeric(sheet['3He ln(d/a^2)UB'], errors='coerce').to_numpy()
lnD_meas_FK = apparent_lnD(spec['F_end'])                  # same inversion, measured F
lnD_data = np.where(np.isfinite(lnD_m), lnD_m, lnD_meas_FK)  # first steps have no bounds
low_signal = sheet['3He Measured (pccSTP)'].astype(float).to_numpy() < 0.1
solid = ~low_signal & np.isfinite(lnD_lb) & np.isfinite(lnD_ub)
lnD_model = apparent_lnD(lrd['model_F'])
lnD_stage1 = np.log(M.D0_A2) - M.EA / (M.R_CAL * (spec['T_C'] + 273.0))

pd.DataFrame({'Temp_C': spec['T_C'], 'Minutes': spec['minutes'], 'F_meas': spec['F_end'],
              'F_model': lrd['model_F'], 'lnDa2_data': lnD_data, 'lnDa2_LB': lnD_lb,
              'lnDa2_UB': lnD_ub, 'lnDa2_model': lnD_model, 'lnDa2_stage1': lnD_stage1}
             ).to_csv(os.path.join(M.DATA_OUTDIR, 'winsor_3he_lrd_fit.csv'), index=False)

label_fit = (rf"Two-domain model: LRD {lrd['f_lrd']:.1%} of $^3$He, "
             rf"$a_\mathrm{{LRD}}/a_\mathrm{{HRD}}$ = {lrd['size_ratio']:.4f}")

# --- Arrhenius ---------------------------------------------------------------------
fig, ax = plt.subplots()
xr = np.array([x.min() - 0.15, x.max() + 0.15])
ax.plot(xr, np.log(M.D0_A2) - M.EA * xr / (M.R_CAL * 1e4), color=C_REF, lw=1.4, ls='--', zorder=1)
ax.plot(x, lnD_data, color=MUTED, lw=0.6, zorder=1)
yerr = np.vstack([np.clip(lnD_data - lnD_lb, 0, None), np.clip(lnD_ub - lnD_data, 0, None)])
yerr = np.where(np.isfinite(yerr), yerr, 0)
ax.errorbar(x[solid], lnD_data[solid], yerr=yerr[:, solid], fmt='o', ms=6, color=INK,
            mec='white', mew=0.8, elinewidth=1, capsize=0, zorder=3)
ax.plot(x[~solid], lnD_data[~solid], 'o', ms=6, mfc='white', mec=INK, mew=1.1, zorder=3)
ax.plot(x, lnD_model, color=C_MODEL, lw=1.2, zorder=2)
ax.plot(x, lnD_model, 'D', ms=4, color=C_MODEL, zorder=4)
ax.set_xlabel(r'$10^4/T$ (K$^{-1}$)')
ax.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
top = ax.twiny()
top.set_title(r'HT-Win-06-01b $^3$He: two-domain fit', fontsize=14, pad=12)
Ctemps = np.array([175, 200, 225, 250])
top.set_xlim(ax.get_xlim())
top.set_xticks(1e4 / (Ctemps + 273.0))
top.set_xticklabels(Ctemps)
top.set_xlabel('Temperature (°C)', labelpad=6)
ax.legend(handles=[Line2D([], [], color=INK, marker='o', ls='none', label='Data (M, LB–UB)'),
                   Line2D([], [], color=INK, marker='o', mfc='white', ls='none', label='Low signal / no bound'),
                   Line2D([], [], color=C_MODEL, marker='D', ms=4, lw=1.2, label=label_fit),
                   Line2D([], [], color=C_REF, lw=1.4, ls='--', label='Stage 1 line (HRD)')],
          loc='lower left', fontsize=9)
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(M.OUTDIR, f'winsor_3he_lrd_arrhenius.{ext}'), dpi=200)
plt.close(fig)

# --- delta plot (departure from the Stage 1 line vs cumulative 3He) ----------------
fig, ax = plt.subplots()
ax.axhline(0, color=C_REF, lw=1.4, ls='--', zorder=1)
d_data, d_model = lnD_data - lnD_stage1, lnD_model - lnD_stage1
ax.plot(spec['F_end'], d_data, color=MUTED, lw=0.6, zorder=1)
ax.errorbar(spec['F_end'][solid], d_data[solid], yerr=yerr[:, solid], fmt='o', ms=6, color=INK,
            mec='white', mew=0.8, elinewidth=1, capsize=0, zorder=3)
ax.plot(spec['F_end'][~solid], d_data[~solid], 'o', ms=6, mfc='white', mec=INK, mew=1.1, zorder=3)
ax.plot(lrd['model_F'], d_model, color=C_MODEL, lw=1.2, marker='D', ms=4, zorder=4)
ax.set_xlim(0, 0.16)
ax.set_xlabel(r'Cumulative $^3$He fraction, $\Sigma F_{^3\mathrm{He}}$')
ax.set_ylabel(r'$\Delta\ln(D/a^2)$ from Stage 1 line')
ax.set_title(r'HT-Win-06-01b $^3$He: delta plot', fontsize=14)
ax.legend(handles=[Line2D([], [], color=INK, marker='o', ls='none', label='Data (M, LB–UB)'),
                   Line2D([], [], color=C_MODEL, marker='D', ms=4, lw=1.2, label='Two-domain model'),
                   Line2D([], [], color=C_REF, lw=1.4, ls='--', label='Stage 1 line (HRD)')],
          loc='upper right', fontsize=10)
fig.tight_layout()
for ext in ('pdf', 'png'):
    fig.savefig(os.path.join(M.OUTDIR, f'winsor_3he_lrd_delta.{ext}'), dpi=200)
plt.close(fig)
print({k: v for k, v in lrd.items() if k != 'model_F'})
