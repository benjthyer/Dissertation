"""
Thesis summary plots built entirely on the installed ``ngibbs`` package.

Nothing here touches ``src/``, ``builder`` or ``scripts`` on sys.path -- every
import is ``ngibbs.<...>``, and every data file is located relative to the
installed package (``ngibbs.engine`` / ``ngibbs.deployment_tests``).

Produces, under ``--out-dir`` (default: ``generated/`` next to this file), as
300 dpi PDFs:

1. Training/test-data density clouds (one figure per data family), drawn from
   the ``*_Test_subset*.tar.gz`` bundles the deployment tests evaluate on,
   with the deployment-test standard rocks overlaid as red 'x':

     density_PT_HeFESToMars.pdf        P-T cloud (NPT + NPS subsets pooled)
     density_PT_HeFESToEarth.pdf
     density_Harker_HeFESToMars.pdf    Si vs every other element (cation mol frac)
     density_Harker_HeFESToEarth.pdf
     density_Harker_MELTS102.pdf       SiO2 vs every other oxide (oxide wt frac),
     density_Harker_MELTS120.pdf       closed-system Cr bundles (NPT + NPS pooled)

2. Phase and property sections for the deployment-test standard rocks, one
   figure per model x pathway, one row per standard rock -- the same layout as
   scripts/phase_comparison.py and scripts/property_comparison.py:

     sections_phase_<model>_<pathway>.pdf     GT phase stack | emulator phase stack
     sections_property_<model>_<pathway>.pdf  one column per property: GT (k-),
                                              emulator (r--), GT assemblage (b:);
                                              isentropic adds a T panel (GT vs
                                              temperature model)
                                              HeFESTo: rho, VP, VS, S, Cp, KS, alpha vs P
                                                       (assemblages through the internal EOS)
                                              MELTS:   rho, S, Cp, V, H vs T (assemblages
                                                       through alphaMELTS's phase-property
                                                       calculator, via PetThermoTools)

   <model> in {HeFESToMars, HeFESToEarth, MELTS102, MELTS120}; MELTS uses the
   Cr sub-API and the Cr standards. <pathway> in {isothermal, isentropic}.
   MELTS property sections are made only for a family's ``property_pathways``
   (MELTS 1.0.2 isothermal).

3. The HeFESTo Earth DMM adiabat evaluated with successively more terms of the
   nGibbs HeFESTo EOS (isomorphic, + metamorphic, + fast), one row per level,
   same columns and line styles as the property sections:

     eos_terms_HeFESToEarth_DMM.pdf

Usage
-----
    python ngibbs_thesis_plots.py                         # -> generated/
    python ngibbs_thesis_plots.py --out-dir thesis_plots
    python ngibbs_thesis_plots.py --only density          # no model loading
    python ngibbs_thesis_plots.py --only sections --gpu
    python ngibbs_thesis_plots.py --only eos_terms
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import ngibbs.engine as _ngibbs_engine
import ngibbs.deployment_tests as _ngibbs_dt
from ngibbs.deployment_tests.training_coverage import (
    _read_bundle_arrays,
    _bundle_ps_t,
    _bundle_composition,
    _density_heatmap,
    hefesto_standard_points,
    melts_standard_points,
)

ENGINE_DIR = Path(_ngibbs_engine.__file__).resolve().parent
TRAINED_DIR = ENGINE_DIR / 'TrainedModels'
DT_DIR = Path(_ngibbs_dt.__file__).resolve().parent
HEFESTO_STANDARDS = DT_DIR / 'HeFESToAdiabatStandards'
MELTS_STANDARDS = DT_DIR / 'MELTSIsobaricStandards'

MELTS_VARIANT = 'Cr'
PATHWAYS = ('isothermal', 'isentropic')

# --------------------------------------------------------------------------- #
# data families
# --------------------------------------------------------------------------- #
# name -> (model sub-dir, bundle glob(s), composition space, standards)
FAMILIES = {
    'HeFESToMars': dict(
        model_dir='HeFESToMars', label='HeFESTo Mars',
        bundles=['HeFESToMars_NPT_Test_subset*.tar.gz', 'HeFESToMars_NPS_Test_subset*.tar.gz'],
        space='elements', singleton='HeFESToMarsEmulator', std_planet='Mars'),
    'HeFESToEarth': dict(
        model_dir='HeFESToEarth', label='HeFESTo Earth',
        bundles=['HeFESToEarth_NPT_Test_subset*.tar.gz', 'HeFESToEarth_NPS_Test_subset*.tar.gz'],
        space='elements', singleton='HeFESToEmulator', std_planet='Earth',
        section_rocks=['BASALTadiabat', 'DMMadiabat', 'SILICAadiabat']),
    'MELTS102': dict(
        model_dir='102', label='MELTS 1.0.2',
        bundles=[f'102Closed_{MELTS_VARIANT}_NPT_Test_subset*.tar.gz',
                 f'102Closed_{MELTS_VARIANT}_NPS_Test_subset*.tar.gz'],
        space='oxides', singleton='MELTS102Emulator', std_version='102',
        property_pathways=('isothermal',)),
    'MELTS120': dict(
        model_dir='120', label='MELTS 1.2.0',
        bundles=[f'120Closed_{MELTS_VARIANT}_NPT_Test_subset*.tar.gz',
                 f'120Closed_{MELTS_VARIANT}_NPS_Test_subset*.tar.gz'],
        space='oxides', singleton='MELTS120Emulator', std_version='120',
        property_pathways=()),
}


def _find_bundle(model_dir: str, pattern: str) -> Optional[Path]:
    """Same lookup order as EmulatorAPI: the model's own directory first,
    then anywhere under ngibbs/deployment_tests."""
    hits = sorted((TRAINED_DIR / model_dir).glob(pattern))
    if not hits:
        hits = sorted(DT_DIR.rglob(pattern))
    if not hits:
        warnings.warn(f'No test bundle matching {pattern!r} for {model_dir}')
        return None
    return hits[-1]


def _load_family(fam: dict):
    """Pool every bundle of a family -> (P, T, comp dict, oxide labels)."""
    P_all, T_all, comps = [], [], []
    for pat in fam['bundles']:
        b = _find_bundle(fam['model_dir'], pat)
        if b is None:
            continue
        print(f'  reading {b.name}')
        feats, free, bounds, meta = _read_bundle_arrays(b)
        P, _S, T = _bundle_ps_t(feats, free, bounds, meta)
        comp = _bundle_composition(feats, meta, fam['space'])
        P_all.append(P)
        T_all.append(T if T is not None else np.full_like(P, np.nan))
        comps.append(comp)
    if not comps:
        raise FileNotFoundError(f"No test bundles found for {fam['label']}")
    keys = [k for k in comps[0] if all(k in c for c in comps[1:])]
    comp = {k: np.concatenate([c[k] for c in comps]) for k in keys}
    return np.concatenate(P_all), np.concatenate(T_all), comp, keys


# --------------------------------------------------------------------------- #
# 1. density clouds
# --------------------------------------------------------------------------- #
# Figures are drawn at the size they are printed in the thesis (text width 5.5 in;
# landscape pages 9 in), so the font sizes below are the printed sizes in points.
TEXT_W = 5.5
LAND_W = 9.0
FS = dict(title=9.5, label=9, tick=8, inplot=8, legend=8.5)


def _fonts(ax, title=None, xlabel=True, ylabel=True):
    """Re-apply the printed font sizes to an axis drawn by an ngibbs helper."""
    if title is not None:
        ax.set_title(title, fontsize=FS['title'])
    else:
        ax.title.set_fontsize(FS['title'])
    if not xlabel:
        ax.set_xlabel('')
    if not ylabel:
        ax.set_ylabel('')
    ax.xaxis.label.set_fontsize(FS['label'])
    ax.yaxis.label.set_fontsize(FS['label'])
    ax.tick_params(labelsize=FS['tick'])
    ax.xaxis.get_offset_text().set_fontsize(FS['tick'])
    ax.yaxis.get_offset_text().set_fontsize(FS['tick'])
    for t in ax.texts:
        t.set_fontsize(FS['inplot'])
    if ax.get_legend() is not None:
        ax.get_legend().remove()


def _tex(label):
    """'Al2O3' -> 'Al$_2$O$_3$'."""
    import re as _re
    if label in ('Fe3', 'Fe2'):
        return f'Fe$^{{{label[-1]}+}}$'
    return _re.sub(r'(\d+)', r'$_{\1}$', label)


def plot_pt_density(name, fam, P, T, std, out_dir):
    # Printed at half the text width (one of two subfigures).
    fig, ax = plt.subplots(figsize=(0.49 * TEXT_W, 0.49 * TEXT_W * 0.95), layout='constrained')
    _density_heatmap(ax, T, P, 'T (K)', 'P (GPa)', '', bins=80, standard_xy=None)
    if std is not None:
        # Each standard rock is a path in P-T: draw it as a line, not a scatter of points.
        P_std, T_std, rock = np.asarray(std[0]), np.asarray(std[1]), np.asarray(std[4])
        for r in dict.fromkeys(rock):
            m = (rock == r) & np.isfinite(P_std) & np.isfinite(T_std)
            o = np.argsort(P_std[m])
            ax.plot(T_std[m][o], P_std[m][o], color='red', lw=1.4, zorder=5)
    ax.invert_yaxis()
    ax.locator_params(axis='x', nbins=5)
    _fonts(ax, title=f"n = {np.isfinite(T).sum():,}")
    path = out_dir / f'density_PT_{name}.pdf'
    fig.savefig(path, dpi=300, facecolor='white')
    plt.close(fig)
    print(f'  -> {path}')


# Per-family axis overrides for the Harker panels (y = the non-pivot component).
# HARKER_YMAX caps the y axis (rows above the cap are left out, so the histogram bins span
# only the shown range); HARKER_LOGY puts y on a log axis (rows with y <= 0 are left out).
HARKER_YMAX = {'MELTS102': {'Cr2O3': 0.02},
               'MELTS120': {'P2O5': 0.01, 'Cr2O3': 0.02}}
HARKER_LOGY = {'MELTS120': {'CO2'}}


def _harker_panel_data(name, other, x, y, sxy):
    """Apply HARKER_YMAX / HARKER_LOGY to one panel: returns x, y, bins, standards, ylim, log."""
    ymax = HARKER_YMAX.get(name, {}).get(other)
    logy = other in HARKER_LOGY.get(name, set())
    x, y = np.asarray(x, float), np.asarray(y, float)
    keep = np.isfinite(x) & np.isfinite(y)
    if ymax is not None:
        keep &= y <= ymax
    if logy:
        keep &= y > 0
    x, y = x[keep], y[keep]
    if sxy is not None:
        sx, sy = np.asarray(sxy[0], float), np.asarray(sxy[1], float)
        sk = np.isfinite(sx) & np.isfinite(sy)
        if ymax is not None:
            sk &= sy <= ymax
        if logy:
            sk &= sy > 0
        sxy = (sx[sk], sy[sk])
    bins, ylim = 50, None
    if ymax is not None or logy:
        xb = np.linspace(x.min(), x.max(), 51)
        if logy:
            yb = np.geomspace(y.min(), y.max(), 51)
        else:
            yb = np.linspace(0.0, ymax, 51)
            ylim = (0.0, ymax)
        bins = [xb, yb]
    return x, y, bins, sxy, ylim, logy


def plot_harker_density(name, fam, comp, std_comp, out_dir, ncols=4):
    pivot = 'SiO2' if fam['space'] == 'oxides' else 'Si'
    unit = 'oxide wt frac.' if fam['space'] == 'oxides' else 'cation mol frac.'
    others = [k for k in comp if k != pivot]
    nrows = int(np.ceil(len(others) / ncols))
    # MELTS (oxide) Harker grids have more panels and get a whole landscape page each;
    # the HeFESTo (element) grids print at the text width on a portrait page.
    figsize = (LAND_W, 4.6) if fam['space'] == 'oxides' else (TEXT_W, 1.45 * nrows + 0.35)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, squeeze=False, layout='constrained')
    for k, other in enumerate(others):
        ax = axes[k // ncols][k % ncols]
        sxy = None
        if std_comp is not None and pivot in std_comp and other in std_comp:
            sxy = (std_comp[pivot], std_comp[other])
        x, y, bins, sxy, ylim, logy = _harker_panel_data(name, other, comp[pivot], comp[other], sxy)
        _density_heatmap(ax, x, y, '', '', '', bins=bins, standard_xy=sxy)
        if logy:
            ax.set_yscale('log')
            ax.locator_params(axis='x', nbins=3)
        else:
            ax.locator_params(nbins=3)
        if ylim is not None:
            ax.set_ylim(*ylim)
        _fonts(ax, title=_tex(other))
    for k in range(len(others), nrows * ncols):
        axes[k // ncols][k % ncols].axis('off')
    n = len(next(iter(comp.values())))
    print(f'  {fam["label"]}: n = {n:,}')
    fig.supxlabel(f'{_tex(pivot)} ({unit})', fontsize=FS['label'])
    fig.supylabel(unit, fontsize=FS['label'])
    path = out_dir / f'density_Harker_{name}.pdf'
    fig.savefig(path, dpi=300, facecolor='white')
    plt.close(fig)
    print(f'  -> {path}')


def run_density(out_dir: Path):
    for name, fam in FAMILIES.items():
        print(f'[density] {fam["label"]}')
        P, T, comp, keys = _load_family(fam)
        if fam['space'] == 'elements':
            std = hefesto_standard_points(HEFESTO_STANDARDS / fam['std_planet'])
            plot_pt_density(name, fam, P, T, std, out_dir)
        else:
            std = melts_standard_points(MELTS_STANDARDS / fam['std_version'],
                                        variant=MELTS_VARIANT, oxide_cols=keys)
        plot_harker_density(name, fam, comp, std[3] if std is not None else None, out_dir)


# --------------------------------------------------------------------------- #
# 2. sections -- shared plotting helpers (layout mirrors scripts/
#    phase_comparison.py and scripts/property_comparison.py)
# --------------------------------------------------------------------------- #
def _np(x) -> np.ndarray:
    if hasattr(x, 'detach'):
        x = x.detach().cpu().numpy()
    return np.asarray(x, dtype=np.float64).reshape(-1)


_PATHWAY_LABEL = {'isothermal': 'Isothermal (P, T)', 'isentropic': 'Isentropic (P, S)'}


def training_mask(emu, conds: Dict[str, np.ndarray]) -> np.ndarray:
    """True where every condition input of ``emu`` lies inside its training range.
    ``conds`` maps each of the emulator's condition feature names (as in its
    ml_indexer.featureNames, e.g. 'Temperature(System_main)') to the values that
    will be passed under that header, in the emulator's own units. The bounds are
    the ones its TrainingRangeWarning checks against (the bundle's stats.txt)."""
    names = list(emu._bound_names[:emu.feature_offset])
    if set(names) != set(conds):
        raise ValueError(f'training_mask needs exactly the condition features {names}, got {list(conds)}')
    keep = np.ones(len(next(iter(conds.values()))), dtype=bool)
    for name, values in conds.items():
        lo, hi = emu._bound_ranges[names.index(name)]
        values = np.asarray(values, dtype=np.float64)
        keep &= (values >= lo) & (values <= hi)
    return keep


def subset_rows(obj, keep: np.ndarray):
    """Restrict every per-row array/table in ``obj`` (recursing into dicts) to the
    rows in ``keep``; anything not of length len(keep) (scalars, paths, titles,
    per-rock constants) is passed through unchanged."""
    n = len(keep)
    if isinstance(obj, dict):
        return {k: subset_rows(v, keep) for k, v in obj.items()}
    if isinstance(obj, (pd.DataFrame, pd.Series)) and len(obj) == n:
        return obj.iloc[np.flatnonzero(keep)].reset_index(drop=True)
    if isinstance(obj, np.ndarray) and obj.ndim >= 1 and obj.shape[0] == n:
        return obj[keep]
    return obj


def _restrict_to_training(d, emu, conds, label):
    """``subset_rows(d, training_mask(emu, conds))``, reporting what was dropped."""
    keep = training_mask(emu, conds)
    if not keep.all():
        print(f'  {label}: {int((~keep).sum())} of {len(keep)} states outside the training range left out')
    return subset_rows(d, keep)


def _save(fig, path):
    fig.savefig(path, dpi=300, facecolor='white')
    plt.close(fig)
    print(f'  -> {path}')


def _phase_grid(rows, draw, gt_label, pathway, xlabel, title, path, ylabel='phase fraction'):
    """One row per rock: GT phase stack (left) | emulator phase stack (right), printed
    at the text width. Column headers on the top row, rock names as row labels."""
    fig, axes = plt.subplots(len(rows), 2, figsize=(TEXT_W, 2.15 * len(rows) + 0.3),
                             squeeze=False, sharex='row', layout='constrained')
    heads = (gt_label, f'Emulator ({pathway})')
    for r, d in enumerate(rows):
        draw(axes[r][0], d['gt_phase'], d, '')
        draw(axes[r][1], d['em_phase'], d, '')
        for c, ax in enumerate(axes[r]):
            ax.set_xlabel(xlabel if r == len(rows) - 1 else '')
            ax.set_ylabel(f"{d['title']}\n{ylabel}" if c == 0 else '')
            if c == 1:
                ax.tick_params(labelleft=False)
            _fonts(ax, title=heads[c] if r == 0 else '')
    _save(fig, path)


def _pct(x):
    """Percent error for prose: two decimals below 1, one above (0.02, 0.63, 2.1, 18.8)."""
    return f'{x:.2f}' if x < 1 else f'{x:.1f}'


def _write_macros(path, macros):
    """One LaTeX newcommand per entry, for input in the chapter text."""
    lines = ['% Auto-generated by ngibbs_thesis_plots.py -- do not edit.']
    lines += ['\\newcommand{\\%s}{%s}' % kv for kv in macros.items()]
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'  -> {path}')


