# Dissertation Fix Journal

High-level record of the changes made to `DissertationBJT` while working
through the punch list. Dated entries are in the order the tasks were
tackled. "Judgment calls" sections flag anywhere a decision was made
without exhaustively verifying every alternative, per the instruction to
flag and move on rather than over-invest.

---

## 1. Removed `thyer2026` citations, replaced with internal Ch. 1 cross-references

Every `\citep{thyer2026}` / `\citet{thyer2026}` in the dissertation was
removed and replaced with an internal `\S\ref{...}` (or `\nameref`) to the
relevant Chapter 1 section, since the dissertation will not be submitted
citing that (unpublished/self) reference.

Files touched: `Chapter1/Writing/chapter1_body.tex` (one duplicate-label
fix needed to make Ch.1 cross-refs resolvable at all -- see item 2),
`Chapter2/Writing/chapter2_body.tex` (8 replacements),
`Chapter3/Writing/HeInSulfides_Main_Body.tex` (3 replacements).

**Judgment calls (flagged per your instruction, not agonized over):**
Each `thyer2026` citation was mapped to the Chapter 1 section whose
content most plausibly matched the citing sentence's claim (e.g. a
citation next to a claim about the numerical diffusion model went to
`\S\ref{numerical-diffusive-permeation-model-for-arbitrary-thermally-history-and-diffusive-disequilibrium}`,
one next to a claim about the bounding-method went to
`\S\ref{bounding-method}`, etc.). I did not re-derive or verify that
each Chapter 1 section actually substantiates the specific numeric claim
next to the old citation -- please spot check these once, since I was
matching by topic/section title rather than re-confirming every number.

---

## 2. Fixed cross-references throughout ("every reference failing")

Two distinct bugs were causing this, not one:

- **Genuinely undefined labels**: a handful of `\ref{}`/`\S\ref{}` calls
  pointed at label names that didn't exist (typos / renamed sections).
  Fixed by correcting the label name at the call site to match the
  actual `\label{}` (e.g. `\ref{tab:ch3-sulfide-samples}` ->
  `\ref{tab:ch3-step-heat-tubes}` in `HeInSulfides_Main_Body.tex`, which
  was simply referencing the wrong table name).

- **Silently wrong references (the bigger issue)**: several `\label{}`
  keys were defined *more than once* across the document -- most
  importantly `experimental-methods`, `analytical-methods`, `results`,
  and `discussion`, which existed as both a Chapter 1 label and a
  Chapter 2 label. LaTeX does not error on this; it silently resolves
  every `\ref` to whichever instance compiled *last*, so many in-chapter
  cross-references were pointing at the wrong chapter's section without
  any visible warning. This is almost certainly what looked like "every
  single reference is failing" -- the numbers were rendering, just
  wrong.

  Fixed by renaming Chapter 2's colliding labels with a `ch2-` prefix
  (`ch2-experimental-methods`, `ch2-analytical-methods`, `ch2-results`,
  `ch2-discussion`) and updating every `\ref`/`\S\ref` call site in
  Chapter 2 (`chapter2_body.tex`, `chapter2goethite_SI_body.tex`,
  `chapter2_naive_isothermal_tables.tex`) to match. Chapter 1 keeps the
  unprefixed names since nothing else collided with it.

  Note: `Chapter2/Writing/SI_Reorganization_Log.md` (a journal from an
  earlier pass on this document) had already independently identified
  this same multiply-defined-label bug and recommended this same
  `ch1-`/`ch2-` prefixing fix, but it had not actually been applied --
  confirms this was a real, previously-known-but-unfixed issue rather
  than something I'm introducing new risk with.

- Also fixed one real duplicate-label collision *within* Chapter 1
  itself: `\label{fig:simulated-arrhenius-lag-artifact}` had been
  accidentally pasted onto two different figures (the ampoule photo and
  the diffusion-simulation figure). Renamed the ampoule photo's label to
  `fig:ampoule-photo` (verified nothing referenced the ampoule photo
  specifically, so this was safe).

**Verification**: full `latexmk` rebuild of the whole dissertation shows
**zero** `undefined on input line`, `Citation ... undefined`, or
`multiply defined` warnings in the log, for the whole 222-page document.

---

## 3. Chapter 2 SI: misaligned last table

The last table in the Chapter 2 SI (`tab:ch2-distilled-naive-3he`, a
12-column longtable) had visibly tighter, unevenly-spaced columns than
the header row above it -- not a structural/data bug, just uneven
column spacing. Fixed by changing its column spec from `r r r r r r r r
r r r r` to `@{\extracolsep{\fill}}r r r r r r r r r r r r`, which
spreads the columns evenly across the full available width, matching
the other tables in that SI. Verified visually via rendered page image
comparison (before/after).

While working in this same SI file (`chapter2goethite_SI_body.tex`) to
fix the duplicate-label issue above, I found two places where the prose
refers to content that was never actually written: a "Helium-4
Blank-Level Corrections" discussion and a closing "Totals" section. Per
your instruction not to over-invest in judgment calls, I did not attempt
to reconstruct this content (checked the standalone journal-manuscript
version of this SI too -- it doesn't have this content either, so it's
genuinely unwritten, not just misplaced). I inserted clearly marked
`\todo{}` stub sections/subsections at the appropriate spots so the
document structure and numbering are in place and the gap is visible
rather than silently missing:
- `\subsection{Helium-4 Blank-Level Corrections}` (stub) after the naive
  3He longtable.
- `\section{Totals}` (stub) at the end of the file.

**You'll want to actually write these two sections before submission.**

---

## 4. Chapter 3 step-heat tables: landscape -> portrait

Both the main-text and SI step-heat tables
(`Chapter3/Writing/chapter3_stepheat_tables.tex`) are generated by
`Chapter3/Figures/write_chapter3_stepheat_tables.py` from source data --
edited the generator (removed the `\begin{landscape}...\end{landscape}`
wrapper from the table preamble/end templates) and re-ran it, rather
than hand-patching the generated `.tex` (which is marked "DO NOT EDIT BY
HAND" and would be overwritten on the next regeneration anyway). All 6
step-heat table macros (`\ChThreeStepHeatLVCOSmall`,
`\ChThreeStepHeatLVCOBig`, `\ChThreeStepHeatLVCOIsolated`,
`\ChThreeStepHeatAsp`, `\ChThreeStepHeatGal`, `\ChThreeStepHeatCCp`) now
render portrait. Verified: zero overfull-hbox warnings for these tables
after rebuild, and a rendered page image confirms clean portrait layout
with working cross-references.

---

## 5. Chapter 3 geochronology table: overflow fix + column split

The original single 14-column geochronology table was ~4 inches too
wide for the page even in landscape. Fixed by splitting it into three
tables, per your suggestion to move Cu/As/Ag/Sb to the SI:

- **`\ChThreeGeochronMainTable`** (main text, Table 3.6): the four
  main-text sample suites (Kidd Creek pyrite, Gympie pyrite, Durango
  apatite, Gogebic hematite), now 10 columns (Sample, Mass, U, Th, Sm,
  Zr, eU, He-4, Age, Note) -- Cu/As/Ag/Sb dropped. Fits with **zero**
  page overflow.
- **`\ChThreeGeochronMainTraceSITable`** (new, SI, Table 3.9): Cu, As,
  Ag, Sb for those same four main-text suites/aliquots, in the same row
  order, so the data isn't lost -- just moved. 6 columns, fits
  comfortably.
- **`\ChThreeGeochronSITable`** (SI, Table 3.10): everything else in the
  compilation (Kidd Creek replicates, Franklin, Rustenberg/Pilanesberg,
  Magnet Cove, French Creek, Salzburg) -- kept the full 14-column
  trace-element suite since these aliquots aren't duplicated in the main
  table.

The 14-column SI table was still ~188pt too wide even after the split.
Closed the remaining gap through several width-reduction steps, all
applied only to that one table via a scoped LaTeX group (not
document-wide): switched from the document's default `\scriptsize` to
`\tiny`, tightened `\tabcolsep` from 3pt down to 0.75pt, reduced
U/Th/Sm/eU decimal precision from 3 to 2 places (SI-only; the main-text
table keeps 3), and dropped the redundant text-mode spaces around
`$\pm$` (math mode already adds its own operator spacing, so the extra
spaces were pure waste). Ended at **zero** overfull-hbox warnings for
this table. All three tables were visually confirmed via rendered page
images -- data is dense but nothing is cut off or overlapping.

**Judgment call**: the `\tiny` + tight-`\tabcolsep` combination makes
Table 3.10 quite dense (small font, columns nearly touching). This was
the tradeoff for keeping all 14 columns in one table at your request
rather than splitting further; if you'd prefer a further split (e.g.
separating the trace elements out of this table too, mirroring what was
done for the main table) over the current density, that's a quick
follow-up change to `write_chapter3_geochron_tables.py`.

**Implementation note for future reference**: overriding a longtable's
font size locally in this document can't be done with a bare `\tiny`
placed right after `\begin{longtable}{...}` -- longtable requires
`\caption` to be the literal first thing in the environment, and a bare
size command there breaks its internal bookkeeping ("Misplaced
\noalign"/"Misplaced \omit" errors). The working pattern (used here, and
worth reusing) is to wrap the whole `landscape`+`longtable` block in a
group that does `\let\scriptsize\tiny`, so the document's existing
`\AtBeginEnvironment{longtable}{\centering\scriptsize}` hook -- which
fires invisibly and correctly as the true first content -- ends up
calling `\tiny` instead.

---

## 6 & 7. Split the Sulfide Step-Heat Compilation SI figure; label every subplot's x-axis

The "Chapter 3 Sulfide Step-Heat Compilation: Arrhenius and Delta Plots,
All Samples" figure (`Chapter3/Figures/fig_ch3_stepheat_si_grid.py`,
originally a 7-row x 2-column grid) was falling off the bottom of the
page. Split into two figures as requested:

- **Figure 3.17** ("...Pyrite Samples"): 4x2 grid -- Rustenburg pyrite,
  LVCOPy230630 (small), 112123LVCOPyIrr (sulfur-isolated),
  BigLVCOPy230707 (big). All four are pyrite samples (three Leadville
  pyrite variants plus Rustenburg pyrite).
- **Figure 3.18** ("...Other Sulfides"): 3x2 grid -- SalAspIrr
  (arsenopyrite), GalTS230630 (galena), CCpTS230630 (chalcopyrite).

Both now fit cleanly on their own page with no overflow (verified via
rendered page images).

Also fixed the x-axis labeling issue you flagged: previously only the
bottom row's subplots had an x-axis title, which misleadingly implied
every row shared the same x-axis scale (they don't -- each sample's
Arrhenius/delta data spans a different range). Every subplot in both new
figures now gets its own x-axis tick numbers *and* axis title
($10^4/T$ (K) for Arrhenius, Cumulative He Yield $F_i$ for Delta),
independent of row position. Each figure's caption also now says
explicitly that rows are not directly comparable on a shared x-axis.

Updated all downstream cross-references that cited a specific row number
of the old combined figure (`Fig.~\ref{fig:ch3-si-stepheat-grid}, row
N`) to point at the correct new figure and renumbered row: SalAspIrr,
GalTS230630, and CCpTS230630 (formerly rows 5/6/7) are now rows 1/2/3 of
the new "Other Sulfides" figure (`fig:ch3-si-stepheat-grid-other`) --
touched `HeInSulfides_Main_Body.tex`, `HeInSulfides_SI_body.tex`, and
the auto-generated `chapter3_stepheat_tables.tex` (fixed at its
generator script, `write_chapter3_stepheat_tables.py`, not by hand).

Left behind: the old combined `Sulfide_StepHeat_SI_Grid.pdf` is now
unused (nothing references it anymore) -- moved to
`_to_delete/Sulfide_StepHeat_SI_Grid.pdf.orphaned` rather than deleted
outright, since I don't have delete permission in this session. See
"Cleanup" below.

---

## Other observations (not part of the punch list, flagging only)

