# Caption revision suggestions — hydrothermal_goethite_body.tex

Prompted by your advisor's note: *"I advise against using captions to explain observations/interpretations. That is what 'results' and 'discussion' are for."*

These are suggestions only — nothing has been changed in the .tex file. For each figure I've quoted the current caption, flagged the sentences that explain or interpret rather than describe, noted whether that content already exists in the body text (so cutting it loses nothing) or would need to be added somewhere (so cutting it *would* lose something unless you move it), and proposed a trimmed caption. You can accept, reject, or mix and match per figure.

The general rule I applied: a caption should tell the reader what they are looking at — what's plotted, what the symbols/colors/lines mean, what conditions produced it, what's excluded and why (a data-handling fact, not an interpretation) — and stop there. Anything that says what the pattern *means*, why it happened, or how it compares to expectation belongs in Results or Discussion.

---

## Fig. `stabilization-grid` (SEM grid, line 52)

**Current:** "Secondary electron images of pyrite, arsenopyrite, and goethite before heat treatment (control), and after heat treatment with and without buffering in a silica glass ampoule. Sulfides were heated at 400°C for at least 4 hours, buffered with fused sulfur (pyrite) or mineral realgar (arsenopyrite). goethite was heated at 300°C, buffered with water for 4 hours and unbuffered in vacuum for 11 hours. Buffered samples retain the smooth surfaces and clear cleavage faces of the controls, with no evidence of decomposition. Unbuffered samples show contraction cracks and surface roughening. For goethite, cracks in the unbuffered material run both parallel and perpendicular to the long axis of the polycrystalline aggregate."

**Flag:** "with no evidence of decomposition" is an interpretation of the texture, not a description of it, and it's already made explicitly in Discussion §4.1: *"retain the smooth surfaces and clear cleavage faces of the untreated controls... This observation shows that buffering... exerts a strong stabilizing effect."* Nothing is lost by cutting it from the caption.

The heating durations/temperatures duplicate Methods §2.5 almost verbatim — not an interpretation problem, but worth trimming as plain redundancy if you want a shorter caption.

**Keep as pure description:** the smooth/rough and cracking descriptions themselves (not their meaning), and the parallel/perpendicular crack-orientation detail — this last one isn't stated anywhere else and is a genuine observation a reader needs the caption for.

**Suggested revision:**
> Secondary electron images of pyrite, arsenopyrite, and goethite before heat treatment (control), and after heat treatment with and without buffering in a silica glass ampoule (see §2.5 for heating conditions). Unbuffered samples show contraction cracks and surface roughening; buffered samples retain the smooth surfaces and clear cleavage faces of the controls. For goethite, cracks in the unbuffered material run both parallel and perpendicular to the long axis of the polycrystalline aggregate.

---

## Fig. `ampoules` (two-panel ampoule photos, line 105)

**Current:** "...( a) A typical ampoule as prepared.... (b) HT-Win-06-01b after completion of the step heats.... At room temperature this ampoule is about one third liquid water by volume. All of the original water remains in the ampoule after the experiment. The gel-like lining on the inner wall is likely amorphous silica dissolved from the ampoule and redeposited by the thermally cycled hydrothermal fluid."

**Flag — two clear cases:**
1. "All of the original water remains in the ampoule after the experiment" is a results claim, and it's already stated twice in the body referencing this exact figure: §2.3 ("retained all of its original water through the entire experiment (Fig. \ref{fig:ampoule-post})") and §3.3 ("The ampoule retained its full water charge for the duration of the experiment (Fig. \ref{fig:ampoule-post})"). The caption is a third repetition. Cut it — the photo plus those two sentences already make the point.
2. "...is likely amorphous silica dissolved from the ampoule and redeposited by the thermally cycled hydrothermal fluid" is an interpretation of the lining, and it is the interpretation given in Discussion §4.5: *"The silica dissolved from the ampoule wall and redeposited as a gel-like lining (Fig. \ref{fig:ampoule-post}) shows that the fluid was capable of dissolving and reprecipitating rock-forming oxides."* This is the strongest example in the manuscript of a caption doing Discussion's job — the caption is essentially a preview of §4.5's argument. Trim to naming the feature only.

**Suggested revision:**
> Silica glass ampoules used for helium step heat experiments. (a) A typical ampoule as prepared, here containing Durango apatite crushate sieved to 300 μm (radii ≈ 150 μm). The ampoule is roughly one cm long and one mm wide; the bars visible behind it are separated by 1 mm. (b) HT-Win-06-01b after completion of the step heats, before breaking for the final furnace step. At room temperature this ampoule is about one third liquid water by volume, with a gel-like lining visible on the inner wall.

---

## Fig. `durango-arrhenius` (Durango Arrhenius plot, line 237)

