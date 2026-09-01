"""
Generates the U-Th/He geochronology data tables for Chapter 3 as
auto-generated LaTeX macros, following the exact pattern established by
Chapter 2's Chapter2/Figures/fig_naive_isothermal_fits.py (see the long
comment there for the full rationale): each table is written as a
\\newcommand macro expanding to a complete `landscape`+`longtable`
environment, so the shared body files can invoke it by name instead of
anyone hand-copying numbers out of the spreadsheet.

Source data: Chapter3/Tables/geochronology_compilation_BJT.xlsx, 'Data'
sheet (the master compilation -- the same numbers as the per-locality
*Distilled sheets used by fig_geochronology_ages.py, but 'Data' also
carries the localities that never got their own *Distilled sheet:
Franklin, Rustenberg/Pilanesberg, Magnet Cove, French Creek, Salzburg,
and the Gogebic hematite standard).

Age convention: 'Age (Ma Atm=1Ra Corr.)', matching fig_geochronology_ages.py
(see its module docstring) -- NOT the raw 'Age (Ma Meas.)' or the
alternative 'Age (Ma Exotic Atm Corrected)' column, so the numbers printed
here agree with the figures. Falls back to the raw measured age (flagged
with a dagger note) for the handful of early aliquots analyzed before a
tube blank was available to compute either corrected age.

Three tables (was two -- split per feedback that the original 14-column
main-text table overflowed the landscape text width by ~4in): Cu, As, Ag,
and Sb (four of the five ratio-to-spike-vanadium trace elements) are no
longer printed in the main-text table; the main table keeps only Zr,
which is enough to make the width fit. The dropped Cu/As/Ag/Sb values for
those same main-text aliquots move to a new, narrow SI table
(\\ChThreeGeochronMainTraceSITable) rather than being lost.

Output: Chapter3/Writing/chapter3_geochron_tables.tex
    \\ChThreeGeochronMainTable : Kidd Creek pyrite, Gympie pyrite, Durango
        apatite standard, and Gogebic (MI-43) hematite standard -- the four
        suites referenced directly in the Results text. U, Th, Sm, Zr, eU,
        4He, age; Cu/As/Ag/Sb moved to \\ChThreeGeochronMainTraceSITable.
    \\ChThreeGeochronMainTraceSITable : Cu, As, Ag, Sb for the same four
        main-text suites above (SI-only; referenced from the main text
        table's caption).
    \\ChThreeGeochronSITable : everything else in the compilation (Kidd
        Creek replicate/mass-only aliquots, Franklin NJ pyrite and
        fluorite, Rustenberg/Pilanesberg pyrite, Magnet Cove carbonatite
        pyrite, French Creek magnetite/pyrite, Salzburg arsenopyrite) --
        not discussed in the main text, reported in the SI for
        completeness with the full trace element suite (Cu, As, Zr, Ag,
        Sb) retained, since these aliquots were never in the main table.

Regenerate after any change to the underlying spreadsheet:
    python3 Chapter3/Figures/write_chapter3_geochron_tables.py
"""
import os
import openpyxl

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(FIG_DIR, '..', 'Tables', 'geochronology_compilation_BJT.xlsx')
OUT_PATH = os.path.join(FIG_DIR, '..', 'Writing', 'chapter3_geochron_tables.tex')

COLS = dict(
    name=0, mass=1, he4mg=2, eU=3,
    agemeas=5, agemeaserr=6, he4=7, he4err=8,
    age1ra=19, age1raerr=20,
    ageexo=27, ageexoerr=28,
    U=29, Uerr=30, Th=31, Therr=32, Sm=33, Smerr=34,
    Cu=35, Cuerr=36, As=37, Aserr=38, Zr=39, Zrerr=40,
    Ag=41, Agerr=42, Sb=43, Sberr=44,
)


def load_rows():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb['Data']
    rows = {}
    for i, row in enumerate(ws.iter_rows(min_row=1, values_only=True), start=1):
        rows[i] = row
    return rows


def g(row, key):
    v = row[COLS[key]]
    return v if isinstance(v, (int, float)) else None


def fmt(v, nd=2):
    return f'{v:.{nd}f}' if v is not None else '--'


def fmt_pm(v, err, nd=2):
    if v is None:
        return '--'
    if err is None:
        return fmt(v, nd)
    # No literal spaces around \pm: it's a binary math operator, so TeX
    # already inserts its own (narrower) operator spacing inside the $...$;
    # adding text-mode spaces outside the $ as well just wastes width that
    # matters for the tight 14-column SI table (table_preamble tiny=True).
    return f'{v:.{nd}f}$\\pm${err:.{nd}f}'


