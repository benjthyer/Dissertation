#!/usr/bin/env python3
"""
build_paper_from_chapter1.py -- ONE-SHOT port of thesis Chapter 1 into the
Copernicus (Geochronology) methods paper, run 2026-10-30.

Builds the paper ONLY by moving blocks of chapter1_body.tex /
chapter1_SI_body.tex verbatim; every place where wording differs from the
thesis is an explicit, logged edit (E/NEW below), and the log is written to
Chapter1/Paper/PORT_CHANGELOG.md.  Full-line LaTeX comments are dropped.

Outputs
  Writing/TubeMethodPaper_body.tex      main text (Intro..Conclusions)
  Writing/TubeMethodPaper_SI_body.tex   supplement body
  Writing/TubeMethodPaper.tex           wrapper (old one backed up)
  Writing/SI.tex                        SI wrapper (old one backed up)
  Paper/PORT_CHANGELOG.md

After this run the paper files are the source of truth; edit them directly
(re-running this script would discard those edits).
"""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, '..', 'Writing')
STAMP = '20261030'

body = open(os.path.join(W, 'chapter1_body.tex'), encoding='utf-8').read().split('\n')
si = open(os.path.join(W, 'chapter1_SI_body.tex'), encoding='utf-8').read().split('\n')

LOG = []          # (where, kind, detail)


def blk(src, a, b, expect=None):
    """Lines a..b (1-indexed, inclusive) of src with full-line comments
    removed.  `expect` must be a prefix of line a (guards against drift)."""
    if expect is not None:
        assert src[a - 1].lstrip().startswith(expect), (a, src[a - 1][:80], expect)
    keep = [l for l in src[a - 1:b] if not l.lstrip().startswith('%')]
    return '\n'.join(keep).strip('\n')


def E(text, old, new, where, note):
    n = text.count(old)
    assert n == 1, f'{where}: expected 1 match, found {n}: {old[:70]!r}'
    LOG.append((where, 'EDIT', f'{note}\n    - was: "{old.strip()}"\n    - now: "{new.strip()}"'
                if new.strip() else f'{note}\n    - deleted: "{old.strip()}"'))
    return text.replace(old, new)


def NEW(text, where, note):
    LOG.append((where, 'NEW', f'{note}\n    > {text.strip()[:400]}{"..." if len(text.strip()) > 400 else ""}'))
    return text


def CUT(where, note):
    LOG.append((where, 'CUT', note))


def MOVE(where, note):
    LOG.append((where, 'MOVE', note))


P = []   # main body pieces
S = []   # SI body pieces

# ======================================================================
# MAIN TEXT
# ======================================================================
P.append(blk(body, 45, 47, '\\providecommand{\\tophline}'))

# ---- Introduction (verbatim)
P.append(blk(body, 49, 57, '\\section{Introduction}'))

# ---- Experimental Methods
P.append(blk(body, 59, 66, '\\section{Experimental Methods}'))
t = blk(body, 68, 68, 'Five helium step heat')
t = E(t, 'Five helium step heat experiments', 'Four helium step heat experiments',
      'Methods para 1', 'Quadrupole empty-ampoule experiment dropped')
t = E(t, 'Four of these experiments involved', 'Three of these experiments involved',
      'Methods para 1', 'Quadrupole empty-ampoule experiment dropped')
t = E(t, ' outlined in this chapter to helium', ' outlined in this work to helium',
      'Methods para 1', 'chapter -> work')
t = E(t, ', and to reproduce measurements of permeability rates from the literature \\citep{norton1953,jones1953,swets1961,altemose1961}', '',
      'Methods para 1', 'Data-driven framing: permeability reproduction is no longer a stated aim')
P.append(t)
t = blk(body, 78, 95, '\\begin{table}[t]')
t = E(t, 'Ampoules labeled ``Quad\'\' had evolved 4He quantified by isotope dilution using a Pfeiffer Prisma QMS 200 quadrupole mass spectrometer, whereas the ampoule labeled ``MC\'\' had both',
      'The ampoule labeled ``Quad\'\' had evolved 4He quantified by isotope dilution using a Pfeiffer Prisma QMS 200 quadrupole mass spectrometer, whereas ampoules labeled ``MC\'\' had both',
      'Table 1 caption', 'Only one Quad ampoule (Durango) remains')
t = E(t, 'Empty & Quad & 630 & 960 & 4785 & 1.32 & --- & Atmosphere \\\\\n', '',
      'Table 1', 'Quadrupole empty-ampoule row removed')
P.append(t)
P.append(blk(body, 97, 99, 'To prepare the silica glass ampoules'))
t = blk(body, 101, 101, 'Except for the encapsulated Durango')
t = E(t, ' About 15 nccSTP of atmospheric helium was introduced into the empty ampoule used for the quadrupole mass spectrometer experiment by heating the ampoule in a muffle furnace to \\textgreater400°C in atmosphere overnight, which was sufficient to support a short permeation experiment of 4He. However, to conduct step heat permeation experiments on 3He, much larger quantities of helium were necessary.', '',
      'Methods, helium loading', 'Quadrupole empty-ampoule loading removed')
