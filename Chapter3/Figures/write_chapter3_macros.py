"""
write_chapter3_macros.py -- emit Chapter3/Writing/chapter3_derived_values.tex,
\\newcommand macros for the three named Arrhenius regressions fit by
prepare_ch3_regression_cache.py (LVCO, Rust, CCp -- see that script's
docstring), read from generated/data/ch3_regression_cache.json, instead of
hand-typing activation energies/R^2/closure temperatures into the Results,
Discussion, and Abstract text.

Point estimates and uncertainties always come from the central ("M",
i.e. the same "treatment as uncertainty" central bound Chapter 2 uses as
its point estimate) bound's own regression -- not the LB/UB
treatment-bound-shifted fits also stored in the cache. Those LB/UB fits
are kept in the JSON for transparency, but are not surfaced as macros:
for CCp, several of the linear region's steps have LB_dln(d/a^2) = 5 (a
workbook sentinel for "lower bound unconstrained", not a real 5-natural-
log-unit uncertainty), which makes the LB-shifted regression for CCp
nonsensical (R^2=0.006, Tc=-136 degC) -- not something that should ever
reach the manuscript text.

This also resolves a real inconsistency the auto-generation replaces:
the old hand-typed Abstract text quoted the Rustenburg fast-pathway
activation energy as "255 +/- 28 kJ/mol", but the Results section quoted
the same regression as "71.8 Kcal/mol" (= 300.6 kJ/mol) -- two different
numbers for the same fit. The 255 kJ figure is close to what an
LB-bound-shifted fit of the same 5 points gives (246.8 +/- 29.6 kJ/mol),
suggesting the Abstract was last hand-updated against a different bound
convention than the Results text. The regenerated Abstract macro below
uses the same M-bound convention as everywhere else in the chapter
(consistent with the CCp Tc=128 degC already in Results matching the
M-bound Tc, not LB's -136 or UB's 138), i.e. 300.6 +/- 7.3 kJ/mol.

Run this AFTER prepare_ch3_regression_cache.py (it only reads that
script's JSON output). run_all_figures.py runs both, in order,
automatically.

Significant-figure handling matches write_chapter2_macros.py: each
uncertainty is rounded to 2 significant figures, then the paired central
value is rounded to the same decimal place.
"""
import json
import math
import os

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(FIG_DIR, 'generated', 'data', 'ch3_regression_cache.json')
OUT_PATH = os.path.join(FIG_DIR, '..', 'Writing', 'chapter3_derived_values.tex')

# Which Tc uncertainty convention to expose -- matches Chapter 2's choice
# (intercept-only: D0/a^2 term only, Ea held fixed at its central value).
TC_STDERR_KEY = 'Tc_C_stderr_interceptonly'

# {macro prefix: cache key}
REGIONS = {'ChThreeLVCO': 'LVCO', 'ChThreeRust': 'Rust', 'ChThreeCCp': 'CCp'}


def round_to_sig_figs(x, sig_figs):
    if x == 0:
        return 0.0, 0
    exponent = math.floor(math.log10(abs(x)))
    decimals = max(sig_figs - int(exponent) - 1, 0)
    return round(x, decimals), decimals


def format_value_and_stderr(value, stderr, sig_figs=2):
    _, decimals = round_to_sig_figs(stderr, sig_figs)
    fmt = f"%.{decimals}f"
    return fmt % round(value, decimals), fmt % round(stderr, decimals)


def newcommand(name, value):
    return f"\\newcommand{{\\{name}}}{{{value}}}\n"


def region_macros(prefix, m):
    ea_kcal, ea_kcal_err = format_value_and_stderr(m['Ea_kcal_mol'], m['Ea_kcal_mol_stderr'])
    ea_kj, ea_kj_err = format_value_and_stderr(m['Ea_kJ_mol'], m['Ea_kJ_mol_stderr'])
    tc, tc_err = format_value_and_stderr(m['Tc_C'], m[TC_STDERR_KEY])
    r2 = f"{m['r2']:.4f}" if m['r2'] < 0.995 else f"{m['r2']:.3f}"
    return [
        newcommand(f'{prefix}EaKcal', ea_kcal),
        newcommand(f'{prefix}EaKcalErr', ea_kcal_err),
        newcommand(f'{prefix}Ea', ea_kj),
        newcommand(f'{prefix}EaErr', ea_kj_err),
        newcommand(f'{prefix}Rtwo', r2),
        newcommand(f'{prefix}N', str(m['n_points'])),
        newcommand(f'{prefix}Tc', tc),
        newcommand(f'{prefix}TcErr', tc_err),
    ]


