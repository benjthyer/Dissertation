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
Franklin, Rustenburg/Pilanesberg, Magnet Cove, French Creek, Salzburg,
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
        fluorite, Rustenburg/Pilanesberg pyrite, Magnet Cove carbonatite
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


# ---------------------------------------------------------------------------
# Rounding conventions (2026-10-29, per K. Farley's sig-fig review):
#   U, Th, Sm, eU : 2 decimal places (ppm)
#   Zr            : 1 decimal place  (ppm)
#   4He           : 1 decimal place  (ncc)
#   Age           : 1 decimal place, or 0 decimal places when the 2-sigma
#                   uncertainty exceeds AGE_INTEGER_ABOVE (10 Ma)
#   Durango apatite overrides: U, Th, Sm, eU to 1 decimal place
#   Gogebic hematite overrides: U, eU to 1 decimal place
#   Cu, As, Ag, Sb (SI only): uncertainty rounded to 2 significant figures
#                   and the value rounded to the same decimal place.
# Every uncertainty is printed to the same decimal place as its value.
# ---------------------------------------------------------------------------
import math

DEFAULT_PREC = dict(U=2, Th=2, Sm=2, Zr=1, eU=2, he4=1, mass=2)
DURANGO_PREC = dict(DEFAULT_PREC, U=1, Th=1, Sm=1, eU=1)
GOGEBIC_PREC = dict(DEFAULT_PREC, U=1, eU=1)
AGE_INTEGER_ABOVE = 10.0   # Ma; ages with larger 2-sigma get no decimals

# Footnote symbols attached to sample names (replace the old "Note" column).
SYM_OLD = r'$^{*}$'          # excluded: old method / early protocol
SYM_OUTLIER = r'$^{\dagger}$'  # excluded: outlier
SYM_MEASAGE = r'$^{\ddagger}$' # uncorrected (measured) age reported


def fmt(v, nd=2):
    return f'{v:.{nd}f}' if v is not None else '--'


def pm(v, err, nd):
    """Two table cells, 'value & $\\pm$err', for an r@{}l column pair, so
    the +/- signs line up down the column. Missing value -> '--' & ''."""
    if v is None:
        return '--', ''
    if err is None:
        return fmt(v, nd), ''
    return fmt(v, nd), r'$\pm$' + fmt(err, nd)


def _unc_decimals(err, sig=2):
    return sig - 1 - int(math.floor(math.log10(abs(err))))


def _fmt_dec(x, d):
    if d > 0:
        return f'{x:.{d}f}'
    return f'{int(round(x, d)):d}'


def pm_round_to_unc(v, err, sig=2):
    """Value +/- err with err rounded to `sig` significant figures and the
    value rounded to the same decimal place (e.g. 410116.35 +/- 23437.59
    -> 410000 +/- 23000)."""
    if v is None:
        return '--', ''
    if err is None or err == 0:
        return f'{v:.{sig + 1}g}', ''
    d = _unc_decimals(err, sig)
    d = _unc_decimals(round(err, d), sig)  # e.g. 9.96 rounds up to 10
    return _fmt_dec(v, d), r'$\pm$' + _fmt_dec(err, d)


def age_cells(row):
    """Age (Ma) +/- 2 sigma as two cells, preferring the 1Ra-atmosphere-
    corrected age (the convention used throughout this chapter's figures and
    text); falls back to the raw measured age (marked with SYM_MEASAGE) for
    any aliquot analyzed before a tube blank was available. Returns
    (value_cell, err_cell, used_measured_age)."""
    for key, ekey, measured in (('age1ra', 'age1raerr', False),
                                ('agemeas', 'agemeaserr', True)):
        a, ae = g(row, key), g(row, ekey)
        if a is not None:
            nd = 0 if (ae is not None and ae > AGE_INTEGER_ABOVE) else 1
            val, err = pm(a, ae, nd)
            if measured:
                err = err + SYM_MEASAGE if err else err
                val = val if err else val + SYM_MEASAGE
            return val, err, measured
    return '--', '', False


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


def _tex_escape(s):
    return s.replace('_', r'\_').replace('%', r'\%').replace('#', r'\#')