def _property_grid(rows, props, gt_label, pathway, xlabel, title, path, prop_label='nGibbs EOS',
                   show_T=None, show_err=False, show_em=True, gi_color='b', gi_lw=1.4):
    """One row per rock, one column per property, printed across a landscape page:
    ground truth (k-), emulator predicted assemblage (r--), GT assemblage through the
    property calculator ``prop_label`` (b:). The isentropic pathway adds a final T panel
    (GT vs temperature model) unless ``show_T`` says otherwise. ``show_err`` prints each
    curve's mean relative error against the ground truth in its panel. ``show_em=False`` drops
    the emulator curve; ``gi_color``/``gi_lw`` style the GT-assemblage curve. Property names
    head the top row; rock names label the rows; one legend."""
    from matplotlib.lines import Line2D
    if show_T is None:
        show_T = pathway == 'isentropic'
    n_cols = len(props) + (1 if show_T else 0)
    fig, axes = plt.subplots(len(rows), n_cols, figsize=(LAND_W, 1.35 * len(rows) + 0.45),
                             squeeze=False, layout='constrained')
    for r, d in enumerate(rows):
        order = np.argsort(d['x'])
        x = d['x'][order]
        panels = [(d['gt'][k][order], d['em'][k][order], d['gi'][k][order], label)
                  for k, label in props]
        if show_T:
            panels.append((d['T_gt'][order], d['T_em'][order], None, d['T_label']))
        for c, (gt, em, gi, label) in enumerate(panels):
            ax = axes[r][c]
            ax.plot(x, gt, 'k-', lw=1.2)
            if show_em:
                ax.plot(x, em, 'r--', lw=1.2)
            if gi is not None:
                ax.plot(x, gi, color=gi_color, ls=':', lw=gi_lw)
            ax.grid(True, alpha=0.25)
            ax.locator_params(nbins=3)
            ax.set_xlabel(xlabel if r == len(rows) - 1 else '')
            ax.set_ylabel(d['title'] if c == 0 else '')
            _fonts(ax, title=label if r == 0 else '')
            if show_err:
                curves = ((em, 'r'),) * show_em + ((gi, gi_color),)
                for i, (pred, color) in enumerate(curves):
                    if pred is None:
                        continue
                    ok = np.isfinite(gt) & np.isfinite(pred) & (gt != 0)
                    mre = 100 * np.mean(np.abs(pred[ok] / gt[ok] - 1))
                    ax.text(0.3, 0.95 - 0.13 * i, f'{mre:.2f}%', color=color, ha='left',
                            va='top', transform=ax.transAxes, fontsize=FS['tick'] - 1)
    handles = [Line2D([], [], color='k', ls='-', label=f'{gt_label}')]
    if show_em:
        handles.append(Line2D([], [], color='r', ls='--', label=f'emulator assemblage + {prop_label}'
                              + (' (T: temperature model)' if show_T else '')))
    handles.append(Line2D([], [], color=gi_color, ls=':', lw=gi_lw,
                          label=f'{gt_label} assemblage + {prop_label}'))
    fig.legend(handles=handles, loc='outside upper center', ncol=len(handles), frameon=False,
               fontsize=FS['legend'])
    _save(fig, path)


