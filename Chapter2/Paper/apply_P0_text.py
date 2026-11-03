#!/usr/bin/env python3
"""apply_P0_text.py -- propagate the P_H2O -> 0 vacuum limit (2026-11-02) into the
Chapter 2 thesis text and the GCA paper text.  Run from Chapter2/Paper/.
Backups: *.pre_P0_20261102.  Journals to Chapter2/Paper/PORT_CHANGELOG.md and
the dissertation-level CHANGES_JOURNAL.md."""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', 'Writing'))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
TAG = '.pre_P0_20261102'
FILES = {
    'thesis body': 'chapter2_body.tex', 'thesis SI': 'chapter2goethite_SI_body.tex',
    'paper body': 'GoethitePaper_body.tex', 'paper SI': 'GoethitePaper_SI_body.tex',
    'paper abstract': 'GoethitePaper_abstract.tex',
}
LOG = {k: [] for k in FILES}

BODY = [
    ('Nucleation barrier scaling (Methods / model section)',
     "Because the barrier scales as\n$\\gamma^3/\\Delta\\mu^2$, the tenfold drop in $\\Delta\\mu$ between vacuum and water saturation raises \nthe energetic barrier $\\Delta G^{*}$ a hundredfold (Table~\\ref{tab:gt_dmu}).",
     "Because the barrier scales as\n$\\gamma^3/\\Delta\\mu^2$, it vanishes in vacuum, where the water pressure approaches zero and $\\Delta\\mu$\ngrows without bound, but is significant at water saturation, where $\\Delta\\mu$ is only 6--11~kJ\n(Table~\\ref{tab:gt_dmu})."),
    ('Driving-force paragraph',
     "Under the vacuum of a step-heating line\n($P_{\\mathrm{H_2O}}\\approx10^{-8}$~atm) it is 76--106~kJ, about ten times larger. The chemical",
     "Under the vacuum of a step-heating line the water\npressure approaches zero, so the chemical potential of water falls without bound and $\\Delta\\mu$ is\nunbounded. The chemical"),
    ('Table gt_dmu caption',
     "at water saturation and at $P_{\\mathrm{H_2O}} = 10^{-8}$~atm.}",
     "at water saturation. In vacuum ($P_{\\mathrm{H_2O}}\\rightarrow0$) the driving force is unbounded.}"),
    ('Calibration equation',
     "\\gamma_{\\mathrm{eff}} = \\left[\\frac{T\\ln(1/s)}{C\\left(\\Delta\\mu_{\\mathrm{off}}^{-2} - \\Delta\\mu_{\\mathrm{on}}^{-2}\\right)}\\right]^{1/3},",
     "\\gamma_{\\mathrm{eff}} = \\left[\\frac{T\\,\\Delta\\mu_{\\mathrm{off}}^{2}\\ln(1/s)}{C}\\right]^{1/3},"),
    ('Calibration: vacuum term',
     "with $\\Delta\\mu_{\\mathrm{on}}$ evaluated at $P_{\\mathrm{H_2O}} = 10^{-8}$~atm and $\\Delta\\mu_{\\mathrm{off}}$ at an\nupper bound on the water pressure with the trap isolated.",
     "where $\\Delta\\mu_{\\mathrm{off}}$ is evaluated at an upper bound on the water pressure with the trap isolated.\nWith the trap in place, the water pressure approaches zero, the driving force is unbounded, and its\ncontribution to the barrier vanishes. Any finite water pressure in the trapped line would give a larger\n$\\gamma_{\\mathrm{eff}}$, so this limit is conservative."),
    ('Calibration: gamma value and length scales',
     "This gives $\\gamma_{\\mathrm{eff}} = 0.16$~J\\,m$^{-2}$\n(range \\ChTwoKinGammaLo--\\ChTwoKinGammaHi). Under vacuum the corresponding critical nucleus is smaller\nthan a formula unit ($r^{*} = \\ChTwoKinRstarVac$~nm) and the barrier is only \\ChTwoKinBarVac~$k_BT$:\nconversion in vacuum is effectively barrierless, consistent with the simple Arrhenius behavior of\nboth vacuum experiments. At this scale classical nucleation theory has no literal meaning, so\n$\\gamma_{\\mathrm{eff}}$ is best read as the single parameter of a rate law in which $\\ln k$ falls as\n$-1/\\Delta\\mu^{2}$, not as an interface energy. At saturation, $r^{*} \\approx 1$~nm and the barrier\nis \\ChTwoKinBarSat~$k_BT$.",
     "This gives $\\gamma_{\\mathrm{eff}} = \\ChTwoKinMCGammaMid$~J\\,m$^{-2}$\n(range \\ChTwoKinGammaLo--\\ChTwoKinGammaHi). In vacuum the barrier vanishes, so conversion is barrierless,\nconsistent with the simple Arrhenius behavior of both vacuum experiments. At saturation and\n250~$^\\circ$C, the critical nucleus has a radius of \\ChTwoKinRstarSat~nm (\\ChTwoKinNfuSat{} formula units)\nand the barrier is \\ChTwoKinBarSat~$k_BT$. For nuclei this small, classical nucleation theory has no\nliteral meaning, so $\\gamma_{\\mathrm{eff}}$ is best read as the single parameter of a rate law in which\n$\\ln k$ falls as $-1/\\Delta\\mu^{2}$, not as an interface energy."),
    ('Translation equation (vacuum term vanishes)',
     "\\left(\\frac{1}{\\Delta\\mu_{\\mathrm{sat}}^{2}} - \\frac{1}{\\Delta\\mu_{\\mathrm{vac}}^{2}}\\right)",
     "\\frac{1}{\\Delta\\mu_{\\mathrm{sat}}^{2}}"),
    ('Translation: gamma values',
     "$\\gamma_{\\mathrm{eff}} = 0.14$, 0.16 and 0.19~J\\,m$^{-2}$",
     "$\\gamma_{\\mathrm{eff}} = 0.12$, 0.14 and 0.15~J\\,m$^{-2}$"),
    ('Assumptions: 10 nm grains',
     "raises the predicted conversion only to $\\sim10^{-23}$;",
     "raises the predicted conversion only to $\\sim10^{-13}$;"),
]
THESIS_CONC = [('Conclusions',
                "At water saturation, the roughly tenfold smaller\ndriving force raises the barrier",
                "At water saturation, the driving force is only 6--11~kJ, whereas it is unbounded at the near-zero\nwater pressure of a vacuum line; this raises the barrier")]