def age_cell(row):
    """Age (Ma) +/- 2 sigma, preferring the 1Ra-atmosphere-corrected age
    (the convention used throughout this chapter's figures/text); falls
    back to the raw measured age with a dagger note for aliquots analyzed
    before a tube blank was available."""
    a, ae = g(row, 'age1ra'), g(row, 'age1raerr')
    if a is not None:
        return fmt_pm(a, ae, 1), ''
    a, ae = g(row, 'agemeas'), g(row, 'agemeaserr')
    if a is not None:
        return fmt_pm(a, ae, 1), '\\textdagger'
    return '--', ''


TRACE_COLS_ZERO_MEANS_NOT_MEASURED = ('Cu', 'As', 'Zr', 'Ag', 'Sb')


def g_trace(row, key):
    """Like g(), but for the five ratio-to-spike-vanadium trace elements
    (Cu, As, Zr, Ag, Sb), where the workbook records an exact 0 (not a
    blank cell) for aliquots on which that element simply wasn't
    monitored/quantified -- e.g. every pre-degassing-protocol Durango
    aliquot (rows 33-36) and several other early-batch aliquots
    throughout the compilation. An exact 0.000 +/- 0.000 is not a
    plausible real ICPMS measurement for any of these five elements
    (checked: no genuinely-measured row for any of them is anywhere near
    0), so it is treated the same as a missing cell and rendered as
    '--' rather than a misleading literal zero."""
    v = g(row, key)
    return None if v == 0 else v


def row_name(row):
    name = row[COLS['name']]
    return _tex_escape(name) if isinstance(name, str) else None


def full_note(row, note):
    age, dagger = age_cell(row)
    return (dagger + (' ' if dagger and note else '') + note).strip()


def data_row_main(rows, i, note=''):
    """10-column row for the main-text table: Sample, Mass, U, Th, Sm, Zr,
    eU, 4He, Age, Note. (Cu/As/Ag/Sb dropped -- see module docstring.)"""
    row = rows[i]
    name = row_name(row)
    if name is None:
        return None
    age, _ = age_cell(row)
    return ' & '.join([
        name,
        fmt(g(row, 'mass'), 2),
        fmt_pm(g(row, 'U'), g(row, 'Uerr'), 3),
        fmt_pm(g(row, 'Th'), g(row, 'Therr'), 3),
        fmt_pm(g(row, 'Sm'), g(row, 'Smerr'), 3),
        fmt_pm(g_trace(row, 'Zr'), g(row, 'Zrerr'), 2),
        fmt(g(row, 'eU'), 3),
        fmt(g(row, 'he4'), 2),
        age,
        full_note(row, note),
    ]) + r' \\'


def data_row_full(rows, i, note=''):
    """14-column row (original layout) for the SI 'everything else' table:
    Sample, Mass, U, Th, Sm, Cu, As, Zr, Ag, Sb, eU, 4He, Age, Note.
    U/Th/Sm/eU are rounded to 2 decimal places here (vs 3 in the
    main-text table) -- one more small width saving on top of \tiny and
    the tightened \tabcolsep, needed to fit this wider 14-column table's
    extra Cu/As/Ag/Sb columns within the landscape text width; matches
    the precision already used for Cu/As/Zr/Ag/Sb."""
    row = rows[i]
    name = row_name(row)
    if name is None:
        return None
    age, _ = age_cell(row)
    return ' & '.join([
        name,
        fmt(g(row, 'mass'), 2),
        fmt_pm(g(row, 'U'), g(row, 'Uerr'), 2),
        fmt_pm(g(row, 'Th'), g(row, 'Therr'), 2),
        fmt_pm(g(row, 'Sm'), g(row, 'Smerr'), 2),
        fmt_pm(g_trace(row, 'Cu'), g(row, 'Cuerr'), 2),
        fmt_pm(g_trace(row, 'As'), g(row, 'Aserr'), 2),
        fmt_pm(g_trace(row, 'Zr'), g(row, 'Zrerr'), 2),
        fmt_pm(g_trace(row, 'Ag'), g(row, 'Agerr'), 2),
        fmt_pm(g_trace(row, 'Sb'), g(row, 'Sberr'), 2),
        fmt(g(row, 'eU'), 2),
        fmt(g(row, 'he4'), 2),
        age,
        full_note(row, note),
    ]) + r' \\'