def row_name(row, flag=None):
    name = row[COLS['name']]
    if not isinstance(name, str):
        return None
    sym = {'old': SYM_OLD, 'outlier': SYM_OUTLIER}.get(flag, '')
    return _tex_escape(name) + sym


# Track whether any printed row fell back to the measured age, so the
# caption only explains SYM_MEASAGE if it is actually used.
_USED_MEASURED_AGE = {'any': False}


def data_row_main(rows, i, prec, flag=None):
    """Main-text row: Sample, Mass, U, Th, Sm, Zr, eU, 4He, Age (U, Th, Sm,
    Zr and Age are value/uncertainty column pairs)."""
    row = rows[i]
    name = row_name(row, flag)
    if name is None:
        return None
    a_val, a_err, measured = age_cells(row)
    _USED_MEASURED_AGE['any'] |= measured
    cells = [name, fmt(g(row, 'mass'), prec['mass'])]
    cells += pm(g(row, 'U'), g(row, 'Uerr'), prec['U'])
    cells += pm(g(row, 'Th'), g(row, 'Therr'), prec['Th'])
    cells += pm(g(row, 'Sm'), g(row, 'Smerr'), prec['Sm'])
    cells += pm(g_trace(row, 'Zr'), g(row, 'Zrerr'), prec['Zr'])
    cells += [fmt(g(row, 'eU'), prec['eU']), fmt(g(row, 'he4'), prec['he4'])]
    cells += [a_val, a_err]
    return ' & '.join(cells) + r' \\'


def data_row_full(rows, i, prec=DEFAULT_PREC, flag=None):
    """SI 'everything else' row: Sample, Mass, U, Th, Sm, Cu, As, Zr, Ag, Sb,
    eU, 4He, Age."""
    row = rows[i]
    name = row_name(row, flag)
    if name is None:
        return None
    a_val, a_err, measured = age_cells(row)
    _USED_MEASURED_AGE['any'] |= measured
    cells = [name, fmt(g(row, 'mass'), prec['mass'])]
    cells += pm(g(row, 'U'), g(row, 'Uerr'), prec['U'])
    cells += pm(g(row, 'Th'), g(row, 'Therr'), prec['Th'])
    cells += pm(g(row, 'Sm'), g(row, 'Smerr'), prec['Sm'])
    cells += pm_round_to_unc(g_trace(row, 'Cu'), g(row, 'Cuerr'))
    cells += pm_round_to_unc(g_trace(row, 'As'), g(row, 'Aserr'))
    cells += pm(g_trace(row, 'Zr'), g(row, 'Zrerr'), prec['Zr'])
    cells += pm_round_to_unc(g_trace(row, 'Ag'), g(row, 'Agerr'))
    cells += pm_round_to_unc(g_trace(row, 'Sb'), g(row, 'Sberr'))
    cells += [fmt(g(row, 'eU'), prec['eU']), fmt(g(row, 'he4'), prec['he4'])]
    cells += [a_val, a_err]
    return ' & '.join(cells) + r' \\'


def data_row_trace(rows, i, prec=None, flag=None):
    """Main-text-samples trace-element SI row: Sample, Cu, As, Ag, Sb."""
    row = rows[i]
    name = row_name(row, flag)
    if name is None:
        return None
    cells = [name]
    for el in ('Cu', 'As', 'Ag', 'Sb'):
        cells += pm_round_to_unc(g_trace(row, el), g(row, el + 'err'))
    return ' & '.join(cells) + r' \\'


def group_header(label, ncols):
    return r'\multicolumn{%d}{l}{\textbf{%s}} \\' % (ncols, label)


def _hdr(cols):
    """cols: list of (label, unit, is_pair). Returns the two header rows."""
    top, bot = [], []
    for label, unit, pair in cols:
        if pair:
            top.append(r'\multicolumn{2}{c}{%s}' % label)
            bot.append(r'\multicolumn{2}{c}{%s}' % unit)
        else:
            top.append(label)
            bot.append(unit)
    return ' & '.join(top) + r' \\' + '\n' + ' & '.join(bot) + r' \\'