# --------------------------------------------------------------------------- #
# 2a. HeFESTo sections
# --------------------------------------------------------------------------- #
HEFESTO_SECTION_PROPS = [('rho', r'$\rho$ (g/cm$^3$)'), ('Vp_fast', r'$V_P$ (km/s)'),
                         ('Vs', r'$V_S$ (km/s)'), ('S', 'S (J/g/K)'), ('cptot', r'$C_p$ (J/g/K)'),
                         ('KStot', r'$K_S$ (GPa)'), ('alptot', r'$\alpha$ ($10^{-5}$ K$^{-1}$)')]


# HeFESTo standard-run names (directory name without 'adiabat'/'mars') -> panel titles.
_ROCK_TITLES = {'SILICA': 'Silica-enriched Pyrolite', 'BASALT': 'Basalt', 'SHERG': 'Shergottite'}


def _hefesto_standard(api, sim_dir):
    """One HeFESTo standard run, restricted to the model's training pressure range:
    conditions, fort.56 bulk properties (``gt``), composition, GT phase fractions, and
    the GT assemblage as component moles (``gt_cm``) and within-phase fractions
    (``gt_wpf``) for the nGibbs EOS."""
    from ngibbs.deployment_tests.meltstable_comparison import (
        _read_conditions, _load_component_moles, _load_composition,
        _load_fort99_phase_totals, _gt_phase_fractions, PROPERTY_MAP,
    )
    from ngibbs.engine.EOS_arithmetic.hefesto_vec import compute_within_phase_frac
    indexer = api.isothermal_emulator.ml_indexer
    rock = sim_dir.name.replace('adiabat', '').replace('mars', '')
    df, P, T, S = _read_conditions(sim_dir)
    # Restrict to the model's training pressure range, applying the SAME
    # row mask to fort.56 (conditions/properties) and fort.99 (phases).
    lo, hi = api.training_pressure_bounds('both')
    totals_all = _load_fort99_phase_totals(sim_dir)
    n = min(len(P), *(len(v) for v in totals_all.values()))
    keep = np.zeros(len(P), dtype=bool)
    keep[:n] = np.isfinite(P[:n]) & (P[:n] >= lo) & (P[:n] <= hi)
    df = df.loc[keep].reset_index(drop=True)
    P, T, S = P[keep], T[keep], S[keep]
    totals = {k: v[:n][keep[:n]] for k, v in totals_all.items()}
    gt_cm = _load_component_moles(sim_dir, indexer)[:n][keep[:n]]
    return dict(
        title=_ROCK_TITLES.get(rock, rock), df=df, P=P, T=T, S=S,
        comp=_load_composition(sim_dir),
        gt_phase=_gt_phase_fractions(totals, indexer.mass_phasedict, len(P)),
        gt={k: pd.to_numeric(df[PROPERTY_MAP[k][0]], errors='coerce').to_numpy(dtype=np.float64)
            for k, _ in HEFESTO_SECTION_PROPS},
        gt_cm=gt_cm, gt_wpf=compute_within_phase_frac(gt_cm, list(indexer.label_indices.values())),
    )


