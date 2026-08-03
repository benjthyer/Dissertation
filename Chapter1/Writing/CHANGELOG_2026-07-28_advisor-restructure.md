# Chapter 1 Restructuring — Advisor Feedback Response (2026-07-28)

Context: the advisor's comments were (1) "It is odd and confusing to find methods buried
deep in the paper (Experimental Methods)" and (2) "I am lost in all the details in the
Analytical Methods. Do we need all that material? Might be better to focus on key
datasets and not present everything you did." Ben also wanted the real, uncorrected
Durango apatite data introduced earlier to motivate the permeation lag problem, while
keeping the existing simulated Durango figure that opens the Introduction.

All edits below are in the shared body files (`chapter1_body.tex`,
`chapter1_SI_body.tex`), so they apply identically to both compile targets: the
dissertation chapter and the standalone `TubeMethodPaper.tex`/`SI.tex` journal
manuscript.

Every change was compile-verified against the full dissertation (all cross-references
resolve, no new errors; see the note at the end of this document).

---

## 1. Moved "Experimental Methods" earlier — no longer buried

**Old structure:** Introduction → Theoretical Framework of Permeation Lag →
Experimental Approaches Addressing Permeation Lag (3 subsections) → **Experimental
Methods** → Analytical Methods → Results → Discussion → Conclusions.

Experimental Methods was section 4 of 8 — a reader had to get through two full
sections of equations (the permeation-lag model, then three tractability approaches,
each with their own derivations) before learning anything about what was physically
built or measured.

**Fix:** The entire `\section{Experimental Methods}\label{experimental-methods}` block
was moved to immediately follow the Introduction's closing figure (the simulated
Durango apatite plot), and now precedes Theoretical Framework. No text within the
section was changed — apparatus description, ampoule-prep procedure, helium-loading
procedure, and both mass-spec measurement protocols moved as a unit.

**New structure:** Introduction → **Experimental Methods** → Theoretical Framework of
Permeation Lag (now includes the new real-data teaser figure, see §2 below) →
Experimental Approaches Addressing Permeation Lag → Analytical Methods → Results →
Discussion → Conclusions.

**Why:** This directly answers "methods buried deep" — a reader now hits the real
apparatus in section 2, before any of the theory. It also sets up the real-data teaser
figure (§2): the teaser can now say "the experiment described above" instead of
forward-referencing an experiment the reader hasn't met yet.

---

## 2. Added a real-data "teaser" figure before the theory, right after the simulation

**Old text** (opening paragraph of Theoretical Framework):

> The process of helium permeation through thin walls of an ampoule is rapid but not
> instantaneous on experimental timescales. Helium evolved from encapsulated minerals
> is only available for measurement following permeation through the glass ampoule
> (Fig.~\ref{fig:durango-stepheat-lag-simulation}), producing a predictable
> "permeation lag" effect in helium measurements that commonly manifests with
> undermeasurement of helium during prograde heating sequences and corresponding
> overmeasurement of helium produced during retrograde sequences
> (Fig.~\ref{fig:simulated-arrhenius-lag-artifact}). This effect can be modeled (and
> corrected for) for a system obeying the simple equation:

**Fix:** Inserted one new sentence, followed by a new figure, before that paragraph's
closing transition into the equations:

> ...(Fig.~\ref{fig:simulated-arrhenius-lag-artifact}). **This is not merely a
> theoretical concern: Fig.~\ref{fig:durango-arrhenius-teaser} shows the same artifact
> in real, uncorrected step heat data for the encapsulated Durango apatite experiment
> described above (\S\ref{experimental-methods}); the correction developed below is
> applied to this dataset in full in \S\ref{results} (Fig.~\ref{fig:durango-arrhenius-lag-corrected}).**
>
> \begin{figure}[t]
> \centering
> \includegraphics[width=8.3cm]{encapsulated\_DApErr.pdf}
> \caption{A preview of the real, uncorrected helium step heat data for the
> encapsulated Durango apatite experiment described in \S\ref{experimental-methods}:
> without any correction for permeation lag, apparent diffusivities calculated with
> the equations of \citet{fechtigkalbitzer1966} are erratic and largely
> uninterpretable -- exactly the artifact anticipated by the simulation of
> Fig.~\ref{fig:durango-stepheat-lag-simulation} above. Correcting for permeation lag
> (developed below) recovers a well-behaved Arrhenius array consistent with previously
> reported diffusion parameters for Durango apatite \citep{farley2000}. This figure is
> revisited in full, with the correction applied and discussed, in \S\ref{results}
> (Fig.~\ref{fig:durango-arrhenius-lag-corrected}).}
> \label{fig:durango-arrhenius-teaser}
> \end{figure}
>
> This effect can be modeled (and corrected for) for a system obeying the simple
> equation:

The figure is the **same underlying image** already used later in Results
(`encapsulated_DApErr.pdf`, `fig:durango-arrhenius-lag-corrected`) — it is not new
content, just shown once early as a short preview (abbreviated caption, no discussion
of annealing/downward-curl) and once again in full later with complete interpretation.
It needed its own label (`fig:durango-arrhenius-teaser`) since LaTeX labels must be
unique per figure instance.

**Why:** This is the concrete answer to "I'd like the uncorrected Durango data
introduced early." Rather than fabricating new content, this reuses a figure that
already existed in Results — it already plots both the uncorrected data (erratic,
uninterpretable) and the corrected data (well-behaved) on one panel, and its own
caption already made exactly this point. It was just positioned at the very end of the
paper. This also preserves the simulated figure Ben likes (kept exactly where it is,
untouched) — the two figures now work together: simulation for mechanism/intuition,
then immediately the real data for concrete evidence, before the theory that explains
and fixes it.

---

## 3. Added a backward pointer in Results to the teaser

**Old text** (Results, opening of the paragraph that first fully discusses Fig.
`fig:durango-arrhenius-lag-corrected`):

> The permeation lag-corrected helium diffusivities for the encapsulated Durango
> apatite experiment are within uncertainty of the Arrhenius relationship for 150µm
> radii Durango apatite reported by \citet{farley2000}, except for the first two
> plotted points and the 400°C step (Fig.~\ref{fig:durango-arrhenius-lag-corrected}).

**Fix:**

> **As previewed in \S\ref{theoretical-framework-of-permeation-lag}
> (Fig.~\ref{fig:durango-arrhenius-teaser}),** the permeation lag-corrected helium
> diffusivities for the encapsulated Durango apatite experiment are within
> uncertainty of the Arrhenius relationship for 150µm radii Durango apatite reported
> by \citet{farley2000}, except for the first two plotted points and the 400°C step
> (Fig.~\ref{fig:durango-arrhenius-lag-corrected}).

**Why:** Closes the loop for a reader who remembers the early teaser — signals this is
the promised "full version" of that figure rather than a new, unrelated plot.

---

## 4. Compressed Analytical Methods; moved narrow, single-experiment corrections to the SI

Three separate passages were compressed. In every case the *general* methodology (what
was done, and to which experiments) stayed in the main text; the specific numeric
derivation of *why* a correction was needed and how it was applied moved to a new SI
section, §5 below.

### 4a. Pump-out and cryofocusing corrections for the atmosphere-equilibrated empty tube

**Old text** (two full paragraphs, Analytical Methods):