def _spec(cols):
    out = []
    for i, (_, _, pair) in enumerate(cols):
        if i == 0:
            out.append('l')
        else:
            out.append('r@{}l' if pair else 'r')
    return ' '.join(out)


def _ncols(cols):
    return sum(2 if p else 1 for _, _, p in cols)


MAIN_COLS = [('Sample', '', False), ('Mass', '(mg)', False),
             ('U', '(ppm)', True), ('Th', '(ppm)', True), ('Sm', '(ppm)', True),
             ('Zr', '(ppm)', True), ('eU', '(ppm)', False),
             ('$^4$He', '(ncc)', False), ('Age', '(Ma)', True)]
FULL_COLS = [('Sample', '', False), ('Mass', '(mg)', False),
             ('U', '(ppm)', True), ('Th', '(ppm)', True), ('Sm', '(ppm)', True),
             ('Cu', '(ppm)', True), ('As', '(ppm)', True), ('Zr', '(ppm)', True),
             ('Ag', '(ppm)', True), ('Sb', '(ppm)', True), ('eU', '(ppm)', False),
             ('$^4$He', '(ncc)', False), ('Age', '(Ma)', True)]
TRACE_COLS = [('Sample', '', False), ('Cu', '(ppm)', True), ('As', '(ppm)', True),
              ('Ag', '(ppm)', True), ('Sb', '(ppm)', True)]

MAIN_N, FULL_N, TRACE_N = _ncols(MAIN_COLS), _ncols(FULL_COLS), _ncols(TRACE_COLS)

FOOTNOTE_OLD = (SYM_OLD + r'Excluded: analyzed under the early (old) protocol '
                r'(\S\ref{ch3-geochron-helium-methods}, \S\ref{ch3-results-gympie-ages}).')
FOOTNOTE_OUTLIER = (SYM_OUTLIER + r'Excluded: outlier '
                    r'(\S\ref{ch3-results-gympie-ages}, Fig.~\ref{fig:ch3-gogebic-he-vs-eu}).')


def table_preamble(cols, footnotes=(), tabcolsep='4pt', size_cmd=None):
    """Landscape longtable preamble with %s slots for caption, label and the
    two header blocks. `size_cmd` (e.g. r'\tiny') locally redefines
    \scriptsize -- the document-wide longtable default set by
    \AtBeginEnvironment in dissertation_preamble.tex -- because a bare size
    command can't go between \begin{longtable} and \caption (see the git
    history of this file for the "Misplaced \noalign" story). `footnotes`
    are printed under the closing rule on the table's last page."""
    ncols = _ncols(cols)
    open_size = (r'{\let\scriptsize%s' % size_cmd + '\n') if size_cmd else ''
    foot = ''.join(r'\multicolumn{%d}{@{}l}{%s} \\' % (ncols, f) + '\n' for f in footnotes)
    return (open_size + r"""\begin{landscape}
\setlength{\tabcolsep}{%s}
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
%s\endlastfoot
""" % (tabcolsep, _spec(cols), ncols, ncols, foot))


def table_end(size_cmd=None):
    return r"""\end{longtable}
\end{landscape}""" + ('\n}' if size_cmd else '')


# Row-index groupings shared by all three tables.
KIDD_CREEK_MAIN = list(range(3, 15))
GYMPIE = list(range(49, 65))
GYMPIE_FLAGS = {49: 'old', 50: 'old', 51: 'old', 52: 'old', 56: 'outlier'}
DURANGO = list(range(33, 47))
DURANGO_FLAGS = {33: 'old', 34: 'old', 35: 'old', 36: 'old'}
DURANGO_AVG = 47
GOGEBIC = list(range(89, 98))
GOGEBIC_FLAGS = {92: 'outlier'}   # 041323MG16b, >1.5 Ga, interpreted U loss

EXPECTED_NAMES = {33: '2211DApA', 36: '2022StDApA', 49: '013023PVGyPy-1',
                  52: '013023PVGyPy-4', 56: '0413PyGy-4', 92: '041323MG16b'}

