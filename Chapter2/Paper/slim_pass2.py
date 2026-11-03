#!/usr/bin/env python3
"""slim_pass2.py -- second slimming pass on the GCA goethite manuscript (2026-11-02).

Run from Chapter2/Paper/. Edits Chapter2/Writing/GoethitePaper_body.tex,
GoethitePaper_SI_body.tex in place (backups *.pre_slim2_20261102) and appends a
journal to Chapter2/Paper/PORT_CHANGELOG.md.
"""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', 'Writing'))
TAG = '.pre_slim2_20261102'
B = os.path.join(W, 'GoethitePaper_body.tex')
S = os.path.join(W, 'GoethitePaper_SI_body.tex')
TH = os.path.join(W, 'chapter2_body.tex')
for p in (B, S):
    shutil.copy(p, p + TAG)
b = open(B, encoding='utf-8').read()
s = open(S, encoding='utf-8').read()
th = open(TH, encoding='utf-8').read().split('\n')
LOG = []


def short(x, n=500):
    x = ' '.join(x.split())
    return x if len(x) <= n else x[:n] + f' ... [{len(x)} chars]'


def E(t, old, new, where, note):
    assert t.count(old) == 1, (where, t.count(old), old[:80])
    LOG.append(f'- **EDIT** [{where}] {note}\n    - was: "{short(old)}"\n    - now: "{short(new)}"')
    return t.replace(old, new)


def span(t, start, end):
    """Return (i, j) of the block from `start` (inclusive) to `end` (exclusive)."""
    assert t.count(start) == 1, start[:80]
    i = t.index(start)
    j = t.index(end, i)
    return i, j


def CUT(t, start, end, where, note, keep_end=True):
    i, j = span(t, start, end)
    LOG.append(f'- **CUT** [{where}] {note}\n    - deleted: "{short(t[i:j], 400)}"')
    return t[:i] + t[j:], t[i:j]


# =====================================================================
# MAIN TEXT
# =====================================================================
# --- item 5: molecular-simulation paragraph; Bassal cited with the factors this study cannot test
b, _ = CUT(b, 'Molecular simulations indicate that helium diffusion in perfectly',
           'Goethite dehydration is suppressed at high water pressure',
           '1 Introduction', 'Molecular-simulation paragraph (Bassal et al. 2022) removed (BJT item 5).')
b = E(b, 'chemical composition could affect helium mobility and retentivity in\nnature.',
      'chemical composition could affect helium mobility and retentivity in\nnature \\citep{bassal2022}.',
      '1 Introduction', 'Bassal et al. (2022) cited where radiation damage and composition are named as untested factors (also still cited in para 2 and 4).')

# --- item 6: ampoule seal sentence; photo to SI
old = b[span(b, 'Fig.~\\ref{fig:ch2-ampoule-post} shows the sealed ampoule', 'cell while the ampoule was held at 250°C for over a week.')[0]:
        b.index('cell while the ampoule was held at 250°C for over a week.') + len('cell while the ampoule was held at 250°C for over a week.')]
b = E(b, old, 'The ampoule retained all of its water through the experiment, including more than a week at\n'
      '250°C with an internal vapor pressure of about 40~bar \\citep{haar1984} (SI Fig.~\\ref{fig:ch2-ampoule-post}).',
      '2 Methods para 2', 'Seal "testament / 11 orders of magnitude" sentence condensed; photo now in the SI.')
b, FIG_AMP = CUT(b, '\\begin{figure}[htbp]\n\\centering\n\\includegraphics[width=0.7\\textwidth]{zoomout2.jpg}',
                 'The sealed ampoule, now referred to as HT-Win-06-01b',
                 '2 Methods', 'Fig. ch2-ampoule-post moved to SI S1 (MOVE).')
FIG_AMP = FIG_AMP.strip('\n')

# --- item 6: temperature-accuracy paragraph -> two sentences + preprint
old = b[span(b, 'Experimental temperature records show', 'Helium isotope measurements of evolved gases')[0]:
        span(b, 'Experimental temperature records show', 'Helium isotope measurements of evolved gases')[1]]
b = E(b, old, 'Recorded temperatures oscillated by \\textasciitilde1°C around each target. Because the ampoule\n'
      'sat between the lamp and the thermocouple junction, any bias would make the sample hotter than\n'
      'recorded, and encapsulated Durango apatite heated in the same way reproduces published\n'
      'diffusivities \\citep{thyer2026method}.\n\n',
      '2 Methods para 5', 'Temperature-accuracy paragraph condensed; validation cited to the preprint (BJT item 6).')

