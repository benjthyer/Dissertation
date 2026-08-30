# Narrative and structure review — hydrothermal_goethite_body.tex

This is a read of the current draft (the version with your already-applied caption trims) plus the two wrapper files and the existing SI. It's organized around the questions you asked. Nothing here touches substance — it's about what's said where, what's left hanging, and how the pieces read together.

## 1. Overall shape

Rough word counts by section (Discussion is the outlier):

| Section | Words |
|---|---|
| Introduction | ~570 |
| Materials and Methods | ~1,300 |
| Permeation Systematics (Theory) | ~1,400 |
| Results | ~1,030 |
| Discussion | ~2,620 |
| Conclusions | ~350 |

Discussion is nearly double any other section, which is normal for a paper carrying this much interpretive weight, but it's worth knowing going in: if anything needs trimming for length, Discussion is where the room is, not Theory (see §6 below).

The paper is really two arguments running in parallel: a methods argument (the ampoule works, permeation lag is tractable, encapsulated Durango apatite proves it) and a science argument (goethite is far more helium-retentive than vacuum step heats suggested). Structurally these are interleaved rather than sequential — Methods and Theory set up both at once, Results reports both, and Discussion's nine subsections alternate between them (§5.1–5.4 are methods validation, §5.5–5.7 are the goethite science, §5.8 is a methods aside, §5.9 is science again). That's a defensible choice given GCA's stated policy that method development is only publishable "accompanied by a novel scientific result... enabled by the new development" — the paper needs both threads visible together to make that case. But it means the science payoff doesn't get an uninterrupted run anywhere in the body; it's always sharing space with method validation. See §3 for a concrete fix.

## 2. The narrative gap: the abstract's punchline isn't fully built in the body

This is the biggest structural note. The abstract ends with what reads as the paper's real thesis:

> "...vacuum step heats of goethite appear to record the mineral's response to the experiment rather than helium migration through it, and helium retention in natural goethite is correspondingly more robust than those experiments imply."

That's a strong, general claim — essentially "trust this experiment's retentivity over the vacuum literature's." But the Conclusions section never quite restates it that plainly. Conclusions gets close piecewise (§6 ¶2: "essentially quantitatively retentive... at 25°C"; ¶3: the He ratio geometry argument) but the synthesis step — *because* vacuum goethite step heats are known to be decomposition-controlled (established already in your Introduction, citing Farley 2024), and *because* this hydrothermal result differs from vacuum by more than vacuum results differ from each other, therefore the vacuum literature's retentivity estimates should be discounted in favor of this one — is only assembled in full in the Abstract. A reader who reads the body but skims the abstract won't come away with that argument.

I'd suggest adding a short passage (a few sentences) either at the end of §5.7 (Helium retentivity of goethite) or as a new closing paragraph in Conclusions that makes this comparison explicit: state the magnitude of vacuum-to-vacuum disagreement (if you have it — e.g., how much Monteiro 2017 and Farley 2024 differ from each other) against the magnitude of your hydrothermal-to-vacuum gap (~7 log units), and draw the "the vacuum experiments are the outliers, not this one" conclusion in the body, not just the abstract.

## 3. The introduction undersells the science it's introducing

The Introduction's final paragraph (the roadmap paragraph, "This paper establishes...") previews only the methods contributions — stabilization, permeation-lag deconvolution, in-situ rate constant measurement — and closes with "the first hydrothermal helium step heat reported for goethite," which is a novelty claim, not a results claim. It never previews *what was found* (the ~7 log unit retentivity gap, the MDD systematics, the closure temperature). Since the Title and Abstract both lead with the science result, and GCA is explicit about not wanting pure method papers, having the Introduction's own roadmap read as a methods-paper summary works against the framing you want. I'd add one sentence to that paragraph previewing the retentivity finding, so a reader who only reads the first and last paragraphs of the Introduction still gets the science, not just the method.

This pairs with the Discussion-ordering point from §1: consider moving §5.8 (Excess helium measured in very long permeation steps — a methods-anomaly aside) so it sits next to §5.4 (the other bounding-method consistency check) rather than between §5.7 (retentivity, a headline science result) and §5.9 (He ratio geometry, also science). As written, the science narrative gets interrupted by a methods tangent right before its last beat. Moving §5.8 lets §5.5–5.7 and §5.9 run together as one uninterrupted science argument, with all four methods-validation subsections grouped at the front of the Discussion.

## 4. Things that could read as distracting or tangential

