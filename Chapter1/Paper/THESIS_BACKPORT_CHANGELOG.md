# Paper -> thesis Chapter 1 back-port (2026-11-02)

New material from the Geochronology paper moved into the thesis. No thesis text was changed except the in-text figure citations listed as CITE; everything listed as MOVE IN is copied verbatim from `TubeMethodPaper_body.tex` / `TubeMethodPaper_SI_body.tex` (line numbers as of 2026-11-02). Backups: `*.pre_paperbackport_20261102`.

- **CITE** [Permeation Step Method, para 2] `Eq.~\eqref{eq:permlag} returns the helium evolved from the natural sample, \(\omega\).` -> `Eq.~\eqref{eq:permlag} returns the helium evolved from the natural sample, \(\omega\) (Fig.~\ref{fig:schematic-permstep}).`
- **MOVE IN** [Permeation Step Method] Fig. schematic-permstep (Schematic_Sequence5.pdf) with its paper caption, verbatim (paper body L43-48).
- **CITE** [Bounding Method, para 2] `than what is predicted by Eq.~\eqref{eq:steadystate}.` -> `than what is predicted by Eq.~\eqref{eq:steadystate} (Fig.~\ref{fig:titanite-bounding}).`
- **CITE** [Bounding Method, para 3] `without permeation steps:` -> `without permeation steps (Fig.~\ref{fig:schematic-bounding}):`
- **MOVE IN** [Bounding Method] Figs. titanite-bounding (BoundingMethodTitaniteSim.pdf) and schematic-bounding (Schematic_Bounding3.pdf) with their paper captions, verbatim (paper body L153-165), after Fig. long-step-relative-uncertainty.
- **MOVE IN** [Analytical Methods, after para 1] Paper paragraph on the in-situ fits of the empty ampoule (first-step exclusion; R^2 justification), verbatim (paper body L213).
- **MOVE IN** [Results, after the 3He/4He permeation-ratio paragraph] Figs. insitu-lambda (InSituLambdaArrhenius.pdf) and insitu-examples (InSituLambdaFits_Examples.pdf) and the two paper results paragraphs (in-situ rate constants; isotope ratio), verbatim (paper body L225-241).
- **MOVE IN** [Results, after the Durango apatite paragraph] Fig. durango-lambda-selfcal (DurangoLambdaSelfCalibration.pdf) and the paper paragraph on the self-calibrated lambda_24, verbatim (paper body L252-263).
- **MOVE IN** [SI, before "Sample Preparation and SEM Imaging"] Paper SI section "In-situ Measurements of the Rate Constant lambda" (Fig. s-insitu-fits, InSituLambdaFits_Grid.pdf; Table s-insitu-lambda), verbatim (paper SI L360-374); only the \input path changed to the dissertation-root path Chapter1/Writing/paper_insitu_lambda_table.
- **MOVE IN** [chapter1.tex wrapper] \input{Chapter1/Writing/paper_derived_values} (\providecommand macros used by the moved paragraphs and captions).

## Typo fixes (2026-11-02), applied to both TubeMethodPaper_body.tex and chapter1_body.tex
Backups: `*.pre_typofix_20261102`.
- "shown in Fig.~\ref{fig:insitu-examples}) and listed" -> stray ")" removed.
- "(150, 175 and 250\textdegree)" -> "(150, 175 and 250\textdegree C)".
- "uncertaity" -> "uncertainty".
- Paper only: "(Eq.~\ref{fig:titanite-bounding})" -> "(Fig.~\ref{fig:titanite-bounding})".