t = E(t, 'ampoules and the other empty ampoule were soaked', 'ampoules and the empty ampoule were soaked',
      'Methods, helium loading', '"other" removed (only one empty ampoule remains)')
P.append(t)
P.append(blk(body, 103, 107, 'The sealed ampoules were placed'))
t = blk(body, 109, 109, 'Helium isotope measurements of evolved')
t = E(t, ' Every few hours, the background was mass-scanned to set the 3He and 4He measure points; each was taken to be a constant mass offset from the background HD\\textsuperscript{+} peak. These mass offsets are precisely measured when tuning the Helix-MC-Plus\\textsuperscript{10K} for helium isotope analysis. Months of helium measurements with the Helix-MC-Plus\\textsuperscript{10K} at Caltech have shown this approach to be reliable, reproducible, and accurate for helium isotope analysis.', '',
      'Methods, MC mass spectrometry', 'Peak-centering routine detail cut (in thesis)')
P.append(t)
t = blk(body, 111, 111, 'Helium-4 evolved during step heats')
t = E(t, 'Helium-4 evolved during step heats of the empty silica glass ampoule equilibrated with atmosphere and the silica glass-encapsulated Durango apatite was quantified',
      'Helium-4 evolved during the step heat of the silica glass-encapsulated Durango apatite was quantified',
      'Methods, quadrupole', 'Quadrupole empty-ampoule experiment dropped')
P.append(t)
t = blk(body, 113, 113, 'A standard gas with a known amount')
t += ' ' + NEW('Further analytical details are given by \\citet{thyer2026thesis}.',
               'Methods, end of analytical paragraphs', 'Pointer to the dissertation for cut details')
P.append(t)

# ---- Theoretical Framework
P.append(blk(body, 115, 122, '\\section{Theoretical Framework'))
P.append(blk(body, 124, 124, 'The process of helium permeation'))
MOVE('Fig. durango-stepwise-yields (DurangoStepYields_RelativeAnomaly)', 'main -> SI (Sect. "Additional figures and tables")')
MOVE('Fig. simulated-arrhenius-lag-artifact (Apatite_diff_sim1.1)', 'main -> SI')
MOVE('Table heating-schedule', 'main -> SI')
P.append(blk(body, 162, 185, 'This effect can be modeled'))
t = blk(body, 187, 192, 'Helium permeation through fused silica in diffusive')
t = E(t, '\\frac{dn}{dt} = \\  - GKnRT', '\\frac{dn}{dt} = - \\lambda n',
      'Theory, Eq. (permode)', 'Main-text first-order law written with the rate constant; the K/G form moves to SI Sect. S1 (Eq. permodeK)')
P.append(t)
orig194 = blk(body, 194, 194, 'Where \\emph{n} is the number of helium atoms')
t194 = NEW('Where \\emph{n} is the number of helium atoms, \\emph{t} is the time, and \\(\\lambda\\) is the ampoule\'s permeation rate constant, which depends on the helium permeability of the glass and the geometry of the ampoule (\\(\\lambda = KGRT\\); Supplement, Sect.~\\ref{sec:s-lambda-K}). It is easily integrated by separation of variables to yield \\(n_{t} = n_{0}e^{- \\lambda t}\\) (see supplement, \\S\\ref{a-ficks-law-formulation}, for details). Relating that result to the measured quantity through Eq.~\\eqref{eq:permlag} in the absence of any release from the sample \\(\\left( m(\\omega = 0) = n_{0} - n_{t} \\right)\\) gives an expression most intuitively stated in terms of the fraction of the ampoule\'s initial helium reservoir that permeates during time \\emph{t}:',
           'Theory, paragraph after Eq. (permode)',
           'Rewritten from thesis paragraph: kept "Where n ... time," and "It is easily integrated ... during time t:" verbatim; replaced the K/G/R/T definitions with one clause defining lambda; e^{-GKRTt} -> e^{-lambda t}. Full original paragraph moved to SI Sect. S1.')
P.append(t194)
t = blk(body, 196, 199, '\\begin{equation}')
t = E(t, ', \\qquad \\lambda = KGRT', '', 'Theory, Eq. (permsol)', 'lambda = KGRT removed from main-text equation (now in SI)')
P.append(t)
t = blk(body, 201, 201, 'Where \\(^{He}F\\) is the fractional')
t = E(t, 'Collecting \\emph{K}, \\emph{G}, \\emph{R}, and \\emph{T} into \\(\\lambda\\) is useful because \\(\\lambda\\) is the quantity that can be measured directly during an experiment (\\S\\ref{in-situ-rate-constant}), whereas \\emph{K} and \\emph{G} cannot be separated without independent knowledge of the ampoule geometry.',
      '\\(\\lambda\\) is the quantity that can be measured directly during an experiment (\\S\\ref{in-situ-rate-constant}).',
      'Theory, after Eq. (permsol)', 'Permeability/geometry clauses removed')
