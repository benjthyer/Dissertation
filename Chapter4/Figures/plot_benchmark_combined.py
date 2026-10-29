"""
Combined wall-time benchmark: HeFESTo and MELTS emulators against their reference codes.

Reads saved CSVs (no model, no GPU needed) and writes
    generated/benchmark_combined_time.pdf           laptop only, one panel
    generated/benchmark_combined_time_machines.pdf  laptop | desktop, shared axes
MELTS emulator on the CPU; HeFESTo emulator on the GPU (emulator alone, and with the
isomorphic EOS terms only), with the CPU time substituted where the GPU was not run
(N < 2^13 on the laptop).

Each machine's CSVs live in one directory (laptop: generated/, desktop:
source/desktop_performance/):

    performance_results.csv             performance_benchmarking.py (HeFESTo Earth emulator)
    benchmark_results_ngibbs_melts.csv  benchmark_ptt_vs_ngibbs.py --part ngibbs
    benchmark_results_ptt_scaling.csv   benchmark_ptt_vs_ngibbs.py --part ptt
    benchmark_results_hefesto.csv       benchmark_hefesto.sh (run in WSL)

Curves
    HeFESTo GPU emulator              GPU Emulator (phase equilibria, mass balance, temperature);
                                      CPU Emulator where the GPU was not run
    HeFESTo GPU emulator + iso. EOS   GPU Emulator + GPU Properties (isomorphic); CPU equivalents
                                      where the GPU was not run
    MELTS emulator                    MELTS102EmulatorCPU.ForwardMB (ptt_out only)
    MELTS emulator + PTT properties   the above plus calc_phase_props_MELTS_parallel
    HeFESTo, alphaMELTS via PTT       measured runs, marker = worker count, each continued as a
                                      thin line: a least-squares straight line (t = a + N / r)
                                      through the runs at that worker count, or t proportional
                                      to N through a single run or when the fitted a < 0; all
                                      run out to the largest N

N for PTT is the number of equilibria it returned (failures are not counted). CSVs that do not
exist are skipped. The N = 16 HeFESTo emulator row is dropped: it is the first call and carries
one-off initialisation.

Usage
    python plot_benchmark_combined.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from performance_benchmarking_plot_only import FIGSIZE, RC

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / 'generated'
MACHINES = {                                  # panel title -> directory holding its CSVs
    'Laptop (4 cores)': OUT_DIR,
    'Desktop (20 cores)': HERE / 'source' / 'desktop_performance',
}
HEFESTO_EMU_CSV = 'performance_results.csv'
MELTS_EMU_CSV = 'benchmark_results_ngibbs_melts.csv'
PTT_CSV = 'benchmark_results_ptt_scaling.csv'
HEFESTO_CSV = 'benchmark_results_hefesto.csv'

COLOR = {'HeFESTo': '#2a78d6', 'MELTS': '#eb6834'}
WORKER_MARKER = {1: 'o', 4: 's', 8: '^', 16: 'v', 20: 'D'}
# The laptop | desktop figure is printed at full text width, so its text (all but the tick
# labels) is about twice the size of the single-panel figure's.
MACHINES_RC = {**RC, 'axes.titlesize': 2 * RC['font.size'], 'axes.labelsize': 2 * RC['axes.labelsize'],
               'legend.fontsize': 2 * RC['legend.fontsize']}


def _reference(ax, df, n_col, workers_col, color, n_max):
    """Measured runs (marker per worker count) and their linear extrapolation to n_max."""
    for w, g in df.groupby(workers_col):
        N, t = g[n_col].to_numpy(float), g['t_s'].to_numpy(float)
        ax.loglog(N, t, ls='none', marker=WORKER_MARKER.get(w, 'P'), ms=5, mfc=color, mec='white',
                  mew=0.8, color=color, zorder=3)
        b, a = np.polyfit(N, t, 1) if len(N) > 1 else (t[0] / N[0], 0.0)
        if a < 0:   # a negative start-up time is unphysical and dives on a log axis
            b, a = (N @ t) / (N @ N), 0.0
        Nx = np.geomspace(N.min(), n_max, 50)
        ax.loglog(Nx, a + b * Nx, color=color, lw=1.0, ls=':', alpha=0.8)
        print(f'  {color} {workers_col}={w}: {1 / b:.1f} assemblages/s'
              + (f', intercept {a:.1f} s' if a else ''))


def _panel(ax, csv_dir, n_max):
    """Draw one machine's curves; returns the worker counts it plotted."""
    if (csv_dir / HEFESTO_EMU_CSV).exists():
        hef = pd.read_csv(csv_dir / HEFESTO_EMU_CSV)
        hef = hef[hef['Batch Size'] > 16]
        N_h = hef['Batch Size'].to_numpy(float)
        # GPU curves only. Where the GPU was not run (zero: below the 2^13-sample activation
        # threshold, or no CUDA device) the CPU time is substituted.
        ran = hef['GPU Emulator'].to_numpy(float) > 0
        t_emu = np.where(ran, hef['GPU Emulator'], hef['CPU Emulator'])
        t_iso = np.where(ran, hef['GPU Properties (isomorphic)'], hef['CPU Properties (isomorphic)'])
        ax.loglog(N_h, t_emu + t_iso, color=COLOR['HeFESTo'], lw=2.0)
        ax.loglog(N_h, t_emu, color=COLOR['HeFESTo'], lw=2.0, ls='--')
    if (csv_dir / MELTS_EMU_CSV).exists():
        mel = pd.read_csv(csv_dir / MELTS_EMU_CSV)
        ax.loglog(mel['N'], mel['t_ngibbs_cpu_props_s'], color=COLOR['MELTS'], lw=2.0)
        ax.loglog(mel['N'], mel['t_ngibbs_cpu_s'], color=COLOR['MELTS'], lw=2.0, ls='--')

    workers = set()
    if (csv_dir / HEFESTO_CSV).exists():
        df = pd.read_csv(csv_dir / HEFESTO_CSV)
        _reference(ax, df, 'assemblages', 'jobs', COLOR['HeFESTo'], n_max)
        workers |= set(df['jobs'])
    if (csv_dir / PTT_CSV).exists():
        df = pd.read_csv(csv_dir / PTT_CSV)
        df = df[df['equilibria_returned'] > 0]
        _reference(ax, df, 'equilibria_returned', 'workers', COLOR['MELTS'], n_max)
        workers |= set(df['workers'])

    ax.grid(True, which='major', color='0.85', linewidth=0.6)
    ax.grid(True, which='minor', color='0.93', linewidth=0.4)
    return workers