**Current:** "...Without permeation lag corrections the apparent diffusivities are highly irregular. With corrections the sample agrees with the diffusion parameters reported by Farley (2000) for the appropriate sieve size (r = 150 μm). Beyond 300°C the activation energy decreases to give a slight downward curl, likely caused by annealing of crystal defects and radiation damage (Wolf 1996; Farley 2000). Apparent diffusivities are calculated with the equations of Fechtig & Kalbitzer (1966). Four corrected diffusivities are within 2σ of zero and are excluded. The full dataset is available in the data repository (Thyer 2026)."

**Flag — two sentences are Discussion's job, verbatim elsewhere:**
- "With corrections the sample agrees with..." duplicates Results §3.1: *"the corrected diffusivities agree within uncertainty with the Arrhenius relationship reported by Farley (2000) for Durango apatite of the same 150 μm half-prism width."*
- "...likely caused by annealing of crystal defects and radiation damage" duplicates Discussion §4.2 almost word for word: *"Above 300°C the corrected array curves downward, a feature documented for Durango apatite and attributed to annealing of radiation damage and crystal defects (Wolf 1996; Farley 2000; Shuster 2006)."* This is the same pattern as the ampoule caption — the *cause* of a feature stated in the caption, then argued again in Discussion.

**Suggested revision:**
> Arrhenius plot of a helium step heat of silica glass encapsulated Durango apatite, with 2σ uncertainties, shown with and without the permeation-lag correction of §3.1. Apparent diffusivities are calculated with the equations of Fechtig & Kalbitzer (1966). Four corrected diffusivities are within 2σ of zero and are excluded.

(I dropped the closing "full dataset is available in the data repository" sentence — see the note at the end of this document about repository citations now that you have a global Data Availability statement.)

---

## Fig. `permeation-fits` (isothermal permeation-step fits, line 250)

**Current:** "...Each series is held at a single temperature between 90 and 110°C. The curvature of each series is what conditions the fit: a series in which the permeation rate has not yet slowed appreciably constrains λ and n₀ only weakly (§3.4). The rate constants recovered here are converted to permeabilities, K = λ/GRT, and plotted against temperature in Fig. [ampoule-permeability]."

**Flag:** "The curvature of each series is what conditions the fit..." is a methodological explanation of *why* the fit behaves as it does — it's not describing the plot, it's teaching the reader how the regression works. It isn't stated in §3.4 (Measuring the ampoule's rate constant) currently, so cutting it from the caption would genuinely lose the point, not just de-duplicate it. Rather than deleting it, I'd move it into §3.4's prose, where a reader looking for the mechanics of the fit would expect to find it, and leave the caption purely descriptive.

**Suggested revision (caption):**
> Cumulative ³He yield against cumulative time for four of the ten series of consecutive isothermal permeation steps on HT-Win-06-01b, with the non-linear least squares fit of λ and n₀ to Eq. [incyield] overlain, shown here as a representative example. Each series is held at a single temperature between 90 and 110°C. Rate constants are converted to permeabilities via K = λ/GRT and plotted against temperature in Fig. [ampoule-permeability].

**Suggested addition to §3.4** (end of the paragraph beginning "Because permeation remains first order..."), so the point isn't lost:
> The curvature of each series is what conditions the fit: a series in which the permeation rate has not yet slowed appreciably constrains λ and n₀ only weakly.

---

## Fig. `ampoule-permeability` (permeability Arrhenius plot, line 263)

**Current:** "...The activation energy is higher than for anhydrous silica glass, as expected (Masaryk 1968; Shelby 1972). The apparent ³He permeability exceeding the literature values of Swets (1961) and Jones (1953) is not expected, and is attributed to displacement of gas-phase volume by liquid water (§4.3). Points labelled 'Diffusion Model with cooling, Anhydrous' show the excess apparent permeability predicted for a dry ampoule that continued to permeate during the 26 minute cooldown before measurement. Their scatter reflects differences in hold duration and is small; the offset from the literature values is near constant and much smaller than the uncertainty on the fitted values."

**Flag — this is the other strong example of the pattern:**
- "The activation energy is higher than for anhydrous silica glass, as expected" duplicates Discussion §4.3: *"the fitted activation energy... is significantly higher than expected for silica glass with or without water."*
- "...is attributed to displacement of gas-phase volume by liquid water (§4.3)" literally cites the section where the explanation lives while also giving the explanation in the caption — this is worth cutting outright rather than moving, since §4.3 already develops the full argument (Eq. [keff] and the reasoning behind it) and the caption's one-line version can't add anything.
- "the offset from the literature values is near constant and much smaller than the uncertainty on the fitted values" duplicates Results §3.2 almost verbatim: *"This offset is small: significantly smaller than the 2σ uncertainties on the fitted values."*

