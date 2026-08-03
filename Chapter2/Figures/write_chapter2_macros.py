"""
write_chapter2_macros.py -- emit Chapter2/Writing/chapter2_derived_values.tex,
a small file of \\newcommand macros for the Stage 1 regression results
(activation energy, closure temperature, R^2, n) read straight from
generated/data/stage1_regression_cache.json (the "M"/central "treatment as
uncertainty" bound), instead of typing these numbers by hand into the
Abstract, Results, Discussion, Conclusions, and figure captions.

Why: those numbers had drifted out of sync with each other (and with the
cache) after the UB/LB diffusivity-inversion fix -- e.g. the Abstract and
Conclusions said "159.1 +/- 5.5 kJ/mol" while Results said "157.1 +/- 5.3
kJ/mol", both supposedly describing the same regression. \\input-ing this
file and referencing its macros everywhere means the next time the
underlying data or regression changes, re-running prepare_regression_cache.py
then this script is enough to keep every occurrence consistent -- there's
no more hand-copying to forget.

Run this AFTER prepare_regression_cache.py (it just reads that script's
JSON output; it does not touch the workbook or refit anything itself).
run_all_figures.py runs both, in order, automatically.

Also reads generated/data/naive_lambda_arrhenius_cache.json (written by
fig_naive_isothermal_fits.py) for the isothermal-permeation Arrhenius
regression's own activation energy/R^2 (\\ChTwoPermEa, \\ChTwoPermEaErr,
\\ChTwoPermRtwo, \\ChTwoPermN) -- these numbers were previously hand-typed
identically into both the main text and the SI ("R2 of 0.936, Ea of
10190+/-1880 cal/mol"), with no script actually producing them (the old
fitting code used an uncorrected/biased model and a bare np.polyfit with
no R^2 or stderr at all). fig_naive_isothermal_fits.py now fits the
bias-corrected model (Chapter 1's Eq.~\\eqref{eq:incyield}) and computes
the regression properly; these macros expose that result the same way
the Stage 1 macros above expose the diffusivity regression.

Significant-figure handling: done here in Python, not in LaTeX. Each
uncertainty is rounded to 2 significant figures; the paired central value
is then rounded to the same decimal place as the (rounded) uncertainty,
which is the conventional way to avoid implying false precision. (For
values in the thousands, e.g. the permeation activation energy, the
decimal-place clamp below means the result is rounded to the nearest
integer rather than truly 2 sig figs -- a pre-existing limitation of this
helper, harmless here since it only affects display precision.)
"""
import json
import math
import os

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(FIG_DIR, 'generated', 'data', 'stage1_regression_cache.json')
PERM_CACHE_PATH = os.path.join(FIG_DIR, 'generated', 'data', 'naive_lambda_arrhenius_cache.json')
OUT_PATH = os.path.join(FIG_DIR, '..', 'Writing', 'chapter2_derived_values.tex')

# Which Tc uncertainty convention to expose as \ChTwoTcErr. The manuscript
# text describes "considering only uncertainty in the regression intercept
# (D0/a^2) term" -- i.e. the intercept-only convention, not the full joint
# slope+intercept propagation (also cached, as Tc_C_stderr, for comparison).
TC_STDERR_KEY = 'Tc_C_stderr_interceptonly'


def round_to_sig_figs(x, sig_figs):
    """Round x to sig_figs significant figures. Returns (rounded_value, decimals),
    where decimals is the number of digits after the decimal point needed
    to display that rounded value (>=0; negative decimal targets, e.g. for
    numbers >= 10**sig_figs, are clamped to 0)."""
    if x == 0:
        return 0.0, 0
    exponent = math.floor(math.log10(abs(x)))
    decimals = max(sig_figs - int(exponent) - 1, 0)
    return round(x, decimals), decimals


def format_value_and_stderr(value, stderr, sig_figs=2):
    """Round stderr to sig_figs significant figures, then round value to
    the same number of decimal places. Returns (value_str, stderr_str)."""
    _, decimals = round_to_sig_figs(stderr, sig_figs)
    fmt = f"%.{decimals}f"
    return fmt % round(value, decimals), fmt % round(stderr, decimals)


def newcommand(name, value):
    return f"\\newcommand{{\\{name}}}{{{value}}}\n"