def data_row_trace(rows, i, note=''):
    """6-column row for the new main-text-samples trace-element SI table:
    Sample, Cu, As, Ag, Sb, Note."""
    row = rows[i]
    name = row_name(row)
    if name is None:
        return None
    return ' & '.join([
        name,
        fmt_pm(g_trace(row, 'Cu'), g(row, 'Cuerr'), 2),
        fmt_pm(g_trace(row, 'As'), g(row, 'Aserr'), 2),
        fmt_pm(g_trace(row, 'Ag'), g(row, 'Agerr'), 2),
        fmt_pm(g_trace(row, 'Sb'), g(row, 'Sberr'), 2),
        full_note(row, note),
    ]) + r' \\'


def _tex_escape(s):
    return s.replace('_', r'\_').replace('%', r'\%').replace('#', r'\#')


def group_header(label, ncols):
    return r'\multicolumn{%d}{l}{\textbf{%s}} \\' % (ncols, label)


MAIN_HEADER_ROW = (r'Sample & Mass & U & Th & Sm & Zr & eU & $^4$He & Age & Note \\'
                    '\n' + r'& (mg) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ncc) & (Ma) & \\')

FULL_HEADER_ROW = (r'Sample & Mass & U & Th & Sm & Cu & As & Zr & Ag & Sb & eU & $^4$He & Age & Note \\'
                    '\n' + r'& (mg) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ncc) & (Ma) & \\')

TRACE_HEADER_ROW = (r'Sample & Cu & As & Ag & Sb & Note \\'
                     '\n' + r'& (ppm) & (ppm) & (ppm) & (ppm) & \\')


def table_preamble(colspec, ncols, tiny=False):
    """tiny=False uses the document-wide longtable default (\scriptsize,
    set by \AtBeginEnvironment in dissertation_preamble.tex). Pass
    tiny=True for the one table (the 14-column SI 'everything else'
    compilation) still too wide at \scriptsize even in landscape -- its
    long hand-typed sample IDs (e.g. `12122022KCPyST05A`) are the actual
    width driver, not column count, so shrinking the whole table by one
    more LaTeX size step is the fix rather than dropping columns already
    ruled out for this table (see build_si_table).

    Implementation note: the extra size step can *not* be a bare \tiny
    placed after \begin{longtable}{...} and before \caption{} -- that
    breaks longtable's internal \LT@makecaption bookkeeping ("Misplaced
    \noalign"/"Misplaced \omit" errors), because \caption inside
    longtable must be the very first thing in the environment. Instead,
    when tiny=True the whole landscape+longtable block is wrapped in a
    group that locally redefines \scriptsize to mean \tiny, so
    \AtBeginEnvironment's own internal call to \scriptsize (fired at
    \begin{longtable}, invisibly, before \caption) picks up \tiny without
    anything extra appearing before \caption in the actual table source.
    Pair with table_end(tiny=True) to close the extra group.
    """
    open_size = r'{\let\scriptsize\tiny\setlength{\tabcolsep}{0.75pt}' + '\n' if tiny else ''
    return r"""%s\begin{landscape}
\begin{footnotesize}
\begin{longtable}{%s}
\caption{%%s}\label{%%s}\\
\toprule
%%s
\midrule
\endfirsthead
\multicolumn{%d}{l}{\textit{(continued)}} \\
\toprule
%%s
\midrule
\endhead
\midrule
\multicolumn{%d}{r}{\textit{continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
""" % (open_size, colspec, ncols, ncols)


def table_end(tiny=False):
    close_size = '\n}' if tiny else ''
    return r"""\end{longtable}
\end{footnotesize}
\end{landscape}""" + close_size


TABLE_END = table_end()
FULL_TABLE_END = table_end(tiny=True)

MAIN_PREAMBLE = table_preamble('l r r r r r r r r l', 10)
FULL_PREAMBLE = table_preamble('l r r r r r r r r r r r r l', 14, tiny=True)
TRACE_PREAMBLE = table_preamble('l r r r r l', 6)


# Row-index groupings shared by all three tables (same underlying aliquots
# as before the column split).
KIDD_CREEK_MAIN = list(range(3, 15))
GYMPIE = list(range(49, 65))
GYMPIE_NOTES = {
    49: 'excl.: early protocol', 50: 'excl.: early protocol',
    51: 'excl.: early protocol', 52: 'excl.: early protocol',
    56: 'excl.: outlier',
}
DURANGO = list(range(33, 47))
DURANGO_NOTES = {
    33: 'old method: pre-degassing', 34: 'old method: pre-degassing',
    35: 'old method: pre-degassing', 36: 'old method: pre-degassing',
}
DURANGO_AVG = 47
GOGEBIC = list(range(89, 98))

