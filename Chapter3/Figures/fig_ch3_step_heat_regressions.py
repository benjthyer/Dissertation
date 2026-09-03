"""
Per-sample Arrhenius and delta plots for all seven plotable Chapter 3
sulfide step-heat experiments, plus a combined delta plot of all four
pyrite experiments together (including Rustenburg, referenced to the
shared LVCO line just like the other three, even though Rustenburg's own
per-sample plots use its own Rust regression -- see PYRITE_SAMPLES below).

Reads:
    Chapter3/Tables/plotable_sulfides_cache.pkl        (per-step data)
    generated/data/ch3_regression_cache.json           (fit lines; run
        prepare_ch3_regression_cache.py first if missing/stale)

Each sample is assigned either its OWN fitted regression line (LVCOPy230630,
Rustenburg Pyrite, CCpTS230630 -- the three named regions in
prepare_ch3_regression_cache.py) or a REFERENCE line borrowed from another
sample's regression, per the Results text (Sec. 3.2): BigLVCOPy230707,
112123LVCOPyIrr, and SalAspIrr (arsenopyrite) all reference the LVCO line;
GalTS230630 (galena) references the CCp line. The delta value at each step
is ln(D/a^2)_measured minus that reference line evaluated at the step's own
temperature, so "delta" always means "departure from whichever line the
manuscript text uses for that sample."

Every diffusivity/delta error bar in this script goes through
plot_style.diffusivity_errorbar(), which handles the "5" LB_dln(d/a^2)
sentinel (an unconstrained-lower-bound flag, not a real uncertainty --
see that function's docstring) by ghosting those specific points rather
than drawing a giant, physically meaningless whisker or silently dropping
them.

Outputs, one pair per sample -> generated/step_heat_regressions/:
    <sample>_arrhenius.pdf   (data + own-fit/reference line, own-fit steps
                               highlighted)
    <sample>_delta.pdf       (delta vs. cumulative 3He yield)
Plus the combined pyrite delta plot:
    generated/step_heat_regressions/Pyrite_delta_compilation.pdf
        (all four pyrite experiments together, referenced to the shared
        LVCO line, with error bars.)
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
OUTDIR = os.path.join(SCRIPT_DIR, 'generated', 'step_heat_regressions')
os.makedirs(OUTDIR, exist_ok=True)

Ctemps = np.array([100, 150, 200, 250, 300, 350, 400, 500, 600])

# {sample: (display label, marker, color, fit_key or None)}
# fit_key names the region in ch3_regression_cache.json that is this
# sample's OWN fitted regression (drawn solid, fitted steps highlighted).
# Samples with fit_key=None instead draw a dashed line borrowed from
# ref_key's region (see REFERENCE map below), per the Results text.
SAMPLE_META = {
    'LVCOPy230630':      dict(label='Pyrite: LVCOPy230630 (Leadville, 200 µm)', marker='o', color='tab:blue', fit_key='LVCO'),
    'BigLVCOPy230707':   dict(label='Pyrite: BigLVCOPy230707 (Leadville, 400 µm)', marker='o', color='tab:cyan', fit_key=None),
    '112123LVCOPyIrr':   dict(label='Pyrite: 112123LVCOPyIrr (Leadville, S-isolated)', marker='o', color='tab:purple', fit_key=None),
    'Rustenburg Pyrite': dict(label='Pyrite: Rustenburg (4He)', marker='D', color='tab:orange', fit_key='Rust'),
    'SalAspIrr':         dict(label='Arsenopyrite: 112123SalAspIrr', marker='s', color='tab:green', fit_key=None),
    'GalTS230630':       dict(label='Galena: GalTS230630', marker='X', color='tab:red', fit_key=None),
    'CCpTS230630':       dict(label='Chalcopyrite: CCpTS230630', marker='v', color='tab:brown', fit_key='CCp'),
}

# Pyrites shown together on the combined delta plot, all referenced to the
# shared LVCO line (see module docstring) regardless of each sample's own
# fit_key above.
PYRITE_SAMPLES = ['LVCOPy230630', 'BigLVCOPy230707', '112123LVCOPyIrr', 'Rustenburg Pyrite']


def _num(df, col):
    return pd.to_numeric(df[col], errors='coerce').to_numpy(dtype=float)


def _safe_name(sample):
    return sample.replace(' ', '_').replace('/', '_')


def _add_temp_axis(ax1):
    ax2 = ax1.twiny()
    xlim = ax1.get_xlim()
    ax2.set_xticks(1e4 / (Ctemps + 273))
    ax2.set_xlim(xlim)
    ax2.set_xticklabels(Ctemps)
    ax2.set_xlabel('Temperature (°C)')
    return ax2


def _line_label(key, m, regressions):
    return (f"{regressions[key]['sample']} regression "
            f"(Ea={m['Ea_kcal_mol']:.1f} kcal/mol, R²={m['r2']:.3f})")


def plot_sample_arrhenius(df, sample, meta, ref_key, regressions):
    x = df['10000/TK'].to_numpy(dtype=float)
    y = df['ln(d/a^2)'].to_numpy(dtype=float)
    lb, ub = _num(df, 'LB_dln(d/a^2)'), _num(df, 'UB_dln(d/a^2)')

    fig, ax1 = plt.subplots()
    # Drawn as its own low-alpha layer, in the data's original (chronological
    # step) order -- rather than through diffusivity_errorbar's own
    # linestyle -- so the step-to-step path stays continuous even where a
    # ghost (unconstrained-LB) point splits diffusivity_errorbar's own
    # normal/ghost series apart.
    ax1.plot(x, y, linestyle=':', color=meta['color'], alpha=0.35, zorder=1)
    diffusivity_errorbar(ax1, x, y, lb, ub, meta['color'], meta['marker'], label=sample,
                         normal_alpha=0.6)

    if meta['fit_key'] is not None:
        fit_steps = set(regressions[meta['fit_key']]['steps'])
        mask = df['step'].isin(fit_steps).to_numpy()
        ax1.scatter(x[mask], y[mask], marker=meta['marker'], color=meta['color'],
                    edgecolor='black', linewidth=1.2, s=70, zorder=5,
                    label='points used in regression')

    m = regressions[ref_key]['M']
    xlim = ax1.get_xlim()
    xfit = np.array(xlim)
    yfit = m['intercept'] + m['slope'] * xfit
    linestyle = '-' if meta['fit_key'] is not None else '--'
    ax1.plot(xfit, yfit, color='black', linestyle=linestyle, linewidth=1.5)
             #label=_line_label(ref_key, m, regressions))
    ax1.set_xlim(xlim)

    _add_temp_axis(ax1)
    ax1.set_xlabel(r'$10^4/T$ (K)')
    ax1.set_ylabel(r'$\ln(D/a^2)$ (s$^{-1}$)')
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=10)
    ax1.set_title(f'{sample}: Apparent 3He Diffusivity')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, f'{_safe_name(sample)}_arrhenius.pdf'), dpi=300, bbox_inches='tight')
    plt.close(fig)


def delta_values(df, ref_fit):
    x = df['10000/TK'].to_numpy(dtype=float)
    y = df['ln(d/a^2)'].to_numpy(dtype=float)
    ref = ref_fit['intercept'] + ref_fit['slope'] * x
    return y - ref


def plot_sample_delta(df, sample, meta, ref_key, regressions):
    m = regressions[ref_key]['M']
    fim = df['Fim'].to_numpy(dtype=float)
    delta = delta_values(df, m)
    lb, ub = _num(df, 'LB_dln(d/a^2)'), _num(df, 'UB_dln(d/a^2)')

    order = np.argsort(fim, kind='stable')
    fig, ax = plt.subplots()
    # See plot_sample_arrhenius for why the connecting line is its own layer.
    ax.plot(fim[order], delta[order], linestyle='-', color=meta['color'], alpha=0.4, zorder=1)
    diffusivity_errorbar(ax, fim[order], delta[order], lb[order], ub[order],
                         meta['color'], meta['marker'], normal_alpha=0.7)
    ax.axhline(0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel(r'Cumulative $^3$He Yield, $F_i$')
    ax.set_ylabel(r'$\Delta = \ln(D/a^2)_\mathrm{meas} - \ln(D/a^2)_\mathrm{ref}$')
    ax.grid(alpha=0.3)
    ref_sample = regressions[ref_key]['sample']
    ref_note = 'own regression' if meta['fit_key'] == ref_key else f'{ref_sample} reference'
    ax.set_title(f'{sample}: Delta Plot\n(referenced to {ref_note}, Ea={m["Ea_kcal_mol"]:.1f} kcal/mol)')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, f'{_safe_name(sample)}_delta.pdf'), dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_pyrite_delta_compilation(cache, regressions):
    ref_fit = regressions['LVCO']['M']
    fig, ax = plt.subplots()#figsize=(7, 5))
    for sample in PYRITE_SAMPLES:
        meta = SAMPLE_META[sample]
        df = cache[cache['sample'] == sample]
        fim = df['Fim'].to_numpy(dtype=float)
        delta = delta_values(df, ref_fit)
        lb, ub = _num(df, 'LB_dln(d/a^2)'), _num(df, 'UB_dln(d/a^2)')
        order = np.argsort(fim, kind='stable')
        ax.plot(fim[order], delta[order], linestyle='-', color=meta['color'], alpha=0.5, zorder=1)
        diffusivity_errorbar(ax, fim[order], delta[order], lb[order], ub[order],
                             meta['color'], meta['marker'], label=sample, normal_alpha=0.8)
    ax.axhline(0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel(r'Cumulative $^3$He Yield, $F_i$')
    ax.set_ylabel(r'$\Delta = \ln(D/a^2)_\mathrm{meas} - \ln(D/a^2)_\mathrm{LVCO\ ref}$')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=10)
    ax.set_title('Pyrite Delta Plot Compilation\n(all referenced to the LVCOPy230630 regression line)')
    fig.tight_layout()
    outpath = os.path.join(OUTDIR, 'Pyrite_delta_compilation.pdf')
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
    ref_map = regressions['delta_reference']

    for sample, meta in SAMPLE_META.items():
        df = cache[cache['sample'] == sample]
        if df.empty:
            print(f"  no rows for '{sample}' -- skipping")
            continue
        ref_key = ref_map[sample]
        print(f"Plotting '{sample}' (n={len(df)}, ref={ref_key})...")
        plot_sample_arrhenius(df, sample, meta, ref_key, regressions)
        plot_sample_delta(df, sample, meta, ref_key, regressions)

    plot_pyrite_delta_compilation(cache, regressions)
    print(f"Wrote per-sample figures to {OUTDIR}")


if __name__ == '__main__':
    main()