# --- item 6: final-step blank / re-extract / sensitivity -> SI
i, j = span(b, 'A\nhot furnace blank subjected to the same volume splits', 'Helium released by the sample reaches the mass spectrometer')
FINAL = b[i:j].strip()
b = b[:i] + 'Blank, re-extract and sensitivity details are given in the SI (\\S\\ref{sec:ch2-si-finalstep}).\n\n' + b[j:]
LOG.append(f'- **MOVE** [2 Methods para 8 -> SI S2] Final-step blank, re-extract and sensitivity sentences moved to SI subsection "Final Step"; '
           f'NEW pointer sentence "Blank, re-extract and sensitivity details are given in the SI (S2)."\n    - moved: "{short(FINAL)}"')

# --- item 8: uncertainty derivations and complete-degas test -> thesis
b = E(b, 'Information (\\S\\ref{sec:ch2-si-permeation}), together with the diffusivity inversions, the\n'
      'isotope-ratio uncertainties and the kinetic analysis of the published vacuum step heats\n'
      '(\\S\\ref{ch2-analytical-methods}).',
      'Information (\\S\\ref{sec:ch2-si-permeation}). The propagation of the permeation-lag bounds into apparent\n'
      'diffusivities and isotope ratios, and a test of the bounding method against direct permeation-step\n'
      'quantification, are described by \\citet{thyer2026thesis}.',
      '2 Methods para 9', 'SI uncertainty derivations and complete-degas test removed; thesis cited (BJT item 8). Also fixes the old S2/S3 mis-pointer.')
b = E(b, 'experiment (\\S\\ref{helium-in-goethite-diffusivity-inversions}).',
      'experiment (\\citealt{thyer2026thesis}).', '2.1', 'Pointer to the removed SI diffusivity-uncertainty section -> thesis.')

# --- item 2: isothermal family out of the methods
b = E(b, 'We compare three types of thermal histories, with two free parameters for steady cooling and the isothermal hold and three for burial and exhumation. ',
      'We compare two types of thermal histories, with two free parameters for steady cooling and three for burial and exhumation. ',
      '2.2 Thermal histories', 'Isothermal family removed (BJT item 2).')
old = b[span(b, '  \\item \\textbf{Isothermal hold:}', '\\end{itemize}')[0]:span(b, '  \\item \\textbf{Isothermal hold:}', '\\end{itemize}')[1]]
b = E(b, old, '', '2.2 Thermal histories', 'Isothermal-hold bullet removed (BJT item 2).')

# --- item 6: chi^2 definition -> SI
i, j = span(b, 'Each path is scored against\n\\begin{equation}', '$\\chi^2$ is evaluated for these free parameters along regularly spaced grids')
CHI = b[i:j].strip()
b = b[:i] + ('Each path is scored by the $\\chi^2$ misfit of its predicted bulk-normalized ratios to the central\n'
             'ratios of the bounding method \\citep{thyer2026data}, with uncertainties set by the bounding-method\n'
             'lower and upper bounds (SI, \\S\\ref{sec:ch2-si-chi2}).\n') + b[j:]
LOG.append(f'- **MOVE** [2.2 -> SI S5] chi^2 definition (Eq. gt_mdd_chi2), sigma rule and degrees of freedom moved to new SI subsection '
           f'"Misfit statistic for thermal histories" (heading NEW); NEW one-sentence summary in the main text.\n    - moved: "{short(CHI)}"')

# --- item 7: vacuum kinetics condensed
old = b[span(b, 'KAF alone gives $\\ChTwoKinKAFEa', 'The kinetic rate parameters fitted to KAF alone')[0]:
        span(b, 'KAF alone gives $\\ChTwoKinKAFEa', 'The kinetic rate parameters fitted to KAF alone')[1]]
b = E(b, old, 'Fitting KAF and HDM separately ($\\ChTwoKinKAFEa\\pm\\ChTwoKinKAFEaErr$ and $\\ChTwoKinHDMEa\\pm\\ChTwoKinHDMEaErr$~kJ\\,mol$^{-1}$)\n'
      'or fitting all steps ($\\ChTwoKinAllFOneEa$~kJ\\,mol$^{-1}$) gives consistent results (\\S\\ref{sec:gt_supp_mech}).\n\n',
      '3.2', 'Per-dataset and all-step activation energies condensed to one sentence (BJT item 7).')
old = b[span(b, 'Thermogravimetric studies of goethite dehydroxylation report', '\\subsection{Helium Release under Water-Saturated')[0]:
        span(b, 'Thermogravimetric studies of goethite dehydroxylation report', '\\subsection{Helium Release under Water-Saturated')[1]]