def hefesto_sections(name, fam, api, out_dir):
    from ngibbs.deployment_tests.meltstable_comparison import (
        find_tables, _emulator_phase_fractions, _emulator_assemblage, _eval_assemblage, PROPERTY_MAP,
    )
    from ngibbs.deployment_tests._phase_plotting import (
        phase_colors, build_ordered_phases, draw_phase_stack,
    )
    rocks = find_tables(HEFESTO_STANDARDS / fam['std_planet'], fam.get('section_rocks'))[:3]
    mpd = api.isothermal_emulator.ml_indexer.mass_phasedict
    ordered = build_ordered_phases(mpd)
    colors = phase_colors()

    data = []
    for sim_dir in rocks:
        d = _hefesto_standard(api, sim_dir)
        gi = _eval_assemblage(api, d['gt_cm'], d['P'], d['T'], d['gt_wpf'])
        d['gi'] = {k: _np(gi[k]) * PROPERTY_MAP[k][2] for k, _ in HEFESTO_SECTION_PROPS}
        data.append(d)

    def draw(ax, fracs, d, title):
        draw_phase_stack(ax, fracs, np.argsort(d['P']), d['P'], ordered, mpd, colors, title)

    for pathway in PATHWAYS:
        isen = pathway == 'isentropic'
        header = 'S(J/g/K)(System_main)' if isen else 'T(K)(System_main)'
        emu = api.isentropic_emulator if isen else api.isothermal_emulator
        rows = []
        for d in data:
            # GT and emulator are both shown only where this pathway's emulator was trained.
            d = _restrict_to_training(d, emu, {'P(GPa)(System_main)': d['P'],
                                               header: d['S'] if isen else d['T']},
                                      f"{d['title']} ({pathway})")
            second = d['S'] if isen else d['T']
            cm, wpf, T_em = _emulator_assemblage(api, d['P'], second, d['comp'], header, isen)
            T_eval = _np(T_em) if isen else d['T']
            props = _eval_assemblage(api, cm, d['P'], T_eval, wpf)
            rows.append(dict(
                d, x=d['P'],
                em_phase=_emulator_phase_fractions(api, d['P'], second, d['comp'], header),
                em={k: _np(props[k]) * PROPERTY_MAP[k][2] for k, _ in HEFESTO_SECTION_PROPS},
                T_gt=d['T'], T_em=T_eval, T_label='T (K)',
            ))
        _phase_grid(rows, draw, 'HeFESTo', pathway, 'P (GPa)', f"{fam['label']}: phase abundances",
                    out_dir / f'sections_phase_{name}_{pathway}.pdf')
        _property_grid(rows, HEFESTO_SECTION_PROPS, 'HeFESTo', pathway, 'P (GPa)', fam['label'],
                       out_dir / f'sections_property_{name}_{pathway}.pdf')
        if isen:
            # Entropy of the emulated assemblage at the predicted T against the S imposed on the isentrope.
            dS = [np.abs(r['em']['S'] - r['S']) for r in rows]
            _write_macros(out_dir / f'sections_{name}_entropy_macros.tex', {
                'EosSClosureMax': f"{max(x.max() for x in dS):.3f}",
                'EosSClosureMaxPct': f"{100 * max((x / np.abs(r['S'])).max() for x, r in zip(dS, rows)):.1f}"})


