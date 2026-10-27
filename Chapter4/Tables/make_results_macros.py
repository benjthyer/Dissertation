"""
LaTeX macros for the numbers quoted in the Chapter 4 Results text (phase presence and
mass conservation), so the prose follows the cached test results when a model is retrained.

Reads only cached CSVs (no ngibbs needed):

    Tables/quality/emulator_quality_<label>.csv           from make_quality_tables.py
    Figures/generated/*_bulk_reconstruction.csv           from make_bulk_reconstruction_figures.py

and writes Tables/results_macros.tex, which the chapter \\input s. Rerun this after
either of those scripts.

Usage
    python make_results_macros.py
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
QDIR = HERE / 'quality'
BULK_DIR = HERE.parent / 'Figures' / 'generated'

MELTS = ['MELTS102_Cr_iso', 'MELTS102_NoCr_iso', 'MELTS120_Cr_iso', 'MELTS120_NoCr_iso']
HEFESTO = ['HeFESToEarth_iso', 'HeFESToEarth_isen', 'HeFESToMars_iso', 'HeFESToMars_isen']
MARS = [m for m in HEFESTO if 'Mars' in m]
BULK_EXCLUDE = 'openox'          # the open-oxygen-system variants are not discussed in the text

# Phases the text groups together
MELTS_COMMON = ['clinopyroxene', 'orthopyroxene', 'plagioclase', 'olivine']
MELTS_RARE = ['graphite', 'alloy-solid', 'leucite', 'nepheline']
# HeFESTo phases quoted as reaching the precision/recall floor (those present in more than
# about 10% of test assemblages, minus the two exceptions the text discusses separately).
HEFESTO_GOOD = ['garnet', 'olivine', 'ringwoodite', 'bridgmanite', 'post-perovskite',
                'ferropericlase', 'ca-perovskite']

_Q = {}


def q(label):
    if label not in _Q:
        _Q[label] = pd.read_csv(QDIR / f'emulator_quality_{label}.csv', index_col='metric',
                                na_values='--')
    return _Q[label]


def vals(labels, phases, metrics):
    """All defined values of the given metrics for the given phases over the given models."""
    out = [q(l).at[m, p] for l in labels for p in phases for m in metrics if p in q(l).columns]
    return np.array([v for v in out if np.isfinite(v)])


# ---------------------------------------------------------------- formatting
def rng(v, nd=2, scale=1.0):
    lo, hi = np.min(v) * scale, np.max(v) * scale
    a, b = f'{lo:.{nd}f}', f'{hi:.{nd}f}'
    return a if a == b else f'{a}--{b}'


def ceil1(x):
    """Smallest one-decimal bound that is at least x (for 'x or less' / 'fewer than x')."""
    return f'{math.ceil(x * 10 - 1e-9) / 10:.1f}'


def sci(x):
    e = math.floor(math.log10(x))
    return rf'{x / 10 ** e:.0f}\times10^{{{e}}}'


# ---------------------------------------------------------------- macros
def presence_macros():
    both = ('precision', 'recall')
    m = {}
    m['PresLiquidRange'] = rng(vals(MELTS, ['melts-liquid'], both))
    m['PresMeltsCommonRange'] = rng(vals(MELTS, MELTS_COMMON, both))
    m['PresHefFloor'] = f'{vals(HEFESTO, HEFESTO_GOOD, both).min():.2f}'    # as shown in the table
    m['PresCaFerriteMarsIsenRecall'] = rng(vals(['HeFESToMars_isen'], ['ca-ferrite'], ['recall']))
    gamma_freq = vals(HEFESTO, ['gamma-iron'], ['proportion_in_dataset'])
    m['PresGammaFreqRange'] = rng(gamma_freq, 0, 100)
    gamma_rec = np.sort([vals([l], ['gamma-iron'], ['recall'])[0] for l in HEFESTO])[:2]
    m['PresGammaRecallLow'] = rng(gamma_rec)         # the two lowest recalls
    m['PresGraphitePrec'] = rng(vals(MELTS, ['graphite'], ['precision']))
    m['PresAlloyRange'] = rng(vals(MELTS, ['alloy-solid'], both))
    m['PresLeuciteRange'] = rng(vals(MELTS, ['leucite'], both))
    m['PresNephelinePrec'] = rng(vals(MELTS, ['nepheline'], ['precision']))
    m['PresRareFreqMax'] = f"{math.ceil(vals(MELTS, MELTS_RARE, ['proportion_in_dataset']).max() * 100 - 1e-9):.0f}"
    m['PresSpinelRecallNoCr'] = rng(vals(['MELTS120_NoCr_iso'], ['spinel'], ['recall']))
    m['PresAkimotoiteRange'] = rng(vals(HEFESTO, ['akimotoite'], both))
    m['PresAlphaIronRange'] = rng(vals(HEFESTO, ['alpha-iron'], both))
    m['PresEpsRecallMars'] = rng(vals(MARS, ['epsilon-iron'], ['recall']))
    m['PresEpsFreqMars'] = rng(vals(MARS, ['epsilon-iron'], ['proportion_in_dataset']))
    m['PresNalRecallMars'] = rng(vals(MARS, ['nal-phase'], ['recall']))
    return m


def mass_macros():
    files = sorted(f for f in BULK_DIR.glob('*_bulk_reconstruction.csv') if BULK_EXCLUDE not in f.name)
    s = pd.concat({f.stem: pd.read_csv(f, index_col='statistic', na_values='--')['all'] for f in files},
                  axis=1)
    row = lambda k: s.loc[k].to_numpy(float)
    return {
        'MassRawMedianRange': rng(row('raw_relerr_median_pct'), 1),
        'MassRawFracRange': rng(row('raw_frac_relerr_gt_1pct'), 0, 100),
        'MassMBMedian': sci(np.median(row('massbalanced_relerr_median_pct'))),
        'MassMBPNinetyNine': ceil1(row('massbalanced_relerr_p99_pct').max()),
        'MassMBFracGtOne': ceil1(row('massbalanced_frac_relerr_gt_1pct').max() * 100),
    }


def main():
    macros = {**presence_macros(), **mass_macros()}
    lines = ['% Generated by make_results_macros.py from the cached quality and bulk-reconstruction CSVs']
    lines += [rf'\newcommand{{\{k}}}{{{v}}}' for k, v in macros.items()]
    (HERE / 'results_macros.tex').write_text('\n'.join(lines) + '\n')
    for k, v in macros.items():
        print(f'{k:30s} {v}')


if __name__ == '__main__':
    main()