SI_GROUPS = [
    ('Kidd Creek Pyrite (replicate / mass-only aliquots)', list(range(16, 23))),
    ('Franklin, NJ Pyrite (marble/volcanics, $\\sim$1.3--1.0 Ga)', list(range(24, 29))),
    ("Franklin, NJ Fluorite", list(range(30, 32))),
    ('Rustenberg/Pilanesberg(?) Pyrite', list(range(68, 76))),
    ('Magnet Cove Carbonatite Pyrite, Arkansas ($\\sim$100 Ma)', list(range(77, 79))),
    ('French Creek, PA Magnetite and Pyrite ($\\sim$130 Ma)', list(range(81, 85))),
    ('Salzburg, Austria Arsenopyrite', [87]),
]


def build_main_table(rows):
    body = [MAIN_PREAMBLE % (
        r"U-Th/He geochronology results for the four sample suites discussed in the main "
        r"text: Kidd Creek pyrite, Gympie pyrite, and the Durango apatite and Gogebic (MI-43) "
        r"hematite standards run alongside them, including U, Th, and Sm (the radiogenic-budget "
        r"elements quantified by ICPMS, \S\ref{sec:ch3-experimental-methods-geochronology}) "
        r"plus Zr, also measured as a ratio to spike vanadium; `--' denotes below detection or "
        r"not measured for that aliquot. The remaining ICPMS trace elements measured the same "
        r"way (Cu, As, Ag, Sb) are reported separately in the Supplementary Information "
        r"(Table~\ref{tab:ch3-main-geochron-trace}) rather than here, to keep this table within "
        r"the page width. Ages are the atmospheric-He-corrected `Age (Ma Atm=1Ra Corr.)' value; "
        r"\textdagger\ marks the handful of early aliquots analyzed before a tube blank was "
        r"available, for which the uncorrected measured age is reported instead. Excluded "
        r"aliquots (\S\ref{ch3-results-gympie-ages}) are noted in the last column, as are the "
        r"first four Durango apatite aliquots (2211DApA, 2211DApC, 2211DApD, 2022StDApA), "
        r"analyzed under the early ``old method'' protocol that predated the warm "
        r"atmosphere-degassing step (\S\ref{ch3-geochron-helium-methods}, "
        r"Fig.~\ref{fig:ch3-durango-age-vs-ra}). The complete compilation, including "
        r"localities not discussed in the main text, is given in the Supplementary "
        r"Information (Table~\ref{tab:ch3-si-geochron}).",
        'tab:ch3-main-geochron', MAIN_HEADER_ROW, MAIN_HEADER_ROW)]

    body.append(group_header('Kidd Creek Pyrite (Archean VMS, $\\sim$2716 Ma host)', 10))
    for i in KIDD_CREEK_MAIN:
        r = data_row_main(rows, i)
        if r:
            body.append(r)

    body.append(r'\midrule')
    body.append(group_header('Gympie Pyrite (Permo-Triassic orogenic Au)', 10))
    for i in GYMPIE:
        r = data_row_main(rows, i, note=GYMPIE_NOTES.get(i, ''))
        if r:
            body.append(r)

    body.append(r'\midrule')
    body.append(group_header('Durango Apatite Standard (accepted age 32.1 Ma; Farley 2000)', 10))
    for i in DURANGO:
        r = data_row_main(rows, i, note=DURANGO_NOTES.get(i, ''))
        if r:
            body.append(r)
    avg_row = data_row_main(rows, DURANGO_AVG, note='')
    if avg_row:
        body.append(avg_row)

    body.append(r'\midrule')
    body.append(group_header('Gogebic Iron Range BIF Hematite Standard (MI-43; 571 Ma)', 10))
    for i in GOGEBIC:
        r = data_row_main(rows, i)
        if r:
            body.append(r)

    body.append(TABLE_END)
    return '\n'.join(body)


