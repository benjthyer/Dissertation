#!/usr/bin/env python3
"""move_thermo_to_SI.py -- consolidate the goethite thermodynamic / nucleation
analysis in the GCA paper's SI and replace it in the main text by one summary
subsection (2026-11-02).  Run from Chapter2/Paper/.  Paper files only (the thesis
chapter keeps its structure).  Backups *.pre_thermoSI_20261102."""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', 'Writing'))
TAG = '.pre_thermoSI_20261102'
B = os.path.join(W, 'GoethitePaper_body.tex')
S = os.path.join(W, 'GoethitePaper_SI_body.tex')
LOG = []


def load(p):
    shutil.copy(p, p + TAG)
    raw = open(p, encoding='utf-8', newline='').read()
    return raw.replace('\r\n', '\n'), '\r\n' in raw


def save(p, t, crlf):
    open(p, 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n') if crlf else t)


def cut(t, start, end):
    assert t.count(start) == 1, start[:70]
    i = t.index(start)
    j = t.index(end, i)
    return t[:i], t[i:j], t[j:]


def E(t, old, new, where, note):
    assert t.count(old) == 1, (where, t.count(old), old[:70])
    LOG.append(f'- **EDIT** [{where}] {note}\n    - was: "{" ".join(old.split())[:300]}"\n    - now: "{" ".join(new.split())[:300]}"')
    return t.replace(old, new)


b, bcr = load(B)
s, scr = load(S)

# ------------------------------------------------------------------ main text
# Methods 2.3 out
pre, M23, post = cut(b, '\\subsection{Thermodynamic and Nucleation Model of Goethite Dehydroxylation}\\label{sec:gt_thermo_methods}',
                     '\\subsection{SEM Study of Thermally Treated Goethite}')
b = pre + post
body23 = M23.split('\n', 1)[1].strip('\n')
iA = body23.index('\\textit{Nucleation barrier.}')
M_A, M_B = body23[:iA].strip('\n'), body23[iA:].strip('\n')
LOG.append('- **MOVE** [Methods 2.3 -> SI S4/S5] Subsection "Thermodynamic and Nucleation Model of Goethite Dehydroxylation" removed from the main text: '
           'reaction and Delta G_r (Eqs. gt_rxn, gt_dGr) -> SI S4 lead; nucleation barrier, Turnbull rate law and internal nucleation (Eqs. gt_barrier, gt_knuc) -> SI S5 lead.')
b = E(b, 'The KAF steps run with the trap isolated are also excluded from the Arrhenius regression.\n',
      'The KAF steps run with the trap isolated are also excluded from the Arrhenius regression.\n'
      'A thermodynamic and classical-nucleation model of goethite dehydroxylation, used in\n'
      '\\S\\ref{sec:gt_nucleation} to interpret the effect of water, is described in the SI\n'
      '(\\S\\ref{sec:eqm-thermo}--\\ref{sec:gt_nuc_si}).\n',
      'Methods 2.1 (end)', 'NEW pointer sentence to the SI model sections.')

# Discussion 4.3 + 4.4 -> SI; one summary subsection in their place
pre, DISC, post = cut(b, '\\subsection{Goethite Stability and the Driving Force for Dehydroxylation}\\label{sec:gt_thermo}',
                      '\\subsection{\\texorpdfstring{High Helium Retentivity of')
i1 = DISC.index('This model can be used to calculate the stability field')
i2 = DISC.index('\\subsection{Water Pressure Control')
D_STAB = DISC[i1:i2].strip('\n')
i3 = DISC.index('\\textit{Calibration.}')
D_NUC = DISC[i3:].strip('\n')
LOG.append('- **CUT** [Discussion 4.3 intro] "The preceding sections establish from helium step heat data alone ... (S gt_nucleation)." (superseded by the summary).')
LOG.append('- **MOVE** [Discussion 4.3 -> SI S4] Phase-diagram findings (enumerated list), Fig. gt_PT, driving-force paragraph and Table gt_dmu -> new SI subsection "Stability and driving force".')
LOG.append('- **CUT** [Discussion 4.4 lead] Empirical-bound paragraph (R <= 10^-2.5; 10^-3.8 for <1 %) -- restated in the summary.')
LOG.append('- **MOVE** [Discussion 4.4 -> SI S5] Calibration (Eq. gt_gamma_cal), translation to saturation (Eq. gt_translate) and assumptions paragraphs.')
SUMMARY = r"""\subsection{Why Water Suppresses Dehydroxylation}\label{sec:gt_nucleation}

Under the vacuum kinetics of Eq.~\eqref{eq:gt_line}, the water-saturated heating schedule would have
converted the sample completely ($\sum_i k_{\mathrm{vac}}(T_i)\,\Delta t_i \approx \ChTwoKinSumKdt$). Even if
all of the observed $^3$He release came from conversion ($\alpha = \ChTwoKinHTAlphaObs$), the conversion rate
at water saturation can be at most $10^{\ChTwoKinLogRObs}$ times the vacuum rate, and at most
$10^{\ChTwoKinLogRDetect}$ times for conversion to stay below 1\%. A thermodynamic and
classical-nucleation model of goethite dehydroxylation accounts for this suppression (SI,
\S\ref{sec:eqm-thermo}--\ref{sec:gt_nuc_si}). Goethite is unstable relative to hematite and water both in
vacuum and at water saturation (SI Fig.~\ref{fig:gt_PT}), but water is a product of the reaction, so its
chemical potential sets the driving force $\Delta\mu$. In the vacuum of a step-heating line the water
pressure approaches zero and $\Delta\mu$ is unbounded; at saturation $\Delta\mu$ is only 6--11~kJ per mole
Fe$_2$O$_3$, 1.6--2.4 times $RT$ (SI Table~\ref{tab:gt_dmu}). Because the barrier to nucleating hematite
within goethite scales as $\gamma^3/\Delta\mu^2$ \citep{turnbull1949}, it vanishes in vacuum, consistent
with the simple Arrhenius behavior of both vacuum experiments, but not at saturation. Calibrating the
model's one free parameter, an effective interfacial energy ($\gamma_{\mathrm{eff}} =
\ChTwoKinMCGammaMid$~J\,m$^{-2}$), on the two steps of \citet{farley2024} in which evolved water
accumulated (\S\ref{sec:gt_kin_results}) gives a barrier of \ChTwoKinBarSat~$k_BT$ at saturation and
250~$^\circ$C. The predicted total conversion over the water-saturated schedule is
$10^{\ChTwoKinMCCNTLo}$ to $10^{\ChTwoKinMCCNTHi}$ (95\%), far below what the data require. This
explanation assumes that the trap-isolated slowdown in vacuum acts through $\Delta\mu$ and that
conversion is solid-state; fluid-mediated conversion lies outside it (\S\ref{sec:gt_hydro}).

"""
b = pre + SUMMARY + post
LOG.append('- **NEW** [Discussion 4.3] Subsection "Why Water Suppresses Dehydroxylation" (label sec:gt_nucleation kept), '
           'summarizing the empirical bound, driving force, vanishing vacuum barrier, gamma_eff calibration, barrier at saturation and '
           'Monte Carlo conversion range; all numbers are macros.\n    > ' + ' '.join(SUMMARY.split())[:1500])
b = E(b, '(\\S\\ref{sec:gt_thermo_methods}--\\ref{sec:gt_nucleation})', '(\\S\\ref{sec:gt_nucleation})',
      'Introduction, roadmap', 'Pointer updated (Methods 2.3 removed).')
b = re.sub(r'\n{3,}', '\n\n', b)
assert 'sec:gt_thermo_methods' not in b

# ------------------------------------------------------------------ SI
M_A = E(M_A, 'The values and equations used to evaluate each of these terms are given in the supplement: \\S\\ref{sec:eqm-thermo}.',
        'The values and equations used to evaluate each of these terms are given below.',
        'SI S4 lead (moved text)', 'Self-reference adjusted.')
s = E(s, '\\section{Equilibrium Thermodynamics of Goethite Dehydroxylation}\n\\label{sec:eqm-thermo}\n',
      '\\section{Thermodynamics of Goethite Dehydroxylation}\n\\label{sec:eqm-thermo}\\label{sec:gt_thermo}\n\n' + M_A + '\n',
      'SI S4 heading', 'Section retitled; main-text reaction/Delta G_r text moved in as its lead; label sec:gt_thermo moved here.')
D_STAB = E(D_STAB, 'This model can be used to calculate', 'The model can be used to calculate',
           'SI S4 stability (moved text)', '"This model" -> "The model".')
s = E(s, '\\section{Calibration of $\\gamma_{\\mathrm{eff}}$}\n\\label{sec:gt_supp_barrier}\n',
      '\\subsection{Stability and driving force}\n\n' + D_STAB + '\n\n'
      '\\section{Nucleation Model of Goethite Dehydroxylation}\\label{sec:gt_nuc_si}\n\n' + M_B + '\n\n' + D_NUC + '\n\n'
      '\\subsection{Calibration of $\\gamma_{\\mathrm{eff}}$}\n\\label{sec:gt_supp_barrier}\n',
      'SI S4/S5', 'NEW subsection "Stability and driving force" (moved Discussion text); NEW section "Nucleation Model of Goethite Dehydroxylation" '
      '(moved Methods + Discussion text); old section "Calibration of gamma_eff" demoted to a subsection of it.')
s = E(s, 'suppression far beyond the $10^{\\ChTwoKinLogRDetect}$ that the data require.',
      'suppression far beyond the $10^{\\ChTwoKinLogRDetect}$ that the data require (main text,\n\\S\\ref{sec:gt_nucleation}).',
      'SI S5 translation (moved text)', 'Pointer to the main-text bound added.')
s = re.sub(r'\n{3,}', '\n\n', s)
save(B, b, bcr)
save(S, s, scr)
with open(os.path.join(HERE, 'PORT_CHANGELOG.md'), 'a', encoding='utf-8') as fh:
    fh.write('\n## Thermodynamics consolidated in the SI (2026-11-02, BJT request). Backups `*.pre_thermoSI_20261102`.\n\n' + '\n'.join(LOG) + '\n')
print('\n'.join(l.split('\n')[0] for l in LOG))
