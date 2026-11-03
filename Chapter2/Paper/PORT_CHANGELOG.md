# Chapter 2 -> GCA manuscript port (2026-11-02)

Built by `build_paper_from_chapter2.py` from `Chapter2/Writing/chapter2_body.tex` and `chapter2goethite_SI_body.tex` (line numbers below refer to those files as of 2026-11-02). Body text is moved verbatim; every wording change is listed as EDIT, every new string as NEW, and every removal as CUT. Full-line LaTeX comments were dropped throughout. The abstract and conclusions were rewritten.

- **MOVE** [1 Introduction] Thesis L4-157 verbatim (Introduction + SEM Figs. control/vacuum, buffered, vacuum interior).
- **EDIT** [2 Methods (heading)] Section renamed: it now also holds the thermodynamic/nucleation model (moved from the Discussion).
    - was: "\section{Experimental Methods}"
    - now: "\section{Methods}"
- **MOVE** [2 Methods para 1-2] Thesis L161-178 verbatim (sample, irradiation, previous vacuum step heats). TODO comment on the 180-135 vs 130-180 Ma age range dropped with the other comments -- still unresolved, see changelog.
- **CUT** [2 Methods para 3] Ampoule preparation (cleaning, pulling, loading, freeze-pump-seal) offloaded to the Geochronology preprint.
    - deleted: "Silica glass was chosen over other laboratory glasses such as borosilicate because it is the most permeable glass type to helium \citep{norton1953,altemose1961}. To prepare the silica glass tube, 10 cm long segments of pure silica glass tubes with an outer diameter of 4 mm and an inner diameter of 3 mm were submerged and sonicated within acetone, ethanol, then MilliQ water baths in sequence, and then were dried overnight in a 100°C oven. The glass tubes were hand-pulled into thinner pipettes using a natural gas and oxygen glass-welding torch and the pipette ends were fused closed. After the gl ... [2532 chars]"
- **EDIT** [2 Methods para 3] Citation added in place of the cut ampoule-preparation text.
    - was: "within a silica glass tube."
    - now: "within a silica glass tube following \citet{thyer2026method}."
- **MOVE** [2 Methods] Fig. ch2-ampoule-post (sealed ampoule after the experiment) kept: it is cited in the recrystallization discussion.
- **MOVE** [SI S1] Fig. ch2-ampoule-dims (ampoule diameter photo, thesis L235-240) moved to the SI, next to the G calculation that cites it.
- **CUT** [2 Methods] Thesis L242 \clearpage.
- **CUT** [2 Methods para 5] Early-trial ampoule bursting pressures (86 bar at 300 C, explode >315 C): apparatus material, offloaded.
    - deleted: "In early trials, we found that similar ampoules most often withstood the \textasciitilde86 bar vapor pressures associated with liquid water saturation at 300°C \citep{haar1984}, but they would explode when further heated to temperatures beyond 315°C."
- **CUT** [2 Methods para 6] Thesis L271-275 (encapsulated vs bare Durango apatite as a temperature check): validation of the method, now in the Geochronology preprint.
- **CUT** [2 Methods para 7] Mass-spectrometer peak-centering / overspray detail cut (routine; generic to the instrument).
    - deleted: "The majority of the analysis time was spent measuring 3He. Every few hours, the background was mass-scanned to set the 3He and 4He measure points; each was taken to be a constant mass offset from the background HD\textsuperscript{+} peak. These mass offsets are precisely measured when tuning the Helix-MC-Plus\textsuperscript{10K} for helium isotope analysis. Months of helium measurements with the Helix-MC-Plus\textsuperscript{10K} at Caltech have shown this approach to be reliable, reproducible, and accurate for helium isotope analysis. Additionally, an electron multiplier monitored atomic mas ... [681 chars]"
- **EDIT** [2 Methods para 10] Thesis-chapter cross-reference -> Geochronology preprint.
    - was: "the bounding method of Chapter~\ref{ch:apparatus} (\S\ref{bounding-method})"
    - now: "the bounding method of \citet{thyer2026method}"
- **EDIT** [2 Methods para 10] Data tables removed; Zenodo dataset cited instead.
    - was: "(Tables~\ref{tab:ch2-distilled-3he} and~\ref{tab:ch2-distilled-4he})"
    - now: "(\citealt{thyer_2026})"
- **MOVE** [2.1] Thesis L333-377 verbatim (kinetic and diffusive reductions).
- **EDIT** [2.2 Thermal histories] Data table removed; Zenodo dataset cited instead.
    - was: "(Table~\ref{tab:ch2-distilled-4he})"
    - now: "(\citealt{thyer_2026})"
- **MOVE** [2.2] Thesis L379-458 (MDD and thermal-history modeling).
- **NEW** [2.3 (heading)] New heading for the model equations moved out of the Discussion; carries the thesis label sec:gt_thermo_methods.
    > \subsection{Thermodynamic and Nucleation Model of Goethite Dehydroxylation}\label{sec:gt_thermo_methods}
- **MOVE** [2.3] Thesis L882-894 (reaction, Delta G_r, surface term) moved from Discussion 4.4 to Methods.
- **MOVE** [2.3] Thesis L956-990 (classical nucleation barrier, Turnbull rate law, internal nucleation / gamma_eff) moved from Discussion 4.5 to Methods.
- **MOVE** [2.4] Thesis L460-479 verbatim (SEM study). TODO comments on pigment grade/supplier dropped -- still open, see changelog.
- **CUT** [3.1] Thesis L487 (sentence pointing to the data tables) and L488-621 (landscape Tables ch2-distilled-3he / ch2-distilled-4he) -> Zenodo.
- **CUT** [3 Results] Thesis L713-736 "Isothermal Discrimination Test at 250 C" and Fig. gt_hold: re-framing of data already in the Arrhenius/delta plots (BJT). Thesis L738 \clearpage.
- **MOVE** [4.1-4.2] Thesis L740-786 verbatim (vacuum kinetics; water-saturated release is diffusive).
- **MOVE** [4.2.1] Thesis L788-872 verbatim (MDD consistency, domain table and figures).
- **EDIT** [4.3 (heading)] Heading renamed because the model itself now sits in Methods 2.3; label sec:gt_thermo_methods moved there.
    - was: "\subsection{Thermodynamic Model of Goethite Dehydroxylation}\label{sec:gt_thermo_methods}\label{sec:gt_thermo}"
    - now: "\subsection{Goethite Stability and the Driving Force for Dehydroxylation}\label{sec:gt_thermo}"
- **MOVE** [4.3] Thesis L876-880 and L898-942 (phase diagram, driving forces, Table gt_dmu) kept in the Discussion.
- **MOVE** [4.4] Thesis L944-954 and L992-1034 (rate bound, calibration, translation, assumptions) kept in the Discussion.
- **MOVE** [4.5] Thesis L1036-1147 verbatim (dehydration/recrystallization caveats; pigment). TODO comment on pigment data sheet dropped.
- **EDIT** [4.7 para 4] Data table removed; Zenodo dataset cited instead.
    - was: "(Table~\ref{tab:ch2-distilled-4he})"
    - now: "(\citealt{thyer_2026})"
- **MOVE** [4.6-4.8] Thesis L1151-1377 verbatim (retentivity; 4He/3He spectra; thermal history).
- **NEW** [5 Conclusions] Conclusions rewritten (BJT allowed liberties). Built from thesis L1381-1434; method-paper claims (86 bar at 300 C, UHV setups) dropped; findings numbered; "log units" -> "natural log units".
    > \section{Conclusions}\label{conclusions}

We applied the silica-glass ampoule method of \citet{thyer2026method} to conduct the first
helium step heat experiment on goethite under water-saturated conditions, using
proton-irradiated goethite Win-06-01b, which has previously been step heated in vacuum. The main
findings are:
\begin{enumerate}
  \item Polycrystalline goethite heated with water does not develop the contraction cracks that
  form in vacuum, and the water-saturated helium release differs fundamentally from release in
  vacuum. Published vacuum step heats of Win-06-01b follow first-order conversion to hematite,
  whereas the water-saturated release shows the history and time dependence of diffusion.
  \item Apparent diffusivities at water saturation are approximately seven natural log units
  lower than those of the same sample in vacuum. Beyond 7\% cumulative $^3$He release they define
  a linear Arrhenius array with an activation energy of \ChTwoEa{}~$\pm$~\ChTwoEaErr{}~kJ/mol, and
  the delta plot follows multiple diffusion domain systematics. A four-domain model places 97\% of
  the $^3$He in a single domain.
  \item Extrapolated to 25\,\textdegree C, this domain is essentially quantitatively retentive of
  helium over billion-year timescales, supporting the use of goethite (U--Th)/He dates to date
  surface processes.
  \item The $^4$He/$^3$He spectrum shows that even this retentive domain lost radiogenic helium in
  nature, and thermally activated diffusion within the four-domain structure can account for that
  loss. Steady cooling from 76--80\,\textdegree C at 150--175~Ma fits the spectrum best, favoring
  crystallization from warm, possibly hydrothermal, fluids; burial of surface-formed goethite to a
  Late Cretaceous peak of 58--65\,\textdegree C, consistent with regional apatite fission-track
  constraints, remains a viable alternative.
  \item The water-saturated $^4$He/$^3$He spectrum rises more gradually than the vacuum spectra of
  the same sample, suggesting that dehydroxylation and diffusion degas goethite with different
  geometries. Vacuum $^4$He/$^3$He spectra of goethite may therefore not encode thermal histories as
  directly as they do for minerals that do not decompose.
  \item A thermodynamic and kinetic analysis explains why water preserves goethite on experimental
  timescales. The water-saturated release requires solid-state conversion to be at least
  $10^{2.5}$ times slower than in vacuum; the roughly tenfold smaller driving force at saturation
  raises the barrier to topotactic hematite nucleation enough to suppress conversion far below
  this limit.