b = E(b, old, 'Thermogravimetric studies report somewhat higher apparent activation energies for goethite\n'
      'dehydroxylation ($154\\pm15$ to $169\\pm8$~kJ\\,mol$^{-1}$; \\citealt{goss1987}), plausibly because\n'
      'dehydroxylation kinetics depend on particle size, morphology, and aluminum content\n'
      '\\citep{langmuir1971,yapp1983,tardy1985,majzlannavrotsky2003}.\n\n',
      '4.1', 'Thermogravimetric comparison condensed to one sentence (BJT item 7).')

# --- item 4: recrystallization / fluid-mediated caveat folded into 4.2; old subsection removed
CAVEAT = ('Two processes other than volume diffusion could have contributed to the water-saturated release.\n'
          'Goethite can recrystallize under hydrothermal conditions \\citep{schwertmann1985}, and fluid-mediated\n'
          'conversion to hematite, which lies outside the solid-state nucleation model of \\S\\ref{sec:gt_nucleation},\n'
          'transformed synthetic goethite pigment heated with excess water (SI, \\S\\ref{sec:gt_pigment}). Either\n'
          'process would likely release essentially all of the helium in the material it affects. Progressive\n'
          'reaction would then make helium release track the extent of reaction, a first-order-like behavior\n'
          'that the water-saturated data do not show (Fig.~\\ref{fig:gt_arrhenius}a), and episodic reaction would\n'
          'produce abrupt excess release in individual steps, which is also not observed\n'
          '(Figs.~\\ref{fig:ch2-arrhenius-zoom} and~\\ref{fig:ch2-delta-zoom}). Their contribution is therefore\n'
          'bounded to be small; to the extent that either contributed, the apparent diffusivities reported here\n'
          'are upper bounds for diffusion in goethite.\n\n')
b = E(b, 'While it is difficult to prove that decomposition or recrystallization is not',
      CAVEAT + 'While it is difficult to prove that decomposition or recrystallization is not',
      '4.2', 'NEW caveat paragraph on recrystallization and fluid-mediated conversion (BJT item 4).')
b, _ = CUT(b, '\\subsection{Goethite Dehydration and/or Recrystallization During Helium Step Heat Experiments}',
           '\\subsection{\\texorpdfstring{High Helium Retentivity of',
           '4.5', 'Whole subsection "Goethite Dehydration and/or Recrystallization..." removed, including the pigment pointer paragraph (now covered by the 4.2 caveat).')

# --- restore the 250 C isothermal test in the Discussion (4.2), after the caveat and before 4.2.1
k = [n for n, l in enumerate(th) if l.startswith('\\subsection{Isothermal Discrimination Test at 250')]
assert len(k) == 1
a = k[0]
e = [n for n in range(a, a + 40) if th[n].strip() == '\\label{fig:gt_hold}'][0] + 1
assert th[e].strip() == '\\end{figure}'
HOLD = '\n'.join(l for l in th[a:e + 1] if not l.lstrip().startswith('%'))
HOLD = HOLD.replace('\\subsection{Isothermal Discrimination Test at 250~$^\\circ$C}',
                    '\\subsubsection{Isothermal Discrimination Test at 250~$^\\circ$C}', 1)
b = E(b, '\\subsubsection{Consistency with MDD Systematics}',
      HOLD + '\n\n\\subsubsection{Consistency with MDD Systematics}', '4.2.1 (new)',
      'Thesis "Isothermal Discrimination Test at 250 C" (thesis L713-736: text + Fig. gt_hold) restored verbatim as a subsubsection of 4.2 (BJT: discussion, not results); only \\subsection -> \\subsubsection.')

# --- item 3: speculation in the 4He/3He section
old = b[span(b, 'Goethite aggregates are known to have interstices that are filled by', 'The hydrothermal experiment records lower bulk-normalized')[0]:
        span(b, 'Goethite aggregates are known to have interstices that are filled by', 'The hydrothermal experiment records lower bulk-normalized')[1]]
b = E(b, old, '\n\n', '4.4 para 1', 'Interstitial-water / LRD speculation removed (BJT item 3); the one-sentence "fine grains or interstitial helium" remark is kept.')
old = b[span(b, 'differs between the hydrothermal and vacuum experiments, and could be explained by the relative', '\\begin{figure}[htbp]\n\\centering\n\\includegraphics[width=\\textwidth]{Ch2_spectra_combined.pdf}')[0]:
        span(b, 'differs between the hydrothermal and vacuum experiments, and could be explained by the relative', '\\begin{figure}[htbp]\n\\centering\n\\includegraphics[width=\\textwidth]{Ch2_spectra_combined.pdf}')[1]]
b = E(b, old, 'differs between the hydrothermal and vacuum experiments.\n\n', '4.4 para 2',
      'Speculative mechanism for the geometry difference removed; the conclusion sentence is kept (BJT item 3).')

