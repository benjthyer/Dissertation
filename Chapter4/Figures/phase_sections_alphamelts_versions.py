"""
Phase sections of the MELTS Cr standard rocks: alphaMELTS 2.3.1 vs 2.3.2 vs nGibbs.

One figure per MELTS version (1.0.2, 1.2.0), laid out like
``sections_phase_<model>_isothermal.pdf`` but with three columns: the
standards as run by alphaMELTS 2.3.1 (MELTSIsobaricStandards), the same inputs
run by alphaMELTS 2.3.2 (MELTSIsobaricStandards232), and the closed-system
isothermal emulator given each standard's P, T and bulk composition. Both
alphaMELTS versions share the same P-T path and bulk composition, so the
emulator column applies to either. Only states inside the emulator's training
range are shown.

Also prints, per rock, the mean phase-assemblage mismatch between each pair of
columns: half the summed |difference| of phase mass fractions (0 = identical
assemblage, 1 = no phase in common), averaged over the shown states.

Usage
-----
    python phase_sections_alphamelts_versions.py    # -> generated/sections_phase_alphamelts_versions_<model>.pdf
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ngibbs_thesis_plots import (FAMILIES, LAND_W, MELTS_STANDARDS, MELTS_VARIANT, _fonts, _save,
                                 _restrict_to_training, subset_rows)

MELTS_STANDARDS_232 = MELTS_STANDARDS.parent / 'MELTSIsobaricStandards232'
FAMILY_NAMES = ('MELTS102', 'MELTS120')
HEADS = ('alphaMELTS 2.3.1', 'alphaMELTS 2.3.2', 'Emulator (isothermal)')


def _mismatch(a, b):
    """Mean over states of half the summed |phase mass fraction difference|."""
    phases = set(a) | set(b)
    n = len(next(iter(a.values())))
    diff = sum(np.abs(a.get(p, np.zeros(n)) - b.get(p, np.zeros(n))) for p in phases)
    return float(np.mean(0.5 * diff))


def version_sections(name, api, out_dir):
    from ngibbs.deployment_tests.melts_comparison import (
        ROCKS, read_system_main, read_bulk_comp, _gt_phase_mass_fractions,
        _emulator_phase_mass_fractions, _BARS_PER_GPA,
    )
    from ngibbs.deployment_tests._melts_phase_plotting import (
        MELTS_PHASE_STACK_ORDER, melts_phase_colors, build_ordered_melts_phases,
        draw_melts_phase_stack,
    )
    fam = FAMILIES[name]
    sub = api.cr if MELTS_VARIANT == 'Cr' else api.nocr
    emu = sub.isothermal_emulator
    ordered = build_ordered_melts_phases(MELTS_PHASE_STACK_ORDER)
    colors = melts_phase_colors()
    header = 'Temperature(System_main)'

    rows = []
    for rock in ROCKS:
        dirs = [root / fam['std_version'] / MELTS_VARIANT / rock for root in (MELTS_STANDARDS, MELTS_STANDARDS_232)]
        if not all(d.exists() for d in dirs):
            warnings.warn(f'missing MELTS standard for {rock}: {dirs}')
            continue
        # Both versions step down the same P-T path from the same bulk composition, but a
        # run can stop early (e.g. MELTS 1.2.0 Lherzolite ends near 1330 C, one step apart
        # between versions), so only the temperatures both runs reached are compared.
        runs = [(rock_dir, read_system_main(rock_dir)) for rock_dir in dirs]
        T_both = np.intersect1d(*(sm['Temperature'].values for _, sm in runs))
        fracs = []
        for rock_dir, sm in runs:
            keep = np.isin(sm['Temperature'].values, T_both)
            if not keep.all():
                print(f'  {rock} ({rock_dir.parents[2].name}): {int((~keep).sum())} step(s) the other '
                      'alphaMELTS version did not reach left out')
            fracs.append(subset_rows(_gt_phase_mass_fractions(rock_dir, sm['index'].values.astype(int),
                                                              sm['mass'].values), keep))
        # The 2.3.1 run supplies the conditions for the training-range cut and the emulator.
        rock_dir, sysmain = runs[0]
        keep = np.isin(sysmain['Temperature'].values, T_both)
        sysmain = subset_rows(sysmain, keep)
        P_bar = sysmain['Pressure'].values
        d = dict(title=f"{rock}, {P_bar[0] / _BARS_PER_GPA:.3g} GPa", T_C=sysmain['Temperature'].values,
                 P_bar=P_bar, bulk=subset_rows(read_bulk_comp(rock_dir), keep), v231=fracs[0], v232=fracs[1])
        d = _restrict_to_training(d, emu, {'Pressure(System_main)': d['P_bar'], header: d['T_C']}, d['title'])
        d['em'] = _emulator_phase_mass_fractions(api, emu, d['P_bar'], d['T_C'], header, d['bulk'])
        print(f"  {d['title']}: mismatch 2.3.1|2.3.2 {_mismatch(d['v231'], d['v232']):.3f}, "
              f"2.3.1|emulator {_mismatch(d['v231'], d['em']):.3f}, "
              f"2.3.2|emulator {_mismatch(d['v232'], d['em']):.3f}")
        rows.append(d)

    fig, axes = plt.subplots(len(rows), 3, figsize=(LAND_W * 0.85, 2.15 * len(rows) + 0.3),
                             squeeze=False, sharex='row', layout='constrained')
    for r, d in enumerate(rows):
        for c, key in enumerate(('v231', 'v232', 'em')):
            ax = axes[r][c]
            draw_melts_phase_stack(ax, d[key], d['T_C'], ordered, colors, '')
            ax.set_xlabel('T (°C)' if r == len(rows) - 1 else '')
            ax.set_ylabel(f"{d['title']}\nmass fraction" if c == 0 else '')
            if c > 0:
                ax.tick_params(labelleft=False)
            _fonts(ax, title=HEADS[c] if r == 0 else '')
    fig.suptitle(f"{fam['label']} ({MELTS_VARIANT})", fontsize=10)
    _save(fig, out_dir / f'sections_phase_alphamelts_versions_{name}.pdf')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out-dir', default=str(Path(__file__).resolve().parent / 'generated'))
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    import ngibbs.engine.models as models
    for name in FAMILY_NAMES:
        print(f'[alphaMELTS versions] {FAMILIES[name]["label"]}')
        version_sections(name, getattr(models, f"{FAMILIES[name]['singleton']}CPU"), out)