\end{enumerate}

Fluid-mediated conversion, which transformed synthetic goethite pigment under similar conditions,
would be accompanied by abrupt helium loss that is not observed. Recrystallization, however,
cannot be excluded; if it contributed, the diffusivities reported here are upper bounds and the
retentivity a lower bound. Separating the effects of crystallite size, chemical composition, and
radiation damage on helium retention will require further water-saturated step heats of
irradiated goethite of controlled grain size, which this approach makes straightforward.
- **NEW** [Statements] Data availability, CRediT, competing interest, acknowledgements and AI declaration carried over from the old GCA manuscript (Manuscripts/HydrothermalGoethite/hydrothermal_goethite_body.tex L590-616); CRediT roles updated to chapter2_contributions.tex; Data Availability now cites the Zenodo entry.
    > \section*{Data Availability}

The step heat data, permeation-lag bounds, and model outputs supporting this study are archived
on Zenodo \citep{thyer_2026}: \url{https://doi.org/10.5281/zenodo.22113166}.

\section*{CRediT authorship contribution statement}

\textbf{Ben J. Thyer:} Conceptualization, Methodology, Investigation, Formal analysis,
Visualization, Writing -- original draft. \textbf{Jonathan Treffkorn:} Methodology,
Investigation. \textbf{Kenneth A. Farley:} Conceptualization, Resources, Supervision, Funding
acquisition, Writing -- review \& editing.

\section*{Declaration of competing interest}

The authors declare that they have no known competing financial interests or personal
relationships that could have appeared to influence the work reported in this paper.

\section*{Acknowledgements}

This work was supported by National Science Foundation (NSF) grant EAR 1945974 to K.A. Farley.
Dr. Paul Asimow is thanked for helpful discussions on the experimental design.

\section*{Declaration of Generative AI and AI-assisted technologies in the writing process}

During the preparation of this work the authors used Claude (Anthropic) to assist with software
programming, and with editing and LaTeX typesetting of the manuscript. After using this tool, the
authors reviewed and edited the content as needed and take full responsibility for the content of
the publication.
- **EDIT** [S1.1 para 1] Thesis-chapter cross-reference -> preprint.
    - was: "following the permeation step method (Chapter~\ref{ch:apparatus}, \S\ref{permeation-step-method})"
    - now: "following the permeation step method of \citet{thyer2026method}"
- **EDIT** [S1.1 para 1] Equation reference -> preprint (xr).
    - was: "so Eq.~\eqref{eq:n0perm} (Chapter~\ref{ch:apparatus}) could not be"
    - now: "so Eq.~\eqref{ch1-eq:n0perm} of \citet{thyer2026method} could not be"
- **EDIT** [S1.1 para 2] Thesis-chapter cross-reference -> preprint.
    - was: "the bounding method described in Chapter~\ref{ch:apparatus} (\S\ref{bounding-method}), which"
    - now: "the bounding method described in \citet{thyer2026method}, which"
- **EDIT** [S1.1 para 2] Equation reference -> preprint (xr).
    - was: "calculated using Eq.~\eqref{eq:steadystate} (Chapter~\ref{ch:apparatus}). 3He"
    - now: "calculated using Eq.~\eqref{ch1-eq:steadystate} of \citet{thyer2026method}. 3He"
- **EDIT** [S1.1 para 3] Thesis-chapter cross-reference -> preprint.
    - was: "rather than assumed from the literature (Chapter~\ref{ch:apparatus}, \S\ref{in-situ-rate-constant})."
    - now: "rather than assumed from the literature (\citealt{thyer2026method})."
- **EDIT** [S1.1 para 4] Equation reference -> preprint (xr).
    - was: "series were fit to Eq.~\eqref{eq:incyield} using"
    - now: "series were fit to Eq.~\eqref{ch1-eq:incyield} of \citet{thyer2026method} using"
- **EDIT** [Fig. S permeation fits caption] Equation reference -> preprint (xr).
    - was: "of Eq.~\eqref{eq:incyield} (Chapter~\ref{ch:apparatus}) to data"
    - now: "of Eq.~\eqref{ch1-eq:incyield} of \citet{thyer2026method} to data"
- **EDIT** [S1.1 para 6] Thesis-chapter cross-reference -> preprint.
    - was: "similar to observations discussed in Chapter~\ref{ch:apparatus} (\S\ref{resolving-the-paradoxically-high-apparent-helium-permeability-in-water-filled-tubes})"
    - now: "similar to observations discussed in \citet{thyer2026method}"
- **EDIT** [S1.1 para 6] Thesis-chapter cross-reference -> preprint.
    - was: "upper bound on the residual helium (Chapter~\ref{ch:apparatus}, \S\ref{bounding-method})."
    - now: "upper bound on the residual helium (\citealt{thyer2026method})."
- **EDIT** [S1.1 para 7] Equation reference -> preprint SI (xr).
    - was: "using Eq.~\eqref{eq:s6-8} from the supplement to Chapter~\ref{ch:apparatus} because"
    - now: "using Eq.~\eqref{ch1-eq:s6-8} from the supplement to \citet{thyer2026method} because"
- **MOVE** [S1.1] Fig. ch2-ampoule-dims moved here from the thesis main text (L235-240).
- **CUT** [S1] SI L100-153 "Measurement and Numerical Simulation of Apparent Permeability of Experimental Ampoule" (permeability regression, cooling-tube simulation rationale, water-displacement explanation of high apparent permeability): the explanation is in the preprint (Eq. keff) and the detail in the thesis.
- **EDIT** [S1.2 para 1] "chapter" -> "study"; equation reference -> preprint (xr).
    - was: "presented in this chapter are reduced using the bounding method (Eq.~\eqref{eq:steadystate})"
    - now: "presented in this study are reduced using the bounding method (Eq.~\eqref{ch1-eq:steadystate} of \citealt{thyer2026method})"
- **EDIT** [S1.2 para 1] Pointer to the cut permeation-rate-constant data section removed.
    - was: "of Fig.~\ref{fig:ch2-ampoule-permeability} (\S\ref{sec:ch2-si-detailed-methods})."
    - now: "of Fig.~\ref{fig:ch2-ampoule-permeability}."
- **EDIT** [S1.2 para 1] "chapter" -> "study".
    - was: "used elsewhere in this chapter)"
    - now: "used elsewhere in this study)"
- **EDIT** [Fig. S nt vs ntSS caption] Pointer to the cut data section removed.
    - was: "$y$-axis, \S\ref{sec:ch2-si-detailed-methods})"
    - now: "$y$-axis)"
- **EDIT** [Fig. S nt vs ntSS caption] Equation reference -> preprint (xr).
    - was: "$x$-axis, Eq.~\eqref{eq:steadystate})"
    - now: "$x$-axis, Eq.~\eqref{ch1-eq:steadystate} of \citealt{thyer2026method})"
- **CUT** [S1.2] SI L166 (permeation-step vs bounding diffusivity concordance paragraph): its figures are cut with the permeation-step dataset section; the Ea agreement is not needed for the argument.
- **EDIT** [S1.2 para 3] Section reference -> preprint.
    - was: "($\Omega$: \S\ref{bounding-method})"
    - now: "($\Omega$; \citealt{thyer2026method})"
- **EDIT** [S1.2 para 3] Section reference -> preprint.
    - was: "(\S\ref{permeation-step-method})"
    - now: "(\citealt{thyer2026method})"
- **CUT** [S2] SI L176-208 "Finite Difference Diffusion Model of Cooling Tube" and Fig. goethite-cooling-rate: method detail (thesis); the permeability-figure caption still describes the modeled points.
- **EDIT** [S2.1] Equation reference -> preprint (xr).
    - was: "evaluated using Eq.~\eqref{eq:steadystate}."
    - now: "evaluated using Eq.~\eqref{ch1-eq:steadystate} of \citet{thyer2026method}."
- **EDIT** [S2.2] This delta value is not in the preprint, so the thesis is cited.
    - was: "measured independently for a water-filled ampoule in Chapter~\ref{ch:apparatus} (\S\ref{results}):"
    - now: "measured independently for a water-filled ampoule by \citet{thyer2026thesis}:"
- **EDIT** [S2.2] Equation reference -> preprint (xr).
    - was: "Eq.~\eqref{eq:steadystate} (Chapter~\ref{ch:apparatus}): $n_{ss}"
    - now: "Eq.~\eqref{ch1-eq:steadystate} of \citet{thyer2026method}: $n_{ss}"
- **CUT** [SI] SI L274-385: permeation-rate-constant dataset tables, permeation-step 3He dataset table, and the permeation-step/bounding concordance section with its two figures -> Zenodo / thesis.
- **MOVE** [S3-S6] SI L387-745 verbatim (kinetic mechanisms; equilibrium thermodynamics; gamma_eff calibration; MDD forward model, N=1-5 fits, two-domain alternative).
- **NEW** [Abstract] Abstract rewritten and shortened from the 492-word thesis abstract (BJT allowed liberties); "seven log units" -> "seven natural log units"; method credited to the Geochronology preprint.
    > (U--Th)/He dating of goethite (FeOOH) can directly date weathering, ferruginization, and
laterite formation, but interpreting goethite He dates requires knowing the conditions under
which goethite retains radiogenic helium. Vacuum step heats, the standard tool for characterizing
helium retention, convert goethite to hematite and record dehydroxylation rather than diffusion
\citep{farley2024}. Because high water pressure suppresses dehydroxylation, we used a recently
developed silica-glass ampoule method \citep{thyer2026method} to conduct the first helium step heat
experiment on proton-irradiated goethite under water-saturated conditions. Goethite Win-06-01b
(Flinders Ranges, South Australia) was sealed with distilled water and heated through multiple
prograde and retrograde cycles between 170 and 250\,\textdegree C over about 40 days. Apparent
$^3$He diffusivities are approximately seven natural log units lower than those measured on the
same sample in vacuum and, beyond 7\% cumulative release, define a linear Arrhenius array with an
activation energy of \ChTwoEa{}~$\pm$~\ChTwoEaErr{}~kJ/mol and a closure temperature of
\ChTwoTc{}~$\pm$~\ChTwoTcErr{}\,\textdegree C at 10\,\textdegree C/Ma. Reanalysis of two published
vacuum step heats of the same sample shows that vacuum release follows first-order conversion to
hematite, whereas the water-saturated release shows the history dependence of diffusion and
follows multiple diffusion domain systematics. A four-domain model places 97\% of the $^3$He in a
single domain that is nearly quantitatively retentive at 25\,\textdegree C over billion-year
timescales. The $^4$He/$^3$He spectrum nonetheless requires natural helium loss from this domain,
which thermally activated diffusion can explain: steady cooling from 76--80\,\textdegree C at
150--175~Ma fits best, while burial of surface-formed goethite to a Late Cretaceous peak of
58--65\,\textdegree C, consistent with regional apatite fission-track data, remains viable.
Thermodynamic and nucleation modeling calibrated on the vacuum data shows that the roughly tenfold
smaller driving force at water saturation raises the barrier to hematite nucleation enough to
suppress solid-state conversion on experimental timescales. Fluid-mediated conversion, observed
in synthetic goethite pigment, and recrystallization are not excluded; if either contributed, the
diffusivities are upper bounds. Water-saturated step heats open the way to systematic experiments
on how crystallite size, composition, and radiation damage control helium retention in goethite.
- **NEW** [goethite_paper_extra.bib] Two bib entries (preprint, thesis) kept local so the shared references.bib is untouched; preprint journal/status is a placeholder ("Geochronology Discussions", in preparation).
    > % Entries used only by the GCA goethite manuscript (GoethitePaper*.tex). @article{thyer2026method, author = {Thyer, Ben J. and Treffkorn, Jonathan and Farley, Kenneth A.}, title = {A simple method for helium step heat experiments at high water or sulfur fugacity}, journal = {Geochronology Discussions}, year = {2026}, note = {in preparation} } @phdthesis{thyer2026thesis, author = {Thyer, Ben J.}, title = {Recipes for  ... [671 chars]

## Post-build fixes (2026-11-02, applied directly to the paper files)

- **EDIT** [goethite_paper_extra.bib; body] The shared `references.bib` entry `thyer_2026` is a biblatex `@dataset`, which elsarticle-harv.bst cannot format (title only, no DOI). Added a local `@misc{thyer2026data}` with the DOI and switched the four body citations to it; `(\citealt{thyer2026data})` -> `\citep{thyer2026data}` so it prints "(Thyer, 2026)".
- **EDIT** [2.2, 4.8 run-in headings] Trailing period removed from the seven `\paragraph{...}` titles ("Diffusion domain structure", "Thermal histories", "Steady cooling", ...): elsarticle adds its own period, which printed "..". Formatting only.
- **EDIT** [wrappers] `\usepackage{xurl}` added so long reference URLs break (one overflowed the page by 550 pt).

## Not changed (flagged for BJT)

- Methods para 10 points to "the kinetic analysis of the published vacuum step heats (S2)", but the kinetic-mechanism comparison is S3 (`sec:gt_supp_mech`). Pointer inherited from the thesis; left as is because body text is cut/move only.
- Sample age: 2 Methods quotes 180-135 Ma, thermal-history modeling uses 130-180 Ma (thesis TODO, comment dropped).
- Pigment product name/grade/supplier and SEM settings for the pigment images (thesis TODOs, comments dropped).
- `thyer2026method` journal/status is a placeholder (Geochronology Discussions, in preparation) -- update once the preprint has a DOI.
- xr pulls in citation keys from the other aux files, so the log shows harmless "Citation ... multiply defined" warnings.
- Compile order: Chapter1 paper + SI first (for ch1- equation numbers), then GoethitePaper_SI, GoethitePaper, bibtex both, then pdflatex x2 each.
- Terminology ("hydrothermal" vs "water vapor saturated") untouched, pending BJT's decision on standardizing it.

## Slimming pass (2026-11-02, BJT request). Backups: `*.pre_slim_20261102`.

- **MOVE** [4.5 -> SI S7] Pigment material moved to a new SI section "Fluid-Mediated Conversion of Synthetic Goethite Pigment" (`sec:gt_pigment`): Methods subsection (`sec:gt_pigment_methods`, the pigment sentences from the SEM-methods paragraph) and Results and Interpretation subsection (observations, Fig. gt_pigment, all-or-nothing paragraph, fluid-chemistry paragraph). Section/subsection headings NEW.
- **EDIT** [2.4 SEM methods heading] `\label{sec:gt_pigment_methods}` removed from the main-text heading (now on the SI subsection).
- **EDIT** [SI S7 Methods] "was treated in the same way but only with water," -> "was treated in the same way as the Bahia goethite (main text, \S\ref{sem-study-...}) but only with water,".
- **EDIT** [4.5, kept in main text] "We conclude that water-saturated conditions do not by themselves exclude fluid-mediated" -> "Synthetic goethite pigment heated with excess water converted to hematite by dissolution and reprecipitation (SI, \S\ref{sec:gt_pigment}), showing that water-saturated conditions do not by themselves exclude fluid-mediated". The rest of that paragraph (no evidence of abrupt He loss in the Win-06-01b data) stays in the main text.
- **MOVE** [4.2.1 -> SI S6] Table ch2-mdd-domains (MDD fits for N = 1-5) moved next to Fig. ch2-si-mdd-3he-fits. **EDIT** SI: "summarized in Table~\ref{tab:ch2-mdd-domains} of the main text." -> "summarized in Table~\ref{tab:ch2-mdd-domains}."
- **MOVE** [4.8 -> SI S6] Table ch2-mdd-thermal (best-fit thermal histories) moved to the SI MDD section. Main-text references unchanged (they now resolve to Table S#).
- **CUT** [4.6] Fig. ch2-isothermal-retention (PRP_goethite_winsor.pdf) removed, with the sentence "Fig.~\ref{fig:ch2-isothermal-retention} shows isothermal holding time against helium age for this same domain for 4 different temperatures." The t'/t = 0.968 example and the 25 C statement stay.
- Result: main text 64 -> 55 pages (review layout); SI 21 -> 24 pages.
- **EDIT** [SI] `\clearpage` before the pigment section so the MDD tables print in S6.

## Slimming pass 2 (2026-11-02, BJT items 2-8 + 250 C test restored). Backups: `*.pre_slim2_20261102`.

- **CUT** [1 Introduction] Molecular-simulation paragraph (Bassal et al. 2022) removed (BJT item 5).
    - deleted: "Molecular simulations indicate that helium diffusion in perfectly crystalline goethite should be highly anisotropic, essentially reducing to 1-dimensional diffusion along the b-axis (typically the long axis of the polycrystalline aggregate) that would amount to near-instantaneous helium escape from goethite \citep{bassal2022}, which is clearly contradicted by observed (U--Th)/He dates as old as \t ... [1013 chars]"
- **EDIT** [1 Introduction] Bassal et al. (2022) cited where radiation damage and composition are named as untested factors (also still cited in para 2 and 4).
    - was: "chemical composition could affect helium mobility and retentivity in nature."
    - now: "chemical composition could affect helium mobility and retentivity in nature \citep{bassal2022}."
- **EDIT** [2 Methods para 2] Seal "testament / 11 orders of magnitude" sentence condensed; photo now in the SI.
    - was: "Fig.~\ref{fig:ch2-ampoule-post} shows the sealed ampoule after the completion of the step heats with all of the original water remaining, a testament to the quality of the ampoule's seal, which had sustained a massive pressure gradient of over 11 orders of magnitude across the ampoule walls, with an inner vapor pressure of about 3$\times$10\textsuperscript{4} torr (\textasciitilde40 bars: \citet{haar1984}) against the \textasciitilde10\textsuperscript{-7} torr ultra-high vacuum of the lamp cell  ... [552 chars]"
    - now: "The ampoule retained all of its water through the experiment, including more than a week at 250°C with an internal vapor pressure of about 40~bar \citep{haar1984} (SI Fig.~\ref{fig:ch2-ampoule-post})."
- **CUT** [2 Methods] Fig. ch2-ampoule-post moved to SI S1 (MOVE).
    - deleted: "\begin{figure}[htbp] \centering \includegraphics[width=0.7\textwidth]{zoomout2.jpg} \caption{A view of the entire experimental ampoule after the completion of the step heat experiment before it was broken for the final step in the resistance furnace. At room temperature, the tube is approximately half-filled with gas, one-third filled with liquid water, and one-sixth filled with $<$2\,mm long shar ... [688 chars]"
- **EDIT** [2 Methods para 5] Temperature-accuracy paragraph condensed; validation cited to the preprint (BJT item 6).
    - was: "Experimental temperature records show \textasciitilde1°C amplitude oscillations around the target temperature. While we cannot exclude the possibility that sustained temperature gradients were present throughout the sample due to the use of the comparatively large \textasciitilde1 mm thick ampoule, we are confident that the conclusions of this work are robust. The ampoule was in direct contact with the thermocouple junction and was in front of the thermocouple junction with respect to the projec ... [699 chars]"
    - now: "Recorded temperatures oscillated by \textasciitilde1°C around each target. Because the ampoule sat between the lamp and the thermocouple junction, any bias would make the sample hotter than recorded, and encapsulated Durango apatite heated in the same way reproduces published diffusivities \citep{thyer2026method}."
- **MOVE** [2 Methods para 8 -> SI S2] Final-step blank, re-extract and sensitivity sentences moved to SI subsection "Final Step"; NEW pointer sentence "Blank, re-extract and sensitivity details are given in the SI (S2)."
    - moved: "A hot furnace blank subjected to the same volume splits as the final HT-Win-06-01b measurement gave a 3He blank of 6.8 fccSTP and a 4He blank of 0.31 nccSTP. This blank correction was less than 1\% of the measured 4He and negligible for 3He. A re-extract of HT-Win-06-01b immediately following the measurement yielded above-blank 3He and 4He signals, which were added to the total measurement, although both constituted less than 1\% of the final step yield. Sensitivity was calculated by measuring a ... [594 chars]"
- **EDIT** [2 Methods para 9] SI uncertainty derivations and complete-degas test removed; thesis cited (BJT item 8). Also fixes the old S2/S3 mis-pointer.
    - was: "Information (\S\ref{sec:ch2-si-permeation}), together with the diffusivity inversions, the isotope-ratio uncertainties and the kinetic analysis of the published vacuum step heats (\S\ref{ch2-analytical-methods})."
    - now: "Information (\S\ref{sec:ch2-si-permeation}). The propagation of the permeation-lag bounds into apparent diffusivities and isotope ratios, and a test of the bounding method against direct permeation-step quantification, are described by \citet{thyer2026thesis}."
- **EDIT** [2.1] Pointer to the removed SI diffusivity-uncertainty section -> thesis.
    - was: "experiment (\S\ref{helium-in-goethite-diffusivity-inversions})."
    - now: "experiment (\citealt{thyer2026thesis})."
- **EDIT** [2.2 Thermal histories] Isothermal family removed (BJT item 2).
    - was: "We compare three types of thermal histories, with two free parameters for steady cooling and the isothermal hold and three for burial and exhumation."
    - now: "We compare two types of thermal histories, with two free parameters for steady cooling and three for burial and exhumation."
- **EDIT** [2.2 Thermal histories] Isothermal-hold bullet removed (BJT item 2).
    - was: "\item \textbf{Isothermal hold:} $T=T_\mathrm{iso}$ from $t_\mathrm{form}$ to the present. Free parameters: $t_\mathrm{form}$ and $T_\mathrm{iso}$."
    - now: ""
- **MOVE** [2.2 -> SI S5] chi^2 definition (Eq. gt_mdd_chi2), sigma rule and degrees of freedom moved to new SI subsection "Misfit statistic for thermal histories" (heading NEW); NEW one-sentence summary in the main text.
    - moved: "Each path is scored against \begin{equation} \chi^2=\sum_i\left(\frac{R_i^{\mathrm{mod}}-R_i^{\mathrm{M}}}{\sigma_i}\right)^2, \qquad\sigma_i=\max\!\left[\tfrac12\left(R_i^{\mathrm{UB}}-R_i^{\mathrm{LB}}\right),\,0.02\right], \label{eq:gt_mdd_chi2} \end{equation} over the \MDDNfit{} steps that have lag-correction bounds and more than 0.1~pccSTP of $^3$He. Where M, LB and UB are the central, lower-bound and upper-bound bulk-normalized ratios of the bounding method \citep{thyer2026data}. This anal ... [734 chars]"
- **EDIT** [3.2] Per-dataset and all-step activation energies condensed to one sentence (BJT item 7).
    - was: "KAF alone gives $\ChTwoKinKAFEa\pm\ChTwoKinKAFEaErr$ and HDM alone $\ChTwoKinHDMEa\pm\ChTwoKinHDMEaErr$~kJ\,mol$^{-1}$), in agreement with the cumulative fit. The result does not depend on the fitting window: fitting all steps instead gives $E_a = \ChTwoKinAllFOneEa$~kJ\,mol$^{-1}$ and the same ranking of models (\S\ref{sec:gt_supp_mech})."
    - now: "Fitting KAF and HDM separately ($\ChTwoKinKAFEa\pm\ChTwoKinKAFEaErr$ and $\ChTwoKinHDMEa\pm\ChTwoKinHDMEaErr$~kJ\,mol$^{-1}$) or fitting all steps ($\ChTwoKinAllFOneEa$~kJ\,mol$^{-1}$) gives consistent results (\S\ref{sec:gt_supp_mech})."
- **EDIT** [4.1] Thermogravimetric comparison condensed to one sentence (BJT item 7).
    - was: "Thermogravimetric studies of goethite dehydroxylation report somewhat higher apparent activation energies, $154\pm15$ to $169\pm8$~kJ\,mol$^{-1}$, for a reaction controlled by a two-dimensional phase boundary, with a different mechanism at early stages and low temperature \citep{goss1987}. This may simply be due to a difference in samples: goethites from different sources have different particle sizes, morphologies, and aluminum contents, all of which affect the kinetics of dehydroxylation \cite ... [556 chars]"
    - now: "Thermogravimetric studies report somewhat higher apparent activation energies for goethite dehydroxylation ($154\pm15$ to $169\pm8$~kJ\,mol$^{-1}$; \citealt{goss1987}), plausibly because dehydroxylation kinetics depend on particle size, morphology, and aluminum content \citep{langmuir1971,yapp1983,tardy1985,majzlannavrotsky2003}."
- **EDIT** [4.2] NEW caveat paragraph on recrystallization and fluid-mediated conversion (BJT item 4).
    - was: "While it is difficult to prove that decomposition or recrystallization is not"
    - now: "Two processes other than volume diffusion could have contributed to the water-saturated release. Goethite can recrystallize under hydrothermal conditions \citep{schwertmann1985}, and fluid-mediated conversion to hematite, which lies outside the solid-state nucleation model of \S\ref{sec:gt_nucleation}, transformed synthetic goethite pigment heated with excess water (SI, \S\ref{sec:gt_pigment}). Either process would likely release essentially all of the helium in the material it affects. Progress ... [1103 chars]"
- **CUT** [4.5] Whole subsection "Goethite Dehydration and/or Recrystallization..." removed, including the pigment pointer paragraph (now covered by the 4.2 caveat).
    - deleted: "\subsection{Goethite Dehydration and/or Recrystallization During Helium Step Heat Experiments}\label{goethite-dehydration-andor-recrystallization-during-hydrothermal-experiments} The aim of helium step heat experiments is to characterize the mechanisms and rates of helium loss in nature to aid in the interpretation of geochronologic and helium geochemical data. The results of this experiment are e ... [4466 chars]"
- **EDIT** [4.2.1 (new)] Thesis "Isothermal Discrimination Test at 250 C" (thesis L713-736: text + Fig. gt_hold) restored verbatim as a subsubsection of 4.2 (BJT: discussion, not results); only \subsection -> \subsubsection.
    - was: "\subsubsection{Consistency with MDD Systematics}"
    - now: "\subsubsection{Isothermal Discrimination Test at 250~$^\circ$C}\label{sec:gt_hold_results} Sequences of isothermal steps can be particularly powerful in discriminating first and second order processes. Diffusion slows quickly as the diffusion front moves inward, depleting the grain rims of helium, whereas the rate of first-order conversion slows less for similar yields. We harnessed the principle to conduct a sensitive test by performing a series of 4 consecutive, long isothermal steps at 250~$^ ... [2087 chars]"
- **EDIT** [4.4 para 1] Interstitial-water / LRD speculation removed (BJT item 3); the one-sentence "fine grains or interstitial helium" remark is kept.
    - was: "Goethite aggregates are known to have interstices that are filled by chemisorbed non-stoichiometric water that represents the earliest water to be lost in vacuum \citep{naono1987}. Non-stoichiometric hydrogen is known to persist in goethite even after heating to 140°C \citep{yapppoths1995}. It is therefore reasonable to posit that artificial 3He observed in less-retentive domains may be trapped by non-stoichiometric water or hydroxyl groups within interstices of goethite aggregates. Dehydration  ... [1162 chars]"
    - now: ""
- **EDIT** [4.4 para 2] Speculative mechanism for the geometry difference removed; the conclusion sentence is kept (BJT item 3).
    - was: "differs between the hydrothermal and vacuum experiments, and could be explained by the relative dominance of dehydration processes or their mode of spatial propagation as a function of water pressure, where the smoothest \textsuperscript{4}He/\textsuperscript{3}He spectra are generated by higher water pressures. We interpret this experimental control on the \textsuperscript{4}He/\textsuperscript{3}He spectra to reflect the relative importance of goethite dehydration and helium diffusion through  ... [578 chars]"
    - now: "differs between the hydrothermal and vacuum experiments."
- **EDIT** [4.5 para 1] Isothermal family removed from the list (BJT item 2).
    - was: "we fitted steady-cooling, burial-and-exhumation, and isothermal thermal histories"
    - now: "we fitted steady-cooling and burial-and-exhumation thermal histories"
- **EDIT** [4.5] Isothermal-hold paragraph replaced by one sentence (BJT item 2).
    - was: "\paragraph{Isothermal hold} The spectrum constrains only the product of diffusivity and time, so the $\chi^2$ minimum is a ridge from $\sim$47\,\textdegree C at 50~Ma to $\sim$35\,\textdegree C at 500~Ma, along which $\chi^2_\nu\approx\MDDIsoChi$ throughout. No isothermal path reproduces the shape of the spectrum: they underpredict the ratios of the early steps and overpredict those of the late steps. We do not consider this family further."
    - now: "Isothermal histories, which constrain only the product of diffusivity and time, cannot reproduce the shape of the spectrum and are not considered further (Table~\ref{tab:ch2-mdd-thermal})."
- **EDIT** [5 Conclusions] Closing caveat aligned with the new 4.2 argument.
    - was: "Fluid-mediated conversion, which transformed synthetic goethite pigment under similar conditions, would be accompanied by abrupt helium loss that is not observed. Recrystallization, however, cannot be excluded; if it contributed, the diffusivities reported here are upper bounds and the retentivity a lower bound."
    - now: "Recrystallization and fluid-mediated conversion, which transformed synthetic goethite pigment under similar conditions, would likely degas the affected material completely; the smooth, diffusive release bounds their contribution to be small. If either contributed, the diffusivities reported here are upper bounds and the retentivity a lower bound."
- **EDIT** [SI S1.1 para 2] Pointer to the removed complete-degas test -> thesis.
    - was: "the two reductions can be compared directly, and that comparison is used below (\S\ref{complete-degas-test}) as an internal test of the bounding method."
    - now: "the two reductions can be compared directly; that comparison, an internal test of the bounding method, is given by \citet{thyer2026thesis}."
- **CUT** [SI S1.2] Complete-degas test (text + Fig. nt vs ntSS) removed; thesis cited instead (BJT item 8).
    - deleted: "\subsection{Consistency of the Bounding Method with Direct Permeation-Step Quantification: The Complete Degas Test}\label{complete-degas-test} All Win-06-01b step heat data presented in this study are reduced using the bounding method (Eq.~\eqref{ch1-eq:steadystate} of \citealt{thyer2026method}), because 4He permeation-step yields were near blank level and could not support the permeation step met ... [5183 chars]"
- **EDIT** [SI S1] Fig. ch2-ampoule-post moved in from the main text (MOVE).
    - was: "\label{fig:ch2-ampoule-dims} \end{figure}"
    - now: "\label{fig:ch2-ampoule-dims} \end{figure} \begin{figure}[htbp] \centering \includegraphics[width=0.7\textwidth]{zoomout2.jpg} \caption{A view of the entire experimental ampoule after the completion of the step heat experiment before it was broken for the final step in the resistance furnace. At room temperature, the tube is approximately half-filled with gas, one-third filled with liquid water, and one-sixth filled with $<$2\,mm long shards of irradiated Win-06-01b goethite. A gel-like substance ... [730 chars]"
- **CUT** [SI S2] Diffusivity-inversion and isotope-ratio uncertainty derivations removed; thesis cited in the main text (BJT item 8).
    - deleted: "\subsection{Uncertainty for Diffusivity Inversions}\label{helium-in-goethite-diffusivity-inversions} Apparent values of D/a\textsuperscript{2} for 3He and 4He were calculated from times and cumulative measured yields using the equations of \citet{fechtigkalbitzer1966}. Lower and upper bounds for diffusivity were calculated using the upper bound for the helium contents of the ampoules before and af ... [5540 chars]"
- **EDIT** [SI S2] Final-step blank / re-extract / sensitivity text moved in from the main text (heading NEW).
    - was: "\section{Analytical Methods}\label{ch2-analytical-methods}"
    - now: "\section{Analytical Methods}\label{ch2-analytical-methods} \subsection{Final Step}\label{sec:ch2-si-finalstep} A hot furnace blank subjected to the same volume splits as the final HT-Win-06-01b measurement gave a 3He blank of 6.8 fccSTP and a 4He blank of 0.31 nccSTP. This blank correction was less than 1\% of the measured 4He and negligible for 3He. A re-extract of HT-Win-06-01b immediately following the measurement yielded above-blank 3He and 4He signals, which were added to the total measurem ... [705 chars]"
- **CUT** [SI S5] Two-domain alternative removed (BJT item 8).
    - deleted: "\subsection{Two-domain alternative} The two-domain structure (2.2\% of the $^3$He at $r/r_0=5.4\times10^{-3}$, 97.8\% at 1.05) fits the $^4$He/$^3$He spectrum better than the adopted four-domain structure: a burial path with crystallization at 195~Ma and a peak of $\sim$66\,\textdegree C at $\sim$100~Ma gives $\chi^2_\nu\approx1.3$. However, this structure reproduces the $^3$He Arrhenius array poo ... [482 chars]"
- **EDIT** [SI S5] chi^2 definition moved in from the main text (heading NEW).
    - was: "\clearpage \section{Fluid-Mediated"
    - now: "\subsection{Misfit statistic for thermal histories}\label{sec:ch2-si-chi2} Each path is scored against \begin{equation} \chi^2=\sum_i\left(\frac{R_i^{\mathrm{mod}}-R_i^{\mathrm{M}}}{\sigma_i}\right)^2, \qquad\sigma_i=\max\!\left[\tfrac12\left(R_i^{\mathrm{UB}}-R_i^{\mathrm{LB}}\right),\,0.02\right], \label{eq:gt_mdd_chi2} \end{equation} over the \MDDNfit{} steps that have lag-correction bounds and more than 0.1~pccSTP of $^3$He. Where M, LB and UB are the central, lower-bound and upper-bound bul ... [844 chars]"

## Vacuum water pressure P_H2O -> 0 in the nucleation calibration (2026-11-02, BJT request)

The trapped vacuum line was previously assigned an arbitrary P_H2O = 1e-8 atm. It is now the zero-pressure limit: the water chemical potential -> -inf, Delta mu_on -> inf, 1/Delta mu_on^2 -> 0. Script: `Chapter2/Figures/fig_goethite_vacuum_kinetics.py` (backup `.pre_P0_20261102`): `_dmu_bulk` returns +inf for P <= 0; `P_ON_PA = 0.0`; defaults of `gamma_from_suppression`, `saturated_rate_factor`, `log10_alpha_hydrothermal` use it; `cnt_scales` returns r* = 0 and barrier = 0 in vacuum; `GAMMA_CAL` (0.14, 0.16, 0.19) -> (0.12, 0.14, 0.15); the hard-coded permissive gamma 0.084 replaced by `gamma_permissive()` (0.081 at 0.1 bar). Macros regenerated (`chapter2_kinetics_values.tex`, backup `.pre_P0_20261102`): gamma 0.14-0.19 -> 0.12-0.15 (MC 0.12-0.15, median 0.14); barrier at saturation 51-129 -> 32-63 k_BT; vacuum barrier 0.5-1.3 -> 0; predicted conversion for gamma = low/mid/high 10^-20.5/-31.4/-53.7 -> 10^-12.4/-20.7/-25.8; calibration grid 10^-51.9..-19.4 -> 10^-26.7..-12.3; Monte Carlo 95% 10^-67.3..-15.7 -> 10^-38.7..-9.1 (required: < 10^-3.8). The 10 nm-grain value (~10^-23 -> ~10^-13) was re-derived as the median of the calibration grid with a 3.76 kJ driving-force shift, which reproduces the old 10^-23 under the old assumption. The phase diagram (equilibrium only) is unaffected; figures arrhenius_reaction_vs_diffusion and first_order_delta_lnk are unaffected; hydrothermal_translation (not used in either document) was regenerated.

### paper body
- **EDIT** [Nucleation barrier scaling (Methods / model section)]
    - was: "Because the barrier scales as $\gamma^3/\Delta\mu^2$, the tenfold drop in $\Delta\mu$ between vacuum and water saturation raises the energetic barrier $\Delta G^{*}$ a hundredfold (Table~\ref{tab:gt_dmu})."
    - now: "Because the barrier scales as $\gamma^3/\Delta\mu^2$, it vanishes in vacuum, where the water pressure approaches zero and $\Delta\mu$ grows without bound, but is significant at water saturation, where $\Delta\mu$ is only 6--11~kJ (Table~\ref{tab:gt_dmu})."
- **EDIT** [Driving-force paragraph]
    - was: "Under the vacuum of a step-heating line ($P_{\mathrm{H_2O}}\approx10^{-8}$~atm) it is 76--106~kJ, about ten times larger. The chemical"
    - now: "Under the vacuum of a step-heating line the water pressure approaches zero, so the chemical potential of water falls without bound and $\Delta\mu$ is unbounded. The chemical"
- **EDIT** [Table gt_dmu caption]
    - was: "at water saturation and at $P_{\mathrm{H_2O}} = 10^{-8}$~atm.}"
    - now: "at water saturation. In vacuum ($P_{\mathrm{H_2O}}\rightarrow0$) the driving force is unbounded.}"
- **EDIT** [Calibration equation]
    - was: "\gamma_{\mathrm{eff}} = \left[\frac{T\ln(1/s)}{C\left(\Delta\mu_{\mathrm{off}}^{-2} - \Delta\mu_{\mathrm{on}}^{-2}\right)}\right]^{1/3},"
    - now: "\gamma_{\mathrm{eff}} = \left[\frac{T\,\Delta\mu_{\mathrm{off}}^{2}\ln(1/s)}{C}\right]^{1/3},"
- **EDIT** [Calibration: vacuum term]
    - was: "with $\Delta\mu_{\mathrm{on}}$ evaluated at $P_{\mathrm{H_2O}} = 10^{-8}$~atm and $\Delta\mu_{\mathrm{off}}$ at an upper bound on the water pressure with the trap isolated."
    - now: "where $\Delta\mu_{\mathrm{off}}$ is evaluated at an upper bound on the water pressure with the trap isolated. With the trap in place, the water pressure approaches zero, the driving force is unbounded, and its contribution to the barrier vanishes. Any finite water pressure in the trapped line would give a larger $\gamma_{\mathrm{eff}}$, so this limit is conservative."
- **EDIT** [Calibration: gamma value and length scales]
    - was: "This gives $\gamma_{\mathrm{eff}} = 0.16$~J\,m$^{-2}$ (range \ChTwoKinGammaLo--\ChTwoKinGammaHi). Under vacuum the corresponding critical nucleus is smaller than a formula unit ($r^{*} = \ChTwoKinRstarVac$~nm) and the barrier is only \ChTwoKinBarVac~$k_BT$: conversion in vacuum is effectively barrierless, consistent with the simple Arrhenius behavior of both vacuum experiments. At this scale class"
    - now: "This gives $\gamma_{\mathrm{eff}} = \ChTwoKinMCGammaMid$~J\,m$^{-2}$ (range \ChTwoKinGammaLo--\ChTwoKinGammaHi). In vacuum the barrier vanishes, so conversion is barrierless, consistent with the simple Arrhenius behavior of both vacuum experiments. At saturation and 250~$^\circ$C, the critical nucleus has a radius of \ChTwoKinRstarSat~nm (\ChTwoKinNfuSat{} formula units) and the barrier is \ChTwoK"
- **EDIT** [Translation equation (vacuum term vanishes)]
    - was: "\left(\frac{1}{\Delta\mu_{\mathrm{sat}}^{2}} - \frac{1}{\Delta\mu_{\mathrm{vac}}^{2}}\right)"
    - now: "\frac{1}{\Delta\mu_{\mathrm{sat}}^{2}}"
- **EDIT** [Translation: gamma values]
    - was: "$\gamma_{\mathrm{eff}} = 0.14$, 0.16 and 0.19~J\,m$^{-2}$"
    - now: "$\gamma_{\mathrm{eff}} = 0.12$, 0.14 and 0.15~J\,m$^{-2}$"
- **EDIT** [Assumptions: 10 nm grains]
    - was: "raises the predicted conversion only to $\sim10^{-23}$;"
    - now: "raises the predicted conversion only to $\sim10^{-13}$;"
- **EDIT** [Table gt_dmu] Vacuum columns ($\Delta\mu_{vac}$ at 10$^{-8}$ atm and the squared ratio) removed: undefined for $P_{H_2O}\rightarrow0$.
- **EDIT** [Conclusions, finding 6]
    - was: "the roughly tenfold smaller driving force at saturation raises the barrier"
    - now: "the driving force, unbounded at the near-zero water pressure of a vacuum line, is only 6--11~kJ at saturation, which raises the barrier"

### paper SI
- **EDIT** [Calibration relation]
    - was: "$\ln(1/s) = (C\gamma_{\mathrm{eff}}^{3}/T)(\Delta\mu_{\mathrm{off}}^{-2} - \Delta\mu_{\mathrm{on}}^{-2})$."
    - now: "$\ln(1/s) = C\gamma_{\mathrm{eff}}^{3}/(T\,\Delta\mu_{\mathrm{off}}^{2})$; the corresponding term for the trapped neighbors vanishes because their driving force is unbounded (item 2)."
- **EDIT** [Item 1]
    - was: "\item $\Delta\mu_{\mathrm{on}}$ and $\Delta\mu_{\mathrm{off}}$ are bulk driving forces,"
    - now: "\item $\Delta\mu_{\mathrm{off}}$ is a bulk driving force,"
- **EDIT** [Item 2 (vacuum limit)]
    - was: "\item They differ only through the chemical potential of water: $\Delta\mu_{\mathrm{on}}$ is evaluated at $P_{\mathrm{H_2O}} = 10^{-8}$~atm and $\Delta\mu_{\mathrm{off}}$ at the water pressure reached with the trap isolated (below). At these pressures (at most 20~Pa), IAPWS-95 and the ideal gas agree, and $\Delta\mu_{\mathrm{on}} - \Delta\mu_{\mathrm{off}} = RT\ln(P_{\mathrm{off}}/P_{\mathrm{on}})"
    - now: "\item With the trap in place, the water pressure in the line approaches zero, so the chemical potential of water falls without bound, $\Delta\mu_{\mathrm{on}}$ is unbounded, and its term $\Delta\mu_{\mathrm{on}}^{-2}$ vanishes. This is the conservative limit: any finite water pressure in the trapped line would give a larger $\gamma_{\mathrm{eff}}$ and a stronger predicted slowdown at saturation. $\Delta\mu_{\mathrm{off}}$ is evaluated at the water pressure reached with the trap isolated (below)."
- **EDIT** [Item 3]
    - was: "\item Surface terms are omitted in both."
    - now: "\item Surface terms are omitted."
- **EDIT** [Volume sensitivity / adopted gamma]
    - was: "enters only through $\ln P$ in $\Delta\mu$ and then through a cube root, so a threefold uncertainty in volume changes $\gamma_{\mathrm{eff}}$ by only about 10\%. The two steps agree within 15\%, and we adopt $\gamma_{\mathrm{eff}} = 0.16$~J\,m$^{-2}$"
    - now: "enters only through $\ln P$ in $\Delta\mu_{\mathrm{off}}$ and then through $\Delta\mu_{\mathrm{off}}^{2/3}$, so a threefold uncertainty in volume changes $\gamma_{\mathrm{eff}}$ by only about 5\%. The two steps agree within 20\%, and we adopt $\gamma_{\mathrm{eff}} = \ChTwoKinMCGammaMid$~J\,m$^{-2}$"
- **EDIT** [Table gt_gamma] gamma_eff columns recomputed with P_on -> 0 (0.138/0.145, 0.150/0.158, 0.164/0.173, 0.178/0.188 -> 0.120/0.124, 0.126/0.130, 0.140/0.145, 0.147/0.152).

### paper abstract
- **EDIT** [Abstract]
    - was: "the roughly tenfold smaller driving force for dehydroxylation at water saturation raises the barrier"
    - now: "the small driving force for dehydroxylation at water saturation, compared with the unbounded driving force at the near-zero water pressure of a vacuum line, raises the barrier"

- **EDIT** [Calibration paragraph, both bodies] Sentence order fixed: the zero-pressure-limit sentences now follow the "pressure estimate ... capacitance manometry" sentence.

## Thermodynamics consolidated in the SI (2026-11-02, BJT request). Backups `*.pre_thermoSI_20261102`.

- **MOVE** [Methods 2.3 -> SI S4/S5] Subsection "Thermodynamic and Nucleation Model of Goethite Dehydroxylation" removed from the main text: reaction and Delta G_r (Eqs. gt_rxn, gt_dGr) -> SI S4 lead; nucleation barrier, Turnbull rate law and internal nucleation (Eqs. gt_barrier, gt_knuc) -> SI S5 lead.
- **EDIT** [Methods 2.1 (end)] NEW pointer sentence to the SI model sections.
    - was: "The KAF steps run with the trap isolated are also excluded from the Arrhenius regression."
    - now: "The KAF steps run with the trap isolated are also excluded from the Arrhenius regression. A thermodynamic and classical-nucleation model of goethite dehydroxylation, used in \S\ref{sec:gt_nucleation} to interpret the effect of water, is described in the SI (\S\ref{sec:eqm-thermo}--\ref{sec:gt_nuc_si"
- **CUT** [Discussion 4.3 intro] "The preceding sections establish from helium step heat data alone ... (S gt_nucleation)." (superseded by the summary).
- **MOVE** [Discussion 4.3 -> SI S4] Phase-diagram findings (enumerated list), Fig. gt_PT, driving-force paragraph and Table gt_dmu -> new SI subsection "Stability and driving force".
- **CUT** [Discussion 4.4 lead] Empirical-bound paragraph (R <= 10^-2.5; 10^-3.8 for <1 %) -- restated in the summary.
- **MOVE** [Discussion 4.4 -> SI S5] Calibration (Eq. gt_gamma_cal), translation to saturation (Eq. gt_translate) and assumptions paragraphs.
- **NEW** [Discussion 4.3] Subsection "Why Water Suppresses Dehydroxylation" (label sec:gt_nucleation kept), summarizing the empirical bound, driving force, vanishing vacuum barrier, gamma_eff calibration, barrier at saturation and Monte Carlo conversion range; all numbers are macros.
    > \subsection{Why Water Suppresses Dehydroxylation}\label{sec:gt_nucleation} Under the vacuum kinetics of Eq.~\eqref{eq:gt_line}, the water-saturated heating schedule would have converted the sample completely ($\sum_i k_{\mathrm{vac}}(T_i)\,\Delta t_i \approx \ChTwoKinSumKdt$). Even if all of the observed $^3$He release came from conversion ($\alpha = \ChTwoKinHTAlphaObs$), the conversion rate at water saturation can be at most $10^{\ChTwoKinLogRObs}$ times the vacuum rate, and at most $10^{\ChTwoKinLogRDetect}$ times for conversion to stay below 1\%. A thermodynamic and classical-nucleation model of goethite dehydroxylation accounts for this suppression (SI, \S\ref{sec:eqm-thermo}--\ref{sec:gt_nuc_si}). Goethite is unstable relative to hematite and water both in vacuum and at water saturation (SI Fig.~\ref{fig:gt_PT}), but water is a product of the reaction, so its chemical potential sets the driving force $\Delta\mu$. In the vacuum of a step-heating line the water pressure approaches zero and $\Delta\mu$ is unbounded; at saturation $\Delta\mu$ is only 6--11~kJ per mole Fe$_2$O$_3$, 1.6--2.4 times $RT$ (SI Table~\ref{tab:gt_dmu}). Because the barrier to nucleating hematite within goethite scales as $\gamma^3/\Delta\mu^2$ \citep{turnbull1949}, it vanishes in vacuum, consistent with the simple Arrhenius behavior of both vacuum experiments, but not at saturation. Calibrating the model's one free parameter, an effective interfacial energy ($\gamma_{\mathrm{eff}} = \ChTwoKinMCGamm
- **EDIT** [Introduction, roadmap] Pointer updated (Methods 2.3 removed).
    - was: "(\S\ref{sec:gt_thermo_methods}--\ref{sec:gt_nucleation})"
    - now: "(\S\ref{sec:gt_nucleation})"
- **EDIT** [SI S4 lead (moved text)] Self-reference adjusted.
    - was: "The values and equations used to evaluate each of these terms are given in the supplement: \S\ref{sec:eqm-thermo}."
    - now: "The values and equations used to evaluate each of these terms are given below."
- **EDIT** [SI S4 heading] Section retitled; main-text reaction/Delta G_r text moved in as its lead; label sec:gt_thermo moved here.
    - was: "\section{Equilibrium Thermodynamics of Goethite Dehydroxylation} \label{sec:eqm-thermo}"
    - now: "\section{Thermodynamics of Goethite Dehydroxylation} \label{sec:eqm-thermo}\label{sec:gt_thermo} Goethite breaks down to hematite by the dehydroxylation reaction \begin{equation} 2\,\alpha\text{-FeOOH} \;\rightleftharpoons\; \alpha\text{-Fe}_2\text{O}_3 + \text{H}_2\text{O}_{(\text{fluid})}, \label{"
- **EDIT** [SI S4 stability (moved text)] "This model" -> "The model".
    - was: "This model can be used to calculate"
    - now: "The model can be used to calculate"
- **EDIT** [SI S4/S5] NEW subsection "Stability and driving force" (moved Discussion text); NEW section "Nucleation Model of Goethite Dehydroxylation" (moved Methods + Discussion text); old section "Calibration of gamma_eff" demoted to a subsection of it.
    - was: "\section{Calibration of $\gamma_{\mathrm{eff}}$} \label{sec:gt_supp_barrier}"
    - now: "\subsection{Stability and driving force} The model can be used to calculate the stability field for goethite with respect to dehydroxylation to hematite and water in $\log P_{\mathrm{H_2O}}$--$T$ space (Fig.~\ref{fig:gt_PT}). This phase diagram communicates several important features of the goethite"
- **EDIT** [SI S5 translation (moved text)] Pointer to the main-text bound added.
    - was: "suppression far beyond the $10^{\ChTwoKinLogRDetect}$ that the data require."
    - now: "suppression far beyond the $10^{\ChTwoKinLogRDetect}$ that the data require (main text, \S\ref{sec:gt_nucleation})."

## "Hydrothermal" -> "water vapor saturated" (2026-11-02; E. Stolper: the pressure is the water vapor pressure, set by temperature). Backups `*.pre_wvs_20261102`.

Kept: natural/literature senses (goethite recrystallization under hydrothermal conditions, Schwertmann 1985; "grew in a hydrothermal setting"; "possibly hydrothermal, fluids"), figure file names, the sample name HT-Win-06-01b, and the Zenodo dataset title in the bibliography.
Figures (legend text only; scripts backed up as `*.pre_wvs_20261102`, old PDFs in `generated/_pre_wvs_20261102/`): Ch2_spectra_combined (fig_ch2_spectra_combined.py), DeltasWinsorGTzoomin_VacuumHydrothermal (fig_delta_plot.py), winsor_goethite_Diffusivities_Arrhenius_Zoomin (fig_decomp_vs_hydrothermal.py), arrhenius_reaction_vs_diffusion (fig_goethite_vacuum_kinetics.py; also the label of the first-order delta plot, not used in the paper). "Hydrothermal ..." -> "Water vapor saturated ...". These figures are shared with thesis Chapter 2.

- **EDIT** [body: Introduction] "a step heat conducted under hydrothermal conditions" -> "a step heat conducted under water vapor saturated conditions"
- **EDIT** [body: Introduction] "for goethite under hydrothermal (high pH\textsubscript{2}O) conditions" -> "for goethite under water vapor saturated conditions"
- **EDIT** [body: Fig. ch2-sem caption] "inherited from before hydrothermal treatment" -> "inherited from before treatment at water vapor saturation"
- **EDIT** [body: Methods] "evolved gases from hydrothermal step heats" -> "evolved gases from water vapor saturated step heats"
- **EDIT** [body: Methods 2.1] "applied to the hydrothermal experiment" -> "applied to the water vapor saturated experiment"
- **EDIT** [body: Fig. ch2-arrhenius-zoom caption] "Apparent diffusivities under hydrothermal conditions" -> "Apparent diffusivities at water vapor saturation"
- **EDIT** [body: Fig. ch2-delta-zoom caption] "Win-06-01b in hydrothermal conditions" -> "Win-06-01b at water vapor saturation"
- **EDIT** [body: Fig. gt_arrhenius caption] "and of the hydrothermal step heat of this study" -> "and of the water vapor saturated step heat of this study"
- **EDIT** [body: 4.2] "for the vacuum and hydrothermal experiments: the hydrothermal experiment" -> "for the vacuum and water vapor saturated experiments: the water vapor saturated experiment"
- **EDIT** [body: 4.5] "The hydrothermal experiment records lower" -> "The water vapor saturated experiment records lower"
- **EDIT** [body: 4.5] "is slowest for the hydrothermal experiment" -> "is slowest for the water vapor saturated experiment"
- **EDIT** [body: 4.5] "differs between the hydrothermal and vacuum experiments." -> "differs between the water vapor saturated and vacuum experiments."
- **EDIT** [body: Fig. ch2-ratio-spectra caption] "the water-saturated hydrothermal experiment of this study" -> "the water vapor saturated experiment of this study"
- **EDIT** [body: Fig. ch2-ratio-spectra caption] "fitted to the hydrothermal spectrum" -> "fitted to the water vapor saturated spectrum"
- **EDIT** [body: Fig. ch2-ratio-spectra caption] "The hydrothermal experiment shows lower" -> "The water vapor saturated experiment shows lower"
- **EDIT** [body: Fig. ch2-ratio-spectra caption] "Hydrothermal steps with less than" -> "Steps of the water vapor saturated experiment with less than"
- **EDIT** [body: Fig. ch2-ratio-spectra caption] "where hydrothermal data exist" -> "where water vapor saturated data exist"
- **EDIT** [body: 4.5] "spectra of goethite under hydrothermal conditions are needed" -> "spectra of goethite at water vapor saturation are needed"
- GoethitePaper_body.tex: remaining "hydrothermal" kept on purpose (5): "...s[width=0.8\textwidth]{DeltasWinsorGTzoomin_VacuumHydrothermal.pdf} \caption{Delta plot simi..."; "...turated release. Goethite can recrystallize under hydrothermal conditions \citep{schwertmann..."; "...entering   \includegraphics[width=0.65\linewidth]{hydrothermal_hold_projection.pdf}   \capti..."; "...l above surface conditions  (perhaps it grew in a hydrothermal setting or experienced burial..."; "...t, favoring   crystallization from warm, possibly hydrothermal, fluids; burial of surface-fo..."
- **EDIT** [SI_body: S1.1] "permeability of ampoules used in hydrothermal step heats" -> "permeability of ampoules used in water vapor saturated step heats"
- **EDIT** [SI_body: Fig. ch2-ampoule-dims caption] "used in the hydrothermal step heats of Win-06-01b" -> "used in the water vapor saturated step heats of Win-06-01b"
- **EDIT** [SI_body: S4 surface energy] "which includes all of the hydrothermal experiments" -> "which includes all of the water vapor saturated experiments"
- **EDIT** [SI_body: S5 translation] "Applied step by step to the hydrothermal schedule" -> "Applied step by step to the water vapor saturated schedule"
- **EDIT** [SI_body: Fig. gt_pigment caption] "synthetic goethite pigment after hydrothermal treatment at 200--250~$^\circ$C" -> "synthetic goethite pigment after treatment at water vapor saturation and 200--250~$^\circ$C"
- GoethitePaper_SI_body.tex: remaining "hydrothermal" kept on purpose (0): 

## MDD / thermal-history methods condensed (2026-11-03; cite Farley & Flowers 2012 and Shuster & Farley 2004 rather than re-derive them). Paper only. Backups `*.pre_mddslim_20261103`.

- **EDIT/CUT** [Methods 2.2, lead + "Diffusion domain structure" + "Thermal histories" lead] Eqs. gt_mdd_domain, gt_mdd_mix and gt_mdd_S and the pointer to the SI forward model removed; procedure now cited to Farley and Flowers (2012) and Shuster and Farley (2004). Kept (unique to this work): two-stage approach, shared Stage 1 Ea, 28-step fitting window and treatment of the six low-signal steps, incremental domain addition, unfitted Arrhenius/delta plots, bulk He age from the same model. Typo "bythe" removed with the rewrite.
    > \subsection{Multiple Diffusion Domain and Thermal History Modeling}\label{sec:gt_mdd_methods} Together, the $^3$He release and the bulk-normalized $^4$He/$^3$He spectrum constrain the thermal history, if the activation energy for diffusion is known \citep{farleyflowers2012}. We interpret the data from HT-Win-06-01b in two stages. First, the diffusion domain structure of the sample is inverted from the $^3$He release alone. Second, natural thermal histories are fitted to the $^4$He/$^3$He spectrum with that domain structure held fixed. Fits for $N=1$--5 domains and the best-fitting thermal histories are given in the SI (\S\ref{sec:ch2-si-mdd}). \paragraph{Diffusion domain structure} Following \citet{farleyflowers2012}, the sample is represented by $N$ non-interacting spherical domains that share the activation energy of the Stage~1 regression (\S\ref{sec:gt_ht_results}). Each domain holds a fraction of the uniformly distributed, proton-induced $^3$He and has a radius relative to the reference domain of the Stage~1 regression, giving $2N-1$ free parameters. These minimize the summed squared misfit of the fractional and cumulative $^3$He yields, weighted equally, over the 28 steps with more than 0.1~pccSTP of $^3$He; the gas released in the six low-signal steps still counts toward the cumulative yields of later steps, and their durations toward the heating schedule. Domains are added one at a time, each search starting from the $(N-1)$-domain solution, until an added domain no longer changes the fit or the domain structure. The Arrhenius and delta plots are not fitted: they follow from applying the \citet{fechtigkalbitzer1966} inversion to the model cumulative release, and their misfit is reported as a reduced $\chi^2$ over the same 28 steps. \paragraph{Thermal histories} Each thermal history predicts a $^4$He/$^3$He spectrum and a bulk He age (taking U and Th to be distributed like the $^3$He) following \citet{shusterfarley2004}, applied to each domain of the four-domain structure. We compare two types of thermal histories, with two free parameters for steady cooling and three for burial and exhumation.
- **EDIT** [Methods 2.2, scoring] The misfit statistic (previously SI Eq. gt_mdd_chi2) stated in words in the main text: central bounding-method ratios, sigma = half the LB-UB range with a 0.02 floor, nu = 22/21. Hard age constraint (130-180 Ma) and the best-fit / parameter-range rule unchanged.
    > Each path is scored by the $\chi^2$ misfit of its predicted bulk-normalized ratios to the central ratios of the bounding method \citep{thyer2026data} over the \MDDNfit{} steps that have lag-correction bounds and more than 0.1~pccSTP of $^3$He, taking each uncertainty as half the range between the lower- and upper-bound ratios, with a floor of 0.02. The reduced $\chi^2$ uses $\nu=22$ degrees of freedom for steady cooling and $\nu=21$ for burial and exhumation.
- **CUT** [SI S6] Subsection "Forward modeling radiogenic 4He in nature and in the laboratory" (Eqs. ch2-si-mdd-modes, gt_mdd_N4, gt_mdd_ratio) removed; section retitled "Multiple Diffusion Domain Fits and Thermal History Results" with a one-sentence NEW lead citing the original methods.
- **EDIT** [SI Table ch2-mdd-thermal caption] "(see Eq. gt_mdd_chi2)" -> "(main text, S gt_mdd_methods)".
- **CUT** [SI S6] Subsection "Misfit statistic for thermal histories" removed (content now one sentence in Methods 2.2).