P.append(t)
MOVE('Theory: "The geometric factor G ..." + Eq. (geomfactor) + "where a is ..."', 'main -> SI Sect. S1 (verbatim)')
P.append(blk(body, 212, 220, 'Equation~\\eqref{eq:permsol} is only strictly valid'))
MOVE('Fig. diffusive-profile-reequilibration-time', 'main -> SI')

# ---- Experimental approaches
P.append(blk(body, 231, 246, '\\section{Experimental Approaches'))
t = blk(body, 248, 248, 'Equation~\\eqref{eq:n0perm} requires')
t = E(t, 'for the ampoule in use, \\(\\lambda = KGRT\\).', 'for the ampoule in use, \\(\\lambda\\).',
      'Permeation step method, para 3', 'lambda = KGRT -> lambda')
t = E(t, ' That measurement is best understood as a prerequisite and extension of the permeation step method rather than as an alternative to it: the consecutive isothermal permeation steps it requires are already part of the method, so the only additional cost is the discipline of running enough of them in sequence.', '',
      'Permeation step method, para 3', 'Duplicate of the "costs little to measure" paragraph of the in-situ section')
P.append(t)
P.append(blk(body, 250, 250, '\\subsection{Measuring the Ampoule'))
CUT('In-situ section, para 1 ("The permeability coefficient K of helium through nominally anhydrous silica glass is well known...")',
    'Duplicates permeation-step para 3 (literature K unreliable, water, volume effect)')
t = blk(body, 254, 254, 'Fortunately, the rate constant')
t = E(t, 'written with the rate constant \\(\\lambda = KGRT\\) defined above', 'written with the rate constant \\(\\lambda\\) defined above',
      'In-situ section, para 2', 'lambda = KGRT -> lambda')
P.append(t)
P.append(blk(body, 256, 277, '\\begin{equation}'))
t = blk(body, 279, 279, 'In addition to the initial helium contents')
t = E(t, 'this procedure simultaneously determines the product of the permeability and geometric factor for the silica glass ampoule. Once \\(\\lambda = \\ KGRT\\) has been satisfactorily constrained over a range of temperatures, the activation energy \\emph{E\\textsubscript{a}} of permeation and the product of the geometric factor and permeability at infinite temperature, \\emph{K\\textsubscript{0}G}, can be fit using linear regression. Determining these values allows for extrapolation of the permeability to the high temperatures of the experimental steps, which can be useful to an experimentalist who wishes to design a heating schedule wherein the permeation lag is negligible for some experimental steps but does not know the permeability coefficient \\emph{K} and/or the geometric factor \\emph{G.}',
      'this procedure simultaneously determines the ampoule\'s rate constant \\(\\lambda\\) without separate knowledge of the glass permeability or the ampoule geometry. Once \\(\\lambda\\) has been satisfactorily constrained over a range of temperatures, the activation energy \\emph{E\\textsubscript{a}} of permeation can be fit by linear regression of \\(\\ln(\\lambda/T)\\) against \\(1/T\\). It is \\(\\lambda/T\\), rather than \\(\\lambda\\), that follows the Arrhenius law: permeation is driven by the helium partial pressure inside the ampoule, which for a fixed helium inventory scales with \\emph{T} (ideal gas law), so \\(\\lambda/T\\) is proportional to the Arrhenian permeability of the glass (Supplement, Sect.~\\ref{sec:s-lambda-K}). Determining these values allows for extrapolation of \\(\\lambda\\) to the high temperatures of the experimental steps, which can be useful to an experimentalist who wishes to design a heating schedule wherein the permeation lag is negligible for some experimental steps.',
      'In-situ section, Arrhenius paragraph', 'K0G/permeability language replaced by an Arrhenius fit of ln(lambda/T); added the justification for lambda/T')
P.append(t)
P.append(blk(body, 281, 285, 'The rate constant costs little'))
MOVE('Fig. long-step-relative-uncertainty (UncertEstLongStep)', 'main -> SI')
P.append(blk(body, 294, 297, '\\begin{equation}'))
t = blk(body, 299, 299, 'Equation~\\eqref{eq:steadystate} only applies')
t = E(t, 'which requires that G and K are known or can be conservatively estimated.', 'which requires that \\(\\lambda\\) is known or can be conservatively estimated.',
      'Bounding method, para 2', 'G and K -> lambda')
P.append(t)
P.append(blk(body, 301, 307, 'Using the steady state concentrations'))

