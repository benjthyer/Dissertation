"""
Generates per-sample 3He step-heat data tables for Chapter 3, as
auto-generated LaTeX macros, following the same pattern as
write_chapter3_geochron_tables.py: each table is written as a
\\newcommand macro expanding to a complete `landscape`+`longtable`
environment, modeled directly on Chapter 2's hand-written step-heat
tables (Chapter2/Writing/chapter2_body.tex, Tables~ch2-distilled-3he/
ch2-distilled-4he) but restricted to 3He only, since every sample here
(unlike Chapter 2's hydrothermal goethite experiment, and unlike this
chapter's own Rustenburg pyrite) is a proton-irradiated 3He step heat.

Source data, per sample:
  - Chapter3/Tables/plotable_sulfides_cache.pkl: the exact same cleaned,
    "treatment as uncertainty" ln(D/a^2) central value and LB/UB
    uncertainty widths already used by every Arrhenius/delta figure in
    this chapter (Sulfide_compilation_Arr.pdf, Pyrite_delta_compilation.pdf,
    the per-sample step_heat_regressions/*.pdf figures, and the
    combined SI grid). Using this cache (rather than re-deriving bounds
    from the raw Reduced01_*.xlsx "Diffusivities" sheet, which carries
    occasional Excel #NUM! formula errors on early, low-signal steps)
    guarantees these tables report exactly the same numbers as the
    figures, by construction.
  - Chapter3/Tables/plotable_row_index.json: which Reduced01_*.xlsx file
    and Step numbers back each sample's plotable_sulfides_cache rows
    (written by Tables/build_plotable_cache.py).
  - Each sample's own Reduced01_*.xlsx: Temp/Time/Cum-3He/ntUB from the
    "Diffusivities" (or "Sheet2") tab, and per-step measured 3He from the
    first tab, joined by the same fixed row-position offset
    Tables/build_plotable_cache.py already establishes and documents
    (first-sheet row = Diffusivities row - 2).

IMPORTANT SCOPE NOTE (unlike Chapter 2's raw tables): only the "plotable"
steps already used throughout this chapter's figures are listed here
(typically the lambda*t>=4 steps with a determinable diffusivity, per
Sec. 3.4/Analytical Methods) -- early permeation/equilibration steps and
any manually-excluded steps (see Tables/build_plotable_cache.py's
MANUAL_STEP_EXCLUSIONS, e.g. SalAspIrr's final 6-step ion-source-failure
tail) are omitted rather than listed with a string of "--" placeholders,
since the raw Diffusivities sheet's un-curated bound columns for those
rows are not reliable (see above). This is noted in each table's caption.

NOTE: rendered in portrait (no `landscape` wrapper) -- these 9-column
tables fit the Caltech thesis's 5.5in text width at \scriptsize (the
\longtable default this preamble sets), unlike Chapter 2's wider
10-13 column distilled tables, which still need landscape.

Output: Chapter3/Writing/chapter3_stepheat_tables.tex
    \\ChThreeStepHeatLVCOSmall    : LVCOPy230630 (Leadville pyrite, 200 um)
    \\ChThreeStepHeatLVCOBig      : BigLVCOPy230707 (Leadville pyrite, 400 um)
    \\ChThreeStepHeatLVCOIsolated : 112123LVCOPyIrr (Leadville pyrite, S-isolated)
    \\ChThreeStepHeatAsp          : SalAspIrr (arsenopyrite)
    \\ChThreeStepHeatGal          : GalTS230630 (galena)
    \\ChThreeStepHeatCCp          : CCpTS230630 (chalcopyrite)

Regenerate after any change to the underlying workbooks/cache:
    python3 Chapter3/Tables/build_plotable_cache.py
    python3 Chapter3/Figures/write_chapter3_stepheat_tables.py
"""
import json
import os
import sys

import openpyxl
import pandas as pd

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
TABLES_DIR = os.path.join(FIG_DIR, '..', 'Tables')
OUT_PATH = os.path.join(FIG_DIR, '..', 'Writing', 'chapter3_stepheat_tables.tex')

sys.path.insert(0, TABLES_DIR)
import build_plotable_cache as bpc  # noqa: E402 -- reuse its column-finding/row-offset logic

LB_SENTINEL_THRESHOLD = 4.9  # matches plot_style.py's convention exactly

