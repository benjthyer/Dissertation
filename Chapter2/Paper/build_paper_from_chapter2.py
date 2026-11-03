#!/usr/bin/env python3
"""
build_paper_from_chapter2.py -- ONE-SHOT port of thesis Chapter 2 into the
GCA (elsarticle) manuscript, run 2026-11-02.

Rules (from BJT):
  * body of the paper: cuts and moves only.  Every place where wording
    differs from the thesis is an explicit, logged edit (EDIT / NEW / CUT-
    inside-paragraph), and the log is written to Chapter2/Paper/PORT_CHANGELOG.md.
  * abstract and conclusions: rewritten (logged as NEW, full text).
  * no data tables -> Zenodo dataset (Thyer, 2026; doi:10.5281/zenodo.22113166).
  * methods offloaded to the Geochronology preprint wherever possible
    (cited as thyer2026method; equation numbers resolved with xr against
    Chapter1/Writing/TubeMethodPaper.aux and SI.aux, prefix "ch1-").
  * the 250 C isothermal discrimination test is cut (re-framing of data
    already in the Arrhenius and delta plots).
Full-line LaTeX comments are dropped.

Outputs (Chapter2/Writing/):
  GoethitePaper.tex, GoethitePaper_abstract.tex, GoethitePaper_body.tex,
  GoethitePaper_SI.tex, GoethitePaper_SI_body.tex, goethite_paper_extra.bib,
  elsarticle.cls + elsarticle-harv.bst (copied from Manuscripts/HydrothermalGoethite/elsarticle)
and Chapter2/Paper/PORT_CHANGELOG.md.

The thesis files (chapter2_body.tex, chapter2goethite_SI_body.tex,
chapter2_abstract.tex) are only read, never written.  The old merged GCA
manuscript in Manuscripts/HydrothermalGoethite/ is left untouched.
After this run the paper files are the source of truth; edit them directly
(re-running this script refuses to overwrite them).
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', 'Writing'))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
OLD = os.path.join(ROOT, 'Manuscripts', 'HydrothermalGoethite')

body = open(os.path.join(W, 'chapter2_body.tex'), encoding='utf-8').read().split('\n')
si = open(os.path.join(W, 'chapter2goethite_SI_body.tex'), encoding='utf-8').read().split('\n')

LOG = []


def blk(src, a, b, expect=None):
    """Lines a..b (1-indexed, inclusive) of src, full-line comments removed.
    `expect` must be a prefix of line a (guards against drift)."""
    if expect is not None:
        assert src[a - 1].lstrip().startswith(expect), (a, src[a - 1][:90], expect)
    keep = [l for l in src[a - 1:b] if not l.lstrip().startswith('%')]
    return '\n'.join(keep).strip('\n')


def _short(s, n=420):
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n] + f' ... [{len(s)} chars]'


def E(text, old, new, where, note, count=1):
    n = text.count(old)
    assert n == count, f'{where}: expected {count} match(es), found {n}: {old[:80]!r}'
    if new.strip():
        LOG.append((where, 'EDIT', f'{note}\n    - was: "{_short(old)}"\n    - now: "{_short(new)}"'))
    else:
        LOG.append((where, 'EDIT', f'{note}\n    - deleted: "{_short(old)}"'))
    return text.replace(old, new)


def X(text, start, end, where, note):
    """Cut from `start` (inclusive) up to `end` (exclusive) inside a block."""
    assert text.count(start) == 1, (where, start)
    s = text.index(start)
    e = text.index(end, s)
    assert text.count(end) == 1, (where, end)
    LOG.append((where, 'CUT', f'{note}\n    - deleted: "{_short(text[s:e], 600)}"'))
    return text[:s] + text[e:]


def NEW(text, where, note, full=False):
    LOG.append((where, 'NEW', f'{note}\n    > ' + (text.strip() if full else _short(text))))
    return text


def CUT(where, note):
    LOG.append((where, 'CUT', note))


def MOVE(where, note):
    LOG.append((where, 'MOVE', note))


P = []   # main body pieces
S = []   # SI body pieces
CITE_M = r'\citet{thyer2026method}'
CITE_Mp = r'\citealt{thyer2026method}'
ZEN = r'\citealt{thyer_2026}'

# ======================================================================
# MAIN TEXT
# ======================================================================
# ---- 1 Introduction (verbatim, incl. the three SEM motivation figures)
P.append(blk(body, 4, 157, '\\section{Introduction}'))
MOVE('1 Introduction', 'Thesis L4-157 verbatim (Introduction + SEM Figs. control/vacuum, buffered, vacuum interior).')

# ---- 2 Methods
t = blk(body, 159, 159, '\\section{Experimental Methods}')
t = E(t, '\\section{Experimental Methods}', '\\section{Methods}', '2 Methods (heading)',
      'Section renamed: it now also holds the thermodynamic/nucleation model (moved from the Discussion).')
P.append(t)
P.append(blk(body, 161, 178, 'This study builds'))
MOVE('2 Methods para 1-2', 'Thesis L161-178 verbatim (sample, irradiation, previous vacuum step heats). TODO comment on the 180-135 vs 130-180 Ma age range dropped with the other comments -- still unresolved, see changelog.')

t = blk(body, 180, 226, 'In this study, an aliquot')
t = X(t, 'Silica glass was chosen over', 'Fig.~\\ref{fig:ch2-ampoule-post} shows the sealed ampoule',
      '2 Methods para 3', 'Ampoule preparation (cleaning, pulling, loading, freeze-pump-seal) offloaded to the Geochronology preprint.')
t = E(t, 'within a silica glass tube. ', 'within a silica glass tube following ' + CITE_M + '. ',
      '2 Methods para 3', 'Citation added in place of the cut ampoule-preparation text.')
P.append(t)
P.append(blk(body, 228, 233, '\\begin{figure}'))
MOVE('2 Methods', 'Fig. ch2-ampoule-post (sealed ampoule after the experiment) kept: it is cited in the recrystallization discussion.')
MOVE('SI S1', 'Fig. ch2-ampoule-dims (ampoule diameter photo, thesis L235-240) moved to the SI, next to the G calculation that cites it.')
CUT('2 Methods', 'Thesis L242 \\clearpage.')

P.append(blk(body, 244, 249, 'The sealed ampoule'))
t = blk(body, 251, 259, 'HT-Win-06-01b was subjected')
# cut the early-trial ampoule-bursting sentence (method-paper material)
s0 = 'In early trials, we found that'
i = t.index(s0)
LOG.append(('2 Methods para 5', 'CUT', 'Early-trial ampoule bursting pressures (86 bar at 300 C, explode >315 C): apparatus material, offloaded.\n    - deleted: "' + _short(t[i:]) + '"'))
t = t[:i].rstrip()
P.append(t)
P.append(blk(body, 261, 270, 'Experimental temperature records'))
CUT('2 Methods para 6', 'Thesis L271-275 (encapsulated vs bare Durango apatite as a temperature check): validation of the method, now in the Geochronology preprint.')
t = blk(body, 277, 299, 'Helium isotope measurements')
t = X(t, 'The majority of the analysis time was spent', 'Measurements of high 3He MM gas standard',
      '2 Methods para 7', 'Mass-spectrometer peak-centering / overspray detail cut (routine; generic to the instrument).')
P.append(t)
P.append(blk(body, 301, 307, 'A cold blank'))
P.append(blk(body, 309, 321, 'For the final step'))
t = blk(body, 323, 331, 'Helium released by the sample')
t = E(t, 'the bounding method of Chapter~\\ref{ch:apparatus} (\\S\\ref{bounding-method})',
      'the bounding method of ' + CITE_M, '2 Methods para 10', 'Thesis-chapter cross-reference -> Geochronology preprint.')
t = E(t, '(Tables~\\ref{tab:ch2-distilled-3he} and~\\ref{tab:ch2-distilled-4he})', '(' + ZEN + ')',
      '2 Methods para 10', 'Data tables removed; Zenodo dataset cited instead.')
P.append(t)

P.append(blk(body, 333, 377, '\\subsection{Kinetic and Diffusive'))
MOVE('2.1', 'Thesis L333-377 verbatim (kinetic and diffusive reductions).')
t = blk(body, 379, 458, '\\subsection{Multiple Diffusion Domain')
t = E(t, '(Table~\\ref{tab:ch2-distilled-4he})', '(' + ZEN + ')', '2.2 Thermal histories',
      'Data table removed; Zenodo dataset cited instead.')
P.append(t)
MOVE('2.2', 'Thesis L379-458 (MDD and thermal-history modeling).')

hdr = NEW('\\subsection{Thermodynamic and Nucleation Model of Goethite Dehydroxylation}\\label{sec:gt_thermo_methods}',
          '2.3 (heading)', 'New heading for the model equations moved out of the Discussion; carries the thesis label sec:gt_thermo_methods.', full=True)
P.append(hdr)
P.append(blk(body, 882, 894, 'Goethite breaks down'))
MOVE('2.3', 'Thesis L882-894 (reaction, Delta G_r, surface term) moved from Discussion 4.4 to Methods.')
P.append(blk(body, 956, 990, '\\textit{Nucleation barrier.}'))
MOVE('2.3', 'Thesis L956-990 (classical nucleation barrier, Turnbull rate law, internal nucleation / gamma_eff) moved from Discussion 4.5 to Methods.')
P.append(blk(body, 460, 479, '\\subsection{SEM Study'))
MOVE('2.4', 'Thesis L460-479 verbatim (SEM study). TODO comments on pigment grade/supplier dropped -- still open, see changelog.')

# ---- 3 Results
P.append(blk(body, 483, 485, '\\section{\\texorpdfstring{Results'))
CUT('3.1', 'Thesis L487 (sentence pointing to the data tables) and L488-621 (landscape Tables ch2-distilled-3he / ch2-distilled-4he) -> Zenodo.')
P.append(blk(body, 623, 664, 'The diffusivities determined'))
P.append(blk(body, 666, 711, '\\subsection{Kinetic Reanalysis'))
CUT('3 Results', 'Thesis L713-736 "Isothermal Discrimination Test at 250 C" and Fig. gt_hold: re-framing of data already in the Arrhenius/delta plots (BJT). Thesis L738 \\clearpage.')

# ---- 4 Discussion
P.append(blk(body, 740, 786, '\\section{Discussion}'))
MOVE('4.1-4.2', 'Thesis L740-786 verbatim (vacuum kinetics; water-saturated release is diffusive).')
P.append(blk(body, 788, 872, '\\subsubsection{Consistency with MDD'))
MOVE('4.2.1', 'Thesis L788-872 verbatim (MDD consistency, domain table and figures).')
t = blk(body, 874, 880, '\\subsection{Thermodynamic Model')
t = E(t, '\\subsection{Thermodynamic Model of Goethite Dehydroxylation}\\label{sec:gt_thermo_methods}\\label{sec:gt_thermo}',
      '\\subsection{Goethite Stability and the Driving Force for Dehydroxylation}\\label{sec:gt_thermo}',
      '4.3 (heading)', 'Heading renamed because the model itself now sits in Methods 2.3; label sec:gt_thermo_methods moved there.')
P.append(t)
P.append(blk(body, 898, 942, 'This model can be used'))
MOVE('4.3', 'Thesis L876-880 and L898-942 (phase diagram, driving forces, Table gt_dmu) kept in the Discussion.')
P.append(blk(body, 944, 954, '\\subsection{Water Pressure Control'))
P.append(blk(body, 992, 1034, '\\textit{Calibration.}'))
MOVE('4.4', 'Thesis L944-954 and L992-1034 (rate bound, calibration, translation, assumptions) kept in the Discussion.')
P.append(blk(body, 1036, 1147, '\\subsection{Goethite Dehydration'))
MOVE('4.5', 'Thesis L1036-1147 verbatim (dehydration/recrystallization caveats; pigment). TODO comment on pigment data sheet dropped.')
P.append(blk(body, 1151, 1199, '\\subsection{\\texorpdfstring{High Helium'))
t = blk(body, 1201, 1274, '\\subsection{Profiling Radiogenic')
t = E(t, '(Table~\\ref{tab:ch2-distilled-4he})', '(' + ZEN + ')', '4.7 para 4',
      'Data table removed; Zenodo dataset cited instead.')
P.append(t)
P.append(blk(body, 1276, 1377, '\\subsection{Thermal History'))
MOVE('4.6-4.8', 'Thesis L1151-1377 verbatim (retentivity; 4He/3He spectra; thermal history).')

# ---- 5 Conclusions (rewritten)
CONC = r"""\section{Conclusions}\label{conclusions}