# ---- Analytical methods
P.append(blk(body, 309, 309, '\\section{Analytical Methods}'))
P.append(NEW('For the empty ampoule experiment, the rate constant \\(\\lambda\\) and the ampoule\'s initial helium content \\(n_{0}\\) were fit independently for \\textsuperscript{3}He and \\textsuperscript{4}He to each run of consecutive isothermal permeation steps using Eq.~\\eqref{eq:incyield} (\\S\\ref{in-situ-rate-constant}). The first step after each temperature change was excluded, because the glass had not yet reached a diffusive steady state (assumption 2 of \\S\\ref{theoretical-framework-of-permeation-lag}). The last two 250\\textdegree C accumulations, which permeated anomalously fast in both isotopes immediately before the anomalous final measurement described below, were also excluded.',
             'Analytical methods, para 1', 'Replaces "Permeabilities were calculated for the empty ampoule experiments by solving Eq. (permsol) for permeability K." Describes the Check A fitting protocol.'))
CUT('Analytical methods, para 1 ("Permeabilities were calculated ... for permeability K.")', 'Replaced by the in-situ fitting description above')
t = blk(body, 313, 313, 'Besides the encapsulated Durango experiment')
t = E(t, 'using the total yield. ', 'using the total yield; these independently known values were used only to evaluate the in-situ fits. ',
      'Analytical methods, total-yield paragraph', 'Clarifies role of the total-yield inventories')
t = E(t, ' The atmosphere-equilibrated empty tube experiment on the Pfeiffer Prisma QMS 200 quadrupole mass spectrometer was pumped for 15 minutes between steps, the encapsulated apatite experiment was pumped for 5 minutes between steps,',
      ' The encapsulated apatite experiment was pumped for 5 minutes between steps,',
      'Analytical methods, total-yield paragraph', 'Quadrupole empty-ampoule pump-out removed')
t = E(t, 'This pump-out time was short enough to neglect for all but the atmosphere-equilibrated empty tube, whose longer 15-minute pump-out and short (45-minute) heated steps required small explicit pump-out and gas-preparation corrections using Eq.~\\eqref{eq:permsol}; see the supplement, \\S\\ref{pump-out-and-gas-preparation-corrections}, for the full derivation.',
      'This pump-out time was short enough to neglect.',
      'Analytical methods, total-yield paragraph', 'Quadrupole-only correction removed')
P.append(t)
P.append(blk(body, 315, 317, 'One high temperature measurement'))
P.append(NEW('All permeation steps of the encapsulated Durango apatite experiment were run at 23.5--24.3\\textdegree C, so a single rate constant governs every \\(n_{0}\\) used in its correction. To let the data determine that rate constant, the correction was repeated for a range of trial rate constants at 25\\textdegree C (\\(\\lambda_{25}\\)), each of which scales every solved \\(n_{0}\\) by the same factor, and the linearity of the corrected Arrhenius array below the high-temperature curl (the \\PaperDurangoNsteps{} steps at \\(\\leq\\)300\\textdegree C that precede the first step above 300\\textdegree C, excluding steps with corrected yields within 2$\\sigma$ of 0) was quantified by the coefficient of determination \\(R^{2}\\) of a linear regression of \\(\\ln(D/a^{2})\\) on \\(1/T\\). The uncertainty of the \\(R^{2}\\)-maximizing \\(\\lambda_{25}\\) was estimated with a leave-one-step-out jackknife. The diffusion parameters of \\citet{farley2000} are not used in this procedure.',
             'Analytical methods, after the Durango paragraph', 'Check B (self-calibration of lambda_25) method'))
P.append(blk(body, 319, 321, '\\subsection*{Numerical Diffusive'))