# {macro name (letters only -- LaTeX command names can't contain digits):
#   (sample key in the cache/index, display label, caption arrhenius/delta
#    figure cross-refs)}
SAMPLES = [
    ('ChThreeStepHeatLVCOSmall', 'LVCOPy230630', 'ch3-stepheat-lvco-small',
     'Pyrite, Leadville, CO, 200 \\textmu m half-prism width',
     'Fig.~\\ref{fig:ch3-sulfide-arrhenius-compilation} (Arrhenius) and '
     'Fig.~\\ref{fig:ch3-pyrite-delta-compilation} (delta)'),
    ('ChThreeStepHeatLVCOBig', 'BigLVCOPy230707', 'ch3-stepheat-lvco-big',
     'Pyrite, Leadville, CO, 400 \\textmu m half-prism width',
     'Fig.~\\ref{fig:ch3-sulfide-arrhenius-compilation} (Arrhenius) and '
     'Fig.~\\ref{fig:ch3-pyrite-delta-compilation} (delta)'),
    ('ChThreeStepHeatLVCOIsolated', '112123LVCOPyIrr', 'ch3-stepheat-lvco-isolated',
     'Pyrite, Leadville, CO, sulfur-isolated (glass-shard-separated)',
     'Fig.~\\ref{fig:ch3-sulfide-arrhenius-compilation} (Arrhenius) and '
     'Fig.~\\ref{fig:ch3-pyrite-delta-compilation} (delta)'),
    ('ChThreeStepHeatAsp', 'SalAspIrr', 'ch3-stepheat-asp',
     'Arsenopyrite, Mitterberg, Austria',
     'Fig.~\\ref{fig:ch3-sulfide-arrhenius-compilation} (Arrhenius) and '
     'Fig.~\\ref{fig:ch3-si-stepheat-grid-other} (delta, row 1)'),
]

SI_SAMPLES = [
    ('ChThreeStepHeatGal', 'GalTS230630', 'ch3-stepheat-gal', 'Galena, Tri-State District, Missouri',
     'Fig.~\\ref{fig:ch3-si-stepheat-grid-other} (row 2)'),
    ('ChThreeStepHeatCCp', 'CCpTS230630', 'ch3-stepheat-ccp', 'Chalcopyrite, Baxter Springs, Kansas',
     'Fig.~\\ref{fig:ch3-si-stepheat-grid-other} (row 3)'),
]

TABLE_PREAMBLE = r"""\begin{footnotesize}
\begin{longtable}{r r r r r r r r r}
\caption{%s}\label{%s}\\
\toprule
%s
\midrule
\endfirsthead
\multicolumn{9}{l}{\textit{(continued)}} \\
\toprule
%s
\midrule
\endhead
\midrule
\multicolumn{9}{r}{\textit{continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
"""

TABLE_END = r"""\end{longtable}
\end{footnotesize}"""

HEADER_ROW = (r'Step & Temp & Time & $^3$He meas. & Cum. $^3$He & $n_{t,\mathrm{UB}}$ & '
              r'$\ln(D/a^2)_{\mathrm{LB}}$ & $\ln(D/a^2)_{m}$ & $\ln(D/a^2)_{\mathrm{UB}}$ \\'
              '\n' + r'& (\textdegree C) & (min) & (pccSTP) & (pccSTP) & (pccSTP) & & & \\')


def fmt(v, nd=2):
    return f'{v:.{nd}f}' if v is not None else '--'


def load_sample_rows(sample):
    """Return a list of row-dicts (step, temp, time_min, he3_meas, cum_he3,
    nt_ub, ln_lb, ln_m, ln_ub) for every plotable step of `sample`, in step
    order, pulling the ln(D/a^2) central+bounds from plotable_sulfides_cache.pkl
    and everything else from that sample's own Reduced01_*.xlsx."""
    cache = pd.read_pickle(os.path.join(TABLES_DIR, 'plotable_sulfides_cache.pkl'))
    index = json.loads((open(os.path.join(TABLES_DIR, 'plotable_row_index.json'))).read())

    sub = cache[cache['sample'] == sample].sort_values('step')
    entry = index[sample]
    wb = openpyxl.load_workbook(os.path.join(TABLES_DIR, entry['source_file']), data_only=True)
    ws2 = bpc._diffusivity_sheet(wb)
    cols = bpc._diff_columns(ws2)
    step_to_row2 = {
        ws2.cell(row=r, column=cols['step']).value: r
        for r in bpc._diff_data_rows(ws2, cols)
    }
    ws1 = wb[wb.sheetnames[0]]
    he3_col = [c for c in range(1, ws1.max_column + 1)
               if ws1.cell(row=1, column=c).value == '3He (pccSTP)'][0]

    ntub_col = [i + 1 for i, h in enumerate(
        [ws2.cell(row=1, column=c).value for c in range(1, ws2.max_column + 1)])
        if h == 'ntUB'][0]
    cum_col = [i + 1 for i, h in enumerate(
        [ws2.cell(row=1, column=c).value for c in range(1, ws2.max_column + 1)])
        if h == 'Cum 3He'][0]
    temp_col = 2  # 'Temp (C)', column B -- fixed position, same for every Reduced01 file
    sec_col = 3   # 'Seconds', column C

    rows = []
    for _, r in sub.iterrows():
        step = r['step']
        r2 = step_to_row2.get(step)
        if r2 is None:
            continue
        r1 = bpc._first_sheet_row(r2)
        temp = ws2.cell(row=r2, column=temp_col).value
        seconds = ws2.cell(row=r2, column=sec_col).value
        cum_he3 = ws2.cell(row=r2, column=cum_col).value
        nt_ub = ws2.cell(row=r2, column=ntub_col).value
        he3_meas = ws1.cell(row=r1, column=he3_col).value if bpc.WS1_DATA_START_ROW <= r1 <= ws1.max_row else None

        def _numeric(v):
            return v if isinstance(v, (int, float)) else None

        ln_m = _numeric(r['ln(d/a^2)'])
        lb_delta = _numeric(r['LB_dln(d/a^2)'])
        ub_delta = _numeric(r['UB_dln(d/a^2)'])
        ln_lb = (ln_m - lb_delta) if (ln_m is not None and lb_delta is not None
                                       and lb_delta < LB_SENTINEL_THRESHOLD) else None
        ln_ub = (ln_m + ub_delta) if (ln_m is not None and ub_delta is not None) else None

        rows.append(dict(step=int(step), temp=temp,
                          time_min=(seconds / 60.0 if isinstance(seconds, (int, float)) else None),
                          he3_meas=he3_meas, cum_he3=cum_he3, nt_ub=nt_ub,
                          ln_lb=ln_lb, ln_m=ln_m, ln_ub=ln_ub))
    return rows


