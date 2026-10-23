"""
Plot the HeFESTo emulator benchmark from a saved CSV (no model, no GPU needed).

Reads generated/performance_results1.csv, written by performance_benchmarking.py
(columns: Batch Size, GPU Emulator, CPU Emulator, and GPU/CPU Properties
(isomorphic | metamorphic | +fast)), and writes 300 dpi PDFs to generated/:

    performance_results.pdf                         wall time vs number of assemblages
    performance_results_assemblages_per_second.pdf  throughput vs number of assemblages
    performance_results_relative.pdf                speed-up relative to a sequential
                                                    reference rate (BURNMAN_S_PER_ASSEMBLAGE)

GPU rows were skipped by the benchmark below 8000 assemblages (written as 0) and are
masked here, as are any NaN rows from an interrupted run.

Usage
    python performance_benchmarking_plot_only.py
    python performance_benchmarking_plot_only.py --csv generated/performance_results.csv
    python performance_benchmarking_plot_only.py --csv generated/performance_results.csv --buildup
        # five cumulative wall-time figures: GPU emulator; + CPU emulator;
        # + CPU isomorphic; + metamorphic; + fast  (performance_buildup_*.pdf)
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / 'generated'

VARIANTS = ('isomorphic', 'metamorphic', '+fast')
# Colour = what is being timed (emulator, then the three property variants in order of
# cost), sampled from a continuous colormap; line style = device.
CALCS = ('emulator',) + VARIANTS
CALC_LABEL = {'emulator': 'emulator (phase equilibria)', 'isomorphic': 'EOS: isomorphic',
              'metamorphic': 'EOS: metamorphic', '+fast': 'EOS: +fast'}
CMAP = matplotlib.colormaps['viridis']
CALC_COLOR = {c: CMAP(x) for c, x in zip(CALCS, np.linspace(0.0, 0.82, len(CALCS)))}
DEVICE_STYLE = {'GPU': '-', 'CPU': ':'}
# Printed size (inches) and font sizes (points) as they appear in the thesis.
FIGSIZE = (5.0, 3.9)
RC = {'font.size': 10, 'axes.labelsize': 10.5, 'xtick.labelsize': 9.5, 'ytick.labelsize': 9.5,
      'legend.fontsize': 9, 'pdf.fonttype': 42}
# Reference sequential rate used for the relative speed-up panel (10 s per 4000 assemblages).
BURNMAN_S_PER_ASSEMBLAGE = 10 / 4000


def _valid(y):
    y = np.asarray(y, dtype=float)
    return np.isfinite(y) & (y > 0)


def _series(data):
    """(device, calc, wall-time array) for every column present."""
    out = []
    for dev in ('GPU', 'CPU'):
        for calc in CALCS:
            col = f'{dev} Emulator' if calc == 'emulator' else f'{dev} Properties ({calc})'
            if col in data:
                out.append((dev, calc, data[col].to_numpy(float)))
    return out


def _plot(N, series, ytrans, ylabel, path, hline=None):
    from matplotlib.lines import Line2D
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=FIGSIZE, layout='constrained')
        for dev, calc, t in series:
            m = _valid(t)
            ax.loglog(N[m], ytrans(N[m], t[m]), color=CALC_COLOR[calc], ls=DEVICE_STYLE[dev],
                      lw=1.8 if dev == 'GPU' else 2.0)
        if hline is not None:
            ax.axhline(hline, color='k', lw=1.0)
        ax.set_xlabel('Number of assemblages, $N$')
        ax.set_ylabel(ylabel)
        ax.set_xlim(N.min(), N.max())
        ax.grid(True, which='major', color='0.85', linewidth=0.6)
        ax.grid(True, which='minor', color='0.93', linewidth=0.4)
        calcs = [c for c in CALCS if any(s[1] == c for s in series)]
        h_calc = [Line2D([], [], color=CALC_COLOR[c], lw=2.5, label=CALC_LABEL[c]) for c in calcs]
        h_dev = [Line2D([], [], color='0.3', ls=DEVICE_STYLE[d], lw=2.0, label=d) for d in ('GPU', 'CPU')]
        leg = ax.legend(handles=h_calc, loc='upper left', frameon=False, handlelength=1.6)
        ax.add_artist(leg)
        ax.legend(handles=h_dev, loc='lower right', frameon=False, handlelength=2.4)
        fig.savefig(path, dpi=300)
        plt.close(fig)
    print(f'  -> {path}')


# (device, calc) curves added at each step of the build-up figures, in order.
BUILD_STEPS = (('GPU', 'emulator'), ('CPU', 'emulator'), ('CPU', 'isomorphic'),
               ('CPU', 'metamorphic'), ('CPU', '+fast'))


def _plot_buildup(N, series, out_dir, hline=None):
    """One wall-time figure per step, each adding one curve to the last.

    Axis limits are fixed from the full data so the panels overlay exactly when
    flipped through in slides.
    """
    lookup = {(d, c): t for d, c, t in series}
    steps = [s for s in BUILD_STEPS if s in lookup]
    ally = np.concatenate([lookup[s][_valid(lookup[s])] for s in steps])
    ylim = (ally.min() / 1.5, ally.max() * 1.5)
    for k in range(1, len(steps) + 1):
        shown = steps[:k]
        dev, calc = shown[-1]
        path = out_dir / f'performance_buildup_{k}_{dev}_{calc.strip("+")}.pdf'
        with plt.rc_context(RC):
            fig, ax = plt.subplots(figsize=FIGSIZE, layout='constrained')
            for d, c in shown:
                t = lookup[(d, c)]
                m = _valid(t)
                ax.loglog(N[m], t[m], color=CALC_COLOR[c], ls=DEVICE_STYLE[d],
                          lw=1.8 if d == 'GPU' else 2.0,
                          label=f'{d} {CALC_LABEL[c]}')
            if hline is not None:
                ax.axhline(hline, color='k', lw=1.0)
            ax.set_xlabel('Number of assemblages, $N$')
            ax.set_ylabel('Wall time (s)')
            ax.set_xlim(N.min(), N.max())
            ax.set_ylim(*ylim)
            ax.grid(True, which='major', color='0.85', linewidth=0.6)
            ax.grid(True, which='minor', color='0.93', linewidth=0.4)
            ax.legend(loc='upper left', frameon=False, handlelength=2.4)
            fig.savefig(path, dpi=300)
            plt.close(fig)
        print(f'  -> {path}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--buildup', action='store_true',
                    help='write the step-by-step build-up wall-time figures instead of the usual three')
    ap.add_argument('--csv', type=Path, default=OUT_DIR / 'performance_results1.csv')
    ap.add_argument('--out-dir', type=Path, default=OUT_DIR)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(args.csv)
    N = data['Batch Size'].to_numpy(float)
    series = _series(data)
    if args.buildup:
        _plot_buildup(N, series, args.out_dir)
        return
    _plot(N, series, lambda n, t: t, 'Wall time (s)', args.out_dir / 'performance_results.pdf')
    _plot(N, series, lambda n, t: n / t, 'Assemblages per second',
          args.out_dir / 'performance_results_assemblages_per_second.pdf')
    _plot(N, series, lambda n, t: n * BURNMAN_S_PER_ASSEMBLAGE / t, 'Speed-up vs. sequential reference',
          args.out_dir / 'performance_results_relative.pdf', hline=1)


if __name__ == '__main__':
    main()