# ---- Results
P.append(blk(body, 323, 323, '\\section{Results}'))
P.append(NEW('''\\begin{figure}[t]
\\centering
\\includegraphics[width=8.3cm]{InSituLambdaArrhenius.pdf}
\\caption{(a) Permeation rate constants \\(\\lambda\\) of the empty ampoule fit in situ to consecutive isothermal permeation steps (Eq.~\\eqref{eq:incyield}) for \\textsuperscript{4}He (circles) and \\textsuperscript{3}He (squares), plotted as \\(\\ln(\\lambda/T)\\) against inverse temperature. Filled symbols are over-determined fits of three or more steps; open symbols are exactly determined two-step fits. Lines are predictions from the measured ampoule geometry and literature permeabilities \\citep{swets1961,jones1953}, shown only as a check. (b) Ratio of the fitted \\textsuperscript{3}He and \\textsuperscript{4}He rate constants compared with \\citet{jones1953}; \\citet{mcmurtry2019} report isotopic fractionations of up to a factor of 1000. Error bars are 2$\\sigma$.}
\\label{fig:insitu-lambda}
\\end{figure}''', 'Results', 'New Fig. (Check A)'))
P.append(NEW('Rate constants fit in situ to consecutive isothermal permeation steps of the empty ampoule are shown in Fig.~\\ref{fig:insitu-lambda} and listed in Table~\\ref{tab:s-insitu-lambda}. Where three or more steps were available after the glass had re-equilibrated (175 and 250\\textdegree C; cumulative \\(\\lambda t\\) of 0.4--2.3), the fits recover the ampoule\'s helium content, which is known independently from the total yield but was not used in the fits, to within \\PaperNzeroMaxPctFourHe\\,\\% for \\textsuperscript{4}He and \\PaperNzeroMaxPctThreeHe\\,\\% for \\textsuperscript{3}He. Exactly determined two-step fits with cumulative \\(\\lambda t \\lesssim 0.5\\) are biased by up to \\PaperNzeroMaxPctTwoStep\\,\\% in \\(n_{0}\\), illustrating the conditioning requirement of \\S\\ref{in-situ-rate-constant}. The fitted rate constants follow an Arrhenius relationship in \\(\\lambda/T\\) with an activation energy of \\PaperEaFourHe\\,kJ\\,mol\\textsuperscript{-1} for \\textsuperscript{4}He, and the well-conditioned fits fall within \\PaperLamPredMaxPct\\,\\% of the rate constants predicted from the measured ampoule geometry and literature permeabilities \\citep[\\PaperEaLit\\,kJ\\,mol\\textsuperscript{-1};][]{swets1961} (Fig.~\\ref{fig:insitu-lambda}a). That prediction is only a check: neither the ampoule geometry nor literature permeabilities are needed to obtain \\(\\lambda\\). These temperatures (125--250\\textdegree C) are too high for permeation steps of apatite or similarly retentive phases, which must be effectively closed to helium loss during permeation steps (generally below \\textasciitilde100\\textdegree C, and lower for less retentive phases), but the procedure is identical at lower temperatures and only requires longer cumulative times because \\(\\lambda\\) is smaller. For the empty ampoule of this work, reaching \\(\\lambda t_{cum} \\approx 0.5\\) would take about \\PaperHoursLamTHalfEighty\\,h at 80\\textdegree C and \\PaperHoursLamTHalfTwentyFive\\,h at 25\\textdegree C; narrower or thinner-walled ampoules shorten these times.',
             'Results, para 1', 'Check A results'))
P.append(NEW('The same fits provide an isotopic fractionation check (Fig.~\\ref{fig:insitu-lambda}b): the well-conditioned fits give \\(\\lambda(^{3}\\mathrm{He})/\\lambda(^{4}\\mathrm{He})\\) = \\PaperRatioMin--\\PaperRatioMax, close to the ratio reported by \\citet{jones1953} and far from the fractionations of \\citet{mcmurtry2019}.',
             'Results, para 2 (lead sentence)', 'Isotope-ratio check from the in-situ fits (the thesis 3He/4He paragraph it used to precede now lives only in the SI)'))
MOVE('Results: thesis 3He/4He paragraph ("Permeation ratios for 3He and 4He ...")', 'removed from main text; an identical paragraph already exists in the SI literature-comparison section')
P.append(blk(body, 332, 334, 'Predicted and measured fractional yields'))
MOVE('Fig. he4-error-histogram (Histograms4He)', 'main -> SI, regenerated without the quadrupole ampoule (Histograms4He_MC.pdf)')
P.append(blk(body, 338, 338, 'The permeation lag-corrected helium'))
MOVE('Table apatite-stepheat', 'main -> SI (verbatim)')
P.append(NEW('''\\begin{figure}[t]
\\centering
\\includegraphics[width=8.3cm]{DurangoLambdaSelfCalibration.pdf}
\\caption{Coefficient of determination (\\(R^{2}\\)) of a linear regression of permeation lag-corrected \\(\\ln(D/a^{2})\\) on \\(1/T\\) for the \\PaperDurangoNsteps{} encapsulated Durango apatite steps below the high-temperature curl, as a function of the trial rate constant at 25\\textdegree C used to solve every permeation step (Eq.~\\eqref{eq:n0perm}). The data select \\(\\lambda_{25}\\) (blue line; the shaded band is the 2$\\sigma$ leave-one-step-out jackknife range). The prediction from the measured ampoule geometry and literature permeabilities (red dashed line) is shown only as a check.}
\\label{fig:durango-lambda-selfcal}
\\end{figure}''', 'Results', 'New Fig. (Check B)'))
P.append(NEW('The encapsulated Durango apatite data also determine their own rate constant. The linearity of the corrected Arrhenius array below the high-temperature curl is greatest at \\(\\lambda_{25}\\) = \\PaperLamTwentyFiveData{} \\(\\pm\\) \\PaperLamTwentyFiveDataTwoSigma{} \\(\\times 10^{-6}\\)\\,s\\textsuperscript{-1} (2$\\sigma$; \\(R^{2}\\) = \\PaperDurangoRtwoMax; Fig.~\\ref{fig:durango-lambda-selfcal}). The rate constant predicted from the ampoule\'s measured geometry and literature permeabilities, which was used for the correction shown in Fig.~\\ref{fig:durango-arrhenius-lag-corrected} and Table~\\ref{tab:apatite-stepheat} (\\(R^{2}\\) = \\PaperDurangoRtwoPred), is \\PaperLamTwentyFivePred{} \\(\\times 10^{-6}\\)\\,s\\textsuperscript{-1}, a ratio of \\PaperLamTwentyFiveRatio{} that lies within the 10\\,\\% uncertainty propagated for Eq.~\\eqref{eq:permsol}. Because this self-calibration uses only the measured yields, the known total yield, and the expectation that helium diffusion in Durango apatite is Arrhenian below 300\\textdegree C, the agreement of the corrected diffusivities with \\citet{farley2000} remains an independent test of the correction.',
             'Results, last para', 'Check B results'))

