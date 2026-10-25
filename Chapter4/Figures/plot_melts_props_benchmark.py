"""
Wall time of the MELTS 1.0.2 phase-property calculation on an nGibbs-predicted assemblage table.

Reads generated/benchmark_results_ngibbs_props.csv, written by
petthermotools/Unit_tests/benchmark_ngibbs_props.py (fixed MORB, balanced P-T grid over
2-10 kbar and 900-1400 C, N = 128 ... 32768), and writes generated/benchmark_melts_props_time.pdf.

Curves (properties only; the emulator forward pass is not included)
    vectorized        nGibbs' internal vectorized MELTS EOS: t_internal_s - t_ngibbs_s, since
                      ForwardMB(outputs=['ptt_props']) times the forward pass and the EOS together
    sequential        PetThermoTools calc_phase_props_MELTS: alphaMELTS supCalc, one state and
                      phase at a time, in one process
    sequential, parallel  calc_phase_props_MELTS_parallel: the same calls split across
                      PetThermoTools' default worker processes

Usage
    python plot_melts_props_benchmark.py
"""
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from performance_benchmarking_plot_only import FIGSIZE, RC

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / 'generated'
CSV = OUT_DIR / 'benchmark_results_ngibbs_props.csv'

# (label, time column or callable, colour)
SERIES = (
    ('Vectorized (nGibbs)', lambda d: d['t_internal_s'] - d['t_ngibbs_s'], '#2a78d6'),
    ('Sequential, 1 process (alphaMELTS)', lambda d: d['t_serial_s'], '#eb6834'),
    ('Sequential, parallel processes (alphaMELTS)', lambda d: d['t_parallel_s'], '#1baf7a'),
)


def main():
    d = pd.read_csv(CSV)
    with plt.rc_context(RC):
        fig, ax = plt.subplots(figsize=FIGSIZE, layout='constrained')
        for label, t, color in SERIES:
            ax.loglog(d['N'], t(d), color=color, lw=2.0, marker='o', ms=4, mec='white', label=label)
        ax.set_xlabel('Number of assemblages, $N$')
        ax.set_ylabel('Wall time (s)')
        ax.set_xlim(d['N'].min(), d['N'].max())
        ax.grid(True, which='major', color='0.85', linewidth=0.6)
        ax.grid(True, which='minor', color='0.93', linewidth=0.4)
        ax.legend(loc='upper left', framealpha=0.9, edgecolor='none', handlelength=2.4)
        path = OUT_DIR / 'benchmark_melts_props_time.pdf'
        fig.savefig(path, dpi=300)
        plt.close(fig)
    print(f'  -> {path}')


if __name__ == '__main__':
    main()
