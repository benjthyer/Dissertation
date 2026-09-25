# nGibbs — Methods Section Outline

**Thesis chapter / manuscript. Annotated section tree.**

Scope decisions applied throughout:

- Derivative sidecars (dn/dP, dn/dT) and Sobolev/derivative-supervised training are **excluded**. No mention of JVP tangents, `tangent_project`, or derivative episodes.
- All released models are of the **Continuous Model** class. The earlier gated (classify-then-regress) architecture appears **only** in §4.1, and only far enough to motivate the continuous formulation.
- Level of detail is dissertation-methods: enough that a reader can reconstruct the *reasoning* and reproduce the *procedure*, with implementation detail deferred to the public repository.
- All quality metrics, accuracy figures, timings, and comparisons against MELTS/HeFESTo belong in **Results**. Methods states *what was measured and how*, never *what the value was*.

Each bullet names what the subsection must establish, not prose to be copied.

---

## 1. Overview and Design Rationale

### 1.1 The computational problem

- State the forward problem free-energy minimizers solve: given bulk composition and two intensive state variables, find the assemblage, phase compositions, and phase abundances that minimize (or, for the isentropic case, the appropriate potential of) the system.
- Name the two reference codes and their domains of application: MELTS/pMELTS for crustal–lithospheric melting and crystallization; HeFESTo for the deep mantle to the core–mantle boundary. Cite both.
- Establish the cost argument that motivates the whole chapter: minimization is iterative, sequential along a P–T path, and does not vectorize; the applications that need it (inversion, Monte Carlo over composition, coupled geodynamic models, large parameter sweeps) need 10⁵–10⁸ evaluations. State the bottleneck qualitatively here; quantify it in Results.

### 1.2 What is emulated, and what is not

- **Central design commitment, stated once and early:** the network emulates only the *chemical* solution — which phases are present, in what molar abundance, with what endmember compositions. It does **not** predict density, seismic velocity, moduli, or heat capacity.
- Justify: those are algebraic consequences of the assemblage through the equations of state, which are exact, cheap, and already implemented. Learning them would (i) duplicate information the assemblage already carries, (ii) permit thermodynamically inconsistent output (a density that does not correspond to any assemblage), and (iii) forfeit the ability to propagate the reference code's own EOS parameters.
- Consequence: the emulator output is a *physical object* (an assemblage), not a vector of numbers, and can be handed to any downstream calculation that accepts one.
- Name the two exceptions and defer them to §8: temperature along an isentrope, and optional non-chemical "free outputs".

### 1.3 Emulator families

- Table or short list of the model families: MELTS 1.0.2 / 1.2 / pMELTS; HeFESTo Earth; HeFESTo Mars. For each: the code emulated, the intensive pair (isothermal vs. isentropic), and the compositional basis (Cr-bearing vs. Cr-free).
- State the governing principle behind splitting the family rather than training one general model: each model sees only compositions inside its own training distribution, and model selection at inference is deterministic and header-driven (§9.3).
- Note that the buffered-fO₂ variants are infrastructure-complete but not released, so that the chapter's claims are scoped to closed-oxygen models.

### 1.4 Chapter roadmap

- One short paragraph mapping §2–§9 onto the pipeline: state space → data generation → data processing → architecture → constraint enforcement → objective → training protocol → auxiliary networks → inference.
- A single schematic figure is worth its space here: raw simulations → indexed table → ML-ready bundle → trained model package → inference API → properties. Reuse the repository's architecture diagram, redrawn.

---

## 2. Problem Formulation and State Space

### 2.1 Inputs

- Define the feature vector: pressure, one of temperature or specific entropy, and the bulk composition expressed as normalized element molar abundances (oxygen excluded from the normalization; state the convention explicitly).
- State that oxide weight percent input is accepted at the API boundary and converted internally, and that ferrous/ferric iron is carried as a genuine degree of freedom when both FeO and Fe₂O₃ are supplied.
- Justify entropy as an alternative to temperature: isentropic paths are the natural coordinate for mantle adiabats, and supplying S directly avoids an inner iteration for T at each pressure step.

### 2.2 Outputs

- Define the three coupled prediction targets and their dimensions:
  1. per-phase molar abundance, one scalar per phase;
  2. per-phase endmember (component) fractions, a simplex per compositionally variable phase;
  3. the product of the two — component moles — which is the quantity mass balance acts on and the quantity the EOS engine consumes.
