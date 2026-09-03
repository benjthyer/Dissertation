"""
Full-page SI compilation figures: two grids (Arrhenius column, delta
column) covering every plotable Chapter 3 sulfide step-heat experiment --
built at the user's request to replace the scattered per-sample citations
to individual step_heat_regressions/*.pdf files with comprehensive
reference figures.

Originally a single 7-row x 2-column grid; split into two figures (one
per page) because the 7-row version ran off the bottom of the page even
at [p]-float, textwidth/textheight scaling: a 4-row Pyrite grid (Rustenburg
Pyrite, LVCOPy230630, 112123LVCOPyIrr, BigLVCOPy230707) and a 3-row Other
Sulfides grid (SalAspIrr/arsenopyrite, GalTS230630/galena,
CCpTS230630/chalcopyrite).

Also: every subplot now gets its own x-axis tick labels AND x-axis title
(previously only the bottom row of the 7-row grid had either) -- rows do
NOT share a common x-axis scale (each sample's Arrhenius/delta data spans
a different range), so labeling only the bottom row misleadingly implied
a shared scale across all rows.

Row order within each grid (as specified): Pyrite grid -- Rustenburg
Pyrite, LVCOPy230630 (small, 200 um), 112123LVCOPyIrr (sulfur-isolated),
BigLVCOPy230707 (big, 400 um). Other Sulfides grid -- SalAspIrr
(arsenopyrite), GalTS230630 (galena), CCpTS230630 (chalcopyrite).

Each row's plotting logic is deliberately the same as the existing
per-sample figures in fig_ch3_step_heat_regressions.py (same cache,
same regression-line/reference-line assignment per Sec. 3.2's Results
text, same diffusivity_errorbar ghosting convention for unconstrained
lower bounds) -- just re-drawn onto a shared grid of subplots instead
of one file per sample, per fig/delta pair. In particular, each
Arrhenius panel (left column) plots the *same* reference regression
line used to compute that row's delta panel (right column), so the
two panels in a row are directly comparable by eye.

Reads:
    Chapter3/Tables/plotable_sulfides_cache.pkl
    Chapter3/Figures/generated/data/ch3_regression_cache.json

Output:
    Chapter3/Figures/generated/Sulfide_StepHeat_SI_Grid_Pyrite.pdf
    Chapter3/Figures/generated/Sulfide_StepHeat_SI_Grid_Other.pdf
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from plot_style import diffusivity_errorbar  # noqa: E402
import matplotlib as mpl  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

CACHE_PKL = os.path.join(SCRIPT_DIR, '..', 'Tables', 'plotable_sulfides_cache.pkl')
REGRESSION_JSON = os.path.join(SCRIPT_DIR, 'generated', 'data', 'ch3_regression_cache.json')
OUTDIR = os.path.join(SCRIPT_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

Ctemps = np.array([600, 500, 400])

# Row metadata, matching SAMPLE_META / DELTA_REFERENCE in
# fig_ch3_step_heat_regressions.py / prepare_ch3_regression_cache.py
# exactly (see module docstring). Split into the two grids below.
PYRITE_ROWS = [
    ('Rustenburg Pyrite', 'Rustenburg Pyrite', 'D', 'tab:orange', 'Rust'),
    ('LVCOPy230630', 'LVCOPy230630 (Leadville, small)', 'o', 'tab:blue', 'LVCO'),
    ('112123LVCOPyIrr', '112123LVCOPyIrr (Leadville, S-isolated)', 'o', 'tab:purple', 'LVCO'),
    ('BigLVCOPy230707', 'BigLVCOPy230707 (Leadville, big)', 'o', 'tab:cyan', 'LVCO'),
]
OTHER_ROWS = [
    ('SalAspIrr', 'SalAspIrr (Arsenopyrite)', 's', 'tab:green', 'LVCO'),
    ('GalTS230630', 'GalTS230630 (Galena)', 'X', 'tab:red', 'CCp'),
    ('CCpTS230630', 'CCpTS230630 (Chalcopyrite)', 'v', 'tab:brown', 'CCp'),
]
# fit_key: the region this sample OWNS (drawn solid, own-fit steps
# highlighted); None means the row instead borrows/references another
# sample's line (drawn dashed), per Sec. 3.2 of the Results text.
FIT_KEY = {
    'Rustenburg Pyrite': 'Rust',
    'LVCOPy230630': 'LVCO',
    'CCpTS230630': 'CCp',
}

FONT = dict(label=11, tick=9.5, legend=6, rowlabel=10.5)  # label/tick/rowlabel bumped at user request (in-plot text too small); legend left as-is (reported fine)


def _num(df, col):
    return pd.to_numeric(df[col], errors='coerce').to_numpy(dtype=float)


def _add_temp_axis(ax, xlim):
    ax2 = ax.twiny()
    ax2.set_xticks(1e4 / (Ctemps + 273))
    ax2.set_xlim(xlim)
    ax2.set_xticklabels(Ctemps, fontsize=FONT['tick'])
    ax2.set_xlabel('Temperature (°C)', fontsize=FONT['label'])
    return ax2


def plot_row(ax_arr, ax_delta, sample, label, marker, color, ref_key, cache, regressions, is_top, max_xticks=None):
    df = cache[cache['sample'] == sample]
    x = df['10000/TK'].to_numpy(dtype=float)
    y = df['ln(d/a^2)'].to_numpy(dtype=float)
    lb, ub = _num(df, 'LB_dln(d/a^2)'), _num(df, 'UB_dln(d/a^2)')
    fim = df['Fim'].to_numpy(dtype=float)

    # --- Arrhenius panel ---
    ax_arr.plot(x, y, linestyle=':', color=color, alpha=0.35, zorder=1, linewidth=0.8)
    diffusivity_errorbar(ax_arr, x, y, lb, ub, color, marker, normal_alpha=0.65,
                          markersize=3.5, capsize=2, arrow_length=0.8)

    fit_key = FIT_KEY.get(sample)
    if fit_key is not None:
        fit_steps = set(regressions[fit_key]['steps'])
        mask = df['step'].isin(fit_steps).to_numpy()
        ax_arr.scatter(x[mask], y[mask], marker=marker, color=color, edgecolor='black',
                        linewidth=0.8, s=22, zorder=5)

    m = regressions[ref_key]['M']
    xlim = ax_arr.get_xlim()
    xfit = np.array(xlim)
    yfit = m['intercept'] + m['slope'] * xfit
    linestyle = '-' if fit_key is not None else '--'
    ref_note = 'own regression' if fit_key == ref_key else f"{regressions[ref_key]['sample']} ref."
    ax_arr.plot(xfit, yfit, color='black', linestyle=linestyle, linewidth=1.1,
                label=f"{ref_note}\nEa={m['Ea_kcal_mol']:.1f} kcal/mol")
    ax_arr.set_xlim(xlim)
    ax_arr.grid(alpha=0.25, linewidth=0.5)
    ax_arr.legend(fontsize=FONT['legend'], loc='lower left', framealpha=0.7, handlelength=1.2)
    ax_arr.tick_params(labelsize=FONT['tick'])
    ax_arr.set_ylabel(r'$\ln(D/a^2)$', fontsize=FONT['label'])
    # Every row gets its own x-axis tick labels and title -- rows do NOT
    # share a common x-axis scale, so labeling only the bottom row (as
    # the original single 7-row grid did) misleadingly implied they did.
    ax_arr.set_xlabel(r'$10^4/T$ (K)', fontsize=FONT['label'])
    if max_xticks is not None:
        ax_arr.xaxis.set_major_locator(MaxNLocator(nbins=max_xticks))
    ax_arr.text(0.02, 0.95, label, transform=ax_arr.transAxes, fontsize=FONT['rowlabel'],
                fontweight='bold', va='top', ha='left',
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.75))
    if is_top:
        _add_temp_axis(ax_arr, xlim)
        ax_arr.set_title('Arrhenius', fontsize=FONT['label'] + 1, pad=28)

    # --- Delta panel ---
    ref_fit = regressions[ref_key]['M']
    delta = y - (ref_fit['intercept'] + ref_fit['slope'] * x)
    order = np.argsort(fim, kind='stable')
    ax_delta.plot(fim[order], delta[order], linestyle='-', color=color, alpha=0.4, zorder=1, linewidth=0.8)
    diffusivity_errorbar(ax_delta, fim[order], delta[order], lb[order], ub[order], color, marker,
                          normal_alpha=0.7, markersize=3.5, capsize=2, arrow_length=0.8)
    ax_delta.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax_delta.grid(alpha=0.25, linewidth=0.5)
    ax_delta.tick_params(labelsize=FONT['tick'])
    ax_delta.set_ylabel(r'$\Delta \ln(D/a^2)$', fontsize=FONT['label'])
    ax_delta.set_xlabel(r'Cumulative He Yield, $F_i$', fontsize=FONT['label'])
    if max_xticks is not None:
        ax_delta.xaxis.set_major_locator(MaxNLocator(nbins=max_xticks))
    if is_top:
        ax_delta.set_title('Delta', fontsize=FONT['label'] + 1, pad=28)


# Per-row figure height, in inches, at the matplotlib source size (before
# LaTeX scales the PDF down to fit \textwidth). Bumped up from the
# original 13.5/7 = 1.929 in/row once the SI captions were shortened
# (HeInSulfides_SI_body.tex), freeing enough vertical room on the page
# for larger plots: since \includegraphics uses
# width=\textwidth,height=\textheight,keepaspectratio and the rendered
# width (\textwidth=5.5in on this class's letter/1.5in-margin page) is
# the binding constraint for both grids, a taller source figure directly
# becomes a taller rendered image at the same width.
ROW_HEIGHT_IN = 2.55


def build_grid(rows, title, outname, cache, regressions, max_xticks=None):
    """Build and save one N-row x 2-column grid figure for the given rows."""
    n = len(rows)
    fig, axes = plt.subplots(n, 2, figsize=(8.25, ROW_HEIGHT_IN * n))
    if n == 1:
        axes = axes.reshape(1, 2)

    for i, (sample, label, marker, color, ref_key) in enumerate(rows):
        plot_row(axes[i, 0], axes[i, 1], sample, label, marker, color, ref_key,
                 cache, regressions, is_top=(i == 0), max_xticks=max_xticks)

    fig.suptitle(title, fontsize=FONT['label'] + 3, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.985), h_pad=1.6, w_pad=2.2)

    outpath = os.path.join(OUTDIR, outname)
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Wrote {outpath}")


def main():
    if not os.path.exists(CACHE_PKL):
        raise FileNotFoundError(f"{CACHE_PKL} not found -- run Chapter3/Tables/build_plotable_cache.py first.")
    if not os.path.exists(REGRESSION_JSON):
        raise FileNotFoundError(f"{REGRESSION_JSON} not found -- run prepare_ch3_regression_cache.py first.")

    cache = pd.read_pickle(CACHE_PKL)
    with open(REGRESSION_JSON) as f:
        regressions = json.load(f)

    mpl.rcParams.update({'font.size': FONT['label']})

    build_grid(
        PYRITE_ROWS,
        'Chapter 3 Sulfide Step-Heat Compilation: Arrhenius and Delta Plots, Pyrite Samples',
        'Sulfide_StepHeat_SI_Grid_Pyrite.pdf',
        cache, regressions, max_xticks=6,
    )
    build_grid(
        OTHER_ROWS,
        'Chapter 3 Sulfide Step-Heat Compilation: Arrhenius and Delta Plots, Other Sulfides',
        'Sulfide_StepHeat_SI_Grid_Other.pdf',
        cache, regressions,
    )


if __name__ == '__main__':
    main()