# --- item 2: isothermal family in the thermal-history section
b = E(b, 'we fitted steady-cooling,\nburial-and-exhumation, and isothermal thermal histories', 'we fitted steady-cooling and\nburial-and-exhumation thermal histories',
      '4.5 para 1', 'Isothermal family removed from the list (BJT item 2).')
old = b[span(b, '\\paragraph{Isothermal hold}', '\\paragraph{Where the families differ}')[0]:span(b, '\\paragraph{Isothermal hold}', '\\paragraph{Where the families differ}')[1]]
b = E(b, old, 'Isothermal histories, which constrain only the product of diffusivity and time, cannot reproduce\n'
      'the shape of the spectrum and are not considered further (Table~\\ref{tab:ch2-mdd-thermal}).\n\n',
      '4.5', 'Isothermal-hold paragraph replaced by one sentence (BJT item 2).')

# --- conclusions: keep consistent with the new caveat
b = E(b, 'Fluid-mediated conversion, which transformed synthetic goethite pigment under similar conditions,\n'
      'would be accompanied by abrupt helium loss that is not observed. Recrystallization, however,\n'
      'cannot be excluded; if it contributed, the diffusivities reported here are upper bounds and the\n'
      'retentivity a lower bound.',
      'Recrystallization and fluid-mediated conversion, which transformed synthetic goethite pigment under\n'
      'similar conditions, would likely degas the affected material completely; the smooth, diffusive\n'
      'release bounds their contribution to be small. If either contributed, the diffusivities reported\n'
      'here are upper bounds and the retentivity a lower bound.',
      '5 Conclusions', 'Closing caveat aligned with the new 4.2 argument.')
b = re.sub(r'\n{3,}', '\n\n', b)
open(B, 'w', encoding='utf-8').write(b)

# =====================================================================
# SUPPLEMENT
# =====================================================================
s = E(s, 'the two reductions can be compared directly, and that comparison is used below (\\S\\ref{complete-degas-test}) as an internal test of the bounding method.',
      'the two reductions can be compared directly; that comparison, an internal test of the bounding method, is given by \\citet{thyer2026thesis}.',
      'SI S1.1 para 2', 'Pointer to the removed complete-degas test -> thesis.')
s, _ = CUT(s, '\\subsection{Consistency of the Bounding Method with Direct Permeation-Step Quantification', '\\section{Analytical Methods}',
           'SI S1.2', 'Complete-degas test (text + Fig. nt vs ntSS) removed; thesis cited instead (BJT item 8).')
s = E(s, '\\label{fig:ch2-ampoule-dims}\n\\end{figure}', '\\label{fig:ch2-ampoule-dims}\n\\end{figure}\n\n' + FIG_AMP,
      'SI S1', 'Fig. ch2-ampoule-post moved in from the main text (MOVE).')
s, _ = CUT(s, '\\subsection{Uncertainty for Diffusivity Inversions}', '\\section{Kinetic mechanisms and the limits',
           'SI S2', 'Diffusivity-inversion and isotope-ratio uncertainty derivations removed; thesis cited in the main text (BJT item 8).')
s = E(s, '\\section{Analytical Methods}\\label{ch2-analytical-methods}\n',
      '\\section{Analytical Methods}\\label{ch2-analytical-methods}\n\n\\subsection{Final Step}\\label{sec:ch2-si-finalstep}\n\n' + FINAL + '\n\n',
      'SI S2', 'Final-step blank / re-extract / sensitivity text moved in from the main text (heading NEW).')
s, _ = CUT(s, '\\subsection{Two-domain alternative}', '\\clearpage\n\\section{Fluid-Mediated',
           'SI S5', 'Two-domain alternative removed (BJT item 8).')
s = E(s, '\\clearpage\n\\section{Fluid-Mediated',
      '\\subsection{Misfit statistic for thermal histories}\\label{sec:ch2-si-chi2}\n' + CHI + '\n\n\\clearpage\n\\section{Fluid-Mediated',
      'SI S5', 'chi^2 definition moved in from the main text (heading NEW).')
s = re.sub(r'\n{3,}', '\n\n', s)
open(S, 'w', encoding='utf-8').write(s)

with open(os.path.join(HERE, 'PORT_CHANGELOG.md'), 'a', encoding='utf-8') as fh:
    fh.write('\n## Slimming pass 2 (2026-11-02, BJT items 2-8 + 250 C test restored). Backups: `*.pre_slim2_20261102`.\n\n')
    fh.write('\n'.join(LOG) + '\n')
print('\n'.join(l.split('\n')[0] for l in LOG))