Nothing in the draft is irrelevant, but a couple of passages are more methods-minutiae than a GCA reader strictly needs in the body, and are candidates for trimming or moving to the SI:

- **§5.8, Excess helium in very long permeation steps.** This is honestly reported (including the authors' own uncertainty about the cause) and it needs to exist somewhere, since the two "complete ampoule degas" steps are visible outliers in Fig. `nt-vs-ntss` and a reader will ask about them. But it's speculative ("we hypothesize"), self-admittedly under-constrained ("insufficient data to make any interpretation confidently"), and the numeric detail (7200 vs. 1590 minutes, the ≈1.5× and ≈25% figures) reads more like an SI-level accounting than a main-text argument. Consider keeping one or two sentences in the body (enough to explain why those two points are excluded from the headline results) and moving the fuller discussion of the hypothesized cause to the SI or shortening it in place.
- **The crack-orientation detail in Fig. 1's caption** ("cracks in the unbuffered material run both parallel and perpendicular to the long axis of the polycrystalline aggregate") is a specific observation that's never picked up again in the Discussion. Either give it a one-clause payoff where dehydration/cracking is discussed (§5.3) — e.g., if the orientation says something about how dehydration propagates through the aggregate — or it's just descriptive noise that could be cut.

Nothing else struck me as off-topic; the silica-glass background in the Introduction, the related-work citations (Harrison 1982/1985, Yakubovich et al.), and the geometric-factor derivation in Methods all pay off later.

## 5. Loose threads / questions the draft raises but doesn't close

- **The Stage 1/Stage 2 terminology.** You've left yourself a note about this at line 279 ("Does the stage 1 / stage 2 regression terminology provide any benefit? Consult.") — flagging it here since it's a live open question in your own text, not a finished decision. Worth resolving before this goes further, since "Stage 1"/"Stage 2" appears in the Results, two Discussion subsections, and the Conclusions.
- **The 2–30% natural helium loss range from the Introduction** (line 22, citing Shuster & Vasconcelos 2005 and others) is never explicitly reconnected to this study's results. It's not directly comparable to your 14.7% experimental cumulative yield (one is inferred natural loss, the other is a controlled step-heat yield), but since the Introduction opens with that range as the motivating uncertainty, a reader may expect the paper to eventually say something like "our results are/aren't consistent with that range" — right now that loop isn't explicitly closed either way.
- **Single-aliquot design.** The entire hydrothermal goethite result — activation energy, closure temperature, the whole retentivity argument — rests on one 1.18 mg aliquot in one ampoule. The Conclusions call for further experiments, but frame that as extending the method to new variables (crystallite size, composition, radiation damage), not as replicating this specific measurement to establish its reproducibility. A GCA reviewer is likely to ask about n=1 directly; it may be worth a sentence acknowledging this as a limitation explicitly, separate from the "more experiments needed" framing that's already there.

## 6. Is the Theory section (§3) over- or underweighted?

No — by word count it's actually smaller than Discussion and only slightly larger than Methods (see the table in §1), and every equation it introduces (Eqs. permlag, carry, permode, geomfactor, permsol, n0perm, incyield, steadystate, bound) gets used later in Results or Discussion. Nothing is derived and then abandoned, which is the usual sign of an over-built theory section.

The one structural risk isn't length, it's genre signaling: giving the permeation-lag framework its own numbered top-level section between Methods and Results (rather than folding it into Methods, or appendicizing the derivations) makes the paper's methodological backbone visually prominent, at exactly the point where GCA's own guidance says a method-forward paper needs a novel result to justify itself. Given that, I'd leave the content as-is but consider two small framing changes rather than cutting anything: (1) a one-sentence lead-in at the start of §3 explicitly stating why this framework is necessary for the goethite result specifically (tying it forward to §5, not just backward to the ampoule), and (2) possibly retitling the section from "Permeation Systematics of Fused Silica Ampoules" (reads like a materials-science section header) to something that keeps the reader oriented toward the goethite question, e.g. "Quantifying and Removing Permeation Lag." Small changes, same content.

## 7. Is the title appropriate?

*"Hydrothermal Helium Step Heats Reveal High Helium Retentivity and Multiple Diffusion Domain Systematics in Goethite"*

Strategically, leading with the science result rather than the method is the right call given GCA's scope note — this title would not read as a methods paper on its own, which matters for getting past the editor. A few things worth weighing:

- **"High Helium Retentivity" is doing a lot of work for a two-word phrase.** The paper's own Discussion is more careful than that: the Stage 1 domain is "essentially quantitatively retentive... at billion-year timescales at 25°C" *in the lab-extrapolated sense*, but the 4He data in the same section shows this domain "experienced helium loss in nature," and §5.3 explicitly can't rule out that dehydration/recrystallization (not diffusion) set the observed rate, which would make the diffusivity an upper bound rather than a clean retentivity number. None of that nuance is wrong to compress out of a title — titles compress — but it's worth deciding deliberately whether "High Helium Retentivity" is the claim you want load-bearing in the title, or whether something like "Helium Retentivity" (dropping "High") more accurately reflects a result that's strong but caveated.
- **The method is completely absent from the title.** That's consistent with GCA's preferences, but it does mean a reader searching for "silica glass ampoule," "encapsulation," or "permeation lag" won't find this paper by title alone — only by keywords/abstract. Since the method is genuinely novel (this is, per your Introduction, a new experimental approach), that's a real tradeoff, not just a style choice. Worth confirming it's intentional.
- **Stale documentation flag, not a content issue:** `hydrothermal_goethite_abstract.tex`'s header comment still lists a "working title" ("High Helium Retentivity in Goethite under Hydrothermal Conditions, Revealed by Step-Heat Experiments in Silica Glass Ampoules") that differs from both the current main-text title and the SI wrapper's title ("Supplementary Information for: High Helium Retentivity in Goethite under Hydrothermal Conditions Measured by Step-Heat Experiments in Silica Glass Ampoules"). All three are currently different strings. Worth reconciling the SI title with whatever the final main-text title is before submission — right now they'd visibly mismatch on the SI's own cover page.

## 8. What the SI should contain

You mentioned assuming you'd need to build an SI with some derivations — worth knowing that one already exists (`hydrothermal_goethite_SI_body.tex`, with a matching wrapper `hydrothermal_goethite_GCA_SI.tex`), carried over from the dissertation chapter. It's not a from-scratch job; it's a trim-and-reconcile job. Its current contents, and what I'd do with each:

- **§1.1, Uncertainty Quantification for Bounding Method** (diffusivity bound derivation, the 4-scenario 4He/3He ratio uncertainty bracketing) — exactly the kind of derivation a careful reader will look for once they hit the bounding equations in the main text. Keep, lightly edited for the standalone (non-dissertation) context.
- **§1.2, Finite Difference Diffusion Model of Cooling Tube** — this is the cooling simulation your Results section already references ("A finite-difference cooling simulation... predicts...") without showing its mechanics. A reader who wants to check that claim will look for exactly this section. Keep, including its supporting figure (the cooling-rate fit).
- **§2, Verification of the Bounding Method via the Permeation Step Method** — this is the full worked comparison behind the one-paragraph summary in main-text §5.4 (the two activation-energy/closure-temperature ranges you quote as agreeing "within uncertainty"). A skeptical reviewer will want to see this in full. Keep the reduction and its logic; see below on the raw data it currently carries.
- **§2.2 and its subsections (Raw Data and Corrections Columns, blank corrections, permeation lag corrections, rate constant dataset, diffusivities, totals) and §3 (Durango apatite step-heat data)** — these are raw/intermediate data tables, exactly what your project instructions say should move to the Zenodo repository instead of living in the paper's SI. These are strong candidates to cut from the SI entirely, replaced by a pointer to the repository, once Zenodo is live.
- **One thing I didn't find that a reader may look for:** the main-text caption/text for Fig. `permeation-fits` explicitly says it shows "four of the ten series... as a representative example." A reader who wants to see the other six fits has nowhere to look right now — that's a natural SI figure (a full ten-panel grid) that doesn't currently exist in the SI body, at least not in what I read.

One more thing surfaced while reading the SI closely, unrelated to what belongs where: **the SI's narrative text (§2.2.2, "Bracketing Method Ratios") states the 4He/3He ratios "plateau around a cumulative 3He fraction of 0.06 at a bulk normalized 4He/3He ratio of 0.75,"** but the current main-text Results (§4.3) says the opposite — "The hydrothermal experiment did not reach a plateau." This looks like leftover language from an earlier reduction (possibly the dissertation-era permeation-step/"naive" dataset rather than the bounding-method dataset used in the final paper) that wasn't updated when the main text's conclusion changed. Worth reconciling before this goes out, since it's a direct factual contradiction between the two documents rather than a phrasing issue.