def build_main_trace_si_table(rows):
    """New SI table: Cu/As/Ag/Sb for the same four main-text suites, kept
    out of the main table above to fit the page width."""
    body = [TRACE_PREAMBLE % (
        r"Cu, As, Ag, and Sb (measured as ratios to spike vanadium by the same ICPMS run as "
        r"U, Th, Sm, and Zr, \S\ref{sec:ch3-experimental-methods-geochronology}) for the same "
        r"Kidd Creek, Gympie, Durango, and Gogebic aliquots reported in "
        r"Table~\ref{tab:ch3-main-geochron}, in the same row order; `--' denotes below "
        r"detection or not measured for that aliquot. Sample notes are repeated from "
        r"Table~\ref{tab:ch3-main-geochron} for reference.",
        'tab:ch3-main-geochron-trace', TRACE_HEADER_ROW, TRACE_HEADER_ROW)]

    body.append(group_header('Kidd Creek Pyrite (Archean VMS, $\\sim$2716 Ma host)', 6))
    for i in KIDD_CREEK_MAIN:
        r = data_row_trace(rows, i)
        if r:
            body.append(r)

    body.append(r'\midrule')
    body.append(group_header('Gympie Pyrite (Permo-Triassic orogenic Au)', 6))
    for i in GYMPIE:
        r = data_row_trace(rows, i, note=GYMPIE_NOTES.get(i, ''))
        if r:
            body.append(r)

    body.append(r'\midrule')
    body.append(group_header('Durango Apatite Standard (accepted age 32.1 Ma; Farley 2000)', 6))
    for i in DURANGO:
        r = data_row_trace(rows, i, note=DURANGO_NOTES.get(i, ''))
        if r:
            body.append(r)
    avg_row = data_row_trace(rows, DURANGO_AVG, note='')
    if avg_row:
        body.append(avg_row)

    body.append(r'\midrule')
    body.append(group_header('Gogebic Iron Range BIF Hematite Standard (MI-43; 571 Ma)', 6))
    for i in GOGEBIC:
        r = data_row_trace(rows, i)
        if r:
            body.append(r)

    body.append(TABLE_END)
    return '\n'.join(body)


def build_si_table(rows):
    body = [FULL_PREAMBLE % (
        r"U-Th/He geochronology results for all remaining sample suites in the compilation, "
        r"not discussed in the main text: Kidd Creek replicate/mass-only aliquots, Franklin "
        r"(NJ) pyrite and fluorite, Rustenberg/Pilanesberg pyrite, Magnet Cove carbonatite "
        r"pyrite, French Creek magnetite/pyrite, and Salzburg arsenopyrite. Reported here for "
        r"completeness, with the full trace-element suite (Cu, As, Zr, Ag, Sb) retained since "
        r"these aliquots are not duplicated in the main text; columns and conventions as in "
        r"Table~\ref{tab:ch3-main-geochron}.",
        'tab:ch3-si-geochron', FULL_HEADER_ROW, FULL_HEADER_ROW)]

    first = True
    for label, idxs in SI_GROUPS:
        if not first:
            body.append(r'\midrule')
        first = False
        body.append(group_header(label, 14))
        for i in idxs:
            r = data_row_full(rows, i)
            if r:
                body.append(r)

    body.append(FULL_TABLE_END)
    return '\n'.join(body)


def main():
    rows = load_rows()
    main_table = build_main_table(rows)
    main_trace_si_table = build_main_trace_si_table(rows)
    si_table = build_si_table(rows)

    out = []
    out.append('% =============================================================')
    out.append('%  chapter3_geochron_tables.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.')
    out.append('%  Written by Figures/write_chapter3_geochron_tables.py from')
    out.append('%  Tables/geochronology_compilation_BJT.xlsx (\'Data\' sheet).')
    out.append('%')
    out.append('%  Regenerate after any change to the spreadsheet:')
    out.append('%    python3 Chapter3/Figures/write_chapter3_geochron_tables.py')
    out.append('%')
    out.append('%  \\input{} by Chapter3/chapter3.tex (defines all three macros before the')
    out.append('%  shared body) and Chapter3/chapter3_SI.tex, so \\ChThreeGeochronMainTable')
    out.append('%  (invoked from HeInSulfides_Main_Body.tex\'s Results section) and')
    out.append('%  \\ChThreeGeochronMainTraceSITable / \\ChThreeGeochronSITable (invoked from')
    out.append('%  HeInSulfides_SI_body.tex) are available wherever needed.')
    out.append('%')
    out.append('%  NOTE on the split (see module docstring for the full rationale): the')
    out.append('%  original single 14-column main-text table overflowed the landscape text')
    out.append('%  width by ~4in. Cu/As/Ag/Sb now live only in the new')
    out.append('%  \\ChThreeGeochronMainTraceSITable; the main table keeps Zr (fits within')
    out.append('%  width) plus U/Th/Sm/eU/4He/Age.')
    out.append('% =============================================================')
    out.append(r'\newcommand{\ChThreeGeochronMainTable}{%')
    out.append(main_table)
    out.append('}')
    out.append('')
    out.append(r'\newcommand{\ChThreeGeochronMainTraceSITable}{%')
    out.append(main_trace_si_table)
    out.append('}')
    out.append('')
    out.append(r'\newcommand{\ChThreeGeochronSITable}{%')
    out.append(si_table)
    out.append('}')

    with open(OUT_PATH, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print(f'Wrote {OUT_PATH}')


if __name__ == '__main__':
    main()
