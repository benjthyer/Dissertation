"""
prepare_regression_cache.py — derive and cache the "Stage 1" Arrhenius
reference line for Win-06-01b-HT (3He) from the master workbook, instead
of hardcoding its slope/intercept in every downstream figure script.

Previously, fig_delta_plot.py, the zoomed panel of
fig_decomp_vs_hydrothermal.py, and fig_partial_retention_plots.py each
separately hardcoded the same regression result (Ea ~= 38033 cal/mol,
ln(D0/a^2) ~= 16.685), copied by hand from a one-off fit done in Excel.
That's fragile: if the underlying step-heat reduction changes (as it
just did, fixing the upper/lower-bound permeation-lag treatment), those
three hardcoded copies silently go stale and can disagree with each
other and with the data.

This script re-derives the same regression directly from the workbook
every time it's run, for all three "treatment as uncertainty" bounds
(central/M, upper/UB, lower/LB), computes each bound's Dodson (1973)
closure temperature and its 1-sigma standard error propagated from the
regression's own slope/intercept uncertainty (see
thermochr_utils.dodson_closure_temperature[_stderr]), and writes the
result to generated/data/stage1_regression_cache.json. Downstream fig_*.py scripts
read that cache via thermochr_utils.load_stage1_cache() rather than
hardcoding numbers.

It also fits the same Stage 1 reference line to the na\"ive/informed
bracketing (permeation-step) method's own 3He diffusivities -- the
direct-measurement check on the bounding method's M/UB/LB regression
above -- via load_diffusivities_HTWin0601b_naive(), caching the result
under the 'naive' key (no LB/UB split: the permeation-step method
propagates its own single 2-sigma per point rather than an explicit
bound pair). Used by fig_naive_stage1_arrhenius.py and referenced in
\\S\\ref{sec:discussion-bounding-direct} (manuscript) /
Chapter 2's complete-degas discussion.

Note Tc_C_stderr (regression statistical uncertainty, propagated) and
the bound-to-bound spread of Tc_C across M/LB/UB (different
data-reduction treatments) are two different notions of "uncertainty"
on the closure temperature -- don't add them in quadrature.

Two different Tc stderr conventions are cached side by side:
  - Tc_C_stderr: full joint propagation from both the slope (Ea) and
    intercept (D0/a2) uncertainties (dodson_closure_temperature_stderr).
  - Tc_C_stderr_interceptonly: intercept (D0/a2) uncertainty only, Ea
    held fixed at its central value (dodson_closure_temperature_stderr_interceptonly).
The manuscript text reports the intercept-only convention ("considering
only uncertainty in the regression intercept (D0/a2) term"), matching
the historical by-hand calculation in the master workbook; the joint
value is kept in the cache for transparency/comparison.

The historical fit used "the last 11 steps" of the experiment. Row
counts aren't reproducible if the dataset gains or loses rows, so this
selects steps the same way but by a fractional-yield threshold instead
(cumulative 3He fractional yield >= FRACTIONAL_YIELD_THRESHOLD), which
happens to select 11-12 steps for the current data and will keep
selecting "the high-yield plateau" if the dataset changes.

Run this before any fig_*.py script that plots a Stage 1 reference line
or partial-retention curve. run_all_figures.py runs it automatically,
first, ahead of every fig_*.py script.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import (load_diffusivities_HTWin0601b_bounds, load_diffusivities_HTWin0601b_naive,
                              fit_reference_line, dodson_closure_temperature, dodson_closure_temperature_stderr,
                              dodson_closure_temperature_stderr_interceptonly)

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
CACHE_DIR = os.path.join(FIG_DIR, 'generated', 'data')
CACHE_PATH = os.path.join(CACHE_DIR, 'stage1_regression_cache.json')

FRACTIONAL_YIELD_THRESHOLD = 0.07  # matches the historical "~7% cumulative 3He yield" plateau cutoff

# Closure-temperature assumptions, matching the master workbook's
# diffusivitiesHTWin0601bM sheet (cells Z26:AD35): a spherical diffusion
# domain (Dodson 1973 geometry factor A=55) cooling at 10 degC/Myr.
DODSON_A = 55.0
COOLING_RATE_C_PER_MYR = 10.0

if __name__ == '__main__':
    os.makedirs(CACHE_DIR, exist_ok=True)
    bounds = load_diffusivities_HTWin0601b_bounds(MASTER_XLSX)

    cache = {'fractional_yield_threshold': FRACTIONAL_YIELD_THRESHOLD, 'isotope': '3He',
              'dodson_A': DODSON_A, 'cooling_rate_C_per_Myr': COOLING_RATE_C_PER_MYR}
    for tag in ('M', 'LB', 'UB'):
        df = bounds['3'][tag]
        fit = fit_reference_line(df['Temp (C)'], df['ln(d/a^2)'], df['Fi+1'],
                                  threshold=FRACTIONAL_YIELD_THRESHOLD)
        fit['Tc_C'] = dodson_closure_temperature(fit['Ea_cal_mol'], fit['D0_a2'],
                                                   COOLING_RATE_C_PER_MYR, A=DODSON_A)
        fit['Tc_C_stderr'] = dodson_closure_temperature_stderr(
            fit['Ea_cal_mol'], fit['D0_a2'], fit['Ea_cal_mol_stderr'], fit['D0_a2_stderr'],
            COOLING_RATE_C_PER_MYR, A=DODSON_A)
        fit['Tc_C_stderr_interceptonly'] = dodson_closure_temperature_stderr_interceptonly(
            fit['Ea_cal_mol'], fit['D0_a2'], fit['D0_a2_stderr'],
            COOLING_RATE_C_PER_MYR, A=DODSON_A)
        cache[tag] = fit
        print(f"Stage 1 reference ({tag}): slope={fit['slope']:.4f}+/-{fit['slope_stderr']:.4f}  "
              f"intercept={fit['intercept']:.4f}+/-{fit['intercept_stderr']:.4f}  "
              f"Ea={fit['Ea_kJ_mol']:.1f}+/-{fit['Ea_kJ_mol_stderr']:.1f} kJ/mol  "
              f"R2={fit['r2']:.4f}  n={fit['n_points']}  "
              f"Tc={fit['Tc_C']:.1f}+/-{fit['Tc_C_stderr']:.1f} degC (joint)  "
              f"+/-{fit['Tc_C_stderr_interceptonly']:.1f} degC (intercept-only)")

    print(f"\nClosure temperature: Tc = {cache['M']['Tc_C']:.1f} +/- {cache['M']['Tc_C_stderr_interceptonly']:.1f} degC "
          f"(intercept-only regression uncertainty, reported in manuscript text; "
          f"joint slope+intercept uncertainty is +/- {cache['M']['Tc_C_stderr']:.1f} degC), "
          f"range {cache['LB']['Tc_C']:.1f}-{cache['UB']['Tc_C']:.1f} degC "
          f"across LB/UB bounds (data-reduction-treatment uncertainty), "
          f"A={DODSON_A} (sphere), cooling rate={COOLING_RATE_C_PER_MYR} degC/Myr")

    # --- Na\"ive/informed bracketing (permeation-step) method: same Stage 1
    # fit, applied to the direct-measurement 3He diffusivities instead of
    # the bounding method's M/UB/LB reduction. ---
    naive = load_diffusivities_HTWin0601b_naive(MASTER_XLSX)['3']
    naive_fit = fit_reference_line(naive['Temp (C)'], naive['ln(d/a^2)'], naive['Fi+1'],
                                    threshold=FRACTIONAL_YIELD_THRESHOLD)
    naive_fit['Tc_C'] = dodson_closure_temperature(naive_fit['Ea_cal_mol'], naive_fit['D0_a2'],
                                                     COOLING_RATE_C_PER_MYR, A=DODSON_A)
    naive_fit['Tc_C_stderr'] = dodson_closure_temperature_stderr(
        naive_fit['Ea_cal_mol'], naive_fit['D0_a2'], naive_fit['Ea_cal_mol_stderr'], naive_fit['D0_a2_stderr'],
        COOLING_RATE_C_PER_MYR, A=DODSON_A)
    naive_fit['Tc_C_stderr_interceptonly'] = dodson_closure_temperature_stderr_interceptonly(
        naive_fit['Ea_cal_mol'], naive_fit['D0_a2'], naive_fit['D0_a2_stderr'],
        COOLING_RATE_C_PER_MYR, A=DODSON_A)
    naive_fit['excluded_steps'] = [11, 12]
    cache['naive'] = naive_fit
    print(f"\nStage 1 reference (naive/informed bracketing, direct-measurement check): "
          f"slope={naive_fit['slope']:.4f}+/-{naive_fit['slope_stderr']:.4f}  "
          f"intercept={naive_fit['intercept']:.4f}+/-{naive_fit['intercept_stderr']:.4f}  "
          f"Ea={naive_fit['Ea_kJ_mol']:.1f}+/-{naive_fit['Ea_kJ_mol_stderr']:.1f} kJ/mol  "
          f"R2={naive_fit['r2']:.4f}  n={naive_fit['n_points']}  "
          f"Tc={naive_fit['Tc_C']:.1f}+/-{naive_fit['Tc_C_stderr']:.1f} degC (joint)  "
          f"+/-{naive_fit['Tc_C_stderr_interceptonly']:.1f} degC (intercept-only)")

    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2)
    print(f"\nWrote {CACHE_PATH}")