> Besides the encapsulated Durango experiment, which contained a helium source, the
> helium contents (\emph{n\textsubscript{0}, n\textsubscript{t}}) of the other
> ampoules changed only by decreasing due to helium permeation through silica glass
> throughout the experiments. These experiments were concluded when measured helium
> permeate of a high temperature step was indistinguishable from blank. The values of
> \emph{n\textsubscript{0}} and \emph{n\textsubscript{t}} for each step were directly
> quantified after the experiments concluded using the total yield. Assuming that the
> helium permeated during the short pump-out time of the lamp cell is negligible, the
> total yield is simply the sum of all the measured abundances of helium for each
> step. The atmosphere-equilibrated empty tube experiment on the Pfeiffer Prisma QMS
> 200 quadrupole mass spectrometer was pumped for 15 minutes between steps, the
> encapsulated apatite experiment was pumped for 5 minutes between steps, and the
> Helix-MC-Plus\textsuperscript{10K} experiments on silica glass ampoules equilibrated
> in 2-20 torr tank helium were pumped for only 1 minute between steps. Using the
> helium permeability values of \citet{swets1961} for silica glass, an ampoule with a
> geometric factor (\emph{G}) of 6000 cm\textsuperscript{-2} would permeate 0.2‰ of
> its helium in 1 minute at 26°C (Eq.~\eqref{eq:permsol}), which is negligible for the
> scope of this work. The atmosphere-equilibrated empty ampoule with a geometric
> factor (\emph{G}) of \textasciitilde4785 cm\textsuperscript{-2} would permeate 2.8‰
> of its helium in its 15-minute pumping time between steps. For that experiment only,
> helium loss during pumping is accounted for by applying the permeation relationship
> of Eq.~\eqref{eq:permsol} (\(n_{0} = n_{t}/(1 - \,^{He}F)\)) to solve for
> \emph{n\textsubscript{0}}, the amount of helium in the ampoule before pump-out, from
> \emph{n\textsubscript{t}}, the amount remaining after pumping with T = 25°C and t =
> 15 minutes. A permeability coefficient (\emph{K}) for helium in silica glass had to
> be assumed in order to apply this correction, so the value of \(1.54 \times
> 10^{10}\) \(\frac{atoms}{s \times cm \times atm}\) at 25°C given by the Arrhenius
> law reported by \citet{swets1961} was used. The validity of this choice is
> supported by the data; the average calculated permeability at room temperature for
> this experiment after correcting for helium lost during the 15-minute pump out is
> also \(1.54 \times 10^{10}\) \(\frac{atoms}{s \times cm \times atm}\).
>
> For that experiment only, a correction was also applied to the high temperature
> steps because they were heated for short durations (45 minutes for all but one
> heated step), so that the permeation of the ampoule at room temperature during gas
> cryofocusing represented a significant portion of the step's yield. This was
> similarly corrected by calculating the expected fractional yield at room
> temperature during the gas preparation time, which is the step's total time minus
> the pump out time and the heated time, (29-31 minutes for all heated steps). For
> that correction, the permeation relationship of Eq.~\eqref{eq:permsol} (\(n_{0} =
> n_{t}/(1 - \,^{He}F)\)) is applied again to solve for the unknown
> \emph{n\textsubscript{0}}, the amount of helium within the ampoule immediately
> after the completion of the heated step, from \emph{n\textsubscript{t}}, the
> amount of helium within the ampoule when the gas is inlet into the mass
> spectrometer about 30 minutes later after spiking and helium purification. This
> cooling and gas preparation correction is not applied to the room temperature
> measurements for which the temperature remained constant during gas preparation.

**Fix (main text now reads):**

> Besides the encapsulated Durango experiment, which contained a helium source, the
> helium contents (\emph{n\textsubscript{0}, n\textsubscript{t}}) of the other
> ampoules changed only by decreasing due to helium permeation through silica glass
> throughout the experiments. These experiments were concluded when measured helium
> permeate of a high temperature step was indistinguishable from blank. The values of
> \emph{n\textsubscript{0}} and \emph{n\textsubscript{t}} for each step were directly
> quantified after the experiments concluded using the total yield. Assuming that the
> helium permeated during the short pump-out time of the lamp cell is negligible, the
> total yield is simply the sum of all the measured abundances of helium for each
> step. The atmosphere-equilibrated empty tube experiment on the Pfeiffer Prisma QMS
> 200 quadrupole mass spectrometer was pumped for 15 minutes between steps, the
> encapsulated apatite experiment was pumped for 5 minutes between steps, and the
> Helix-MC-Plus\textsuperscript{10K} experiments on silica glass ampoules equilibrated
> in 2-20 torr tank helium were pumped for only 1 minute between steps. **This
> pump-out time was short enough to neglect for all but the atmosphere-equilibrated
> empty tube, whose longer 15-minute pump-out and short (45-minute) heated steps
> required small explicit pump-out and gas-preparation corrections using
> Eq.~\eqref{eq:permsol}; see the supplement, \S\ref{pump-out-and-gas-preparation-corrections},
> for the full derivation.**

The removed portion (from "Using the helium permeability values..." through the end
of the second paragraph) now lives verbatim in the SI — see §5a below.

**Why:** The kept text explains the general total-yield method and applies to every
experiment; a reader needs that to follow the paper. The removed text is a fully
worked numeric derivation (specific permeability value, specific geometric factor,
specific timing) for correcting one calibration tube's timing artifact — necessary to
reproduce the work, not necessary to follow the argument.