- Emphasize that (3) is not a separate head but the composition of (1) and (2), so mass balance constrains both jointly.
- Note that phase presence/absence is *not* a separate output in the continuous architecture; it is the sign of the abundance. Forward-reference §4.2.

### 2.3 Compositional bases and projections

- Define the three bases and the dimension symbols used throughout: components (C), oxides (O), elements (E), phases (P), compositionally variable phases (VP), components in variable phases (VC). Note O = E + 1 because of ferric iron.
- Present the linear maps between bases as fixed matrices (component→oxide, oxide→element, and their composition component→element). State that these are exact stoichiometry, not fitted, and are model constants.
- Explain the all-positive component remapping (the Px–Sp transform): certain pyroxene and spinel endmember sets admit negative component amounts in their native formulation, which is incompatible with a softmax parameterization. The transform is an invertible change of component basis chosen so that all admissible compositions have non-negative coordinates, and reduces to the identity for every phase not affected. This is worth a displayed equation and a sentence on invertibility.

### 2.4 The dataset indexer

- Explain that the model's output geometry is *derived from the data*, not hand-specified: the set of elements, phases, and components is read off the column headers of the training table and compiled into an indexer object.
- List what the indexer carries: phase and component orderings, the phase→component index maps, the projection matrices above, the input normalizer state, and the per-phase abundance scale T₀ (§3.5).
- State the provenance property that matters for reproducibility: **the indexer is serialized inside both the dataset bundle and every trained model package**, so a model always knows the exact basis it was trained in and cannot be silently applied in another.
- Note the one operational consequence worth recording: when episodes warm-start from earlier checkpoints, the indexer from the current training bundle is treated as canonical, so late-added quantities are not lost through a chain of checkpoints.

### 2.5 Normalization

- Min–max normalization of the full feature vector to [0,1], with the ranges fit on the **training split only** and inherited by validation, test, and inference.
- State why this is not a detail: an independently fit validation normalizer would present the network with inputs on a different scale than it was trained on, which is a silent, plausible-looking failure. Zero-range features are passed through rather than divided by zero.
- Note the normalizer travels in the model package, so inference normalization is identical to training normalization by construction.

---

## 3. Training Data Generation

> Ordering note: this section is about *sampling design*, not about running software. Keep the cluster mechanics to one compact subsection and push command-level detail to the repository.

### 3.1 Bulk composition sampling

- Source: GEOROC and PetDB whole-rock analyses. State the filtering applied per model family (e.g. the MgO threshold used to target mantle-relevant compositions for the HeFESTo models) and the rationale — training density should follow the compositions the emulator will actually be asked about.
- Iron speciation: describe the Fe³⁺/ΣFe grid used to spread each sampled composition across an oxidation range, and state the range. Justify: oxidation state is a genuine input dimension, and natural analyses report it inconsistently.
- Oxide exclusions and zeroed components per family (e.g. MnO, NiO), with the reason (unsupported by the reference model, or negligible and basis-inflating).
- State the composition→element-mole conversion convention and the total-mole normalization target.

### 3.2 State-variable sampling

- **Isothermal / MELTS families:** describe the P–T grid design — pressure range, temperature range or cooling path, isobaric versus polybaric paths, batch versus fractional modes — and which of those are represented in released models.
- **Isentropic / HeFESTo families:** describe how each simulation's P–T path is generated. An analytic potential-temperature ↔ entropy regression supplies a reference adiabat for a sampled potential temperature and Ca content; the path is written as an explicit list of (P, T) steps with small random perturbation added so that the training set covers a neighborhood of the reference adiabat rather than a measure-zero curve. Say plainly that this perturbation is the reason the emulator can later be asked about off-reference states at all.
- Present the reference-adiabat regression as a displayed equation if it is used again in §8.1 (it is). Give its provenance and its intended domain.

### 3.3 Execution

- **MELTS:** alphaMELTS driven by parallel shell invocations; state version numbers. One or two sentences.
- **HeFESTo:** SLURM array jobs on the Caltech HPC cluster. Describe the unit of work (one directory per simulation, containing a control file and a P–T path file), the batching into array jobs, and queue-aware staggered submission for large campaigns. Report the scale of the campaigns actually run (number of simulations, number of rows) — this belongs in Methods because it defines the dataset, not in Results.
- State the failure mode and its handling: a fraction of simulations do not converge or terminate without output; these directories are detected and dropped at import. Report the attrition rate, since it bears on whether the sampled distribution equals the achieved distribution.