We applied the silica-glass ampoule method of \citet{thyer2026method} to conduct the first
helium step heat experiment on goethite under water-saturated conditions, using
proton-irradiated goethite Win-06-01b, which has previously been step heated in vacuum. The main
findings are:
\begin{enumerate}
  \item Polycrystalline goethite heated with water does not develop the contraction cracks that
  form in vacuum, and the water-saturated helium release differs fundamentally from release in
  vacuum. Published vacuum step heats of Win-06-01b follow first-order conversion to hematite,
  whereas the water-saturated release shows the history and time dependence of diffusion.
  \item Apparent diffusivities at water saturation are approximately seven natural log units
  lower than those of the same sample in vacuum. Beyond 7\% cumulative $^3$He release they define
  a linear Arrhenius array with an activation energy of \ChTwoEa{}~$\pm$~\ChTwoEaErr{}~kJ/mol, and
  the delta plot follows multiple diffusion domain systematics. A four-domain model places 97\% of
  the $^3$He in a single domain.
  \item Extrapolated to 25\,\textdegree C, this domain is essentially quantitatively retentive of
  helium over billion-year timescales, supporting the use of goethite (U--Th)/He dates to date
  surface processes.
  \item The $^4$He/$^3$He spectrum shows that even this retentive domain lost radiogenic helium in
  nature, and thermally activated diffusion within the four-domain structure can account for that
  loss. Steady cooling from 76--80\,\textdegree C at 150--175~Ma fits the spectrum best, favoring
  crystallization from warm, possibly hydrothermal, fluids; burial of surface-formed goethite to a
  Late Cretaceous peak of 58--65\,\textdegree C, consistent with regional apatite fission-track
  constraints, remains a viable alternative.
  \item The water-saturated $^4$He/$^3$He spectrum rises more gradually than the vacuum spectra of
  the same sample, suggesting that dehydroxylation and diffusion degas goethite with different
  geometries. Vacuum $^4$He/$^3$He spectra of goethite may therefore not encode thermal histories as
  directly as they do for minerals that do not decompose.
  \item A thermodynamic and kinetic analysis explains why water preserves goethite on experimental
  timescales. The water-saturated release requires solid-state conversion to be at least
  $10^{2.5}$ times slower than in vacuum; the roughly tenfold smaller driving force at saturation
  raises the barrier to topotactic hematite nucleation enough to suppress conversion far below
  this limit.