- Page 184 (printed numbering) has a highlighted placeholder reading
  "(figs. 3.0xx)" in the chalcopyrite/chalcocite discussion text, and
  the SI's "Conclusions" section (`\S3.5`) has a `\todo{Summarize He
  retentivity findings and geochronologic implications.}` placeholder.
  Both look like pre-existing, intentionally-marked TODOs from before
  this session (not something I introduced, and not a broken `\ref` --
  the full-document rebuild shows zero undefined references). Flagging
  in case they were off your radar.

## Cleanup

This session's scratch files were moved into a new `_to_delete/`
subfolder in the repo root rather than deleted, since I don't have file
deletion permission on your machine from here:
- `_to_delete/_claude_stage/` -- staging tarballs and comparison PNGs
  used while testing compiles in a separate sandbox.
- `_to_delete/Sulfide_StepHeat_SI_Grid.pdf.orphaned` -- the old combined
  figure PDF, superseded by the two split figures above.

You can delete the `_to_delete/` folder whenever convenient; nothing in
the dissertation still references anything inside it.

## Full-document verification

Final rebuild of the complete 222-page dissertation (`latexmk -pdf`):
zero undefined-reference warnings, zero undefined-citation warnings,
zero multiply-defined-label warnings, zero overfull-hbox warnings in any
table alignment. All six fixed items (tables, figures, cross-references)
were additionally spot-checked visually via rendered page images, not
just by the absence of LaTeX warnings.

---

## Follow-up: larger step-heat grid figures, shorter captions, fewer pyrite x-axis ticks

Requested after the initial punch list, on Figures 3.17/3.18 (the split
pyrite / other-sulfides grids from items 6-7 above):

- **Captions cut roughly in half**, keeping only the essentials (sample
  list, the solid/dashed reference-line convention and where it's
  described, the per-row x-axis-scale note, and the cross-reference to
  the companion figure) and dropping repeated explanatory phrasing.
- **Images enlarged.** The shorter caption alone doesn't automatically
  grow the image -- the `\includegraphics[width=\textwidth,
  height=\textheight,keepaspectratio]` call was already, and remains,
  bound by `width=\textwidth` (5.5in on this class's letter/1.5in-margin
  page), not by height. So the actual fix was increasing the source
  matplotlib figure's per-row height (`ROW_HEIGHT_IN`, in
  `fig_ch3_stepheat_si_grid.py`, raised from 13.5/7 ~= 1.93 in/row to
  2.55 in/row): since width is the binding constraint, a taller source
  figure renders taller once scaled to that fixed width, using the
  vertical room the shorter caption freed up. Rebuilt and confirmed zero
  page-overflow (`Overfull \vbox`) warnings at the new size.
- **Pyrite grid x-axis ticks capped at 6.** The pyrite delta panels in
  particular had 8-9 tick labels crammed into narrow, 4-5-decimal-place
  ranges (e.g. `0.00325 0.00350 0.00375 ...`). Added
  `matplotlib.ticker.MaxNLocator(nbins=6)` to both the Arrhenius and
  delta panels' primary x-axis, applied only to the pyrite grid
  (`max_xticks=6` in `build_grid`/`plot_row`) since the other-sulfides
  grid's ticks were already reasonably spaced and you only flagged
  pyrite. Now renders at 5-6 clean ticks per panel instead of 8-9
  overlapping ones.

Verified via full rebuild (zero undefined refs/citations/overflow) and
rendered page images of both figures.

---

## Follow-up: new "Arsenopyrite" subsection (Ch. 3 Discussion)

Filled in the previously-empty `\subsection{Arsenopyrite}` in
`Chapter3/Writing/HeInSulfides_Main_Body.tex` (in §3.4 Discussion,
between "Remarkable Helium Retentivity of Pyrite and Arsenopyrite" and
"Thermal Helium Migration Systematics for Other Sulfides"), with two
short paragraphs per your request:

- Arsenopyrite's distorted, lower-symmetry structure relative to pyrite
  (\citep{morimotoclark1961}) as a first-order reason to expect it to be
  less helium-retentive than pyrite, noting this should vary with
  arsenopyrite's specific arsenic content.
- That equilibrium arsenopyrite composition is itself a function of
  formation temperature, increasing with temperature
  (\citep{barton1969,morimotoclark1961}), which complicates generalizing
  from one experimental aliquot to arsenopyrite as a species.
- The observed result -- arsenopyrite less retentive than pyrite but
  more retentive than any other sulfide measured in this study -- in
  agreement with \citep{yakubovich2019}.

Added a label (`ch3-discussion-arsenopyrite`) for consistency with the
sibling subsections, though nothing references it yet.

**Bonus fix while verifying**: found a genuinely broken citation
elsewhere in this same file, unrelated to the new subsection --
`\citep{lee1992}` (on the pipe/short-circuit diffusion mechanism
invoked for the Rustenburg pyrite) had no matching entry in
`references.bib`. This is very likely a typo for `lee1993` (Lee, J.K.W.,
1993, "The argon release mechanisms of hornblende in vacuo" --
topically exactly the short-circuit/pipe-diffusion citation being made,
and cited alongside the closely related `lo2000`, which explicitly
discusses "short-circuit diffusion"). Fixed to `\citep{lee1993}`; please
double check this is the paper you intended, since I'm inferring the
correct key from context rather than from your own confirmation. This
was missed by the "zero undefined citations" check earlier in this
journal -- worth being aware the full-document sweep isn't guaranteed to
be exhaustive against typos that happen to collide with no key at all
(this one only surfaced now because rebuilding after this edit re-ran
biber against the current citation set).

Verified via full rebuild: zero undefined references/citations, zero
overfull-hbox/vbox warnings, new subsection text and all three citations
render and resolve correctly (checked visually on the compiled page).

## Follow-up: Chapter 3 Conclusions section, a duplicate-label fix, and a remaining-work list

`Chapter3/Writing/HeInSulfides_Main_Body.tex`: while reading the full
chapter to write the Conclusions section, found that
`\label{fig:ch3-he-age-vs-inclusion-size}` (the He-age-vs-apatite-
inclusion-size figure) was defined TWICE for the same figure, once in
"Origin of Radiogenic Helium in Sulfides" (introducing the model) and
again in "Interpretation of Kidd Creek Pyrite Ages" (applying it). Per
LaTeX's normal (silent, no-error) behavior for duplicate labels, every
`\ref` to that label -- including the one in the *first* occurrence's
own paragraph -- was resolving to whichever instance compiled last,
which was quietly wrong. Fixed by renaming the second instance's label
to `fig:ch3-kiddcreek-he-age-vs-inclusion-size` and updating its
adjacent in-text `\ref`. Verified via full rebuild: zero "multiply
defined" warnings afterward (there had been exactly one before the fix).

Replaced the `\section{Conclusions}` placeholder
(`\todo{Summarize He retentivity findings and geochronologic
implications.}`) with a five-paragraph conclusion, in the voice and
citation density of Chapters 1 and 2's own Conclusions sections: (1) the
chapter's motivation and two-pronged approach (direct dating + step-heat
characterization); (2) the pyrite/arsenopyrite retentivity result and
where it sits on a diffusive-dose comparison against other
geochronometers; (3) the two apparent helium-loss pathways within
pyrite itself (short-circuit/pipe diffusion in deformed Rustenburg vs.
volume diffusion in undeformed Leadville); (4) the Kidd Creek and Gympie
age results and what they date (inclusion phases, not the sulfide
itself); (5) the practical takeaway (viable complement to Re-Os, but
locality-dependent) and a pointer to future work. All internal
`\S\ref{}`/`Fig.~\ref{}` targets and citation keys used were confirmed
to already exist elsewhere in the chapter before insertion -- no new
citations were introduced. Verified via full rebuild: zero undefined
references/citations, zero multiply-defined labels, zero overfull-hbox/
vbox warnings; visually confirmed on the compiled page.

Also compiled and delivered (in chat, not written into this file) a
list of everything still flagged `\todo{}`/`\hl{}` in the chapter's
Writing files, plus two numeric/wording inconsistencies noticed while
reading (an abstract-vs-body mismatch in the Gympie mean age, and a
likely "monzonite" -> "monazite" typo in the abstract) -- see chat for
the full list; nothing in it was acted on yet since it needs your input
(citations to add, values to confirm, etc.).

---

# 2026-09-01 -- Porting the hydrothermal-goethite manuscript into Chapters 1 and 2

Source of truth for this pass: `Manuscripts/HydrothermalGoethite/
hydrothermal_goethite_body.tex` (+ its abstract). **The manuscript and its
SI were not modified.** The manuscript's SI was deliberately not used as a
source, per instruction. Material present in the chapters but absent from
the manuscript was left untouched throughout; the operation was *replace
the chapter's version of a passage with the manuscript's revised version*,
never *import manuscript-only sections wholesale*.

Second half of the pass: the method-naming rebrand.

- "informed" method -> **permeation step method**
- "treatment as uncertainty" -> **bounding method**
- "naive" method is no longer a third method. In-experiment measurement of
  the ampoule's permeation rate constant lambda is now framed as a
  prerequisite/extension of the permeation step method (and, where the
  bounding method is used, as the empirical basis for a conservative
  lower-bound lambda).

Rename scope was extended to LaTeX labels, macro names, generated figure
filenames, generated cache filenames and the figure-generating scripts, per
your answer to the scope question.

---

## 1. Chapter 1 -- `Chapter1/Writing/chapter1_body.tex`

Only the permeation-lag theory (the manuscript's `\subsection{Quantifying
and Removing Permeation Lag}`, at the end of its Methods) was ported, as
specified. Chapter 1 already carried the permeation-step / bounding /
in-situ-rate-constant section structure from an earlier pass, so this was
prose refinement rather than restructuring. Eleven targeted replacements:

1. **Added Eq. `eq:carry`** (step-to-step continuity, `n_t^i = n_0^{i+1}`)
   plus the framing sentence that recovering omega needs the ampoule's
   content immediately before and after a step, pointing at the two routes.
   New equation; did not exist in the chapter before.
2. **Folded lambda into Eq. `eq:permsol`.** It now reads
   `^He F = m/n_0 = 1 - e^{-lambda t}, lambda = KGRT` instead of
   `1 - e^{-KGRTt}`. Added the manuscript's derivation sentence (integrate
   by separation of variables, then relate to `m` via `m(omega=0) = n_0 - n_t`)
   and its rationale for collecting K, G, R, T into lambda (lambda is what
   is measurable in-experiment; K and G are not separable without knowing
   the ampoule geometry).
3. **Steady-state assumption**: added the manuscript's explicit hold rule --
   hold at the permeation temperature for at least one diffusive timescale
   `tau = L^2/D` after every temperature change before measuring. The
   chapter's own supplement figure references were kept.
4. **Permeation step method closing paragraph** rewritten: literature
   permeabilities should not be relied on (water changes glass permeability;
   water-bearing ampoules run anomalously fast), so lambda is measured on
   the ampoule in use -- explicitly framed as *a prerequisite and extension
   of the permeation step method rather than an alternative to it*. This is
   the main place the retired "naive" method's content now lives.
5. **In-situ rate constant section**, five edits:
   - decay-equation sentence reworded now that lambda is defined earlier;
   - manuscript's rationale for fitting individual step yields rather than
     cumulative yields (cumulative fitting propagates early errors and
     biases the solver toward early measurements);
   - solver detail added: Levenberg-Marquardt in SciPy weighted by each
     measurement's own uncertainty, initial guesses
     `lambda ~ 6e-6 s^-1` and `n_0 ~ m_i/(1-e^{-lambda t_i})`,
     uncertainties from the fit covariance matrices (Excel Solver kept as
     an alternative);
   - added the caveat that the fit can technically be done with two
     consecutive measurements but then yields no parameter uncertainties;
   - closing recommendation restated: in-experiment lambda is *a routine
     part of the method*, not an optional refinement.
6. **Bounding method opening reframed.** Was: "Experimentalists may opt to
   treat permeation lag as uncertainty without applying corrections for
   convenience." Now: permeation steps need a measurable low-temperature
   signal; when the sample is retentive the signal falls to blank level and
   Eq. `eq:n0perm` cannot be applied, so the residual is bounded from above
   instead. This is the substantive change of framing you asked for -- the
   bounding method is a fallback for a real experimental limitation, not a
   shortcut.
7. **Bounding method conservatism** paragraph extended: Eq.
   `eq:steadystate` is conservative whenever the lambda used does not
   exceed the true one (a lower bound on lambda gives an upper bound on the
   residual), so any lambda demonstrably underestimating the true rate
   constant is admissible; closes with the explicit "excellent fallback"
   statement.

### Chapter 1 abstract -- `Chapter1/Writing/chapter1_abstract.tex`

One sentence pair added after the "experimental framework and key
equations" sentence, naming the two routes (*permeation step method*,
*bounding method*) and stating that both rest on an in-experiment
measurement of the rate constant. No other change; no numbers touched.

### Chapter 1 SI

Not modified. It contained no "naive"/"informed"/"treatment as uncertainty"
language to rebrand (that vocabulary had already been retired there), and
the manuscript SI was out of scope.

---

## 2. Chapter 2 -- `Chapter2/Writing/chapter2_body.tex`

### 2.1 Introduction

- Removed the `\todo{port language changes from manuscript...}` note, which
  this pass discharges.
- Paragraphs 1-2 replaced with the manuscript's wording (adds the
  `ansart2022` citation, already present in `references.bib`; folds the
  "decomposes to hematite in the very experiments used to characterize it"
  caveat into the framing sentence rather than leaving it a separate claim).
- The Farley (2024) decomposition paragraph replaced with the manuscript's
  version (`\citet` form, capacitance-manometry detail, "vacuum step-heat
  results need not describe helium behavior in nature"). The duplicated
  tail this created in the following chapter paragraph was removed.
- Added the manuscript's framing sentence to the closing introduction
  paragraph: dehydration is suppressed at high water pressure, so a
  hydrothermal step heat may interrogate helium loss rather than
  decomposition kinetics.
- Everything else in the introduction (Bassal molecular simulations, the
  MDD/crystallite-size discussion, Shuster & Vasconcelos two-domain
  results, the aggregate-size material) is chapter-only and untouched.

### 2.2 `\paragraph{Permeation Lag Correction}` -- rewritten

This section carried all three old method names and was the core of the
rebrand. It was rewritten end-to-end (7.0 kB -> 8.2 kB). Every experimental
detail was preserved: the <120 degC bracketing steps, the 10 series of 3-4
consecutive permeation steps at 90-110 degC for 120-180 min with 26 min
cooling, the excluded 11th series, the SciPy/Levenberg-Marquardt fit
weighted by measurement uncertainty, the initial guesses, the covariance
uncertainties, the `lambda t < 4` exclusions and the `eq:s6-8` route for
later steps, and the Swets/Jones permeability sourcing with G from the
measured diameters. What changed:

- "Naive Bracketing" -> the permeation step method could not be carried
  through for 4He because Eq. `eq:n0perm` cannot be applied to blank-level
  signals.
- "Treatment as Uncertainty" -> the bounding method, described as
  constraining the residual from above rather than measuring it.
- A new paragraph states that *both* routes require lambda, that lambda was
  measured in-experiment, and that this measurement is a prerequisite of
  the permeation step method and the empirical basis for choosing a
  conservative lambda for the bounding method -- not a separate method.
- Added, from the manuscript: the fitted rate constants span
  `\ChTwoPermLamMin`-`\ChTwoPermLamMax` s^-1 with 2-sigma uncertainties of
  0.08-0.46 log units and no trend against step duration; and the note that
  a lambda underestimating the true rate constant yields a conservative
  (higher) upper bound on the residual.
- Both figure captions rewritten: the fits caption gained the manuscript's
  "curvature is what conditions the fit" sentence; both had their bare
  "(Masaryk, 1968; Shelby, 1972)"-style prose citations converted to
  `\citep`/`\citet` against `references.bib`.

### 2.3 Results

- The 4He Arrhenius array description now follows the manuscript:
  **concave-down to about 5% cumulative 3He yield**, then roughly linear
  about one log unit below the 3He array. The chapter previously said
  concave-down "until a cumulative **4He** yield of ~0.1%". These are
  different claims, and I took the manuscript as the revised one --
  **worth a spot check.**
- Table lead-in and both distilled-dataset table captions: "treatment as
  uncertainty" -> "bounding method". Table data untouched.

### 2.4 Discussion

- **Ampoule permeability** (`internal-measurement-of-ampoule-apparent-
  permeability`): the activation energy now reads
  `\ChTwoPermEakJ +/- \ChTwoPermEaErrkJ kJ/mol` instead of
  `\ChTwoPermEa +/- \ChTwoPermEaErr cal/mol` -- the macro pair for kJ/mol
  already existed and the manuscript uses it. The manuscript's fuller
  mechanism was ported in: helium diffusivity in water vs. glass
  (7e-5 vs 2e-8 cm^2/s), the 3%/1% glass/water partitioning relative to the
  gas phase, and the generalized rate-constant relation
  `lambda_ampoule = lambda_empty (V_condensed + V_gas)/V_gas`, cross-
  referenced to Chapter 1's Eq. `eq:keff`. Also added the manuscript's
  point that the offset cannot be explained by cooling-period permeation.
- **Complete degas test** (`complete-degas-test`): method names updated;
  added the manuscript's statement that the bounding method's LB/central/UB
  reductions give Stage 1 activation energies of 157.1-160.6 kJ/mol and
  closure temperatures of 97.5-101.2 degC. The long analysis of the two
  anomalous complete-degas steps is chapter-only and untouched (it is more
  detailed than the manuscript's).
- **Retentivity** (`high-helium-retentivity-of-win-06-01b-ht`): "~8 log
  units lower" -> "approximately seven natural log units lower", matching
  the manuscript's consistent figure; the same change was made in the
  `fig:ch2-arrhenius-zoom` caption ("nearly 8 log units"). Added the
  Stage 2 reference-line closure temperature (~45 degC at 10 degC/Ma) to
  the body text, where it had previously appeared only in a figure caption.
- **4He/3He ratios** (`spectra-of-win-06-01b-ht`): ported the manuscript's
  interpretive paragraph -- the differing spectra imply the geometry of
  helium loss differs between hydrothermal and vacuum experiments, so
  vacuum 4He/3He spectra of goethite may not encode loss history the way
  they do for hematite or apatite -- together with its explicit caveat that
  this rests on 4He step yields of only 0.15-0.5 nccSTP and needs
  stronger-signal repeats.

### 2.5 Conclusions

The last two paragraphs were replaced with the manuscript's revised
closing: the linear 7-15% cumulative-yield array with its activation
energy, essentially quantitative retention at 25 degC over billion-year
timescales, the 4He requirement of natural loss, the 4He/3He loss-geometry
paragraph, and the alteration caveat (if dehydration or recrystallization
contributed, the diffusivities are upper bounds and the retentivity a lower
bound) folded together with the call for single-crystal hydrothermal work.

### 2.6 Chapter 2 abstract -- `Chapter2/Writing/chapter2_abstract.tex`

Added one sentence after the permeation-step bracketing sentence: 4He
permeation-step yields were at blank level, so permeation lag was removed
by the bounding method using the in-experiment rate constant, with the
permeation step method (3He only) reproducing the result. No numbers or
results claims changed.

### 2.7 Chapter 2 SI -- `Chapter2/Writing/chapter2goethite_SI_body.tex`

- `\section{Na"ive-Method Isothermal Permeability Dataset}` ->
  `\section{In-Experiment Permeation Rate Constant Dataset}` (and its
  `\markright`).
- `\subsection*{Na"ive-Method Step-Heat Dataset}` ->
  `\subsection*{Permeation Step Method Step-Heat Dataset}`, with its
  paragraph rewritten. It had previously described the main text's table as
  belonging to "the informed bracketing (``treatment as uncertainty'')
  method", which was self-contradictory under any naming; it now correctly
  says the main-text table is the bounding method's and this one is the
  permeation step method's.
- Step-heat table caption: "under the na"ive bracketing method" -> "under
  the permeation step method".
- `\todo{}` for the 4He blank corrections and the housekeeping comment
  about the removed 4He tables both updated to the new names.
- Two places describing the comparison figure's axes: "the bounding
  method's ``treatment as uncertainty'' spread" -> "lower- and
  upper-bound spread".
- Hyphenation normalized to "permeation step method" (was sometimes
  "permeation-step method").

---

## 3. Identifier, filename and macro renames

### LaTeX labels

| old | new |
| --- | --- |
| `fig:ch2-naive-cumulative-yield` | `fig:ch2-permeation-fits` |
| `fig:ch2-naive-arrhenius` | `fig:ch2-ampoule-permeability` |
| `tab:ch2-naive-isothermal-raw` | `tab:ch2-permeation-isothermal-raw` |
| `tab:ch2-naive-isothermal-fits` | `tab:ch2-permeation-isothermal-fits` |
| `tab:ch2-distilled-naive-3he` | `tab:ch2-distilled-permstep-3he` |
| `ch2-si-distilled-naive` | `ch2-si-distilled-permstep` |
| `fig:ch2-bracket-arrhenius-zoom` | `fig:ch2-permstep-arrhenius-zoom` |

### Macros

`\ChTwoNaiveRawTable` -> `\ChTwoPermStepRawTable`,
`\ChTwoNaiveFitTable` -> `\ChTwoPermStepFitTable`, and
`\ChTwoBracket{Ea,EaErr,Tc,TcErr,Rtwo,N}` ->
`\ChTwoPermStep{...}`.

### Files renamed

| old | new |
| --- | --- |
| `Chapter2/Writing/chapter2_naive_isothermal_tables.tex` | `chapter2_permstep_isothermal_tables.tex` |
| `Chapter2/Figures/fig_naive_isothermal_fits.py` | `fig_permstep_isothermal_fits.py` |
| `Chapter2/Figures/fig_naive_isothermal_fits_first2.py` | `fig_permstep_isothermal_fits_first2.py` |
| `Chapter2/Figures/fig_naive_stage1_arrhenius.py` | `fig_permstep_stage1_arrhenius.py` |
| `Chapter2/Figures/fig_diffusivity_naive_vs_bounding.py` | `fig_diffusivity_permstep_vs_bounding.py` |
| `generated/data/naive_lambda_arrhenius_cache.json` | `permstep_lambda_arrhenius_cache.json` |
| `generated/data/naive_lambda_arrhenius_cache_first2.json` | `permstep_lambda_arrhenius_cache_first2.json` |
| `NaiveIsothermalFits_Grid*.pdf` | `PermeationStepFits_Grid*.pdf` |
| `NaiveIsothermalFits_{120,150}min_byTemp*.pdf` | `PermeationStepFits_{120,150}min_byTemp*.pdf` |
| `NaiveLambda_Arrhenius*.pdf` | `AmpoulePermeability_Arrhenius*.pdf` |
| `Winsor_diffusivity_naive_vs_bounding.pdf` | `Winsor_diffusivity_permstep_vs_bounding.pdf` |
| `..._Arrhenius_Zoomin_naive.pdf` | `..._Arrhenius_Zoomin_permstep.pdf` |

The existing files under `Chapter2/Figures/generated/` were renamed on disk
as well, so the chapters build against the current artifacts without
rerunning the figure scripts.

### Figure titles / axis labels

User-visible strings in the plotting scripts were rebranded too: "Win-06-01b
Isothermal Step-Heat Naive Permeability Fits" -> "... Permeation Rate
Constant Fits"; "Naive Apparent Lambdas" -> "Apparent Permeation Rate
Constants"; "Naive $n_0$ Error (%)" -> "Fitted $n_0$ Error (%)"; "Naive
Fit" -> "Permeation Fit". Docstrings and stdout messages updated to match.

### Deliberately NOT renamed

- The workbook sheet names `diffusivitiesHTWin0601bNaive` and
  `DistilledNaiveMethod`. These are keys into your data file; renaming them
  in code without renaming the sheets would break the reduction.
- The internal JSON dict key `'naive'` in
  `stage1_regression_cache.json` and the Python locals `naive`/`naive_fit`
  that read it. Invisible in the dissertation, and renaming them requires
  regenerating the cache, which needs SciPy (not installed on the machine
  this ran on -- see "Verification" below). Easy follow-up if you want it.

---

## 4. Keeping the manuscript building without touching it

The manuscript still says `\ChTwoBracketEa` and still
`\includegraphics{NaiveLambda_Arrhenius.pdf}` etc., and it was not to be
edited. Two shims were added so a future `copy_manuscript_sources.py` sync
does not break it:

1. `Chapter2/Figures/write_chapter2_macros.py` now emits the legacy
   `\ChTwoBracket*` names as aliases of the new `\ChTwoPermStep*` ones. The
   same six aliases were appended to the current
   `Chapter2/Writing/chapter2_derived_values.tex` so it matches what the
   generator would now produce.
2. `Manuscripts/HydrothermalGoethite/copy_manuscript_sources.py` gained a
   `LEGACY_FIGURE_ALIASES` map, so each legacy figure basename the
   manuscript references resolves to its renamed source file and is copied
   into `Manuscripts/HydrothermalGoethite/figures/` under the old name. Its
   `EXTERNAL_TEX_INPUTS` entry was repointed at the renamed tables file.

**This is the one file outside Chapters 1 and 2 that was edited** -- it is
build tooling in the manuscript's directory, not manuscript prose, and
leaving it alone would have silently broken your next sync. Delete the
alias map (and the alias `\newcommand`s) whenever the manuscript itself is
renamed.

---

## 5. Verification

- **Reference/label/macro/figure integrity check** across every live `.tex`
  in the dissertation: zero undefined `\ref`/`\eqref`/`\nameref` targets,
  zero `\ChTwo*` macros used but undefined, zero `\includegraphics` targets
  missing from the graphics path.
- **LaTeX compile**: Chapter 1 body + abstract, Chapter 2 body + abstract +
  SI body + the generated tables file were compiled together in a stub
  wrapper. Clean run, PDF produced. The only errors were four
  `\nameref` calls (hyperref not loaded in the stub) and the expected
  unresolved references into Chapter 1's SI, which the stub did not input.
- **Python**: every script in `Chapter2/Figures/` byte-compiles, as does
  the patched `copy_manuscript_sources.py`.
- **Not verified**: a full `latexmk` build of `dissertation.tex`, and a
  rerun of the figure scripts. This machine's TeX install lacks `siunitx`,
  `biblatex` and `biber`, and its Python lacks SciPy. Please run
  `make figures-ch2 && make thesis` on your own machine once. Nothing in
  this pass changes any figure's data or geometry, only its filename and
  its title text, so a rerun should be cosmetic.

### One thing I broke and put back

While attempting the full build I ran `latexmk` in the repo root, which
overwrote the tracked `dissertation.pdf`. I restored it from `HEAD`
(`git show HEAD:dissertation.pdf`), so it is byte-identical to the
committed version again. If you were carrying an uncommitted newer build
of that PDF, it is gone and needs a rebuild -- the `.tex` sources were
never at risk. Untracked/ignored build artifacts in the root
(`dissertation.aux`, `.log`, `.fls`, `.idx`, `.toc`) were also overwritten
and will be regenerated on your next build.

---

## 6. Manuscript passages considered and deliberately not ported

Flagged rather than acted on, since each would have *added* manuscript-only
material to a chapter rather than replacing chapter text:

- The manuscript's "Encapsulation stabilizes reactive phases" discussion,
  in particular its comparison against the Harrison (1982, 1985)
  hydrothermal step-heat approach (one aliquot per measurement, requires a
  priori noble gas concentration) and the argument that this method's
  advantage is many isothermal measurements on a single aliquot. There is
  no corresponding passage in either chapter for it to replace. It reads
  most naturally as a Chapter 1 Discussion addition -- say the word.
- The manuscript's generalization of Chapter 1's Eq. `eq:keff` from
  `K_eff = K_dry (V_water + V_gas)/V_gas` to
  `lambda_ampoule = lambda_empty (V_condensed + V_gas)/V_gas` -- i.e. from
  water specifically to any condensed payload, and from a permeability to a
  rate constant. Chapter 2 now cites the generalized form, but Chapter 1's
  own equation was left as-is, since it sits in Chapter 1's Discussion and
  you scoped Chapter 1 to the permeation-lag theory only.
- The manuscript's ampoule-preparation section gives numeric geometric
  factors G (2390 cm^-2 for the Durango ampoule, 6980 cm^-2 for the
  goethite ampoule). Chapter 2 states G is computed from the measured
  diameters but never gives the value. Adding it would be an addition, not
  a replacement.
- The manuscript's Results paragraph on the ratio spectra ("at any given
  cumulative 3He yield the hydrothermal experiment records lower
  bulk-normalized ratios ... its approach toward a plateau is the slowest
  of the three") duplicates material already in Chapter 2's Discussion, so
  it was not also inserted into Chapter 2's Results.

## 7. Judgment calls worth a spot check

1. The 4He Arrhenius concave-down changeover (5% cumulative 3He vs. 0.1%
   cumulative 4He) -- see 2.3. I took the manuscript as authoritative.
2. The seven-vs-eight log unit change in Chapter 2's retentivity section
   and the `fig:ch2-arrhenius-zoom` caption.
3. The 157.1-160.6 kJ/mol / 97.5-101.2 degC Stage 1 range added to
   `complete-degas-test` is quoted from the manuscript; Chapter 2's own
   macros only carry the central value, so it is a hard-coded number in the
   chapter now.
4. `fig:ch2-arrhenius-zoom`'s caption still says the 4He array sits a log
   unit below the 3He array "after a cumulative fractional yield of 14%
   3He", while the body (per the manuscript) now says 5%. I left the
   caption's figure alone since it may describe something narrower, but the
   two now read inconsistently.
5. Pre-existing and unrelated, noticed by the integrity checker:
   `ChapterA/chapterA.tex` defines ten labels twice each (`app:bushveld`,
   `sec:appA-intro`, `sec:appA-litreview`, `sec:appA-methods`,
   `sec:appA-observations`, `sec:appA-discussion`, `sec:appA-conclusions`,
   `sec:appA-datatable`, `sec:appA-fieldmap`, `sec:appA-photos`). Not
   touched by this pass.

## Follow-up: marcasite SEM images added to "Effectiveness of the Ampoule Method"

`Chapter3/Writing/HeInSulfides_Main_Body.tex`, subsection "Effectiveness
of the Ampoule Method in Stabilizing Sulfides"
(`ch3-sem-imaging-tube-buffered-sulfides`): added a new figure,
`fig:ch3-marcasite-grid`, a four-panel SEM grid (Control / Unbuffered /
Vacuum / Buffered) built from the four marcasite images in
`Chapter3/Figures/source/` (`Marc_control_10um5.pdf`,
`marc_open_400_5Hr_10um05.pdf`, `Marc_Vac_400C_4_5hr_2um2.pdf`,
`Marc_buff_600_8Hr_10um09.pdf`), styled after Chapter 1's own
`fig:mineral-grid`. Treatment temperatures/durations in the caption are
taken from each file's own naming (400C/5hr open, 400C/4.5hr vacuum,
600C/8hr buffered), which do not exactly match the general 400C/8-11hr
description in the Chapter 1 SI's methods text (\S1.6s) -- these appear
to be a separate, marcasite-specific run; please confirm the caption's
stated conditions are correct.