if __name__ == '__main__':
    with open(CACHE_PATH) as f:
        cache = json.load(f)

    lines = [
        "% =============================================================\n",
        "%  chapter3_derived_values.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.\n",
        "%  Written by Figures/write_chapter3_macros.py from\n",
        "%  Figures/generated/data/ch3_regression_cache.json (itself written by\n",
        "%  Figures/prepare_ch3_regression_cache.py from\n",
        "%  Tables/plotable_sulfides_cache.pkl).\n",
        "%\n",
        "%  Regenerate after any data/regression change:\n",
        "%    python3 Figures/prepare_ch3_regression_cache.py\n",
        "%    python3 Figures/write_chapter3_macros.py\n",
        "%  (run_all_figures.py does both automatically.)\n",
        "%\n",
        "%  \\input{} by HeInSulfides_Main_Body.tex and HeInSulfides_abstract.tex\n",
        "%  so the Abstract, Results, and Discussion all read the same numbers.\n",
        "%\n",
        "%  Three named linear Arrhenius regions (see prepare_ch3_regression_cache.py\n",
        "%  docstring for the physical rationale and exact step numbers of each):\n",
        "%    ChThreeLVCO* : LVCOPy230630 prograde array (n=9, R2=0.998) -- shared\n",
        "%      reference line for BigLVCOPy230707, 112123LVCOPyIrr, and (qualitatively)\n",
        "%      SalAspIrr arsenopyrite.\n",
        "%    ChThreeRust* : Rustenburg Pyrite down-temperature retrograde cluster\n",
        "%      (n=5, R2=0.998) -- the short-circuit/pipe-diffusion fast pathway.\n",
        "%    ChThreeCCp*  : CCpTS230630 chalcopyrite retrograde/prograde tail (n=9,\n",
        "%      R2=0.981) -- shared reference line for GalTS230630 galena.\n",
        "%  Each region exposes:\n",
        "%    <p>EaKcal/<p>EaKcalErr : activation energy, kcal/mol (Results convention)\n",
        "%    <p>Ea/<p>EaErr         : activation energy, kJ/mol (Abstract convention)\n",
        "%    <p>Rtwo/<p>N            : regression R^2 and number of points\n",
        "%    <p>Tc/<p>TcErr          : Dodson (1973) closure temperature, degC\n",
        "%      (sphere, A=55, 10 degC/Myr cooling; intercept-only regression\n",
        "%      uncertainty -- D0/a^2 term only, Ea held fixed, matching Chapter 2's\n",
        "%      convention). All three point estimates and uncertainties are the\n",
        "%      regression's central (\"M\"/\"treatment as uncertainty\") bound; see\n",
        "%      this script's module docstring for why the LB/UB bound-shifted fits\n",
        "%      are not also exposed as macros.\n",
        "% =============================================================\n",
    ]
    for prefix, key in REGIONS.items():
        lines += region_macros(prefix, cache[key]['M'])

    with open(OUT_PATH, 'w') as f:
        f.writelines(lines)

    for prefix, key in REGIONS.items():
        m = cache[key]['M']
        print(f"{key}: Ea = {m['Ea_kcal_mol']:.1f}+/-{m['Ea_kcal_mol_stderr']:.1f} kcal/mol "
              f"({m['Ea_kJ_mol']:.1f}+/-{m['Ea_kJ_mol_stderr']:.1f} kJ/mol), "
              f"R2 = {m['r2']:.4f}, n = {m['n_points']}, "
              f"Tc = {m['Tc_C']:.1f}+/-{m[TC_STDERR_KEY]:.1f} degC")
    print(f"Wrote {OUT_PATH}")