PAPER_CONC = [('Conclusions, finding 6',
               "the roughly tenfold smaller driving force at saturation\n  raises the barrier",
               "the driving force, unbounded at the near-zero water pressure of a vacuum line, is only\n  6--11~kJ at saturation, which raises the barrier")]
PAPER_ABS = [('Abstract',
              "the roughly tenfold smaller driving force for dehydroxylation at water saturation raises the \nbarrier",
              "the small driving force for dehydroxylation at water saturation, compared with the unbounded\ndriving force at the near-zero water pressure of a vacuum line, raises the \nbarrier")]
SI = [
    ('Calibration relation',
     "$\\ln(1/s) = (C\\gamma_{\\mathrm{eff}}^{3}/T)(\\Delta\\mu_{\\mathrm{off}}^{-2} - \\Delta\\mu_{\\mathrm{on}}^{-2})$.",
     "$\\ln(1/s) = C\\gamma_{\\mathrm{eff}}^{3}/(T\\,\\Delta\\mu_{\\mathrm{off}}^{2})$; the corresponding term for the\ntrapped neighbors vanishes because their driving force is unbounded (item 2)."),
    ('Item 1',
     "\\item $\\Delta\\mu_{\\mathrm{on}}$ and $\\Delta\\mu_{\\mathrm{off}}$ are bulk driving forces,",
     "\\item $\\Delta\\mu_{\\mathrm{off}}$ is a bulk driving force,"),
    ('Item 2 (vacuum limit)',
     None, None),   # handled by regex below
    ('Item 3',
     "\\item Surface terms are omitted in both.", "\\item Surface terms are omitted."),
    ('Volume sensitivity / adopted gamma',
     "enters only through $\\ln P$ in $\\Delta\\mu$ and then through a cube root, so a threefold uncertainty\nin volume changes $\\gamma_{\\mathrm{eff}}$ by only about 10\\%. The two steps agree within 15\\%, and\nwe adopt $\\gamma_{\\mathrm{eff}} = 0.16$~J\\,m$^{-2}$",
     "enters only through $\\ln P$ in $\\Delta\\mu_{\\mathrm{off}}$ and then through $\\Delta\\mu_{\\mathrm{off}}^{2/3}$, so a\nthreefold uncertainty in volume changes $\\gamma_{\\mathrm{eff}}$ by only about 5\\%. The two steps agree within\n20\\%, and we adopt $\\gamma_{\\mathrm{eff}} = \\ChTwoKinMCGammaMid$~J\\,m$^{-2}$"),
]
ITEM2_NEW = ("  \\item With the trap in place, the water pressure in the line approaches zero, so the chemical\n"
             "  potential of water falls without bound, $\\Delta\\mu_{\\mathrm{on}}$ is unbounded, and its term\n"
             "  $\\Delta\\mu_{\\mathrm{on}}^{-2}$ vanishes. This is the conservative limit: any finite water pressure in\n"
             "  the trapped line would give a larger $\\gamma_{\\mathrm{eff}}$ and a stronger predicted slowdown at\n"
             "  saturation. $\\Delta\\mu_{\\mathrm{off}}$ is evaluated at the water pressure reached with the trap\n"
             "  isolated (below).\n")
