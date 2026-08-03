"""
Quadrupole Mass Spectrometer Data Reduction.
Run from Chapter1/Figures/ (the directory with QUAD CSV and ICPMS output).

Reads:  <QUAD_name>.csv  (Pfeiffer QMS 200 batch output)
        <ICPMS_name>_reducedICPMS.csv  (from reduce_icpms.py)
Writes: <QUAD_name>_reducedQUAD.csv

Configuration: edit the CONTROL BOARD section below.
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (He_Age, recoil_correct, MDD_diffusive_loss_correct,
                              outlier_stats)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)

# ---------------------------------------------------------------------------
# CONTROL BOARD
# ---------------------------------------------------------------------------
QUAD_name  = ''              # e.g. 'Batch41_quad.csv'
ICPMS_name = '2023_02_10_BJT_ratios_dilute_apatite_reducedICPMS.csv'

Pt_blanks = False            # Use Pt-tube blanks as procedural blanks
do_alpha_eject_corr = False
do_diffusive_loss_corrections = True
goethite_diffusive_corrections = {'FvLRD': 0.05, 'HRD_deficit': 0.08}
alpha_stopping_dist_file = 'alpha_stopping_distances.csv'
# ---------------------------------------------------------------------------

if not QUAD_name:
    raise SystemExit("Set QUAD_name in the control board before running.")

QUAD  = pd.read_csv(QUAD_name, na_values=[''])
outdf = pd.read_csv(ICPMS_name, index_col=0) if os.path.exists(ICPMS_name) \
        else pd.DataFrame([])

CITref      = QUAD['\tCIT RefNo'].tolist()
quadAnalyses = QUAD['Name'].tolist()
quadType    = QUAD['\tAnalysis'].tolist()
HenCC       = QUAD['\tCalc nCC'].to_numpy()
HeSigma     = HenCC * 0.03

try:
    radii = QUAD['r'].to_numpy()
    has_radii = True
except KeyError:
    has_radii = False
    do_alpha_eject_corr = False

laser_blanks, line_blanks, Qprocedural_blanks, Qstandards, Qsamples = [], [], [], [], []
for i, qtype in enumerate(quadType):
    if 'LB' in qtype:
        if 'Laser' in qtype:
            laser_blanks.append(i)
        else:
            line_blanks.append(i)
    elif 'STD' in qtype:
        Qstandards.append(i)
    elif 'blank' in quadAnalyses[i].lower():
        Qprocedural_blanks.append(i)
    else:
        Qsamples.append(i)

laser_blanks = np.array(laser_blanks)
line_blanks  = np.array(line_blanks)
Qstandards   = np.array(Qstandards)
Qsamples     = np.array(Qsamples)
Qprocedural_blanks = np.array(Qprocedural_blanks)

LB, LBs = (outlier_stats(HenCC[line_blanks])[:2] if len(line_blanks) > 1
            else (HenCC[line_blanks][0], HeSigma[line_blanks][0]))

if Pt_blanks:
    LLB, LLBs = (outlier_stats(HenCC[Qprocedural_blanks])[:2]
                 if len(Qprocedural_blanks) > 1
                 else (HenCC[Qprocedural_blanks][0], HeSigma[Qprocedural_blanks][0]))
else:
    LLB, LLBs = (outlier_stats(HenCC[laser_blanks])[:2] if len(laser_blanks) > 1
                 else (HenCC[laser_blanks][0], HeSigma[laser_blanks][0]))

n_extra_cols = 4 if do_diffusive_loss_corrections or do_alpha_eject_corr else 0
newHE = np.zeros((len(quadAnalyses), 10 + n_extra_cols
                  + (6 if do_alpha_eject_corr else 0)))

ref = 'zzz'
for i, name in enumerate(quadAnalyses):
    if i in Qstandards:
        newHE[i, :2] = [HenCC[i] - LB, HeSigma[i] + LBs * 2]
    elif i in Qsamples:
        is_re = 're' in name.lower()
        if is_re:
            newHE[i, :2] = [newHE[i-1, 0] + HenCC[i] - LLB,
                            newHE[i-1, 1] + HeSigma[i] + LLBs * 2]
        else:
            newHE[i, :2] = [HenCC[i] - LLB, HeSigma[i] + LLBs * 2]
            ref = CITref[i]
        matched = np.array(outdf.iloc[np.where(outdf.index == ref)[0], :6])
        if matched.shape[0]:
            UThSm = matched[0] if matched.shape[0] == 1 else \
                np.array([matched[np.nanargmin(matched[:, j*2+1]), j*2:(j*2+2)].flatten()
                          for j in range(3)]).flatten()
            UThSm[np.isnan(UThSm)] = 0
            newHE[i, 2:8] = UThSm
            if np.sum(UThSm) != 0:
                newHE[i, 8:10] = He_Age(newHE[i, :8])

col_names = ['He (nccSTP)', 'He 2sigma', 'U (mol)', 'U 2s', 'Th (mol)', 'Th 2s',
             'Sm (mol)', 'Sm 2s', 'Age (yr)', 'Age 2s']

if do_alpha_eject_corr and has_radii:
    alpha_sd = pd.read_csv(alpha_stopping_dist_file, index_col=0)
    a_phase = 'apatite'  # adjust if needed
    for i, r in enumerate(radii):
        if not np.isnan(r):
            newHE[i, 10:16] = recoil_correct([r, r*0.2], newHE[i, :8], alpha_sd, a_phase)
    col_names += ['Ft', 'Ft 2s', 'He corr', 'He corr 2s', 'Age corr', 'Age corr 2s']

if do_diffusive_loss_corrections:
    for i in Qsamples:
        newHE[i, 10:14] = MDD_diffusive_loss_correct(
            goethite_diffusive_corrections, newHE[i, :8])
    col_names += ['He corr', 'He corr 2s', 'Age corr', 'Age corr 2s']

remove_rows = np.concatenate([line_blanks, Qprocedural_blanks, laser_blanks])
newHE = np.delete(newHE, remove_rows, axis=0)
Qindices = np.array(sorted(np.append(Qsamples, Qstandards)))

out_name = QUAD_name.replace('.csv', '_reducedQUAD.csv')
pd.DataFrame(newHE, columns=col_names,
             index=np.array(quadAnalyses)[Qindices]).to_csv(out_name)
print(f"Done! Output: {out_name}")