# ---- Discussion
t = blk(body, 479, 494, '\\section{Discussion}')
t = E(t, 'the effective permeability of helium roughly scales with the inverse volume fraction of the gas phase',
      'the effective rate constant of helium permeation roughly scales with the inverse volume fraction of the gas phase',
      'Discussion, volume displacement', 'permeability -> rate constant (data-driven framing)')
t = E(t, 'K_{eff} = K_{dry}', '\\lambda_{eff} = \\lambda_{dry}', 'Discussion, Eq. (keff)', 'K -> lambda')
t = E(t, 'Where \\(K_{eff}\\) is the effective helium permeability, \\(K_{dry}\\) is the nominal helium permeability at anhydrous conditions,',
      'Where \\(\\lambda_{eff}\\) is the effective rate constant, \\(\\lambda_{dry}\\) is the rate constant of the same ampoule without water,',
      'Discussion, after Eq. (keff)', 'K -> lambda')
P.append(t)
P.append(blk(body, 496, 507, '\\subsection{Evolving Helium Permeability'))

# ---- Conclusions (verbatim)
P.append(blk(body, 509, 522, '\\section{Conclusions}'))

main = '\n\n'.join(P) + '\n'
n_ch = main.count('this chapter')
main = main.replace('this chapter', 'this work')
if n_ch:
    LOG.append(('Main text (global)', 'EDIT', f'"this chapter" -> "this work" ({n_ch}x)'))

# ======================================================================
# SUPPLEMENT
# ======================================================================
S.append(NEW('\\section{Relating the Rate Constant to Glass Permeability and Ampoule Geometry}\\label{sec:s-lambda-K}',
             'SI Sect. S1 heading', 'New SI section holding the permeability/geometry material moved out of the main text'))
t = blk(body, 187, 194, 'Helium permeation through fused silica in diffusive')
t = E(t, '\\label{eq:permode}', '\\label{eq:permodeK}', 'SI S1', 'Label renamed (main text keeps eq:permode for dn/dt = -lambda n)')
t = E(t, 'Equation~\\eqref{eq:permode} is identical', 'Equation~\\eqref{eq:permodeK} is identical', 'SI S1', 'Label renamed')
t = E(t, ' Relating that result to the measured quantity through Eq.~\\eqref{eq:permlag} in the absence of any release from the sample \\(\\left( m(\\omega = 0) = n_{0} - n_{t} \\right)\\) gives an expression most intuitively stated in terms of the fraction of the ampoule\'s initial helium reservoir that permeates during time \\emph{t}:',
      ' Comparison with main-text Eq.~\\eqref{eq:permode} gives \\(\\lambda = KGRT\\).',
      'SI S1', 'Ending of the moved paragraph adapted to its new location')
t = E(t, '(see supplement, \\S\\ref{a-ficks-law-formulation}, for details)', '(see Sect.~\\ref{a-ficks-law-formulation} for details)',
      'SI S1', 'Self-reference within the SI')
S.append(t)
MOVE('Main-text paragraph defining n, t, G, K, R, T and Eq. (permode) in K form', 'main -> SI S1 (verbatim apart from the edits above)')
S.append(blk(body, 203, 210, 'The geometric factor \\emph{G}'))
S.append(blk(si, 29, 1049, '\\section{A Fick'))
S.append(blk(si, 1050, 1215, '\\section{Estimating permeation lag'))
t = blk(si, 1216, 1242, '\\section{Comparison to Literature')
t = E(t, '{PermeabilityMeasurements.pdf}', '{PermeabilityMeasurements_MC.pdf}', 'SI, literature comparison', 'Quadrupole data removed from figure')
t = E(t, 'Helium permeabilities measured in silica glass ampoules at Caltech on a quadrupole mass spectrometer (4He only) and on a Helix-MC-Plus\\textsuperscript{10K} (both 3He and 4He) multi-collector mass spectrometer are compared',
      'Helium permeabilities measured in an empty silica glass ampoule at Caltech on a Helix-MC-Plus\\textsuperscript{10K} multi-collector mass spectrometer (both 3He and 4He) are compared',
      'SI, Fig. permeability-literature-comparison caption', 'Quadrupole data removed')