GAMMA_ROWS = ("    230 & 0.333 & 190 & 19.6 & 0.120 & 0.124 \\\\\n"
              "    230 & 0.333 & 600 & 6.2  & 0.126 & 0.130 \\\\\n"
              "    240 & 0.224 & 190 & 11.6 & 0.140 & 0.145 \\\\\n"
              "    240 & 0.224 & 600 & 3.7  & 0.147 & 0.152 \\\\\n")


def rep(t, key, where, old, new):
    n = t.count(old)
    assert n == 1, (key, where, n, old[:80])
    LOG[key].append(f'- **EDIT** [{where}]\n    - was: "{" ".join(old.split())[:400]}"\n    - now: "{" ".join(new.split())[:400]}"')
    return t.replace(old, new)


def dmu_table(t, key):
    i = t.index('\\label{tab:gt_dmu}')
    j = t.index('\\end{tabular}', i)
    blk = t[i:j]
    new = blk.replace('\\begin{tabular}{cccccc}', '\\begin{tabular}{cccc}')
    new = new.replace(' & $\\Delta\\mu_{\\mathrm{vac}}$ & $(\\Delta\\mu_{\\mathrm{vac}}/\\Delta\\mu_{\\mathrm{sat}})^2$ \\\\', ' \\\\')
    new = re.sub(r'^(\s*\d{3} & [\d.]+\s*& [\d.]+\s*& [\d.]+) & [\d.]+\s*& \d+\s*\\\\', r'\1 \\\\', new, flags=re.M)
    assert new.count('&') == blk.count('&') - 12, (key, 'dmu table')
    LOG[key].append('- **EDIT** [Table gt_dmu] Vacuum columns ($\\Delta\\mu_{vac}$ at 10$^{-8}$ atm and the squared ratio) removed: undefined for $P_{H_2O}\\rightarrow0$.')
    return t[:i] + new + t[j:]


def gamma_table(t, key):
    i = t.index('\\label{tab:gt_gamma}')
    a = t.index('\\hline\n', t.index('\\hline\n', i) + 1) + len('\\hline\n')
    b = t.index('    \\hline', a)
    assert t[a:b].count('\\\\') == 4, (key, 'gamma table')
    LOG[key].append('- **EDIT** [Table gt_gamma] gamma_eff columns recomputed with P_on -> 0 '
                    '(0.138/0.145, 0.150/0.158, 0.164/0.173, 0.178/0.188 -> 0.120/0.124, 0.126/0.130, 0.140/0.145, 0.147/0.152).')
    return t[:a] + GAMMA_ROWS + t[b:]