### 3.4 Import to a single indexed table

- Describe parsing of the reference codes' output files into one wide table whose columns follow the `quantity(phase)` convention that the indexer later reads.
- Enumerate what is retained per row: state variables, bulk composition, phase assemblage, per-phase component molar abundances, per-phase masses, and the bulk properties reported by the reference code (retained for validation, not as training targets — cross-reference §1.2).
- Note the metadata sidecar (run identifiers, code version, run parameters) and its role in provenance.

### 3.5 Coverage and the domain-of-validity claim

- Summarize, per released model, the achieved envelope in P, T or S, and composition. Figures: a P–T coverage density map and a bulk-composition projection (e.g. Si–Mg) are the right two.
- State the scoping claim explicitly and once: the emulator is a *fit*, not a theory, and no accuracy claim is made outside the sampled envelope. This is the honest boundary of the method, and stating it here prevents having to hedge repeatedly in Results.

---

## 4. Data Processing to Training Bundles

### 4.1 Large-table handling

- Memory-mapped, chunked parsing of the compiled tables; state the scale this is designed for and why in-memory dataframes are not viable. Keep it to a few sentences — it is engineering, and the code is public.

### 4.2 Physical consistency filters

- List the filters and, for each, the physical inconsistency it removes. At minimum:
  - rows where a phase has zero mass but non-zero derived properties (or vice versa);
  - rows whose reconstructed bulk composition disagrees with the stated bulk composition beyond tolerance;
  - phases below a minimum modal proportion, which are numerically present but chemically meaningless;
  - phases too rare in the dataset to be learned at all, removed from the basis (and propagated to the validation and test tables so the bases match);
  - optional per-phase compositional bounds used to remove known pathological assignments.
- State the tolerances used and the fraction of rows removed at each stage. Assert-style guardrails (a filter that removes more than a few percent is treated as an error, not a cleanup) are worth one sentence, because they are what makes the numbers trustworthy.

### 4.3 Balancing and augmentation

- Explain the imbalance problem concretely: raw simulation output is dominated by common assemblages and by whichever region of the path is sampled most densely (e.g. subsolidus rows, or a narrow melt-fraction band). Unweighted training then buys mean accuracy at the cost of exactly the boundaries of interest.
- Describe the mechanisms and say which were used for which released model:
  - **culling-based balancing** across melt fraction (or the relevant continuous covariate), to flatten a strongly peaked distribution;
  - **rare-phase upsampling**, where rows containing a targeted phase are replicated;
  - **modal resampling**, where phase abundances within an equilibrium assemblage are perturbed by a bounded multiplier while intensive compositions are held fixed. State the justification for why this is a legitimate augmentation and not label noise — and state its limit, since the perturbed row is not itself an exact equilibrium.
  - Note that test/validation augmentation, where used at all, uses much tighter bounds, and why.
- Be explicit about which of these are enabled in the released configurations. If a mechanism exists but was not used, say so in one clause rather than describing it at length.

### 4.4 Feature and label arrays

- Enumerate the bundle's arrays and define each: features; per-phase molar abundances; intensive component fractions; binary presence labels; phase masses; optional free outputs.
- State the storage convention for molar abundance (linear, versus the logarithmic convention the earlier architecture required) and forward-reference §5.2, where the continuous model's target transform is defined.

### 4.5 The per-phase vanishing-abundance scale, T₀

- Define T₀ as a low percentile (state which) of the distribution of a phase's **non-zero** molar abundance across the filtered training set — i.e. "how small does this phase's abundance get before the data calls it absent", estimated per phase from data rather than assumed globally.
- Give the motivation now, because §6.4 depends on it: phase abundances span orders of magnitude between a dominant phase and a trace one, so any single global threshold or smoothing width is wrong for most phases.
- State that it is computed after filtering, on the final labels, and stored in the bundle and hence in the model.
- Note the degenerate case (a phase never present in this dataset) and how it is handled.

### 4.6 Bundle contents and provenance

