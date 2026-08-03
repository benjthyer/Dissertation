"""
MC Diffusion Cell Data Reduction with cold-bracket permeation corrections.
Run from Chapter1/Figures/ (the directory containing all data CSV files and
the NGL Watlow Heat Log folder).

Reads:  <DIFFCELL_name>  (MC batch CSV)
        <STD_name>       (MC standards CSV for MCHeReducer)
        NGL Watlow Heat Log/DC<ID> Watlow.txt (for real step times)
Writes: <stem>_3He_COLDS_TubeReduced.csv   — cold-blank permeability data
        <stem>_3He_reduced.csv             — high-temperature diffusivity inversions
        (same pair for 4He)

Configuration: edit the CONTROL BOARD section below.
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (swets_K, Jones, tube_permeate2, Ratoms,
                              pull_number, extract_timesMC, MCHeReducer,
                              InvertFrequencyFactor, KenColdInversion)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)

# ---------------------------------------------------------------------------
# CONTROL BOARD
# ---------------------------------------------------------------------------
DIFFCELL_name = '112123SalAspIrr.csv'
STD_name      = 'STD_nov.csv'
total_3He     = 51.77 * 0.8     # pccSTP — set to 0 to auto-sum
total_4He     = 13.47 * 0.8     # nccSTP — set to 0 to auto-sum
OD            = 967 / 1E4       # cm — outer diameter
ID            = 533 / 1E4       # cm — inner diameter
perm_model    = 'modeled'       # 'modeled' or 'measured'
Tcutoff       = [30+273, 65+273, 225+273]  # [room, warm, hot] in Kelvin
# ---------------------------------------------------------------------------

G = 2 / (np.log(OD / ID) * (ID / 2) ** 2)


def get_real_time(ID_str):
    """Return the last recorded Watlow time (seconds) minus 25 for a given DC ID."""
    path = os.path.join('NGL Watlow Heat Log', f'DC{ID_str} Watlow.txt')
    with open(path) as f:
        return float(f.readlines()[-1].split('\t')[0]) - 25


reducer = MCHeReducer(STD_name)
DIFFCELL = pd.read_csv(DIFFCELL_name, header=None).to_numpy()

# Filter out bad rows (zero signals)
metadata  = DIFFCELL[:, 1]
TempK_all = np.array([273 + pull_number(str(d).split(' ')[2]) for d in metadata])
DIFFCELL  = DIFFCELL[(TempK_all > 273 + 70) *
                     ((TempK_all > 370 + 273) + (TempK_all < 220 + 273)), :]
DIFFCELL  = DIFFCELL[(DIFFCELL[:, 4].astype(float) > 0) *
                     (DIFFCELL[:, 6].astype(float) > 0), :]

He3, He4 = reducer.reduce(DIFFCELL)

metadata          = DIFFCELL[:, 1]
TimeSeconds       = np.array([60 * pull_number((str(d).split(' ')[1]).split('_')[1])
                               for d in metadata])
TempKelvin        = np.array([273 + pull_number(str(d).split(' ')[2]) for d in metadata])
coldtimes         = np.array([0] + list(extract_timesMC(DIFFCELL[:, 2])))
recordedTimeSeconds = np.array([
    get_real_time((str(d).split(' ')[1]).split('_')[0]) for d in metadata])

He_signals  = [He3, He4]
total_yields = [total_3He, total_4He]
data_holder_MC = {}

for j, (He, total_yield) in enumerate(zip(He_signals, total_yields)):
    name = ['3He', '4He'][j]
    HenCC = He.copy()
    HenCC[HenCC < 0] = 0
    if total_yield == 0:
        total_yield = np.sum(HenCC)

    n0_modeled, n1_modeled = [], []
    n0_measured, n1_measured = [], []
    Smeas, colds, Smeascolds, M = [], [], [], []
    fcum, Fp, D_a2, lnD_a2 = [], 0.0, [], []
    n1_n0_mod, n1_n0_mes = [], []
    Rel_times = []
    prev_cold = prev_inter = 0
    cold_counter = total_colds = -1
    Names = DIFFCELL[:, 0].copy()

    for i, datum in enumerate(metadata):
        if TempKelvin[i] < Tcutoff[2]:
            colds.append(i)
            cold_counter += 1
            total_colds += 1

            if TempKelvin[i] > Tcutoff[1]:
                n1_n0_mod_i = tube_permeate2(
                    T=TempKelvin[i], t=TimeSeconds[i], ID=ID, OD=OD,
                    He=name)
            elif TempKelvin[i] < Tcutoff[0] and prev_cold > 0:
                n1_n0_mod_i = tube_permeate2(
                    T=TempKelvin[i], t=coldtimes[i], ID=ID, OD=OD, He=name)
            else:
                n1_n0_mod_i = 0
                print(f'COLD {i} FELL THROUGH')

            n1_n0_mod.append(n1_n0_mod_i)
            if n1_n0_mod_i:
                n0_modeled.append(HenCC[i] / (1 - n1_n0_mod_i))
                n1_modeled.append(HenCC[i] / (1 / n1_n0_mod_i - 1))
            else:
                n0_modeled.append(0)
                n1_modeled.append(0)

            if prev_cold >= 2 and TempKelvin[i] < Tcutoff[0]:
                Smeascolds.append(cold_counter)
                Smeas.append(i)
                Rel_times.append(coldtimes[i])
                r = (HenCC[i] / coldtimes[i]) / (HenCC[i-1] / coldtimes[i-1])
                m = (1 - r) / np.mean([coldtimes[i], coldtimes[i-1]])
                n0_measured.append(HenCC[i] / (m * coldtimes[i]))
                n1_measured.append(HenCC[i] / (1 / (1 - m * coldtimes[i]) - 1))
                n1_n0_mes.append(r)
                M.append(m)
            elif (prev_inter >= 1 and TempKelvin[i] > Tcutoff[1]
                  and abs(TempKelvin[i] - TempKelvin[i-1]) < 2):
                Smeascolds.append(cold_counter)
                Smeas.append(i)
                Rel_times.append(TimeSeconds[i])
                r = (HenCC[i] / TimeSeconds[i]) / (HenCC[i-1] / TimeSeconds[i-1])
                m = (1 - r) / np.mean([TimeSeconds[i], TimeSeconds[i-1]])
                n0_measured.append(HenCC[i] / (m * TimeSeconds[i]))
                n1_measured.append(HenCC[i] / (1 / (1 - m * TimeSeconds[i]) - 1))
                n1_n0_mes.append(r)
                M.append(m)

            prev_cold   = prev_cold + 1 if TempKelvin[i] < Tcutoff[0] + 40 else 0
            prev_inter  = 0 if TempKelvin[i] < Tcutoff[0] + 40 else prev_inter + 1
            if TempKelvin[i] >= Tcutoff[0] + 40:
                prev_cold = 0
            Names[i] = f'{total_colds} in sequence {metadata[i]}'
        else:
            prev_cold = prev_inter = 0
            total_colds = 0

    n0_modeled = np.array(n0_modeled)
    n1_modeled = np.array(n1_modeled)
    n0_measured = np.array(n0_measured)
    n1_measured = np.array(n1_measured)
    n1_measured_out = np.zeros_like(n0_modeled)
    n0_measured_out = np.zeros_like(n0_modeled)
    n1_n0_mes_out   = np.zeros_like(n0_modeled)
    n1_measured_out[Smeascolds] = n1_measured
    n0_measured_out[Smeascolds] = n0_measured
    n1_n0_mes_out[Smeascolds]   = np.array(n1_n0_mes)

    Smeas_arr = np.array(Smeas)
    lambdas = (-np.log(n1_measured / n0_measured)
               / (TempKelvin[Smeas_arr] * np.array(Rel_times) * Ratoms))
    K_meas = lambdas * np.log(OD / ID) * (ID / 2) ** 2 / 2
    K_ref  = np.array([swets_K(T) for T in TempKelvin[Smeas_arr]])
    DK_swets = np.log(K_meas) - np.log(K_ref)
    lnlambdas = np.log(lambdas)

    lambdas_out   = np.zeros_like(n0_modeled)
    lnlambdas_out = np.zeros_like(n0_modeled)
    K_meas_out    = np.zeros_like(n0_modeled)
    DK_swets_out  = np.zeros_like(n0_modeled)
    lambdas_out[Smeascolds]   = lambdas
    lnlambdas_out[Smeascolds] = lnlambdas
    K_meas_out[Smeascolds]    = K_meas
    DK_swets_out[Smeascolds]  = DK_swets

    # Save cold-blank reduction
    colds_arr = np.array(colds)
    cold_df = pd.DataFrame({
        'Names':                     Names[colds_arr],
        'Temp (C)':                  TempKelvin[colds_arr] - 273,
        'Nominal/Hot Time (sec)':    TimeSeconds[colds_arr],
        'Total/Cold Time (sec)':     coldtimes[colds_arr],
        'Watlow Times (sec)':        recordedTimeSeconds[colds_arr],
        'lambda':                    lambdas_out,
        'n1/n0 modeled':             n1_n0_mod,
        'n1/n0 measured':            n1_n0_mes_out,
        'n0_modeled':                n0_modeled,
        'n0_measured':               n0_measured_out,
        'n1_modeled':                n1_modeled,
        'n1_measured':               n1_measured_out,
        'He Measured (nCC@STP)':     HenCC[colds_arr],
        'K measured':                K_meas_out,
        'Delta K':                   DK_swets_out,
        '10^4/T (K)':                1E4 / TempKelvin[colds_arr],
        'ln(lambda)':                lnlambdas_out,
    })
    cold_name = DIFFCELL_name[:-4] + f'_{name}_COLDS_TubeReduced.csv'
    cold_df.to_csv(cold_name)
    print(f"Saved cold data: {cold_name}")

    # High-temperature steps: reverse traversal to collect n0/n1 pairs
    HTind = []
    prev_cold_ht = 0
    n0_ht, n1_ht = [], []
    for i, measured in reversed(list(enumerate(HenCC))):
        if TempKelvin[i] < Tcutoff[2]:
            if prev_cold_ht == 0:
                n1_ht.append(n0_modeled[np.array(colds) == i][0])
                n0_ht.append(n1_modeled[np.array(colds) == i][0])
            else:
                n1_ht[-1] += measured
            prev_cold_ht += 1
        else:
            prev_cold_ht = 0
            HTind.append(i)

    HTind.reverse()
    n0_ht.reverse()
    n1_ht.reverse()
    n0_ht = np.array(n0_ht)[:-1]
    n1_ht = np.array(n1_ht)[1:]
    HTind = np.array(HTind)

    # Analytical hot-correction fallback where consecutive colds weren't measured
    corrtype = ['Cold Correction'] * len(HTind)
    for k, ind in enumerate(HTind):
        if n1_ht[k] < 0:
            corrtype[k] = 'Hot Correction'
            meas = HenCC[ind]
            Tk   = TempKelvin[ind]
            ts   = TimeSeconds[ind]
            Beta = ts * Tk * Ratoms * G * swets_K(Tk)
            if name == '3He':
                Beta *= Jones(Tk)
            hot = (((meas - n0_ht[k]) / Beta) * (1 - np.exp(-Beta))
                   + n0_ht[k] * np.exp(-Beta)) / (1 - (1 / Beta) * (1 - np.exp(-Beta)))
            n1_ht[k] = hot
            if k < len(HTind) - 1:
                n0_ht[k + 1] = hot

    HT_corr = HenCC[HTind] + n1_ht - n0_ht
    HT_corr[HT_corr < 0] = 0

    Fp = 0.0
    D_a2, lnD_a2, fcum = [], [], []
    for k, h in enumerate(HTind):
        F = Fp + HT_corr[k] / total_yield
        ff = InvertFrequencyFactor(t=TimeSeconds[h], F=F, Fp=Fp)
        D_a2.append(ff)
        lnD_a2.append(np.log(ff) if ff > 0 else np.nan)
        fcum.append(F)
        Fp = F

    hot_df = pd.DataFrame({
        'Names':          DIFFCELL[HTind, 1],
        'Temp (C)':       TempKelvin[HTind] - 273,
        'Time (min)':     TimeSeconds[HTind] / 60,
        'Watlow (min)':   recordedTimeSeconds[HTind] / 60,
        f'{name} measured': HenCC[HTind],
        f'Corrected {name}': HT_corr,
        'Fcum':           fcum,
        'D/a^2':          D_a2,
        '10^4/T':         1E4 / TempKelvin[HTind],
        'ln(D/a^2)':      lnD_a2,
        'n0':             n0_ht,
        'n1':             n1_ht,
        'Correction Type': corrtype,
    })
    hot_name = DIFFCELL_name[:-4] + f'_{name}_reduced.csv'
    hot_df.to_csv(hot_name)
    data_holder_MC[name] = hot_df
    print(f"Saved hot data:  {hot_name}")

    # Quick Arrhenius preview plot
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twiny()
    Ctemps = np.linspace(200, 700, 11, dtype=int)
    valid = ~np.array([np.isinf(v) or np.isnan(v) for v in lnD_a2])
    ax1.plot(1E4 / TempKelvin[HTind][valid], np.array(lnD_a2)[valid], linestyle='--')
    ax1.scatter(1E4 / TempKelvin[HTind][valid], np.array(lnD_a2)[valid])
    ax2.set_xticks(1E4 / (Ctemps + 273))
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticklabels(Ctemps)
    ax2.set_xlabel('Temperature (°C)')
    ax1.set_xlabel(r'$10^4/T$ (K)')
    ax1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
    plt.title(f'Diffusivity Inversion — {name}\nTotal yield = {total_yield:.1f}')
    plt.tight_layout()
    plt.savefig(hot_name.replace('.csv', '.pdf'), dpi=300)
    plt.close(fig)
