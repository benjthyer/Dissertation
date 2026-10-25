"""
Chapter 4 tables built from the installed ``ngibbs`` package.

1. Emulator quality tables (deployment tests). Each emulator is scored against its
   shipped Test_subset bundle with ``ngibbs.deployment_tests.evaluate_emulator_quality``
   (the function ``EmulatorAPI.test()`` uses). The full metrics x phases table for each
   emulator is cached as ``quality/emulator_quality_<label>.csv``. Two LaTeX tables are
   built from three metrics per phase -- mean ground-truth abundance (wt% of system),
   phase-presence precision and recall -- with one 3-column group per model:

       tab_quality_melts.tex     MELTS 1.0.2 / 1.2.0, Cr / no-Cr, closed isothermal
       tab_quality_hefesto.tex   HeFESTo Earth / Mars, isothermal / isentropic

2. Component tables from ``config/projections/compToOxV2.csv``:

       tab_components_melts.tex    phases and components of the MELTS emulators above
       tab_components_hefesto.tex  phases and components of the HeFESTo emulators
                                   (ml_indexer.components_in_phases, Earth and Mars)

Usage
    python make_quality_tables.py              # run the deployment tests, then write tables
    python make_quality_tables.py --from-csv   # rebuild the .tex from the cached CSVs only
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
QDIR = HERE / 'quality'

# (label, header text, API attribute in ngibbs.engine.models, sub-API, emulator)
MELTS_MODELS = [
    ('MELTS102_Cr_iso', r'1.0.2, Cr', 'MELTS102EmulatorCPU', 'cr', 'isothermal'),
    ('MELTS102_NoCr_iso', r'1.0.2, no Cr', 'MELTS102EmulatorCPU', 'nocr', 'isothermal'),
    ('MELTS120_Cr_iso', r'1.2.0, Cr', 'MELTS120EmulatorCPU', 'cr', 'isothermal'),
    ('MELTS120_NoCr_iso', r'1.2.0, no Cr', 'MELTS120EmulatorCPU', 'nocr', 'isothermal'),
]
HEFESTO_MODELS = [
    ('HeFESToEarth_iso', r'Earth ($P$, $T$)', 'HeFESToEmulatorCPU', None, 'isothermal'),
    ('HeFESToEarth_isen', r'Earth ($P$, $S$)', 'HeFESToEmulatorCPU', None, 'isentropic'),
    ('HeFESToMars_iso', r'Mars ($P$, $T$)', 'HeFESToMarsEmulatorCPU', None, 'isothermal'),
    ('HeFESToMars_isen', r'Mars ($P$, $S$)', 'HeFESToMarsEmulatorCPU', None, 'isentropic'),
]
METRICS = ('proportion_in_dataset', 'precision', 'recall')
# Precision/recall cells are shaded on a one-way scale: white at 1.00 to SHADE_RED at
# SHADE_FLOOR and below (linear in RGB). Needs \usepackage{colortbl} in the preamble.
SHADED = ('precision', 'recall')
SHADE_FLOOR = 0.80
SHADE_RED = (232, 120, 112)


# --------------------------------------------------------------------------- run tests
def _api(models, attr, sub):
    api = getattr(models, attr)
    return getattr(api, sub) if sub else api


def run_quality(model_list):
    import ngibbs.engine.models as models
    from ngibbs.deployment_tests import evaluate_emulator_quality

    QDIR.mkdir(parents=True, exist_ok=True)
    for label, _, attr, sub, emu in model_list:
        api = _api(models, attr, sub)
        bundle = api._test_bundles[emu]
        print(f'[quality] {label}: {Path(bundle).name}')
        r = evaluate_emulator_quality(api, bundle, emulator_name=emu)
        r['phase_quality_metrics'].to_csv(QDIR / f'emulator_quality_{label}.csv', na_rep='--')


def load_quality(label):
    return pd.read_csv(QDIR / f'emulator_quality_{label}.csv', index_col='metric', na_values='--')


# --------------------------------------------------------------------------- quality tables
def _phase_label(p):
    return {'melts-liquid': 'liquid', 'rhm-oxide': 'rhm-oxide', 'hp-clinopyroxene':
            'HP clinopyroxene', 'alpha-pbo-type-sio2': r'$\alpha$-PbO$_2$-SiO$_2$',
            'alpha-iron': r'$\alpha$-iron', 'gamma-iron': r'$\gamma$-iron',
            'epsilon-iron': r'$\varepsilon$-iron', 'nal-phase': 'NAL phase',
            'ca-perovskite': 'Ca-perovskite', 'ca-ferrite': 'Ca-ferrite', 'k-feldspar': 'K-feldspar',
            }.get(p, p).replace('-', '-')


def _shade(v):
    """RGB triple for a precision/recall value, or None for white."""
    f = float(np.clip((1.0 - v) / (1.0 - SHADE_FLOOR), 0.0, 1.0))
    rgb = tuple(int(round(255 + f * (c - 255))) for c in SHADE_RED)
    return None if rgb == (255, 255, 255) else rgb


def _cell(v, kind):
    text = _fmt(v, kind)
    if kind in SHADED and v is not None and np.isfinite(v):
        rgb = _shade(v)
        if rgb is not None:
            return rf'\cellcolor[RGB]{{{rgb[0]},{rgb[1]},{rgb[2]}}}{text}'
    return text


def _fmt(v, kind):
    if v is None:
        return '--'
    if not np.isfinite(v):
        return 'n.d.'
    return f'{v:.2f}'


def _dropped_note():
    a, b = 15000 - n_rows('HeFESToEarth_iso'), 15000 - n_rows('HeFESToEarth_isen')
    which = f'{a} assemblages of each Earth subset' if a == b else \
        f'{a} and {b} assemblages of the Earth isothermal and isentropic subsets'
    return (which + ' contain pseudowollastonite, which the Earth models do not include, '
            'and are excluded')


def n_rows(label):
    return int(load_quality(label).loc['n_samples'].iloc[0])


def quality_table(model_list, caption, label, title_note):
    tabs = {lab: load_quality(lab) for lab, *_ in model_list}
    phases = []
    for t in tabs.values():
        phases += [p for p in t.columns if p not in phases]
    mean_ab = {p: np.nanmean([t.at['proportion_in_dataset', p] if p in t.columns else np.nan
                              for t in tabs.values()]) for p in phases}
    phases.sort(key=lambda p: -mean_ab[p])

    n = len(model_list)
    out = [r'\begin{table}[!htbp]', r'\centering', r'\footnotesize',
           r'\setlength{\tabcolsep}{2.2pt}',
           rf'\caption{{{caption}}}', rf'\label{{{label}}}',
           r'\begin{tabular}{@{}l' + 'rrr' * n + r'@{}}', r'\toprule']
    out.append(' & ' + ' & '.join(rf'\multicolumn{{3}}{{c}}{{{h}}}'
                                   for _, h, *_ in model_list) + r' \\')
    out.append(''.join(rf'\cmidrule(lr){{{2 + 3 * i}-{4 + 3 * i}}}' for i in range(n)))
    out.append('Phase & ' + ' & '.join(['Freq.', 'Prec.', 'Rec.'] * n) + r' \\')
    out.append(r'\midrule')
    for p in phases:
        cells = []
        for lab, *_ in model_list:
            t = tabs[lab]
            for m in METRICS:
                cells.append(_cell(t.at[m, p] if p in t.columns else None, m))
        out.append(f'{_phase_label(p)} & ' + ' & '.join(cells) + r' \\')
    out += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    return '\n'.join(out) + '\n'


# --------------------------------------------------------------------------- components
OX_ELEMENTS = {  # oxide -> (cation symbol, cations per oxide, oxygens per oxide)
    'SiO2': ('Si', 1, 2), 'TiO2': ('Ti', 1, 2), 'Al2O3': ('Al', 2, 3), 'FeO': ('Fe2', 1, 1),
    'MgO': ('Mg', 1, 1), 'CaO': ('Ca', 1, 1), 'Na2O': ('Na', 2, 1), 'K2O': ('K', 2, 1),
    'P2O5': ('P', 2, 5), 'MnO': ('Mn', 1, 1), 'H2O': ('H', 2, 1), 'Cr2O3': ('Cr', 2, 3),
    'NiO': ('Ni', 1, 1), 'CO2': ('C', 1, 2), 'Fe2O3': ('Fe3', 2, 3),
}
CATION_ORDER = ['K', 'Na', 'Ca', 'Mg', 'Fe2', 'Mn', 'Ni', 'Fe3', 'Fe', 'Al', 'Cr', 'Ti', 'Si', 'P', 'C']
HYDRATES = {'analcime'}          # written X·H2O rather than with (OH)


def _num(x):
    if abs(x - 1) < 1e-9:
        return ''
    if abs(x - round(x)) < 1e-9:
        return f'{int(round(x))}'
    return f'{x:g}'


def _el(sym, x):
    tex = {'Fe2': 'Fe', 'Fe3': r'Fe$^{3+}$'}.get(sym, sym)
    n = _num(x)
    if not n:
        return tex
    return tex + (f'$_{{{n}}}$' if not tex.endswith('$') else f'$_{{{n}}}$')


def formula(row, name=''):
    """Element formula of one compToOx row (oxide coefficients)."""
    nz = {ox: v for ox, v in row.items() if v != 0}
    if list(nz) == ['H2O']:
        return r'H$_2$O'
    cat, O = {}, 0.0
    neg = any(v < 0 for v in row.values)
    for ox, v in row.items():
        if v == 0:
            continue
        sym, ncat, nox = OX_ELEMENTS[ox]
        cat[sym] = cat.get(sym, 0) + v * ncat
        O += v * nox
    if neg or ('Fe2' in cat and 'Fe3' not in cat):
        fe = cat.pop('Fe2', 0) + cat.pop('Fe3', 0)
        if abs(fe) > 1e-9:
            cat['Fe'] = fe
    elif 'Fe2' in cat and 'Fe3' in cat:          # mixed valence: label both
        cat['Fe2+'] = cat.pop('Fe2')
    cat = {k: v for k, v in cat.items() if abs(v) > 1e-9}
    H = cat.pop('H', 0)
    if name in HYDRATES and H:
        O -= H / 2
    elif H:
        O -= H
    parts = []
    for sym in CATION_ORDER + ['Fe2+']:
        if sym in cat:
            if sym == 'Fe2+':
                parts.insert(0, (r'Fe$^{2+}$' + (f'$_{{{_num(cat[sym])}}}$' if _num(cat[sym]) else '')))
            else:
                parts.append(_el(sym, cat[sym]))
    # put Fe2+ right before Fe3+ for mixed-valence formulae
    s = ''.join(p for p in parts if not p.startswith(r'Fe$^{2+}$'))
    fe2 = [p for p in parts if p.startswith(r'Fe$^{2+}$')]
    if fe2:
        s = s.replace(r'Fe$^{3+}$', fe2[0] + r'Fe$^{3+}$', 1)
    if abs(O) > 1e-9:
        s += 'O' + (f'$_{{{_num(O)}}}$' if _num(O) else '')
    if H and name in HYDRATES:
        s += r'$\cdot$' + (_num(H / 2) or '') + r'H$_2$O'
    elif H:
        s += '(OH)' + (f'$_{{{_num(H)}}}$' if _num(H) else '')
    return s.replace('$$', '')


def comp_to_ox():
    import ngibbs
    p = Path(ngibbs.__file__).parent / 'config' / 'projections' / 'compToOxV2.csv'
    return pd.read_csv(p, index_col=0)


def _row(c2o, comp, phase):
    for key in (f'{comp} : {phase}', comp):
        if key in c2o.index:
            return c2o.loc[key]
    raise KeyError(f'{comp} ({phase}) not in compToOxV2')


def _merge_identical(entries):
    """Merge phases whose component lists and formulae are identical (e.g. MELTS
    orthopyroxene and clinopyroxene) into one entry 'phase A, phase B'."""
    out = []
    for phase, mark, rows in entries:
        for k, (ph2, mk2, rows2) in enumerate(out):
            if rows2 == rows and mk2 == mark:
                out[k] = (ph2 + [phase], mk2, rows2)
                break
        else:
            out.append(([phase], mark, rows))
    return out


def _split(entries, ncols):
    """Split entries at phase boundaries into ncols groups of about equal row count."""
    sizes = [len(r) for _, _, r in entries]
    target = sum(sizes) / ncols
    groups, cur, n = [], [], 0
    for e, sz in zip(entries, sizes):
        if cur and n + sz / 2 > target * (len(groups) + 1) and len(groups) < ncols - 1:
            groups.append(cur)
            cur = []
        cur.append(e)
        n += sz
    groups.append(cur)
    return groups


def components_table(entries, caption, label, marks_note, ncols=2, size=r'\footnotesize',
                     fit=False):
    """One landscape page: the phase/component/formula list split into ``ncols``
    side-by-side tabulars, with a thin rule between phases.
    entries: list of (phase, mark, [(component, formula_tex)])."""
    groups = _split(_merge_identical(entries), ncols)
    out = [r'\begin{landscape}', r'\begin{table}[p]', r'\centering', size,
           r'\setlength{\tabcolsep}{4pt}', r'\setlength{\aboverulesep}{0.2ex}',
           r'\setlength{\belowrulesep}{0.3ex}', rf'\caption{{{caption}}}\label{{{label}}}',
           r'\noindent']
    if fit:                      # scale the row of tabulars to exactly the page width
        out.append(r'\resizebox{\linewidth}{!}{%')
    for gi, group in enumerate(groups):
        out += [r'\begin{tabular}[t]{@{}l l l@{}}', r'\toprule', r'Phase & Component & Formula \\',
                r'\midrule']
        for k, (phases, mark, rows) in enumerate(group):
            names = [_phase_label(ph) for ph in phases]
            for i, (c, f) in enumerate(rows):
                ph = ''
                if i < len(names):                 # one phase name per line when merged
                    ph = names[i] + (',' if i < len(names) - 1 else mark)
                out.append(f'{ph} & {c} & {f} \\\\')
            for extra in names[len(rows):]:
                out.append(f'{extra} & & \\\\')
            if k < len(group) - 1:
                out.append(r'\cmidrule{1-3}')
        out += [r'\bottomrule', r'\end{tabular}']
        if gi < len(groups) - 1:
            out.append(r'\hspace{2em}' if fit else r'\hfill')
    if fit:
        out.append('}')
    out += [r'\par\medskip', r'\noindent ' + marks_note,
            r'\end{table}', r'\end{landscape}']
    return '\n'.join(out) + '\n'


def melts_components(c2o):
    import ngibbs.engine.models as models
    cips = {}
    for label, _, attr, sub, emu in MELTS_MODELS:
        ix = getattr(_api(models, attr, sub), f'{emu}_emulator').ml_indexer
        cips[label] = {p: list(c) for p, c in ix.components_in_phases.items()}
    phases, seen = [], set()
    for cip in cips.values():
        for p in cip:
            if p not in seen:
                seen.add(p)
                phases.append(p)
    entries = []
    for p in phases:
        in120only = all(p not in cips[l] for l in cips if l.startswith('MELTS102'))
        comps = []
        for lab in cips:
            for c in cips[lab].get(p, []):
                if c not in [x for x, _ in comps]:
                    comps.append((c, None))
        rows = []
        for c, _ in comps:
            cr_only = all(c not in cips[l].get(p, []) for l in cips if 'NoCr' in l)
            only120 = not in120only and all(c not in cips[l].get(p, [])
                                            for l in cips if l.startswith('MELTS102'))
            name = c
            if p == 'melts-liquid':                      # oxide weight fractions
                ox = c.replace('wt% ', '')
                f = re.sub(r'(\d+)', r'$_{\1}$', ox)
                name = re.sub(r'(\d+)', r'$_{\1}$', ox)
            else:
                f = formula(_row(c2o, c, p), c)
                if c in ('H2O', 'CO2'):
                    name = re.sub(r'(\d+)', r'$_{\1}$', c)
            name += (r'$^{\dagger}$' if only120 else '') + (r'$^{\ddagger}$' if cr_only else '')
            rows.append((name, f))
        if p == 'melts-liquid':                          # oxides, four per row
            oxs = [n for n, _ in rows]
            rows = [('oxides' if i == 0 else '', ', '.join(oxs[i:i + 4]))
                    for i in range(0, len(oxs), 4)]
        entries.append((p, r'$^{\dagger}$' if in120only else '', rows))
    return entries


def hefesto_components(c2o):
    import ngibbs.engine.models as models
    cips = {}
    for lab, attr in (('Earth', 'HeFESToEmulatorCPU'), ('Mars', 'HeFESToMarsEmulatorCPU')):
        ix = getattr(models, attr).isothermal_emulator.ml_indexer
        cips[lab] = {p: list(c) for p, c in ix.components_in_phases.items()}
    phases = list(cips['Earth']) + [p for p in cips['Mars'] if p not in cips['Earth']]
    entries = []
    for p in phases:
        only = [lab for lab in cips if p in cips[lab]]
        mark = '' if len(only) == 2 else (r'$^{\mathrm{E}}$' if only == ['Earth'] else r'$^{\mathrm{M}}$')
        comps = cips['Earth'].get(p) or cips['Mars'].get(p)
        entries.append((p, mark, [(c, formula(_row(c2o, c, p), c)) for c in comps]))
    return entries


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--from-csv', action='store_true', help='skip the deployment tests')
    args = ap.parse_args()
    if not args.from_csv:
        run_quality(MELTS_MODELS + HEFESTO_MODELS)

    note = ('Freq.: fraction of test assemblages in which the phase is present in the ground truth '
            '(0.00 is below 0.005). Prec./Rec.: precision and recall of the predicted phase presence, shaded from white '
            '(1.00) to red (0.80 and below). '
            '-- : phase not in the model; n.d.: undefined (no predicted or no true occurrences).')
    (HERE / 'tab_quality_melts.tex').write_text(quality_table(
        MELTS_MODELS,
        r'Phase frequency and phase-presence quality of the closed-system isothermal \textsc{MELTS} '
        r'1.0.2 and 1.2.0 emulators, with (Cr) and without (no Cr) chromium, on their held-out test '
        r'subsets (15{,}000 assemblages each). ' + note,
        'tab:ch4-quality-melts', ''))
    (HERE / 'tab_quality_hefesto.tex').write_text(quality_table(
        HEFESTO_MODELS,
        r'Phase frequency and phase-presence quality of the isothermal ($P$, $T$) and isentropic '
        r'($P$, $S$) \textsc{HeFESTo} Earth and Mars emulators on their '
        r'held-out test subsets (15{,}000 assemblages each; ' + _dropped_note() + r'). ' + note,
        'tab:ch4-quality-hefesto', ''))

    c2o = comp_to_ox()
    (HERE / 'tab_components_melts.tex').write_text(components_table(
        melts_components(c2o),
        r'Phases and components of the \textsc{MELTS} emulators, with formulae from the '
        r'component-to-oxide stoichiometry used by \emph{nGibbs}. Liquid components are oxides.',
        'tab:ch4-components-melts',
        r'$^{\dagger}$\,\textsc{MELTS} 1.2.0 emulators only. $^{\ddagger}$\,Cr variants only.',
        ncols=2, size=r'\scriptsize'))
    (HERE / 'tab_components_hefesto.tex').write_text(components_table(
        hefesto_components(c2o),
        r'Phases and components of the \textsc{HeFESTo} emulators, with formulae from the '
        r'component-to-oxide stoichiometry used by \emph{nGibbs}.',
        'tab:ch4-components-hefesto',
        r'$^{\mathrm{E}}$\,Earth model only. $^{\mathrm{M}}$\,Mars model only.',
        ncols=3, size=r'\scriptsize', fit=True))
    print('tables written to', HERE)


if __name__ == '__main__':
    main()