if __name__ == '__main__':
    with open(CACHE_PATH) as f:
        cache = json.load(f)
    m = cache['M']

    ea_str, ea_err_str = format_value_and_stderr(m['Ea_kJ_mol'], m['Ea_kJ_mol_stderr'])
    tc_str, tc_err_str = format_value_and_stderr(m['Tc_C'], m[TC_STDERR_KEY])
    r2_str = f"{m['r2']:.3f}"
    n_str = str(m['n_points'])

    with open(PERM_CACHE_PATH) as f:
        perm = json.load(f)
    perm_ea_str, perm_ea_err_str = format_value_and_stderr(
        perm['Ea_cal_mol'], perm['Ea_cal_mol_2se'])
    perm_r2_str = f"{perm['r2']:.3f}"
    perm_n_str = str(perm['n_points'])

    lines = [
        "% =============================================================\n",
        "%  chapter2_derived_values.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.\n",
        "%  Written by Figures/write_chapter2_macros.py from\n",
        "%  Figures/generated/data/stage1_regression_cache.json (itself written by\n",
        "%  Figures/prepare_regression_cache.py from the master workbook).\n",
        "%\n",
        "%  Regenerate after any data/regression change:\n",
        "%    python3 Figures/prepare_regression_cache.py\n",
        "%    python3 Figures/write_chapter2_macros.py\n",
        "%  (run_all_figures.py does both automatically.)\n",
        "%\n",
        "%  \\input{} by BOTH chapter2goethite.tex (standalone) and\n",
        "%  Chapter2/chapter2.tex (dissertation chapter) so the Abstract,\n",
        "%  Results, Discussion, and Conclusions all read the same numbers.\n",
        "%\n",
        "%  Stage 1 reference line (3He, \"treatment as uncertainty\" central/M\n",
        "%  bound, fractional 3He yield >= {:.2f}, n={} points, R2={:.4f}):\n".format(
            cache['fractional_yield_threshold'], m['n_points'], m['r2']),
        "%    ChTwoEa/ChTwoEaErr : activation energy (kJ/mol)\n",
        "%    ChTwoTc/ChTwoTcErr : Dodson (1973) closure temperature (degC),\n",
        "%      intercept-only regression uncertainty (D0/a^2 term only, Ea\n",
        "%      held fixed) -- see thermochr_utils.dodson_closure_temperature_stderr_interceptonly.\n",
        "%      Joint slope+intercept uncertainty is +/- {:.1f} degC if ever needed.\n".format(
            m['Tc_C_stderr']),
        "%    ChTwoRtwo/ChTwoN   : regression R^2 and number of points\n",
        "%\n",
        "%  Isothermal 3He permeation Arrhenius regression (from\n",
        "%  generated/data/naive_lambda_arrhenius_cache.json, n={} sequences, R2={:.4f}):\n".format(
            perm['n_points'], perm['r2']),
        "%    ChTwoPermEa/ChTwoPermEaErr : activation energy, 2 s.e. (cal/mol)\n",
        "%    ChTwoPermRtwo/ChTwoPermN   : regression R^2 and number of sequences\n",
        "% =============================================================\n",
        newcommand('ChTwoEa', ea_str),
        newcommand('ChTwoEaErr', ea_err_str),
        newcommand('ChTwoTc', tc_str),
        newcommand('ChTwoTcErr', tc_err_str),
        newcommand('ChTwoRtwo', r2_str),
        newcommand('ChTwoN', n_str),
        newcommand('ChTwoPermEa', perm_ea_str),
        newcommand('ChTwoPermEaErr', perm_ea_err_str),
        newcommand('ChTwoPermRtwo', perm_r2_str),
        newcommand('ChTwoPermN', perm_n_str),
    ]

    with open(OUT_PATH, 'w') as f:
        f.writelines(lines)

    print(f"Ea = {ea_str} +/- {ea_err_str} kJ/mol")
    print(f"Tc = {tc_str} +/- {tc_err_str} degC (intercept-only)")
    print(f"R2 = {r2_str}, n = {n_str}")
    print(f"Isothermal permeation: Ea = {perm_ea_str} +/- {perm_ea_err_str} cal/mol, "
          f"R2 = {perm_r2_str}, n = {perm_n_str}")
    print(f"Wrote {OUT_PATH}")
