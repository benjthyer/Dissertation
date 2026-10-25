"""
Combined wall-time benchmark: HeFESTo and MELTS emulators against their reference codes.

Reads saved CSVs (no model, no GPU needed) and writes generated/benchmark_combined_time.pdf.
Emulators on the CPU only.

    generated/performance_results.csv             performance_benchmarking.py (HeFESTo Earth emulator)
    generated/benchmark_results_ngibbs_melts.csv  benchmark_ptt_vs_ngibbs.py --part ngibbs
    generated/benchmark_results_ptt_scaling.csv   benchmark_ptt_vs_ngibbs.py --part ptt
    generated/benchmark_results_hefesto.csv       benchmark_hefesto.sh (run in WSL)

Curves
    HeFESTo emulator                  CPU Emulator (phase equilibria, mass balance, temperature)
    HeFESTo emulator + EOS            CPU Emulator + CPU Properties (+fast): every EOS term
    MELTS emulator                    MELTS102EmulatorCPU.ForwardMB (ptt_out only)
    MELTS emulator + PTT properties   the above plus calc_phase_props_MELTS_parallel
    HeFESTo, alphaMELTS via PTT       measured runs, marker = worker count, each continued as a
                                      thin line: a least-squares straight line (t = a + N / r)
                                      through the runs at that worker count, or t proportional
                                      to N through a single run; both run out to the largest N

N for PTT is the number of equilibria it returned (failures are not counted). Reference-code
CSVs that do not exist yet are skipped. The N = 16 HeFESTo emulator row is dropped: it is the
first call and carries one-off initialisation.

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
HEFESTO_EMU_CSV = OUT_DIR / 'performance_results.csv'
MELTS_EMU_CSV = OUT_DIR / 'benchmark_results_ngibbs_melts.csv'
PTT_CSV = OUT_DIR / 'benchmark_results_ptt_scaling.csv'
HEFESTO_CSV = OUT_DIR / 'benchmark_results_hefesto.csv'

COLOR = {'HeFESTo': '#2a78d6', 'MELTS': '#eb6834'}
WORKER_MARKER = {1: 'o', 4: 's', 8: '^'}


def _reference(ax, df, n_col, workers_col, color, n_max):
    """Measured runs (marker per worker count) and their linear extrapolation to n_max."""
    for w, g in df.groupby(workers_col):
        N, t = g[n_col].to_numpy(float), g['t_s'].to_numpy(float)
        ax.loglog(N, t, ls='none', marker=WORKER_MARKER.get(w, 'D'), ms=5, mfc=color, mec='white',
                  mew=0.8, color=color, zorder=3)
        if len(N) > 1:
            b, a = np.polyfit(N, t, 1)
        else:
            b, a = t[0] / N[0], 0.0
        Nx = np.geomspace(N.min(), n_max, 50)
        ax.loglog(Nx, a + b * Nx, color=color, lw=1.0, ls=':', alpha=0.8)
        print(f'  {color} {workers_col}={w}: {1 / b:.1f} assemblages/s'
              + (f', intercept {a:.1f} s' if len(N) > 1 else ''))


def main():
    hef = pd.read_csv(HEFESTO_EMU_CSV)
    hef = hef[hef['Batch Size'] > 16]
    N_h = hef['Batch Size'].to_numpy(float)
    t_emu_h = hef['CPU Emulator'].to_numpy(float)
    t_eos_h = t_emu_h + hef['CPU Properties (+fast)'].to_numpy(float)
    mel = pd.read_csv(MELTS_EMU_CSV)
    n_max = N_h.max()

    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=FIGSIZE, layout='constrained')
        ax.loglog(N_h, t_eos_h, color=COLOR['HeFESTo'], lw=2.0)
        ax.loglog(N_h, t_emu_h, color=COLOR['HeFESTo'], lw=2.0, ls='--')
        ax.loglog(mel['N'], mel['t_ngibbs_cpu_props_s'], color=COLOR['MELTS'], lw=2.0)
        ax.loglog(mel['N'], mel['t_ngibbs_cpu_s'], color=COLOR['MELTS'], lw=2.0, ls='--')

        workers = set()
        if HEFESTO_CSV.exists():
            df = pd.read_csv(HEFESTO_CSV)
            _reference(ax, df, 'assemblages', 'jobs', COLOR['HeFESTo'], n_max)
            workers |= set(df['jobs'])
        if PTT_CSV.exists():
            df = pd.read_csv(PTT_CSV)
            df = df[df['equilibria_returned'] > 0]
            _reference(ax, df, 'equilibria_returned', 'workers', COLOR['MELTS'], n_max)
            workers |= set(df['workers'])

        ax.set_xlabel('Number of assemblages, $N$')
        ax.set_ylabel('Wall time (s)')
        ax.set_xlim(N_h.min(), n_max)
        ax.grid(True, which='major', color='0.85', linewidth=0.6)
        ax.grid(True, which='minor', color='0.93', linewidth=0.4)

        ref = dict(ls=':', lw=1.0, marker='o', ms=5, mec='white')
        h_series = [
            Line2D([], [], color=COLOR['HeFESTo'], **ref, label='HeFESTo'),
            Line2D([], [], color=COLOR['HeFESTo'], lw=2.0, label='HeFESTo emulator + EOS'),
            Line2D([], [], color=COLOR['HeFESTo'], lw=2.0, ls='--', label='HeFESTo emulator'),
            Line2D([], [], color=COLOR['MELTS'], **ref, label='alphaMELTS via PTT'),
            Line2D([], [], color=COLOR['MELTS'], lw=2.0, label='MELTS emulator + PTT properties'),
            Line2D([], [], color=COLOR['MELTS'], lw=2.0, ls='--', label='MELTS emulator'),
        ]
        leg = ax.legend(handles=h_series, loc='upper left', framealpha=0.9, edgecolor='none',
                        handlelength=2.4)
        if workers:
            ax.add_artist(leg)
            h_w = [Line2D([], [], ls='none', marker=WORKER_MARKER.get(w, 'D'), ms=5, color='0.35',
                          label=f'{w} worker{"s" if w > 1 else ""}') for w in sorted(workers)]
            ax.legend(handles=h_w, loc='lower right', framealpha=0.9, edgecolor='none')
        path = OUT_DIR / 'benchmark_combined_time.pdf'
        fig.savefig(path, dpi=300)
        plt.close(fig)
    print(f'  -> {path}')


if __name__ == '__main__':
    main()
