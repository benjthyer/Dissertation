#!/usr/bin/env python3
"""slim_mdd_methods.py -- cite Farley & Flowers (2012) and Shuster & Farley (2004)
instead of re-deriving them in the GCA paper (2026-11-03, per K. Farley via BJT).
Main-text Methods 2.2 condensed (equations removed; choices unique to this work kept);
SI: forward-model derivation and chi^2 subsection removed; N = 1-5 fits and the two
result tables kept.  Thesis untouched.  Run from Chapter2/Paper/.
Backups *.pre_mddslim_20261103."""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', 'Writing'))
TAG = '.pre_mddslim_20261103'
B = os.path.join(W, 'GoethitePaper_body.tex')
S = os.path.join(W, 'GoethitePaper_SI_body.tex')


def load(p):
    shutil.copy(p, p + TAG)
    raw = open(p, encoding='utf-8', newline='').read()
    return raw.replace('\r\n', '\n'), '\r\n' in raw


def save(p, t, crlf):
    open(p, 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n') if crlf else t)


NEW_METHODS = r"""\subsection{Multiple Diffusion Domain and Thermal History Modeling}\label{sec:gt_mdd_methods}

Together, the $^3$He release and the bulk-normalized $^4$He/$^3$He spectrum constrain the thermal history, if the activation energy
for diffusion is known \citep{farleyflowers2012}. We interpret the data from HT-Win-06-01b in two stages. First, the diffusion
domain structure of the sample is inverted from the $^3$He release alone. Second, natural thermal histories are fitted to the
$^4$He/$^3$He spectrum with that domain structure held fixed. Fits for $N=1$--5 domains and the best-fitting thermal histories
are given in the SI (\S\ref{sec:ch2-si-mdd}).

\paragraph{Diffusion domain structure} Following \citet{farleyflowers2012}, the sample is represented by $N$ non-interacting
spherical domains that share the activation energy of the Stage~1 regression (\S\ref{sec:gt_ht_results}). Each domain holds a
fraction of the uniformly distributed, proton-induced $^3$He and has a radius relative to the reference domain of the Stage~1
regression, giving $2N-1$ free parameters. These minimize the summed squared misfit of the fractional and cumulative $^3$He
yields, weighted equally, over the 28 steps with more than 0.1~pccSTP of $^3$He; the gas released in the six low-signal steps
still counts toward the cumulative yields of later steps, and their durations toward the heating schedule. Domains are added
one at a time, each search starting from the $(N-1)$-domain solution, until an added domain no longer changes the fit or the
domain structure. The Arrhenius and delta plots are not fitted: they follow from applying the \citet{fechtigkalbitzer1966}
inversion to the model cumulative release, and their misfit is reported as a reduced $\chi^2$ over the same 28 steps.

\paragraph{Thermal histories} Each thermal history predicts a $^4$He/$^3$He spectrum and a bulk He age (taking U and Th to be
distributed like the $^3$He) following \citet{shusterfarley2004}, applied to each domain of the four-domain structure.
We compare two types of thermal histories, with two free parameters for steady cooling and three for burial and exhumation.
"""

THERM_SCORE = r"""Each path is scored by the $\chi^2$ misfit of its predicted bulk-normalized ratios to the central ratios of the bounding
method \citep{thyer2026data} over the \MDDNfit{} steps that have lag-correction bounds and more than 0.1~pccSTP of $^3$He,
taking each uncertainty as half the range between the lower- and upper-bound ratios, with a floor of 0.02. The reduced
$\chi^2$ uses $\nu=22$ degrees of freedom for steady cooling and $\nu=21$ for burial and exhumation.
"""

b, bcr = load(B)
s, scr = load(S)
LOG = []

# ---------------- main text
i = b.index('\\subsection{Multiple Diffusion Domain and Thermal History Modeling}')
j = b.index('\\begin{itemize}', i)
old_head = b[i:j]
b = b[:i] + NEW_METHODS + b[j:]
LOG.append('- **EDIT/CUT** [Methods 2.2, lead + "Diffusion domain structure" + "Thermal histories" lead] Eqs. gt_mdd_domain, gt_mdd_mix and '
           'gt_mdd_S and the pointer to the SI forward model removed; procedure now cited to Farley and Flowers (2012) and Shuster and '
           'Farley (2004). Kept (unique to this work): two-stage approach, shared Stage 1 Ea, 28-step fitting window and treatment of the '
           'six low-signal steps, incremental domain addition, unfitted Arrhenius/delta plots, bulk He age from the same model. '
           'Typo "bythe" removed with the rewrite.\n    > ' + ' '.join(NEW_METHODS.split()))
o = b.index('Each path is scored by the $\\chi^2$ misfit')
e = b.index('$\\chi^2$ is evaluated for these free parameters', o)
b = b[:o] + THERM_SCORE + b[e:]
LOG.append('- **EDIT** [Methods 2.2, scoring] The misfit statistic (previously SI Eq. gt_mdd_chi2) stated in words in the main text: '
           'central bounding-method ratios, sigma = half the LB-UB range with a 0.02 floor, nu = 22/21. Hard age constraint '
           '(130-180 Ma) and the best-fit / parameter-range rule unchanged.\n    > ' + ' '.join(THERM_SCORE.split()))
assert 'sec:4he-forward' not in b and 'sec:ch2-si-chi2' not in b and 'eq:gt_mdd' not in b

# ---------------- SI
i = s.index('\\section{Multiple Diffusion Domain and Thermal History Modeling}\\label{sec:ch2-si-mdd}')
j = s.index('\\subsection{Multiple diffusion domain fits for $N=1$--5}', i)
s = (s[:i] + '\\section{Multiple Diffusion Domain Fits and Thermal History Results}\\label{sec:ch2-si-mdd}\n\n'
     'The modeling procedure is described in the main text (\\S\\ref{sec:gt_mdd_methods}) and follows '
     '\\citet{farleyflowers2012} and \\citet{shusterfarley2004}.\n\n' + s[j:])
LOG.append('- **CUT** [SI S6] Subsection "Forward modeling radiogenic 4He in nature and in the laboratory" (Eqs. ch2-si-mdd-modes, '
           'gt_mdd_N4, gt_mdd_ratio) removed; section retitled "Multiple Diffusion Domain Fits and Thermal History Results" with a '
           'one-sentence NEW lead citing the original methods.')
s = s.replace('about the best fit (see Eq.~\\eqref{eq:gt_mdd_chi2}).}', 'about the best fit (main text, \\S\\ref{sec:gt_mdd_methods}).}')
LOG.append('- **EDIT** [SI Table ch2-mdd-thermal caption] "(see Eq. gt_mdd_chi2)" -> "(main text, S gt_mdd_methods)".')
i = s.index('\\subsection{Misfit statistic for thermal histories}')
j = s.index('\\clearpage', i)
s = s[:i] + s[j:]
LOG.append('- **CUT** [SI S6] Subsection "Misfit statistic for thermal histories" removed (content now one sentence in Methods 2.2).')
assert 'eq:gt_mdd' not in s and 'sec:4he-forward' not in s
b = re.sub(r'\n{3,}', '\n\n', b)
s = re.sub(r'\n{3,}', '\n\n', s)
save(B, b, bcr)
save(S, s, scr)
with open(os.path.join(HERE, 'PORT_CHANGELOG.md'), 'a', encoding='utf-8') as fh:
    fh.write('\n## MDD / thermal-history methods condensed (2026-11-03; cite Farley & Flowers 2012 and Shuster & Farley 2004 rather '
             'than re-derive them). Paper only. Backups `*.pre_mddslim_20261103`.\n\n' + '\n'.join(LOG) + '\n')
print('\n'.join(l.split('\n')[0] for l in LOG))