t = E(t, 'These experiments on empty tubes at Caltech show', 'This experiment on an empty tube at Caltech shows',
      'SI, Fig. permeability-literature-comparison caption', 'Singular (quadrupole ampoule removed)')
S.append(t)
t = blk(si, 1243, 1243, '\\section{Additional Analytical')
S.append(t)
CUT('SI "Pump-Out and Gas-Preparation Corrections for the Atmosphere-Equilibrated Empty Ampoule"', 'Quadrupole experiment dropped')
S.append(blk(si, 1251, 1257, '\\subsection{Anomalous Signal'))
CUT('SI "Sample Preparation and SEM Imaging of Buffered and Decomposed Sulfides"', 'Orphaned (SEM figure now lives in Chapter 3)')

S.append(NEW('\\section{Additional Figures and Tables Referenced in the Main Text}\\label{sec:s-moved}',
             'SI heading', 'New SI section for floats moved out of the main text'))
S.append(blk(body, 126, 138, '\\begin{figure}[t]'))
S.append(blk(body, 141, 160, '\\begin{table}[t]'))
S.append(blk(body, 224, 229, '\\begin{figure}[t]'))
S.append(blk(body, 287, 292, '\\begin{figure}[t]'))
t = blk(body, 325, 330, '\\begin{figure}[t]')
t = E(t, '{Histograms4He.pdf}', '{Histograms4He_MC.pdf}', 'SI, Fig. he4-error-histogram', 'Quadrupole ampoule removed')
S.append(t)
S.append('\\input{paper_insitu_lambda_table}')
LOG.append(('SI', 'NEW', 'Table s-insitu-lambda (auto-generated by fig_insitu_lambda.py)'))
S.append('\\clearpage\n' + blk(body, 374, 477, '\\begin{chplandscape}'))

# supplementary data tables: drop the quadrupole table
tab = si[1268:]
txt = '\n'.join(tab)
a = txt.index('\\label{tab:s-emptytube-quad}')
start = txt.rfind('\\begin{small}', 0, a)
end = txt.index('\\clearpage', a) + len('\\clearpage')
txt = txt[:start] + txt[end:]
txt = '\n'.join(l for l in txt.split('\n') if not l.lstrip().startswith('%'))
txt = E(txt, '{PredictingPermeation_error_vs_fraction.pdf}', '{PredictingPermeation_error_vs_fraction_MC.pdf}',
        'SI, Fig. predicted-vs-measured-permeation', 'Quadrupole ampoule removed')
txt = E(txt, ' (with some corrections applied to the quadrupole experiment: see main text for details)', '',
        'SI, Fig. predicted-vs-measured-permeation caption', 'Quadrupole ampoule removed')
txt = E(txt, 'For the empty ampoules, except for 3 measurements', 'For the empty ampoule, except for 3 measurements',
        'SI, Fig. predicted-vs-measured-permeation caption', 'Singular (quadrupole ampoule removed)')
CUT('SI table s-emptytube-quad', 'Quadrupole experiment dropped')
S.append(txt.strip())

sibody = '\n\n'.join(S) + '\n'
n_ch = sibody.count('this chapter')
sibody = sibody.replace('this chapter', 'this work')
if n_ch:
    LOG.append(('SI (global)', 'EDIT', f'"this chapter" -> "this work" ({n_ch}x)'))

hdr = ('% =============================================================\n'
       '%  {name}\n'
       '%  Copernicus (Geochronology) manuscript body, ported from thesis\n'
       '%  Chapter 1 on 2026-10-30 by Paper/build_paper_from_chapter1.py.\n'
       '%  Every wording change relative to the thesis is listed in\n'
       '%  Paper/PORT_CHANGELOG.md. This file is now the source of truth for\n'
       '%  the paper; edit it directly.\n'
       '% =============================================================\n\n')
open(os.path.join(W, 'TubeMethodPaper_body.tex'), 'w', encoding='utf-8').write(
    hdr.format(name='TubeMethodPaper_body.tex') + main)
open(os.path.join(W, 'TubeMethodPaper_SI_body.tex'), 'w', encoding='utf-8').write(
    hdr.format(name='TubeMethodPaper_SI_body.tex') + sibody)

# ======================================================================
# WRAPPERS (back up the old ones first)
# ======================================================================
for name in ('TubeMethodPaper.tex', 'SI.tex'):
    src = os.path.join(W, name)
    bak = src + f'.pre_port_{STAMP}'
    if not os.path.exists(bak):
        shutil.copy2(src, bak)

bib = {}
for name in ('TubeMethodPaper.tex', 'SI.tex'):
    txtw = open(os.path.join(W, name + f'.pre_port_{STAMP}'), encoding='utf-8').read()
    for m in re.finditer(r'(\\bibitem\[[^\]]*\]\{([^}]+)\}.*?)(?=\n\s*\n|\\end\{thebibliography\})', txtw, re.S):
        bib.setdefault(m.group(2), m.group(1).strip())
