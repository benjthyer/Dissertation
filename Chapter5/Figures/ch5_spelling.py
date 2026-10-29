"""Spelling corrections applied to transcribed field notes and photo
captions when the Chapter 5 / Appendix A tables and photo album are
generated (2026-10-29 proofreading pass). The source spreadsheet and the
Word caption document are left untouched; corrections are applied on the
way into LaTeX. Whole-word, case-preserving for the first letter."""
import re

FIXES = {
    'anastamosing': 'anastomosing', 'chormitite': 'chromitite',
    'crystalization': 'crystallization', 'feldspatic': 'feldspathic',
    'flexture': 'flexure', 'igneouss': 'igneous', 'measureable': 'measurable',
    'migmatitmatic': 'migmatitic', 'mymerkitic': 'myrmekitic',
    'necesarily': 'necessarily', 'ocillitory': 'oscillatory',
    'porhpyitic': 'porphyritic', 'porhpyritic': 'porphyritic',
    'recrystalized': 'recrystallized', 'reistance': 'resistance',
    'spme': 'some', 'strongy': 'strongly', 'struturally': 'structurally',
    'paleoup': 'paleo-up', 'klipriver': 'Kliprivier',
    'english': 'English', 'african': 'African',
}
_RX = re.compile(r'\b(' + '|'.join(FIXES) + r')\b', re.IGNORECASE)


def fix(s):
    def rep(m):
        w = m.group(0)
        r = FIXES[w.lower()]
        return (r[0].upper() + r[1:]) if w[0].isupper() else r
    return _RX.sub(rep, s) if isinstance(s, str) else s
