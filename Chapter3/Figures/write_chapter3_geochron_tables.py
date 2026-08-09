"""
Generates the two U-Th/He geochronology data tables for Chapter 3 as
auto-generated LaTeX macros, following the exact pattern established by
Chapter 2's Chapter2/Figures/fig_naive_isothermal_fits.py (see the long
comment there for the full rationale): each table is written as a
\\newcommand macro expanding to a complete `landscape`+`longtable`
environment, so the shared body files can invoke it by name
(\\ChThreeGeochronMainTable / \\ChThreeGeochronSITable) instead of anyone
hand-copying numbers out of the spreadsheet.

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

Output: Chapter3/Writing/chapter3_geochron_tables.tex
    \\ChThreeGeochronMainTable : Kidd Creek pyrite, Gympie pyrite, Durango
        apatite standard, and Gogebic (MI-43) hematite standard -- the four
        suites referenced directly in the Results text.
    \\ChThreeGeochronSITable : everything else in the compilation (Kidd
        Creek replicate/mass-only aliquots, Franklin NJ pyrite and
        fluorite, Rustenberg/Pilanesberg pyrite, Magnet Cove carbonatite
        pyrite, French Creek magnetite/pyrite, Salzburg arsenopyrite) --
        not discussed in the main text, reported in the SI for completeness.

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
    return f'{v:.{nd}f} $\\pm$ {err:.{nd}f}'


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


def data_row(rows, i, note=''):
    row = rows[i]
    name = row[COLS['name']]
    if not isinstance(name, str):
        return None
    age, dagger = age_cell(row)
    full_note = (dagger + (' ' if dagger and note else '') + note).strip()
    return ' & '.join([
        _tex_escape(name),
        fmt(g(row, 'mass'), 2),
        fmt_pm(g(row, 'U'), g(row, 'Uerr'), 3),
        fmt_pm(g(row, 'Th'), g(row, 'Therr'), 3),
        fmt_pm(g(row, 'Sm'), g(row, 'Smerr'), 3),
        fmt_pm(g_trace(row, 'Cu'), g(row, 'Cuerr'), 2),
        fmt_pm(g_trace(row, 'As'), g(row, 'Aserr'), 2),
        fmt_pm(g_trace(row, 'Zr'), g(row, 'Zrerr'), 2),
        fmt_pm(g_trace(row, 'Ag'), g(row, 'Agerr'), 2),
        fmt_pm(g_trace(row, 'Sb'), g(row, 'Sberr'), 2),
        fmt(g(row, 'eU'), 3),
        fmt(g(row, 'he4'), 2),
        age,
        full_note,
    ]) + r' \\'


def _tex_escape(s):
    return s.replace('_', r'\_').replace('%', r'\%').replace('#', r'\#')


def group_header(label, ncols=14):
    return r'\multicolumn{%d}{l}{\textbf{%s}} \\' % (ncols, label)


HEADER_ROW = (r'Sample & Mass & U & Th & Sm & Cu & As & Zr & Ag & Sb & eU & $^4$He & Age & Note \\'
              '\n' + r'& (mg) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ppm) & (ncc) & (Ma) & \\')

TABLE_PREAMBLE = r"""\begin{landscape}
\begin{footnotesize}
\begin{longtable}{l r r r r r r r r r r r r l}
\caption{%s}\label{%s}\\
\toprule
%s
\midrule
\endfirsthead
\multicolumn{14}{l}{\textit{(continued)}} \\
\toprule
%s
\midrule
\endhead
\midrule
\multicolumn{14}{r}{\textit{continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
"""

TABLE_END = r"""\end{longtable}
\end{footnotesize}
\end{landscape}"""


def build_main_table(rows):
    body = [TABLE_PREAMBLE % (
        r"U-Th/He geochronology results for the four sample suites discussed in the main "
        r"text: Kidd Creek pyrite, Gympie pyrite, and the Durango apatite and Gogebic (MI-43) "
        r"hematite standards run alongside them, including all trace elements quantified by "
        r"ICPMS (\S\ref{sec:ch3-experimental-methods-geochronology}): U, Th, and Sm (the "
        r"radiogenic-budget elements) plus Cu, As, Zr, Ag, and Sb, all measured as ratios to "
        r"spike vanadium; `--' denotes below detection or not measured for that aliquot. Ages "
        r"are the atmospheric-He-corrected `Age (Ma Atm=1Ra Corr.)' value; \textdagger\ marks "
        r"the handful of early aliquots analyzed before a tube blank was available, for which "
        r"the uncorrected measured age is reported instead. Excluded aliquots "
        r"(\S\ref{ch3-results-gympie-ages}) are noted in the last column, as are the first four "
        r"Durango apatite aliquots (2211DApA, 2211DApC, 2211DApD, 2022StDApA), analyzed under "
        r"the early ``old method'' protocol that predated the warm atmosphere-degassing step "
        r"(\S\ref{ch3-geochron-helium-methods}, Fig.~\ref{fig:ch3-durango-age-vs-ra}). The "
        r"complete compilation, including localities not discussed in the main text, is given "
        r"in the Supplementary Information (Table~\ref{tab:ch3-si-geochron}).",
        'tab:ch3-main-geochron', HEADER_ROW, HEADER_ROW)]

    body.append(group_header('Kidd Creek Pyrite (Archean VMS, $\\sim$2716 Ma host)'))
    for i in range(3, 15):
        r = data_row(rows, i)
        if r:
            body.append(r)

    body.append(r'\midrule')
    body.append(group_header('Gympie Pyrite (Permo-Triassic orogenic Au)'))
    gympie_notes = {
        49: 'excl.: early protocol', 50: 'excl.: early protocol',
        51: 'excl.: early protocol', 52: 'excl.: early protocol',
        56: 'excl.: outlier',
    }
    for i in range(49, 65):
        r = data_row(rows, i, note=gympie_notes.get(i, ''))
        if r:
            body.append(r)

    body.append(r'\midrule')
    body.append(group_header('Durango Apatite Standard (accepted age 32.1 Ma; Farley 2000)'))
    durango_notes = {
        33: 'old method: pre-degassing', 34: 'old method: pre-degassing',
        35: 'old method: pre-degassing', 36: 'old method: pre-degassing',
    }
    for i in range(33, 47):
        r = data_row(rows, i, note=durango_notes.get(i, ''))
        if r:
            body.append(r)
    avg_row = data_row(rows, 47, note='')
    if avg_row:
        body.append(avg_row)

    body.append(r'\midrule')
    body.append(group_header('Gogebic Iron Range BIF Hematite Standard (MI-43; 571 Ma)'))
    for i in range(89, 98):
        r = data_row(rows, i)
        if r:
            body.append(r)

    body.append(TABLE_END)
    return '\n'.join(body)


def build_si_table(rows):
    body = [TABLE_PREAMBLE % (
        r"U-Th/He geochronology results for all remaining sample suites in the compilation, "
        r"not discussed in the main text: Kidd Creek replicate/mass-only aliquots, Franklin "
        r"(NJ) pyrite and fluorite, Rustenberg/Pilanesberg pyrite, Magnet Cove carbonatite "
        r"pyrite, French Creek magnetite/pyrite, and Salzburg arsenopyrite. Reported here for "
        r"completeness; columns and conventions as in Table~\ref{tab:ch3-main-geochron}.",
        'tab:ch3-si-geochron', HEADER_ROW, HEADER_ROW)]

    groups = [
        ('Kidd Creek Pyrite (replicate / mass-only aliquots)', list(range(16, 23))),
        ('Franklin, NJ Pyrite (marble/volcanics, $\\sim$1.3--1.0 Ga)', list(range(24, 29))),
        ("Franklin, NJ Fluorite", list(range(30, 32))),
        ('Rustenberg/Pilanesberg(?) Pyrite', list(range(68, 76))),
        ('Magnet Cove Carbonatite Pyrite, Arkansas ($\\sim$100 Ma)', list(range(77, 79))),
        ('French Creek, PA Magnetite and Pyrite ($\\sim$130 Ma)', list(range(81, 85))),
        ('Salzburg, Austria Arsenopyrite', [87]),
    ]
    first = True
    for label, idxs in groups:
        if not first:
            body.append(r'\midrule')
        first = False
        body.append(group_header(label))
        for i in idxs:
            r = data_row(rows, i)
            if r:
                body.append(r)

    body.append(TABLE_END)
    return '\n'.join(body)


def main():
    rows = load_rows()
    main_table = build_main_table(rows)
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
    out.append('%  \\input{} by Chapter3/chapter3.tex (defines both macros before the')
    out.append('%  shared body) and Chapter3/chapter3_SI.tex, so both')
    out.append('%  \\ChThreeGeochronMainTable (invoked from HeInSulfides_Main_Body.tex\'s')
    out.append('%  Results section) and \\ChThreeGeochronSITable (invoked from')
    out.append('%  HeInSulfides_SI_body.tex) are available wherever needed.')
    out.append('% =============================================================')
    out.append(r'\newcommand{\ChThreeGeochronMainTable}{%')
    out.append(main_table)
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