def _series_handles(two_columns=False):
    """Legend entries; two_columns lays them out HeFESTo | MELTS by padding the shorter column."""
    ref = dict(ls=':', lw=1.0, marker='o', ms=5, mec='white')
    hefesto = [
        Line2D([], [], color=COLOR['HeFESTo'], **ref, label='HeFESTo'),
        Line2D([], [], color=COLOR['HeFESTo'], lw=2.0, label='HeFESTo GPU emulator + iso. EOS'),
        Line2D([], [], color=COLOR['HeFESTo'], lw=2.0, ls='--', label='HeFESTo GPU emulator'),
    ]
    melts = [
        Line2D([], [], color=COLOR['MELTS'], **ref, label='alphaMELTS via PTT'),
        Line2D([], [], color=COLOR['MELTS'], lw=2.0, label='MELTS emulator + PTT properties'),
        Line2D([], [], color=COLOR['MELTS'], lw=2.0, ls='--', label='MELTS emulator'),
    ]
    if two_columns:
        melts += [Line2D([], [], ls='none', label='')] * (len(hefesto) - len(melts))
    return hefesto + melts


def _worker_handles(workers):
    return [Line2D([], [], ls='none', marker=WORKER_MARKER.get(w, 'P'), ms=5, color='0.35',
                   label=f'{w} worker{"s" if w > 1 else ""}') for w in sorted(workers)]


def main():
    hef = pd.read_csv(OUT_DIR / HEFESTO_EMU_CSV)
    N_h = hef.loc[hef['Batch Size'] > 16, 'Batch Size'].to_numpy(float)
    n_min, n_max = N_h.min(), N_h.max()

    with plt.rc_context(RC):
        # Laptop alone
        fig, ax = plt.subplots(figsize=FIGSIZE, layout='constrained')
        print('Laptop')
        workers = _panel(ax, OUT_DIR, n_max)
        ax.set_xlabel('Number of assemblages, $N$')
        ax.set_ylabel('Wall time (s)')
        ax.set_xlim(n_min, n_max)
        leg = ax.legend(handles=_series_handles(), loc='upper left', framealpha=0.9,
                        edgecolor='none', handlelength=2.4)
        if workers:
            ax.add_artist(leg)
            ax.legend(handles=_worker_handles(workers), loc='lower right', framealpha=0.9,
                      edgecolor='none')
        path = OUT_DIR / 'benchmark_combined_time.pdf'
        fig.savefig(path, dpi=300)
        plt.close(fig)
        print(f'  -> {path}')

    with plt.rc_context(MACHINES_RC):
        # Laptop | desktop, shared axes
        # The doubled legend gets its own row below the panels.
        legend_h = 2.0
        fig = plt.figure(figsize=(2 * FIGSIZE[0], FIGSIZE[1] + legend_h), layout='constrained')
        gs = fig.add_gridspec(2, 2, height_ratios=[FIGSIZE[1], legend_h])
        ax0 = fig.add_subplot(gs[0, 0])
        axs = [ax0, fig.add_subplot(gs[0, 1], sharex=ax0, sharey=ax0)]
        workers = set()
        for ax, (title, csv_dir) in zip(axs, MACHINES.items()):
            print(title)
            workers |= _panel(ax, csv_dir, n_max)
            ax.set_title(title)
            ax.set_xlabel('Assemblages, $N$')
        axs[0].set_ylabel('Wall time (s)')
        axs[0].set_xlim(n_min, n_max)
        axs[1].tick_params(labelleft=True)
        # One legend below the panels, so it hides no data: HeFESTo | MELTS | worker-count
        # columns. Matplotlib fills columns top-down in equal heights, so the series
        # columns are padded with blank entries to the length of the worker column.
        lax = fig.add_subplot(gs[1, :])
        lax.axis('off')
        series = _series_handles(two_columns=True)
        n_rows = max(len(series) // 2, len(workers))
        pad = [Line2D([], [], ls='none', label='')]
        hef_col, melts_col = series[:len(series) // 2], series[len(series) // 2:]
        handles = (hef_col + pad * (n_rows - len(hef_col)) + melts_col + pad * (n_rows - len(melts_col))
                   + _worker_handles(workers))
        lax.legend(handles=handles, loc='center', ncol=3, fontsize=1.3 * RC['legend.fontsize'],
                   frameon=False, handlelength=2.0, columnspacing=1.2)
        for ax, letter in zip(axs, 'ab'):
            ax.text(0.03, 0.97, f'({letter})', transform=ax.transAxes, ha='left', va='top',
                    fontsize=2 * RC['font.size'])
        path = OUT_DIR / 'benchmark_combined_time_machines.pdf'
        fig.savefig(path, dpi=300)
        plt.close(fig)
    print(f'  -> {path}')


if __name__ == '__main__':
    main()