**Keep as pure description:** what the "Diffusion Model with cooling, Anhydrous" points represent (a reader can't parse the legend without this) and that their scatter reflects hold-duration differences (a data-provenance fact, not an interpretation).

**Suggested revision:**
> Apparent permeation coefficients for HT-Win-06-01b against inverse temperature, converted from the rate constants fitted in Fig. [permeation-fits] via K = λ/GRT, plotted against literature values for anhydrous silica glass (Swets 1961; Jones 1953). Points labelled "Diffusion Model with cooling, Anhydrous" show the excess apparent permeability predicted for a dry ampoule that continued to permeate during the 26 minute cooldown before measurement; their scatter reflects differences in hold duration.

---

## Fig. `arrhenius-full` (full Arrhenius plot vs. vacuum experiments, line 276)

**Current:** "...The Stage 2 reference line described from Farley (2024) is fit to the step heats of Monteiro (2017). Error bars on the data from this study are omitted for clarity. A diffusion domain corresponding to the Stage 2 reference line would have a closure temperature of about 45°C at a cooling rate of 10°C/Ma."

**Flag — different from the others:** the closure-temperature statement is a genuine calculated result, and unlike every other flagged sentence above, it does **not** appear anywhere else in the manuscript — I checked. So this isn't redundant caption content to delete; it's an analytical result that's only ever been given in a caption, which is arguably a bigger problem than over-explaining. I'd suggest moving it into Discussion §5.4 (Helium retentivity of goethite), alongside the existing Stage 1 closure-temperature discussion, and leaving only the descriptive plot-element sentences in the caption.

**Suggested revision (caption):**
> Arrhenius plot of ³He and ⁴He apparent diffusivities from HT-Win-06-01b, with step heats of the same Win-06-01b material in vacuum from Monteiro (2017) and Farley (2024). The Stage 2 reference line described from Farley (2024) is fit to the step heats of Monteiro (2017). Error bars on the data from this study are omitted for clarity.

**Suggested addition to §5.4**, after the existing Stage 1 closure-temperature sentence:
> A diffusion domain corresponding to the Stage 2 reference line (Fig. [arrhenius-full]) would have a closure temperature of about 45°C at a cooling rate of 10°C/Ma.

---

## Fig. `arrhenius-zoom` (Stage 1 regression, line 286)

**Current:** "...A diffusion domain corresponding to this line has a closure temperature of [Tc] ± [err] °C at a cooling rate of 10°C/Ma. Apparent diffusivities calculated from ⁴He generally lie about one log unit lower after a cumulative ³He yield of 5%."

**Flag:** the closure-temperature sentence is stated verbatim in both Results §3.3 and Discussion §5.4 — this is the most-repeated sentence in the manuscript (three times total). Cut from the caption; it's well established elsewhere.

The ⁴He-vs-³He offset sentence is closer to a genuine plot description (it's just describing the relative position of the two curves) and is only loosely echoed in Results §3.3 — I'd call this one borderline-acceptable to keep, since a reader looking only at the figure benefits from it. Your call.

**Suggested revision:**
> The linear regression of the ³He apparent diffusivities of HT-Win-06-01b above 7% cumulative yield, defining the Stage 1 reference line. Apparent diffusivities calculated from ⁴He generally lie about one log unit lower after a cumulative ³He yield of 5%.

---

## Fig. `nt-vs-ntss` ($n_t$ vs. $n^{ss}$, line 337)

**Current:** "...Excluding the two complete-degas steps discussed in §5.5, $n_t$ never exceeds $n^{ss}$. Both complete-degas steps exceed their own $n^{ss}$ with an excess roughly proportional to the duration of the complete-degas step."

**Flag:** both sentences are results/interpretation restated from Discussion §5.3 and §5.5 (*"$n_t \leq n^{ss}$ for every permeation step in the experiment"*; *"This excess scales with step duration"*). The bare fact that the two triangle points sit above the 1:1 line is visible in the plot itself and doesn't need a caption sentence; the "roughly proportional to duration" claim is an interpretation that's already made explicitly in §5.5.

**Suggested revision:**
> Two independent calculations of the ampoule's residual ³He inventory following each high temperature experimental step for HT-Win-06-01b: $n_t$, quantified directly from the low temperature permeation step measurement via Eq. [n0perm] ($y$-axis), against $n^{ss}$, the upper bound of Eq. [steadystate] calculated from the high-temperature experimental step ($x$-axis). Color gives the permeation step duration. Circles are ordinary steps; triangles are two very long "complete ampoule degas" steps, held at 100°C for over a factor of ten longer than any other permeation step in the experiment (§5.5). The dashed line is 1:1, representing the upper limit for self-consistent data.

---

## Fig. `delta-zoom` (delta plot, line 348)

**Current:** "...Delta is the difference between apparent log diffusivity and the Stage 1 reference line (Fig. [arrhenius-zoom]), which removes the temperature dependence of the dominant migration process to show how apparent diffusivities evolve through the experiment. ³He decreases monotonically, then follows the reference line from 7–15%. ⁴He delta values increase initially and settle about one log unit below the ³He reference line."

**Flag:** this one is more defensible than the others because "delta plot" isn't a standard axis a reader can decode on sight — some definition is needed. But the clause "which removes the temperature dependence of the dominant migration process to show how apparent diffusivities evolve" is explaining *why* the method works, which is the same move as the flagged sentences above, and it isn't otherwise stated in Discussion §5.4 where delta values are actually interpreted. I'd suggest keeping the bare definition (what delta *is*, computationally) and moving the rationale into §5.4 alongside the existing MDD discussion, or cutting the rationale clause entirely if you're comfortable letting Farley (2018) carry that justification by citation alone.

The trend sentences (³He decreasing monotonically, ⁴He settling one log unit below) are closer to plot description than interpretation, though they do closely echo Results §3.3 wording — minor redundancy, not a rule violation, so I'd leave them unless you want a tighter caption regardless.

**Suggested revision:**
> Delta plot after Farley (2018), comparable to the $r/r_0$ plots of Lovera (1991) and Farley & Flowers (2012). Delta is the difference between apparent log diffusivity and the Stage 1 reference line (Fig. [arrhenius-zoom]). ³He decreases monotonically, then follows the reference line from 7–15%. ⁴He delta values increase initially and settle about one log unit below the ³He reference line.

---

## Fig. `ratio-spectra` (⁴He/³He ratio spectra, line 383)

**Current:** "...The ⁴He/³He ratios sample relative 4He concentration of different domains with different helium retentivities in nature. The hydrothermal experiment records lower ratios at a given yield than either vacuum experiment for the entire duration of the experiment. All three begin at very small values and increase steeply, with the rate of increase slowing between 5% and 20% cumulative yield. The hydrothermal experiment is plotted as an envelope spanning the lower and upper bounds of Eq. [bound]."

**Flag:** "The ⁴He/³He ratios sample relative 4He concentration of different domains with different helium retentivities in nature" is explaining what the ratio *means* geologically — that's the opening move of Discussion §5.6, which gives the fuller version: *"record the rounding of the radiogenic helium concentration profile by natural loss..."* This is the clearest remaining case of a caption doing interpretive work that Discussion already does properly.

The comparison and trend-shape sentences are closer to plot description (what the curves do relative to each other) and are also given in Discussion §5.6, but more as data description than as an argument — I'd treat these as optional trims rather than required ones.

**Suggested revision:**
> Bulk-normalized ⁴He/³He ratios for Win-06-01b step heats against cumulative fractional ³He yield (§5.6). All three experiments begin at very small values and increase steeply, with the hydrothermal experiment recording lower ratios at a given yield than either vacuum experiment throughout. The hydrothermal experiment is plotted as an envelope spanning the lower and upper bounds of Eq. [bound].

---

## A note outside the advisor's specific comment

Three captions (`durango-arrhenius`, and the apatite/goethite methods text) each separately cite the Zenodo data repository. Since you're adding a manuscript-level Data Availability statement (§7), these per-figure citations are now redundant with that statement and could be cut wherever they appear only to point the reader at the repository, unless you want the redundancy for a reader who only looks at figures. Flagging it here since it came up while going through captions, not because it's an interpretation problem.

---

## Summary table

| Figure | Sentence(s) to cut | Where it already lives (nothing lost) | Needs to move, not just cut |
|---|---|---|---|
| stabilization-grid | "with no evidence of decomposition" | §4.1 | no |
| ampoules | "All of the original water remains..."; "...likely amorphous silica... redeposited..." | §2.3 / §3.3; §4.5 | no |
| durango-arrhenius | "With corrections the sample agrees..."; "...likely caused by annealing..." | §3.1; §4.2 | no |
| permeation-fits | "The curvature of each series is what conditions the fit..." | — (not stated elsewhere) | **yes → §3.4** |
| ampoule-permeability | "The activation energy is higher... as expected"; "...is attributed to displacement of gas-phase volume..."; offset-vs-uncertainty sentence | §4.3; §4.3; §3.2 | no |
| arrhenius-full | "A diffusion domain corresponding to the Stage 2 reference line... 45°C..." | — (not stated elsewhere) | **yes → §5.4** |
| arrhenius-zoom | Closure-temperature sentence | §3.3 and §5.4 (stated twice already) | no |
| nt-vs-ntss | "$n_t$ never exceeds $n^{ss}$..."; "...excess roughly proportional to duration" | §5.3; §5.5 | no |
| delta-zoom | "...which removes the temperature dependence... to show how apparent diffusivities evolve" | — (not stated elsewhere) | optional → §5.4, or cut |
| ratio-spectra | "The ⁴He/³He ratios sample relative 4He concentration..." | §5.6 (fuller version) | no |
