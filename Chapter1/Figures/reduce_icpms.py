"""
ICPMS Data Reduction Pipeline.
Run from Chapter1/Figures/ (the directory containing ICPMS CSV and this script).

Reads:  <ICPMS_name>.csv   (Agilent 8800 ratio-mode output)
Writes: <ICPMS_name>_reducedICPMS.csv

Configuration: edit the CONTROL BOARD section below.
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from molmass import Formula
import pandas as pd
import scipy.interpolate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (outlier_stats, isotope_dilution, Nonfunc,
                              pull_number, mass_multiplier, He_Age,
                              recoil_correct, MDD_diffusive_loss_correct)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)

# ---------------------------------------------------------------------------
# CONTROL BOARD — edit here
# ---------------------------------------------------------------------------
ICPMS_name = '2023_02_10_BJT_ratios_dilute_apatite.csv'
calc_ppm = False
phase = 'FeS2'
phase_mass_tracer = 'Fe'

Nnormal = {   # mass in grams delivered in 1 mL of the normal solution
    'Fe': 1E-4, 'Cu': 1E-6, 'As': 1E-6, 'Zr': 1E-7,
    'Ag': 1E-7, 'Sb': 1E-7, 'U': 1E-8, 'Th': 1E-8, 'Sm': 1E-9,
}
normal_rejects = []
acid_blank_rejects = []
spike_blank_rejects = [1]
procedural_blanks_rejects = []
do_not_spline = ['U', 'Th', 'Sm', 'Fe', 'Sb', 'As', 'Ag', 'Cu', 'Zr']

do_alpha_eject_corr = False
do_diffusive_loss_corrections = True
goethite_diffusive_corrections = {'FvLRD': 0.05, 'HRD_deficit': 0.08}
alpha_stopping_dist_file = 'alpha_stopping_distances.csv'
Pt_blanks = False
# ---------------------------------------------------------------------------

# Convert normal solution masses to moles
for key in list(Nnormal.keys()):
    Nnormal[key] /= Formula(key).mass

phase_mass_multiplier = mass_multiplier(Formula(phase), phase_mass_tracer)

ICPMS = pd.read_csv(ICPMS_name)
name_col = ICPMS.columns[ICPMS.iloc[0, :].isin(['Sample Name'])][0]
dat_col  = ICPMS.columns[ICPMS.iloc[0, :].isin(['Acq. Date-Time'])][0]
analyses = ICPMS[name_col][1:].to_numpy()
dates    = ICPMS[dat_col][1:].to_numpy().tolist()
times    = [datetime.strptime(ts, '%m/%d/%Y %I:%M:%S %p') for ts in dates]
time0    = times[0]
minutes  = np.array([(t - time0).total_seconds() / 60 for t in times])

element, replicates = [], 0
for i, col in enumerate(ICPMS.columns):
    if 'Replicate' in col:
        element.append(str(col.split(' [')[0]).strip())
    if 'Rep' in str(ICPMS.iat[0, i]):
        r = int(ICPMS.iat[0, i].split(' Rep')[1])
        replicates = max(replicates, r)

data = np.zeros((len(analyses), len(element), replicates))
for i, col in enumerate(ICPMS.columns):
    if 'Replicate' in col:
        el_t = str(col.split(' [')[0]).strip()
        c = np.where(np.array(element) == el_t)[0][0]
    if 'Rep' in str(ICPMS.iat[0, i]):
        r = int(ICPMS.iat[0, i].split('Rep')[1])
        data[:, c, r - 1] = ICPMS[col][1:]

spike_blanks, procedural_blanks, acid_blanks, normals, samples = [], [], [], [], []
for i, name in enumerate(analyses):
    nm = name.lower()
    if 'blank' in nm or 'SB' in name or '.p' in nm or 'AB' in name:
        if 's-' in nm or 'spike' in nm or 'SB' in name:
            spike_blanks.append(i)
        elif 'p-' in nm or 'pr' in nm or '.p' in nm:
            procedural_blanks.append(i)
        else:
            acid_blanks.append(i)
    elif 'normal' in nm or 'n-' in nm or 'N' in name:
        normals.append(i)
    else:
        samples.append(i)

spike_blanks = np.array(spike_blanks)
procedural_blanks = np.array(procedural_blanks)
acid_blanks  = np.array(acid_blanks)
normals      = np.array(normals)
samples      = np.array(samples)

isotope  = {el.replace(' ', ''): i for i, el in enumerate(element)}
analysis = {an: i for i, an in enumerate(analyses)}

# --- Spike isotope ratios ---
spike_blanks_r = [s for i, s in enumerate(spike_blanks) if i not in spike_blank_rejects]
RThspike, sRThspike, _ = outlier_stats(data[spike_blanks_r, isotope['232/230Th'], :])
RUspike,  sRUspike,  _ = outlier_stats(data[spike_blanks_r, isotope['238/235U'],  :])
RUnat = Formula('U').spectrum()[238][1] / Formula('U').spectrum()[235][1]

# --- Normal solution standardization ---
normals_r = normals[[i for i, _ in enumerate(normals) if i not in normal_rejects]]
plot_minutes = np.linspace(0, np.max(minutes), 100)
spike_U, spike_Us, spike_Th, spike_Ths = [], [], [], []

for nor in normals_r:
    Rab, Rsab, _ = outlier_stats(data[nor, isotope['238/235U'], :])
    NU_arr = isotope_dilution(Nb=Nnormal['U'],
                              Ra=np.random.normal(RUspike, sRUspike, 2000),
                              Rab=np.random.normal(Rab, Rsab, 2000), Rb=RUnat)
    Nu, Nus, _ = outlier_stats(NU_arr)
    spike_U.append(Nu); spike_Us.append(Nus)

    Rab, Rsab, _ = outlier_stats(data[nor, isotope['232/230Th'], :])
    NTH_arr = isotope_dilution(Nb=Nnormal['Th'],
                               Ra=np.random.normal(RThspike, sRThspike, 2000),
                               Rab=np.random.normal(Rab, Rsab, 2000), Rb=np.inf)
    NTh, NThs, _ = outlier_stats(NTH_arr)
    spike_Th.append(NTh); spike_Ths.append(NThs)

if 'U' in do_not_spline:
    mu, sig, _ = outlier_stats(np.array(spike_U))
    NU_spike  = Nonfunc(mu); NUs_spike = Nonfunc(sig)
else:
    NU_spike  = scipy.interpolate.UnivariateSpline(minutes[normals_r], spike_U, k=2)
    NUs_spike = scipy.interpolate.UnivariateSpline(minutes[normals_r], spike_Us, k=2)

if 'Th' in do_not_spline:
    mu, sig, _ = outlier_stats(np.array(spike_Th))
    NTh_spike  = Nonfunc(mu); NThs_spike = Nonfunc(sig)
else:
    NTh_spike  = scipy.interpolate.UnivariateSpline(minutes[normals_r], spike_Th, k=2)
    NThs_spike = scipy.interpolate.UnivariateSpline(minutes[normals_r], spike_Ths, k=2)

KR = {}
for key in list(Nnormal.keys()):
    if key not in ['U', 'Th']:
        el = [i for i, e in enumerate(isotope) if key in e]
        if len(el) == 1:
            Kl, Ksl = [], []
            for nor in normals_r:
                K, Ks, _ = outlier_stats(Nnormal[key] / data[nor, el, :])
                Kl.append(K); Ksl.append(Ks)
            if key in do_not_spline:
                mu, sig, _ = outlier_stats(np.array(Kl))
                KE = Nonfunc(mu); KErr = Nonfunc(sig)
            else:
                KE   = scipy.interpolate.UnivariateSpline(minutes[normals_r], Kl, k=2)
                KErr = scipy.interpolate.UnivariateSpline(minutes[normals_r], Ksl, k=2)
            KR[key] = [KE, KErr]

# --- Procedural blanks ---
proc_r = [p for i, p in enumerate(procedural_blanks)
          if i not in procedural_blanks_rejects]
if not proc_r:
    Nblanks  = np.zeros(len(KR) + 2)
    Nsblanks = np.zeros(len(KR) + 2)
else:
    proc_r = np.array(proc_r)
    NU, NUs, NTh, NThs = [], [], [], []
    for pbr in proc_r:
        Rab, Rabs, _ = outlier_stats(data[pbr, isotope['238/235U'], :])
        NUi, NUsi, _ = outlier_stats(isotope_dilution(
            Rab=np.random.normal(Rab, Rabs, 2000),
            Nb=np.random.normal(NU_spike(minutes[pbr]), NUs_spike(minutes[pbr]), 2000),
            Ra=RUnat, Rb=np.random.normal(RUspike, sRUspike, 2000)))
        NU.append(NUi); NUs.append(NUsi)
        Rab, Rabs, _ = outlier_stats(data[pbr, isotope['232/230Th'], :])
        NThi, NThsi, _ = outlier_stats(isotope_dilution(
            Rab=np.random.normal(Rab, Rabs, 2000),
            Nb=np.random.normal(NTh_spike(minutes[pbr]), NThs_spike(minutes[pbr]), 2000),
            Ra=np.inf, Rb=np.random.normal(RThspike, sRThspike, 2000)))
        NTh.append(NThi); NThs.append(NThsi)
    NUI, NUIs, _ = outlier_stats(np.array(NU))
    NThI, NThIs, _ = outlier_stats(np.array(NTh))
    Nblanks  = [max(NUI, 0), max(NThI, 0)]
    Nsblanks = [NUIs, NThIs]
    for key in KR:
        el = [i for i, e in enumerate(isotope) if key in e]
        Nel, Nsel = [], []
        for pcr in proc_r:
            Rab, Rabs, _ = outlier_stats(data[pcr, el, :])
            Neli, Nseli, _ = outlier_stats(
                np.random.normal(KR[key][0](minutes[pcr]), KR[key][1](minutes[pcr]), 2000)
                * np.random.normal(Rab, Rabs, 2000))
            Nel.append(Neli); Nsel.append(Nseli)
        NELI, NELIs, _ = outlier_stats(Nel)
        Nblanks.append(max(NELI, 0))
        Nsblanks.append(NELIs)
    Nblanks  = np.array(Nblanks)
    Nsblanks = np.array(Nsblanks)

# --- Final sample calculations ---
outelements = ['U', 'Th'] + list(KR.keys())
outarray = np.zeros((len(samples) + len(proc_r if hasattr(proc_r, '__len__') else []),
                     len(outelements) * 2))

for i, sam in enumerate(samples):
    Rab, Rabs, _ = outlier_stats(data[sam, isotope['238/235U'], :])
    NUi, NUsi, _ = outlier_stats(isotope_dilution(
        Rab=np.random.normal(Rab, Rabs, 2000),
        Nb=np.random.normal(NU_spike(minutes[sam]), NUs_spike(minutes[sam]), 2000),
        Ra=RUnat, Rb=np.random.normal(RUspike, sRUspike, 2000)))
    outarray[i, 0] = NUi  - Nblanks[0]
    outarray[i, 1] = (NUsi + Nsblanks[0]) * 2
    Rab, Rabs, _ = outlier_stats(data[sam, isotope['232/230Th'], :])
    NThi, NThsi, _ = outlier_stats(isotope_dilution(
        Rab=np.random.normal(Rab, Rabs, 2000),
        Nb=np.random.normal(NTh_spike(minutes[sam]), NThs_spike(minutes[sam]), 2000),
        Ra=np.inf, Rb=np.random.normal(RThspike, sRThspike, 2000)))
    outarray[i, 2] = NThi - Nblanks[1]
    outarray[i, 3] = (NThsi + Nsblanks[1]) * 2
    for ei, key in enumerate(KR):
        el = [j for j, e in enumerate(isotope) if key in e]
        Rab, Rabs, _ = outlier_stats(data[sam, el, :])
        Neli, Nseli, _ = outlier_stats(
            np.random.normal(KR[key][0](minutes[sam]), KR[key][1](minutes[sam]), 2000)
            * np.random.normal(Rab, Rabs, 2000))
        outarray[i, 4 + ei * 2] = Neli - Nblanks[2 + ei]
        outarray[i, 5 + ei * 2] = (Nseli + Nsblanks[2 + ei]) * 2

# Build output DataFrame
UThSm_ind = next(i for i, e in enumerate(outelements) if 'Sm' in e)
UThSm_block = np.copy(np.append(
    outarray[:len(samples), :4],
    outarray[:len(samples), UThSm_ind * 2:UThSm_ind * 2 + 2], axis=1))

row_names = analyses[samples].tolist()
column_names = ['U (moles)', 'U 2s', 'Th (moles)', 'Th 2s', 'Sm (moles)', 'Sm 2s']
for outel in outelements:
    column_names += [f'{outel} ({"ppm" if calc_ppm else "moles"})',
                     f'{outel} 2s']

outdf = pd.DataFrame(
    np.append(UThSm_block, outarray[:len(samples)], axis=1),
    columns=column_names, index=row_names)

new_name = ICPMS_name.replace('.csv', '_reducedICPMS.csv')
outdf.to_csv(new_name)
print(f"Done! Output: {new_name}")
