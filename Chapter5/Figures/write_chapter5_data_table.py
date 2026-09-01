"""
Generates the field-station and structural-measurement data tables for
Chapter 5 (Draaikraal field study) as auto-generated LaTeX macros,
following the same pattern established by Chapter 3's
Chapter3/Figures/write_chapter3_geochron_tables.py: each table is written
as a \\newcommand macro expanding to a complete `landscape`+`longtable`
environment, so Chapter5/Writing/chapter5_body.tex can invoke it by name
(\\ChFiveFieldStationTable / \\ChFiveStructuralMeasurementsTable) instead
of anyone hand-copying rows out of the spreadsheet.

Source data: Chapter5/Tables/Draaikraal 2023 BJT.xlsx, a GPS/GIS export
(one row per geotagged field observation) with four sheets:
'Geotagged Stratigraphy' (241 rows -- the main field-station log used for
\\ChFiveFieldStationTable), 'Geotagged Structure Only' (43 rows -- strike/
dip/structure-type readings, used for \\ChFiveStructuralMeasurementsTable),
'Geotagged Notes only', and 'Non-geological Markers' (camp/access points,
etc.) -- the latter two are not currently tabulated here.

Of the sheets' ~40 columns, only those with meaningful fill rates and
relevance to a printed field-data table are kept (see the fill-rate scan
this script's column list was chosen from): station name, stratigraphic
height, lat/lon, elevation, the interpreted map unit, a merged lithology-
description/notes column, and (for the structure sheet) structure type,
strike, and dip. Columns dropped: datetime, in-field (as opposed to
final-interpreted) unit, lithology code, lineament position, the 2D/1D
projected-coordinate/traverse-height columns (all derived from lat/lon/
elevation -- see Chapter5/Writing chapter5_body.tex,
\\S\\ref{sec:ch5-stratigraphic-column-methods} for that projection method),
photo numbers, the mineral-percentage point-count columns (mostly unused
free-text annotations, not real modal percentages), and the magnetic-
susceptibility index column.

Regenerate after any change to the underlying spreadsheet:
    python3 Chapter5/Figures/write_chapter5_data_table.py
"""
import os
import openpyxl

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(FIG_DIR, '..', 'Tables', 'Draaikraal 2023 BJT.xlsx')
OUT_PATH = os.path.join(FIG_DIR, '..', 'Writing', 'chapter5_data_table.tex')

# Column indices (0-based, matching the sheets' shared header layout).
COLS = dict(
    name=0, strat_height=1, lat=2, lon=3, elevation=4,
    unit=6, lithology_desc=14, notes=15,
    strike=17, dip=18, structure_type=20,
)


def load_rows(sheet_name):
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb[sheet_name]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        rows.append(row)
    return rows


def g(row, key):
    return row[COLS[key]]


def _tex_escape(s):
    if s is None:
        return ''
    s = str(s)
    for a, b in (('\\', r'\textbackslash{}'), ('_', r'\_'), ('%', r'\%'),
                 ('#', r'\#'), ('&', r'\&'), ('$', r'\$'),
                 ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}')):
        s = s.replace(a, b)
    return s


def fmt_num(v, nd):
    return f'{v:.{nd}f}' if isinstance(v, (int, float)) else '--'


def merged_desc(row):
    """Lithology Description and Notes merged into one wrapped column;
    '--' when both are blank."""
    parts = [_tex_escape(g(row, k)) for k in ('lithology_desc', 'notes')
             if g(row, k) not in (None, '')]
    return '; '.join(parts) if parts else '--'


def table_preamble(colspec, ncols, caption, label, header_row):
    return r"""\begin{landscape}
\begin{footnotesize}
\begin{longtable}{%s}
\caption{%s}\label{%s}\\
\toprule
%s
\midrule
\endfirsthead
\multicolumn{%d}{l}{\textit{(continued)}} \\
\toprule
%s
\midrule
\endhead
\midrule
\multicolumn{%d}{r}{\textit{continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
""" % (colspec, caption, label, header_row, ncols, header_row, ncols)


TABLE_END = r"""\end{longtable}
\end{footnotesize}
\end{landscape}"""