### 4b. Anomalous signal recalculation for one Helix-MC measurement

**Old text** (Analytical Methods, full paragraph):

> The last high temperature step of the empty ampoule experiment on the
> Helix-MC-Plus\textsuperscript{10K} multi-collector mass spectrometer had an unusual
> and non-linear signal evolution at the beginning of the measurement for both 3He and
> 4He. For this measurement, 4He was recalculated using a linear regression on the
> last three of six measurement cycles with an R\textsuperscript{2} of 0.985 to
> regress to the 4He content at time 0. Typically, the signal evolution for a
> measurement like this would have a negative slope because the helium in the mass
> spectrometer is consumed as it is ionized and measured, but the slope for this
> measurement was positive. 3He from this measurement was calculated based on the
> recalculated 4He and an assumed isotope ratio for the measurement of 0.07 Ra. Three
> more measurements were taken over the next few days to ensure complete degassing of
> the ampoule. Two of these measurements yielded helium above blank, but were small
> compared to the final high temperature step. The yields of these steps were all
> considered in the calculation of the experiment's total yield.

**Fix (replaced with one sentence):**

> One high temperature measurement -- the last step of the empty ampoule experiment on
> the Helix-MC-Plus\textsuperscript{10K} multi-collector mass spectrometer -- showed
> unusual, non-linear signal evolution and required a bespoke recalculation to recover
> its 4He and 3He yields; see the supplement, \S\ref{anomalous-signal-recalculation},
> for details.

The full paragraph now lives verbatim in the SI — see §5b below.

**Why:** This is a one-off anomaly-handling narrative for a single measurement on a
calibration (non-flagship) experiment. It's exactly the kind of "everything you did"
detail the advisor flagged — worth preserving for reproducibility, not worth a reader's
attention in the main argument.

### 4c. Durango apatite mass-verification aside + redundant figure-caption restatement

**Old text** (end of the flagship Durango paragraph, Analytical Methods):

> 4 of the 25 high temperature experimental steps of the encapsulated Durango apatite
> produced apatite yields that were small compared to the amount of helium within the
> tube, and therefore the corrected apatite yields for that step ($\omega$ in 0) were
> within error (2$\sigma$) of 0 and were not plotted on the Arrhenius plot of
> Fig.~\ref{fig:durango-arrhenius-lag-corrected}. Uncertainty for a step's fractional
> cumulative yield was estimated as the sum of the uncertainty of its fractional
> yield plus the uncertainties of the measured fractional yields of all previous
> measurements, added in quadrature. The total yield was estimated based on the
> precisely-measured mass of the encapsulated Durango apatite (3.18 mg) and its
> helium concentration of 194.2 nccSTP/mg \citep{farley2000}. This assumption is
> supported by the measurement of 8 different \textgreater0.5 mg aliquots of the same
> Durango Apatite sample in-lab, which yield a concentration of 194 ± 9 nccSTP/mg. No
> uncertainty in the total yield estimation is propagated through to the diffusivities
> reported here.

**Fix:**

> 4 of the 25 high temperature experimental steps of the encapsulated Durango apatite
> produced corrected yields within error (2$\sigma$) of 0 and were excluded from
> Fig.~\ref{fig:durango-arrhenius-lag-corrected} **(see figure caption)**. Uncertainty
> for a step's fractional cumulative yield was estimated as the sum of the
> uncertainty of its fractional yield plus the uncertainties of the measured
> fractional yields of all previous measurements, added in quadrature. The total
> yield was estimated based on the precisely-measured mass of the encapsulated
> Durango apatite (3.18 mg) and its helium concentration of 194.2 nccSTP/mg
> \citep{farley2000}, **a value independently verified in-lab (supplement,
> \S\ref{durango-mass-verification})**. No uncertainty in the total yield estimation
> is propagated through to the diffusivities reported here.

Two separate, smaller compressions here:

- The "4 of 25 steps... not plotted" clause was trimmed (not moved) — it was fully
  redundant with the Fig.~`fig:durango-arrhenius-lag-corrected` caption, which
  already states: *"Four measurements of the permeation lag corrected apparent
  diffusivities are within error of 0 at the 2σ level and thus are excluded from the
  plot."* Saying it twice added length without adding information.