def build_table(macro, sample, tab_key, label, fig_note, caption_extra=''):
    rows = load_sample_rows(sample)
    tab_label = f'tab:{tab_key}'
    caption = (
        rf"$^3$He step-heat dataset for {label} (sample {sample.replace('_', chr(92) + '_')}), "
        rf"under the uncertainty bounding method (\S\ref{{bounding-method}}). "
        rf"The measured and cumulative $^3$He, "
        rf"upper-bound residual ampoule content ($n_{{t,\mathrm{{UB}}}}$), and the "
        rf"corresponding lower-bound, central, and upper-bound apparent diffusivities are "
        rf"plotted in {fig_note}. "
        rf"$\ln(D/a^2)_{{\mathrm{{LB}}}}$ is left blank where the lower bound is "
        rf"unconstrained (\S\ref{{sec:ch3-analytical-methods}}).{caption_extra}"
    )
    body = [TABLE_PREAMBLE % (caption, tab_label, HEADER_ROW, HEADER_ROW)]
    for r in rows:
        body.append(' & '.join([
            str(r['step']),
            fmt(r['temp'], 1),
            fmt(r['time_min'], 1),
            fmt(r['he3_meas'], 4),
            fmt(r['cum_he3'], 4),
            fmt(r['nt_ub'], 4),
            fmt(r['ln_lb'], 3),
            fmt(r['ln_m'], 3),
            fmt(r['ln_ub'], 3),
        ]) + r' \\')
    body.append(TABLE_END)
    return '\n'.join(body)


def main():
    out = []
    out.append('% =============================================================')
    out.append('%  chapter3_stepheat_tables.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.')
    out.append('%  Written by Figures/write_chapter3_stepheat_tables.py from')
    out.append('%  Tables/plotable_sulfides_cache.pkl, Tables/plotable_row_index.json,')
    out.append('%  and the per-sample Tables/Reduced01_*.xlsx workbooks.')
    out.append('%')
    out.append('%  Regenerate after any change to the underlying data:')
    out.append('%    python3 Chapter3/Tables/build_plotable_cache.py')
    out.append('%    python3 Chapter3/Figures/write_chapter3_stepheat_tables.py')
    out.append('%')
    out.append('%  Main-text macros (pyrite/arsenopyrite): \\ChThreeStepHeatLVCOSmall,')
    out.append('%  \\ChThreeStepHeatLVCOBig, \\ChThreeStepHeatLVCOIsolated, \\ChThreeStepHeatAsp.')
    out.append('%  SI macros (galena/chalcopyrite): \\ChThreeStepHeatGal, \\ChThreeStepHeatCCp.')
    out.append('% =============================================================')
    for macro, sample, tab_key, label, fig_note in SAMPLES:
        out.append(r'\newcommand{\%s}{%%' % macro)
        out.append(build_table(macro, sample, tab_key, label, fig_note))
        out.append('}')
        out.append('')
    for macro, sample, tab_key, label, fig_note in SI_SAMPLES:
        out.append(r'\newcommand{\%s}{%%' % macro)
        out.append(build_table(macro, sample, tab_key, label, fig_note))
        out.append('}')
        out.append('')

    with open(OUT_PATH, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print(f'Wrote {OUT_PATH}')


if __name__ == '__main__':
    main()