- List what travels with the data: arrays, indexer, the processing configuration that produced it, and a statistics summary.
- State the reproducibility claim this buys: any bundle can be traced to the configuration that made it, and any model to the bundle it was trained on.

### 4.7 Splitting

- **State the splitting rule prominently, because it is the single most consequential methodological choice in this section:** the split is by *unique bulk composition*, not by row. All rows sharing a composition — that is, an entire P–T path — go to the same partition.
- Justify: rows along one path are strongly autocorrelated; a random row-wise split would place near-duplicates on both sides and inflate held-out accuracy without measuring generalization to a new rock.
- State the fractions, the seed handling, and the roles of the three partitions: training; a validation partition used every epoch for model selection and early stopping; and a held-out partition touched only for final evaluation (whose results appear in Results).

---

## 5. Network Architecture

### 5.1 Why a continuous saturation formulation

- Set up the failure mode of the natural design. A gated architecture predicts presence with a classifier and magnitude with a regressor; the predicted abundance is the magnitude multiplied by a thresholded gate. Because gate and magnitude are different variables, crossing the decision threshold makes abundance jump discontinuously from a finite value to zero, and nothing in the objective ties the size of that jump to zero.
- Contrast with the physics: at a phase-out boundary, abundance goes to zero *continuously*, linearly in reaction progress. The gated model is therefore wrong precisely at the boundaries that phase diagrams are made of.
- State the fix in one sentence: make gate and magnitude the *same* variable.

### 5.2 The saturation variable

- Define the three stages of one per-phase scalar and give them displayed definitions:
  - a raw branch output *g* (read physically as an affinity),
  - a signed saturation *m* = leaky ReLU(*g*), which is what the mole regression loss operates on,
  - the physical abundance *n* = max(*m*, 0), which is what everything downstream uses.
- Show that the composition is continuous at zero because the leaky branch passes through the origin, so phase-out is a kink rather than a step, while *n* still attains **exact** zeros and therefore exact sparsity.
- Make the thermodynamic connection explicitly: the complementarity condition (abundance non-negative, affinity non-negative, product zero) is exactly what a rectifier encodes. This is the argument that elevates the design from a numerical trick to a physical parameterization, so give it its own short paragraph.
- Define the target transform: because labels are stored in the earlier architecture's logarithmic output space, targets are converted back to linear moles rather than asking the network to reproduce a transform that is undefined at zero — the one place the continuity actually matters.

### 5.3 Encoder and shared representation

- Describe the encoder as a configurable-geometry MLP (expanding then contracting layer stack; leaky-ReLU activations; optional layer normalization and dropout), and state that the working representation is the encoder output **concatenated with the raw input**, so that the heads retain direct access to pressure, entropy, and bulk composition rather than only a learned summary.
- Note that the architecture has no separate saturation sub-network — a deliberate consequence of §5.2 — and that the encoder is what the earlier design called its middle stage.

### 5.4 Chemistry heads

- One head per compositionally variable phase, producing a softmax over that phase's endmembers. State why softmax is the right parameterization (the target is a simplex) and connect back to §2.3 for why the component basis had to be made all-positive first.
- Describe **admissibility masking**: endmembers requiring an element absent from the bulk composition are masked out before the softmax, so the network is not asked to learn a constraint that is known exactly. State how a fully masked phase is handled.
- Note the optional single hidden layer in the chemistry head, and the deliberate decision not to give it its own depth-search space.

### 5.5 Abundance heads

- One branch per phase, each an MLP mapping the shared representation to a single unactivated scalar (*g* above).
- Describe and justify **chem-first conditioning**: the branches receive the endmember fractions alongside the shared representation. Given the endmember compositions and the bulk, mass balance nearly determines the abundances through a linear system, so supplying the chemistry lets the branches approximate that solve instead of rediscovering it. State that this is concatenation, not replacement — a branch can ignore it — and that a parallel (unconditioned) variant exists as a configuration.
- Give the assembly step: component moles are the per-phase abundance distributed over that phase's endmember fractions, with compositionally fixed phases handled by their constant composition vectors.

### 5.6 Numerical precision

- Keep this short but do not omit it. State that the abundance branches and the boundary-smoothing arithmetic of §6.4 are evaluated in single precision regardless of any ambient mixed-precision context, and give the reason in one sentence: the smoothing width anneals to a small fraction of an already small per-phase scale, and reduced-precision quantization of *g* would exceed that width before the schedule finishes — destroying exactly the behavior the scheme exists to control. The encoder and chemistry heads retain the mixed-precision speed benefit.

