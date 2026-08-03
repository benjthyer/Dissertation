# Chapter 2 SI Reorganization — Change Log

Date: 2026-07-27
Files touched: `Chapter2/Workspace/chapter2_body.tex`, `Chapter2/Workspace/chapter2goethite_SI_body.tex`
Builds verified: `chapter2goethite.tex` (standalone chapter draft), `chapter2goethite_SI.tex` (standalone SI draft), `dissertation.tex` (combined, 173 pages, zero undefined references)

## Why

The SI had grown to contain two things that don't belong together: (1) the isothermal-permeation-fit methodology that justifies a load-bearing assumption used by the main text's "treatment as uncertainty" method, and (2) the naïve/informed bracketing method — a separate, more heavily-reduced treatment of the same dataset that the main text no longer relies on for its primary conclusions. The goal of this pass was to pull (1) into the main text where it belongs, and reframe the SI as a secondary, independent verification built on the bracketing method, per direction from Ben.

Clarifications from Ben that shaped these edits, and are reflected below:
- The only truly load-bearing part of the isothermal fitting exercise is that it justifies the assumption that literature permeability values are *lower* than the ampoule's true permeability, making the treatment-as-uncertainty bounds conservative (i.e., wider than the true bounds) rather than optimistic. This is counterintuitive for a hydrothermal experiment (hydration is generally expected to slow permeation), so it needs real evidentiary support in the main text, not just an assertion.
- The isothermal permeation fits done in this chapter measured **3He only** — 4He signals during those steps were blank-level and could not be independently fit.
- The isotope permeability ratio δ = K₃/K₄ = 1.10 ± 0.19 (2σ), and its 2σ upper bound of 1.29 used in the bound calculation, is **not** measured in this chapter. It comes from a water-filled tube experiment in Chapter 1 (Thyer et al., 2026).

---

## 1. Retitled and reframed the SI's top-level section

**File:** `chapter2goethite_SI_body.tex`

**Before:**
```
\section{Analytical Methods for Permeation Lag Corrections using the Na\"ive Bracketing Method for the Encapsulated, Irradiated Win-06-01b Step Heat Experiment}
\label{sec:ch2-si-detailed-methods}

\textit{Ben J. Thyer, California Institute of Technology, October 2024}

\subsection{Summary}
```

**After:**
```
\section{Supplementary Verification: The Na\"ive/Informed Bracketing Method for the Encapsulated, Irradiated Win-06-01b Step Heat Experiment}
\label{sec:ch2-si-detailed-methods}

\textit{Ben J. Thyer, California Institute of Technology, October 2024}

This supplement documents the na\"ive/informed bracketing method: an independent, more heavily-reduced treatment of the HT-Win-06-01b dataset that explicitly tracks the helium content of the ampoule step by step, rather than bounding it as in the main text's ``treatment as uncertainty'' approach (\S\ref{experimental-methods}, \S\ref{analytical-methods}). It is retained here solely as a secondary, independent verification of the main text's results and conclusions, not as the primary basis for them: where the two methods' distilled datasets and derived quantities agree, this corroborates the main text's simpler, more easily justified treatment. The isothermal permeation-fit methodology that establishes the ampoule's elevated permeability -- the evidentiary basis for the main text's conservative literature-permeability assumption -- is summarized in the main text (\S\ref{experimental-methods}) and detailed in full here (\S\ref{nauxefve-apparent-lambdas-permeability-coefficient-description-and-methods}).

\subsection{Summary}
```

**Reasoning:** The old title named the SI after the bracketing method already, but didn't say *why* a reader should care about it relative to the main text, and the label preceding it (`sec:ch2-si-detailed-methods`, referenced from the main text) is unchanged so the existing forward-pointer still resolves. The new opening paragraph states the SI's demoted, secondary role explicitly and points both directions — forward to where the shared permeability methodology now lives in the main text, and to where the rest of this section's own detail still is.

---

## 2. Added the isothermal 3He permeation-fit evidence to the main text

**File:** `chapter2_body.tex` (within "Experimental Methods")

This is the load-bearing piece: without it, the main text's claim that "literature permeability values underestimate the true value" (and are therefore conservative for the bound calculation) rested only on assertion, not evidence.

**Before** (the paragraph ended here, then jumped straight to applying the bound):
```
to calculate an upper bound constraint of the helium content of the ampoule, and lower permeabilties produce more 
conservative (higher) upper bound constraints. 

For simplicity, a conservative $\lambda t$ (where $\lambda = GRTK$) is estimated here using the 4He
permeability \emph{K} reported by Swets et al., 1961, while the 3He 
permeability is taken to be the product of the 4He permeability and the 3He/4He permeability ratio
reported by Jones, 1953. The geometric constant \emph{G} is calulated using the measured inner and
outer diameter of the ampoule (Fig.~\ref{fig:ch2-ampoule-dims}).
```

**After:**
```
to calculate an upper bound constraint of the helium content of the ampoule, and lower permeabilties produce more
conservative (higher) upper bound constraints.

A linear regression of ln($K$) against inverse temperature (Fig.~\ref{fig:ch2-naive-arrhenius}) fit to these isothermal
3He permeation measurements over 90-110°C yields an R\textsuperscript{2} of 0.936 and an activation energy of
10190$\pm$1880 (2 s.e.) cal/mol, a factor of two higher than expected for pure silica glass with or without water
\citep{masaryk1968,shelby1972}, but similar to glasses with a high abundance of network-modifying cations such as
Na, K, Pb, or Li \citep{norton1953,altemose1961}. This elevated permeability runs counter to expectations for a
hydrothermal experiment: hydration of silica glass is generally reported to slow helium permeation at all
temperatures \citep{tsuru2011}, under the common paradigm that ions such as (OH)\textsuperscript{-} clog interstitial
space within the amorphous glassy network to slow permeation and decrease helium solubility
\citep{norton1953,shackelford1999}. The same elevated permeability was independently observed at 100°C in a separate
silica glass ampoule at Caltech partially filled with MilliQ water and equilibrated with \textasciitilde0.1 torr of
tank helium. Because 4He signals during these isothermal steps were blank-level (\S\ref{helium-4-blank-corrections}),
only the ampoule's 3He permeability could be measured directly this way; the isothermal fitting procedure itself is
described in full in the Supplementary Information (\S\ref{nauxefve-apparent-lambdas-permeability-coefficient-description-and-methods}).

For simplicity, a conservative $\lambda t$ (where $\lambda = GRTK$) is estimated here using the 4He
permeability \emph{K} reported by Swets et al., 1961, an anhydrous literature value which this experiment's own
isothermal 3He permeation measurements show to underestimate the ampoule's true (3He) permeability
(Fig.~\ref{fig:ch2-naive-arrhenius}); 4He permeability itself could not be independently measured in this
experiment (\S\ref{helium-4-blank-corrections}). The 3He permeability is instead taken to be the product of the
4He permeability and the relative 3He/4He permeability, taken to be 1.29, the 2$\sigma$ upper bound of the value
measured independently for a water-filled ampoule in Chapter~\ref{ch:apparatus} \citep{thyer2026}: 1.10 $\pm$ 0.19
(2$\sigma$), itself already in excess of the range reported by Jones, 1953 (1.06-1.11 across the relevant temperature
range). The geometric constant \emph{G} is calulated using the measured inner and
outer diameter of the ampoule (Fig.~\ref{fig:ch2-ampoule-dims}).
```

