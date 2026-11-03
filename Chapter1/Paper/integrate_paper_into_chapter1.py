#!/usr/bin/env python3
"""
integrate_paper_into_chapter1.py -- ONE-SHOT back-port (2026-11-02) of the new
material developed for the Geochronology paper into thesis Chapter 1:
  * ampoule schematics (Schematic_Sequence5, Schematic_Bounding3)
  * titanite bounding-method simulation (BoundingMethodTitaniteSim)
  * in-situ rate-constant checks: Fig. insitu-lambda, Fig. insitu-examples,
    Fig. durango-lambda-selfcal, SI Fig. s-insitu-fits, SI Table s-insitu-lambda,
    and the paper paragraphs that describe them.

Rules (BJT): no thesis text is changed except to add in-text citations of the
new figures; paper text is moved in verbatim where needed.  Every insertion is
journaled in Chapter1/Paper/THESIS_BACKPORT_CHANGELOG.md.  Backups:
*.pre_paperbackport_20261102.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', 'Writing'))
CH = os.path.normpath(os.path.join(HERE, '..'))
TAG = '.pre_paperbackport_20261102'

def rd(p):
    return open(p, encoding='utf-8').read()

pb = rd(os.path.join(W, 'TubeMethodPaper_body.tex')).split('\n')
ps = rd(os.path.join(W, 'TubeMethodPaper_SI_body.tex')).split('\n')
LOG = []

def blk(src, a, b, expect):
    assert src[a - 1].lstrip().startswith(expect), (a, src[a - 1][:80], expect)
    return '\n'.join(src[a - 1:b]).strip('\n')

def cite(text, old, new, where):
    assert text.count(old) == 1, (where, old)
    LOG.append(f'- **CITE** [{where}] `{old.strip()}` -> `{new.strip()}`')
    return text.replace(old, new)

def insert_after(text, anchor, block, where, what):
    assert text.count(anchor) == 1, (where, anchor[:60])
    i = text.index(anchor) + len(anchor)
    LOG.append(f'- **MOVE IN** [{where}] {what}')
    return text[:i] + '\n\n' + block + text[i:]

def insert_before(text, anchor, block, where, what):
    assert text.count(anchor) == 1, (where, anchor[:60])
    i = text.index(anchor)
    LOG.append(f'- **MOVE IN** [{where}] {what}')
    return text[:i] + block + '\n\n' + text[i:]

# ---------------------------------------------------------------- paper blocks
F_PERMSTEP = blk(pb, 43, 48, '\\begin{figure}')
assert 'fig:schematic-permstep' in F_PERMSTEP
F_TITANITE = blk(pb, 153, 158, '\\begin{figure}')
assert 'fig:titanite-bounding' in F_TITANITE
F_BOUND3 = blk(pb, 160, 165, '\\begin{figure}')
assert 'fig:schematic-bounding' in F_BOUND3
P_CHECKA_METHOD = blk(pb, 213, 213, 'For the empty ampoule experiment, the rate constant')
F_INSITU = blk(pb, 225, 230, '\\begin{figure}')
F_EXAMPLES = blk(pb, 232, 237, '\\begin{figure}')
P_CHECKA_RES = blk(pb, 239, 239, 'Rate constants fit in situ')
P_RATIO = blk(pb, 241, 241, 'The same fits provide an isotopic')
F_SELFCAL = blk(pb, 252, 261, '\\begin{figure}')
P_CHECKB = blk(pb, 263, 263, 'The encapsulated Durango apatite data also')
S_INSITU = blk(ps, 360, 374, '\\section{In-situ Measurements')
assert S_INSITU.endswith('\\input{paper_insitu_lambda_table}')

# ---------------------------------------------------------------- main body
p = os.path.join(W, 'chapter1_body.tex')
shutil.copy(p, p + TAG)
t = rd(p)

# permeation step method: citation + schematic
t = cite(t, 'Eq.~\\eqref{eq:permlag} returns the helium evolved from the natural sample, \\(\\omega\\).',
         'Eq.~\\eqref{eq:permlag} returns the helium evolved from the natural sample, \\(\\omega\\) (Fig.~\\ref{fig:schematic-permstep}).',
         'Permeation Step Method, para 2')
t = insert_after(t, 'Eq.~\\eqref{eq:permlag} returns the helium evolved from the natural sample, \\(\\omega\\) (Fig.~\\ref{fig:schematic-permstep}).',
                 F_PERMSTEP, 'Permeation Step Method', 'Fig. schematic-permstep (Schematic_Sequence5.pdf) with its paper caption, verbatim (paper body L43-48).')

# bounding method: citations + titanite simulation + schematic
t = cite(t, 'than what is predicted by Eq.~\\eqref{eq:steadystate}.',
         'than what is predicted by Eq.~\\eqref{eq:steadystate} (Fig.~\\ref{fig:titanite-bounding}).',
         'Bounding Method, para 2')
t = cite(t, 'without permeation steps:', 'without permeation steps (Fig.~\\ref{fig:schematic-bounding}):',
         'Bounding Method, para 3')
t = insert_after(t, '\\label{fig:long-step-relative-uncertainty}\n\\end{figure}',
                 F_TITANITE + '\n\n' + F_BOUND3, 'Bounding Method',
                 'Figs. titanite-bounding (BoundingMethodTitaniteSim.pdf) and schematic-bounding (Schematic_Bounding3.pdf) with their paper captions, verbatim (paper body L153-165), after Fig. long-step-relative-uncertainty.')

# analytical methods: Check A fitting protocol
t = insert_after(t, 'Permeabilities were calculated for the empty ampoule experiments by solving Eq.~\\eqref{eq:permsol} for permeability \\emph{K}.',
                 P_CHECKA_METHOD, 'Analytical Methods, after para 1',
                 'Paper paragraph on the in-situ fits of the empty ampoule (first-step exclusion; R^2 justification), verbatim (paper body L213).')

# results: Check A and isotope ratio, after the 3He/4He permeation-ratio paragraph
anchor_ratio = [l for l in t.split('\n') if l.startswith('Permeation ratios for 3He and 4He measured in the empty tube experiment')]
assert len(anchor_ratio) == 1
t = insert_after(t, anchor_ratio[0], F_INSITU + '\n\n' + F_EXAMPLES + '\n\n' + P_CHECKA_RES + '\n\n' + P_RATIO,
                 'Results, after the 3He/4He permeation-ratio paragraph',
                 'Figs. insitu-lambda (InSituLambdaArrhenius.pdf) and insitu-examples (InSituLambdaFits_Examples.pdf) and the two paper results paragraphs (in-situ rate constants; isotope ratio), verbatim (paper body L225-241).')

# results: Check B after the Durango paragraph
anchor_dur = [l for l in t.split('\n') if l.startswith('The permeation lag-corrected helium diffusivities for the encapsulated Durango apatite experiment')]
assert len(anchor_dur) == 1
t = insert_after(t, anchor_dur[0], F_SELFCAL + '\n\n' + P_CHECKB, 'Results, after the Durango apatite paragraph',
                 'Fig. durango-lambda-selfcal (DurangoLambdaSelfCalibration.pdf) and the paper paragraph on the self-calibrated lambda_24, verbatim (paper body L252-263).')
open(p, 'w', encoding='utf-8').write(t)

# ---------------------------------------------------------------- SI
p = os.path.join(W, 'chapter1_SI_body.tex')
shutil.copy(p, p + TAG)
t = rd(p)
block = S_INSITU.replace('\\input{paper_insitu_lambda_table}', '\\input{Chapter1/Writing/paper_insitu_lambda_table}')
t = insert_before(t, '\\section{Sample Preparation and SEM Imaging of Buffered and Decomposed Sulfides}', block,
                  'SI, before "Sample Preparation and SEM Imaging"',
                  'Paper SI section "In-situ Measurements of the Rate Constant lambda" (Fig. s-insitu-fits, InSituLambdaFits_Grid.pdf; Table s-insitu-lambda), verbatim (paper SI L360-374); only the \\input path changed to the dissertation-root path Chapter1/Writing/paper_insitu_lambda_table.')
open(p, 'w', encoding='utf-8').write(t)

# ---------------------------------------------------------------- wrapper: \Paper* macros
p = os.path.join(CH, 'chapter1.tex')
shutil.copy(p, p + TAG)
t = rd(p)
anchor = '\\label{ch:apparatus}'
t = insert_after(t, anchor, '% Auto-generated \\Paper* values (in-situ lambda fits, Durango self-calibration) -- see\n'
                 '% Chapter1/Figures/fig_insitu_lambda.py. Shared with the Geochronology paper.\n'
                 '\\input{Chapter1/Writing/paper_derived_values}', 'chapter1.tex wrapper',
                 '\\input{Chapter1/Writing/paper_derived_values} (\\providecommand macros used by the moved paragraphs and captions).')
open(p, 'w', encoding='utf-8').write(t)

with open(os.path.join(HERE, 'THESIS_BACKPORT_CHANGELOG.md'), 'w', encoding='utf-8') as fh:
    fh.write('# Paper -> thesis Chapter 1 back-port (2026-11-02)\n\n'
             'New material from the Geochronology paper moved into the thesis. No thesis text was changed except '
             'the in-text figure citations listed as CITE; everything listed as MOVE IN is copied verbatim from '
             '`TubeMethodPaper_body.tex` / `TubeMethodPaper_SI_body.tex` (line numbers as of 2026-11-02). '
             'Backups: `*.pre_paperbackport_20261102`.\n\n')
    fh.write('\n'.join(LOG) + '\n')
print('\n'.join(LOG))
