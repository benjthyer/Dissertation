"""
Combined Arrhenius compilation of the three Leadville pyrite step-heat
experiments and the arsenopyrite step-heat experiment (figure 3.3 in the
manuscript text), with the LVCO regression line
(prepare_ch3_regression_cache.py) overlaid, plus a reference line for He
diffusion in Durango apatite (r=150 um, Ea=33 kcal/mol; Farley 2000).

Rustenburg pyrite is deliberately NOT included here -- it's a different
locality/generation (South African, octahedral, 4He/isotope-dilution)
with its own distinct short-circuit-diffusion Arrhenius geometry (Rust
regression) that doesn't belong on the same shared-slope compilation as
the three similar Leadville experiments; it gets its own dedicated plot
from fig_ch3_step_heat_regressions.py (Rustenburg_Pyrite_arrhenius.pdf /
Rustenburg_Pyrite_delta.pdf) instead.

Previously this script read a standalone plotable_sulfides.xlsx snapshot
via a bare relative path -- fragile (depended on the caller's cwd) and
stale (didn't reflect later fixes to the plotable-row selection or
diffusivity reduction). It now reads the same
Tables/plotable_sulfides_cache.pkl cache and generated/data/
ch3_regression_cache.json used by every other Chapter 3 step-heat figure,
so this plot never drifts out of sync with them.

Run prepare_ch3_regression_cache.py first if
generated/data/ch3_regression_cache.json is missing or stale.

Output: generated/Sulfide_compilation_Arr.pdf
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from plot_style import apply_style, diffusivity_errorbar
apply_style()

CACHE_PKL = os.path.join(SCRIPT_DIR, '..', 'Tables', 'plotable_sulfides_cache.pkl')
REGRESSION_JSON = os.path.join(SCRIPT_DIR, 'generated', 'data', 'ch3_regression_cache.json')
OUTDIR = os.path.join(SCRIPT_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

Ctemps = np.array([100, 150, 200, 250, 300, 350, 400, 500, 600])

# Samples plotted here: the three Leadville pyrites + arsenopyrite
# (Rustenburg pyrite gets its own plot -- see module docstring; galena
# and chalcopyrite are excluded -- they're plotted together on their own
# compilation elsewhere, since their retentivity is an order of magnitude
# lower and would compress the pyrite/arsenopyrite data on a shared axis).
SAMPLES = [
    ('LVCOPy230630', 'Pyrite: LVCOPy230630 (Leadville, 200 um)', 'o', 'tab:blue'),
    ('BigLVCOPy230707', 'Pyrite: BigLVCOPy230707 (Leadville, 400 um)', 'o', 'tab:cyan'),
    ('112123LVCOPyIrr', 'Pyrite: 112123LVCOPyIrr (Leadville, S-isolated)', 'o', 'tab:purple'),
    ('SalAspIrr', 'Arsenopyrite: 112123SalAspIrr', 's', 'tab:green'),
]


def _num(df, col):
    return pd.to_numeric(df[col], errors='coerce').to_numpy(dtype=float)


def main():
    if not os.path.exists(CACHE_PKL):
        raise FileNotFoundError(f"{CACHE_PKL} not found -- run Chapter3/Tables/build_plotable_cache.py first.")
    if not os.path.exists(REGRESSION_JSON):
        raise FileNotFoundError(f"{REGRESSION_JSON} not found -- run prepare_ch3_regression_cache.py first.")

    cache = pd.read_pickle(CACHE_PKL)
    with open(REGRESSION_JSON) as f:
        regressions = json.load(f)

    fig, ax1 = plt.subplots(figsize=(7.5, 5.5))
    ax2 = ax1.twiny()

    for sample, label, marker, color in SAMPLES:
        df = cache[cache['sample'] == sample]
        if df.empty:
            print(f"  no rows for '{sample}' -- skipping")
            continue
        x = df['10000/TK'].to_numpy(dtype=float)
        y = df['ln(d/a^2)'].to_numpy(dtype=float)
        lb, ub = _num(df, 'LB_dln(d/a^2)'), _num(df, 'UB_dln(d/a^2)')
        # Own low-alpha connecting line (chronological step order) so it
        # stays continuous across any ghosted (unconstrained-LB) points --
        # see diffusivity_errorbar's docstring.
        ax1.plot(x, y, linestyle=':', color=color, alpha=0.4, zorder=1)
        diffusivity_errorbar(ax1, x, y, lb, ub, color, marker, label=label, normal_alpha=0.65)

    xlim = ax1.get_xlim()
    xfit = np.array(xlim)

    m = regressions['LVCO']['M']
    yfit = m['intercept'] + m['slope'] * xfit
    ax1.plot(xfit, yfit, color='black', linestyle='-', linewidth=1.5)
             #label=f"{regressions['LVCO']['sample']} regression "
             #      f"(Ea={m['Ea_kcal_mol']:.1f} kcal/mol, R²={m['r2']:.3f})")

    """# Durango apatite reference line, r = 150 um (Farley 2000)
    ax1.plot(xfit, np.log(((10 ** 1.5) / (0.015 ** 2)) * np.exp(-33000 * xfit / (1.987 * 10000))),
             color='dimgray', linestyle='-.', linewidth=1.5,
             label='Durango Apatite, r = 150 µm (Farley 2000)')"""

    ax1.set_xlim(xlim)
    ax2.set_xticks(1e4 / (Ctemps + 273))
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticklabels(Ctemps)
    ax2.set_xlabel('Temperature (°C)')
    ax1.set_xlabel(r'$10^4/T$ (K)')
    ax1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=10, loc='lower left')
    ax1.set_title('Irradiated Encapsulated Leadville Pyrite and Arsenopyrite\n3He Apparent Diffusivity Compilation')
    fig.tight_layout()
    outpath = os.path.join(OUTDIR, 'Sulfide_compilation_Arr.pdf')
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Wrote {outpath}")


if __name__ == '__main__':
    main()