Replaced all four `\hl{}` placeholders in this subsection's paragraph
with real cross-references: two point to the new marcasite grid
(the open-air/vacuum/buffered marcasite observations), and two point to
Chapter 1's `fig:mineral-grid` (the pyrite/arsenopyrite unbuffered and
buffered observations, which were already illustrated there and needed
no new figure). Verified via full rebuild: zero undefined refs/
citations, zero multiply-defined labels, and the new figure introduces
no new overfull-hbox/vbox warnings (identical warning set to the prior
build). Visually confirmed on the compiled page -- the four-panel grid
renders cleanly on its own page, fits within the text width, and each
panel is legible.

## Follow-up: marcasite grid to 2x2, larger Ch3 in-plot text, arrows removed from Gogebic plot

Three requests handled together:

**Marcasite grid (Fig. 3.9) 1x4 -> 2x2**: `Chapter3/Writing/HeInSulfides_Main_Body.tex`.
Same four images, rearranged into a 2-row x 2-column table (Control/
Unbuffered top, Vacuum/Buffered bottom) at 0.42\textwidth per panel
(up from 0.22\textwidth) -- each image is now about 4x the printed
area. Verified via full rebuild: no new overfull-hbox/vbox warnings
(the figure still fits on one page), visually confirmed the panels are
noticeably larger and each SEM texture is easier to make out.

**Larger in-plot text, Chapter 3 only**: `Chapter3/Figures/plot_style.py`
(the shared matplotlib style, normally kept byte-identical across
Chapter1/2/3 -- this copy now deliberately diverges, noted in its own
docstring/comments so it isn't accidentally copied back into the other
chapters) -- TITLE_SIZE 16->20, LABEL_SIZE 14->17, TICK_SIZE 12->15,
SUPTITLE_SIZE 16->20; LEGEND_SIZE left at 11 (reported as already fine).
Also bumped the SI step-heat grid's own separate font dict
(`fig_ch3_stepheat_si_grid.py`, which doesn't use plot_style.py):
label 9->11, tick 7.5->9.5, rowlabel 8.5->10.5; its legend size (6)
also left alone. Regenerated every Chapter 3 figure this affects via
`run_all_figures.py` (had to `pip install --user scipy molmass tqdm`
on the device first -- those were missing, unrelated to this change).

One figure could NOT be regenerated: `fig_cumulative_diffusive_time.py`
(produces Fig. 3.10, the diffusive-dose/Fo comparison plot) fails with
`ValueError: Worksheet named 'DistilledUncertaintyTreatment' not found`
reading `Chapter2/Tables/Win0601bHT_data_and_reduction.xlsx` -- that
workbook's actual sheets are `DistilledBoundingMethod` and
`DistilledPermeationMethod`, so this looks like a stale sheet-name
reference in `thermochr_utils.py`'s `low_signal_HTWin0601b_mask()`
left over from a workbook rename, predating this session. This is a
data-pipeline bug, not a styling one, so I did not attempt a fix --
Fig. 3.10 still has the old, smaller in-plot text until this is
resolved. Separately, `fig_pyrite_diffusivity.py` also fails (missing
`Batch 56.csv`), but its outputs (`double_natural_pyrite.pdf`,
`MDDPlot.pdf`) aren't referenced anywhere in Chapter 3's Writing files,
so this one appears to be dead/orphaned and was left alone.

Also, while running a from-scratch clean rebuild (`latexmk -C`) to
verify the above, found another genuinely undefined citation, unrelated
to any of this session's edits: `\citep{smith1993,hannington1999}` at
`HeInSulfides_Main_Body.tex` line ~1270 (Kidd Creek metamorphic-history
discussion) -- `smith1993` has no entry in `references.bib` and no
close-match key exists to infer a typo fix from (unlike the earlier
lee1992/lee1993 case), so this is left for you to supply the correct
citation or remove it.

**Gogebic hematite plot (Fig. 3.3) arrows removed**:
`Chapter3/Figures/fig_gogebic_hematite_eu.py`. Removed the two
"process-direction" annotation arrows and their labels ("U-loss",
"Incomplete dissolution") that pointed away from the main aliquot
cluster. Kept the small arrow/label identifying the 041323MG16b
outlier point, since that one identifies a specific plotted point
rather than making an interpretive claim, and the U-loss interpretation
of MG16b is still made in the caption/body text. Flagged to the user
in chat in case "remove the arrows" was meant to include the MG16b
pointer too.

Verified via a full from-scratch clean rebuild (`latexmk -C` then
rebuild): zero multiply-defined labels, zero new overfull-hbox/vbox
warnings (identical set to before, aside from the one pre-existing
smith1993 citation above), page count unchanged at 224. Visually
confirmed the marcasite grid, the Gogebic plot, and the (unregenerated,
for contrast) Fo comparison plot all render as expected.

## Follow-up: Fig. 3.10 data fix, lee1992/lee1993 citation correction

**Fig. 3.10 fixed**: `Chapter3/Figures/thermochr_utils.py`,
`low_signal_HTWin0601b_mask()` -- changed the sheet name it reads from
`Chapter2/Tables/Win0601bHT_data_and_reduction.xlsx` from
`DistilledUncertaintyTreatment` (no longer exists) to
`DistilledBoundingMethod` (confirmed: same 35-row shape, same column
order, `3He Measured (pccSTP)` still at the same position) at the
user's confirmation that this is the sheet's new name. Regenerated
Fig. 3.10 -- it now has the same larger in-plot text as the rest of
Chapter 3. Only `Chapter3/Figures/thermochr_utils.py` was touched;
`Chapter2/Figures/thermochr_utils.py` still references the old sheet
name and was left alone (out of scope -- flagged to the user in chat
in case Chapter 2 has the same latent bug).

While regenerating, the figure's title (a hardcoded 2-line
`ax.set_title(...)` call in `fig_cumulative_diffusive_time.py`) turned
out to overflow its axes and collide with the y-axis label at the
larger TITLE_SIZE from the previous follow-up -- its second line
("Hematite, Goethite, Zircon, and Monazite with Diffusive Time") was
much longer than the first. Rewrapped it into 3 more evenly balanced
lines; caught via visual inspection of the rendered page, confirmed
fixed the same way.

