#!/usr/bin/env python3
"""replace_hydrothermal.py -- "hydrothermal" -> "water vapor saturated" wording for the
experiments of this study in the GCA paper and SI (2026-11-02; per E. Stolper: the
pressure is the water vapor pressure, fixed by temperature, not an independent
hydrothermal pressure).  Natural/literature uses of "hydrothermal" are kept.
Run from Chapter2/Paper/.  Backups *.pre_wvs_20261102."""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', 'Writing'))
TAG = '.pre_wvs_20261102'

BODY = [
    ('Introduction', 'a step heat conducted under hydrothermal conditions', 'a step heat conducted under water vapor saturated conditions'),
    ('Introduction', 'for goethite under hydrothermal (high pH\\textsubscript{2}O) conditions', 'for goethite under water vapor saturated conditions'),
    ('Fig. ch2-sem caption', 'inherited from before hydrothermal treatment', 'inherited from before treatment at water vapor saturation'),
    ('Methods', 'evolved gases from hydrothermal step heats', 'evolved gases from water vapor saturated step heats'),
    ('Methods 2.1', 'applied to the hydrothermal experiment', 'applied to the water vapor saturated experiment'),
    ('Fig. ch2-arrhenius-zoom caption', 'Apparent diffusivities under hydrothermal conditions', 'Apparent diffusivities at water vapor saturation'),
    ('Fig. ch2-delta-zoom caption', 'Win-06-01b in hydrothermal conditions', 'Win-06-01b at water vapor saturation'),
    ('Fig. gt_arrhenius caption', 'and of the hydrothermal step heat of this study', 'and of the water vapor saturated step heat of this study'),
    ('4.2', 'for the vacuum and hydrothermal experiments: the hydrothermal experiment', 'for the vacuum and water vapor saturated experiments: the water vapor saturated experiment'),
    ('4.5', 'The hydrothermal experiment records lower', 'The water vapor saturated experiment records lower'),
    ('4.5', 'is slowest for the hydrothermal experiment', 'is slowest for the water vapor saturated experiment'),
    ('4.5', 'differs between the hydrothermal and vacuum experiments.', 'differs between the water vapor saturated and vacuum experiments.'),
    ('Fig. ch2-ratio-spectra caption', 'the water-saturated hydrothermal experiment of this study', 'the water vapor saturated experiment of this study'),
    ('Fig. ch2-ratio-spectra caption', 'fitted to the hydrothermal spectrum', 'fitted to the water vapor saturated spectrum'),
    ('Fig. ch2-ratio-spectra caption', 'The hydrothermal experiment shows lower', 'The water vapor saturated experiment shows lower'),
    ('Fig. ch2-ratio-spectra caption', 'Hydrothermal steps with less than', 'Steps of the water vapor saturated experiment with less than'),
    ('Fig. ch2-ratio-spectra caption', 'where hydrothermal data exist', 'where water vapor saturated data exist'),
    ('4.5', 'spectra of goethite under hydrothermal conditions are needed', 'spectra of goethite at water vapor saturation are needed'),
]
SI = [
    ('S1.1', 'permeability of ampoules used in hydrothermal step heats', 'permeability of ampoules used in water vapor saturated step heats'),
    ('Fig. ch2-ampoule-dims caption', 'used in the hydrothermal step heats of Win-06-01b', 'used in the water vapor saturated step heats of Win-06-01b'),
    ('S4 surface energy', 'which includes all of the hydrothermal experiments', 'which includes all of the water vapor saturated experiments'),
    ('S5 translation', 'Applied step by step to the hydrothermal schedule', 'Applied step by step to the water vapor saturated schedule'),
    ('Fig. gt_pigment caption', 'synthetic goethite pigment after hydrothermal treatment\n  at 200--250~$^\\circ$C', 'synthetic goethite pigment after treatment at water vapor\n  saturation and 200--250~$^\\circ$C'),
]
KEEP = ['recrystallize under hydrothermal conditions', 'grew in a hydrothermal setting', 'possibly hydrothermal, fluids',
        'hydrothermal_hold_projection.pdf', 'VacuumHydrothermal.pdf']


def pat(s):
    return re.compile(r'\s+'.join(re.escape(w) for w in s.split()))


log = []
for fn, reps in (('GoethitePaper_body.tex', BODY), ('GoethitePaper_SI_body.tex', SI)):
    p = os.path.join(W, fn)
    shutil.copy(p, p + TAG)
    raw = open(p, encoding='utf-8', newline='').read()
    crlf = '\r\n' in raw
    t = raw.replace('\r\n', '\n')
    for where, old, new in reps:
        m = list(pat(old).finditer(t))
        assert len(m) == 1, (fn, where, old, len(m))
        t = t[:m[0].start()] + new + t[m[0].end():]
        log.append(f'- **EDIT** [{fn.replace("GoethitePaper_", "").replace(".tex", "")}: {where}] "{" ".join(old.split())}" -> "{" ".join(new.split())}"')
    left = [t[max(0, x.start() - 50):x.end() + 30].replace('\n', ' ') for x in re.finditer(r'(?i)hydrothermal', t)]
    for l in left:
        assert any(k in l for k in KEEP), (fn, l)
    log.append(f'- {fn}: remaining "hydrothermal" kept on purpose ({len(left)}): ' + '; '.join(f'"...{l.strip()}..."' for l in left))
    open(p, 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n') if crlf else t)

with open(os.path.join(HERE, 'PORT_CHANGELOG.md'), 'a', encoding='utf-8') as fh:
    fh.write('\n## "Hydrothermal" -> "water vapor saturated" (2026-11-02; E. Stolper: the pressure is the water vapor pressure, '
             'set by temperature). Backups `*.pre_wvs_20261102`.\n\n'
             'Kept: natural/literature senses (goethite recrystallization under hydrothermal conditions, Schwertmann 1985; '
             '"grew in a hydrothermal setting"; "possibly hydrothermal, fluids"), figure file names, the sample name HT-Win-06-01b, '
             'and the Zenodo dataset title in the bibliography.\n'
             'Figures (legend text only; scripts backed up as `*.pre_wvs_20261102`, old PDFs in `generated/_pre_wvs_20261102/`): '
             'Ch2_spectra_combined (fig_ch2_spectra_combined.py), DeltasWinsorGTzoomin_VacuumHydrothermal (fig_delta_plot.py), '
             'winsor_goethite_Diffusivities_Arrhenius_Zoomin (fig_decomp_vs_hydrothermal.py), arrhenius_reaction_vs_diffusion '
             '(fig_goethite_vacuum_kinetics.py; also the label of the first-order delta plot, not used in the paper). '
             '"Hydrothermal ..." -> "Water vapor saturated ...". These figures are shared with thesis Chapter 2.\n\n')
    fh.write('\n'.join(log) + '\n')
print('\n'.join(log))