FIELD_HEADER_ROW = (r'Station & Strat.\ Ht.\ (m) & Lat & Lon & Elev.\ (m) & Unit & Description / Notes \\')
FIELD_PREAMBLE = ('l r r r r l p{6cm}', 7,
    r"Field stations from the `Geotagged Stratigraphy' sheet of the Draaikraal field GPS/GIS "
    r"compilation (Chapter5/Tables/Draaikraal 2023 BJT.xlsx): station name, stratigraphic height "
    r"relative to the Merensky Reef (\S\ref{sec:ch5-stratigraphic-column-methods}), latitude/"
    r"longitude (WGS84), elevation, the final interpreted map unit (lithology codes defined in "
    r"\S\ref{sec:ch5-lithologic-descriptions}), and a merged lithology-description/field-notes "
    r"column; `--' denotes no description or notes recorded for that station. Structural "
    r"(strike/dip) readings are tabulated separately in Table~\ref{tab:ch5-structural-data}.",
    'tab:ch5-field-stations', FIELD_HEADER_ROW)

STRUCT_HEADER_ROW = (r'Station & Lat & Lon & Elev.\ (m) & Unit & Structure Type & Strike & Dip & Notes \\')
STRUCT_PREAMBLE = ('l r r r l l r r p{4cm}', 9,
    r"Structural measurements from the `Geotagged Structure Only' sheet of the Draaikraal field "
    r"GPS/GIS compilation. Strike is recorded with west = 0\textdegree{} (right-hand-rule dip "
    r"direction follows); dip in degrees from horizontal. `--' denotes not recorded for that "
    r"station.",
    'tab:ch5-structural-data', STRUCT_HEADER_ROW)


def build_field_table(rows):
    colspec, ncols, caption, label, header = FIELD_PREAMBLE
    body = [table_preamble(colspec, ncols, caption, label, header)]
    for row in rows:
        name = g(row, 'name')
        if name is None:
            continue
        body.append(' & '.join([
            _tex_escape(name),
            fmt_num(g(row, 'strat_height'), 1),
            fmt_num(g(row, 'lat'), 5),
            fmt_num(g(row, 'lon'), 5),
            fmt_num(g(row, 'elevation'), 1),
            _tex_escape(g(row, 'unit')) or '--',
            merged_desc(row),
        ]) + r' \\')
    body.append(TABLE_END)
    return '\n'.join(body)


def build_structural_table(rows):
    colspec, ncols, caption, label, header = STRUCT_PREAMBLE
    body = [table_preamble(colspec, ncols, caption, label, header)]
    for row in rows:
        name = g(row, 'name')
        if name is None:
            continue
        body.append(' & '.join([
            _tex_escape(name),
            fmt_num(g(row, 'lat'), 5),
            fmt_num(g(row, 'lon'), 5),
            fmt_num(g(row, 'elevation'), 1),
            _tex_escape(g(row, 'unit')) or '--',
            _tex_escape(g(row, 'structure_type')) or '--',
            fmt_num(g(row, 'strike'), 0),
            fmt_num(g(row, 'dip'), 0),
            _tex_escape(g(row, 'notes')) or '--',
        ]) + r' \\')
    body.append(TABLE_END)
    return '\n'.join(body)


def main():
    field_rows = load_rows('Geotagged Stratigraphy')
    struct_rows = load_rows('Geotagged Structure Only')

    field_table = build_field_table(field_rows)
    struct_table = build_structural_table(struct_rows)

    out = []
    out.append('% =============================================================')
    out.append('%  chapter5_data_table.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.')
    out.append('%  Written by Figures/write_chapter5_data_table.py from')
    out.append("%  Tables/Draaikraal 2023 BJT.xlsx ('Geotagged Stratigraphy' and")
    out.append("%  'Geotagged Structure Only' sheets).")
    out.append('%')
    out.append('%  Regenerate after any change to the spreadsheet:')
    out.append('%    python3 Chapter5/Figures/write_chapter5_data_table.py')
    out.append('%')
    out.append(r'%  \input{} by Chapter5/chapter5.tex (defines both macros before the')
    out.append(r'%  shared body), invoked from chapter5_body.tex\'s Sample and Station')
    out.append('%  Data section (\\S\\ref{sec:ch5-sample-station-data}).')
    out.append('% =============================================================')
    out.append(r'\newcommand{\ChFiveFieldStationTable}{%')
    out.append(field_table)
    out.append('}')
    out.append('')
    out.append(r'\newcommand{\ChFiveStructuralMeasurementsTable}{%')
    out.append(struct_table)
    out.append('}')

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    print(f'Wrote {OUT_PATH}  ({len(field_rows)} field-station rows, {len(struct_rows)} structural rows)')


if __name__ == '__main__':
    main()
