#!/usr/bin/env python
"""Bulk-reconstruction figures (PDF) for the shipped nGibbs emulators.

For each emulator: b_hat vs b and (b - b_hat)/b vs b, one panel per element,
the raw network reconstruction (mass_balance='none') in orange with the
mass-balanced one in blue on top.  Also writes the per-element statistics table
for each emulator.

Everything is written to ``generated/`` next to this file:

    generated/<family>[_<variant>]_<kind>_bulk_parity.pdf      (thesis-sized, see plot_parity_thesis)
    generated/<family>[_<variant>]_<kind>_bulk_relerr.pdf
    generated/<family>[_<variant>]_<kind>_bulk_reconstruction.csv

Only the installed ``ngibbs`` package is used (its shipped TrainedModels and
Test_subset bundles), so this file can live in any repository.

Examples
--------
    python make_bulk_reconstruction_figures.py                       # every shipped emulator
    python make_bulk_reconstruction_figures.py --families 102 120 --kinds isothermal
    python make_bulk_reconstruction_figures.py --pair my_model.tar my_Test_subset.tar.gz
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from ngibbs.deployment_tests.bulk_reconstruction import (
    evaluate_bulk_reconstruction, plot_bulk_reconstruction, write_summary,
)
from ngibbs.deployment_tests.discovery import shipped_emulators
from ngibbs.engine.NN import rebuild_MELTS_model
from ngibbs.engine.emulator import NN_MELTS

OUT_DIR = Path(__file__).resolve().parent / 'generated'


# Element labels for the thesis figure (closed-system models carry ferric iron as its own element).
_EL_TEX = {'Fe': r'Fe$^{2+}$', 'Fe3': r'Fe$^{3+}$'}
_MB_COLORS = {'raw': '#eb6834', 'massbalanced': '#2a78d6'}
_MB_LABELS = {'raw': 'raw network', 'massbalanced': 'mass balanced'}


def plot_parity_thesis(r, path, ncols=3, width_in=5.5, dpi=300):
    """Thesis version of the b_hat-vs-b figure: one panel per element, sized to print at
    `width_in` (the thesis text width) with legible fonts, minimal text (element name,
    axes b and b_hat, one legend in the spare panel). Scatter layers are rasterized."""
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    b = r['b']
    all_el = list(r['elements'])
    els = [e for e in all_el if (b[:, all_el.index(e)] > 1e-6).any()]
    keys = [k for k in ('raw', 'massbalanced') if k in r['b_hat']]
    nrows = -(-(len(els) + 1) // ncols)          # one spare cell for the legend
    rc = {'font.size': 10, 'axes.titlesize': 11, 'axes.labelsize': 11, 'xtick.labelsize': 8.5,
          'ytick.labelsize': 8.5, 'legend.fontsize': 10, 'pdf.fonttype': 42}
    with plt.rc_context(rc):
        fig, axes = plt.subplots(nrows, ncols, figsize=(width_in, 1.8 * nrows + 0.2),
                                 squeeze=False, layout='constrained')
        for ax in axes.flat[len(els):]:
            ax.axis('off')
        for ax, e in zip(axes.flat, els):
            j = all_el.index(e)
            vals = np.concatenate([b[:, j]] + [r['b_hat'][k][:, j] for k in keys])
            hi = float(np.nanpercentile(vals, 99.9)) * 1.05 or 1.0
            ax.plot([0, hi], [0, hi], color='0.45', lw=0.8, ls='--', zorder=1)
            for z, k in enumerate(keys):
                ax.scatter(b[:, j], r['b_hat'][k][:, j], s=2, alpha=0.4, lw=0,
                           color=_MB_COLORS[k], rasterized=True, zorder=2 + z)
            ax.set_xlim(0, hi)
            ax.set_ylim(0, hi)
            ax.set_aspect('equal')
            ax.locator_params(nbins=3)
            ax.set_title(_EL_TEX.get(e, e), loc='left', pad=2)
            ax.spines[['top', 'right']].set_visible(False)
        for k, ax in enumerate(axes.flat[:len(els)]):
            if k % ncols == 0:
                ax.set_ylabel(r'$\hat b$')
            if k + ncols >= len(els):
                ax.set_xlabel(r'$b$')
        handles = [Line2D([], [], marker='o', ls='', ms=6, color=_MB_COLORS[k], label=_MB_LABELS[k])
                   for k in keys]
        axes.flat[len(els)].legend(handles=handles, loc='center', frameon=False)
        fig.savefig(path, dpi=dpi)
        plt.close(fig)
    return path


def _jobs(args):
    if args.pair:
        for ckpt, bundle in args.pair:
            ckpt, bundle = Path(ckpt), Path(bundle)
            yield ckpt.stem, ckpt, bundle
        return
    for e in shipped_emulators(families=args.families, kinds=args.kinds):
        if e.bundle is None:
            print(f'[skip] {e.label}: no Test_subset bundle found for {e.checkpoint.name}')
            continue
        yield e.label, e.checkpoint, e.bundle


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--families', nargs='+', help='TrainedModels sub-directories to include')
    ap.add_argument('--kinds', nargs='+', choices=['isothermal', 'isentropic', 'openox'])
    ap.add_argument('--pair', nargs=2, action='append', metavar=('CHECKPOINT', 'BUNDLE'),
                    help='explicit checkpoint + Test_subset bundle (repeatable); '
                         'replaces the shipped-emulator discovery')
    ap.add_argument('--max-samples', type=int, default=None, help='random row cap per bundle')
    ap.add_argument('--seed', type=int, default=1337)
    ap.add_argument('--device', default='cpu', choices=['cpu', 'cuda'])
    ap.add_argument('--mass-balance', default='iterative', choices=['iterative', 'pinv'],
                    help='correction shown in blue (raw is always mass_balance=none)')
    ap.add_argument('--fmt', default='pdf', help='output format (pdf, png, svg)')
    ap.add_argument('--dpi', type=int, default=300, help='raster resolution of the scatter layers')
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_done = 0
    for label, ckpt, bundle in _jobs(args):
        t0 = time.time()
        emu = NN_MELTS(rebuild_MELTS_model(str(ckpt)), cuda=(args.device == 'cuda'),
                       mass_balance=args.mass_balance)
        r = evaluate_bulk_reconstruction(emu, bundle, max_samples=args.max_samples, seed=args.seed)
        paths = plot_bulk_reconstruction(r, OUT_DIR, label, fmt=args.fmt, dpi=args.dpi)
        # Overwrite the package's parity figure with the thesis-sized version.
        paths['parity'] = plot_parity_thesis(r, OUT_DIR / f'{label}_bulk_parity.{args.fmt}', dpi=args.dpi)
        write_summary(r, OUT_DIR / f'{label}_bulk_reconstruction.csv')
        s = r['summary']
        print(f'[done] {label}  ({time.time() - t0:.1f} s, n={r["meta"]["n_samples"]:,})  '
              + '  '.join(f"{k}: med|rel| {s.at[f'{k}_relerr_median_pct', 'all']:.2g}% "
                          f"p98 {s.at[f'{k}_relerr_p98_pct', 'all']:.2g}%" for k in r['b_hat'])
              + f"  -> {', '.join(p.name for p in paths.values())}")
        n_done += 1
    print(f'{n_done} emulator(s) written to {OUT_DIR}')


if __name__ == '__main__':
    main()