\end{enumerate}

Fluid-mediated conversion, which transformed synthetic goethite pigment under similar conditions,
would be accompanied by abrupt helium loss that is not observed. Recrystallization, however,
cannot be excluded; if it contributed, the diffusivities reported here are upper bounds and the
retentivity a lower bound. Separating the effects of crystallite size, chemical composition, and
radiation damage on helium retention will require further water-saturated step heats of
irradiated goethite of controlled grain size, which this approach makes straightforward."""
P.append(NEW(CONC, '5 Conclusions', 'Conclusions rewritten (BJT allowed liberties). Built from thesis L1381-1434; '
             'method-paper claims (86 bar at 300 C, UHV setups) dropped; findings numbered; '
             '"log units" -> "natural log units".', full=True))

# ---- statements (administrative; carried from the old GCA manuscript / chapter2_contributions.tex)
STATE = r"""\section*{Data Availability}

The step heat data, permeation-lag bounds, and model outputs supporting this study are archived
on Zenodo \citep{thyer_2026}: \url{https://doi.org/10.5281/zenodo.22113166}.

\section*{CRediT authorship contribution statement}

\textbf{Ben J. Thyer:} Conceptualization, Methodology, Investigation, Formal analysis,
Visualization, Writing -- original draft. \textbf{Jonathan Treffkorn:} Methodology,
Investigation. \textbf{Kenneth A. Farley:} Conceptualization, Resources, Supervision, Funding
acquisition, Writing -- review \& editing.

\section*{Declaration of competing interest}

The authors declare that they have no known competing financial interests or personal
relationships that could have appeared to influence the work reported in this paper.

\section*{Acknowledgements}

This work was supported by National Science Foundation (NSF) grant EAR 1945974 to K.A. Farley.
Dr. Paul Asimow is thanked for helpful discussions on the experimental design.

\section*{Declaration of Generative AI and AI-assisted technologies in the writing process}

During the preparation of this work the authors used Claude (Anthropic) to assist with software
programming, and with editing and LaTeX typesetting of the manuscript. After using this tool, the
authors reviewed and edited the content as needed and take full responsibility for the content of
the publication."""
P.append(NEW(STATE, 'Statements', 'Data availability, CRediT, competing interest, acknowledgements and AI declaration '
             'carried over from the old GCA manuscript (Manuscripts/HydrothermalGoethite/hydrothermal_goethite_body.tex L590-616); '
             'CRediT roles updated to chapter2_contributions.tex; Data Availability now cites the Zenodo entry.', full=True))

# ======================================================================
# SUPPLEMENT
# ======================================================================
t = blk(si, 22, 98, '\\section{Permeation Lag Correction')
t = E(t, 'following the permeation step method (Chapter~\\ref{ch:apparatus}, \\S\\ref{permeation-step-method})',
      'following the permeation step method of ' + CITE_M, 'S1.1 para 1', 'Thesis-chapter cross-reference -> preprint.')
t = E(t, 'so Eq.~\\eqref{eq:n0perm} (Chapter~\\ref{ch:apparatus}) could not be',
      'so Eq.~\\eqref{ch1-eq:n0perm} of ' + CITE_M + ' could not be', 'S1.1 para 1', 'Equation reference -> preprint (xr).')
t = E(t, 'the bounding method described in Chapter~\\ref{ch:apparatus} (\\S\\ref{bounding-method}), which',
      'the bounding method described in ' + CITE_M + ', which', 'S1.1 para 2', 'Thesis-chapter cross-reference -> preprint.')
t = E(t, 'calculated using Eq.~\\eqref{eq:steadystate} (Chapter~\\ref{ch:apparatus}). 3He',
      'calculated using Eq.~\\eqref{ch1-eq:steadystate} of ' + CITE_M + '. 3He', 'S1.1 para 2', 'Equation reference -> preprint (xr).')
t = E(t, 'rather than assumed from the literature (Chapter~\\ref{ch:apparatus}, \\S\\ref{in-situ-rate-constant}).',
      'rather than assumed from the literature (' + CITE_Mp + ').', 'S1.1 para 3', 'Thesis-chapter cross-reference -> preprint.')
t = E(t, 'series were fit to Eq.~\\eqref{eq:incyield} using',
      'series were fit to Eq.~\\eqref{ch1-eq:incyield} of ' + CITE_M + ' using', 'S1.1 para 4', 'Equation reference -> preprint (xr).')
t = E(t, 'of Eq.~\\eqref{eq:incyield} (Chapter~\\ref{ch:apparatus}) to data',
      'of Eq.~\\eqref{ch1-eq:incyield} of ' + CITE_M + ' to data', 'Fig. S permeation fits caption', 'Equation reference -> preprint (xr).')
t = E(t, 'similar to observations discussed in Chapter~\\ref{ch:apparatus} (\\S\\ref{resolving-the-paradoxically-high-apparent-helium-permeability-in-water-filled-tubes})',
      'similar to observations discussed in ' + CITE_M, 'S1.1 para 6', 'Thesis-chapter cross-reference -> preprint.')
t = E(t, 'upper bound on the residual helium (Chapter~\\ref{ch:apparatus}, \\S\\ref{bounding-method}).',
      'upper bound on the residual helium (' + CITE_Mp + ').', 'S1.1 para 6', 'Thesis-chapter cross-reference -> preprint.')
t = E(t, 'using Eq.~\\eqref{eq:s6-8} from the supplement to Chapter~\\ref{ch:apparatus} because',
      'using Eq.~\\eqref{ch1-eq:s6-8} from the supplement to ' + CITE_M + ' because', 'S1.1 para 7', 'Equation reference -> preprint SI (xr).')
S.append(t)
S.append(blk(body, 235, 240, '\\begin{figure}'))
MOVE('S1.1', 'Fig. ch2-ampoule-dims moved here from the thesis main text (L235-240).')
CUT('S1', 'SI L100-153 "Measurement and Numerical Simulation of Apparent Permeability of Experimental Ampoule" '
    '(permeability regression, cooling-tube simulation rationale, water-displacement explanation of high apparent '
    'permeability): the explanation is in the preprint (Eq. keff) and the detail in the thesis.')
t = blk(si, 155, 164, '\\subsection{Consistency of the Bounding')
t = E(t, 'presented in this chapter are reduced using the bounding method (Eq.~\\eqref{eq:steadystate})',
      'presented in this study are reduced using the bounding method (Eq.~\\eqref{ch1-eq:steadystate} of ' + CITE_Mp + ')',
      'S1.2 para 1', '"chapter" -> "study"; equation reference -> preprint (xr).')
t = E(t, ' of Fig.~\\ref{fig:ch2-ampoule-permeability} (\\S\\ref{sec:ch2-si-detailed-methods}).',
      ' of Fig.~\\ref{fig:ch2-ampoule-permeability}.', 'S1.2 para 1', 'Pointer to the cut permeation-rate-constant data section removed.')
t = E(t, 'used elsewhere in this chapter)', 'used elsewhere in this study)', 'S1.2 para 1', '"chapter" -> "study".')
t = E(t, '$y$-axis, \\S\\ref{sec:ch2-si-detailed-methods})', '$y$-axis)', 'Fig. S nt vs ntSS caption',
      'Pointer to the cut data section removed.')
t = E(t, '$x$-axis, Eq.~\\eqref{eq:steadystate})', '$x$-axis, Eq.~\\eqref{ch1-eq:steadystate} of ' + CITE_Mp + ')',
      'Fig. S nt vs ntSS caption', 'Equation reference -> preprint (xr).')
S.append(t)
CUT('S1.2', 'SI L166 (permeation-step vs bounding diffusivity concordance paragraph): its figures are cut with the permeation-step dataset section; the Ea agreement is not needed for the argument.')
t = blk(si, 168, 170, 'The two ``complete degas')
t = E(t, '($\\Omega$: \\S\\ref{bounding-method})', '($\\Omega$; ' + CITE_Mp + ')', 'S1.2 para 3', 'Section reference -> preprint.')
t = E(t, '(\\S\\ref{permeation-step-method})', '(' + CITE_Mp + ')', 'S1.2 para 3', 'Section reference -> preprint.')
S.append(t)

S.append(blk(si, 174, 174, '\\section{Analytical Methods}'))
CUT('S2', 'SI L176-208 "Finite Difference Diffusion Model of Cooling Tube" and Fig. goethite-cooling-rate: method detail '
    '(thesis); the permeability-figure caption still describes the modeled points.')
t = blk(si, 210, 272, '\\subsection{Uncertainty for Diffusivity')
t = E(t, 'evaluated using Eq.~\\eqref{eq:steadystate}.', 'evaluated using Eq.~\\eqref{ch1-eq:steadystate} of ' + CITE_M + '.',
      'S2.1', 'Equation reference -> preprint (xr).')
t = E(t, 'measured independently for a water-filled ampoule in Chapter~\\ref{ch:apparatus} (\\S\\ref{results}):',
      'measured independently for a water-filled ampoule by \\citet{thyer2026thesis}:', 'S2.2',
      'This delta value is not in the preprint, so the thesis is cited.')
t = E(t, 'Eq.~\\eqref{eq:steadystate} (Chapter~\\ref{ch:apparatus}): $n_{ss}', 'Eq.~\\eqref{ch1-eq:steadystate} of ' + CITE_M + ': $n_{ss}',
      'S2.2', 'Equation reference -> preprint (xr).')
S.append(t)
CUT('SI', 'SI L274-385: permeation-rate-constant dataset tables, permeation-step 3He dataset table, and the permeation-step/bounding '
    'concordance section with its two figures -> Zenodo / thesis.')
S.append(blk(si, 387, 469, '\\section{Kinetic mechanisms'))
S.append(blk(si, 473, 615, '\\section{Equilibrium Thermodynamics'))
S.append(blk(si, 619, 682, '\\section{Calibration of'))
S.append(blk(si, 685, 745, '\\section{Multiple Diffusion Domain'))
MOVE('S3-S6', 'SI L387-745 verbatim (kinetic mechanisms; equilibrium thermodynamics; gamma_eff calibration; MDD forward model, N=1-5 fits, two-domain alternative).')

# ======================================================================
# ABSTRACT (rewritten)
# ======================================================================
ABS = r"""(U--Th)/He dating of goethite (FeOOH) can directly date weathering, ferruginization, and
laterite formation, but interpreting goethite He dates requires knowing the conditions under
which goethite retains radiogenic helium. Vacuum step heats, the standard tool for characterizing
helium retention, convert goethite to hematite and record dehydroxylation rather than diffusion
\citep{farley2024}. Because high water pressure suppresses dehydroxylation, we used a recently
developed silica-glass ampoule method \citep{thyer2026method} to conduct the first helium step heat
experiment on proton-irradiated goethite under water-saturated conditions. Goethite Win-06-01b
(Flinders Ranges, South Australia) was sealed with distilled water and heated through multiple
prograde and retrograde cycles between 170 and 250\,\textdegree C over about 40 days. Apparent
$^3$He diffusivities are approximately seven natural log units lower than those measured on the
same sample in vacuum and, beyond 7\% cumulative release, define a linear Arrhenius array with an
activation energy of \ChTwoEa{}~$\pm$~\ChTwoEaErr{}~kJ/mol and a closure temperature of
\ChTwoTc{}~$\pm$~\ChTwoTcErr{}\,\textdegree C at 10\,\textdegree C/Ma. Reanalysis of two published
vacuum step heats of the same sample shows that vacuum release follows first-order conversion to
hematite, whereas the water-saturated release shows the history dependence of diffusion and
follows multiple diffusion domain systematics. A four-domain model places 97\% of the $^3$He in a
single domain that is nearly quantitatively retentive at 25\,\textdegree C over billion-year
timescales. The $^4$He/$^3$He spectrum nonetheless requires natural helium loss from this domain,
which thermally activated diffusion can explain: steady cooling from 76--80\,\textdegree C at
150--175~Ma fits best, while burial of surface-formed goethite to a Late Cretaceous peak of
58--65\,\textdegree C, consistent with regional apatite fission-track data, remains viable.
Thermodynamic and nucleation modeling calibrated on the vacuum data shows that the roughly tenfold
smaller driving force at water saturation raises the barrier to hematite nucleation enough to
suppress solid-state conversion on experimental timescales. Fluid-mediated conversion, observed
in synthetic goethite pigment, and recrystallization are not excluded; if either contributed, the
diffusivities are upper bounds. Water-saturated step heats open the way to systematic experiments
on how crystallite size, composition, and radiation damage control helium retention in goethite."""
NEW(ABS, 'Abstract', 'Abstract rewritten and shortened from the 492-word thesis abstract (BJT allowed liberties); '
    '"seven log units" -> "seven natural log units"; method credited to the Geochronology preprint.', full=True)

# ======================================================================
# WRAPPERS
# ======================================================================
PRE = r"""\usepackage{lmodern}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{array}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{subcaption}
\usepackage{lineno}
\usepackage{xr}
\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}
\graphicspath{{../Figures/source/}{../Figures/generated/}}
\input{chapter2_derived_values}
\input{chapter2_kinetics_values}
\input{mdd_free_report_values}
\providecommand{\hl}[1]{#1}
"""
FRONT_AUTH = r"""\author[caltech]{Ben J. Thyer\corref{cor1}}
\ead{bthyer@caltech.edu}
\author[caltech]{Jonathan Treffkorn}
\author[caltech]{Kenneth A. Farley}
\cortext[cor1]{Corresponding author.}
\affiliation[caltech]{organization={Division of Geological and Planetary Sciences, California Institute of Technology},
            city={Pasadena}, postcode={91125}, state={CA}, country={USA}}
"""
TITLE = 'Hydrothermal Helium Step Heats Reveal High Helium Retentivity and Multiple Diffusion Domain Systematics in Goethite'

MAIN = r"""% GoethitePaper.tex -- GCA submission wrapper (elsarticle, review layout).
% Built by Chapter2/Paper/build_paper_from_chapter2.py (2026-11-02); see Chapter2/Paper/PORT_CHANGELOG.md.
% Cross-references: \externaldocument{GoethitePaper_SI} for the SI, and prefix ch1- for the
% Geochronology preprint (Chapter1/Writing/TubeMethodPaper.aux / SI.aux) -- compile those first.
\documentclass[preprint,12pt,review,authoryear]{elsarticle}
\journal{Geochimica et Cosmochimica Acta}
""" + PRE + r"""\externaldocument{GoethitePaper_SI}
\externaldocument[ch1-]{../../Chapter1/Writing/TubeMethodPaper}
\externaldocument[ch1-]{../../Chapter1/Writing/SI}

\begin{document}
\linenumbers
\begin{frontmatter}
\title{""" + TITLE + r"""}
""" + FRONT_AUTH + r"""\begin{abstract}
\input{GoethitePaper_abstract}
\end{abstract}
\begin{keyword}
goethite \sep (U--Th)/He geochronology \sep helium diffusion \sep step heating \sep dehydroxylation \sep multiple diffusion domains
\end{keyword}
\end{frontmatter}

\input{GoethitePaper_body}

\bibliographystyle{elsarticle-harv}
\bibliography{../../references,goethite_paper_extra}
\end{document}
"""
SIW = r"""% GoethitePaper_SI.tex -- Supplementary Information wrapper for GoethitePaper.tex.
% Built by Chapter2/Paper/build_paper_from_chapter2.py (2026-11-02).
\documentclass[preprint,12pt,authoryear]{elsarticle}
\journal{Geochimica et Cosmochimica Acta}
""" + PRE + r"""\externaldocument{GoethitePaper}
\externaldocument[ch1-]{../../Chapter1/Writing/TubeMethodPaper}
\externaldocument[ch1-]{../../Chapter1/Writing/SI}
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\renewcommand{\theequation}{S\arabic{equation}}

\begin{document}
\begin{frontmatter}
\title{Supplementary Information for: """ + TITLE + r"""}
""" + FRONT_AUTH + r"""\end{frontmatter}

\input{GoethitePaper_SI_body}

\bibliographystyle{elsarticle-harv}
\bibliography{../../references,goethite_paper_extra}
\end{document}
"""
BIB = r"""% Entries used only by the GCA goethite manuscript (GoethitePaper*.tex).
@article{thyer2026method,
  author  = {Thyer, Ben J. and Treffkorn, Jonathan and Farley, Kenneth A.},
  title   = {A simple method for helium step heat experiments at high water or sulfur fugacity},
  journal = {Geochronology Discussions},
  year    = {2026},
  note    = {in preparation}
}
@phdthesis{thyer2026thesis,
  author  = {Thyer, Ben J.},
  title   = {Recipes for Rare Metal Ores: Magmas, Metasomatism, and Meteoric Mobilization via Sulfide/Goethite {(U-Th)/He} Geochronology and {ML}-Accelerated Thermodynamic Modeling},
  school  = {California Institute of Technology},
  address = {Pasadena, CA, USA},
  year    = {2026}
}
"""
NEW(BIB, 'goethite_paper_extra.bib', 'Two bib entries (preprint, thesis) kept local so the shared references.bib is untouched; '
    'preprint journal/status is a placeholder ("Geochronology Discussions", in preparation).')

OUT = {
    'GoethitePaper.tex': MAIN,
    'GoethitePaper_SI.tex': SIW,
    'GoethitePaper_abstract.tex': ABS + '\n',
    'GoethitePaper_body.tex': '% Built by Chapter2/Paper/build_paper_from_chapter2.py -- see PORT_CHANGELOG.md\n\n'
                              + '\n\n'.join(P) + '\n',
    'GoethitePaper_SI_body.tex': '% Built by Chapter2/Paper/build_paper_from_chapter2.py -- see PORT_CHANGELOG.md\n\n'
                                 + '\n\n'.join(S) + '\n',
    'goethite_paper_extra.bib': BIB,
}
for name in OUT:
    if os.path.exists(os.path.join(W, name)) and '--force' not in sys.argv:
        sys.exit(f'{name} exists; refusing to overwrite (paper files are the source of truth now)')
for name, txt in OUT.items():
    open(os.path.join(W, name), 'w', encoding='utf-8').write(txt)
for f in ('elsarticle.cls', 'elsarticle-harv.bst'):
    shutil.copy(os.path.join(OLD, 'elsarticle', f), os.path.join(W, f))

# ---------------------------------------------------------------- changelog
with open(os.path.join(HERE, 'PORT_CHANGELOG.md'), 'w', encoding='utf-8') as fh:
    fh.write('# Chapter 2 -> GCA manuscript port (2026-11-02)\n\n'
             'Built by `build_paper_from_chapter2.py` from `Chapter2/Writing/chapter2_body.tex` and '
             '`chapter2goethite_SI_body.tex` (line numbers below refer to those files as of 2026-11-02). '
             'Body text is moved verbatim; every wording change is listed as EDIT, every new string as NEW, '
             'and every removal as CUT. Full-line LaTeX comments were dropped throughout. The abstract and '
             'conclusions were rewritten.\n\n')
    for where, kind, detail in LOG:
        fh.write(f'- **{kind}** [{where}] {detail}\n')
print(f'{len(LOG)} log entries; wrote', ', '.join(OUT))