**Reasoning:** The new first paragraph brings over exactly the evidentiary content from the SI's "Naïve Apparent Lambdas" section (the activation-energy regression result and the "this is counter to expectations" discussion), while deliberately leaving behind the *mechanics* of how the fit was done (the 10-series identification, the eqn 3.6a non-linear least-squares procedure, the per-series fit-grid figure) — that stays in the SI as method detail, since per your clarification it isn't itself load-bearing for the main text's argument. The paragraph also states plainly that only 3He could be measured this way, so a reader can't come away thinking 4He permeability was independently constrained here.

**Also fixed a factual error while rewriting the second paragraph:** the old text said Swets 1961's (4He) literature value "is lower than the measured 4He permeability of the ampoule used in this experiment" — but per your clarification, 4He permeability was never measured in this experiment, only 3He. This looks like a copy-paste artifact from an earlier draft. The corrected text ties the comparison to the 3He measurement that was actually made, and explicitly states 4He permeability could not be independently measured. The sentence attributing δ = 1.29 to Chapter 1 was already citing `\citet{thyer2026}` correctly, but I tightened the wording ("measured independently for a water-filled ampoule in Chapter~\ref{ch:apparatus}") so it can't be misread as an in-chapter measurement, and added the Jones 1953 comparison (1.06–1.11) that was previously only in the SI, to reinforce that 1.29 is a deliberately conservative, above-literature choice.

---

## 3. Trimmed the SI's now-duplicated activation-energy paragraph

**File:** `chapter2goethite_SI_body.tex` (within "Naïve Apparent Lambdas...")

**Before:**
```
A linear regression of ln(K) against Inverse temperature (In Kelvin) was
fit for the temperature range 90-110°C with an R\textsuperscript{2}
value of 0.936, yielding an activation energy of 10190±1880 (2 se)
cal/mol, which is a factor of 2 higher than expected for pure silica
glass with or without water \citep{masaryk1968,shelby1972}, but similar
to glasses with high abundance of network modifying cations such as Na,
K, Pb, or Li \citep{norton1953,altemose1961}. Two times the standard error
of the y estimation is taken to be the uncertainty of log permeation
ln(K) when used for permeation lag corrections by the informed
bracketing method.
```

**After:**
```
A linear regression of ln(K) against Inverse temperature (In Kelvin) was
fit for the temperature range 90-110°C with an R\textsuperscript{2}
value of 0.936, yielding an activation energy of 10190±1880 (2 se)
cal/mol (see main text, \S\ref{experimental-methods}, for interpretation
of this value and its comparison to literature). Two times the standard error
of the y estimation is taken to be the uncertainty of log permeation
ln(K) when used for permeation lag corrections by the informed
bracketing method.
```

