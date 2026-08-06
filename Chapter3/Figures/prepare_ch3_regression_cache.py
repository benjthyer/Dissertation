"""
prepare_ch3_regression_cache.py -- fit the three linear Arrhenius regions
described in Chapter 3's Results (Sec. 3.2, "Sulfide Step Heat
Experiments") directly from Chapter3/Tables/plotable_sulfides_cache.pkl,
instead of hand-typing their slope/Ea/R^2/closure temperature into the
Results, Discussion, and Abstract text.

Why: those numbers had already started to drift -- the Abstract's "255 +/-
28 kJ/mol" for the Rustenburg pyrite fast-pathway activation energy does
not match the Results section's own "71.8 Kcal/mol" (300.6 kJ/mol) for
the same regression, and two blank \\hl{} placeholders in the Discussion
were never filled in with the numbers the surrounding prose describes.
\\input-ing generated macros (write_chapter3_macros.py) everywhere these
values are quoted means a data or methodology change only has to be
re-run through this pipeline, not hunted down and re-typed by hand.

Three named linear regions are fit, each identified by the literal step
numbers of the plotable-cache rows the Results text is describing. These
are not re-derived by an automatic threshold (unlike Chapter 2's
fractional-yield cutoff) because the geometry here is idiosyncratic per
sample -- a prograde run, a down-temperature retrograde cluster, and a
mixed retrograde/prograde tail -- so the selection is pinned explicitly
and was confirmed by brute-force search over contiguous step windows to
be the unique n-point window reproducing the manuscript's previously
hand-fit R^2/Ea for each sample (see fit windows below for the exact
match):

  LVCO (LVCOPy230630, steps 39-47): prograde array immediately following
    the step-38 peak of a retrograde-prograde cycle. n=9, matches the
    reported R^2=0.998, Ea=47.6 kcal/mol ("Results" Sec. 3.2).
  Rust (Rustenburg Pyrite, steps 90582-90586): five consecutive
    down-temperature retrograde measurements (500 -> 450 degC) right
    after the 495 degC peak at step 90581 -- "the down-temperature
    retrogrades of heating cycles" the Results text refers to. n=5,
    matches the reported R^2=0.998, Ea=71.8 kcal/mol.
  CCp (CCpTS230630, steps 31-39): the mixed down-then-up temperature
    tail following the step-27 (430 degC) peak. n=9, matches the
    reported R^2=0.9811, Ea=41.8 kcal/mol, and (via the Dodson closure
    temperature below) the reported Tc=128 degC.

For each region, fits are computed for all three "treatment as
uncertainty" bounds (M = central, LB, UB -- the LB_dln(d/a^2) /
UB_dln(d/a^2) columns already in the plotable cache), giving both a
regression statistical uncertainty (stderr on the M fit) and a
data-reduction-treatment range (spread across LB/UB), the same two
distinct uncertainty notions Chapter 2's stage1_regression_cache.json
distinguishes. Each bound's Dodson (1973) closure temperature is also
computed (sphere geometry, A=55; 10 degC/Myr cooling -- matching the
assumption already used for the Chapter 3 chalcopyrite Tc=128 degC
and Chapter 2's Stage 1 line).

Run this before write_chapter3_macros.py or any fig_ch3_*.py script.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import scipy.stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from thermochr_utils import (dodson_closure_temperature, dodson_closure_temperature_stderr,
                              dodson_closure_temperature_stderr_interceptonly)

CACHE_PKL = os.path.join(SCRIPT_DIR, '..', 'Tables', 'plotable_sulfides_cache.pkl')
OUT_DIR = os.path.join(SCRIPT_DIR, 'generated', 'data')
OUT_PATH = os.path.join(OUT_DIR, 'ch3_regression_cache.json')

DODSON_A = 55.0
COOLING_RATE_C_PER_MYR = 10.0
R_CAL = 1.987  # cal/(mol K)
CAL_TO_J = 4.184

# Named linear regions: {short_name: (sample, [step numbers])}. See module
# docstring for how these were identified.
LINEAR_REGIONS = {
    'LVCO': ('LVCOPy230630', [39, 40, 41, 42, 43, 44, 45, 46, 47]),
    'Rust': ('Rustenburg Pyrite', [90582, 90583, 90584, 90585, 90586]),
    'CCp':  ('CCpTS230630', [31, 32, 33, 34, 35, 36, 37, 38, 39]),
}

# Every plotable sample's delta-plot reference regression, per the Results
# text (Sec. 3.2): LVCO's line is shared by the other two Leadville pyrite
# grain-size experiments and (qualitatively) by arsenopyrite; CCp's line
# is shared by galena; LVCO and Rust each also serve as their own reference.
DELTA_REFERENCE = {
    'LVCOPy230630': 'LVCO',
    'BigLVCOPy230707': 'LVCO',
    '112123LVCOPyIrr': 'LVCO',
    'SalAspIrr': 'LVCO',
    'Rustenburg Pyrite': 'Rust',
    'CCpTS230630': 'CCp',
    'GalTS230630': 'CCp',
}


def _bound_y(sub, bound):
    y = sub['ln(d/a^2)'].to_numpy(dtype=float)
    if bound == 'M':
        return y
    lb = pd.to_numeric(sub['LB_dln(d/a^2)'], errors='coerce').to_numpy(dtype=float)
    ub = pd.to_numeric(sub['UB_dln(d/a^2)'], errors='coerce').to_numpy(dtype=float)
    return y - lb if bound == 'LB' else y + ub


def fit_named_region(df, sample, steps, bound):
    sub = df[df['sample'] == sample].set_index('step').loc[steps]
    x = sub['10000/TK'].to_numpy(dtype=float)
    y = _bound_y(sub, bound)
    fit = scipy.stats.linregress(x, y)

    Ea_cal_mol = -fit.slope * 10000.0 * R_CAL
    Ea_cal_mol_stderr = fit.stderr * 10000.0 * R_CAL
    D0_a2 = np.exp(fit.intercept)
    D0_a2_stderr = D0_a2 * fit.intercept_stderr

    out = dict(sample=sample, steps=steps, bound=bound,
               slope=float(fit.slope), intercept=float(fit.intercept),
               slope_stderr=float(fit.stderr), intercept_stderr=float(fit.intercept_stderr),
               r2=float(fit.rvalue ** 2), n_points=int(len(steps)),
               Ea_cal_mol=float(Ea_cal_mol), Ea_cal_mol_stderr=float(Ea_cal_mol_stderr),
               Ea_kJ_mol=float(Ea_cal_mol * CAL_TO_J / 1000.0),
               Ea_kJ_mol_stderr=float(Ea_cal_mol_stderr * CAL_TO_J / 1000.0),
               Ea_kcal_mol=float(Ea_cal_mol / 1000.0),
               Ea_kcal_mol_stderr=float(Ea_cal_mol_stderr / 1000.0),
               D0_a2=float(D0_a2), D0_a2_stderr=float(D0_a2_stderr))

    out['Tc_C'] = dodson_closure_temperature(Ea_cal_mol, D0_a2, COOLING_RATE_C_PER_MYR, A=DODSON_A)
    out['Tc_C_stderr'] = dodson_closure_temperature_stderr(
        Ea_cal_mol, D0_a2, Ea_cal_mol_stderr, D0_a2_stderr, COOLING_RATE_C_PER_MYR, A=DODSON_A)
    out['Tc_C_stderr_interceptonly'] = dodson_closure_temperature_stderr_interceptonly(
        Ea_cal_mol, D0_a2, D0_a2_stderr, COOLING_RATE_C_PER_MYR, A=DODSON_A)
    return out


def main():
    if not os.path.exists(CACHE_PKL):
        raise FileNotFoundError(f"{CACHE_PKL} not found -- run Chapter3/Tables/build_plotable_cache.py first.")
    df = pd.read_pickle(CACHE_PKL)

    os.makedirs(OUT_DIR, exist_ok=True)
    cache = {'dodson_A': DODSON_A, 'cooling_rate_C_per_Myr': COOLING_RATE_C_PER_MYR,
             'delta_reference': DELTA_REFERENCE}

    for name, (sample, steps) in LINEAR_REGIONS.items():
        cache[name] = {'sample': sample, 'steps': steps}
        for bound in ('M', 'LB', 'UB'):
            fit = fit_named_region(df, sample, steps, bound)
            cache[name][bound] = fit
        m = cache[name]['M']
        lb, ub = cache[name]['LB'], cache[name]['UB']
        print(f"{name} ({sample}, n={m['n_points']}): "
              f"Ea={m['Ea_kcal_mol']:.1f}+/-{m['Ea_kcal_mol_stderr']:.1f} kcal/mol "
              f"({m['Ea_kJ_mol']:.1f}+/-{m['Ea_kJ_mol_stderr']:.1f} kJ/mol; "
              f"treatment range {lb['Ea_kJ_mol']:.1f}-{ub['Ea_kJ_mol']:.1f} kJ/mol)  "
              f"R2={m['r2']:.4f}  Tc={m['Tc_C']:.1f}+/-{m['Tc_C_stderr_interceptonly']:.1f} degC")

    with open(OUT_PATH, 'w') as f:
        json.dump(cache, f, indent=2)
    print(f"\nWrote {OUT_PATH}")


if __name__ == '__main__':
    main()
