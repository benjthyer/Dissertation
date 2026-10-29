"""
Generates the Chapter 5 SI field-station table (Draaikraal field study) as
an auto-generated LaTeX macro, \\ChFiveFieldStationTable, written to
Writing/chapter5_data_table.tex and invoked from the SI
(Writing/chapter5_SI_body.tex). Same macro-file pattern as Chapter 3's
write_chapter3_geochron_tables.py.

Source data: Tables/Draaikraal 2023 BJT.xlsx, a GPS/GIS export with one row
per geotagged field observation. The 'Geotagged Stratigraphy' sheet holds
every station (236 rows); the 'Geotagged Structure Only' and 'Geotagged
Notes only' sheets are row-for-row subsets of it, so a single table built
from 'Geotagged Stratigraphy' carries everything. (Until 2026-10-24 there
were two tables in the main text -- stations and structural readings --
see CHANGES_JOURNAL.md.)

Columns kept: station, stratigraphic height above the Merensky Reef,
lat/lon, elevation, final interpreted map unit, lithology code, the
structural reading (type and strike/dip, strike as an azimuth with N = 0),
and photo numbers (hyperlinked to the SI photo album). The lithology
description and field notes -- long and present for only about a third of
the stations -- are footnotes to the station name, so they print at the foot
of the page that lists the station (longtable carries \\footnote through to
the right page). The table is portrait; footnotes are numbered 1.. within
the table. Dropped as derived or unused:
datetime, in-field unit, lineament position, the 2D/1D projection columns
(derived from lat/lon/elevation, Ch. 5 Stratigraphic Column Analytical
Methods), the W = 0 strike column (duplicate of the N = 0 one), the
mineral-percentage columns (sparse free-text), and magnetic index.

Clean-ups applied: 'Beddin' -> 'Bedding' and unit 'RzRz' -> 'Rz' (typos);
photo cells mangled by Excel into one number ('99100101102', '114117')
are split back into their photo numbers.

Regenerate after any change to the spreadsheet:
    python3 Chapter5/Figures/write_chapter5_data_table.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ch5_spelling import fix as fix_spelling  # noqa: E402
import sys
import re
import openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ch5_photo_refs import EXCLUDED_PHOTOS  # noqa: E402  (photos left out of the album)

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(FIG_DIR, '..', 'Tables', 'Draaikraal 2023 BJT.xlsx')
OUT_PATH = os.path.join(FIG_DIR, '..', 'Writing', 'chapter5_data_table.tex')
MAX_PHOTO = 125

COLS = dict(
    name=0, strat_height=1, lat=2, lon=3, elevation=4,
    unit=6, lith_code=8, lithology_desc=14, notes=15, photos=16,
    strike_n0=19, dip=18, structure_type=20,
)
FIXES = {'Beddin': 'Bedding', 'RzRz': 'Rz'}


def g(row, key):
    v = row[COLS[key]]
    if isinstance(v, str):
        v = v.strip()
        v = FIXES.get(v, v)
        if v == '':
            return None
    return v


def tex(s):
    if s is None:
        return ''
    s = fix_spelling(str(s))
    for a, b in (('\\', r'\textbackslash{}'), ('_', r'\_'), ('%', r'\%'),
                 ('#', r'\#'), ('&', r'\&'), ('$', r'\$'),
                 ('~', r'$\sim$'), ('^', r'\textasciicircum{}'),
                 ('<', r'$<$'), ('>', r'$>$')):
        s = s.replace(a, b)
    return s


def num(v, nd):
    return f'{v:.{nd}f}' if isinstance(v, (int, float)) else '--'


def _split_run(digits):
    """'99100101102' -> [99, 100, 101, 102]; '114117' -> [114, 117]:
    the increasing split into 1-3 digit photo numbers, if one exists."""
    def rec(s, prev):
        if not s:
            return []
        for k in (3, 2, 1):
            if len(s) >= k and s[0] != '0':
                n = int(s[:k])
                if prev < n <= MAX_PHOTO:
                    rest = rec(s[k:], n)
                    if rest is not None:
                        return [n] + rest
        return None
    return rec(digits, 0)


def photos_cell(v):
    if v is None:
        return '--'
    if isinstance(v, float):
        v = str(int(v))
    out = []
    for tok in re.split(r'\s*,\s*', str(v)):
        m = re.fullmatch(r'(\d+)\s*-\s*(\d+)', tok)
        if m:
            out.append(rf'\ChFivePhoto{{{m.group(1)}}}--\ChFivePhoto{{{m.group(2)}}}')
            continue
        if re.fullmatch(r'\d+', tok):
            nums = [int(tok)] if int(tok) <= MAX_PHOTO else (_split_run(tok) or [])
            if not nums:
                out.append(tex(tok))
            out += [rf'\ChFivePhoto{{{n}}}' for n in nums if n not in EXCLUDED_PHOTOS]
        elif tok:
            out.append(tex(tok))
    return ', '.join(out) or '--'


def structure_cell(row):
    st, strike, dip = g(row, 'structure_type'), g(row, 'strike_n0'), g(row, 'dip')
    if st in (None, 'None') and strike is None:
        return '--'
    try:
        sd = f'{int(float(strike)):03d}/{int(float(dip))}'
    except (TypeError, ValueError):
        sd = ''
    abbrev = {'Bedding': 'Bed.', 'Cleavage': 'Clv.', 'Contact': 'Cont.',
              'Modal Layering': 'M.L.'}.get(st, tex(st) if st else '')
    return (abbrev + ' ' + sd).strip() or '--'


def note_text(row):
    """Lithology description and field notes, joined into one footnote
    (None when the station has neither)."""
    parts = []
    for k in ('lithology_desc', 'notes'):
        v = g(row, k)
        if v is not None:
            v = tex(v).strip()
            parts.append(v if v[-1] in '.?!)' else v + '.')
    if not parts:
        return None
    t = ' '.join(parts)
    return t[0].upper() + t[1:]


HEADER = (r'Station & Ht. & Lat. & Lon. & Elev. & '
          r'Unit & Lith. & Structure & Photos \\')
NCOLS = 9
COLSPEC = (r'@{}>{\raggedright\arraybackslash}p{1.95cm} r r r r l l l '
           r'>{\raggedright\arraybackslash}p{1.5cm}@{}')
CAPTION = (
    r"Field stations of the Draaikraal campaign (July 2023), from the `Geotagged Stratigraphy' "
    r"sheet of \texttt{Chapter5/Tables/Draaikraal 2023 BJT.xlsx}, in order of stratigraphic height. "
    r"Ht.: stratigraphic height (m) relative to the Merensky Reef, from the projection described in "
    r"\S\ref{sec:ch5-stratigraphic-column-methods}. Lat./Lon.: WGS84, decimal degrees. Elev.: "
    r"elevation (m). Unit: final interpreted map "
    r"unit and Lith.: lithology code (\S\ref{sec:ch5-lithologic-descriptions}). Structure: "
    r"bedding (Bed.), cleavage (Clv.), contact (Cont.) or modal layering (M.L.), as strike/dip with "
    r"strike an azimuth from north. Photos: field photograph numbers; those reproduced in "
    r"\S\ref{sec:ch5-SI-photo-album} or as figures are links, the others are in the "
    r"supplementary photo album. Field descriptions and notes are footnotes to "
    r"the station name, at the foot of the page. `--': not recorded.")


def build(rows):
    out = [r'\begingroup',
           # footnotes numbered 1.. within this table, then the chapter's count restored
           r'\edef\ChFiveSavedFootnote{\the\value{footnote}}\setcounter{footnote}{0}',
           r'\renewcommand{\thefootnote}{\arabic{footnote}}',
           r'\begin{scriptsize}',
           r'\fontsize{7.5}{8.6}\selectfont',
           r'\renewcommand{\arraystretch}{0.9}',
           r'\setlength{\tabcolsep}{3pt}',
           r'\begin{longtable}{' + COLSPEC + '}',
           r'\caption{' + CAPTION + r'}\label{tab:ch5-field-stations}\\',
           r'\toprule', HEADER, r'\midrule', r'\endfirsthead',
           r'\multicolumn{%d}{@{}l}{\textit{Table~\ref{tab:ch5-field-stations} (continued)}} \\' % NCOLS,
           r'\toprule', HEADER, r'\midrule', r'\endhead',
           r'\midrule',
           r'\multicolumn{%d}{r@{}}{\textit{continued on next page}} \\' % NCOLS,
           r'\endfoot', r'\bottomrule', r'\endlastfoot']
    n = nnotes = 0
    for row in rows:
        if g(row, 'name') is None:
            continue
        n += 1
        name = tex(g(row, 'name'))
        note = note_text(row)
        if note:
            nnotes += 1
            name += r'\footnote{\scriptsize ' + note + '}'
        out.append(' & '.join([
            name,
            num(g(row, 'strat_height'), 0),
            num(g(row, 'lat'), 5),
            num(g(row, 'lon'), 5),
            num(g(row, 'elevation'), 0),
            tex(g(row, 'unit')) or '--',
            tex(g(row, 'lith_code')) or '--',
            structure_cell(row),
            photos_cell(g(row, 'photos')),
        ]) + r' \\')
    out += [r'\end{longtable}', r'\end{scriptsize}',
            r'\setcounter{footnote}{\ChFiveSavedFootnote}', r'\endgroup']
    return '\n'.join(out), n, nnotes


def main():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    rows = list(wb['Geotagged Stratigraphy'].iter_rows(min_row=2, values_only=True))
    rows.sort(key=lambda r: (r[COLS['strat_height']] if isinstance(r[COLS['strat_height']], (int, float)) else 1e9))
    table, n, nnotes = build(rows)
    hdr = [
        '% =============================================================',
        '%  chapter5_data_table.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.',
        '%  Written by Chapter5/Figures/write_chapter5_data_table.py from',
        "%  Chapter5/Tables/Draaikraal 2023 BJT.xlsx ('Geotagged Stratigraphy').",
        '%  Regenerate after any change to the spreadsheet:',
        '%    python3 Chapter5/Figures/write_chapter5_data_table.py',
        '%  \\input{} by Chapter5/chapter5.tex (defines the macro); invoked from',
        '%  Chapter5/Writing/chapter5_SI_body.tex.',
        '% =============================================================',
        r'\providecommand{\ChFivePhoto}[1]{#1}',
        r'\newcommand{\ChFiveFieldStationTable}{%',
        table,
        '}',
    ]
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(hdr) + '\n')
    print(f'Wrote {OUT_PATH} ({n} stations, {nnotes} with a footnote)')


if __name__ == '__main__':
    main()