# --------------------------------------------------------------------------- #
# 2c. HeFESTo EOS terms, one level per row, on the Earth DMM adiabat
# --------------------------------------------------------------------------- #
# nGibbs EOS keys behind each column of HEFESTO_SECTION_PROPS at each level. rho, VS and S
# have no phase-change term, so they are the same at every level; Cp, KS and alpha gain the
# metamorphic (cross-phase reaction) terms, and VP only the intra-phase order-disorder
# ("fast") relaxation. The ground truth is fort.56 throughout.
EOS_TERM_LEVELS = {
    'isomorphic':  ('rho', 'Vp', 'Vs', 'S', 'cpiso', 'KSiso', 'alpiso'),
    '+metamorphic': ('rho', 'Vp', 'Vs', 'S', 'cptot', 'KStot', 'alptot'),
    '+fast':       ('rho', 'Vp_fast', 'Vs', 'S', 'cptot', 'KStot', 'alptot'),
}
EOS_TERMS_ROCK = 'DMMadiabat'


def hefesto_eos_terms(api, out_dir, pathway='isentropic'):
    """eos_terms_HeFESToEarth_DMM.pdf: the DMM adiabat's bulk properties from the emulated and
    the HeFESTo assemblage, with the isomorphic, + metamorphic and + fast EOS terms. Every
    level comes from one EOS call per assemblage: requesting Vp_fast runs both extra passes,
    and the isomorphic values are returned alongside."""
    from ngibbs.deployment_tests.meltstable_comparison import _emulator_assemblage
    keys = sorted({k for ks in EOS_TERM_LEVELS.values() for k in ks})

    def eos(cm, P, T, wpf):
        out = api.get_property_hefesto_vectorized_from_assemblage(
            torch.tensor(cm, dtype=torch.float64),
            torch.tensor(np.stack([P, T], axis=1), dtype=torch.float64),
            property_names=keys, within_phase_frac=torch.tensor(wpf, dtype=torch.float64))
        return {k: _np(out[k]) * (1e5 if k.startswith('alp') else 1.0) for k in keys}

    isen = pathway == 'isentropic'
    header = 'S(J/g/K)(System_main)' if isen else 'T(K)(System_main)'
    emu = api.isentropic_emulator if isen else api.isothermal_emulator
    d = _hefesto_standard(api, HEFESTO_STANDARDS / 'Earth' / EOS_TERMS_ROCK)
    d = _restrict_to_training(d, emu, {'P(GPa)(System_main)': d['P'],
                                       header: d['S'] if isen else d['T']},
                              f"{d['title']} ({pathway})")
    second = d['S'] if isen else d['T']
    cm, wpf, T_em = _emulator_assemblage(api, d['P'], second, d['comp'], header, isen)
    em = eos(cm, d['P'], _np(T_em) if isen else d['T'], wpf)
    gi = eos(d['gt_cm'], d['P'], d['T'], d['gt_wpf'])

    cols = [k for k, _ in HEFESTO_SECTION_PROPS]
    rows, mre = [], {}
    print(f"  mean relative error vs HeFESTo, {d['title']} ({pathway}); emulated | HeFESTo assemblage")
    for level, level_keys in EOS_TERM_LEVELS.items():
        rows.append(dict(title=level, x=d['P'], gt=d['gt'],
                         em={c: em[k] for c, k in zip(cols, level_keys)},
                         gi={c: gi[k] for c, k in zip(cols, level_keys)}))
        errs = []
        for c in cols:
            gt = d['gt'][c]
            ok = np.isfinite(gt) & (gt != 0)
            e = [100 * np.nanmean(np.abs(r[c][ok] / gt[ok] - 1)) for r in (rows[-1]['em'], rows[-1]['gi'])]
            mre[level, c] = e
            errs.append('/'.join(f'{x:.2f}' for x in e))
        print(f"    {level:13s} " + '  '.join(f'{c}={e}%' for c, e in zip(cols, errs)))
    names = dict(rho='Rho', Vp_fast='Vp', Vs='Vs', S='S', cptot='Cp', KStot='Ks', alptot='Alp')
    macros = {f'EosErr{n}': _pct(mre['+fast', c][0]) for c, n in names.items()}          # emulated, all terms
    macros.update({f'EosErrHef{n}': _pct(mre['+fast', c][1])                              # HeFESTo assemblage
                   for c, n in names.items() if n in ('Cp', 'Ks', 'Alp')})
    macros.update({f'EosErrNoMeta{n}': _pct(mre['isomorphic', c][0])                      # no metamorphic terms
                   for c, n in names.items() if n in ('Cp', 'Ks', 'Alp')})
    macros['EosErrVpNoFast'] = _pct(mre['+metamorphic', 'Vp_fast'][0])                    # no order-disorder term
    _write_macros(out_dir / f"eos_terms_{d['title']}_macros.tex", macros)
    _property_grid(rows, HEFESTO_SECTION_PROPS, 'HeFESTo', pathway, 'P (GPa)', 'HeFESTo Earth',
                   out_dir / f"eos_terms_HeFESToEarth_{d['title']}.pdf", show_T=False, show_err=True, show_em=False,
                   gi_color='#4da6ff', gi_lw=2.2)