### 5.7 Model packaging

- Describe the trained-model artifact: weights, architecture configuration, the indexer, and the processing/training configurations, statistics, and log carried alongside.
- State the property this guarantees: a released model is self-describing and can be loaded without the repository that trained it.

---

## 6. Constraint Enforcement and the Objective

### 6.1 The mass-balance constraint

- State the constraint: the element totals implied by the predicted component moles must reproduce the input bulk composition. Note that only the *direction* is constrained, since the bulk is supplied normalized, and say why the scale is rebuilt each iteration rather than held fixed.
- Emphasize why this cannot be left to the loss alone: mass balance is not a soft preference, and a downstream user integrating an emulated assemblage needs conservation to hold, not to hold on average.

### 6.2 The projection operator

- Present it as a support-restricted, damped, minimum-norm correction: at each of a small fixed number of iterations, the residual between the implied and target element vectors is mapped back onto component space through the transpose of the stoichiometry matrix, restricted to the currently present phases, and the result is clamped non-negative. Give the displayed update, including the Tikhonov term.
- Make the two arguments that justify the design:
  - **Support restriction is physical**: a phase that has left the assemblage must not participate in a mass-balance reaction, so the correction is confined to phases with positive abundance.
  - **The iteration terminates rather than merely converging**: entries can only leave the active support, never re-enter, so the support is monotonically non-increasing — unlike generic alternating projection, whose convergence rate degrades precisely near phase-out.
- Note the conditioning safeguards (regularization applied in double precision; the solve is a small batched system in the element dimension, so the cost is negligible) and report the residual the operator returns as a diagnostic.

### 6.3 The training objective

- State that the projection is applied at **inference**, while at training the network is scored on its *pre-projection* output, with the mass-balance residual entering as a loss term. Give the reason: the post-projection residual is zero by construction and carries no gradient, so scoring it would teach nothing; penalizing the pre-projection residual instead pulls the raw heads toward the feasible manifold and reduces how much repair the projector must do at inference.
- Enumerate the four terms with their functional forms and their roles:
  1. **Chemistry** — a symmetric relative L2 on predicted endmember fractions, masked to admissible components. State why a *relative* measure: endmember fractions within a phase span orders of magnitude and an absolute error would be dominated by the major endmember.
  2. **Abundance** — a Huber loss on the signed saturation *m*, with the stated delta. Note the key contrast with the gated model: absent phases are supervised **toward zero** rather than excluded from supervision, because the behavior at and below zero is the entire point of the architecture.
  3. **Presence** — a binary cross-entropy on *g* treated as a logit. Justify why this term is retained at all given that abundance is already supervised: the Huber term is minimized *at* zero and therefore gives essentially no gradient distinguishing a confidently-absent phase from a marginally-absent one, leaving a decision boundary that noise can flip.
  4. **Bulk residual** — a symmetric relative L2 on the pre-projection element-mole direction, as motivated above. State that it is opt-in, that it is numerically delicate, and that in the released recipes it is enabled only after the abundance branches have been trained (§7.2).
- State the relative weights actually used, and the overall loss scaling applied for optimizer conditioning.

### 6.4 Boundary-temperature annealing

> This is the most novel piece of the training method and deserves its own subsection with equations.