MAIN_GROUPS = [
    ('Kidd Creek Pyrite (Archean VMS, $\\sim$2716 Ma host)', KIDD_CREEK_MAIN, {}, DEFAULT_PREC),
    ('Gympie Pyrite (Permo-Triassic orogenic Au)', GYMPIE, GYMPIE_FLAGS, DEFAULT_PREC),
    ('Durango Apatite Standard (accepted age 32.1 Ma; Farley 2000)',
     DURANGO + [DURANGO_AVG], DURANGO_FLAGS, DURANGO_PREC),
    ('Gogebic Iron Range BIF Hematite Standard (MI-43; 571 Ma)', GOGEBIC, GOGEBIC_FLAGS, GOGEBIC_PREC),
]

SI_GROUPS = [
    ('Kidd Creek Pyrite (replicate / mass-only aliquots)', list(range(16, 23))),
    ('Franklin, NJ Pyrite (marble/volcanics, $\\sim$1.3--1.0 Ga)', list(range(24, 29))),
    ("Franklin, NJ Fluorite", list(range(30, 32))),
    ('Rustenburg/Pilanesberg(?) Pyrite', list(range(68, 76))),
    ('Magnet Cove Carbonatite Pyrite, Arkansas ($\\sim$100 Ma)', list(range(77, 79))),
    ('French Creek, PA Magnetite and Pyrite ($\\sim$130 Ma)', list(range(81, 85))),
    ('Salzburg, Austria Arsenopyrite', [87]),
]

ROUNDING_CAPTION = (
    r" Uncertainties are 2$\sigma$ and are given to the same decimal place as the value: "
    r"U, Th, Sm, and eU to 0.01~ppm (0.1~ppm for Durango apatite, and for U and eU in "
    r"Gogebic hematite), Zr to 0.1~ppm, $^4$He to 0.1~ncc, and ages to 0.1~Ma, or to "
    r"1~Ma where the uncertainty exceeds 10~Ma.")


def _measured_age_caption():
    if not _USED_MEASURED_AGE['any']:
        return ''
    return (r" %s marks early aliquots analyzed before a tube blank was available, for "
            r"which the uncorrected measured age is reported instead." % SYM_MEASAGE)


def _body_rows(rows, groups, ncols, row_fn):
    body = []
    for k, (label, idxs, flags, prec) in enumerate(groups):
        if k:
            body.append(r'\midrule')
        body.append(group_header(label, ncols))
        for i in idxs:
            r = row_fn(rows, i, prec=prec, flag=flags.get(i))
            if r:
                body.append(r)
    return body


def build_main_table(rows):
    hdr = _hdr(MAIN_COLS)
    rows_tex = _body_rows(rows, MAIN_GROUPS, MAIN_N, data_row_main)
    caption = (
        r"U-Th/He geochronology results for the four sample suites discussed in the main "
        r"text: Kidd Creek pyrite, Gympie pyrite, and the Durango apatite and Gogebic (MI-43) "
        r"hematite standards run alongside them, including U, Th, and Sm (the radiogenic-budget "
        r"elements quantified by ICPMS, \S\ref{sec:ch3-experimental-methods-geochronology}) "
        r"plus Zr, also measured as a ratio to spike vanadium; `--' denotes below detection or "
        r"not measured for that aliquot. The remaining ICPMS trace elements measured the same "
        r"way (Cu, As, Ag, Sb) are reported separately in the Supplementary Information "
        r"(Table~\ref{tab:ch3-main-geochron-trace}) rather than here, to keep this table within "
        r"the page width. Ages are the atmospheric-He-corrected `Age (Ma Atm=1Ra Corr.)' value."
        + _measured_age_caption() +
        r" %s marks aliquots analyzed under the early (``old method'') protocol that predated "
        r"the warm atmosphere-degassing step (\S\ref{ch3-geochron-helium-methods}, "
        r"Fig.~\ref{fig:ch3-durango-age-vs-ra}), and, for the first four Gympie aliquots, also "
        r"the Parr-vessel HCl digestion (\S\ref{ch3-results-gympie-ages}); %s marks outliers "
        r"excluded from interpretation (\S\ref{ch3-results-gympie-ages}; "
        r"\S\ref{sec:ch3-experimental-methods-geochronology} for Gogebic 041323MG16b)."
        % (SYM_OLD, SYM_OUTLIER)
        + ROUNDING_CAPTION +
        r" The complete compilation, including localities not discussed in the main text, is "
        r"given in the Supplementary Information (Table~\ref{tab:ch3-si-geochron}).")
    pre = table_preamble(MAIN_COLS, footnotes=(FOOTNOTE_OLD, FOOTNOTE_OUTLIER), tabcolsep='4pt',
                         size_cmd=MAIN_SIZE)
    return '\n'.join([pre % (caption, 'tab:ch3-main-geochron', hdr, hdr)] + rows_tex
                     + [table_end(size_cmd=MAIN_SIZE)])


