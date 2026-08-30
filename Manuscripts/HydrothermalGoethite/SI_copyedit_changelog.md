# Copyedit changelog — hydrothermal_goethite_SI_body.tex

## Round 1 (initial copyedit pass: hanging references, grammar, formatting, spelling)

*(Reconstructed summary — the original Round 1 write-up was accidentally overwritten by the Round 2 write-up before you saw it. This section reconstructs it from my own working notes; the edits themselves were applied and committed correctly at the time, only this changelog entry was lost.)*

Scope this round: the SI body as it stood before you added back the finite-difference numerical model content, checked for hanging references (as you'd asked), plus a general grammar/typo/formatting/spelling pass.

- **LaTeX syntax error — fixed**: an orphaned `steps}\label{...}` fragment left over after a `\section{}` command, which would have broken compilation. Removed the stray fragment.
- **Hanging references — fixed** (4 total): `eq:eqn1` → `eq:permode` and `ch:apparatus` → main text `\S\ref{sec:bounding}` (both inferred from context — the surrounding text made the intended target clear); `fig:ch2-arrhenius-zoom` → `fig:arrhenius-zoom` and `fig:ch2-delta-zoom` → `fig:delta-zoom` (straightforward renames — these figures exist under the shorter label elsewhere in the document).
- **Hanging references — flagged, not fixed**: `fig:ch2-naive-arrhenius`, `\nameref{helium-4-blank-corrections}`, and `fig:long-step-relative-uncertainty` all pointed at content that didn't exist anywhere in the document (not a typo/rename situation — the referenced figures/sections were genuinely absent), so I left these for you to resolve rather than guessing. Also flagged: a stale header comment describing a "permeation step verification" section that no longer existed, and a title mismatch between the SI wrapper (`hydrothermal_goethite_GCA_SI.tex`) and the current main manuscript title.
- **Grammar** — 3 fixes (sentence-level corrections; specifics not retained in this reconstruction, but all were minor).
- **Formatting/consistency** — a batch of fixes: isotope superscripts (e.g. `\textsuperscript{3}He`), degree symbols, steady-state hyphenation, en-dashes, the `\pm` symbol, "1 sigma" → "1$\sigma$", and removal of accidental double spaces.
- **Spelling**: none found — LaTeX-aware spell check (`aspell --mode=tex`) flagged only legitimate technical terms, variable names, and citation keys.

## Round 2 (after you added back the finite-difference numerical model content)

Scope this round: the same file, after you restored a large amount of finite-difference/numerical-model derivation content (the new "Finite Difference Diffusion Model of Cooling Tube" section — numerical methods, the analytical steady-state concentration-profile derivation, and the parameterized cooling-rate subsection). I re-checked every `\ref`/`\eqref`/`\citep` target against both this file and the main body, re-ran the LaTeX-aware spell check, and re-verified brace balance, then read through the new content for clarity and flow. Test-compiled the SI standalone again (main-text cross-refs stubbed): clean, no LaTeX errors, 16 pages.

Good news on the cleanup front: most of what I flagged as "stale" last round is already gone. The old header comment block describing a missing "permeation step verification" section, the `\nameref{helium-4-blank-corrections}` dangling reference, the `fig:ch2-naive-arrhenius` and `fig:long-step-relative-uncertainty` references to figures that didn't exist, and the extra `EQM_Timescales_Permeation.pdf` figure are all gone from the file as it stands now. There is now exactly **one** figure in the SI — the cooling-rate parameterization plot (`fig:ch2-goethite-cooling-rate` / `goethite_cooling_rate_fit.pdf`) — so nothing needed removing on that front; it was already down to just that one.

### Hanging reference — fixed

- `Eq.~\eqref{eq:3}` (in "the geometric constant of permeation $G$ from Eq.~\eqref{eq:3}") pointed at nothing. The formula shown right next to it, $G = 2/(a^2\ln(b/a))$, is exactly the main text's `eq:geomfactor`, so I pointed it there: `main text Eq.~\eqref{eq:geomfactor}`. I also changed "geometric constant of permeation" to "geometric factor" in that sentence — the main text and the rest of the SI both call it "geometric factor," and "geometric constant of permeation" only appeared this once.

### Missing citation — fixed

- `\citet{carslawjaeger1959}` (Carslaw & Jaeger, cited for "the equation for the change in concentration by diffusion in a cylinder, eqn. 5, page 17, second edition") had no entry in `references.bib`, so it would have rendered as "?" in the bibliography. I added the standard entry for Carslaw, H. S. and Jaeger, J. C., *Conduction of Heat in Solids*, 2nd ed., Clarendon Press, Oxford, 1959 — this is an unambiguous, well-known reference, so I'm confident in the entry, but worth a glance since I can't confirm it's the exact edition/printing you have in hand.

### Corrupted text — fixed

- Right after "Letting $f(r) = \partial C_r/\partial r$ and $f'(r) = \partial^2 C_r/\partial r^2$:", the source had two garbled lines — `es elsewhere in this` followed by `% chapter.` — sitting between that sentence and the next equation. This reads like the tail end of a sentence that got cut off and corrupted during the paste (something like "...are used elsewhere in this [dissertation/chapter]" is my guess from the fragment, but I can't reconstruct the original with confidence). I removed the two stray lines rather than guess at what belongs there, so the sentence now flows straight into the equation that follows. Worth double-checking that nothing substantive was lost here — the note was likely just a self-reference to other dissertation chapters, which wouldn't apply in the standalone SI anyway, but I can't be certain that's all it was.
- Separately: the "Letting $f(r)=\ldots$ and $f'(r)=\ldots$" notation is defined here but $f$ and $f'$ are never actually used in the two equations that follow (they use $\partial C/\partial r$ and $\partial^2 C/\partial r^2$ directly instead). Not something I changed, since it's math notation rather than prose — but it reads as a leftover from a version of the derivation that did use the shorthand. Worth a look. *(Moot after Round 3 — this passage was cut along with the rest of the analytical derivation.)*

### Formatting / consistency

- **Steady-state**: 8 more instances of unhyphenated "steady state" as a compound adjective (steady-state permeation, quantity, condition, concentration ×2, value, and two instances of "steady-state concentration profile," one of them in a subsection title) hyphenated to match the rest of both documents. Left alone the 2 instances where "steady state" is a standalone noun phrase ("At steady state, dC/dt = 0"; "at steady state, the radial density is integrated") — those are correct as written.
- **Δx → Δr**: the CFL stability condition was written with $\Delta x$ even though the discretization uses $\Delta r$ everywhere else in the derivation (it's a radial finite-difference scheme, no $x$ anywhere). Fixed to $\Delta r$.
- **"insured" → "ensured"**: "numerical stability was insured by..." — wrong word (insurance vs. guaranteeing an outcome).
- **En dash**: "5-10%" → "5--10%" (surface area of ampoule end-caps vs. walls), matching the convention used everywhere else.
- **Capitalization**: subsection title "A Parameterized Cooling Rate of the Ht-Win-06-01b Ampoule" → "...HT-Win-06-01b Ampoule" (matches the sample designation used correctly everywhere else).
- **Missing blank line** after that same subsection heading, matching the blank-line-after-every-heading convention used throughout the rest of the file.

### Rewritten for clarity/flow

- "Which, by the product rule, can be expressed as:" — starts a sentence with "Which," which is a fragment. Changed to "By the product rule, this can be expressed as:". *(This sentence was part of the analytical derivation cut in Round 3.)*
- The lead-in to the FTCS discretization equation said helium concentrations are "updated according to the following equation" (singular), but two equations actually follow — the continuous PDE (repeated from Eq.~(s4-2) for reference) and then its discretized form. Reworded to say so explicitly: "...updated at each step using an FTCS discretization of the radially symmetric diffusion equation for a cylinder (Eq.~(s4-2)), repeated below for reference before its discretized form:" — so the repeated equation no longer reads as a mistake.
- The description of converting concentration to radial density ("by multiplying by the circumference of a circle with radius r and the cylinder height h") was slightly imprecise about what's actually being multiplied together. Reworded to "by multiplying by the surface area of a cylindrical shell of radius r and height h, i.e. its circumference $2\pi r$ times h" — same math, clearer about what quantity you're forming. *(This sentence was also part of the analytical derivation cut in Round 3.)*

### Spelling

None found this round either — same LaTeX-aware spell check, same result: every flagged token was a legitimate technical term, variable name, or citation key.

### Not touched

- The three main-text figure cross-references still in the file (`fig:ampoule-permeability`, `fig:arrhenius-zoom`, `fig:delta-zoom`) are all live, valid references to real main-text figures, used in the (unchanged) "Analytical Methods" section on diffusivity inversions and isotope-ratio uncertainty. I didn't remove these — they're not stale, and that content wasn't part of what you added back.
- I didn't touch any of the derivation's actual math (equations, subscripts, algebra) — only the surrounding prose, labels, and one dead reference. If any of the LaTeX math itself needs a check against your source, that's worth doing separately since I didn't re-derive anything.

## Round 3 (dropped the analytical steady-state derivation; switched the numerical model to burn-in initialization)

Scope this round: per your call to drop the 4-page "Analytical Solution for Diffusive Steady-State Concentration Profile" subsection (since it's only used to initialize the numerical model's starting concentration profile, it's preserved in your dissertation, and a numerical burn-in gets the same result with far less derivation), I removed that subsection from the SI and updated `data/goethite_thermal_sims.py` to match — the finite-difference model now initializes its concentration profile numerically instead of analytically.

### SI body (`hydrothermal_goethite_SI_body.tex`)

- **Deleted** the entire "Analytical Solution for Diffusive Steady-State Concentration Profile" subsection (the derivation from the general cylindrical diffusion equation down through the glass/gas partition ratio, Eqs. s4-2-2 through s4-7).
- **Preserved and relocated**: the subsection's opening derivation — the general cylindrical diffusion equation (Eq.~s4-1, citing \citet{carslawjaeger1959}) reduced to the radially symmetric form (Eq.~s4-2) — because "Numerical Methods" depends on Eq.~s4-2 and referenced it twice (this was actually a forward reference in the previous draft, since Eq.~s4-2 was defined later, in the subsection just deleted). It's now derived at the start of "Numerical Methods," right before its first use, so the equation is defined before it's cited.
- **Added**: a short paragraph at the end of "Numerical Methods" explaining that the initial concentration profile for a fresh charge of helium is now obtained numerically — hold the boundary conditions fixed at their values for that charge and temperature and iterate the FDM (Eq.~s5-0) until the profile stops changing (a numerical "burn-in" to steady state) — rather than via the closed-form analytical solution that used to live in the deleted subsection.
- **Reworded**: the Cooling Rate subsection's sentence "a steady-state concentration profile was assumed for the new arbitrary charge at T = 24°C" now reads "...was initialized at T = 24°C using the numerical burn-in procedure described in \S\ref{sec:numerical-methods}", cross-referencing the new paragraph above instead of an assumption that no longer has a derivation backing it in this document.
- **`carslawjaeger1959` bib entry**: unchanged — still cited (now in "Numerical Methods" instead of the deleted subsection), so the entry added in Round 2 stays in use.
- **Verified**: brace balance, full ref/citation resolution (every `\ref`/`\eqref`/`\citep` target confirmed to resolve, including the relocated Eq.~s4-1/s4-2), and a clean standalone compile test — 12 pages (down from 16, consistent with cutting roughly 4 pages of derivation).

### Numerical model script (`data/goethite_thermal_sims.py`)

- **`permeation_sim.__init__`**: previously computed the initial glass/gas partition (`nglass`) and the initial concentration profile (`c`) directly from the closed-form analytical steady-state solution (the dissertation's Eq. 1.35 and Eq. 1.32 — the same derivation that used to be in the SI). Replaced with: start from a "fresh charge" initial guess (all helium in the gas phase, empty glass, `c = 0` everywhere), then call the burn-in relaxation described below to reach steady state numerically.
- **`stabilize_profile()`**: this method already existed in your script (holds the boundary conditions fixed and runs the FDM for one diffusive equilibration timescale, `tauD = (b-a)^2/D`) but wasn't wired into `__init__` — it looks like exactly the burn-in approach you described, so I hooked it up rather than writing a new one. Two small fixes needed to use it safely from `__init__`: added a `verbose` flag (so the automatic burn-in during initialization runs quietly — the previous hardcoded `verbose=True` would have popped up a progress bar on every single simulation initialization) and passed `record=False` to its internal `hold_T` call (the burn-in was previously implicitly logging itself as a real "Hold T" experimental step in `reportmatrix` if called before `reportmatrix` existed, it would have crashed outright; now it's correctly excluded from the step record, since it's initialization, not a real step).
- **`reset()`**: an existing utility method (not currently called anywhere in the script, but present as a public method) had the same analytical-initialization pattern, plus a latent bug where it updated `S` for the new temperature but not `D` or `K`. Brought it in line with the same burn-in approach for consistency, and fixed the missing `D`/`K` update.
- **Verified**: for a representative case (T = 300°C initial charge), the burn-in reproduces the old analytical solution to within ~0.5% in the concentration profile and ~0.06% in the gas-phase inventory; the glass-phase inventory (`nglass`, a much smaller quantity) differs by ~4% relative, which is a small absolute difference given how small that term is. Ran the full 5×3 temperature/hold-time grid end-to-end with no errors (finishes in under 20 seconds) and confirmed the fitted rate constants still vary smoothly and monotonically across the grid as before.