bib['thyer2026thesis'] = ('\\bibitem[Thyer(2026)]{thyer2026thesis}\n'
                          'Thyer, B. J. \\emph{From Surface to Core, Opening New Windows into the Chemistry of Planets '
                          'through Novel Methods in Mass Spectrometry and Machine Learning}. Ph.D. thesis, California '
                          'Institute of Technology, Pasadena, CA, USA (2026).')


def cited(tex):
    keys = set()
    for m in re.finditer(r'\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}', tex):
        keys.update(k.strip() for k in m.group(1).split(','))
    return keys


def bibliography(tex, extra=''):
    keys = cited(tex + extra)
    missing = sorted(k for k in keys if k not in bib)
    items = sorted((bib[k] for k in keys if k in bib), key=lambda s: s.split(']')[0].lower())
    return '\\begin{thebibliography}{}\n\n' + '\n\n'.join(items) + '\n\n\\end{thebibliography}\n', missing


old_main = open(os.path.join(W, f'TubeMethodPaper.tex.pre_port_{STAMP}'), encoding='utf-8').read()
abstract = open(os.path.join(W, 'chapter1_abstract.tex'), encoding='utf-8').read()
pre, _, rest = old_main.partition('\\begin{thebibliography}')
pre = pre.replace('\\usepackage{longtable}\n',
                  '\\usepackage{longtable}\n\\usepackage{xr}\n\\externaldocument{SI}\n\\input{paper_derived_values}\n', 1)
pre = pre.replace('\\input{chapter1_body}', '\\input{TubeMethodPaper_body}')
pre = pre.replace('\\authorcontribution{',
                  '\\codedataavailability{Data and the scripts used to reduce them and to generate all figures will be archived on Zenodo [DOI to be added].}\n\n\\authorcontribution{', 1)
LOG.append(('Wrapper', 'NEW', 'Code and data availability statement (placeholder DOI)'))
bibtxt, miss_main = bibliography(main, abstract)
open(os.path.join(W, 'TubeMethodPaper.tex'), 'w', encoding='utf-8').write(pre + bibtxt + '\n\\end{document}\n')

old_si = open(os.path.join(W, f'SI.tex.pre_port_{STAMP}'), encoding='utf-8').read()
pre, _, rest = old_si.partition('\\begin{thebibliography}')
pre = pre.replace('\\usepackage{longtable}\n',
                  '\\usepackage{longtable}\n\\usepackage{xr}\n\\externaldocument{TubeMethodPaper}\n\\input{paper_derived_values}\n', 1)
pre = pre.replace('\\input{chapter1_SI_body}',
                  '\\renewcommand{\\thesection}{S\\arabic{section}}\n\\renewcommand{\\thefigure}{S\\arabic{figure}}\n'
                  '\\renewcommand{\\thetable}{S\\arabic{table}}\n\\renewcommand{\\theequation}{S\\arabic{equation}}\n'
                  '\\input{TubeMethodPaper_SI_body}')
bibtxt, miss_si = bibliography(sibody)
open(os.path.join(W, 'SI.tex'), 'w', encoding='utf-8').write(pre + bibtxt + '\n\\end{document}\n')

# ======================================================================
# CHANGELOG
# ======================================================================
def words(tex):
    tex = re.sub(r'\\begin\{(equation|table|longtable|figure|chplandscape)\}.*?\\end\{\1\}', ' ', tex, flags=re.S)
    tex = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' ', tex)
    return len(re.findall(r'[A-Za-z]{2,}', tex))


out = ['# Chapter 1 -> Copernicus paper: port change log (2026-10-30)', '',
       'Generated by `Paper/build_paper_from_chapter1.py`. The paper was assembled by moving thesis',
       'blocks verbatim; every wording difference from `chapter1_body.tex` / `chapter1_SI_body.tex`',
       'is listed below. NEW = text not in the thesis; EDIT = changed wording; CUT = removed;',
       'MOVE = relocated without wording change. Full-line LaTeX comments were dropped throughout.', '',
       f'Main-text prose words (approx., excl. equations/floats): thesis {words(chr(10).join(body))} -> paper {words(main)}',
       f'SI prose words (approx.): thesis {words(chr(10).join(si))} -> paper {words(sibody)}', '']
for kind in ('NEW', 'EDIT', 'CUT', 'MOVE'):
    out.append(f'## {kind}')
    out.append('')
    for where, k, detail in LOG:
        if k == kind:
            out.append(f'- **{where}** -- {detail}')
    out.append('')
if miss_main or miss_si:
    out += ['## Missing bibliography entries', '', f'- main: {miss_main}', f'- SI: {miss_si}', '']
open(os.path.join(HERE, 'PORT_CHANGELOG.md'), 'w', encoding='utf-8').write('\n'.join(out))
print('missing main:', miss_main)
print('missing SI:', miss_si)
print('\n'.join(out[:10]))