- The 8-aliquot independent verification aside moved to the SI (see §5c) — it
  supports the credibility of one input number (194.2 nccSTP/mg) but isn't needed to
  follow the Durango analysis itself.

The core Durango logic (informed-bracketing n₀ calculation, uncertainty propagation,
why some steps are bracketed differently) was **not** touched — this is the flagship
result and stays in full in the main text.

**Why:** Same rationale as 4a/4b, applied more conservatively since this is the
flagship dataset: remove only genuine redundancy and one verification aside, keep all
of the actual analytical logic.

---

## 5. New SI section: "Additional Analytical Corrections for the Empty Ampoule Calibration Experiments"

Added to `chapter1_SI_body.tex`, immediately before "Supplementary Data Tables" (this
section auto-numbers as **1.5s** in the dissertation; "Supplementary Data Tables"
shifts from 1.5s to 1.6s automatically — no manual renumbering needed, per the
`ChapterSI` numbering mechanism set up earlier).

Three subsections, each holding one of the passages removed from Analytical Methods
above, lightly reworded only where necessary to stand alone without the main-text
sentence that used to introduce them:

- **5a. Pump-Out and Gas-Preparation Corrections for the Atmosphere-Equilibrated Empty
  Ampoule** (`\label{pump-out-and-gas-preparation-corrections}`) — verbatim text from
  §4a above (the "Using the helium permeability values..." paragraph and the full
  cryofocusing-correction paragraph).
- **5b. Anomalous Signal Recalculation for the Tank Helium-Soaked Empty Ampoule**
  (`\label{anomalous-signal-recalculation}`) — verbatim text from §4b above.
- **5c. Independent Verification of the Encapsulated Durango Apatite Mass**
  (`\label{durango-mass-verification}`) — the 8-aliquot aside from §4c, reworded
  slightly to open as a standalone statement:

  > The total yield for the encapsulated Durango apatite experiment (main text,
  > \S\ref{analytical-methods}) is estimated from the precisely-measured mass of the
  > encapsulated apatite (3.18 mg) and a helium concentration of 194.2 nccSTP/mg
  > \citep{farley2000}. This concentration is independently supported by the
  > measurement of 8 different \textgreater0.5 mg aliquots of the same Durango
  > apatite sample in-lab, which yield a concentration of 194 ± 9 nccSTP/mg.

**Why a new section instead of folding into an existing one:** none of the existing SI
sections (Fick's Law derivation, diffusive steady-state profiles, permeation-lag
uncertainty, literature comparison) are thematically about ad hoc corrections to
specific calibration runs — forcing this content into one of them would have been a
worse fit than a short, clearly-labeled section of its own.

---

## Net effect

- Analytical Methods (main text) is roughly 850-900 words shorter — the three
  moved/trimmed passages, replaced by four short pointer sentences.
- Experimental Methods is unchanged in content, just relocated (section 2 instead of
  section 4).
- One new figure (a relabeled duplicate of an existing image) and two new pointer
  sentences tie the early "real data" preview to its full discussion in Results.
- Nothing was deleted from the paper — everything that moved to the SI is fully
  reproduced there, just not in the reader's way of the main argument.

## Compile verification

Recompiled the full dissertation (`pdflatex` x2, matching the project's normal
pdflatex → biber → pdflatex → pdflatex cycle, using a local biblatex stub since biber
isn't available in this sandbox) after all edits above:

- No new errors and no undefined references introduced by these changes (the same
  handful of pre-existing, unrelated sandbox limitations remain: `\citealp` undefined
  in the minimal biblatex stub, and `fontawesome5.sty`/`t5enc.def` missing for the
  standalone Copernicus-journal compile only -- both pre-date this session's edits and
  are unrelated to this restructuring).
- Table of contents confirms the new order: 1.1 Introduction, 1.2 Experimental
  Methods, 1.3 Theoretical Framework, 1.4 Experimental Approaches, 1.5 Analytical
  Methods, 1.6 Results, 1.7 Discussion, 1.8 Conclusions; SI sections renumbered
  automatically to 1.1s-1.6s with the new section appearing as 1.5s.
- The teaser figure renders as Fig. 1.2, the backward pointer in Results resolves to
  "As previewed in §1.3 (Fig. 1.2)...", and all four new `\S\ref{}` pointers into the
  new SI section resolve correctly (no "??").
