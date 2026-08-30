# Copyedit changelog — hydrothermal_goethite_body.tex

Scope: main body text only (`hydrothermal_goethite_body.tex`), not the SI. Line numbers refer to the file before and after these edits — the edit count is unchanged (432 lines both versions), so line numbers below match the current file. Nothing in the substance of any claim, number, or citation was touched; every change below is spelling, grammar, or LaTeX mechanics. Content-level suggestions I noticed along the way but did **not** apply are in their own section at the end.

I verified the edit mechanically before and after: identical counts of `{`, `}`, `(`, `)`, `$`, `&`, `%`, `[`, `]`, backslashes, and `\begin`/`\end` pairs for every environment, and a test compile (stubbed bibliography/figures, since those aren't part of this round) produced clean output with no errors traceable to the edited text.

## Duplicated or missing words

| Line | Before | After |
|---|---|---|
| 228 | "...radiation damage annealing [...], which can cause **can cause** helium release to accelerate." | "...which can cause helium release to accelerate." |
| 314 | "Our measurement of faster helium permeation rate for **the the** HT-Win-06-01b ampoule..." | "Our measurement of **a** faster helium permeation rate for the HT-Win-06-01b ampoule..." (also restores a missing article) |
| 64 | "...6675 cm⁻² for the goethite ampoule (520 μm inner, 810 μm outer diameter." | "...810 μm outer diameter)." (missing closing parenthesis) |

## Misspellings

| Line | Before | After |
|---|---|---|
| 56 | "permation lag" | "permeation lag" |
| 56 | "permeate heium anomalously fast" | "permeate helium anomalously fast" |
| 66 | "the encapulation process" | "the encapsulation process" |
| 66 | "held in liquid nitogen instead" | "held in liquid nitrogen instead" |
| 117 | "to charectarize temperature gradients" | "to characterize temperature gradients" |
| 212 | "An alternative apporoach is available" | "An alternative approach is available" |
| 214 | "an increasinly accurate approximation" | "an increasingly accurate approximation" |
| 214 | "Additionaly, an upper bound..." | "Additionally, an upper bound..." |
| 228 | "This bounding appoach is an excellent fallback" | "This bounding approach is an excellent fallback" |

## Spelling consistency (document otherwise uses American spelling)

| Line | Before | After |
|---|---|---|
| 82 | "Less than one microlitre of distilled water" | "...one microliter of distilled water" |
| 263 (caption) | "Points labelled ``Diffusion Model...''" | "Points labeled ``Diffusion Model...''" |

## Capitalization

| Line | Before | After | Why |
|---|---|---|---|
| 22 | "decomposes to **Hematite** (Fe₂O₃)" | "decomposes to **hematite** (Fe₂O₃)" | Mineral names are lowercase mid-sentence elsewhere in the document ("goethite," "apatite"); this was the one exception. |
| 56 | "helium step heat measurements of Durango **Apatite**" | "...of Durango **apatite**" | "Durango apatite" is lowercase everywhere else it appears. |

## Sample ID consistency

| Line | Before | After |
|---|---|---|
| 82 | "An aliquot of 1.18 mg **Win-06-01** goethite blades" | "...**Win-06-01b** goethite blades" (matches the sample designation used everywhere else, including two sentences earlier) |

## Subject–verb agreement

| Line | Before | After |
|---|---|---|
| 25 | "...such as water, sulfur, or oxygen **is** retained" | "...**are** retained" |
| 304 | "...the existing approach requires... and **rely** on precise knowledge..." | "...and **relies** on precise knowledge..." |
| 309 | "Step heats on encapsulated Durango apatite **reproduces** the diffusion behavior..." | "...**reproduce** the diffusion behavior..." |

## Other grammar and word choice

| Line | Before | After | Why |
|---|---|---|---|
| 20 | "...surface processes **such** weathering and ferruginization" | "...surface processes **such as** weathering..." | Missing "as." |
| 179 | "The measured helium from such a step **then is** a measurement..." | "...**is then** a measurement..." | Misplaced adverb. |
| 304 | "an arbitrary **amount** of isothermal step heat measurements" | "an arbitrary **number** of isothermal step heat measurements" | "Amount" is for uncountable nouns; "measurements" are countable. |
| 302 | "...does not preclude decomposition **of a smaller extent**..." | "...decomposition **to a lesser extent**..." | Wrong preposition. |
| 358 | "...that would produce extensive cracks in the sample, **like in** vacuum heated samples" | "...**as in** vacuum-heated samples" | "Like" should be "as" when comparing clauses; "vacuum heated" hyphenated as a compound adjective (see below). |
| 316 | "...are about 3% and 1% **respectively** of the gas-phase concentration" | "...3% and 1%**, respectively,** of the gas-phase concentration" | Standard comma placement around a parenthetical "respectively." |
| 122 | "...heated either in vacuum... or in open air **while** buffered samples were sealed..." | "...in open air**,** while buffered samples..." | Missing comma before a contrastive "while" clause. |
| 105 (caption) | "A gel-like lining on the inner wall is visible**, see** §5.3 for discussion." | "...is visible **(see §5.3).**" | Comma splice. |
| 368 | "...an apatite crystal of about 650 μm radius; **However,** closure temperature..." | "...650 μm radius. **However,** closure temperature..." | A semicolon can't be followed by a capitalized new sentence; changed to a period. |
| 371–372 | "...by a factor of ≈1.5**;** whereas the shorter step..." (and a stray double space before "exceeds") | "...by a factor of ≈1.5**,** whereas the shorter step..." | "Whereas..." is a dependent clause, not a second independent clause, so it takes a comma, not a semicolon; also removed the double space. |
| 396 | "Sealing goethite in **a** silica glass **ampoules** with water enables..." | "...in **a** silica glass **ampoule** with water..." | Article/number disagreement. |

## Hyphenation of compound adjectives (mostly internal inconsistencies — the same phrase is hyphenated correctly elsewhere in the document)

| Line(s) | Phrase |
|---|---|
| 152, 372 | "first order process" → "first-order process" (the document already correctly uses "first-order rate law," "first-order process," and "first-order processes" elsewhere) |
| 201, 250 (caption) | "least squares solve/fit" → "least-squares solve/fit" |
| 214, 337 (caption), 372 | "high temperature" → "high-temperature" (before a noun; already hyphenated correctly several other times, including twice in the same caption at line 337) |
| 337 (caption), 372 | "low temperature" → "low-temperature" (same issue) |
| 263 (caption) | "26 minute cooldown" → "26-minute cooldown" |
| 374 | "150 minute permeation step" → "150-minute permeation step" |
| 374 | "steady state helium inventory" → "steady-state helium inventory" |
| 358 | "vacuum heated samples" → "vacuum-heated samples" |

## Typography / LaTeX mechanics

| Line | Issue | Fix |
|---|---|---|
| 27 | Bare figure reference with no parentheses: "...step heat experiments Fig.~\ref{...}, motivating..." | "...(Fig.~\ref{...}), motivating..." |
| 84 | Stray space inside a parenthetical: "( 10⁻⁷ torr)" | "(10⁻⁷ torr)" |
| 195 | Missing space before a parenthetical section reference: "data(\S\ref{...})" | "data (\S\ref{...})" |
| 372 | Missing space before `\citep`: "sample\citep{lee1993}" | "sample \citep{lee1993}" |
| 208 | "Levenberg-Marquardt" (hyphen) | "Levenberg--Marquardt" (en dash, standard for a compound personal name) |
| 398 | "linear between 7-15% cumulative yield" | "linear between 7--15% cumulative yield" (en dash, matching the same range written correctly twice elsewhere, e.g. line 281) |
| 258 | "an offset that is **near constant**" | "...**nearly constant**" ("near" isn't a standard adverb before an adjective) |

## Equation-terminal punctuation

Three displayed equations had punctuation inconsistent with how every other equation in the document is followed. The convention used elsewhere: a period before an independent new sentence (e.g. Eq. permlag → "Here $n_0$ is..."), a comma before a "where X is Y" defining clause (e.g. Eq. permode → "where $n$ is...", Eq. geomfactor → "with $a$ the..."). Brought these three in line with that pattern:

- **Eq. permsol** (line 183): ended with a comma, followed by the unrelated new sentence "This equation is applied to recover..." — changed the equation's trailing comma to a period.
- **Eq. n0perm** (line 189): ended with a period, followed by a lowercase "where $^{He}F$ is the fraction..." defining clause — changed the equation's trailing period to a comma (matches the lowercase "where" already there).
- **Eq. keff** (line 320–323): ended with a period, followed by a capitalized "Where $\lambda_{ampoule}$ is..." defining clause — changed the trailing period to a comma and lowercased "Where" → "where," for the same reason.

## Abbreviation definition

- Line 343: "MDD" is used twice later in the same subsection (§5.5) without ever being defined. Added the parenthetical the first time "multiple diffusion domain" appears in that subsection's prose: "...should show multiple diffusion domain **(MDD)** behavior..."

---

## Suggested content/clarity changes — not applied

These go beyond copyediting (word-choice or restructuring rather than mechanical correction), so I've left them for you to weigh in on rather than changing them:

- **Line 22, two "but"s in one long sentence:** "...are always non-zero but modest, ranging from 2 to 30% [...], but the effects of temperature, crystallite size, and chemical composition have not been determined..." Consider splitting into two sentences for readability.
- **Line 166, repeated citation string:** the same four citations (Norton 1953, Altemose 1961, Swets 1961, Masaryk 1968) are given twice in adjacent sentences — once for the Arrhenius law for $K(T)$, once for calling Eq. permode "the standard permeation equation." Consider citing once and cross-referencing, or dropping the second instance.
- **Lines 385–387, "geometry of helium loss" repeated three times in three consecutive sentences** ("...the geometry of helium loss differs..." / "...in governing the geometry of the helium loss..." / "...the geometry of helium loss due to dehydration and helium diffusion may differ, implying..."). The third sentence in particular reads as close to restating the second. Consider tightening this passage.
- **Line 316, dangling "within":** "...the permeability rate constant is related to the volume fractions of the gas and condensed phases **within** according to the following relationship..." Reads a little elliptically; "within the ampoule" (or similar) would remove the ambiguity.
- **Line 122, single sentence carrying the whole SEM protocol:** "...unbuffered samples were heated either in vacuum in the lamp-heating apparatus of [Farley 1999] or in open air, while buffered samples were sealed in silica glass ampoules with fused sulfur, mineral realgar, or water for pyrite, arsenopyrite, and goethite respectively." This is grammatically fine now but is doing a lot of work in one sentence; could be split into an unbuffered-samples sentence and a buffered-samples sentence for easier reading.
- **Line 387 (last sentence of §5.9):** "This claim entirely rests upon the correctness of the ⁴He data reported here, for which each step yield is somewhat small..." — "somewhat small" is vague; if you have the actual range or a representative number more specific than "most often between 0.15 and 0.5 nccSTP" (already given a few words later), consider leading with that instead.
