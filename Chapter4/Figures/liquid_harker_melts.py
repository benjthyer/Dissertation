"""
Liquid lines of descent of the MELTS Cr standard rocks: alphaMELTS vs nGibbs.

Harker diagrams (liquid SiO2 vs every other liquid oxide, wt%) for the three
deployment-test standard rocks (Bishop Tuff, Lherzolite, MORB) under isobaric
cooling. The alphaMELTS liquid (melts-liquid.tbl) is drawn as a solid line in
the rock's color; the nGibbs emulation is drawn as a black dotted line. nGibbs
runs the Cr sub-API's isothermal (P, T) emulator at the standard's own P-T path
and bulk composition, exactly as the ``sections_*_isothermal`` figures do.

Each rock is run with the MELTS version in ROCK_FAMILY, and compared with the
alphaMELTS standard run of that same version: Lherzolite and MORB with MELTS
1.0.2, Bishop Tuff with MELTS 1.2.0.

States outside the emulator's training range (e.g. Bishop Tuff below 700 C)
are left out of both curves. Rows where the liquid is below LIQ_MIN of the system mass are left out of both
curves: near the solidus the liquid composition is poorly constrained (and, for
the emulator, its mass is near zero), so its trace is not meaningful.

Usage
-----
    python liquid_harker_melts.py                        # -> generated/liquid_harker_MELTS.pdf
    python liquid_harker_melts.py --gpu
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from ngibbs_thesis_plots import (FAMILIES, FS, LAND_W, MELTS_STANDARDS, MELTS_VARIANT, _fonts, _save, _tex,
                                 _restrict_to_training)

LIQ_MIN = 0.01  # minimum liquid mass fraction of the system for a row to be drawn
OTHERS = ['TiO2', 'Al2O3', 'Cr2O3', 'Fe2O3', 'FeO', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5', 'H2O']
# rock -> FAMILIES key: the emulator and the alphaMELTS standard run it is compared with.
ROCK_FAMILY = {'BishopTuff': 'MELTS120', 'Lherzolite': 'MELTS102', 'MORB': 'MELTS102'}
# Categorical slots 1-3 of the dissertation's figure palette, in fixed order.
ROCK_COLORS = {'BishopTuff': '#2a78d6', 'Lherzolite': '#eb6834', 'MORB': '#1baf7a'}
ROCK_LABELS = {'BishopTuff': 'Bishop Tuff', 'Lherzolite': 'Lherzolite', 'MORB': 'MORB'}


def _melts_liquid(rock_dir, sysmain):
    """alphaMELTS liquid oxide wt% (rows with liquid >= LIQ_MIN), ordered by falling T."""
    from ngibbs.deployment_tests.melts_comparison import read_phase_tbl
    tbl = read_phase_tbl(rock_dir, 'melts-liquid')
    sys_mass = dict(zip(sysmain['index'].values.astype(int), sysmain['mass'].values))
    m_sys = np.array([sys_mass.get(int(i), np.nan) for i in tbl['Index']])
    keep = tbl['liq mass (gm)'].to_numpy(dtype=np.float64) / m_sys >= LIQ_MIN
    tbl = tbl.loc[keep].sort_values('T (C)', ascending=False)
    return {ox: tbl[f'wt% {ox}'].to_numpy(dtype=np.float64) for ox in ['SiO2'] + OTHERS}


def _ngibbs_liquid(api, emu, sysmain, bulk):
    """nGibbs isothermal emulation of the same P-T path: liquid oxide wt% (rows with
    liquid >= LIQ_MIN), ordered by falling T."""
    from ngibbs.deployment_tests.melts_comparison import _emulator_input_oxides, _bulk_oxide
    oxides = _emulator_input_oxides(emu)
    P, T = sysmain['Pressure'].values, sysmain['Temperature'].values
    table = np.column_stack([P, T] + [_bulk_oxide(bulk, ox) for ox in oxides])
    with torch.no_grad():
        res = api.ForwardMB(table.astype(np.float32),
                            headers=['Pressure(System_main)', 'Temperature(System_main)'] + oxides,
                            outputs=['ptt_out'])['ptt_out']
    mass = res['mass_g'].fillna(0.0)
    frac = mass['liquid1'].to_numpy(dtype=np.float64) / mass.sum(axis=1).to_numpy(dtype=np.float64)
    order = np.argsort(-T)
    keep = (frac >= LIQ_MIN)[order]
    liq = res['liquid1']
    return {ox: liq[f'{ox}_Liq'].to_numpy(dtype=np.float64)[order][keep] for ox in ['SiO2'] + OTHERS}


def main(out_dir: Path, use_gpu: bool):
    import ngibbs.engine.models as models
    from ngibbs.deployment_tests.melts_comparison import read_system_main, read_bulk_comp
    suffix = 'GPU' if use_gpu and torch.cuda.is_available() else 'CPU'

    curves = {}
    for rock, name in ROCK_FAMILY.items():
        fam = FAMILIES[name]
        api = getattr(models, f"{fam['singleton']}{suffix}")
        sub = api.cr if MELTS_VARIANT == 'Cr' else api.nocr
        rock_dir = MELTS_STANDARDS / fam['std_version'] / MELTS_VARIANT / rock
        if not rock_dir.exists():
            warnings.warn(f'missing MELTS standard {rock_dir}')
            continue
        emu = sub.isothermal_emulator
        sysmain = read_system_main(rock_dir)
        # Both curves are drawn only where the emulator was trained.
        path = _restrict_to_training(
            {'sysmain': sysmain, 'bulk': read_bulk_comp(rock_dir)}, emu,
            {'Pressure(System_main)': sysmain['Pressure'].values,
             'Temperature(System_main)': sysmain['Temperature'].values}, rock)
        curves[rock] = (_melts_liquid(rock_dir, path['sysmain']),
                        _ngibbs_liquid(api, emu, path['sysmain'], path['bulk']))
        print(f'  {rock} ({fam["label"]}): {len(curves[rock][0]["SiO2"])} alphaMELTS / '
              f'{len(curves[rock][1]["SiO2"])} nGibbs liquid rows')

    ncols = 4
    nrows = int(np.ceil((len(OTHERS) + 1) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(LAND_W, 5.4), squeeze=False, layout='constrained')
    for k, ox in enumerate(OTHERS):
        ax = axes[k // ncols][k % ncols]
        for rock, (gt, em) in curves.items():
            ax.plot(gt['SiO2'], gt[ox], color=ROCK_COLORS[rock], ls='-', lw=1.4)
            ax.plot(em['SiO2'], em[ox], color='k', ls=':', lw=1.6)
        ax.grid(True, alpha=0.25)
        ax.locator_params(nbins=4)
        _fonts(ax, title=_tex(ox))
    # The spare last panel carries the legend.
    for k in range(len(OTHERS), nrows * ncols):
        axes[k // ncols][k % ncols].axis('off')
    leg_ax = axes[-1][-1]
    handles = [Line2D([], [], color=ROCK_COLORS[r], lw=1.4,
                      label=f"{ROCK_LABELS[r]} (alphaMELTS {FAMILIES[ROCK_FAMILY[r]]['label'].split()[-1]})")
               for r in curves]
    handles += [Line2D([], [], color='k', ls=':', lw=1.6, label='nGibbs (isothermal)')]
    leg_ax.legend(handles=handles, loc='center', frameon=False, fontsize=FS['legend'])
    fig.supxlabel(f'{_tex("SiO2")} in liquid (wt%)', fontsize=FS['label'])
    fig.supylabel('oxide in liquid (wt%)', fontsize=FS['label'])
    _save(fig, out_dir / 'liquid_harker_MELTS.pdf')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out-dir', default=str(Path(__file__).resolve().parent / 'generated'))
    ap.add_argument('--gpu', action='store_true', help='use the GPU singletons when CUDA is available')
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    main(out, args.gpu)