- Restate the problem it solves: near a phase boundary the abundance loss has vanishing gradient and the presence loss is fighting the kink at *g* = 0. Both losses are weakest exactly where the model's accuracy matters most.
- Define the annealed smoothing scale as a per-phase temperature *T* = *a*·T₀, with T₀ the data-derived scale of §4.5 and *a* a scalar annealed on a linear schedule from a soft start to a sharp end **within each training episode**.
- Give the three coupled modifications, each with its equation and its rationale:
  - The regressed abundance becomes a temperature-scaled softplus of *g* in place of the hard rectifier. State the gradient this induces (a sigmoid in *g*/*T*), why it is well conditioned near the boundary, and why it *vanishes* — rather than merely shrinking — for confidently absent phases, so the loss stops pulling them back toward zero. Give the bias against the hard target, note that it is symmetric, bounded, and shrinks with *T*, so it is annealed away by construction rather than being a separate error to correct.
  - The presence logit is scaled by the **fixed** T₀, not the annealed *T*, so that the classifier's calibration means the same thing at every point in the schedule. State the scaling constant and what confidence it corresponds to at one T₀.
  - The presence term carries a per-sample confidence weight that vanishes at the boundary and saturates within a few *T*, using the **annealed** *T*. State the division of labour this produces: the well-conditioned abundance loss owns fine calibration near the boundary; cross-entropy owns dragging back samples that are confidently wrong far from it.
- Note that the scheme is opt-in per episode and that recipes not enabling it recover the unsmoothed objective exactly — relevant because the released models are trained through a mix of both.

### 6.5 Per-phase loss weighting

- Describe the weighting scheme: one weight per phase applied to the abundance, presence, and chemistry terms (never to the bulk term, which has no per-phase notion), with optional axis-specific overrides.
- State the rationale — rare phases are starved of gradient in proportion to their rarity — and name the phases actually upweighted in the released configurations, with a word on why each is difficult.
- State and justify the asymmetry: on the presence term, weights are applied only to the ground-truth-positive contribution. Upweighting a rare phase's already-numerous negatives would rescale the loss without changing what the network is pushed toward.

---

## 7. Training Protocol

### 7.1 Episode-based orchestration

- Describe training as an ordered sequence of episodes declared in a configuration file, each an independent training or hyperparameter-search stage with its own epochs, learning rate, schedule, loss weights, frozen heads, and — where useful — its own architecture.
- State the configuration precedence (per-episode overrides above run-level globals above code defaults) and the warm-start rule: each episode initializes from the previous episode's best model, with compatible weights transferred across architecture changes and mismatched modules reinitialized.
- Justify why this is the right structure for this problem rather than a single training run: the outputs are strongly coupled but not equally learnable, and the mass-balance argument of §5.5 means the abundance branches are only well posed once the chemistry heads are informative.

### 7.2 The staged curriculum

- Lay out the stages used for the released models and the reason for each:
  1. encoder and chemistry heads trained together, with the abundance branches frozen;
  2. abundance branches trained on top of a fixed chemistry representation;
  3. a joint stage with all heads unfrozen, with the bulk residual term enabled and the boundary-temperature schedule active.
- State the head-freezing mechanism at the level of intent (a stage names which parts of the model it holds fixed) and note that names referring to structures the continuous architecture does not have are explicit no-ops, not errors — a small but real reproducibility point when older recipes are rerun.
- Note the deliberate exclusion: no separate binary/saturation pretraining stage exists for these models, because there is no separate saturation head to pretrain.

### 7.3 Optimization

- Optimizer, learning rates per stage, and the AMSGrad/epsilon settings used, with a sentence on why the epsilon matters given the loss scaling of §6.3.
- **Weight-decay routing:** decay is assigned by which part of the model a parameter belongs to — encoder, chemistry heads, and abundance branches are treated differently, with the abundance branches held at zero decay. State the reason: decay on a branch whose output is a signed affinity biases the phase-boundary location itself.
- Schedulers used (cosine annealing, one-cycle), with the note that one-cycle stages are used less for convergence than as deliberate stochastic perturbation to escape local minima between episodes.

### 7.4 Adaptive regularization

- Describe the controller: dropout rate is raised when validation loss exceeds training loss by a set margin and lowered when it falls below, within bounds declared per stage; input noise is adjusted only when dropout is already at its ceiling or floor.
- State that dropout layers are wired into the graph at rate zero from the start so that the rate can be changed without changing layer shapes or invalidating warm starts.
- Note the honest caveat: this makes the effective regularization a function of the training trajectory, so it is reported per run rather than as a fixed hyperparameter.

### 7.5 Model selection and stopping

- Validation loss is evaluated every epoch on the composition-disjoint validation partition, under the same boundary temperature the epoch trained at.
- **Baseline guarding:** the incoming model is evaluated before training begins and treated as the epoch-zero candidate, so a stage that never improves on its own starting point cannot overwrite a better checkpoint. Worth stating explicitly — it is a real result-integrity safeguard, not bookkeeping.
- Early stopping with a per-stage patience; best-epoch weights restored at the end of each stage.
- Diagnostics recorded per epoch: the distribution of the normalized affinity *g*/T₀ across phases, and the residual between predicted and true abundance for samples near a phase boundary. State that these are monitoring quantities; their values belong to Results.

### 7.6 Hyperparameter search

- Describe the search as a greedy coordinate procedure rather than a Bayesian or random search: parameters are visited in turn, each candidate value is trained from a common anchor checkpoint, and the best is locked before moving to the next.
- Distinguish the two search modes used: a structural stage over layer geometry, and a hyperparameter stage over regularization, weight decay, and noise. State that architectural candidates are ordered by complexity and always include the current configuration as an origin.
- State the constraint on interpretation, since it affects how search results may be read: candidate losses are only comparable within a single sweep against a common baseline, and are not comparable across stages with different objectives or weights.
- Justify the choice of method honestly: episodes cost hours to days on the datasets at hand, the parameters are few and largely separable, and a warm-startable greedy search that reuses the anchor is a better use of a fixed compute budget than an independent-trial search.

### 7.7 Computational environment and scale

- Hardware for training (workstation GPU class, memory) and for data generation (cluster). Software versions: Python, PyTorch, CUDA, alphaMELTS, HeFESTo.
- Mixed precision: state the setting used, that it is confined to the encoder and chemistry heads, and cross-reference §5.6 for what is excluded.
- **Large-dataset handling** — give this real space, since it is what made the current dataset scale tractable:
  - all per-row transforms (label basis transform, feature normalization, out-of-bounds filtering) are applied once and cached as a memory-mapped workspace keyed by a fingerprint of the bundle and transform parameters, so the cost is paid once and amortized across every subsequent run and every episode;
  - above a configurable memory threshold, training streams from that workspace through a chunk-shuffled, asynchronously prefetched loader instead of materializing the dataset in RAM, with a random per-epoch chunk order and an in-chunk shuffle;
  - state the shuffling compromise plainly: this is chunk-level rather than global shuffling, and note the mitigation (rows are shuffled once at bundle creation).
- Report the wall-clock scale of a full training campaign. Detailed throughput benchmarking belongs in Results.

---

## 8. Auxiliary Networks

### 8.1 Temperature along an isentrope

- State the problem: an isentropic model takes (P, S, X) as input, but users need T, and T is not recoverable from the assemblage alone without an inner solve.
- Describe the solution as **residual regression against an analytic reference**: the target is the difference between the true temperature and the reference adiabat of §3.2 evaluated at the same pressure and entropy. Give the equation.
- Justify the residual formulation over direct regression: the reference already captures the leading-order behavior over the whole mantle pressure range, so the network learns a small, well-scaled correction; errors are bounded by the correction's magnitude rather than by the absolute temperature; and the model degrades gracefully toward a physically sensible prediction rather than an arbitrary one.
- Describe the input vector: state variables together with the predicted assemblage — molar abundances and intensive compositions — so that the correction is conditioned on the phase assemblage that actually sets it.
- State that two variants are trained: one on emulator-predicted assemblages and one on ground-truth assemblages. Explain what each isolates — the first is the deployed model and inherits the emulator's own error; the second bounds how much of the temperature error is attributable to the temperature network alone. This separation is what makes the Results error budget interpretable, so set it up here.
- Note the architecture briefly (configurable-geometry MLP regressor with the same adaptive-regularization and early-stopping machinery as §7.4–7.5) and the bundle roles used for validation and holdout.

### 8.2 Free outputs

- Define free outputs as non-chemical scalars carried through the bundle and optionally regressed from features plus predicted assemblage.
- State which, if any, are used in the released models, and why the mechanism exists (properties the reference code reports that are not derivable from the EOS engine).
- Keep this short if the released models use only the temperature case — say so rather than describing capability at length.

---

## 9. Inference

### 9.1 Forward paths

- Define the two exposed paths and the tradeoff between them:
  - a network-only pass, fastest, no conservation guarantee;
  - a mass-balanced pass, which applies the projection of §6.2 and returns an assemblage that conserves mass to solver tolerance.
- State which is used for the results reported in the chapter, and note the optional additional mass-polishing step and when it is warranted.

### 9.2 Input handling

- Header-driven column identification; acceptance of oxide weight percent or element mole input; the iron speciation rule when only total iron is supplied; unit conventions per model family (state them in a small table, since MELTS and HeFESTo differ in pressure and temperature units).
- Note validation performed on input: composition normalization, and behavior when an input falls outside the training envelope. State plainly whether the emulator warns, extrapolates, or refuses — a reader needs to know.

### 9.3 Automatic model selection

- Describe the deterministic routing: chromium content selects between the Cr-bearing and Cr-free families; the supplied intensive variable (temperature versus entropy, read from the headers) selects the isothermal or isentropic model.
- Justify the split-model design over a single general model: each model then only ever sees compositions from its own training distribution, and a Cr-free query is not silently answered by a network whose chromium dimension is unconstrained.
- State the buffered-fO₂ route as infrastructure present but unreleased, in one sentence, so that the routing description is complete without overclaiming.

### 9.4 Isentrope construction

- Describe the composed procedure that produces a full adiabatic profile: for a bulk composition and a set of potential temperatures, entropy is obtained from the potential-temperature relation, the isentropic network is evaluated over a pressure grid, temperature is supplied by the residual network of §8.1, and aggregate properties follow from §9.5.
- Note that this is the point at which the separately trained components compose, and that each therefore contributes to the profile's error budget — forward-reference to the Results decomposition.

### 9.5 Deterministic property evaluation

- Describe the vectorized equation-of-state engine as a **direct translation of the reference code's own thermodynamic routines**, not a learned or refitted model, operating on component moles at given (P, T) and aggregating over phases by Voigt–Reuss–Hill averaging.
- List the properties returned and their units in a table.
- State the two ways component moles reach it — imported from reference-code output, or predicted by the emulator — and note that the first path is what allows the engine itself to be validated independently of the network. This separation is essential to the Results structure, so establish it here.
- One sentence on batching and device placement; timings belong in Results.

---

## 10. Software Availability and Reproducibility

- Repository location, license, and archived release DOI; citation file.
- The two-tier distribution: a lightweight inference package containing trained weights, the indexer, and the API; and the full development repository containing data generation, processing, and training infrastructure. State which is needed for which purpose.
- What is released alongside each model: weights, architecture configuration, indexer, and the processing and training configurations that produced it — so that any reported number is traceable to a configuration.
- Data availability: source composition databases, and the disposition of the generated simulation output and ML-ready bundles (archived, available on request, or regenerable from the released configurations — state which, plainly).
- Random-seed and determinism statement, including an honest note on the sources of run-to-run variation (adaptive regularization trajectory, chunk-shuffled loading, non-deterministic GPU kernels).

---

## Notes for drafting

**Figures this section should carry** (four to five; more belongs in Results):

1. Pipeline schematic — simulations → indexed table → bundle → model → API → properties.
2. Architecture diagram — encoder, skip concatenation, chemistry heads, chem-first abundance branches, assembly, projection.
3. The saturation variable — *g* → *m* → *n*, plotted, with the softplus-smoothed variant overlaid at two annealing temperatures. This one figure carries §5.2 and §6.4 together and is the most valuable in the section.
4. Training-data coverage — P–T density and a bulk-composition projection.
5. Optional: the episode/curriculum timeline, if §7.2 proves hard to follow in prose.

**Equations worth displaying** (roughly ten): the all-positive component transform; the saturation composition; the complementarity condition; component-mole assembly; the mass-balance constraint and the projection update; the four loss terms; the annealed temperature and the softplus-smoothed abundance; the temperature-residual target.

**Boundaries to hold:**

- No accuracy numbers, no timings, no comparisons to the reference codes. Where the temptation is strongest — §3.5 coverage, §7.7 scale, §9.5 cost — state *what was measured* and cross-reference Results.
- Dataset-defining counts (simulations run, rows retained, attrition at each filter, split fractions) **do** belong in Methods. They describe the experiment, not its outcome.
- Justify every non-obvious choice in one or two sentences at the point it is introduced. The distinctive contributions here are the continuous saturation formulation, the terminating support-restricted projection, the data-derived per-phase boundary temperature, and the composition-disjoint split — each should read as a decision with a reason, not as a description of what the code does.

**If this becomes a manuscript rather than a thesis chapter:** compress §3.3, §4.1, §7.1, and §7.7 to a few sentences each and move them to supplementary material; keep §5.2, §6.2, and §6.4 at full length, since they are the methodological contribution.