**lee1992 vs. lee1993 citation correction**: the user clarified that
`lee1992` (Lee \& Aldama, 1992, "Multipath diffusion: A general
numerical model", *Computers \& Geosciences*) is a real paper they
intentionally cite for the pipe/short-circuit diffusion mechanism, and
that both `lee1992` and `smith1993` were added to `references.bib`
themselves after this conversation started -- which is why both were
flagged as undefined in the last two follow-ups (my earlier "fix" of
the main-text occurrence from `lee1992` to `lee1993`, back before this
session's conclusion-writing work, was wrong; it had already been
reverted, apparently by the user's own edit, since the main-text
occurrence at line 1046 already read `lee1992` when checked this turn).
Corrected the one remaining wrong occurrence: the Conclusions
paragraph I wrote this session cited `\citep{lee1993}` for this same
short-circuit/pipe-diffusion point (copying what I mistakenly believed
was the corrected key at the time) -- changed to `\citep{lee1992}` to
match the main text and the actual paper being invoked. `lee1993`
remains correctly used elsewhere (Chapter 1, general noble-gas
degassing-mechanism citations) -- untouched.

Verified via a full from-scratch clean rebuild (`latexmk -C` then
rebuild): zero undefined references or citations (including `lee1992`,
`lee1993`, and `smith1993`, all now resolving), zero multiply-defined
labels, zero overfull-vbox warnings, identical overfull-hbox set to
before, page count unchanged at 224. Visually confirmed Fig. 3.10's
data and new title render correctly.

---

# 2026-09-01b -- Chapter 2 SEM images combined into 1x2 grids

Follow-on to the port above. The six standalone SEM figures in Chapter 2's
`\paragraph{Goethite Dehydration and/or Recrystallization...}` section were
combined into three 1x2 grid figures, in the order they already appeared,
matching the house style of `fig:mineral-grid` (Chapter 1) and
`fig:ch3-marcasite-grid` (Chapter 3): a `tabular` inside a single `figure`,
bold panel headers above each image, `\setlength{\tabcolsep}{4pt}`, one
merged caption, one label. No `subcaption`/`subfigure` -- neither reference
figure uses it.

All six source PDFs are 245.76 x 184.32 pt (identical 4:3), so panels at
`width=0.46\textwidth` come out the same height with no cropping or
rescaling. **No image files were modified, regenerated or replaced.**

## The three grids

| new figure | label | panels (left, right) |
| --- | --- | --- |
| 1 | `fig:ch2-sem-control-vacuum` | `bahiaGoeControl_20um4.pdf` ("Control"), `Goethite_Vac_300C_11hr_10umB0.pdf` ("Vacuum, 300 degC, 11 h") |
| 2 | `fig:ch2-sem-buffered` | `bahiaGoeGypsum300C8hr_10um8.pdf` ("Gypsum-buffered, 300 degC, 8 h"), `Goeth_Water_300C_4hr_10um6.pdf` ("Water-buffered, 300 degC, 4 h") |
| 3 | `fig:ch2-sem-vacuum-interior` | `Goethite_Vacuum_300C_11hr_10u9.pdf` ("Vacuum, 300 degC, 11 h (SE)"), `C5_goeth_Vac205.pdf` ("Vacuum, cross section (BSE)") |

Pairing is strictly the order the images already appeared in, which happens
to group sensibly: untreated vs. dehydrated; the two buffered treatments
side by side; and the vacuum decomposition texture next to the cross
section proving those cracks are pervasive through the interior.

## Labels

The six old labels (`fig:ch2-sem-control`, `-vacuum`, `-gypsum`, `-water`,
`-zoom-decomp`, `-backscatter`) are **retired**, not kept as hidden
duplicates -- the house-style grids carry one label each, and keeping six
labels pointing at three figure numbers would render as "Fig. 2.20 and
Fig. 2.20". Every reference was repointed:

- Results, SEM paragraph: cracks in vacuum/open air now cite
  `Figs.~\ref{fig:ch2-sem-control-vacuum},~\ref{fig:ch2-sem-vacuum-interior}`;
  the no-cracks-when-buffered clause cites `\ref{fig:ch2-sem-buffered}`.
- MDD-consistency paragraph and the dehydration/recrystallization
  paragraph: both collapsed to the range
  `Figs.~\ref{fig:ch2-sem-control-vacuum}--\ref{fig:ch2-sem-vacuum-interior}`.
- Caption-internal cross-references were rewritten to name panels rather
  than former figure numbers (e.g. "most of the aggregate's surface
  resembled the gypsum-buffered panel", "from the same subsample as the
  vacuum-heated grain of Fig.~\ref{fig:ch2-sem-control-vacuum}").

## Captions

All six original captions were merged into three with no loss of content --
every observation survives, including the gypsum-dehydrates-first
mechanism, the higher-temperature goethite/gypsum reaction product, the
"roughest texture on the grain" qualifier, the inherited-crack caveat about
the control, the same-scale note tying grid 3's left panel to grid 2, and
the pervasive-interior-cracks conclusion.

## Verification

- Reference/label/macro/figure integrity check across every live `.tex`:
  zero undefined refs, zero orphaned labels, zero missing graphics.
- Compiled and visually inspected the three rendered pages: panels align,
  headers sit correctly above each image, captions set cleanly, and the
  `Figs. X--Y` ranges resolve. Zero overfull/underfull boxes in the grid
  figures themselves.
- Proof PNGs were moved to `_to_delete/` (`sem-49/50/51.png`) rather than
  left in the tree; delete that folder at your convenience.

---

# 2026-09-03 -- Chapter 1 figure grids; removed the stray dashed lines at zero

Source-only change to `Chapter1/Figures/*.py`. **No figure was regenerated
for the dissertation** (one script was run once as a smoke test -- see
Verification), and no data, axis limits, colors, labels or captions were
touched. Regenerate with `make figures-ch1` when convenient.

## What the "dashed lines at 0" actually were

They were not deliberate reference lines. They are the output of the shared
`make_grid()` helper (defined in both `diffusion_utils.py` and
`thermochr_utils.py`), which was supposed to draw dashed gridlines at every
major tick:

```python
x_coords = [xt.get_position()[0] for xt in ax.get_xticklabels()[1:-1]]
y_coords = [yt.get_position()[1] for yt in ax.get_yticklabels()[1:-1]]
plt.vlines(x_coords, *ylim, linestyle='--', color='Black', alpha=0.2)
plt.hlines(y_coords, *xlim, linestyle='--', color='Black', alpha=0.2)
```

Under the matplotlib these figures were built with, tick-label
`get_position()` returns `(0, 0)` before the figure is drawn, so both
coordinate lists collapse to all-zeros and the helper draws exactly **one**
dashed line per axis, at zero, instead of a grid. That is why the artifact
shows up only where zero falls inside the axis range:

| figure | visible artifact |
| --- | --- |
| `UncertEstLongStep` | dashed line at y=0 *and* at x=0 |
| `EQM_Timescales_Permeation` | dashed line at y=0 (x=0 off-range) |
| `Helium_Partitioning`, `PercentHeInGlass` | dashed line at x=0 (y=0 off-range) |
| `Thermal_Perturbation_Error`, `ChangingYieldH2Otube` | none visible (both zeros off-range) |
| `VRvsRtau` | none (log axes); only the faint alpha=0.05 minor lines drew |

So the two requests turn out to be the same fix: the plots showing a dashed
line at zero are exactly the plots that never got a grid. Replacing the
helper call with a real grid does both.

## Changes

**`make_grid()` -> `ax.grid(True)`** (8 call sites, 8 figures):
`ChangingYieldH2Otube`, `Helium_Partitioning`, `Thermal_Perturbation_Error`,
`PercentHeInGlass`, `VRvsRtau`, `EQM_timescales`,
`EQM_Timescales_Permeation`, `UncertEstLongStep`. The now-unused
`make_grid` import was dropped from all five affected scripts
(`fig_changing_yield_h2o_tube.py` no longer imports `thermochr_utils` at
all). `make_grid()` itself was left untouched in `diffusion_utils.py` and
`thermochr_utils.py` -- those files are duplicated into Chapters 2 and 3
and fixing the helper there would silently restyle their figures too.

**Grid added where there was none** (12 figures):
`Diffusion_Tube_Simulation1.0` (Fig1.py), the SI blank-permeation plots
(`generated/Blanks/*He_*.pdf`), `encapsulated_DApErr`,
`FDM_diff_prof_zero_IC`, `FDM_diff_prof_300C_IC`, `glass_solubility`,
`PermeabilityMeasurements`, `Rayleigh_Distillation`,
`Kinetic3He4HePermeability`, `EQNtest`, `LagPlot`, `FirstOrderDecay`.
On the twin-axis figures (`ax2 = ax1.twiny()`) the grid goes on `ax1`,
matching what `fig_relative_permeabilities.py` already did.

**Lines at zero removed**: the red dotted `ax.hlines(0, 0, 7, linestyle=':')`
in `FirstOrderDecay` -- the one hand-drawn zero line that was not a
`make_grid()` artifact.

**Histograms** (`Histograms4He`, `Histograms3He`): these had a hand-rolled
grid -- dashed `axvline`s at -20/-10/10/20/30/40 -- rather than a real one.
Replaced with `ax.grid(True)` plus `ax.set_axisbelow(True)`, which is needed
because the bars carry an explicit `zorder=2` and matplotlib's default
`axes.axisbelow: line` would otherwise draw the grid *over* them. The thick
solid black `axvline(0)` marking zero error was kept -- it is a deliberate
marker, not a dashed artifact.

## Deliberately not changed

- `PredictingPermeation_error_vs_fraction`: `ax.axhline(0, color='black')`
  -- solid, not dashed, and a meaningful zero-error reference. Left in
  place; say the word if you want the grid to carry it instead.
- `DurangoStepYields_RelativeAnomaly`: `axhline(1)` (no-anomaly baseline)
  and `Relative_Permeabilities`: dashed line at ratio 1. Both are at 1, not
  0, and both are real references.
- `Rayleigh_Distillation`: the dashed `axhline(IR)` is a labeled data
  series.
- `goethite_thermal_sims.py`: a `pcolormesh` error map whose white
  `which='minor'` grid delineates cells. A major grid over an image would
  be wrong, and its output is not a Chapter 1 figure.
- `VRvsRtau` is log-log. `ax.grid(True)` gives major gridlines only, so it
  loses the faint minor lines `make_grid()` happened to draw there (the one
  thing that helper did do correctly). Add `which='both'` if you want them
  back.

## Verification

- Every `Chapter1/Figures/*.py` byte-compiles, and no reference to
  `make_grid` remains in any Chapter 1 figure script.
- Axes-vs-grid audit: every figure-producing axes in Chapter 1 now has
  exactly one grid call.
- `fig_changing_yield_h2o_tube.py` was actually run (it was the only edited
  script whose imports no longer require SciPy, which is not installed on
  the machine this ran on) and its output inspected: the grid renders in the
  house style, the stray line is gone, the data is unchanged. Its
  `generated/ChangingYieldH2Otube.pdf` is therefore newer than the rest --
  harmless, since `generated/` is untracked and you will rebuild anyway.
- The other scripts could not be executed here (no SciPy). The edits are
  one-line grid calls and import removals, but a `make figures-ch1` on your
  machine is the real check.


---

# 2026-09-03 -- Kidd Creek reinterpreted as pyrite+arsenopyrite (not all pyrite); Gympie relabeled arsenopyrite

Prompted by your observation that most/all of the Gympie suite and much of
the Kidd Creek suite is probably arsenopyrite or As-rich pyrite rather than
pure pyrite. Grounded this in the trace-element data already in
`Chapter3/Tables/geochronology_compilation_BJT.xlsx` (`KiddCreekDistilled`
and `GympieDistilled` sheets, `As (ppm)` column) before touching any prose:

- Of the 12 dated Kidd Creek aliquots, 11 form the coherent
  age-vs-Th/He array discussed throughout the chapter. Seven of those 11
  have measured As of ~1,600-410,000 ppm -- clearly arsenopyrite, not
  pyrite; the other four (an earlier "2211" prep batch) have no As
  measurement but the same age/Th-He systematics, so are treated as part
  of the same population.
- The 12th, oldest aliquot (`011123KCPyST05C`, 1596 +/- 46 Ma) has As =
  49 ppm -- by far the lowest in the suite, and consistent with the
  "golden pyrite cube" aliquots picked out by eye during sample
  preparation. This is the one aliquot now interpreted as genuine pyrite.
- Two Gympie aliquots (`230625GyPyUnAbr`, `230628GyPyHClab`) have As
  1-2 orders of magnitude above the rest of the Gympie suite; flagged in
  the text as unreliable rather than taken at face value.

Note: a literal `0` (not blank/`None`) in this workbook's As column is
this early KiddCreek batch's convention for "not measured", confirmed by
direct cell inspection -- `fig_geochronology_ages.py`'s loader now treats
0 the same as a blank cell for this field.

## Text changes

- `Chapter3/Writing/HeInSulfides_Main_Body.tex`: 15 mechanical renames
  (Gympie "pyrite" -> "arsenopyrite" throughout, including both Results
  subsection titles; Kidd Creek "pyrite" -> "pyrite/arsenopyrite" in
  intro/methods mentions). Full rewrite of the
  "Interpretation of Kidd Creek Pyrite/Arsenopyrite Ages" discussion
  section (`ch3-discussion-kiddcreek-ages`): reframes the 11-aliquot
  arsenopyrite array and the 12th aliquot as low-As pyrite rather than an
  outlier, ties the ~1.6 Ga closed-system prediction at the observed
  ~30 um inclusion size to the pyrite date, adds the golden-pyrite-cube
  and Gympie-As-reliability caveats, and the "only one pyrite date, not
  proof, but internally consistent" qualifier, citing the step-heat
  retentivity comparison (`fig:ch3-sulfide-arrhenius-compilation`,
  `fig:ch3-fo-comparison`). Both figure captions
  (`fig:ch3-he-age-vs-inclusion-size`, `fig:ch3-kiddcreek-age-th-he`)
  rewritten to match the new figure content (below). Conclusions
  paragraph rewritten to state the same reinterpretation: Kidd Creek
  arsenopyrite requires open-system He loss, the single pyrite aliquot is
  consistent with closed-system behavior.
- `Chapter3/Writing/HeInSulfides_abstract.tex`: "gympie sulfides" ->
  "Gympie arsenopyrite"; mean age corrected 253 +/- 21 Ma -> 258 +/- 35 Ma
  (matches the body's actual computed mean -- these didn't agree before);
  fixed a stray "the the country rock" typo; replaced the Kidd Creek
  closed/open-system sentence with the new framing (arsenopyrite lost He,
  the one low-As pyrite aliquot is closed-system).
- `Chapter3/Writing/HeInSulfides_SI_body.tex`: one rename, "Gympie pyrite
  suite" -> "Gympie arsenopyrite suite".

## Figure changes

- `Chapter3/Figures/fig_geochronology_ages.py`
  (`KiddCreek_Age_vs_Th_and_He.pdf`, `fig:ch3-kiddcreek-age-th-he`):
  `_load_distilled_sheet()` now also reads `As (ppm)` (with the 0=not-
  measured handling above). `plot_kidd_creek_th_he()` now colors each
  point by log10(As) via a shared colorbar instead of one flat color;
  aliquots with no As measurement plot grey with a legend entry. The
  lowest-As (oldest, pyrite) point renders clearly as the darkest-colored
  outlier at the top of both panels.
- `Chapter3/Figures/fig_alpha_stopping_distances.py`
  (`He_Age_vs_Apatite_Inclusion_Size.pdf`,
  `fig:ch3-he-age-vs-inclusion-size`): the reference band label changed
  from "(Arseno)pyrite U-Th/He ages" to "Arsenopyrite". The shared
  0-30 um teal band (`_add_observed_inclusion_band`, still used as-is by
  the unrelated, unreferenced `plot_sulfide_fraction`/
  `Fraction_Sulfide_Hosted_He_vs_Apatite_Inclusion_Size.pdf`) was
  replaced, only within `plot_helium_age()`, by a single vertical line at
  the observed 30 um inclusion half-width. Added a "Pyrite" point with a
  2-sigma error bar at (R=30 um, age=1596+/-46 Ma) -- it lands right at
  the model curve's crossing of that line, which is the "elegant"
  intersection you were expecting.

Both figures regenerated and visually checked (rendered pages, not just
console output).

## Judgment calls (flagged, not agonized over)

- Left the individual SEM figure captions (`fig:ch3-kcpy-groundmass`,
  `fig:ch3-kcpy-aspy`, `fig:ch3-kcpy-apatites`, `fig:ch3-gympie-
  inclusions`) saying "pyrite" unchanged -- these describe specific
  photographed grains, and grain-level mineral identity isn't something
  the bulk trace-element data can confirm or deny for that particular
  imaged material.
- Left the generic, literature-sourced "Gold-bearing pyrite-quartz
  mineralization at Gympie occurs..." deposit-description sentence
  unchanged -- that's describing the deposit type in the literature, not
  making a claim about the specific analyzed aliquots.

## Verification

Full clean rebuild (`latexmk -C` then rebuild): 225 pages, zero errors,
zero multiply-defined labels, zero new overfull-hbox warnings (none fall
within any of the edited passages). One undefined citation,
`\citep{hurley1941}` (Main Body line ~1399, in the Gympie Carboniferous-
age paragraph) -- this is unrelated to this change, from your own
concurrent edit to that section; `hurley1941` has no entry in
`references.bib`. Flagged for you to supply or remove, same as prior
undefined-citation entries in this journal.


---

# 2026-09-04 -- Walked back the As-based pyrite/arsenopyrite split for Kidd Creek

Follow-on correction to the 2026-09-03 entry above, per your feedback: the
As-content, mass-balance, and optical-habit lines of evidence used there to
argue that most Kidd Creek aliquots are arsenopyrite and one is pyrite don't
actually agree with each other closely enough to support that split. Backed
this off specifically for Kidd Creek (the Gympie "arsenopyrite" renaming
from the prior entry stands -- you didn't ask to revisit that one).

## Text changes

`Chapter3/Writing/HeInSulfides_Main_Body.tex`, Kidd Creek interpretation
section (`ch3-discussion-kiddcreek-ages`): added a new paragraph explaining
how pyrite vs. arsenopyrite was meant to be told apart here -- optical habit
during sample picking, direct As measurement
(Table `tab:ch3-main-geochron-trace`), and an independent mass-balance
estimate of arsenopyrite content from each aliquot's pre-digestion weighed
mass vs. its ICP-measured Fe content under a two-phase pyrite-arsenopyrite
mixing constraint ($N_{py}MM_{py} + N_{AsPy}MM_{AsPy} = $ measured mass) --
and states that these three lines of evidence don't agree with each other for
either suite. Cites that measured As is generally far below the
~460,000 ppm expected for stoichiometric FeAsS (only 1 of 8 As-measured
Kidd Creek aliquots comes close). Conclusion: individual Kidd Creek
aliquots can't be reliably split into pyrite vs. arsenopyrite, so the
"11 arsenopyrite + 1 pyrite" framing from the prior entry is dropped in
favor of treating the whole suite as pyrite/arsenopyrite together.

The rest of the section (the age array, the two-component mixing model, the
30 um / 1.6 Ga closed-system prediction) is kept, since that data pattern is
independent of mineral identity, but every place that previously said
"arsenopyrite-dominated aliquots" now reads "the eleven-aliquot array" or
similar. The paragraph on 011123KCPyST05C is rewritten to no longer claim it
is confirmed pyrite: its old age matching the closed-system prediction is
now explicitly presented as one of two equally-plausible readings --
genuine near-total closed-system retention, or an anomalously old age from
incomplete acid digestion (a known failure mode already discussed elsewhere
in this chapter for the Gogebic hematite outlier) -- without preferring
either. The step-heat pyrite-more-retentive-than-arsenopyrite argument is
kept but explicitly hedged as only relevant "if" this aliquot is confirmed
pyrite, which it can't be.

Cascaded the same correction to `HeInSulfides_abstract.tex` and the
Conclusions paragraph in `HeInSulfides_Main_Body.tex`, since both restated
the "eleven arsenopyrite / one pyrite" framing.

## Figure changes

- `Chapter3/Figures/fig_geochronology_ages.py`
  (`KiddCreek_Age_vs_Th_and_He.pdf`, `fig:ch3-kiddcreek-age-th-he`):
  reverted `plot_kidd_creek_th_he()` to a single flat color (no more
  log(As) colorbar/grey-for-unmeasured coloring from the prior entry).
- `Chapter3/Figures/fig_alpha_stopping_distances.py`
  (`He_Age_vs_Apatite_Inclusion_Size.pdf`,
  `fig:ch3-he-age-vs-inclusion-size`): removed the "Arsenopyrite"-labeled
  reference band and the single "Pyrite" point. In their place,
  `plot_helium_age()` now imports `_load_distilled_sheet` from
  `fig_geochronology_ages.py` and plots all twelve measured Kidd Creek
  dates (with their 2-sigma error bars) at the observed 30 um inclusion
  half-width, all in one color/marker -- no mineral-based distinction.
  Eleven cluster well below the model's closed-system curve; the twelfth
  sits right on it. Nudged the "Observed inclusion half-width" text label
  up out of the new point cluster so it doesn't overlap the markers.

Both figures regenerated and visually checked.

## Verification

Full clean rebuild (`latexmk -C` then rebuild, including a fresh
`references.bib` sync -- the previous `hurley1941` undefined-citation flag
was just a stale `.bbl` on my end, not a real gap; it now resolves):
225 pages, zero errors, zero undefined references/citations, zero
multiply-defined labels, identical overfull-hbox set to the prior entry
(48, none in the edited passages).


---

# 2026-09-07 -- Chapter 3 proofreading pass (grammar, spelling, typos, consistency)

Full proofreading pass over all of Chapter 3's prose (`HeInSulfides_Main_Body.tex`,
`HeInSulfides_abstract.tex`, `HeInSulfides_SI_body.tex`, and the table captions
in `chapter3_geochron_tables.tex`), at your request. About 100 fixes applied;
verified with a full clean rebuild (225 pages, zero errors, zero undefined
refs/citations, same 48-overfull-hbox baseline). Grouped below rather than
listed file-by-file/line-by-line.

## Spelling and typos fixed
mathmatically/mathmatical -> mathematically/mathematical; additionaly ->
additional; delievered -> delivered; montiored -> monitored; abundaces ->
abundances; acivation -> activation (and pluralized to "activation energies"
to fix the subject-verb agreement it was tangled up in); aginst -> against;
assymetric -> asymmetric; cumlative -> cumulative; incorperated ->
incorporated; interogated -> interrogated; retentively -> retentivity;
reexisting -> pre-existing; realtively -> relatively; arsonpyrite ->
arsenopyrite; Leavldville -> Leadville; Compliment -> Complement (section
heading -- wrong word, not a typo of spelling); monzonite-structure ->
monazite-structure (abstract -- monzonite is an igneous rock, not the
phosphate mineral structure meant here); Rustenberg -> Rustenburg
(3 places, including one table header that had it flagged "(?)" -- this
is consistently "Rustenburg" everywhere else in the chapter); U/Ph -> U/Pb;
orU-Th -> or U-Th (missing space).

## Grammar
Several subject-verb agreement fixes ("Pyrite and arsenopyrite ... was
collected" -> "were collected"; "the precise timing and mechanism ... is
not fully understood" -> "are"; "Radiogenic helium evolution ... show" ->
"shows"; "there exists many copper-bearing sulfide phases" -> "exist";
"the data ... was consistent" -> "were", matching this document's own
"these data are/do not" convention elsewhere; "differences ... is
discussed" -> "are"; "the identity, size distribution, and digestion
behavior ... is a property" -> "are properties" / "differs" -> "differ").
Fixed a doubled/garbled phrase ("single-jump mechanistic single-jumps" ->
"single-jump mechanisms"), a dangling clause missing "which" before
"leaves the diffusion/migration physics... undercharacterized", a
duplicated "which for which" (Bushveld sentence), a sentence with no verb
("this aliquot's contained U-Th-Sm rich inclusions near or on surface of
the sulfide grains" -> "...U-Th-Sm-rich inclusions sat near or on the
surface..."), a "Step heat data step heat experiments" duplication (SI),
and a handful of missing/misplaced commas, plus one stray sentence-initial
lowercase "the" after a period.

## Consistency
- Capitalized "Gympie" where it had lowercased mid-sentence (6 places,
  careful to leave the `\label`/`\ref` identifiers like
  `fig:ch3-gympie-...` alone, since those are case-sensitive).
- Capitalized "Arrhenius" where lowercased in running prose (4 places;
  again left the `arrhenius` inside figure label/ref identifiers alone).
- "Re/Os" and "Rb/Sr" -> "Re-Os"/"Rb-Sr" to match this chapter's
  established hyphenated convention (used ~80 times elsewhere).
- "atmospheric-corrected" -> "atmospherically corrected" (1 outlier vs.
  4 correct uses); "isotope-dilution quantified" ->
  "isotope-dilution-quantified" to match the fully-hyphenated form used
  elsewhere; "early permian"/"carboniferous" -> "Early Permian"/
  "Carboniferous" (formal period names, capitalized everywhere else);
  "Gympie block" -> "Gympie Block" (2 of 3 uses already capitalized).
- Fixed three sample-name typos in the Leadville grain-size subsection
  where the third experiment was twice called "112123LVCOPy" (dropping
  the "Irr" suffix used everywhere else) and the big-grain experiment was
  once called plain "LVCOPy230707" instead of "BigLVCOPy230707" -- as
  written these would have read as a fourth, nonexistent sample.
- "section \ref{...}" -> "\S\ref{...}" and "Sec.~\ref{...}" -> "\S\ref{...}"
  (3 places) to match the "\S\ref" convention used ~50 other times;
  likewise added a missing "\S" to three bare "\ref{sem-imaging-of...}"
  cross-references, and a missing "Table~" before one bare
  "(\ref{tab:ch3-step-heat-tubes})".
- Normalized a few other doubled/inconsistent hyphenations
  ("short circuit" -> "short-circuit", "multiple domain volume diffusion"
  -> "multiple-domain volume diffusion", "high vacuum, high temperature"
  -> "high-vacuum, high-temperature", "U-Th bearing" -> "U-Th-bearing").
- Raw "±" characters -> "$\pm$" (LaTeX macro, matching the ~100 other
  uses) in two places.
- Expanded the document's one contraction ("don't" -> "do not") to match
  the formal register used everywhere else.
- \subsubsection*{Sphalerite} (was: unlabeled \emph{Sphalerite}, the only
  one of three parallel Results subheadings in the SI not using
  \subsubsection*).

## Corrected an inverted causal claim
"an anomalously old U-Th/He age is also the expected signature of
incomplete acid digestion, which would leave some U-Th-Sm-bearing residue
undissolved, **underestimating** the apparent age" -- undissolved
U-Th-Sm residue means the measured parent-isotope budget is too *low*,
which makes the calculated age too *old* (overestimated), not
underestimated. Changed "underestimating" -> "overestimating" so the
sentence supports the point it's making (that incomplete digestion is a
plausible explanation for an anomalously *old* date).

## Flagged, not changed -- please take a look
A few things a proofread can catch but shouldn't silently "fix" because
they're substantive, not typos:
1. **Cumulative fractional yield ceiling stated three different ways.**
   The same claim ("no pyrite or arsenopyrite step heat experiment
   exceeded X% cumulative fractional yield") appears with three different
   numbers: 6% in Results (§3.3), 7% in Discussion §3.4.1, 5% in the
   Conclusions. I don't have the raw yield totals to know which is right.
2. **Abstract's Kidd Creek paragraph doesn't match the Discussion/
   Conclusions.** The abstract still frames the old aliquot's age as
   confirmed evidence of "a perfectly retentive 2.7 Ga sulfide host" with
   no hedge, while the Discussion and Conclusions both now present that
   as one of two equally-plausible readings (genuine retention vs.
   incomplete digestion). The abstract also cites the reference apatite
   cooling age as "~370 Ma" where the Discussion/Conclusions use
   "392 ± 32 Ma" throughout -- worth reconciling both the number and the
   framing.
3. **`\hl{Tube Photo}` placeholder still in the SI text** (Chalcopyrite/
   Chalcocite results, right before "Although permeation lag..." -- I
   only added the missing period before it, not touched the placeholder
   itself).


---

# 2026-09-25 -- Integrating the goethite thermodynamic/kinetic analysis into Chapter 2 and the GCA manuscript

Source: `Chapter2/Writing/ch2_goethite_stability_sections.tex` (standalone draft of
goethite stability, dehydroxylation kinetics and the controls on 3He release). The chapter gets
the full treatment; the manuscript gets a condensed main-text version with details in the SI.
Existing text was edited only where needed for consistency or to avoid redundancy; every such
edit is listed below. A pre-change snapshot is the git commit "Before integrating Goethite
thermodynamics" (35caf37).

Rules applied to numbers: auto-generated macros (`\ChTwo*`) take priority, then values already
in the paper, then values from the new draft.

## 1. Figure scripts (Chapter2/Figures)

- Renamed so `run_all_figures.py` (glob `fig_*.py`) picks them up:
  `goethite_hematite_phase_diagram.py` -> `fig_goethite_hematite_phase_diagram.py`,
  `goethite_vacuum_kinetics.py` -> `fig_goethite_vacuum_kinetics.py`,
  `goethite_hydrothermal_tests.py` -> `fig_goethite_hydrothermal_tests.py`
  (git mv for the two tracked ones). The `importlib` paths between them were updated.
  `goethite_thermal_sims.py` (a simulation script, deliberately excluded from the runner) was
  NOT renamed.
- **Hydrothermal data now use the bounding method throughout.** `load_ht()` in
  `fig_goethite_vacuum_kinetics.py` previously used the raw measured cumulative 3He. It now reads
  the bounding-method table (`data/Win0601bHT_distilled.csv`): cumulative F bounded by
  [Sigma, Sigma + n_t,UB], central = midpoint; ln(D/a^2) LB/central/UB straight from the table;
  steps without bounds or with measured 3He < 0.1 pccSTP excluded (same rule as every other
  Ch. 2 plot). New helper `ht_lnk_bounds()` gives first-order ln k bounds.
  The hydrothermal points in `arrhenius_reaction_vs_diffusion` and `first_order_delta_lnk` now
  carry bounding-method error bars and exclude low-signal steps.
- `fig_goethite_hydrothermal_tests.py` rewritten on the bounding method:
  - Test 1 (history dependence) now reports offsets from a line through the first prograde sweep
    (fitted separately to LB/central/UB) and a conservative offset (step UB minus LB line), plus
    retrograde-vs-prograde agreement in the last cycle.
  - Test 2 (250 C holds) calibrates diffusion on the mean LB/central/UB ln(D/a^2) of the three
    5 h steps, and the constant-rate reaction on the bounded release over the 15 h window
    [dSigma - n_t,UB(before), dSigma + n_t,UB(end)] (dSigma includes intervening permeation-step
    yields -- the same convention as the table's ln(D/a^2)).
  - Writes `generated/data/hydrothermal_tests_summary.json`.
- Vacuum dataset label "HM" -> "HDM" in plot labels/legends (matches existing figure names such
  as `...VacuumHDMKAF`); internal key renamed likewise.
- All three scripts were run; new outputs in `generated/`: `goethite_hematite_Ph2o_T_hydrated`,
  `size_basis_sensitivity`, `arrhenius_reaction_vs_diffusion`, `vacuum_kinetics_KAF_to_HM`
  (+ `_fits.csv`), `first_order_delta_lnk`, `hydrothermal_translation`,
  `hydrothermal_diffusion_vs_conversion`, `synthetic_degeneracy_test.csv` (plus the older
  phase-diagram outputs the script also writes).
- Note: scipy and CoolProp were installed into the Cowork VM to run them; make sure they are in
  your Windows conda env before `make figures`.

### Resulting number changes vs. the draft (bounding method)
| Quantity | Draft | Now |
|---|---|---|
| Test 1, first-cycle drop | 1.3--1.6 ln units at 200/210 C (low-signal steps) | 0.45 / 0.86 at 225 / 215 C retrograde (>= 0.18 / 0.47 at bounds); 220 C re-visit 0.58 (>= 0.32); low-signal steps 1.3--2.1 lower |
| Test 1, last cycle | 0.06--0.45 | 0.07--0.45, bounds overlap |
| Final-segment Ea | 157 +/- 3 | `\ChTwoEa` +/- `\ChTwoEaErr` (Stage 1 regression macro) |
| Test 2, F0 / observed F | 0.0872 / 0.1460 | 0.0872--0.0877 / 0.1460--0.1463 |
| Test 2, diffusion | 0.1482 | 0.148 (0.139--0.158) |
| Test 2, constant-rate reaction | 0.1672 (+36%) | 0.170--0.180 (+39--60% in long-step release) |
| HT vs vacuum line (reaction rep.) | up to 2.8 orders, median 2.3; retro 2--4 ln below | 1.3--2.8, median 2.4; retro 0.7--1.5 ln below |
| HT residuals vs wet prediction | 30--101 (0.16); 20--68 (0.14); 53--169 (0.19) | 30--62; 20--41; 53--105 |
| Total 3He released | 14.8% | 14.7% (value already in paper) |
| Observed apparent alpha | 0.148/0.888 = 0.17 | 0.147/0.888 = 0.17 |

Vacuum-only numbers (Ea 121.4 +/- 4.4, phi 0.112, gamma_eff, etc.) are unchanged and were
re-verified by re-running the scripts.

## 2. references.bib (root)
Added `majzlan2003a`, `berman1985`, `voigt1981`, `wagner2002`, `bell2014`, `mampel1940`.
Draft keys mapped to existing ones: `majzlan2003b` -> `majzlan2003`, `fechtig1966` ->
`fechtigkalbitzer1966`. **`voigt1981` has a placeholder title "TODO: verify title"** -- I could
not verify it online. `robie1995` was not added (it was only in a TODO comment).

## 3. Chapter 2 (`Chapter2/Writing/`)

### chapter2_body.tex -- new material
- Analytical Methods, before "SEM Study...": new `\paragraph{Thermodynamic Model of Goethite
  Dehydroxylation}` (`sec:gt_thermo_methods`; Eqs. gt_rxn ... gt_dmu_shift, Table
  `tab:gt_thermo_data`) and `\paragraph{Kinetic Analysis of Vacuum Step Heats}`
  (`sec:gt_kinetics_methods`; KAF = Farley et al. 2024, HDM = Monteiro et al. 2017; Eqs.
  gt_F1 ... gt_FK; states that the hydrothermal data use the bounding method).
- Analytical Methods, after "SEM Study...": new `\paragraph{Hydrothermal Treatment of Synthetic
  Goethite Pigment}` (`sec:gt_pigment_methods`) -- explicitly qualitative, per your description
  (>= 5 large ampoules, excess water, fused at ambient pressure, manually regulated oven,
  200--250 C, ~1 day). TODOs: pigment product/grade; SEM instrument/prep for these images.
- Discussion, inserted immediately before "Goethite Dehydration and/or Recrystallization...":
  `sec:gt_thermo` (P-T figure, driving-force table), `sec:gt_vacuum` (vacuum = conversion; links
  phi plateau / conversion to Farley 2024's Stage 3 / Stage 2; keeps the 4He/3He whole-grain
  paragraph), `sec:gt_hydro` (Tests 1 and 2 on the bounding method, Table `tab:gt_hold`),
  `sec:gt_nucleation` (nucleation barrier, gamma_eff calibration, translation to saturation,
  residuals, assumptions).
- Discussion, inserted immediately before "High Helium Retentivity...": `sec:gt_pigment` with
  the new two-panel figure `fig:gt_pigment` (subfigures `goe_pig_treatedRed19.pdf`,
  `goe_pig_treatedYellow37.pdf`) and the nucleation-limited / all-or-nothing interpretation.
- Heading levels demoted to the chapter's `\paragraph` style; inner run-in headings became
  italic lead-ins. Labels keep the draft's `gt_` prefix. `Eq.~\ref` -> `Eq.~\eqref`,
  `Section~\ref` -> `\S\ref`, figures/tables given `[htbp]`.
- Layout-only changes vs. the draft: Cp integrals, FK, nucleation-rate and residual equations
  split over two lines; thermo-data table restructured (one Cp coefficient per row, notes in a
  minipage) -- all to remove overfull boxes.

### chapter2_body.tex -- edits to existing text
1. Introduction, end of last paragraph: +1 sentence pointing to the new analysis.
2. Fig. `ch2-arrhenius-full` caption: removed "A diffusive domain corresponding to the Stage 2
   reference line would have a closure temperature of about 45 C..." (your decision).
3. Fig. `ch2-arrhenius-zoom` caption: "the last 11 measurements" -> "the last `\ChTwoN`"
   (macro = 12; macro-priority rule).
4. "Consistency with MDD Systematics": +1 sentence forward reference to the new sections.
5. "Goethite Dehydration and/or Recrystallization": added "(\S\ref{sec:gt_thermo})" after the
   majzlan2003 citation; replaced the "Dehydration processes may be responsible for some or all
   ... even if dehydration completely controls ..." passage with a statement that the kinetic
   analysis shows solid-state dehydration contributed negligibly, keeping the conditional
   upper-bound sentence.
6. "High Helium Retentivity": removed the two Stage 2 / 45 C closure-temperature sentences.
7. Fig. `ch2-fourier-win0601b` caption: "Whether or not the frequency factor ... is unclear."
   -> "We interpret this Stage 2 process as first-order conversion of goethite to hematite
   rather than volume diffusion (\S\ref{sec:gt_vacuum})."
8. 4He/3He section: +1 sentence linking the interpretation to \S gt_vacuum--gt_hydro.
9. Conclusions, last paragraph: "we cannot exclude the possibility that subtle dehydration or
   recrystallization occurred..." replaced by a summary of the new result, keeping fluid-mediated
   conversion and recrystallization as open possibilities and the upper-bound sentence.

### Other Chapter 2 files
- `chapter2_abstract.tex`: +1 sentence summarizing the thermodynamic/nucleation result.
- `chapter2goethite_SI_body.tex`: appended three SI sections from the draft's supplement
  (`sec:gt_supp_mech`, `sec:gt_supp_basis`, `sec:gt_supp_barrier`), HM -> HDM; mechanism-forms
  table wrapped in `\resizebox`.
- `chapter2goethite.tex` (standalone wrapper): `\usepackage{subcaption}` for the pigment figure.
- `ch2_goethite_stability_sections.tex`: header note only (superseded; kept for reference).

## 4. GCA manuscript (`Manuscripts/HydrothermalGoethite/`)
Legacy method names in the manuscript were left untouched.
- `hydrothermal_goethite_body.tex`:
  - New `\subsection{Thermodynamic and kinetic analysis of goethite dehydroxylation}`
    (`sec:methods-kinetics`) after the SEM methods subsection (condensed; Eqs. gt_rxn, gt_F1,
    gt_stepk).
  - New `\subsection{Hydrothermal helium release is diffusive, not dehydroxylation}`
    (`sec:discussion-conversion`) before "Dehydration and recrystallization"; two figures
    (`fig:gt_arrhenius`, `fig:gt_hydro_tests`), Eqs. gt_line, gt_barrier, gt_translate; one
    paragraph on the pigment result (details and SEM figure in SI).
  - Edits to existing text: "Dehydration or recrystallization could therefore contribute ... and
    neither can be excluded" -> solid-state dehydration too slow (ref), subtle dehydration /
    recrystallization / fluid-mediated conversion not excluded; removed the Stage 2 / 45 C
    closure-temperature sentences; +1 clause in the 4He/3He paragraph; Conclusions last
    paragraph rewritten as in the chapter.
- `hydrothermal_goethite_abstract.tex`: +2 sentences on the vacuum reanalysis / nucleation result.
- `hydrothermal_goethite_SI_body.tex`: appended five sections (thermodynamic model incl.
  surface-area basis; vacuum kinetics incl. mechanism tests; hydrothermal tests with the hold
  table; nucleation model incl. barrier ratio and residuals; synthetic pigment methods + the
  two-panel SEM figure). SI-only labels use a `gtsi_` prefix so they cannot collide with the
  main-text labels that `xr` imports.
- `main_xrefs.tex`: +7 macros (`\MainRefMethodsGoethite`, `\MainRefMethodsSEM`,
  `\MainRefMethodsKinetics`, `\MainRefDiscussionMDD`, `\MainRefDiscussionConversion`,
  `\MainFigGtArrhenius`, `\MainFigGtHydroTests`).
- `hydrothermal_goethite_GCA_SI.tex`: header comment updated with the new main-text dependencies.
- `copy_manuscript_sources.py` needed no change; re-run it (done once) to pick up the new
  figures and bib entries.

## 5. Verification
- Full `dissertation.tex` build (latexmk/biber): 0 errors; the only undefined reference is the
  pre-existing `app:bushveld`; no new overfull boxes (one fewer than before). 222 -> 244 pages.
- `hydrothermal_goethite_GCA.tex` and `_GCA_SI.tex` (bibtex): 0 errors, 0 undefined references.
  The SI's "Citation multiply defined" natbib warnings come from `xr` importing the main text's
  citations and were already present.
- Standalone `chapter2goethite(.tex/_SI.tex)`: build; their undefined cross-chapter references
  are of the same kind as before.
- Pages with the new tables, the pigment figure and the hold-test table were rendered and checked.

## 6. Open items for you
- `voigt1981` title (placeholder in references.bib).
- Hematite Maier--Kelley coefficient source (TODO comment kept).
- Manometer day-boundary artifact (TODO kept: confirm with the line operator).
- Pigment product data sheet; SEM instrument/prep for the pigment images.
- The red product is identified as hematite by color and habit only (no XRD); the text says so.
- In the manuscript the pigment SEM figure is in the SI (to keep the main text brief); move it
  to the main text if you prefer.


---

# 2026-09-25b -- Merged the revised goethite stability draft into Chapter 2

Source: the revised `Chapter2/Writing/ch2_goethite_stability_sections.tex` (same file now on
disk). Its changes relative to the draft integrated earlier today were merged into
`chapter2_body.tex` and `chapter2goethite_SI_body.tex`. The draft's numbers still come from the
raw (not permeation-lag-corrected) hydrothermal data, so wherever the draft and the chapter
disagreed on a hydrothermal number, the chapter's bounding-method value (or macro) was kept or
recomputed. The GCA manuscript was not touched.

## Figure scripts (Chapter2/Figures)
The three `fig_goethite_*.py` files on disk had been replaced by copies from outside the repo:
old import names (`goethite_*.py`), data paths without `data/`, the "HM" labels, and none of the
bounding-method changes -- as written they would not have run. Fixes:
- `fig_goethite_vacuum_kinetics.py`: re-applied the `data/` paths, the `fig_` import name, the
  HDM labels, the bounding-method `load_ht()` / `ht_lnk_bounds()`, and the bounding-method
  hydrothermal points in `arrhenius_reaction_vs_diffusion` and `first_order_delta_lnk`.
- `fig_goethite_hydrothermal_tests.py`: kept the draft's new `hold_projection()` (each model
  calibrated on the three 5 h steps and projected through the 170.8 h step), now with a `col`
  argument for the central / lower-bound / upper-bound series. New single-panel figure
  `hydrothermal_hold_projection.pdf` (Chapter 2, `fig:gt_hold`) with bounds bars and bands. The
  earlier two-panel `hydrothermal_diffusion_vs_conversion.pdf` (constant-rate test) is still
  produced because the GCA manuscript uses it. `history_test()` (Test 1 numbers) retained.
- `fig_goethite_hematite_phase_diagram.py`: unchanged (identical to the committed version).
- All re-run; the figure outputs were refreshed and `generated/data/hydrothermal_tests_summary.json` was updated.

## chapter2_body.tex
- Thermodynamic methods (`sec:gt_thermo_methods`): replaced with the draft's revised text --
  derivation of the apparent Gibbs energy, the new water paragraph with Eq. `eq:gt_Gw`, the
  expanded surface-energy derivation (factor-of-two explanation), and the phase-diagram method
  (Brent on log P, 1e-12--1e4 bar, truncation at ice). The ideal-vapor boundary approximation and
  `eq:gt_dmu_shift` were removed, as in the draft. The 10 nm surface-term example moved here from the
  Discussion, as in the draft. Kept your manual edit `\Delta\mu \equiv -\Delta G_r^{0}` (the
  draft writes `-\Delta G_r`).
- Discussion `sec:gt_thermo`: removed the 10 nm example (now in Methods) and the
  RT ln(Psat/P) = 96.1 kJ example; the Table `tab:gt_dmu` text follows the draft.
- `sec:gt_vacuum`: +fitting-window independence (Ea = 122.7 with all steps) and the Goss (1987)
  TG comparison (TODO comment kept).
- Test 1: kept the bounding-method numbers and the `\ChTwoEa` macro; adopted the draft's wording
  (first-order conversion has no memory) and figure pointers (Fig. gt_arrhenius a/b).
- Test 2: replaced with the draft's first-order-vs-diffusion projection, recomputed on the
  bounding method: F0 = 0.0795 (0.0793--0.0798); diffusion 0.149 (0.148--0.150) vs observed
  0.146 (0.1460--0.1463); first-order 0.173 (0.172--0.174), a 46% (44--47%) overprediction;
  R2/R3/A2/A3 0.174--0.212. (Draft, raw data: 0.148, 0.172, 44%, 0.174--0.209.)
  `tab:gt_hold` and `fig:gt_hydro_tests` removed; new `fig:gt_hold`.
- `sec:gt_nucleation`: replaced with the draft's revised text (CNT citations, the
  transition-state upper bound `eq:gt_ceiling`, the Young/Volmer argument against free-surface
  nucleation, the topotactic-mechanism paragraph, the enumerated driving-force definitions, the
  9 kBT detectability bound, four assumptions). Kept the bounding-method numbers: residuals
  30--62 / 20--41 / 53--105 orders (draft 30--101 / 20--68 / 53--169) and alpha = 0.147/0.888.
  Equation line-splits re-applied.

## chapter2goethite_SI_body.tex
- Mechanism section: +the all-steps refit paragraph.
- Barrier section: +"Sensitivity to surface terms" paragraph and Table `tab:gt_surf_sens`.

## references.bib
+18 entries: berman1988, helgeson1978, anderson2005, gibbs1878, volmer1926, becker1935,
turnbull1950, eyring1935, christian2002, kashchiev2000, deyoreo2003, lasaga1998, porter2009,
limadefaria1963, watari1979, watari1983, cudennec2005, saito2016. Saito, Watari 1979/1983 and
Lima-de-Faria were checked against the publisher pages; the Lima-de-Faria end page (203) and the
rest are from standard citations -- worth a glance.

## Verification
Full dissertation build: 0 errors; only undefined reference is the pre-existing `app:bushveld`;
no new overfull boxes; 249 pages. `fig_goethite_hydrothermal_tests.py` also runs on the local VM.

## Still open / for you
- The GCA manuscript still uses the earlier constant-rate Test 2 and the earlier nucleation text.
- Numbers in the draft file itself (`ch2_goethite_stability_sections.tex`) remain the raw-data
  values; the chapter is authoritative.
- New draft numbers not re-derived here (vacuum-only or thermodynamic, independent of the
  permeation-lag correction): Ea = 122.7 for all-step fits, the TST ceiling of 63 kBT, the 9 kBT
  detectability bound, and Table `tab:gt_surf_sens`. They are taken from the draft as written.


---

# 2026-09-25c -- GCA manuscript brought up to date with the revised goethite analysis

Same content decisions as 2026-09-25b (bounding-method numbers throughout; the chapter is the
source). Legacy method names in the manuscript untouched.

## hydrothermal_goethite_body.tex (main text, kept condensed)
- `sec:methods-kinetics`: now says Delta G_r is evaluated in the apparent Gibbs energy
  convention (`berman1988`); Delta mu defined as `-\Delta G_r^{0}` to match your Chapter 2 edit.
- `sec:discussion-conversion`:
  - Thermodynamics paragraph: +role of water (partial pressure, not total pressure; ~46 J
    mechanical term at 40 bar; mass action on the bulk reaction).
  - Vacuum paragraph: +cumulative-fit Ea within the window (122.9) and with all steps (122.7).
  - Hydrothermal paragraph: Test 1 now points to Fig. `gt_arrhenius`b and uses the first-order
    "no memory" wording; Test 2 is now the first-order-vs-diffusion projection (diffusion 0.149,
    0.148--0.150; first-order 0.173, 0.172--0.174, 44--47% overprediction; observed
    0.1460--0.1463). The two-panel figure `fig:gt_hydro_tests` was replaced by `fig:gt_hold`
    (`hydrothermal_hold_projection.pdf`), same figure as the chapter.
  - Nucleation paragraph: +transition-state upper bound on the vacuum barrier (<= 63 kBT),
    free-surface nucleation fails it even with zero interfacial energy (>~2e2 kBT), internal
    topotactic nucleation (limadefaria1963, watari1979, watari1983, cudennec2005),
    gamma_eff within the coherent/semicoherent range (porter2009, saito2016), barriers
    0.5--1.3 vs 52--129 kBT against the ~9 kBT needed for 1% conversion, and the surface-term
    sensitivity (alpha ~1e-23 even at 10 nm).
- Abstract and Conclusions unchanged (still accurate).

## hydrothermal_goethite_SI_body.tex
The five goethite SI sections were regenerated from the current Chapter 2 text (same assembly as
before: `gtsi_` labels, main-text references through `main_xrefs.tex`, the main-text figures
`fig:gt_arrhenius` and `fig:gt_hold` not duplicated). They now include everything merged into
the chapter in 2026-09-25b: revised thermodynamic derivation, fitting-window note and Goss
comparison, the projection form of Test 2, the revised nucleation section, the all-steps refit
paragraph, and the surface-term sensitivity table.

## main_xrefs.tex / hydrothermal_goethite_GCA_SI.tex
`\MainFigGtHydroTests` replaced by `\MainFigGtHold` (fig:gt_hold); SI header comment updated.

## Chapter2/Figures/fig_goethite_hydrothermal_tests.py
Removed the now-unused two-panel constant-rate figure (`make_figure`,
`hold_test_constant_rate`); the old `hydrothermal_diffusion_vs_conversion.*` outputs (generated/
and the manuscript's figures/) were moved to `_to_delete/old_figures/`. Re-run.
`copy_manuscript_sources.py` re-run (88 cited entries).

## Verification
Main text and SI (bibtex) compile with 0 errors and 0 undefined references; main 58 pp., SI
37 pp. No new overfull boxes of note (one 11.9 pt line in the SI, text only). The
dissertation is unaffected by this pass.

---

# 2026-09-28 -- Ch. 2 delta plot and 4/3He plot redrawn as step spectra

**Figures** (`Chapter2/Figures/fig_delta_plot.py`, `fig_3_4_plot.py`; regenerated
`DeltasWinsorGTzoomin_VacuumHydrothermal{,_asUncertainty}.pdf` and
`Comparative_Ratios_Dtplot_WinsorGT_VacuumHDMKAF.pdf`). Points replaced with
spectrum-style bars: each step spans x from the cumulative fractional 3He yield at
the start of the step (end of the previous step; 0 for the first) to the yield at
the end of the step. Hydrothermal steps are boxes spanning the step's uncertainty
(delta plot: +/-(UB-LB)/2, or LB/UB in the `_asUncertainty` variant; ratio plot:
LB-UB) with a line at the central value. Vacuum steps (no uncertainties) are flat
segments at the step's value; in the delta plot 3He is solid and 4He dotted.
Step spans are computed from the full step series before low-signal/no-bound steps
are dropped, so dropped steps leave gaps. Hydrothermal colours in the delta plot
are now blue (3He) and green (4He); legends use proxy handles; the ratio-plot
legend is pinned to lower right.

**Hydrothermal x-positions changed slightly.** The old delta plot placed points at
the M sheet's `FiUB` column (cumulative yield + upper-bound gas still in the tube);
the bars now use `Fi` (Sigma 3He / total 3He), matching the vacuum `Fcum`
convention. The old ratio plot read the distilled sheet's `F 3He` column, which is
actually each step's *starting* yield (Fi of the previous step), so its points
lagged one step; the bars now run start->end.

**Stale sheet name fixed in Chapter 2** (the latent bug flagged in the Ch. 3
follow-up): `Chapter2/Figures/thermochr_utils.py` `low_signal_HTWin0601b_mask()`
and `fig_3_4_plot.py` now read `DistilledBoundingMethod` (formerly
`DistilledUncertaintyTreatment`). The new sheet also has fewer columns, so
`fig_3_4_plot.py` now reads the ratio columns by header name instead of position
(the old positions 23-26 no longer exist). Added helpers `step_yield_edges()` and
`step_yield_edges_HTWin0601b()` to `thermochr_utils.py`. Neither figure could
be regenerated before this fix, so the previous PDFs (6 Aug) predated the 26 Aug
workbook; the hydrothermal values differ from those PDFs for that reason too.
`fig_nt_vs_ntss_comparison.py` still reads the old sheet name (not touched).

**Captions** (`Chapter2/Writing/chapter2_body.tex`, `fig:ch2-delta-zoom`,
`fig:ch2-ratio-spectra`): one sentence each describing the bar representation;
the ratio caption's "shaded envelope" wording replaced.

**Not verified by compile:** the device's TeX install lacks `siunitx`, so
`pdflatex dissertation.tex` stopped in the preamble. That aborted run truncated
`dissertation.aux`/`.out` (regenerated on the next latexmk build);
`dissertation.pdf` was restored from a copy taken beforehand.

## Follow-up: step connectors and a two-scale x axis on the 4/3He plot

- Both plots: fine vertical lines (0.6 pt, series colour) now join each step's
  central value to the next step's, at the x where one ends and the next begins.
  Only contiguous steps are joined; gaps left by dropped steps stay open. New
  helper `draw_step_connectors()` in `Chapter2/Figures/thermochr_utils.py`.
- `fig_3_4_plot.py`: x axis is now piecewise-linear (matplotlib `function` scale):
  Sigma F3He 0-0.2 fills the left 2/3 of the axes and 0.2-1.0 the right 1/3, with
  a double-slash break mark on the top and bottom spines at 0.2. Steps that cross
  0.2 stay continuous. Break position and fraction are `X_BREAK` / `ZOOM_FRAC` at
  the top of the plotting section. Title padded slightly to clear the top mark.
- Captions for `fig:ch2-delta-zoom` and `fig:ch2-ratio-spectra` now mention the
  connectors; the ratio caption also describes the scale change.

## Follow-up: 4/3He plot -- error boxes removed, interior gap bridged

- `fig_3_4_plot.py`: hydrothermal LB-UB error boxes removed (Ken's request); the
  hydrothermal series is now the central (M) ratio only, drawn at the same 2.2 pt
  weight as the vacuum series, with a line legend entry. Step selection is
  unchanged (same 10 of 34 steps excluded).
- Interior gaps left by excluded steps (here the single gap at Sigma F3He
  ~0.040-0.042 from the dropped low-signal retrograde steps) are bridged for
  display only: first half of the gap at the preceding step's ratio, second half at
  the following step's (`bridge_interior_gaps()` in `fig_3_4_plot.py`). The
  leading gap before the first plotted step is left open. The delta plot is
  unchanged (still has its error boxes and open gap).
- `fig:ch2-ratio-spectra` caption: bounds wording replaced with "drawn at the
  bounding method's central 4/3He ratio", plus one sentence disclosing the
  display-only gap bridging.

## Follow-up: delta plot gap bridged (error boxes kept)

- `fig_delta_plot.py` (both variants): the interior hydrothermal gap is bridged the
  same way as the 4/3He plot (first half at the preceding step's central delta,
  second half at the following step's), for both 3He and 4He. Error boxes are
  unchanged and drawn only over real steps -- none over the bridge.
- `bridge_interior_gaps()` moved from `fig_3_4_plot.py` into
  `Chapter2/Figures/thermochr_utils.py` so both scripts share it; the 4/3He
  figure regenerates identically.
- `fig:ch2-delta-zoom` caption: one sentence disclosing the display-only bridge
  and that no uncertainty is shown over it.

---

# 2026-09-29 -- Chapter 2 kinetic-fit statistics now come from macros; D3 refit with phi

## New auto-generated file
`Chapter2/Writing/chapter2_kinetics_values.tex` (59 `\ChTwoKin*` macros), written by
`write_kinetics_macros()` in `Chapter2/Figures/fig_goethite_vacuum_kinetics.py` together with
`Figures/generated/data/goethite_kinetics_cache.json`. It covers the cumulative F1 fit (Ea, ln A,
phi, s, rms, n), the joint and per-experiment Arrhenius lines through the step rate
constants, k at 250 C and conversion per hour, the TST ceiling (63 kBT) and 1% detectability
bound (9 kBT), trap-isolated rate factors, the residual rms values, the water fit, the all-steps refits,
the D3 variants, and the full row sets of SI Tables `tab:gt_mech_fits` and `tab:gt_synth`
(`\ChTwoKinMechFitRows`, `\ChTwoKinSynthRows`). It is `\input` in `Chapter2/chapter2.tex`,
`Writing/chapter2goethite.tex` and `Writing/chapter2goethite_SI.tex`. Do not edit it by hand.

## Script changes (fig_goethite_vacuum_kinetics.py)
- `fit_model()` takes `phi=<value>` (fixed) or `phi_free=True`; the default behavior is unchanged.
- `run()` now also fits D3 with phi fixed at the F1 value (0.112) and with phi free, on the
  same 19 KAF / 21 HDM steps, and repeats every fit with all steps (columns `*_all`), which
  reproduces the previously hand-typed all-steps numbers exactly.
- New `residual_stats()` and `write_kinetics_macros()`; called from `__main__`.

## Result: D3 with the same phi
| Model | Ea (kJ/mol) | rms KAF | rms HDM prediction |
|---|---|---|---|
| F1 | 122.9 | 0.0085 | 0.0167 |
| R3 | 101.7 | 0.0111 | 0.0234 |
| R2 | 90.3 | 0.0133 | 0.0292 |
| D3, phi = phi(F1) = 0.112 | 245.6 | 0.0237 | 0.0539 |
| D3, phi free (0.155) | 267.6 | 0.0199 | 0.0541 |
| D3, phi = 0 | 183.7 | 0.0455 | 0.0529 |
Imposing the plateau improves the KAF misfit for D3 but not its prediction of HDM, and it still ranks
below F1, R3 and R2 (above A2/A3). Its trap-isolated rate factor is s = 0.69.

## Text changes
- `chapter2_body.tex`: all hard-coded kinetic-fit numbers in `sec:gt_vacuum`, the Arrhenius
  figure caption, the trap-isolated paragraph and the two nucleation bounds replaced by macros;
  +2 sentences reporting the D3-with-phi fits; fixed a missing space ("window.A").
  (Your concurrent delta-plot caption edit was preserved.)
- `chapter2goethite_SI_body.tex`: model-fit and synthetic tables now built from macros (two
  new D3 rows); the all-steps paragraph uses macros; +D3-with-phi comparison in "Fits to
  the vacuum data".
- Displayed-value changes from rounding: D3 KAF rms prints 0.045 (was 0.046; value 0.0455);
  all-steps R2 KAF rms 0.012 (was 0.0116); "five times worse" -> "5.3 times".
- GCA manuscript not changed (it still hard-codes these numbers).
Verified: full dissertation build, 0 errors, no undefined macros; the macro file written on the
local VM is byte-identical to the one tested.

## Follow-up: delta plot legend moved off the data

- `fig_delta_plot.py` (both variants): legend text reduced from 11 pt to 8.5 pt
  (`LEGEND_FONTSIZE`), tighter handle length / label spacing, and the legend is
  now anchored centre-right against the right axes edge at Delta = 3 (`LEGEND_Y`,
  data units), sitting in the empty band between the hydrothermal 3He line at 0
  and the vacuum plateaus at ~6. Checked visually: overlaps no data.

---

# 2026-09-29b -- New Arrhenius comparison figure replaces the Stage 2 figure in Chapter 2

## Figure (Chapter2/Figures/fig_goethite_vacuum_kinetics.py, make_arrhenius_comparison)
`arrhenius_reaction_vs_diffusion.pdf` redrawn in the house style of
`winsor_goethite_Diffusivities_Arrhenius.pdf` (plot_style.apply_style, top-axis temperature in C,
1e4/T axis, KAF red / HDM orange / hydrothermal blue, dashed connectors):
- temperature range now 125--325 C;
- the points of each experiment are joined sequentially by dashed lines; no prograde/retrograde
  distinction;
- filled = vacuum steps in the kinetic fitting window, open = outside it; large pink
  (tab:pink) circles mark the two LN2-isolated KAF steps;
- hydrothermal: bounding-method central values with LB/UB bars, low-signal steps excluded;
- black line = joint first-order fit; per-experiment dashed fit lines and the Stage 2 line
  are gone;
- two panels side by side (12.8 x 5.9 in, fonts scaled 1.6x) with a shared legend underneath,
  so the figure plus its long caption fit on one page at full text width. (A stacked version
  was too tall for the page with the caption.)

## chapter2_body.tex
- The Results figure `fig:ch2-arrhenius-full` (winsor_goethite_Diffusivities_Arrhenius.pdf,
  Stage 2 reference line) was replaced by this figure, now labelled `fig:gt_arrhenius`, with a
  new caption that compares the two reductions (first-order k vs. FK D/a^2) for the vacuum and
  hydrothermal experiments.
- The duplicate copy of the figure in the Discussion (`sec:gt_vacuum`) was removed; the three
  references to `fig:ch2-arrhenius-full` now point to `fig:gt_arrhenius`b.

## GCA manuscript
`hydrothermal_goethite_body.tex`: the `fig:gt_arrhenius` caption was updated to describe the new
styling (colors, dashed connectors, black fit line, pink circles), and the figure is now included at full text width.
The manuscript still also shows `winsor_goethite_Diffusivities_Arrhenius.pdf` (fig:arrhenius-full,
with the Stage 2 line), which is still produced by fig_decomp_vs_hydrothermal.py.

Verified: dissertation and manuscript build, 0 errors, no new undefined references, and no
float-too-large warning for the new figure.

---

# 2026-09-29c -- Trial: fitting window trimmed by one step; figure and phase-diagram tweaks

## Trial window (easy to undo)
`fig_goethite_vacuum_kinetics.py`: new flag `TRIM_LAST_FIT_STEP = True` drops the last step of
each fitting window (KAF 5-23 -> 5-22, i.e. 285 C step excluded; HDM 8-28 -> 8-27, i.e. 338 C
step excluded). **To undo: set it to False and rerun the script** (then
fig_goethite_hydrothermal_tests.py and copy_manuscript_sources.py). The window description in
Methods and every phi-dependent number in the chapter are now macros, so the chapter follows the
flag automatically: new `\ChTwoKinWinKAF/HDM`, `\ChTwoKinWinKAFT/HDMT`, `\ChTwoKinPhiPct`,
`\ChTwoKinOneMinusPhi`, `\ChTwoKinHTFEnd`, `\ChTwoKinHTAlphaObs`, `\ChTwoKinLogAlphaLow/Mid/High`,
`\ChTwoKinAlphaPermissive` (chapter2_body.tex: fitting-window sentence, "~11%" plateau,
predicted hydrothermal alpha, permissive-gamma alpha, apparent alpha).

Effect (old -> trimmed):
| | old | trimmed |
|---|---|---|
| cumulative F1 Ea / ln A / phi / s | 122.9 / 18.67 / 0.112 / 0.46 | 120.8 / 18.15 / 0.101 / 0.47 |
| F1 rms KAF / HDM | 0.0085 / 0.017 | 0.0087 / 0.018 |
| joint step-rate line Ea / ln A (n) | 121.4 +/- 4.4 / 18.08 +/- 1.05 (38) | 130.4 +/- 3.4 / 20.27 +/- 0.81 (36) |
| KAF alone / HDM alone | 134.9 +/- 6.1 / 116.3 +/- 5.6 | 139.3 +/- 6.2 / 126.6 +/- 3.9 |
| k(250 C), conversion/h | 5.4e-5, 18% | 6.1e-5, 20% |
| residual rms KAF / HDM (log10) | 0.15 / 0.21 | 0.12 / 0.12 |
| D3 (phi=0) rms KAF / HDM | 0.045 / 0.053 | 0.038 / 0.055 |
| D3 (phi=phi_F1) rms KAF / HDM | 0.024 / 0.054 | 0.026 / 0.056 |
| predicted HT log10 alpha (0.14/0.16/0.19) | -20.6/-31.5/-53.7 | -20.5/-31.4/-53.7 |
| hold projection (F1 / D3) | 0.173 / 0.149 | unchanged (0.173 / 0.149) |
Model ranking unchanged. Numbers not tied to the fits (gamma_eff calibration, the hydrothermal
residual ranges, Test 1/2) did not change at the precision quoted.

## Arrhenius comparison figure
Light grey grid on both panels; x label now `10^4/T (K)` (was a stacked fraction).

## Phase diagrams (fig_goethite_hematite_phase_diagram.py)
All P-T phase diagrams (goethite_hematite_Ph2o_T_hydrated, size_basis_sensitivity,
goethite_hematite_Ph2o_T_equal_area/_equal_diameter) now plot log P_H2O from -3 to 4 bar and
T from 0.5 to 275 C (new constants PT_LOGP_PLOT_MIN, PT_T_MAX_C; the solver range is unchanged).
The legends of the two-panel equal_area/equal_diameter figures were moved to center-right.

## Not updated (trial)
The GCA manuscript still hard-codes the old window's numbers (e.g. Ea 121.4 +/- 4.4,
phi = 0.112) but uses the regenerated figure, whose legend now reads Ea = 130 +/- 3 kJ/mol.

---

# 2026-09-29d -- Chapter 2 restructured (goethite-forward); HDM fitting window ends before ~317 C

No text was rewritten except as noted below. Everything else was moved as whole paragraphs, figures or tables.
The GCA manuscript was not touched and will be rebuilt later.

## Fitting window (fig_goethite_vacuum_kinetics.py)
- `WINDOW_STEPS_TRIAL = {"KAF": (5, 22), "HDM": (8, 26)}`, `USE_TRIAL_WINDOW = True`. This excludes HDM step 27
  (317 C) and all steps after it; KAF is unchanged from the 29b trial.
  - To restore the original 5-23 / 8-28, set `USE_TRIAL_WINDOW = False`.
- Re-run on the device: `fig_goethite_vacuum_kinetics.py`, then `fig_goethite_hydrothermal_tests.py`.
- Main results:
  - Joint Arrhenius line: Ea = 137.0 +/- 2.7 kJ/mol, ln A = 21.91 +/- 0.66, N = 35.
    The 29b trial gave 130 +/- 3; the original window gave 121.4 +/- 4.4.
  - Per experiment: KAF 139.3 +/- 6.2, HDM 135.4 +/- 2.5.
  - Cumulative F1: Ea = 120.8, phi = 0.101, rms 0.0087 (KAF) / 0.018 (HDM).
  - D3 at phi(F1): rms 0.026 / 0.057, 3.0x F1.
  - Hydrothermal translation: log alpha = -20.5 / -31.4 / -53.7.
  - All of these are macros, so the text follows automatically.

## chapter2_body.tex
- Introduction: the three SEM figures (control/vacuum, buffered, vacuum interior) were moved here from
  the Discussion to motivate the method.
- Experimental Methods:
  - The SEM study paragraph now also carries the label `sec:gt_pigment_methods`.
  - Two sentences on the pigment runs (water only; no vacuum or open-air runs) were added, with a
    TODO for the pigment's product name and supplier.
  - The separate "Synthetic Pigment" methods paragraph was DELETED, with permission.
- Moved to the SI:
  - Permeation Lag Correction (with the permeation-fit and ampoule-permeability figures).
  - The Discussion paragraphs on measured/simulated apparent permeability and on the consistency of the
    bounding method / complete degas test (with the nt-vs-ntss figure).
  - All analytical methods: the finite-difference cooling tube, diffusivity inversions, isotope-ratio
    uncertainty, and the Kinetic Analysis of Vacuum Step Heats.
- Discussion order: MDD consistency; vacuum; hydrothermal; dehydration/recrystallization; pigment;
  retentivity; 4He/3He. The thermodynamics block now comes last: Thermodynamic Model methods, then
  sec:gt_thermo, then sec:gt_nucleation.
- The thermo-kinetic sensitivity sections stay in the SI.

## chapter2goethite_SI_body.tex
- New section headings (added text):
  - "Permeation Lag Correction and Ampoule Permeability" (`sec:ch2-si-permeation`)
  - "Analytical Methods" (`ch2-analytical-methods`)
- Both sit before the existing dataset section.

## Verification
- Full dissertation: 0 errors, 247 pp.
- Undefined references:
  - the pre-existing `app:bushveld`;
  - `fig:ch2-fourier-win0601b` (the figure was removed on 09-29 but is still cited, body around line 1023).
- One float is too large by 1.3 pt (the Fourier hematite-reference figure; not moved).

---

# 2026-09-29e -- Chapter 2 flow edits after the restructure

Goal: make the new order (goethite observations first, thermodynamics last) read correctly.
Pre-edit copies of the body, SI body and abstract are kept in the session scratchpad; git HEAD also has them.
The GCA manuscript is still untouched.

## chapter2_body.tex

### Introduction
- The last sentence of the "Goethite dehydration is suppressed..." paragraph was removed from that
  paragraph and rewritten as a new closing paragraph (roadmap). It previously cited
  "(S thermo--S pigment)", a range that is now out of order. It now reads: first hydrothermal step
  heat, compared with the vacuum step heats (S gt_vacuum--gt_hydro); the thermodynamic/kinetic
  analysis then explains why water has this effect (S gt_thermo_methods--gt_nucleation).
- MOVED from the end of Results into the Introduction: the SEM observations paragraph ("SEM imagery
  taken of thermally treated natural goethites... remained black"). It is unchanged except for a
  new lead sentence, "Early trials of the method were encouraging (S SEM methods)." The Introduction
  text now cites the SEM figures that sit there.

### Experimental Methods
- ADDED a paragraph after the final-step (furnace) paragraph. It says that measured yields lag the
  release because of permeation, that they were corrected by the bounding method (Ch. 1, S
  bounding-method; LB/central/UB in the distilled tables), and it points to
  SI S sec:ch2-si-permeation and SI S ch2-analytical-methods.
  - Reason: with those sections moved to the SI, the main text no longer said how the data were
    reduced.

### Results
- 3He table caption: "(see \ref{permeation-lag-correction})" became "(see \S\ref{...})".
- The SEM paragraph was removed from here (moved to the Introduction, above).

### Discussion
- MDD paragraph:
  - "This is tested quantitatively in S vacuum--S nucleation" became "...in S vacuum--S hydro,
    and explained in S nucleation". The old range now spans unrelated sections.
  - The hard-coded "160 kJ/mol" became \ChTwoEa{} (macros take priority).
- Vacuum section (sec:gt_vacuum):
  - The first sentence now names "the first-order conversion model of S sec:gt_kinetics_methods",
    because those equations are now in the SI.
  - "(S sec:gt_kinetics_methods)" was added after "the fitting window".
  - "We use these two steps in S nucleation to calibrate the nucleation model" became
    "We return to these two steps in S nucleation, where they calibrate the nucleation model."
- Hydrothermal section: the last sentence was recast as a forward reference: "Section
  nucleation shows why: the conversion rate expected at water saturation is too small..."
- Dehydration section: "The kinetic analysis of S vacuum--S nucleation indicates" became "The
  kinetic analysis of S vacuum--S hydro, and the nucleation analysis of S nucleation, indicate".
- Pigment section (sec:gt_pigment):
  - New opening. It previously followed the nucleation section: "Fluid-mediated conversion does
    occur in some materials." It now reads: "Goethite can also convert to hematite through the
    fluid, by dissolution of goethite and precipitation of hematite, and this fluid-mediated
    conversion does occur in some materials."
  - "a pathway outside the solid-state model of S nucleation" became "...outside the solid-state
    nucleation model developed in S nucleation".
  - MOVED the thermodynamic paragraph ("Grain size and bulk thermodynamics do not explain why these
    blades reacted...", with its TODO comment) to the end of S gt_nucleation. It uses Table gt_dmu,
    which now comes later. It opens there with a new lead: "Assumption (iv) matters for the
    synthetic pigment of S pigment." "these blades" became "the pigment blades".
  - The pigment conclusion sentence was reworded so it does not rest on the later thermodynamics.
    It now reads: "We conclude that water-saturated conditions do not by themselves exclude
    fluid-mediated conversion of goethite, even where solid-state conversion is suppressed
    (S nucleation)."
- Fourier/retentivity:
  - The citation of the removed figure fig:ch2-fourier-win0601b was replaced with "(see the
    vacuum step heats of Win-06-01b and the overlapping hematite samples in Fig.
    fourier-hematite-ref)".
  - That figure's width went from 0.80 to 0.75 \textwidth. Before, its float was 1.3 pt too large.
- Thermodynamic block (start of S gt_thermo_methods): ADDED a lead-in paragraph. It says the
  preceding sections establish, from the release patterns alone, conversion in vacuum and
  diffusion in water, and that the thermodynamics here explains why and bounds the
  conversion (S thermo, S nucleation).
- Typo fixed in assumption (ii): "so and only the chemical potential" became "so only the chemical
  potential".
- Four \clearpage were removed: one in the middle of the dehydration section, and the ones after the
  isothermal-retention figure, the Fourier figure and the 4He/3He figure. The first flushed the SEM
  figures, which are now in the Introduction. The others left half-empty pages. The \clearpage after
  the ampoule figures, after the Results figures and before the Conclusions are kept. The chapter is
  about 2 pages shorter, and every float lands within about a page of its first mention.

### Conclusions (reordered to follow the new flow; no findings changed)
- Paragraph 1: motivation and method. The SEM sentence ("Hydrothermally treated goethite does not
  develop the visible dehydration-induced contraction cracks...") moved here from the last
  paragraph, as the motivation.
- Paragraph 2: the observational result first. "Vacuum step heats of the same sample follow
  first-order conversion to hematite, whereas the hydrothermal release shows the history and time
  dependence of diffusion" was moved here from the last paragraph and lightly reworded. It is
  followed by the diffusivity and retentivity results ("It gives" became "The hydrothermal
  experiment gives").
- Paragraph 3: the 4He/3He paragraph (unchanged).
- Paragraph 4: the thermodynamic explanation ("A thermodynamic and kinetic analysis of goethite
  dehydroxylation explains why water has this effect: at water saturation...") and then the
  unchanged caveats and future work.

## chapter2_abstract.tex
- The thermodynamic/nucleation sentences moved from before the results to after them.
- ADDED one sentence before them: reanalysis of the vacuum step heats shows first-order conversion,
  whereas the hydrothermal release records diffusion.
- "shows that conducting step heats..." became "explains this difference and shows that
  conducting step heats...".
- Everything else is unchanged.

## chapter2goethite_SI_body.tex
- Complete degas test:
  - "Stage 1 procedure used for the bounding method above" became "...in the main text" (it is no
    longer above).
  - Fixed "Figs.~/ref{...},~/ref{...}" to \ref, which was a broken rendering.
- Dataset section intro: "described in full in the main text (S ch2-experimental-methods)" became
  "described in full in S sec:ch2-si-permeation and S finite-difference... (cooling tube)".
- Your caption edit in tab:gt_mech_fits cited \citet{montiero2017}, which is not a bib key. It is
  fixed to monteiro2017.

## Chapter2/Figures/fig_permstep_isothermal_fits.py and chapter2_permstep_isothermal_tables.tex
- Fit-table caption: "described in the main text (S experimental-methods)" became "described in
  S sec:ch2-si-permeation". The old label did not exist.
- \footnotesize moved inside the table float. The old \begin{footnotesize} around a float had no
  effect, and the table was 32 pt too wide.
- The generated .tex was edited in place with its CRLF endings kept. The script was changed to
  match, so a rerun gives the same result.

## Verification
- Full dissertation: 0 errors, 245 pp.
- The only undefined reference is the pre-existing app:bushveld.
- No float-too-large warnings, and no overfull boxes > 2 pt in Chapter 2 or its SI.

---

# 2026-09-30 -- Nucleation-rate wording + Turnbull & Fisher; legible phase diagrams

## chapter2_body.tex (edited in place on your latest version)
- Eq. gt_knuc lead-in: "the rate constant is a nucleation rate," became "...a nucleation rate of
  the form derived by \citet{turnbull1949},".
- "exp(-dG*/kBT) the probability of forming a critical nucleus" became "exp(-dG*/kBT) is the
  equilibrium fraction of sites occupied by critical nuclei".
- references.bib: added turnbull1949 (Turnbull & Fisher 1949, JCP 17, 71). The key matches the
  file's short-key style, and the Zotero file path was dropped. If you re-export from Zotero,
  its key is turnbull_rate_1949.

## Chapter2/Figures/fig_goethite_hematite_phase_diagram.py (phase diagrams only)
- New `_styled(width_in, printed_frac)` decorator. It applies plot_style.apply_style inside an
  rc_context, so the other figures in the script (dmu maps, barrier ratio, etc.) are unchanged.
  - Scale rule: 0.125 x figure width / printed fraction of \textwidth. That is the same printed
    text size as the Arrhenius comparison figure (12.8 in, scale 1.6, full width).
  - make_pt_hydrated (6.5 in at 0.7\linewidth): scale 1.16.
  - make_basis_sensitivity (11 in, full width): 1.375.
  - make_figure (now 10 x 10 in, two stacked panels, legends to the right): 1.25.
- Hard-coded small font sizes were removed. Legends and labels now use the shared sizes.
- Legends: sizes are labelled "bulk (+0.00 kJ)" etc. under a legend title "size (dG_surf)", so
  the legends fit. They sit at lower right. handlelength is 1.4.
- Main-text diagram:
  - The alpha-FeOOH label is now an arrow pointing into the narrow goethite field. It had
    overlapped the curves.
  - The hematite + water label moved to the upper right of the hematite field.
- SI size-basis figure: the liquid-vapor curve is labelled on the plot instead of in the legend,
  so the legend no longer covers the 10 nm curve.
- Re-run on the device.

---

# 2026-09-30b -- 09-29e flow edits re-merged onto your current Chapter 2

Your save of chapter2_body.tex on 09-30 had been made from a buffer opened before the 09-29e edits.
As a result, those edits were missing from the body, and two were missing from the SI.

## What was done
- Your current files were the base: your thermodynamics restructure (details moved to SI
  sec:eqm-thermo), your caption and Delta-mu edits, and the Turnbull & Fisher edit.
- Every 09-29e body edit was re-applied onto them:
  - Introduction: SEM paragraph and roadmap.
  - Methods: the permeation-lag/SI pointer paragraph.
  - Caption \S.
  - Section-range fixes.
  - \ChTwoEa in place of 160 kJ/mol.
  - Pointers to sec:gt_kinetics_methods.
  - Forward references to S nucleation.
  - Pigment opening, pigment conclusion sentence, and the pigment thermodynamic paragraph moved
    to the end of S nucleation.
  - Fourier citation fix and 0.75 figure width.
  - "so only" typo.
  - The four \clearpage removals.
  - Reordered Conclusions.
- NOT re-applied: the 09-29e thermodynamic lead-in paragraph. You wrote your own lead-in in
  sec:gt_thermo_methods ("This work suggests, so far empiraclly and qualitatively, ...").
  Note the typo "empiraclly" there, and "wate" in the fig:gt_PT caption. Both are left for you.
- SI: re-applied two fixes.
  - "described in full in the main text (S ch2-experimental-methods)" now points to the SI
    sections.
  - "/ref" is now "\ref".
- The abstract edits and the other SI edits were already present.

## Verification
- Full dissertation: 0 errors, 246 pp.
- The only undefined reference is app:bushveld.
- No float-too-large warnings.

---

# 2026-09-30c -- Review response, items 1-2: rate-law sensitivity, empirical bound, Monte Carlo

## fig_goethite_vacuum_kinetics.py (new section "Water-inhibition rate laws")
- Three laws are calibrated on the two trap-isolated KAF steps, R(P_off) = s:
  - nucleation, ln R ~ -C g^3 / (T dmu^2);
  - Langmuir site blocking, R = (1+K P_on)/(1+K P), with K held constant;
  - power law, R = (P/P_on)^-n.
- Each law is applied at P_sat(T) step by step through the hydrothermal schedule:
  alpha = 1 - exp(-sum k_vac R dt).
- A rate law linear in dmu is checked too. It predicts s = 1.000, so it cannot reproduce the
  calibration.
- `rate_law_table`: the deterministic grid (both steps x 190/600 mL x end-of-step or half pressure).
  Output: generated/hydrothermal_rate_law_sensitivity.csv.
- `rate_law_monte_carlo` (4000 draws, fixed seed) samples:
  - the step;
  - s, log-uniform over F1/R3 step-rate reductions x neighbour choice (230 C: 0.30-0.37;
    240 C: 0.22-0.23);
  - V_app, log-uniform 190-600 mL;
  - the pressure fraction, uniform 0.5-1;
  - for nucleation only, a common Delta G_r offset, uniform +-2.8 kJ.
- `empirical_bounds`: sum k_vac dt over the schedule is 60.
  - All observed 3He from conversion would need R <= 10^-2.5.
  - Less than 1% conversion needs R <= 10^-3.8.
- `cnt_scales`: r* and the formula units in the critical nucleus.
  - Vacuum: 0.08-0.11 nm, 0.04-0.11 f.u., barrier 0.5-1.3 kBT.
  - Saturation: 0.8-1.1 nm, 42-105 f.u., barrier 51-129 kBT.
- New SI figure: generated/hydrothermal_rate_law_sensitivity.pdf.
- About 45 new \ChTwoKin* macros.
- \ChTwoKinDetect is now computed from the actual schedule, ln(sum k_vac dt / 0.01), instead of
  k(250 C) x total time. Its value is unchanged (9).
- Results:

  | Law | log10 R at 250 C | alpha, grid | alpha, MC 95% |
  |---|---|---|---|
  | nucleation | -53.5 to -21.1 | 10^-51.9 to 10^-19.4 | 10^-67.3 to 10^-15.7 |
  | Langmuir | -6.9 to -5.6 | 10^-5.1 to 10^-3.8 | 10^-4.9 to 10^-3.9 |
  | power | -1.9 to -1.1 | 0.52-0.99 | 0.59-1.00 |

  The power law is excluded by the observed release.

## chapter2_body.tex -- S gt_nucleation rewritten around the reviewer's points
- It now opens with "What the data require": the empirical bounds (R <= 10^-2.5; R <= 10^-3.8 for
  less than 1%).
- "Candidate rate laws": the three laws plus the linear check. Cites topley1935, lvov2007 and
  koga2019 (all new in references.bib). New Table tab:gt_ratelaws.
- The discrimination paragraph says:
  - the power law is falsified;
  - site blocking and nucleation both predict negligible conversion;
  - the magnitude of the suppression (10^-5.6 to 10^-53.5 at 250 C) is set by the law, not by
    the data;
  - the nucleation model is one explanation, not a measurement.
- The CNT derivation, the TST ceiling and "nucleation must be internal" are kept. The topotactic
  paragraph is condensed.
- REMOVED the Porter coherent/semicoherent justification of gamma_eff, and "within the range
  expected for coherent and semicoherent interfaces".
- New paragraph "Where classical nucleation theory applies", with the r*, formula-unit and
  barrier macros. gamma_eff is now described as a phenomenological parameter (B = C g^3). Saito's
  0.24 J/m2 is kept as an order-of-magnitude comparison, with a caveat.
- gamma_eff is now "0.16 J/m2, range 0.14-0.19" (macros), replacing "0.16 +- 0.03".
- The barrier ranges now come from macros (51-129 kBT; the text had said 52-129).
- New sentence: the vapor-pressure estimate is an upper bound, which is conservative.
- The detectability equation now uses the schedule sum.
- New Monte Carlo sentence: 10^-67 to 10^-16 (95%). The thermodynamic offset contributes most of
  the spread.
- Assumption (i) now points to the site-blocking result.
- The item-1 driving-force reference now reads Eq. gt_dGr (S eqm-thermo). eq:gt_Gw now lives in
  the SI.
- Softened elsewhere:
  - Hydrothermal section end: requires more than 10^2.5; every consistent law gives more.
  - Dehydration section: "about five orders of magnitude or more".
  - Conclusions: rewrote the thermodynamics paragraph (empirical bound; ~5 orders of magnitude if
    site blocking, tens if nucleation; the size is not determined by the data).
  - Abstract: "many orders of magnitude" became "at least five orders of magnitude".
  - The "10^{2.5}" in the hydrothermal section and the Conclusions is typed, not a macro.

## chapter2goethite_SI_body.tex
- New section sec:gt_supp_ratelaws "Sensitivity to the water-inhibition rate law":
  - the three laws' equations;
  - the constant-K and P_on caveats;
  - the linear-law check;
  - the empirical-bound derivation;
  - the Monte Carlo sampling;
  - Figure fig:gt_ratelaws.
- tab:gt_surf_sens: moved the long table footnote into the caption. It was 139 pt too wide.

## Verification
- Full dissertation: 0 errors, 251 pp.
- The only undefined reference is app:bushveld.
- No overfull boxes > 2 pt in Chapter 2 or its SI.
- The script reproduces the same macros on the device.

---

# 2026-10-01 -- Cut the thermodynamic/kinetic modelling to its essentials

Pre-cut state is committed as 94aab4c ("Thermodynamic overkill progress save").

## Main text, S gt_nucleation: 287 lines down to 90
- KEPT:
  - The data bound: sum k_vac dt ~ 60; R <= 10^-2.5 if all 3He came from conversion; R <= 10^-3.8
    for less than 1%.
  - The CNT barrier (eq:gt_barrier) and the Turnbull-Fisher rate (eq:gt_knuc), with the
    gamma^3/dmu^2 scaling.
  - The internal-nucleation scope: the 5-line replacement citing the topotactic literature.
  - The gamma_eff calibration equation (eq:gt_gamma_cal) and result, 0.16 (0.14-0.19) J/m2.
  - A short statement that the vacuum nucleus is sub-formula-unit, so gamma_eff is a
    phenomenological parameter.
  - The translation equation (eq:gt_translate), with the predicted alpha for the three gamma values
    and the Monte Carlo 95% range, plus one sentence that the values reflect the assumed form and
    exceed what the data require.
  - Assumptions (i)-(iv), condensed into one paragraph.
  - The pigment thermodynamics paragraph (unchanged).
- CUT:
  - The candidate-rate-law paragraph, Table tab:gt_ratelaws and the law-comparison paragraph
    (site blocking, power law, linear law).
  - The TST upper bound (eq:gt_ceiling) and the free-surface nucleation argument.
  - The Saito comparison.
  - The per-gamma k_sat/k_vac values at 250 and 200 C.
  - The detectability equation.
  - The gamma_eff = 0.084 "permissive" sentence.
- MOVED to the SI calibration section: the driving-force evaluation list, the water-pressure bound
  and Table tab:gt_gamma.
- Elsewhere: the hydrothermal-section closing sentence, the dehydration section, the Conclusions and
  the abstract now refer to nucleation control only. The abstract reads "many orders of magnitude".

## SI
- Equilibrium thermodynamics:
  - The apparent-G discussion is condensed to 3 sentences.
  - The Cp integrated forms are removed; the Cp forms are stated inline, and the hematite TODO is
    kept.
  - The basis-dependence pointer is replaced by one sentence (-1.41 kJ at 10 nm at equal diameter;
    it affects stability only).
- CUT: the section "Sensitivity of the size effect to the surface-area basis" (Table tab:gt_basis,
  Fig. fig:gt_basis).
- "Nucleation barrier ratio and the calibration of gamma_eff" became "Calibration of gamma_eff" (same
  label, sec:gt_supp_barrier).
  - The barrier-ratio discussion and Fig. fig:gt_barrier_ratio are cut.
  - It now holds the calibration details moved from the main text, fig:gt_translation, the
    surface-term sensitivity table, and a nucleation-only Monte Carlo paragraph.
- CUT: the section "Sensitivity to the water-inhibition rate law" and Fig. fig:gt_ratelaws.

## fig_goethite_vacuum_kinetics.py
- The rate-law code is reduced to nucleation only:
  - Removed the Langmuir, power-law and linear branches, linear_law_s and make_rate_law_figure.
  - Removed 22 macros.
  - The nucleation numbers are unchanged (same seed).
- Moved to _to_delete/old_figures/: the generated hydrothermal_rate_law_sensitivity.*,
  size_basis_sensitivity.* and nucleation_barrier_ratio_vs_T.* figures. The phase-diagram script
  still makes the last two; they are no longer used.
- references.bib still contains topley1935, lvov2007 and koga2019. They are now uncited, so they
  are not printed.

## Verification
- Full dissertation: 0 errors, 243 pp (was 251).
- The only undefined reference is app:bushveld.
- No float-too-large warnings, and no overfull boxes > 2 pt in Chapter 2 or its SI.

---

# 2026-10-01b -- SI kinetic-mechanisms section: h(alpha) and x defined; integral form removed

## chapter2goethite_SI_body.tex, sec:gt_supp_mech
- Removed the g(alpha) integral equation.
- Replaced it with:
  - the rate law dalpha/dt = A exp(-Ea/RT) h(alpha), citing vyazovkin2011;
  - a plain-language definition of the reaction model h(alpha), with what it means physically for
    F1, R2/R3 and A2/A3;
  - an explicit definition of x as the Arrhenius-weighted time (x = kt for a single isothermal
    step; the Fourier number Dt/a^2 for D3).
- Table tab:gt_mech_forms:
  - dropped the g(alpha) column, keeping Model | h(alpha) | alpha(x);
  - new caption;
  - removed the \resizebox, which would otherwise have stretched the narrower table.

## references.bib
- Added vyazovkin2011 (ICTAC Kinetics Committee recommendations, Thermochim. Acta 520, 1-19).

## Open (from your 09-30 move of the kinetic-analysis methods into the main text)
- Two undefined references:
  - \label{sec:gt_kinetics_methods}: the moved text has no heading or label, but the body still
    cites it twice (vacuum section).
  - eq:gt_FK: the Fechtig-Kalbitzer equation is no longer in the files, but it is cited in the
    body (Arrhenius caption area, input line ~733).
- sec:gt_supp_mech is still a \subsection. After the move it sits under the SI section
  "Equilibrium Thermodynamics of Goethite Dehydroxylation".

---

# 2026-10-01c -- Hematite Cp switched to Berman (1988); dependent values recalculated

Source: your uploaded goethite_hematite_phase_diagram.py and ch2_goethite_stability_sections.tex.
Only the hematite Cp changes were taken.

## Chapter2/Figures/fig_goethite_hematite_phase_diagram.py
- Hematite Cp now uses the Berman (1988) polynomial, K_HEM = (146.86, 0, -5.5768e6, 5.2563e8), plus
  the lambda term T(l1 + l2 T)^2 with l1 = -0.07403, l2 = 2.7921e-4, T_lambda = 955 K.
- New function _lambda_int. G_solids now uses _berman_int(K_HEM) + _lambda_int.
- The Maier-Kelley MK_HEM and _mk_int are kept for comparison only.
- The docstring has been updated.
- Your legend edits in this file are kept.
- Re-run: the phase diagrams. Also re-ran fig_goethite_vacuum_kinetics.py; molmass was installed
  in the local VM for thermochr_utils.

## Recalculated values (old -> new)
- Hematite Cp(298 K): 104.8 -> 104.0 J/mol/K.
- dmu_sat (Table tab:gt_dmu, main text): 200 C 8.10 -> 8.11; 225 C 9.36 -> 9.37; 250 C 10.65 -> 10.66.
  The other columns are unchanged.
- Table tab:gt_gamma: 240 C / 190 mL / P/2 changes from 0.172 to 0.173. Everything else is
  unchanged.
- Table tab:gt_surf_sens:

  | Grain size | Delta-mu_sat | Delta-mu_vac | log alpha |
  |---|---|---|---|
  | bulk | 10.65 -> 10.66 | unchanged | -32.0 -> -31.9 |
  | 100 nm | 10.27 -> 10.28 | 103.5 -> 103.6 | -31.2 -> -31.0 |
  | 10 nm | 6.89 -> 6.90 | unchanged | -23.3 -> -23.2 |

  The log-alpha column changed mostly because the old values predated the current fitting window
  and vacuum line. The Cp change alone moves it by less than 0.1.
- Unchanged at the quoted precision:
  - Delta G_r at 298 K (-0.26 kJ; 0.13 kJ per FeOOH). The Cp terms vanish at T_r.
  - The saturation crossings (18, 28 and 108 C) and log P at 25 C (2.62, -1.52, -2.11).
  - The vacuum dmu values.
  - All \ChTwoKin* macros, which were regenerated and are identical.

## SI text
- The Cp paragraph now describes the Berman hematite polynomial and the lambda term (formula only;
  the integrals are not shown, as elsewhere in this section). The TODO now says to verify the
  coefficients against Berman Tables 3a/3b (they are from the CHNOSZ transcription).
- tab:gt_thermo_data:
  - hematite k0-k3 and l1, l2 rows;
  - Cp(298) = 104.0;
  - the footnote now separates the sources (hematite Cp: berman1988) and adds coefficient units.

## Note (not changed)
- The body currently cites fig:ch2-sem-air and fig:ch2-sem-vacuum, which are undefined. These are
  from your in-progress edits.

---

# 2026-10-01d -- Redo of 10-01c on your current files; g(alpha) removal re-applied

What went wrong in 10-01c: the copy of your .tex files used as the base was stale. Staging had
not finished when it was read, so it was an older snapshot. Committing it overwrote your recent
edits. This time the staged files were checksum-verified against the files on disk before
editing, and only targeted replacements were made, with your CRLF line endings preserved.

## chapter2_body.tex (3 lines)
- tab:gt_dmu, Delta-mu_sat: 8.10 -> 8.11, 9.36 -> 9.37, 10.65 -> 10.66 (Berman hematite Cp).

## chapter2goethite_SI_body.tex
- The hematite Cp sentence now uses the Berman (1988) polynomial plus the lambda term (the
  Maier-Kelley text and its TODO are replaced). New TODO: verify the coefficients against Berman
  Tables 3a/3b.
- tab:gt_thermo_data:
  - hematite k0-k3 and l1, l2;
  - Cp(298) 104.8 -> 104.0;
  - the footnote now separates the sources (hematite Cp: berman1988) and gives the coefficient
    units.
- tab:gt_gamma: 0.172 -> 0.173 (240 C, 190 mL, P/2).
- tab:gt_surf_sens:
  - Delta-mu_sat 10.66 / 10.28 / 6.90;
  - 100 nm Delta-mu_vac 103.6;
  - log alpha -31.9 / -31.0 / -23.2.
- sec:gt_supp_mech (re-applied from 10-01b):
  - removed the g(alpha) integral equation and the g(alpha) table column;
  - defined h(alpha) and x explicitly, citing vyazovkin2011;
  - new table caption;
  - removed the \resizebox.

## references.bib
- vyazovkin2011 appended. It was missing from the current file.

# 2026-10-01e -- Chapter 2 body restructuring pass (move-only)

Backup: Chapter2/Writing/chapter2_body.tex.pre_reorder_backup_20261001. No prose added or
deleted; only passages moved. Moved blocks are tagged in the source with
`% --- ... (moved from Discussion, 2026-10-01) ---`.

## chapter2_body.tex
- Methods: kinetic-reduction assumption (F_i = (1-phi) alpha_i), eqs gt_F1/gt_F1_cum/gt_stepk,
  the Fechtig-Kalbitzer comparison sentence, fitting window and exclusions, the phi justification
  (F ~ 0.9 stall, Stage 2/3), the vacuum 4He/3He maximum near F ~ 0.9 (from the 4He/3He
  section), and the design of the 250 C isothermal test.
- Results: fig:gt_arrhenius, early-step excess release, eq gt_line and KAF/HDM/all-step fits,
  HDM out-of-sample prediction, trap-isolated steps, 250 C test outcome and fig:gt_hold.
- Discussion reordered: vacuum = conversion -> water-saturated = diffusive (+ MDD) ->
  thermodynamics (sec:gt_thermo_methods now merged with sec:gt_thermo; heading
  "Thermodynamic Model of Goethite Dehydroxylation" carries both labels) -> nucleation ->
  dehydration/recrystallization caveats -> pigment (+ assumption (iv) paragraph appended) ->
  retentivity -> 4He/3He.