def run_eos_terms(out_dir: Path, use_gpu: bool):
    import ngibbs.engine.models as models
    suffix = 'GPU' if use_gpu and torch.cuda.is_available() else 'CPU'
    print(f'[eos_terms] HeFESTo Earth ({suffix})')
    hefesto_eos_terms(getattr(models, f'HeFESToEmulator{suffix}'), out_dir)


# --------------------------------------------------------------------------- #
# 2b. MELTS sections (Cr sub-API, Cr standards; isobaric cooling -> x = T)
# --------------------------------------------------------------------------- #
MELTS_SECTION_PROPS = [('rho', r'$\rho$ (g/cm$^3$)'), ('S', 'S (J/g/K)'), ('Cp', r'$C_p$ (J/g/K)'),
                       ('V', r'V (cm$^3$/g)'), ('H', 'H (J/g)')]
MELTS_PTT_MODEL = {'102': 'MELTSv1.0.2', '120': 'MELTSv1.2.0'}
# ptt_out names the emulator's alkali feldspar 'k-feldspar1'; alphaMELTS only knows 'alkali-feldspar'.
_PTT_TO_MELTS_PHASE = {'k-feldspar1': 'alkali-feldspar1'}
# Fixed-composition phases (oxide moles per formula unit). ptt_out writes composition tables
# only for compositionally variable phases, so these would otherwise get no properties.
# 'fluid' is the MELTS 1.0.2 pure-water phase; graphite has no oxide form and stays out.
_PURE_PHASE_OXIDES = {
    'quartz': {'SiO2': 1}, 'tridymite': {'SiO2': 1}, 'fluid': {'H2O': 1},
    'apatite': {'CaO': 5, 'P2O5': 1.5, 'H2O': 0.5}, 'whitlockite': {'CaO': 3, 'P2O5': 1},
    'muscovite': {'K2O': 0.5, 'Al2O3': 1.5, 'SiO2': 3, 'H2O': 1}, 'calcite': {'CaO': 1, 'CO2': 1},
}