**Reasoning:** Kept the regression statistic itself (still relevant here since the SI's own uncertainty convention for the informed bracketing method, in the sentence right after, depends on it) and the bracket-specific uncertainty-convention sentence, but removed the literature-comparison interpretation now that it lives in the main text, to avoid two slightly-differently-worded copies drifting apart later.

---

## 4. Removed the SI's "counter to expectations" paragraph (now in main text)

**File:** `chapter2goethite_SI_body.tex`

**Before:**
```
Helium permeation for the hydrothermal experiment appears faster than
anhydrous literature values for helium permeability, at least at
temperatures slightly above 100°C, in contrast with studies that show
that hydration of silica glass slows helium permeation at all
temperatures \citep{tsuru2011} and the common paradigm that ions such
as (OH)\textsuperscript{-} would clog interstitial space within an
amorphous glassy network to slow permeation and decrease helium
solubility \citep{norton1953,shackelford1999}. This same result is also
observed in helium permeability measurements at 100°C taken at Caltech
of a silica glass ampoule partially filled with MilliQ water and
equilibrated with \textasciitilde0.1 torr of tank helium.
```

**After:**
```
The main text (\S\ref{experimental-methods}) discusses why this elevated apparent permeability is notable and how it motivates the conservative treatment of literature permeability values used there; the isothermal fits above are the direct evidentiary basis for that discussion.
```

**Reasoning:** This paragraph moved to the main text essentially verbatim (see change #2) since it's the "not obvious, counter to expectations" argument you flagged as the load-bearing point. Left a one-line pointer rather than deleting silently, so a reader working through the SI top-to-bottom isn't left wondering where the interpretation went.

---

## 5. Trimmed the SI's duplicated "Diffusivities" section

**File:** `chapter2goethite_SI_body.tex`

**Before:**
```
are tabulated to the right of the sheet. For the 3He diffusivities, a
linear regression was fit to the steps with cumulative 3He fractional
yield $\geq$7\% (\ChTwoN\ points for the central, ``M,'' treatment), giving
an R2 statistic of \ChTwoRtwo. No uncertainty on the total amounts of 3He and 4He is propagated into the diffusivities
because the experiment operated at low cumulative yields where this
error affects all diffusivities nearly homogeneously, so it is only
relevant for the y-intercept of the regression and the corresponding
calculated closure temperature. In both cases, the uncertainty from the
intercept and slope parameters of the linear regression is significantly
larger than the uncertainty related to the total yield, so it is
neglected. Applying the upper and lower bounds of the total yield for
3He does not affect the R2 statistic of the linear regression.
```

**After:**
```
are tabulated to the right of the sheet. The Stage 1 reference-line linear regression (Fig.~\ref{fig:ch2-arrhenius-zoom}),
its statistics, and the treatment of total-yield uncertainty in the regression are described in the main text
(\S\ref{analytical-methods}); the same regression underlies both the main text's treatment-as-uncertainty results
and the naive-bracketing dataset reported here.
```

**Reasoning:** This section had already accumulated the same Stage 1 regression description (R², n-points) that the main text's "Analytical Methods" section gives in full — a side effect of an earlier session's fix for a stale R²/step-count figure. Rather than maintain two copies of the same regression description, this points to the single copy in the main text and clarifies that it's a shared regression, not a bracketing-method-specific one.

---

## 6. Annotated the SI's "Totals" section

**File:** `chapter2goethite_SI_body.tex`

**Before:**
```
\section{Totals}\label{totals}

For the final step, the glass ampoule was broken and the remainder of
```

**After:**
```
\section{Totals}\label{totals}

The main text (\S\ref{experimental-methods}) already summarizes this final furnace-fusion step and its blank/re-extract
corrections; the additional spreadsheet-level detail below (volume-split calibration, standard-averaging convention)
is retained here for completeness. For the final step, the glass ampoule was broken and the remainder of
```

**Reasoning:** Unlike "Diffusivities," this section has some detail (volume-split calibration, the twice-measured-standard averaging convention) not already in the main text's narrative version of the same step, so it wasn't trimmed — just annotated so a reader understands why it looks similar to a passage they already read.

---

## 7. Rewrote the main text's forward-pointer to the SI

**File:** `chapter2_body.tex` (end of "Experimental Methods," after the SEM sub-study)

**Before:**
```
Detailed analytical methods for reducing the raw helium measurements of HT-Win-06-01b--- including the raw data corrections, permeation lag corrections for \textsuperscript{3}He and \textsuperscript{4}He, the na\"ive bracketing approach used to independently constrain ampoule permeability, the finite-difference cooling-tube model used to assess the contribution of the cooling period to apparent permeability, and the final resistance-furnace degassing step---are provided in the Supplementary Information (\S\ref{sec:ch2-si-detailed-methods}).
```

**After:**
```
The full isothermal-permeation-fit methodology underlying the permeability values used above, the finite-difference cooling-tube model used to assess the contribution of the cooling period to apparent permeability, and the resistance-furnace degassing step are detailed further in the Supplementary Information (\S\ref{sec:ch2-si-detailed-methods}). That same supplement also records, as a secondary and independent verification of the results and conclusions presented here, the na\"ive/informed bracketing method: an alternative, more heavily-reduced treatment of this dataset that explicitly tracks the ampoule's helium content step by step rather than bounding it as above.
```

**Reasoning:** The old sentence listed "the naïve bracketing approach used to independently constrain ampoule permeability" as one item among several pieces of method detail parked in the SI — which undersold its role and didn't distinguish it from the genuinely supplementary items (raw data corrections, cooling-tube model). The new version splits this into two sentences: one for the remaining pure-methodology detail, and one that explicitly names the bracketing method as a secondary verification exercise, matching its new framing at the top of the SI.

---

## Verification

- No duplicate `\label{}` keys between `chapter2_body.tex` and `chapter2goethite_SI_body.tex` (checked via grep).
- `dissertation.tex` recompiled twice (to stabilize cross-references): 173 pages, zero undefined `\ref`/`\eqref` warnings in the log.
- Confirmed via `pdftotext` that the new main-text paragraph (activation energy, "counter to expectations" language, corrected 3He/Chapter-1 attribution) and the new SI section title ("Supplementary Verification: The Naïve/Informed Bracketing Method") render correctly in the compiled dissertation PDF.
- `chapter2goethite.tex` (standalone chapter draft) and `chapter2goethite_SI.tex` (standalone SI draft) both compile without fatal errors. Both still carry a **pre-existing, unaddressed** limitation: since neither standalone draft `\input`s the other (or Chapter 1), any cross-reference from one into the other -- including several already there before this pass (`eq:steadystate`, `ch:apparatus`, `fig:ch2-n0-grid-errors`, `sec:ch2-si-detailed-methods`) and now also my two new `\S\ref{experimental-methods}`/`\S\ref{analytical-methods}` pointers in the SI -- renders as an undefined reference in that isolated build. This only affects the standalone review copies, not the combined dissertation build, and was flagged rather than fixed per our discussion; happy to wire this up if you want those standalone copies to compile cleanly on their own.

## Not yet done (out of scope for this pass, left for your review)

- "Summary" and "Raw Data and Corrections" sections of the SI were not trimmed -- they read as general instrumental background rather than bracketing-method-specific or duplicative, so I left them as-is pending your read-through.
- The `\paragraph{Profiling Radiogenic Helium Loss...}` discussion in the main text's Discussion section (the bulk-normalized 4He/3He ratio spectra plot) was already main-text content, not SI content, so it needed no move -- flagging only so it's clear I checked.

---

# Addendum (2026-07-27): Equation Profiling and Lambda-Fit Standardization

Date: 2026-07-27
Files touched: `Chapter2/Workspace/chapter2_body.tex`, `Chapter2/Workspace/chapter2goethite_SI_body.tex`, `Chapter2/Workspace/Figures/fig_naive_isothermal_fits.py`, `Chapter2/Workspace/Figures/write_chapter2_macros.py`, `Chapter2/Workspace/Figures/run_all_figures.py`, `Chapter1/Paper/chapter1_body.tex`
Builds verified: `Chapter1/Paper/TubeMethodPaper.tex` (29 pages, clean), `chapter2goethite.tex` (31 pages), `chapter2goethite_SI.tex` (19 pages), `dissertation.tex` (173 pages, zero undefined `\ref`/`\eqref` warnings)

## Why

Two requests: (1) audit every equation in Chapter 2 (main text + SI) and make sure it's either a real `\eqref` to a Chapter 1 equation or a properly labeled Chapter-2-internal equation with a descriptive name -- several were pseudo-numbered by hand (e.g. "eqn. 3.3b1", "1.9a", "eqn 4.4a") with no real `\label`/`\eqref` wiring, a holdover from the original Word/pandoc conversion. (2) Chapter 2's isothermal-lambda fit used a different fitting equation than Chapter 1's; you asked to standardize on one, leaning toward Chapter 1's version since it's "more explicit," and accepted that this would mean redoing Chapter 2's isothermal fits (while confirming this can't affect the actual step-heat data reduction, since these fits only justify the K\textsubscript{obs} > K\textsubscript{lit} assumption).

## 1. Converted four hand-numbered pseudo-equations to real labeled equations

**File:** `chapter2goethite_SI_body.tex`

| Old pseudo-tag | New label | What it is |
|---|---|---|
| eqn. 3.3b1 | `eq:ch2-longcool` | altered $n_0$ form for permeation steps that cooled >26 min before measurement |
| 1.9a | `eq:ch2-kcold` | Eq.~naive solved for $K$, used to determine $K_\mathrm{cold}$ |
| (4.4) | `eq:ch2-4he-nss` | steady-state $n_{ss}$ in terms of $\Omega/\lambda$ |
| 4.4a | `eq:ch2-4he-ratio` | $n_t^{4He}$ estimated from the measured $m^{4He}/m^{3He}$ ratio and $K_3/K_4$ |

Each was converted from a bare `\[...\]` display with a hand-typed `\#(...)` comment tag into a real `\begin{equation}...\label{...}\end{equation}`, which the `memoir`-based class auto-numbers as "(2.x)" per the chapter-numbering convention already confirmed elsewhere in this document. All ~9 back-references to these tags elsewhere in the SI (e.g. "using eqn. 3.3b1", "Eqn. 4.4a is solved in...") were updated to `Eq.~\eqref{...}` so they track the label instead of a hand-typed number that could drift.

**Left alone:** the enumerated 4-scenario list and its 4 corresponding $\omega_4/\omega_3$ formulas in the main text's new "Analytical Methods" section (the isotope-ratio-bound derivation you wrote yourself) were left as unlabeled `\begin{enumerate}` items -- they're self-contained, not cross-referenced from anywhere else, and forcing them into 4 more numbered display equations seemed like it would clutter the section rather than clarify it. The cooling-rate quadratic fit in the "Finite Difference Diffusion Model of Cooling Tube" subsection was also left as an unlabeled `\[...\]` display for the same reason (it's a one-off empirical fit specific to this cooling model, not referenced elsewhere). Flagging both so you can override if you'd rather they were numbered too.

**Also fixed in passing:** the main text's own new "Analytical Methods" section had reintroduced the same factual error already fixed in change #2 of the section above -- "The 4He permeability is thus conservatively taken to be identical to \citet{swets1961}, which is lower than the measured 4He permeability of the ampoule used in this experiment" -- and cited the $\delta$=1.29 value as `(\citet{thyer2026})` rather than `Eq.~\eqref{eq:steadystate}`/`\citep{}`. Both were corrected the same way as before (4He was never independently measured in this chapter; the 1.29 value comes from Chapter 1's water-filled-tube measurement), and the bare inline `$n_{ss} = \frac{m}{\lambda t - 1}$ (\citet{thyer2026})` was changed to point at Chapter 1's actual `Eq.~\eqref{eq:steadystate}`.

## 2. Standardized Chapter 2's isothermal-lambda fit on Chapter 1's equation

**Recommendation and why:** Chapter 1's `Eq.~\eqref{eq:incyield}` (the individual-measurement, non-cumulative form) is the better choice, per your instinct -- and it turns out Chapter 2's own analysis code (`diffusion_utils.py`, present in both chapters' `Figures/` folders) already contains a function that implements exactly this idea (`forward_permeate1`), it just wasn't wired up to `fig_naive_isothermal_fits.py`, which was instead fitting the plain cumulative form (`forward_permeate`, Chapter 1's `Eq.~\eqref{eq:cumyield}`) directly -- the biased form both chapters' text warn against. The SI's prose described its own from-scratch bias-corrected derivation ("eqn 3.6a") that was never actually connected to the fitting script, so the reported Ea/R² weren't reproducible from any code that actually ran.

**Bug found and fixed along the way:** while confirming that `forward_permeate1` really is algebraically identical to Chapter 1's `Eq.~\eqref{eq:incyield}`, I found that `chapter1_body.tex`'s displayed equation for `eq:incyield` doesn't match either the code or its own surrounding prose:

Before (line 196 of `chapter1_body.tex`):
```
m_{i + 1} = n_{0}\left( 1 - e^{- \lambda t_{i + 1}} \right)\ \bullet \prod_{j = 1}^{i}\left( 1 - e^{- \lambda t_{j}} \right)
```
This is a *product* of terms -- but the paragraph right above it describes an increment (this measurement's cumulative yield minus the previous measurement's), and `diffusion_utils.py`'s `forward_permeate1` (present in *both* Chapter 1's and Chapter 2's `Figures/` folders, unchanged) computes exactly that *difference*, not a product:
```python
def forward_permeate1(t, lamb, n0):
    return (n0 * (1 - np.exp(-lamb * t[1]))) - (n0 * (1 - np.exp(-lamb * t[0])))
```
I corrected the displayed equation to match the code and the prose:
```
m_{i + 1} = n_{0}\left( 1 - e^{- \lambda t_{i + 1}} \right) - n_{0}\left( 1 - e^{- \lambda t_{i}} \right)
```
This looks like a transcription artifact from the original Word/pandoc conversion (a subtraction rendered as a bullet-product). I fixed it directly in `chapter1_body.tex` since it's the shared body file for both the standalone Tube paper and the dissertation chapter, and the surrounding prose and actual code leave no ambiguity about which form is correct -- but since Chapter 1 is your more mature, already-drafted chapter, please double check this rendered correctly in both `TubeMethodPaper.pdf` and the dissertation before treating it as final.

**`fig_naive_isothermal_fits.py` rewritten** to actually fit `forward_permeate1` (weighted by each measurement's own uncertainty via `scipy.optimize.curve_fit`'s `sigma` argument) instead of `forward_permeate`, and to compute the Arrhenius regression with `scipy.stats.linregress` (giving real R²/stderr) instead of a bare `np.polyfit` (which gave neither -- meaning the previously-reported "R²=0.936, Ea=10190±1880 cal/mol" wasn't actually reproducible from any code that ran). Re-running the corrected fit gives:

- Ea = 10192 ± 1882 (2 s.e.) cal/mol, R² = 0.936, n = 10 sequences (vs. the old hardcoded 10190 ± 1880, R² = 0.936 -- nearly identical, meaning the bias from the wrong model was small for this dataset, but the pipeline is now genuinely reproducible from code rather than a stale hand-typed number).
- The load-bearing conclusion (measured K > literature K, motivating the conservative bound assumption) still holds at every temperature: K\textsubscript{meas}/K\textsubscript{lit} = 1.11 at 90°C, 1.35 at 100°C, 1.63 at 110°C.

**New reproducible macro pipeline for these numbers**, mirroring the Stage 1 Ea/Tc macros from the section above: `write_chapter2_macros.py` now also reads `data/naive_lambda_arrhenius_cache.json` (written by `fig_naive_isothermal_fits.py`) and emits `\ChTwoPermEa`, `\ChTwoPermEaErr`, `\ChTwoPermRtwo`, `\ChTwoPermN`. Both the main text (Experimental Methods) and the SI ("Naïve Apparent Lambdas") now cite these macros instead of the hand-typed "10190±1880 cal/mol, R² of 0.936." `run_all_figures.py` was reordered so `fig_naive_isothermal_fits.py` runs right after `prepare_regression_cache.py` and before `write_chapter2_macros.py` (previously the macro script ran before any `fig_*.py` script, which would have made it fail or go stale the first time someone re-ran the full pipeline from scratch).

**SI's "eqn 3.6a" derivation removed**, replaced with a short paragraph pointing at Chapter 1's `Eq.~\eqref{eq:incyield}` and explaining the standardization, plus the correct initial-guess value for $\lambda$ (the SI said $6\times10^{-5}$ s$^{-1}$; the actual code's default is $6\times10^{-6}$ s$^{-1}$ -- fixed to match). The per-series fit-grid figure caption and one remaining "function 3.6a" reference were updated to `Eq.~\eqref{eq:incyield}` as well.

## Verification

- `data/naive_lambda_arrhenius_cache.json` regenerated by the corrected script; `write_chapter2_macros.py` re-run and `chapter2_derived_values.tex` regenerated with the new macros populated correctly.
- Numerically checked K\textsubscript{meas} > K\textsubscript{lit} at 90/100/110°C from the new regression (see above) -- the assumption the whole isothermal-fit exercise exists to justify still holds under the corrected model.
- Recompiled `Chapter1/Paper/TubeMethodPaper.tex`, `chapter2goethite.tex`, `chapter2goethite_SI.tex`, and `dissertation.tex`. All four build without fatal errors. `dissertation.tex` (173 pages) shows zero undefined `\ref`/`\eqref` warnings for any of the equation labels touched in this pass (`eq:ch2-longcool`, `eq:ch2-kcold`, `eq:ch2-4he-nss`, `eq:ch2-4he-ratio`, `eq:steadystate`, `eq:incyield`, `eq:cumyield`).
- **Could not verify bibliography/citation resolution this session** -- this sandbox environment doesn't currently have a working `biber` install (a change from earlier in this session), so all four builds show "wrong format version" warnings on their `.bbl` files and every `\citep`/`\citet` renders as an undefined citation. This is a pre-existing tooling gap unrelated to the content edits above (confirmed: zero non-citation `\ref` warnings), but means the compiled PDFs' *citation superscripts/author-year text* couldn't be visually re-verified this pass. Worth re-running biber next time it's available to regenerate clean `.bbl` files.
- **New finding, not yet acted on:** `chapter1_body.tex` and `chapter2_body.tex` both use the exact same hand-typed section labels (`\label{experimental-methods}`, `\label{analytical-methods}`, `\label{results}`, `\label{discussion}`), which `dissertation.tex` flags as "multiply defined" -- meaning any `\ref{experimental-methods}`-style cross-reference (including several I added/edited this pass, and some pre-existing ones) silently resolves to whichever chapter's occurrence LaTeX saw last, not necessarily the one intended. This predates this session's edits and wasn't part of what you asked me to fix, but it's a real latent bug worth namespacing (e.g. `ch1-experimental-methods` / `ch2-experimental-methods`) before relying on those cross-references for a final version.

---

# Addendum 2 (2026-07-27): Removed a Redundant Equation, Narrowed the SI to the Naïve Dataset Only

Date: 2026-07-27
Files touched: `Chapter2/Workspace/chapter2_body.tex`, `Chapter2/Workspace/chapter2goethite_SI_body.tex`
Builds verified: `chapter2goethite.tex` (35 pages, up from 31), `chapter2goethite_SI.tex` (13 pages, down from 19), `dissertation.tex` (170 pages, down from 173, zero undefined non-citation `\ref`/`\eqref` warnings, same pre-existing 4 multiply-defined labels as before -- no new ones introduced)

## Why

Two things prompted this pass. First: you pointed out that the SI's "eqn 4.4" (`eq:ch2-4he-nss`, $n_{ss}=\Omega/\lambda=\omega/(\lambda t)$) looked identical to Chapter 1's already-established `Eq.~\eqref{eq:steadystate}` ($n^{ss}\le m/(\lambda t-1)$) -- worth checking carefully rather than taking at face value, since the two aren't *literally* the same expression. Second, and the larger piece of this pass: you want the SI narrowed further, so it covers only the na\"ive/informed bracketing dataset and its bespoke, step-by-step corrections -- with the entire isothermal-lambda-fitting exercise (including the cumulative-yield grid plots and the cooling-period numerical model) moved into the main text, where the load-bearing evidentiary argument (measured K > literature K) already lives.

## 1. Checked whether `eq:ch2-4he-nss` and `eq:steadystate` are really the same, and consolidated

**Verification:** they are closely related but not algebraically identical as written. `eq:steadystate` is an *upper bound* expressed in terms of the measured value $m$, incorporating the conservative assumption that the ampoule's helium content at the start of the step is $\ge 0$: $n^{ss} \le m/(\lambda t-1)$. `eq:ch2-4he-nss` was an *exact* flux-balance identity expressed in terms of the sample's true helium production $\omega$: $n_{ss}=\Omega/\lambda=\omega/(\lambda t)$. They coincide only in the same long-step, $\lambda t \gg 1$ limit that the surrounding SI text was already invoking one paragraph later (where $\omega \approx m$ is argued to hold) -- at which point the "$-1$" in `eq:steadystate`'s denominator becomes negligible and the two expressions converge. So: you were right that this was a redundant, less-careful restatement of machinery Chapter 1 already established, just not literally interchangeable notation-for-notation.

**Fix:** removed the separately-labeled `eq:ch2-4he-nss` equation entirely. The derivation in `chapter2goethite_SI_body.tex`'s "Permeation Lag Corrections for 4He" subsection now explicitly builds on `Eq.~\eqref{eq:steadystate}` (Chapter~\ref{ch:apparatus}), stating that its long-step limit is what's being invoked, rather than re-deriving a near-duplicate from scratch. The rest of that subsection (the isotope-ratio manipulation and the final `eq:ch2-4he-ratio`, which *is* a genuinely new, chapter-2-specific result actually used in the spreadsheet) is unchanged.

**Before:**
```
This approach utilizes the
steady state \(n_{t}\) value \(n_{ss}\), which can be calculated for any
long high temperature experimental step where the helium source is
assumed constant and the permeation coefficient is known.

\begin{equation}
n_{ss} = \frac{\Omega}{\lambda} = \frac{\omega}{\lambda t}
\label{eq:ch2-4he-nss}
\end{equation}

Taking the ratio of the steady state abundances for 3He and 4He within
the ampoule:
```

**After:**
```
This approach utilizes the
steady-state \(n_{t}\) value \(n_{ss}\) already established in
Chapter~\ref{ch:apparatus}: for any long high-temperature experimental
step where the helium source is assumed constant and the permeation
coefficient is known, Eq.~\eqref{eq:steadystate} gives
$n^{ss} \le m/(\lambda t - 1)$, which for these long steps
($\lambda t \gg 1$) is well approximated by $n^{ss} \approx \omega/(\lambda t)$,
the exact steady-state balance between the sample's helium production
rate $\Omega$ and permeative loss ($n^{ss}=\Omega/\lambda$, with
$\omega = \Omega t$ the total production over the step).

Taking the ratio of the steady state abundances for 3He and 4He within
the ampoule:
```

## 2. Moved the entire isothermal-lambda-fit exercise from the SI into the main text

**Files:** `chapter2_body.tex` (Experimental Methods), `chapter2goethite_SI_body.tex`

Previously, the main text carried only a condensed evidentiary summary (the activation-energy regression result and the "counter to expectations" discussion, moved in an earlier pass), while the SI's "Na\"ive Apparent Lambdas" section held the actual methodology: the 10-series identification, the `Eq.~\eqref{eq:incyield}` curve-fitting procedure, the initial-guess values, the `NaiveIsothermalFits_Grid.pdf` per-series fit figure, and (as a separate nested subsection) the finite-difference cooling-tube numerical model with its own two figures (`goethite_cooling_rate_fit.pdf`, `goethite_n0_grid_errors.pdf`) and three discussion paragraphs. All of that methodology -- everything from "10 series of 3-4 consecutive permeation steps..." through the cooling-model's closing paragraph ("...supporting the validity of this approach.") -- moved into `chapter2_body.tex`, inserted at the point where the main text already gestured at it (right after "...as described in the naive method outlined by Thyer et al., 2026" and before the pre-existing "All measured apparent permeabilities were equal to or in excess of the literature values..." sentence, with the cooling-tube-model content following as its own `\paragraph{Finite Difference Diffusion Model of Cooling Tube}`).

All figure labels (`fig:ch2-naive-cumulative-yield`, `fig:ch2-goethite-cooling-rate`, `fig:ch2-n0-grid-errors`) and the subsection label (`finite-difference-diffusion-model-of-cooling-tube`) moved with their content -- each now defined exactly once, in `chapter2_body.tex`, confirmed by grep before recompiling (no duplicate-label warnings resulted from the move). The two "(Fig.~..., supplementary material)" qualifiers in the main text's pre-existing cooling-period sentence, which pointed at the SI copy of `fig:ch2-n0-grid-errors`, became unnecessary once the figure is embedded locally and were folded into the fuller replacement text instead of left dangling.

The main text's SEM-paragraph forward-pointer, which previously said "The full isothermal-permeation-fit methodology ... are detailed further in the Supplementary Information," was rewritten since that's no longer true -- it now only points to the SI for the resistance-furnace degassing step (\S\ref{totals}) and frames the na\"ive/informed bracketing method as building on the (now-local) isothermal-permeability fits, rather than as an independent parallel methodology section.

## 3. Trimmed the SI's "Na\"ive Apparent Lambdas" section down to just the dataset

**File:** `chapter2goethite_SI_body.tex`

**Before** (section title and opening; ~120 lines of methodology, two figures, and an Arrhenius restatement followed before reaching the actual data):
```
\section{Naïve Apparent Lambdas (Permeability Coefficient)
Description and
Methods}\label{naive-apparent-lambdas-permeability-coefficient-description-and-methods}

Although helium permeability of silica glass is generally well studied
for dry conditions, it is a function of water content ...
[... 10-series identification, Eq.~\eqref{eq:incyield} fit description,
initial guess, goethite_n0_grid_errors.pdf figure, Arrhenius regression
restatement, NaiveIsothermalFits_Grid.pdf figure ...]

\subsubsection{Naïve-Method Step-Heat Dataset}\label{ch2-si-distilled-naive}
```

**After:**
```
\section{Na\"ive-Method Isothermal Permeability Dataset}\label{naive-apparent-lambdas-permeability-coefficient-description-and-methods}

The effective permeability coefficients used by the informed bracketing method below -- and the isothermal-permeation-fit methodology, cooling-tube numerical model, and Arrhenius regression used to determine them -- are described in full in the main text (\S\ref{experimental-methods}). The complete fitted dataset underlying that regression is reported here.

\subsection{Na\"ive-Method Step-Heat Dataset}\label{ch2-si-distilled-naive}
```

The label (`naive-apparent-lambdas-permeability-coefficient-description-and-methods`) is unchanged so nothing referencing this section by name breaks; only the visible title and content shrank. The distilled step-heat dataset subsection (now promoted from `\subsubsection` to `\subsection`, since it's essentially the section's only remaining content) and its three data tables are otherwise untouched.

Similarly, the SI's "Finite Difference Diffusion Model of Cooling Tube" subsection (its own methodology, two figures, and three discussion paragraphs) was replaced with a single pointer sentence:
```
The finite-difference numerical model used to evaluate the contribution of the 26-minute cooling period to these apparent permeabilities -- and to confirm that the ampoule's markedly elevated permeability is not an artifact of that cooling history -- is described in full in the main text (\S\ref{finite-difference-diffusion-model-of-cooling-tube}).
```
This reuses the exact same label as the (now sole) copy of this content in the main text -- necessary, since keeping a second `\label{finite-difference-diffusion-model-of-cooling-tube}` in the SI would have collided with the new main-text one.

## 4. Rewrote the SI's top-level scope statement

**File:** `chapter2goethite_SI_body.tex`

**Before** (last sentence of the opening paragraph):
```
The isothermal permeation-fit methodology that establishes the ampoule's elevated permeability -- the evidentiary basis for the main text's conservative literature-permeability assumption -- is summarized in the main text (\S\ref{experimental-methods}) and detailed in full here (\S\ref{naive-apparent-lambdas-permeability-coefficient-description-and-methods}).
```

**After:**
```
This supplement covers only the na\"ive/informed bracketing dataset and the bespoke, step-by-step corrections applied to it (\S\S\ref{raw-data-and-corrections-columns}--\ref{totals}); the isothermal-permeation-fit methodology and cooling-tube numerical model that establish the ampoule's elevated permeability -- the evidentiary basis for the main text's conservative literature-permeability assumption, and a prerequisite for the corrections applied below -- are described in full in the main text (\S\ref{experimental-methods}), not here.
```
This directly states the SI's narrowed scope (no more "summarized... and detailed in full here" split -- the methodology lives only in the main text now) rather than leaving a reader to infer it from the section-by-section content.

## 5. Two small equation-reference cleanups found along the way

**File:** `chapter2goethite_SI_body.tex`

While re-reading the "Raw Data" and "Helium-4 Blank Corrections" subsections (untouched by the larger move above, but adjacent to it), found two more vague, un-linked equation references left over from the original conversion, in the same spirit as the "eqn 3.3b1"/"1.9a"/"4.4"/"4.4a" ones fixed in the addendum above:
- `"{[}supp. EQN 1.9 with log permeability...{]}"` -> now cites `Eq.~\eqref{eq:naive}` (Chapter~\ref{ch:apparatus}) directly, since that's the decay equation actually being evaluated at $K$=23.88 ln(atoms/cm·atm·s).
- `"(Supp. EQN 3.6)"` -> now cites `Eq.~\eqref{eq:cumyield}` (Chapter~\ref{ch:apparatus}) directly, matching how every other mention of this same cumulative-permeation equation elsewhere in this document already cites it.

## Verification

- Grepped for the figure filenames (`NaiveIsothermalFits_Grid.pdf`, `goethite_cooling_rate_fit.pdf`, `goethite_n0_grid_errors.pdf`) and their labels (`fig:ch2-naive-cumulative-yield`, `fig:ch2-goethite-cooling-rate`, `fig:ch2-n0-grid-errors`, `finite-difference-diffusion-model-of-cooling-tube`) across both files before recompiling: each `\includegraphics`/`\label` now appears exactly once, in `chapter2_body.tex` only.
- Recompiled `chapter2goethite.tex` (31 -> 35 pages, gained the moved content), `chapter2goethite_SI.tex` (19 -> 13 pages, lost the moved content), and `dissertation.tex` (173 -> 170 pages -- net negative since the duplicated figures/discussion that used to appear in both the SI and a condensed main-text form now appear only once, more fully, in the main text).
- `dissertation.tex` shows zero undefined non-citation `\ref`/`\eqref` warnings for any label touched in this pass, and the same 4 pre-existing multiply-defined labels as before (`experimental-methods`, `analytical-methods`, `results`, `discussion`) -- confirming this pass didn't introduce any new label collisions.
- Same bibliography caveat as the addendum above: this sandbox's `biber` is still unavailable, so citation rendering couldn't be visually re-verified, only the non-citation cross-references (which is what this pass actually touched).

---

## Addendum 3 (2026-07-27): Fine-Scale Copy-Edit Pass (Typos, Grammar, Citation Formatting, Clarity)

**Files:** `chapter2_abstract.tex`, `chapter2_body.tex`, `chapter2goethite_SI_body.tex`

**Why:** Ben asked for a full read-through of the Chapter 2 body and SI looking for typos, grammatical errors, missing/misformatted citations, unfinished sentences, and opportunities to improve clarity. This addendum documents every change made in that pass. Nothing here is a scientific/content change — content, equations, figures, and data tables are untouched.

### Abstract (`chapter2_abstract.tex`)
- "uncertainty persists under which mineralogical..." -> "uncertainty persists regarding the mineralogical and environmental conditions under which..." (the original sentence's grammar didn't parse; "persists under which" isn't valid English).
- "dehydration-induced helium loss raising questions about their relevance helium retention" -> "...raising questions about their relevance **to** helium retention..." (missing word).
- "led **me** to develop" / "Using this method, **I** report" -> "led **us**"/"**we** report", matching the "we" convention used throughout `chapter2_body.tex` and the SI (per the earlier "switch first-person I to We" pass) -- the abstract had been missed by that earlier conversion.

### Unfinished sentence (`chapter2goethite_SI_body.tex`, Permeation Lag Corrections for 4He)
- Found a sentence that was cut off mid-thought: "...the ``3He $n_0$ (pccSTP)'' column. **This value is take**" followed immediately by a new paragraph. The fragment was fully redundant with the sentence immediately preceding it (which already explains where the value comes from), so it was deleted rather than completed.

### Genuine typos (spelling)
- SI: "Flanders Ranges" -> "Flinders Ranges" (matches the abstract and every other mention of this locality).
- SI: "``Cooling Time'' **Is** the difference" -> "is" (stray capital mid-sentence).
- SI: "column **subtracted** 1560 seconds" -> "column **minus** 1560 seconds" (missing preposition).
- SI: "it **is allows** for" -> "it allows for".
- SI: "from **it's** value of $n_0$" -> "from **its** value" (possessive, not contraction).
- SI: "can be found **at after** the final columns" -> "can be found after the final columns".
- SI: "The first of these three **measuremen''s (H'30413)**" -> "measurements (H30413)" (stray quote-mark artifacts).
- SI: "**arrrhenius** plots" -> "Arrhenius plots".
- Body: "**ferruginiztion**" -> "ferruginization" (correctly spelled two sentences later in the same paragraph).
- Body: "collected within float at the **Flinders Range**" -> "Flinders Ranges" (plural, matches every other mention).
- Body: "The **pemeability** of ampoules" -> "permeability"; "sequential isothermal **permation** steps" -> "permeation steps".
- Body: "The geometric constant $G$ is **calulated**" -> "calculated".
- Body: "These measurements are **ommited** from further analysis" -> "omitted".
- Body: "were used to **calculatethe** cooling rate" -> "calculate the cooling rate" (missing space).
- Body: "which is **permissable**" -> "permissible"; "lower **permeabilties**" -> "permeabilities".
- Body: "is most typically applied to **data** surface processes" -> "**date** surface processes" (wrong word -- this sentence is about U-Th/He dating, not data).
- Body: raw-caret frequency-factor notation `(D0/a\^{}2)` and `(Fo = Dt/a\^{}2)` -> converted to `D\textsubscript{0}/a\textsuperscript{2}` and `Dt/a\textsuperscript{2}`, matching the `\textsubscript`/`\textsuperscript` convention used for this same quantity everywhere else in the chapter (e.g. line ~96, ~618).
- Body: duplicated word "on the **the** regression" -> "on the regression"; "excess apparent permeability **permeability**" -> "excess apparent permeability" (duplicated word in a figure caption).
- Body: "This image clearly **showsthat**" -> "shows that" (missing space).
- Body: "Thermo **Fischer** SFT mass spectrometer" -> "Thermo **Fisher**" (matches every other mention of the instrument vendor in this chapter).

### Grammar
- Body: "Months of helium measurements... **has** shown this approach" -> "**have** shown" (subject-verb agreement; "Months" is plural).
- Body: "higher differential permeability between the helium **two isotopes**" -> "the **two helium** isotopes" (word order).
- Body: "**therelative** 3He/4He permeability" -> "the relative 3He/4He permeability" (missing space).
- Body: run-on sentence "...SFT mass spectrometer **A** hot furnace blank..." -> added a period: "...mass spectrometer. A hot furnace blank...".
- Body: duplicated sentence fragment in the dehydration/recrystallization discussion -- "...does not. \newline does not (Figs...)" -- collapsed to a single "...does not (Figs...)." In the same passage, also fixed: "**ocurring**"->"occurring", "**possiblility**"->"possibility", "**occuring**"->"occurring", "**natual**"->"natural", "**aggreagates**"->"aggregates", and the missing-space run-ons "``hidden''**dehydration**" -> "``hidden'' dehydration" and "may **occurbefore**" -> "may occur before".

### Citation formatting (fixing internal inconsistencies only -- not converting the chapter's still-deferred plain-prose citation style to `\citep`/`\citet`, per this file's own header note)
- Body: "Cherniak and Watson, 2011; **Farley 2018**)" -> "Farley, 2018)" (missing comma, inconsistent with the other entries in the same parenthetical list).
- Body: "the models presented by Bassal et al., 2022 suggest" -> "Bassal et al. **(2022)** suggest" (narrative citation needs parentheses around the year).
- Body: "180-135 Ma. \citep{waltenberg2012}." -> removed the stray period before the citation.
- Body: "the results **on** \citet{farley2024} clearly agree well with **Monteiro, 2017**" -> "the results **of** \citet{farley2024}... with \citet{monteiro2017}" (wrong preposition, plus the second half of the same sentence used plain prose for a source cited by `\citet` moments earlier -- `monteiro2017` already exists in `references.bib` and is used this way throughout the rest of the chapter).
- Body: "The experiment in **Farley et al., 2024** was open to..." -> `\citet{farley2024}` (same source is cited via `\citet{farley2024}` twice more in the same paragraph; this was the odd one out).
- SI: "as conservatively measured by **(\citep{thyer2026})**" -> `\citep{thyer2026}` (removed the double parenthesization -- `\citep` already supplies its own parentheses).
- Body: "equilibrated with ~0.1 torr of tank helium **(\citep{thyer2026}), who posit**..." -> "...tank helium, as reported by \citet{thyer2026}, who posit..." (same double-parenthesization bug, plus `\citep` doesn't work grammatically as the subject of "who posit" -- needed the narrative `\citet` form).
- Body, SI, and one figure caption: "Swets et al., 1961 and **Jones, 1954**" -> "Jones, **1953**" (three occurrences, all in the same Arrhenius-plot figure caption; every other mention of this source in both files -- including the actual `\citep{jones1953}` bib key -- uses 1953, so 1954 was a transcription error, not an intentional second source).

### Flagged, not fixed: a genuinely missing reference
Three places (`chapter2_body.tex` lines ~97, ~647, ~1024) cite "Farley and Flowers, 2012" in plain prose for a hematite step-heat study. I checked `references.bib` for a matching entry and confirmed there isn't one (`flowers2007` and `flowers2009` exist but are different papers by different author combinations). Since fabricating a bibliographic entry isn't an option, this citation is left as-is; **Ben should either supply the full reference for a proper bib entry, or confirm the citation should be removed/replaced.**

### Verification
- Re-grepped all `\citep{}`/`\citet{}` keys in both files against `references.bib` after every edit above: zero broken/undefined keys (same clean result as before this pass).
- Recompiled all three builds: `chapter2goethite.tex` (35 pages, unchanged), `chapter2goethite_SI.tex` (13 pages, unchanged), `dissertation.tex` (171 pages -- a 1-page increase from minor rewording, not a content change). No new undefined non-citation `\ref`/`\eqref` warnings, and the same 4 pre-existing multiply-defined labels as always (`experimental-methods`, `analytical-methods`, `results`, `discussion`) -- no new label collisions introduced.
- Same standing caveat: this sandbox's `biber` is still unavailable, so citation *rendering* (as opposed to key validity) couldn't be visually re-verified.

---

## Addendum 4 (2026-07-28): Published the Raw Isothermal Dataset + Per-Sequence Fits as SI Tables

**Files:** `Chapter2/Workspace/Figures/fig_naive_isothermal_fits.py`, `Chapter2/Workspace/chapter2_naive_isothermal_tables.tex` (new, auto-generated), `chapter2goethite_SI_body.tex`, `chapter2goethite_SI.tex`, `Chapter2/chapter2.tex`

**Why:** Ben pointed out that the SI's "Naïve-Method Isothermal Permeability Dataset" section said the underlying data was "reported here," but no table actually carried it -- `NaiveIsothermalFits_Grid.pdf` plots the same data, but the numbers themselves, and each sequence's fitted $\lambda$/$n_0$ (only ever visible as tiny text in that plot's subplot titles), were never tabulated anywhere. Ben added a `DistilledNaiveLambdas` sheet to `Win0601bHT_data_and_reduction.xlsx` -- just the 5 columns needed to publish the raw dataset (Temperature, Nominal Time, Cooling Time, $^3$He measured, $\pm2\sigma$), stripped of the internal bookkeeping columns (`Series ID`, `HeRefNo`, `Name`, `Type`, `Sensitivity`, ...) that the `Naive Apparent Lambdas` sheet carries -- and asked for it to be added to the SI, ideally alongside the fitted $\lambda$/$n_0$ values computed dynamically by the existing Python fitting code rather than hand-transcribed.

### What I found
`fig_naive_isothermal_fits.py` already reads `Naive Apparent Lambdas`, groups it into the 10 isothermal sequences, and fits each one via a weighted non-linear least-squares fit of `forward_permeate1` (the same bias-corrected model as Chapter 1's Eq.~\eqref{eq:incyield}) -- that's exactly the fit whose results needed to be tabulated. I confirmed by direct comparison that `DistilledNaiveLambdas`'s values are numerically identical, row for row and series for series, to the corresponding columns already loaded from `Naive Apparent Lambdas` -- so both sheets describe the same 10 sequences, just with different column sets.

### Design decision: auto-generated `\newcommand` macros, same pattern as `chapter2_derived_values.tex`
Rather than hand-transcribing either table into `chapter2goethite_SI_body.tex` (which is exactly the kind of hand-copying that caused the activation-energy/closure-temperature drift `write_chapter2_macros.py` was built to prevent), both tables are generated by Python and `\input{}` as macros:
- `fig_naive_isothermal_fits.py` now also writes `Chapter2/Workspace/chapter2_naive_isothermal_tables.tex`, defining `\ChTwoNaiveRawTable` (Table 1.1: the raw per-step dataset) and `\ChTwoNaiveFitTable` (Table 1.2: each sequence's fitted $\lambda$/$n_0$ $\pm2\sigma$), each a `\newcommand` whose body is a complete table environment.
- Before generating the raw-data table, the script now also reads `DistilledNaiveLambdas`, groups it by blank-row-separated blocks (it has no `Series ID` column), and asserts it matches the already-loaded `Naive Apparent Lambdas`-derived sequences to the last decimal -- if Ben ever edits one sheet without the other, this raises a loud error rather than silently publishing stale or inconsistent numbers. The raw table itself is built from this cross-checked data.
- `fit_n0_lambda()` was extended to also return $n_0$'s own fit uncertainty (`sqrt(cov[1,1])`) -- previously only $\lambda$'s uncertainty was returned/used, since only $\lambda$ fed the Arrhenius plot; the table needed $n_0$'s uncertainty too, so nothing existing needed to change to add this, only a new return value.
- The `\newcommand`-wrapping (rather than a plain `\input` of raw table text at the point of use) is necessary specifically because `chapter2_derived_values.tex`'s existing pattern only holds preamble-safe scalar macros, and these tables need to appear at a specific point *inside* the shared body file -- whose own `\input` path resolution depends on which wrapper (standalone vs. dissertation) is compiling it. Defining the tables as macros in each wrapper's preamble (mirroring exactly how `chapter2_derived_values` is already handled there) means the shared body can invoke `\ChTwoNaiveRawTable`/`\ChTwoNaiveFitTable` by name, with no path resolution needed at the point of use. (Confirmed separately, with a minimal standalone test file, that a `longtable` environment compiles correctly from inside a `\newcommand` body.)
- `chapter2goethite_SI.tex` and `Chapter2/chapter2.tex` each gained one new `\input` line (immediately after their existing `\input{...chapter2_derived_values}`), loading the new generated file the same way.
- `chapter2goethite_SI_body.tex`'s "Naïve-Method Isothermal Permeability Dataset" section now invokes `\ChTwoNaiveRawTable` and `\ChTwoNaiveFitTable` (with a `\clearpage` between them, since the raw table alone runs ~2 pages) directly after the paragraph that promises "the complete fitted dataset ... is reported here," and that paragraph now names both tables explicitly instead of just gesturing at "here."

### Table contents
- **Table 1.1** (`tab:ch2-naive-isothermal-raw`): Series, Temp (°C), Nominal Time (min), Cooling Time (min), $^3$He measured (pccSTP), $\pm2\sigma$ -- 31 rows across the 10 series, `\midrule`-separated by series (mirroring the blank-row separation already used in the spreadsheet), as a `longtable` (footnotesize) since it runs to 2 pages.
- **Table 1.2** (`tab:ch2-naive-isothermal-fits`): Series, Temp (°C), Duration (min), $n$ (steps), $\lambda$ (s$^{-1}$) $\pm2\sigma$, $n_0$ (pccSTP) $\pm2\sigma$ -- one row per sequence, a single-page `tabular`.
- Both captions cross-reference each other and the existing `NaiveIsothermalFits_Grid.pdf`/`NaiveLambda_Arrhenius.pdf` figures, so a reader can trace a plotted point back to its row in either table.

### Verification
- Ran `fig_naive_isothermal_fits.py` directly: printed `'DistilledNaiveLambdas' cross-check OK: 10 series match 'Naive Apparent Lambdas' exactly` before writing the tables file -- confirming the two sheets currently agree.
- Rendered `chapter2goethite_SI.pdf` pages 8 and 10 to PNG and visually inspected both tables: correctly typeset, series groupings visible, no truncated columns or overflow.
- Recompiled all three builds: `chapter2goethite.tex` (35 pages, unchanged -- these tables only appear in the SI), `chapter2goethite_SI.tex` (13 -> 15 pages), `dissertation.tex` (171 -> 176 pages). Two pdflatex passes on the standalone SI resolved the new tables' own forward-referenced `\ref`s (`tab:ch2-naive-isothermal-raw`/`-fits` are referenced in prose on page 8, before their captions define them on page 10 -- ordinary multi-pass LaTeX behavior, not a bug). No new undefined non-citation `\ref`/`\eqref` warnings anywhere, and the same 4 pre-existing multiply-defined labels as every prior addendum (`experimental-methods`, `analytical-methods`, `results`, `discussion`) -- no new collisions.
- Same standing caveat: this sandbox's `biber` is still unavailable, so bibliography rendering couldn't be visually re-verified (irrelevant here anyway -- this addendum touched no citations).

---

## Addendum 5 (2026-07-28): Converted the Farley & Flowers (2012) Citations Now That a Bib Entry Exists

**File:** `chapter2_body.tex`

**Why:** Addendum 3 flagged three plain-prose "Farley and Flowers, 2012" citations with no backing `references.bib` entry and asked Ben to supply one rather than fabricating it. Ben added `farleyflowers2012` to `references.bib`. This addendum converts all three occurrences to `\citet`/`\citep` against that new key.

- Line ~97 (Introduction): "for hematite (Farley and Flowers, 2012; Farley, 2018), is needed to" -> "for hematite \citep{farleyflowers2012,farley2018}, is needed to". Combined into a single `\citep` with both keys (rather than `\citep{farleyflowers2012}` followed by the still-plain-prose "Farley, 2018") because `farley2018` already has a valid bib entry and is cited via `\citep{farley2018}` dozens of times elsewhere in this chapter -- leaving it as bare prose right next to a freshly-converted `\citep` would have produced an ugly double-parenthetical "(Farley \& Flowers, 2012) (Farley, 2018)" for what was one semicolon-joined citation group in the original.
- Line ~647 (Fig.~\ref{fig:ch2-delta-zoom} caption): "...or r/r0 plots in \citet{lovera1991} and Farley and Flowers, 2012." -> "...\citet{lovera1991} and \citet{farleyflowers2012}." (narrative form, matching the parallel `\citet{lovera1991}` immediately before it).
- Line ~1024 (Fig.~\ref{fig:ch2-fourier-hematite-ref} caption): "...Grand Canyon, Arizona (Farley and Flowers, 2012) and the Gogebic Range, Michigan \citep{farleymckeon2015}..." -> "...Arizona \citep{farleyflowers2012} and the Gogebic Range, Michigan \citep{farleymckeon2015}..." (parenthetical form, matching the immediately adjacent `\citep{farleymckeon2015}`).

### Verification
- Re-grepped all `\citep{}`/`\citet{}` keys in `chapter2_body.tex` and `chapter2goethite_SI_body.tex` against `references.bib`: zero broken/undefined keys, including the new `farleyflowers2012`.
- Recompiled `chapter2goethite.tex` (35 pages, unchanged) cleanly in place. `dissertation.tex`, compiled in place, hit a fatal `! File ended while scanning use of \@writefile` on its `.aux`/`.bcf` files -- these turned out to be truncated at suspiciously round byte counts (e.g. exactly 36864 and 102400 bytes), which is a write/flush limitation of this sandbox's mounted copy of the repository, not a LaTeX content problem. Confirmed by rsync-ing the whole repo to the sandbox's local disk and recompiling there: two clean passes, 177 pages (up 1 from the added words), zero new undefined non-citation references, and the same 4 pre-existing multiply-defined labels as every prior addendum. `farleyflowers2012` appears as an "undefined citation" in the log, same as every other citation key in this sandbox -- the standing `biber`-unavailable caveat, not a broken reference.
- Practical implication: this mount-truncation issue is specific to this remote session's environment and full-dissertation-sized aux/bcf files: it hasn't affected the smaller `chapter2goethite.tex`/`chapter2goethite_SI.tex` builds in any prior addendum. Overleaf or a local TeX install shouldn't hit it, but worth knowing about if a future from-scratch `dissertation.tex` compile in this same kind of remote sandbox errors out the same way -- delete/regenerate the `.aux`/`.bcf`/`.out` family and, if that doesn't help, retry from a local (non-mounted) copy.