def build_main_trace_si_table(rows):
    """SI table: Cu/As/Ag/Sb for the same four main-text suites, kept out of
    the main table to fit the page width."""
    hdr = _hdr(TRACE_COLS)
    rows_tex = _body_rows(rows, MAIN_GROUPS, TRACE_N, data_row_trace)
    caption = (
        r"Cu, As, Ag, and Sb (measured as ratios to spike vanadium by the same ICPMS run as "
        r"U, Th, Sm, and Zr, \S\ref{sec:ch3-experimental-methods-geochronology}) for the same "
        r"Kidd Creek, Gympie, Durango, and Gogebic aliquots reported in "
        r"Table~\ref{tab:ch3-main-geochron}, in the same row order; `--' denotes below "
        r"detection or not measured for that aliquot. Uncertainties are 2$\sigma$, rounded to "
        r"two significant figures, with each value rounded to the same decimal place. "
        r"Footnote symbols (%s, %s) as in Table~\ref{tab:ch3-main-geochron}."
        % (SYM_OLD, SYM_OUTLIER))
    pre = table_preamble(TRACE_COLS, footnotes=(FOOTNOTE_OLD, FOOTNOTE_OUTLIER), tabcolsep='8pt',
                         size_cmd=MAIN_SIZE)
    return '\n'.join([pre % (caption, 'tab:ch3-main-geochron-trace', hdr, hdr)] + rows_tex
                     + [table_end(size_cmd=MAIN_SIZE)])


# Font sizes (each locally replaces the document-wide \scriptsize longtable
# default). The 13-quantity SI table still needs \tiny to fit the landscape
# text width; the main-text and trace tables fit at \small.
MAIN_SIZE = r'\small'
SI_SIZE = r'\tiny'


def build_si_table(rows):
    hdr = _hdr(FULL_COLS)
    groups = [(label, idxs, {}, DEFAULT_PREC) for label, idxs in SI_GROUPS]
    rows_tex = _body_rows(rows, groups, FULL_N, data_row_full)
    caption = (
        r"U-Th/He geochronology results for all remaining sample suites in the compilation, "
        r"not discussed in the main text: Kidd Creek replicate/mass-only aliquots, Franklin "
        r"(NJ) pyrite and fluorite, Rustenburg/Pilanesberg pyrite, Magnet Cove carbonatite "
        r"pyrite, French Creek magnetite/pyrite, and Salzburg arsenopyrite. Reported here for "
        r"completeness, with the full trace-element suite (Cu, As, Zr, Ag, Sb) retained since "
        r"these aliquots are not duplicated in the main text; columns, rounding, and conventions "
        r"as in Table~\ref{tab:ch3-main-geochron} (Cu, As, Ag, and Sb rounded as in "
        r"Table~\ref{tab:ch3-main-geochron-trace})." + _measured_age_caption())
    pre = table_preamble(FULL_COLS, tabcolsep='3.5pt', size_cmd=SI_SIZE)
    return '\n'.join([pre % (caption, 'tab:ch3-si-geochron', hdr, hdr)] + rows_tex
                     + [table_end(size_cmd=SI_SIZE)])


def main():
    rows = load_rows()
    for i, nm in EXPECTED_NAMES.items():
        assert rows[i][COLS['name']] == nm, (i, rows[i][COLS['name']], nm)
    si_table = build_si_table(rows)
    main_trace_si_table = build_main_trace_si_table(rows)
    main_table = build_main_table(rows)

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
    out.append('%  Rounding and footnote-symbol conventions: see the comment block above')
    out.append('%  DEFAULT_PREC in the generator script.')
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