def _pure_phase_table(phase, n):
    """(n,) rows of the fixed oxide wt% of a pure phase, as a ptt composition table."""
    from ngibbs.config.constants import OXIDE_MOLAR_MASSES
    grams = {ox: k * OXIDE_MOLAR_MASSES[ox] for ox, k in _PURE_PHASE_OXIDES[phase].items()}
    total = sum(grams.values())
    # PetThermoTools finds a phase's table by its SiO2_ column, so always write one.
    cols = {'SiO2': 0.0, **{ox: 100.0 * g / total for ox, g in grams.items()}}
    return pd.DataFrame({f'{ox}_{phase}': np.full(n, wt) for ox, wt in cols.items()})


def _melts_ptt_props(res, model, label):
    """Bulk per-gram properties of a PTT-format assemblage ('Conditions' with T_C/P_bar, one
    oxide wt% table per phase, 'mass_g'), from alphaMELTS's own phase-property calculator
    via PetThermoTools. Phases alphaMELTS can't evaluate are dropped from the totals, so
    the per-gram values cover the remaining mass; a warning reports the uncovered share."""
    from petthermotools.nGibbs_bridge import add_phase_props
    res = {_PTT_TO_MELTS_PHASE.get(k, k): v for k, v in res.items() if k != 'All'}
    res['mass_g'] = res['mass_g'].rename(columns=_PTT_TO_MELTS_PHASE)
    n = len(res['Conditions'])
    for k in res['mass_g'].columns:
        phase = k.rstrip('0123456789')
        if k not in res and phase in _PURE_PHASE_OXIDES:
            res[k] = _pure_phase_table(phase, n)
    phases = [k for k in res['mass_g'].columns if k in res]
    total = res['mass_g'].sum(axis=1).to_numpy(dtype=np.float64)
    add_phase_props(res, Model=model)
    cond = res['Conditions']
    with np.errstate(divide='ignore', invalid='ignore'):
        mass = np.where(cond['mass_g'] > 0, cond['mass_g'], np.nan)
        missed = np.nanmax(1.0 - mass / total)
        # 'Cp_J/(kg.K^2)' is PetThermoTools' column name; the values are J/K scaled to phase mass.
        Cp = sum(np.nan_to_num(res[f'{k}_prop']['Cp_J/(kg.K^2)'].to_numpy(dtype=np.float64))
                 for k in phases)
        out = {'rho': cond['rho_kg/m^3'].to_numpy(dtype=np.float64) / 1000.0,
               'S': cond['S_J/K'].to_numpy(dtype=np.float64) / mass, 'Cp': Cp / mass,
               'V': cond['V_cm^3'].to_numpy(dtype=np.float64) / mass,
               'H': cond['H_J'].to_numpy(dtype=np.float64) / mass}
    if missed > 1e-3:
        warnings.warn(f'{label}: up to {100 * missed:.1f}% of the assemblage mass has no '
                      'alphaMELTS phase properties and is left out of the bulk values.')
    return out


def _gt_ptt_results(rock_dir, sysmain):
    """The alphaMELTS standard run as a PTT-format dict: per-phase oxide wt% from each
    <phase>.tbl and phase grams from Phase_mass_tbl.txt. Co-existing instances of one
    phase (e.g. rhm-oxide1/2) are merged: masses summed, compositions mass-weighted."""
    from ngibbs.deployment_tests.melts_comparison import (
        read_phase_mass, read_phase_tbl, _dedupe_tbl_instances, _reindex_to,
    )
    index = sysmain['index'].values.astype(int)
    mass_df, phase_cols = read_phase_mass(rock_dir)
    mass_df = _reindex_to(index, mass_df, index_col='index')
    res = {'Conditions': pd.DataFrame({'T_C': sysmain['Temperature'].values,
                                       'P_bar': sysmain['Pressure'].values})}
    masses = {}
    for col, phase in phase_cols:
        tbl = read_phase_tbl(rock_dir, 'melts-liquid' if phase == 'liquid' else phase)
        if tbl is None:
            warnings.warn(f'{rock_dir}: no {phase}.tbl; {phase} left out of the GT properties.')
            continue
        key = f'{phase}1'
        masses[key] = masses.get(key, 0.0) + mass_df[col].fillna(0.0).values
        if key not in res:
            wt = [c for c in tbl.columns if c.startswith('wt% ')]
            tbl = _reindex_to(index, _dedupe_tbl_instances(tbl, wt), index_col='Index')
            res[key] = pd.DataFrame({f'{c[4:]}_{phase}': tbl[c].fillna(0.0).values for c in wt})
    res['mass_g'] = pd.DataFrame(masses)
    return res