for key, fn in FILES.items():
    p = os.path.join(W, fn)
    shutil.copy(p, p + TAG)
    raw = open(p, encoding='utf-8', newline='').read()
    crlf = '\r\n' in raw
    t = raw.replace('\r\n', '\n')
    if key in ('thesis body', 'paper body'):
        for where, o, n in BODY:
            t = rep(t, key, where, o, n)
        t = dmu_table(t, key)
        for where, o, n in (THESIS_CONC if key == 'thesis body' else PAPER_CONC):
            t = rep(t, key, where, o, n)
    elif key in ('thesis SI', 'paper SI'):
        for where, o, n in SI:
            if o is None:
                m = re.search(r"  \\item They differ only through the chemical potential of water:.*?32--41~kJ for the pressures in Table~\\ref\{tab:gt_gamma\}\.\n", t, flags=re.S)
                assert m, key
                LOG[key].append(f'- **EDIT** [{where}]\n    - was: "{" ".join(m.group(0).split())[:400]}"\n    - now: "{" ".join(ITEM2_NEW.split())}"')
                t = t[:m.start()] + ITEM2_NEW + t[m.end():]
            else:
                t = rep(t, key, where, o, n)
        t = gamma_table(t, key)
    else:
        for where, o, n in PAPER_ABS:
            t = rep(t, key, where, o, n)
    if crlf:
        t = t.replace('\n', '\r\n')
    open(p, 'w', encoding='utf-8', newline='').write(t)

head = ('\n## Vacuum water pressure P_H2O -> 0 in the nucleation calibration (2026-11-02, BJT request)\n\n'
        'The trapped vacuum line was previously assigned an arbitrary P_H2O = 1e-8 atm. It is now the zero-pressure limit: '
        'the water chemical potential -> -inf, Delta mu_on -> inf, 1/Delta mu_on^2 -> 0. Script: '
        '`Chapter2/Figures/fig_goethite_vacuum_kinetics.py` (backup `.pre_P0_20261102`): `_dmu_bulk` returns +inf for P <= 0; '
        '`P_ON_PA = 0.0`; defaults of `gamma_from_suppression`, `saturated_rate_factor`, `log10_alpha_hydrothermal` use it; '
        '`cnt_scales` returns r* = 0 and barrier = 0 in vacuum; `GAMMA_CAL` (0.14, 0.16, 0.19) -> (0.12, 0.14, 0.15); the '
        'hard-coded permissive gamma 0.084 replaced by `gamma_permissive()` (0.081 at 0.1 bar). Macros regenerated '
        '(`chapter2_kinetics_values.tex`, backup `.pre_P0_20261102`): gamma 0.14-0.19 -> 0.12-0.15 (MC 0.12-0.15, median 0.14); '
        'barrier at saturation 51-129 -> 32-63 k_BT; vacuum barrier 0.5-1.3 -> 0; predicted conversion for gamma = low/mid/high '
        '10^-20.5/-31.4/-53.7 -> 10^-12.4/-20.7/-25.8; calibration grid 10^-51.9..-19.4 -> 10^-26.7..-12.3; Monte Carlo 95% '
        '10^-67.3..-15.7 -> 10^-38.7..-9.1 (required: < 10^-3.8). The 10 nm-grain value (~10^-23 -> ~10^-13) was re-derived '
        'as the median of the calibration grid with a 3.76 kJ driving-force shift, which reproduces the old 10^-23 under the old '
        'assumption. The phase diagram (equilibrium only) is unaffected; figures arrhenius_reaction_vs_diffusion and '
        'first_order_delta_lnk are unaffected; hydrothermal_translation (not used in either document) was regenerated.\n\n')
with open(os.path.join(HERE, 'PORT_CHANGELOG.md'), 'a', encoding='utf-8') as fh:
    fh.write(head)
    for key in ('paper body', 'paper SI', 'paper abstract'):
        fh.write(f'### {key}\n' + '\n'.join(LOG[key]) + '\n\n')
with open(os.path.join(ROOT, 'CHANGES_JOURNAL.md'), 'a', encoding='utf-8') as fh:
    fh.write(head.replace('## ', '## Chapter 2: '))
    for key in ('thesis body', 'thesis SI'):
        fh.write(f'### {key} ({FILES[key]})\n' + '\n'.join(LOG[key]) + '\n\n')
for k, v in LOG.items():
    print(k, len(v))