def melts_sections(name, fam, api, out_dir):
    from ngibbs.deployment_tests.melts_comparison import (
        ROCKS, read_system_main, read_bulk_comp, _system_main_feature, _ENTROPY_FEATURE,
        _emulator_input_oxides, _bulk_oxide, _gt_property_table, _gt_phase_mass_fractions,
        _emulator_phase_mass_fractions, _BARS_PER_GPA,
    )
    from ngibbs.deployment_tests._melts_phase_plotting import (
        MELTS_PHASE_STACK_ORDER, melts_phase_colors, build_ordered_melts_phases,
        draw_melts_phase_stack,
    )
    sub = api.cr if MELTS_VARIANT == 'Cr' else api.nocr
    std_dir = MELTS_STANDARDS / fam['std_version'] / MELTS_VARIANT
    ordered = build_ordered_melts_phases(MELTS_PHASE_STACK_ORDER)
    colors = melts_phase_colors()
    model = MELTS_PTT_MODEL[fam['std_version']]

    data = []
    for rock in ROCKS[:3]:
        rock_dir = std_dir / rock
        if not rock_dir.exists():
            warnings.warn(f'missing MELTS standard {rock_dir}')
            continue
        sysmain = read_system_main(rock_dir)
        mass_g = sysmain['mass'].values
        P_bar = sysmain['Pressure'].values
        d = dict(
            rock_dir=rock_dir, bulk=read_bulk_comp(rock_dir),
            title=f"{rock}, {P_bar[0] / _BARS_PER_GPA:.3g} GPa",
            T_C=sysmain['Temperature'].values, P_bar=P_bar,
            S_spec=_system_main_feature(sysmain, _ENTROPY_FEATURE),
            gt_phase=_gt_phase_mass_fractions(rock_dir, sysmain['index'].values.astype(int), mass_g),
            gt={k: _np(v) for k, v in _gt_property_table(sysmain, mass_g).items()},
            gi=_melts_ptt_props(_gt_ptt_results(rock_dir, sysmain), model, f'{rock} GT'),
        )
        data.append(d)

    def draw(ax, fracs, d, title):
        draw_melts_phase_stack(ax, fracs, d['T_C'], ordered, colors, title)

    for pathway in PATHWAYS:
        isen = pathway == 'isentropic'
        emu = sub.isentropic_emulator if isen else sub.isothermal_emulator
        header = _ENTROPY_FEATURE if isen else 'Temperature(System_main)'
        title = f"{fam['label']} ({MELTS_VARIANT})"
        if emu is None:
            warnings.warn(f'{title} has no {pathway} emulator; {pathway} sections skipped.')
            continue
        rows = []
        for d in data:
            # GT and emulator are both shown only where this pathway's emulator was trained.
            d = _restrict_to_training(d, emu, {'Pressure(System_main)': d['P_bar'],
                                               header: d['S_spec'] if isen else d['T_C']},
                                      f"{d['title']} ({pathway})")
            second = d['S_spec'] if isen else d['T_C']
            rows.append(dict(d, x=d['T_C'], second=second, em_phase=_emulator_phase_mass_fractions(
                api, emu, d['P_bar'], second, header, d['bulk'])))
        _phase_grid(rows, draw, 'alphaMELTS', pathway, 'T (°C)', f'{title}: phase mass fractions',
                    out_dir / f'sections_phase_{name}_{pathway}.pdf', ylabel='mass fraction')
        if pathway not in fam.get('property_pathways', PATHWAYS):
            continue

        # Separate from the phase figure so a failing temperature model (needed
        # only by the isentropic property pathway) doesn't cost the phase plot.
        try:
            for row in rows:
                oxides = _emulator_input_oxides(emu)
                table = np.column_stack([row['P_bar'], row['second']]
                                        + [_bulk_oxide(row['bulk'], ox) for ox in oxides])
                with torch.no_grad():
                    out = api.ForwardMB(table.astype(np.float32),
                                        headers=['Pressure(System_main)', header] + oxides,
                                        outputs=['ptt_out'] + (['temperature'] if isen else []))
                T_C_eval = _np(out['temperature']) if isen else row['T_C']
                res = out['ptt_out']
                res['Conditions']['T_C'] = T_C_eval
                row.update(em=_melts_ptt_props(res, model, f"{row['title']} emulator ({pathway})"),
                           T_gt=row['T_C'], T_em=T_C_eval, T_label='T (°C)')
        except Exception as e:
            warnings.warn(f"{title} {pathway} property section skipped: {type(e).__name__}: {e}")
            continue
        _property_grid(rows, MELTS_SECTION_PROPS, 'alphaMELTS', pathway, 'T (°C)', title,
                       out_dir / f'sections_property_{name}_{pathway}.pdf',
                       prop_label='alphaMELTS EOS')


def run_sections(out_dir: Path, use_gpu: bool):
    import ngibbs.engine.models as models  # loads every packaged emulator
    suffix = 'GPU' if use_gpu and torch.cuda.is_available() else 'CPU'
    for name, fam in FAMILIES.items():
        api = getattr(models, f"{fam['singleton']}{suffix}")
        print(f"[sections] {fam['label']} ({suffix})")
        try:
            if fam['space'] == 'elements':
                hefesto_sections(name, fam, api, out_dir)
            else:
                melts_sections(name, fam, api, out_dir)
        except Exception as e:  # keep going so one model can't kill the batch
            warnings.warn(f"{fam['label']} sections failed: {type(e).__name__}: {e}")


# --------------------------------------------------------------------------- #
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out-dir', default=str(Path(__file__).resolve().parent / 'generated'))
    ap.add_argument('--only', choices=['density', 'sections', 'eos_terms'], default=None)
    ap.add_argument('--gpu', action='store_true', help='use the GPU singletons when CUDA is available')
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if args.only in (None, 'density'):
        run_density(out)
    if args.only in (None, 'sections'):
        # No torch.no_grad() here: the internal EOS may take autograd derivatives;
        # the emulator forward passes already run without grad on their own.
        run_sections(out, args.gpu)
    if args.only in (None, 'eos_terms'):
        run_eos_terms(out, args.gpu)
