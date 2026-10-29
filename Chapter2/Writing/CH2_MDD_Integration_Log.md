# Chapter 2 — integration of the MDD / thermal-history analysis

Date: 2026-10-27. Source analysis: `Writing/winsor_mdd_free_report.tex` (figures and tables from `Figures/fig_winsor_mdd_report.py`, values in `Writing/mdd_free_report_values.tex`).

Backups of every edited file were made before editing, with the suffix `.pre_mdd_integration_20261027` (`Writing/chapter2_body.tex`, `Writing/chapter2goethite_SI_body.tex`, `Writing/chapter2_abstract.tex`, `Writing/chapter2goethite.tex`, `chapter2.tex`). `git diff` against HEAD shows the same changes (the CRLF files — abstract, SI body, `chapter2.tex` — were already CRLF in the working tree, so on a non-Windows git use `git diff --ignore-cr-at-eol`).

Line numbers refer to the ORIGINAL (pre-edit) files. Existing text was changed in only three places (A1, D, F); everything else is new text inserted at the location given.


## Summary

| ID | File | Location | Change |
|---|---|---|---|
| A1 | `Writing/chapter2_body.tex` | Experimental Methods, first paragraph (sample description) (orig. line 167-168) | Changed existing text |
| A2 | `Writing/chapter2_body.tex` | Experimental Methods: NEW subsection between "Kinetic and Diffusive Reductions of Step-Heat Data" and "SEM Study of Thermally Treated Goethite" (orig. line 385) | New text |
| B | `Writing/chapter2_body.tex` | Discussion > Helium Release under Water-Saturated Conditions Is Diffusive > Consistency with MDD Systematics: NEW text, table and two figures appended after the existing final paragraph (existing text unchanged) (orig. line 722) | New text |
| C | `Writing/chapter2_body.tex` | Discussion > High Helium Retentivity of Win-06-01b-HT: NEW sentences appended to the closure-temperature paragraph (orig. line 1016) | New text |
| D | `Writing/chapter2_body.tex` | Discussion > Profiling Radiogenic Helium Loss with 4He/3He Ratios: NEW closing sentence on the last paragraph (existing text unchanged) (orig. line 1182-1182) | Changed existing text |
| E | `Writing/chapter2_body.tex` | Discussion: NEW subsection "Thermal History of Win-06-01b" after "Profiling Radiogenic Helium Loss ..." and before Conclusions (orig. line 1184) | New text |
| F | `Writing/chapter2_body.tex` | Conclusions, second paragraph: REPLACED the closing either/or sentence (orig. line 1210-1212) | Changed existing text |
| G | `Writing/chapter2_abstract.tex` | Abstract: NEW sentences inserted after "...surface conditions over billion-year timescales." (orig. line 42) | New text |
| SI1 | `Writing/chapter2goethite_SI_body.tex` | SI body: NEW section "Multiple Diffusion Domain and Thermal History Model" appended at the end of the file (orig. line 700) | New text |
| H1 | `chapter2.tex` | Dissertation wrapper Chapter2/chapter2.tex: NEW \input of mdd_free_report_values (orig. line 36) | New text |
| H2 | `Writing/chapter2goethite.tex` | Standalone wrapper Chapter2/Writing/chapter2goethite.tex: NEW \input of mdd_free_report_values (orig. line 77) | New text |

## Open items flagged during integration

- **He age range.** The sample description says 180–135 Ma (Waltenberg 2012); the thermal-history modelling used 130–180 Ma. A `% TODO(BJT)` comment marks this at A1. If 135–180 Ma is correct, rerun `fig_winsor_mdd_report.py` with `MEASURED_AGE = (135, 180)` (and the same constant in `fig_winsor_mdd_alt_paths.py`) and update the numbers in E/F/G.
- **Abstract typo (pre-existing, not changed):** the line "that thermal decomposition of goethite is greatly suppressed in the presence" appears twice in a row in `chapter2_abstract.tex`.
- **Hard-coded numbers.** Table rows and a few values are macros from `mdd_free_report_values.tex`; the remaining numbers in B, C, E, F, G and SI1 are typed in and must be updated by hand if the analysis is rerun.
- **Superseded files (not deleted):** `Writing/chapter2_thermal_history_section.tex`, `chapter2_thermal_history_values.tex`, `_thermal_history_preview.tex`, `Figures/fig_winsor_mdd_free_chapter.py`, `Figures/fig_winsor_mdd_cooling_chapter.py`, older LRD scripts. `Writing/_mdd_integration_preview.pdf` is a throwaway preview of the edited pages.
- **Not compiled with biber here** (the Linux test VM lacks biblatex). A natbib test build of abstract + body + SI compiled without errors; the only undefined references are the pre-existing cross-references to Chapter 1 (`ch:apparatus`, `bounding-method`, `eq:steadystate`, …).

## Details

### A1. Experimental Methods, first paragraph (sample description)

- File: `Writing/chapter2_body.tex`; original line 167-168; operation: replace.

**Original text:**

```latex
ages: 180-135 Ma \citep{waltenberg2012}. To
produce
```

**New text:**

```latex
ages: 180-135 Ma \citep{waltenberg2012}. Its $^4$He/$^3$He spectrum constrains its
natural thermal history (\S\ref{sec:gt_thermal_history}).
% TODO(BJT): the thermal-history modeling uses a He age range of 130--180 Ma
% (\S\ref{sec:gt_mdd_methods}); reconcile with the 180-135 Ma quoted here.
To
produce
```

### A2. Experimental Methods: NEW subsection between "Kinetic and Diffusive Reductions of Step-Heat Data" and "SEM Study of Thermally Treated Goethite"

- File: `Writing/chapter2_body.tex`; original line 385; operation: insert before.
- Inserted before: `\subsection{SEM Study of Thermally Treated Goethite}`

**Inserted text:**

```latex
\subsection{Multiple Diffusion Domain and Thermal History Modeling}\label{sec:gt_mdd_methods}

The $^3$He release and the bulk-normalized $^4$He/$^3$He spectrum of HT-Win-06-01b are
interpreted in two stages. First, the diffusion domain structure of the sample is inverted
from the $^3$He release alone. Second, natural thermal histories are fitted to the
$^4$He/$^3$He spectrum with that domain structure held fixed, so that every thermal history
must work within the bounds set by the $^3$He data. Derivations and numerical details are
given in the SI (\S\ref{sec:ch2-si-mdd}).

\paragraph{Diffusion domain structure.} The sample is represented by $N$ non-interacting
spherical domains that share the activation energy and frequency factor of the Stage~1
regression (\S\ref{sec:gt_ht_results}). Domain $j$ holds a fraction $f_j$ of the uniformly
distributed, proton-induced $^3$He ($\sum_j f_j=1$) and has radius $r_j$ relative to the
reference radius $r_0$ implied by the Stage~1 regression, so that
\begin{equation}
  \left(\frac{D}{a^2}\right)_j = \left(\frac{r_j}{r_0}\right)^{-2}\frac{D_0}{a_0^2}\exp\!\left(-\frac{E_a}{RT}\right).
  \label{eq:gt_mdd_domain}
\end{equation}
A model with $N$ domains has $2N-1$ free parameters. During the heating schedule, the
reference domain accumulates the non-dimensional time
$\tau_{0,i}=\sum_{m\le i}(D_0/a_0^2)\exp(-E_a/RT_m)\,\Delta t_m$ by the end of step $i$, and
domain $j$ reaches $\tau_{0,i}(r_j/r_0)^{-2}$. With $F(\tau)$ the cumulative fraction released
by an initially uniform sphere \citep{crank1979}, the model cumulative and fractional
$^3$He yields are
\begin{equation}
  \Sigma F_i=\sum_{j=1}^{N}f_j\,F\!\left(\tau_{0,i}\,(r_j/r_0)^{-2}\right),\qquad
  \Delta F_i=\Sigma F_i-\Sigma F_{i-1}.
  \label{eq:gt_mdd_mix}
\end{equation}
Following \citet{farleyflowers2012}, the fractional and cumulative yields are weighted
equally, and $\{f_j,r_j\}$ minimize
\begin{equation}
  S=\sum_i\left(\Delta F_i^{\mathrm{mod}}-\Delta F_i^{\mathrm{obs}}\right)^2
   +\sum_i\left(\Sigma F_i^{\mathrm{mod}}-\Sigma F_i^{\mathrm{obs}}\right)^2,
  \label{eq:gt_mdd_S}
\end{equation}
summed over the 28 steps with more than 0.1~pccSTP of $^3$He. The gas released in the six
low-signal steps still counts toward the cumulative yields of later steps, and their
durations toward the heating schedule. Domains are added one at a time, each search
starting from the $(N-1)$-domain solution, until an added domain no longer changes the fit
or the domain structure. The Arrhenius and delta plots are not fitted: they follow from
applying the \citet{fechtigkalbitzer1966} inversion to the model cumulative release, and
their misfit is reported as a reduced $\chi^2$ over the same 28 steps.

\paragraph{Radiogenic $^4$He in nature and in the laboratory.} Each domain produces
$^4$He uniformly at rate $P$ and loses it by diffusion through a zero-concentration
boundary from the time of crystallization, $t_\mathrm{form}$. The concentration is
expanded in the eigenfunctions of the sphere, $C=\sum_kA_k(t)\sin(k\pi x)/x$, where $x$ is
radial position normalized to the domain radius \citep{carslawjaeger1959}, and the
amplitudes $A_k$ are integrated exactly through a thermal history discretized into
1--2~Myr intervals of constant temperature (\S\ref{sec:ch2-si-mdd}). Because the
eigenfunctions do not depend on $D$, the present-day amplitudes $A_{k,j}$ carry each
domain's non-uniform natural $^4$He profile into the laboratory, where each mode decays as
$\exp(-k^2\pi^2\tau)$. The $^4$He remaining in domain $j$ when the reference domain has
reached laboratory time $\tau$ is therefore
\begin{equation}
  N_j(\tau)=3\sum_k A_{k,j}\,\frac{(-1)^{k+1}}{k\pi}\exp\!\left[-k^2\pi^2\tau\left(\frac{r_j}{r_0}\right)^{-2}\right],
  \label{eq:gt_mdd_N4}
\end{equation}
and the predicted step ratio is
\begin{equation}
  \frac{R_{\mathrm{step},i}}{R_\mathrm{bulk}}=\frac{\Delta N_{4,i}/N_{4,\mathrm{tot}}}{\Delta F_i^{\mathrm{obs}}},
  \qquad
  \Delta N_{4,i}=\sum_jf_j\left[N_j(\tau_{0,i-1})-N_j(\tau_{0,i})\right],
  \label{eq:gt_mdd_ratio}
\end{equation}
where $N_{4,\mathrm{tot}}=\sum_jf_jN_j(0)$ includes the gas released at fusion. The
reference times $\tau_{0,i}$ are solved from the \emph{measured} cumulative $^3$He by
inverting Eq.~\eqref{eq:gt_mdd_mix}, so the prediction does not depend on the heating
schedule or on step-to-step scatter in the kinetics, and no uniform $^4$He distribution is
assumed at the start of the experiment. Taking U and Th to be distributed like the $^3$He,
the bulk He age is $t_\mathrm{He}=\sum_jf_jN_j(0)/P$.

\paragraph{Thermal histories.} We compare three families of piecewise-linear thermal
history, each with two free parameters.
\begin{itemize}
  \item \textbf{Steady cooling:} the temperature falls linearly from $T_0$ at
  $t_\mathrm{form}$ to 25\,\textdegree C today. The goethite forms at an elevated
  temperature, for example from warm fluids at depth, and cools monotonically. Free
  parameters: $t_\mathrm{form}$ and $T_0$.
  \item \textbf{Burial and exhumation:} the path passes through $(t_\mathrm{form},T_s)$,
  $(t_\mathrm{peak},T_\mathrm{max})$, $(50~\mathrm{Ma},T_s)$ and $(0,T_s)$ with
  $T_s=20$\,\textdegree C. The goethite forms at the surface, is buried and heated to a
  peak temperature, and is exhumed by the Paleogene, when sediments in Flinders Ranges
  valleys show that basement was exposed \citep{mitchell1998}. Free parameters:
  $t_\mathrm{peak}$ and $T_\mathrm{max}$, for fixed crystallization ages of 180, 195 and
  210~Ma.
  \item \textbf{Isothermal hold:} $T=T_\mathrm{iso}$ from $t_\mathrm{form}$ to the
  present. Free parameters: $t_\mathrm{form}$ and $T_\mathrm{iso}$.
\end{itemize}
Each path is scored against
\begin{equation}
  \chi^2=\sum_i\left(\frac{R_i^{\mathrm{mod}}-R_i^{\mathrm{M}}}{\sigma_i}\right)^2,
  \qquad\sigma_i=\max\!\left[\tfrac12\left(R_i^{\mathrm{UB}}-R_i^{\mathrm{LB}}\right),\,0.02\right],
  \label{eq:gt_mdd_chi2}
\end{equation}
over the \MDDNfit{} steps that have lag-correction bounds and more than 0.1~pccSTP of
$^3$He ($\nu=22$), where M, LB and UB are the central, lower-bound and upper-bound
bulk-normalized ratios of the bounding method (Table~\ref{tab:ch2-distilled-4he}).
$\chi^2$ is mapped on regular grids: for burial, $t_\mathrm{peak}$ from 55~Ma to
$t_\mathrm{form}-2.5$~Ma in 2.5~Myr steps and $T_\mathrm{max}=30$--90\,\textdegree C; for
steady cooling and the isothermal hold, $t_\mathrm{form}=50$--500~Ma in 5~Myr steps and
$T_0=25$--120\,\textdegree C or $T_\mathrm{iso}=0$--70\,\textdegree C, with temperatures in
1\,\textdegree C steps. The joint 1$\sigma$ region of each map is
$\chi^2\le\chi^2_{\min}+2.30\max(1,\chi^2_\nu)$. The measured He age (130--180~Ma;
\citealt{waltenberg2012}) is treated as a hard constraint: the best fit of each family is
the lowest-$\chi^2$ path with a predicted age in that range, and parameter ranges are those
of the age-consistent paths within the same $\Delta\chi^2$ of that best fit.
```

### B. Discussion > Helium Release under Water-Saturated Conditions Is Diffusive > Consistency with MDD Systematics: NEW text, table and two figures appended after the existing final paragraph (existing text unchanged)

- File: `Writing/chapter2_body.tex`; original line 722; operation: insert after.
- Inserted after: `often observed in the apparent diffusivities for polycrystalline
hematite \citep{farley2018}.`

**Inserted text:**

```latex
A multiple diffusion domain inversion of the $^3$He release (\S\ref{sec:gt_mdd_methods})
quantifies this inference (Table~\ref{tab:ch2-mdd-domains}; Fig.~\ref{fig:ch2-mdd-domains}).
A single domain cannot fit the release (Arrhenius $\chi^2_\nu=27$), and two domains capture
the high early diffusivities but leave a poor Arrhenius fit ($\chi^2_\nu=3.3$). Three
domains reduce the yield misfit by more than half ($\chi^2_\nu=1.08$). With four, the
smallest domain splits in two and the fit improves slightly further ($\chi^2_\nu=1.00$).
Every domain added beyond four coincides in size with the dominant domain and leaves the
fit unchanged. We therefore adopt four domains as a complete description of the $^3$He data:
\begin{itemize}
  \item 0.57\% of the $^3$He at $r/r_0=6.8\times10^{-4}$;
  \item 0.66\% at $2.9\times10^{-3}$;
  \item 1.5\% at 0.031;
  \item 97.2\% at 1.12.
\end{itemize}
The three small domains, holding 2.8\% of the $^3$He in total, are fully degassed during the
experiment and account for the high early diffusivities and the gradual approach of the
delta plot to the Stage~1 line (Fig.~\ref{fig:ch2-mdd-arrh-delta}). The dominant domain releases
12\% of its $^3$He during the experiment and diffuses at 0.80 times the Stage~1 rate. The
Stage~1 line is therefore a slightly fast description of the dominant domain, because the
bulk-inverted diffusivities on which it was regressed still carry a small contribution from
the fast domains. The four-domain model reproduces the Arrhenius array, including its
retrograde segments, and the delta plot, although neither is fitted directly. Fits for
$N=1$--5 are shown in the SI (Fig.~\ref{fig:ch2-si-mdd-3he-fits}).

\begin{table}[htbp]
\centering
\caption{Multiple diffusion domain fits to the $^3$He release of HT-Win-06-01b ($N$ domains,
$k=2N-1$ parameters). RMS is the yield misfit ($\times10^{-4}$, fraction of total $^3$He)
over the 28 steps above the signal threshold. ``Fast'' is the $^3$He fraction in domains
with $r/r_0<0.1$; $f_\mathrm{main}$ and $r_\mathrm{main}/r_0$ are the fraction and size of
the largest-fraction domain. For $N\ge5$, the dominant domain is split among several
domains of identical size.}
\label{tab:ch2-mdd-domains}
\begin{tabular}{rrrrrrr}
\toprule
$N$ & $k$ & RMS & Arrh.\ $\chi^2_\nu$ & fast (\%) & $f_\mathrm{main}$ (\%) & $r_\mathrm{main}/r_0$\\
\midrule
\MDDDomainTableRows
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.7\textwidth]{mdd_free/absolute/chapter/ch2_mdd_domains.pdf}
\caption{Domain spectra of the best-fitting multiple diffusion domain models for $N=1$--10.
Symbol area scales with the square root of the $^3$He fraction; the dashed line marks the
Stage~1 reference domain. The three small domains are unchanged from $N=4$ onward; domains
added beyond $N=4$ coincide in size with the dominant domain.}
\label{fig:ch2-mdd-domains}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{mdd_free/absolute/chapter/ch2_mdd_arrh_delta_N4.pdf}
\caption{(a) Arrhenius plot and (b) delta plot (departure from the Stage~1 line) of the
measured $^3$He diffusivities of HT-Win-06-01b, with the values implied by the four-domain
fit to the $^3$He yields. Neither plot is fitted directly. The six low-signal steps are
omitted.}
\label{fig:ch2-mdd-arrh-delta}
\end{figure}
```

### C. Discussion > High Helium Retentivity of Win-06-01b-HT: NEW sentences appended to the closure-temperature paragraph

- File: `Writing/chapter2_body.tex`; original line 1016; operation: insert after.
- Inserted after: `temperature for that domain would be \ChTwoTc ± \ChTwoTcErr °C.`

**Inserted text:**

```latex
The multiple diffusion domain inversion (\S\ref{consistency-with-mdd-systematics}) indicates
that the dominant domain, which holds 97\% of the $^3$He, diffuses at 0.80 times the rate of
the Stage~1 line. Its closure temperature is correspondingly about 1.6\,\textdegree C higher,
well within the quoted uncertainty; the Stage~1 parameters are used throughout this section.
```

### D. Discussion > Profiling Radiogenic Helium Loss with 4He/3He Ratios: NEW closing sentence on the last paragraph (existing text unchanged)

- File: `Writing/chapter2_body.tex`; original line 1182-1182; operation: replace.

**Original text:**

```latex
recrystallization caused partial helium loss in nature.
```

**New text:**

```latex
recrystallization caused partial helium loss in nature. Section~\ref{sec:gt_thermal_history}
tests whether thermally activated diffusion alone, within the domain structure inferred from
the $^3$He release, can reproduce the measured spectrum.
```

### E. Discussion: NEW subsection "Thermal History of Win-06-01b" after "Profiling Radiogenic Helium Loss ..." and before Conclusions

- File: `Writing/chapter2_body.tex`; original line 1184; operation: insert before.
- Inserted before: `\section{Conclusions}\label{conclusions}`

**Inserted text:**

```latex
\subsection{Thermal History of Win-06-01b}\label{sec:gt_thermal_history}

Win-06-01b was collected as float in the Flinders Ranges, South Australia. Apatite
fission-track studies in the region record cooling from roughly 50--70\,\textdegree C after
the mid-Cretaceous \citep{gibsonstuwe2000,mitchell1998}, and Triassic intramontane basins
less than 1.5~km thick indicate that parts of the ranges were near the surface in the Early
Mesozoic \citep{mitchell1998}. With the four-domain structure of
\S\ref{consistency-with-mdd-systematics} held fixed, we fitted steady-cooling,
burial-and-exhumation and isothermal thermal histories to the $^4$He/$^3$He spectrum
(\S\ref{sec:gt_mdd_methods}). Table~\ref{tab:ch2-mdd-thermal} gives the best fit of each
family, Fig.~\ref{fig:ch2-mdd-spectrum-compare} compares the best steady-cooling and burial
predictions with the spectrum, and Fig.~\ref{fig:ch2-mdd-heatmaps} shows their $\chi^2$ maps on a
common colour scale.

\begin{table}[htbp]
\centering
\caption{Thermal histories fitted to the $^4$He/$^3$He spectrum of HT-Win-06-01b with the
four-domain structure fixed. Each row gives the best path with a predicted He age of
130--180~Ma ($\nu=22$). For steady cooling, $T_\mathrm{max}=T_0$ is reached at
crystallization, so $t_\mathrm{peak}=t_\mathrm{form}$. For the isothermal hold,
$T_\mathrm{max}=T_\mathrm{iso}$ throughout. Burial crystallization ages are fixed. The last
three columns give the ranges of the age-consistent paths within the joint 1$\sigma$ region
about the best fit.}
\label{tab:ch2-mdd-thermal}
\resizebox{\textwidth}{!}{%
\begin{tabular}{lrrrrrlll}
\toprule
Path & $t_\mathrm{form}$ (Ma) & $t_\mathrm{peak}$ (Ma) & $T_\mathrm{max}$ (\textdegree C) &
$\chi^2_\nu$ & $t_\mathrm{He}$ (Ma) & $t_\mathrm{form}$ (1$\sigma$) & $t_\mathrm{peak}$ (1$\sigma$) &
$T_\mathrm{max}$ (1$\sigma$)\\
\midrule
\MDDThermalTableRows
\bottomrule
\end{tabular}}
\end{table}

\paragraph{Steady cooling.} Linear cooling to 25\,\textdegree C fits the spectrum best. The best
age-consistent path starts at 78\,\textdegree C at 150~Ma ($\chi^2_\nu=2.00$), and the
age-consistent 1$\sigma$ range is crystallization at 150--175~Ma at 76--80\,\textdegree C,
followed by cooling at $\sim$0.3\,\textdegree C\,Myr$^{-1}$. Such paths pass through
$\sim$55\,\textdegree C at 90~Ma, inside the apatite fission-track window. The spectrum alone
prefers somewhat younger, hotter paths: the unconstrained minimum
($\chi^2_\nu=\MDDLinGlobalChi$; \MDDLinGlobalT\,\textdegree C at \MDDLinGlobalTform~Ma) predicts
a He age of \MDDLinGlobalAge~Ma, and the unconstrained 1$\sigma$ region lies entirely at ages
younger than 130~Ma (Fig.~\ref{fig:ch2-mdd-heatmaps}b). Requiring the measured age costs
$\Delta\chi^2\approx7$.

\paragraph{Burial and exhumation.} Burial paths fit the spectrum less well
($\chi^2_\nu=4.8$--6.2), but they agree closely with independent regional constraints. For
crystallization at 180 and 195~Ma, the best age-consistent paths peak at 61\,\textdegree C at
70 and 80~Ma, with 1$\sigma$ ranges of 58--65\,\textdegree C between 98 and 60~Ma
(Fig.~\ref{fig:ch2-mdd-heatmaps}a). These peaks fall in or just after the apatite
fission-track window, within the 50--70\,\textdegree C range of \citet{gibsonstuwe2000} and at
the $<$60\,\textdegree C limit reported near Copley \citep{mitchell1998}. For crystallization at
210~Ma, only hotter and earlier peaks (70--74\,\textdegree C at 105--130~Ma) give an age within
the measured range, and they fit worse ($\chi^2_\nu=6.2$).

\paragraph{Isothermal hold.} The spectrum constrains only the product of diffusivity and
time, so the $\chi^2$ minimum is a ridge from $\sim$47\,\textdegree C at 50~Ma to
$\sim$35\,\textdegree C at 500~Ma, along which $\chi^2_\nu\approx\MDDIsoChi$ throughout. No
isothermal path reproduces the shape of the spectrum: they underpredict the ratios of the
early steps and overpredict those of the late steps. We do not consider this family further.

\paragraph{Where the families differ.} The steady-cooling and burial predictions differ
mainly in the earliest steps ($\Sigma F_{3\mathrm{He}}\lesssim0.035$;
Fig.~\ref{fig:ch2-mdd-spectrum-compare}), which sample the outer rim of the dominant domain. On
the burial path the sample sits at 20\,\textdegree C for the last 50~Myr, long enough for
radiogenic $^4$He to re-accumulate in the rim, so the early ratios are overpredicted. Steady
cooling keeps the rim depleted until geologically recent times, with diffusive loss
declining monotonically toward the present. Elsewhere both leave the same residual pattern:
ratios underpredicted between $\Sigma F_{3\mathrm{He}}=0.04$ and 0.06, and overpredicted in
the two longest high-temperature steps.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{mdd_free/absolute/chapter/ch2_mdd_spectrum_compare_N4.pdf}
\caption{Bulk-normalized $^4$He/$^3$He spectrum of HT-Win-06-01b (black, bounding-method LB--UB
boxes) with the best age-consistent burial path for crystallization at 195~Ma (blue) and the
best age-consistent steady-cooling path (green), for the four-domain structure.}
\label{fig:ch2-mdd-spectrum-compare}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{mdd_free/absolute/chapter/ch2_mdd_heatmaps_N4.pdf}
\caption{Reduced $\chi^2$ of the $^4$He/$^3$He spectrum for (a) burial paths with crystallization
at 195~Ma, as a function of the time and magnitude of peak temperature, and (b) steady cooling
to 25\,\textdegree C, as a function of crystallization age and initial temperature. Both panels
share one colour scale, anchored to the overall minimum. White outlines show the joint
1$\sigma$ region of each map, dashed lines the predicted bulk He age at 130 and 180~Ma,
diamonds the best fit, and the star the best fit with a He age of 130--180~Ma. The orange box
in (a) is the apatite fission-track peak window \citep{gibsonstuwe2000,mitchell1998}.}
\label{fig:ch2-mdd-heatmaps}
\end{figure}

\paragraph{Formation setting.} The two families encode different formation settings.
Burial assumes the goethite formed at the surface, for example in a weathering profile, and
was later buried. Steady cooling has it forming at $\sim$76--80\,\textdegree C. The better fit of
steady cooling therefore favours crystallization from warm fluids, in a hydrothermal system
or at depth, over formation at the surface. Burial nevertheless remains a viable
alternative: it is the setting assumed by most goethite (U--Th)/He studies, and it matches
the independent fission-track constraints closely. Two further qualifications apply. First,
a hydrothermal system cools to ambient temperature in far less than a million years, so the
150~Myr linear decline is not the cooling of the system itself. It implies that the sample
stayed in a warm subsurface setting after crystallization and cooled slowly, by exhumation
or a declining geotherm, and the two-parameter family cannot separate the fluid temperature
at crystallization from the ambient temperature shortly afterwards. Second, the comparison
is between parameterized families: a burial path with a warmer Cenozoic, or a brief
hydrothermal pulse followed by slow cooling, has not been tested and might fit as well.

\paragraph{Remaining misfit and caveats.} Even the steady-cooling solution leaves systematic
residuals. The intermediate domain ($r/r_0\approx0.03$, 1.5\% of the $^3$He) degasses at
$\Sigma F_{3\mathrm{He}}\approx0.02$--0.06. With the common activation energy, it would have
lost most of its radiogenic $^4$He in nature, which depresses the predicted ratios where the
measured ratios are highest. A higher activation energy for this domain, which the retrograde
segments of the experiment could test, or domain-dependent $^4$He production, for example from
U--Th zoning across colloform bands, could remove this misfit while preserving the $^3$He fit;
each adds one parameter. A two-domain structure fits the spectrum better but reproduces the
$^3$He Arrhenius array poorly, so we do not adopt it (\S\ref{sec:ch2-si-mdd}). The temperature
scale rests on extrapolating the Stage~1 activation energy from 200--250\,\textdegree C to
near-surface temperatures ($\pm\sim$4\,\textdegree C near 60\,\textdegree C, not propagated
here); the surface temperatures and the burial exhumation time are fixed; and U and Th are
assumed to be distributed like the $^3$He, both within and among domains.
```

### F. Conclusions, second paragraph: REPLACED the closing either/or sentence

- File: `Writing/chapter2_body.tex`; original line 1210-1212; operation: replace.

**Original text:**

```latex
The \textsuperscript{4}He data require that this domain
experienced helium loss in nature, suggesting either that Win-06-01b was hydrothermal in origin,
or that non-thermal processes such as fluid-mediated recrystallization contributed to helium loss in nature.
```

**New text:**

```latex
The \textsuperscript{4}He data require that this domain
experienced helium loss in nature. A four-domain diffusion model fitted to the $^3$He release
shows that 97\% of the $^3$He resides in a single domain and can account for this loss by
thermally activated diffusion alone. Within that model, steady cooling from crystallization at
76--80\,\textdegree C at 150--175~Ma to the present surface temperature fits the
$^4$He/$^3$He spectrum best, favouring crystallization from warm, possibly hydrothermal, fluids.
Burial of surface-formed goethite to a Late Cretaceous peak of 58--65\,\textdegree C, consistent
with regional apatite fission-track constraints, remains a viable alternative.
```

### G. Abstract: NEW sentences inserted after "...surface conditions over billion-year timescales."

- File: `Writing/chapter2_abstract.tex`; original line 42; operation: after.
- Inserted after: `surface conditions over billion-year timescales.`

**Inserted text:**

```latex
 A four-domain diffusion model fitted to the $^3$He release places 97\% of the $^3$He in a
single domain and attributes the natural loss of radiogenic helium from that domain to
thermally activated diffusion. Steady cooling from crystallization at $\sim$76--80\,\textdegree C
in the Jurassic fits the $^4$He/$^3$He spectrum best, favouring a hydrothermal origin, while
burial of surface-formed goethite to $\sim$60\,\textdegree C in the Late Cretaceous remains a
viable alternative.
```

### SI1. SI body: NEW section "Multiple Diffusion Domain and Thermal History Model" appended at the end of the file

- File: `Writing/chapter2goethite_SI_body.tex`; original line 700; operation: after.
- Inserted after: `conversion, because it enters the small $\Delta\mu_{\mathrm{sat}}$ (6--11~kJ) squared.`

**Inserted text:**

```latex
\section{Multiple Diffusion Domain and Thermal History Model}\label{sec:ch2-si-mdd}

This section gives the details of the model summarized in \S\ref{sec:gt_mdd_methods} of the
main text.

\subsection{Natural $^4$He profiles}
Each spherical domain produces $^4$He uniformly at rate $P$ and loses it by diffusion with a
zero-concentration boundary,
\begin{equation}
  \frac{\partial C}{\partial t}=\frac{D}{a^2}\,\frac{1}{x^2}\frac{\partial}{\partial x}\!\left(x^2\frac{\partial C}{\partial x}\right)+P,
  \qquad C(1,t)=0,\quad C(x,t_\mathrm{form})=0 ,
  \label{eq:ch2-si-mdd-pde}
\end{equation}
where $x$ is radial position normalized to the domain radius. With
$C=\sum_k A_k(t)\sin(k\pi x)/x$ \citep{carslawjaeger1959}, each mode evolves as
\begin{equation}
  \frac{\mathrm{d}A_k}{\mathrm{d}t}=-k^2\pi^2\frac{D}{a^2}A_k+c_kP,\qquad c_k=\frac{2(-1)^{k+1}}{k\pi},
  \label{eq:ch2-si-mdd-modes}
\end{equation}
which over an interval $\Delta t$ at constant temperature has the exact solution
\begin{equation}
  A_k \leftarrow A_k e^{-\lambda_k}+c_kP\,\Delta t\,\frac{1-e^{-\lambda_k}}{\lambda_k},
  \qquad \lambda_k=k^2\pi^2\frac{D}{a^2}\Delta t .
  \label{eq:ch2-si-mdd-update}
\end{equation}
Thermal histories are discretized into intervals of constant temperature of 2~Myr (burial)
or 1~Myr (steady cooling); an isothermal hold is a single interval. The $^4$He content per
unit volume of a domain is $N=3\sum_kA_k(-1)^{k+1}/(k\pi)$. We use 8000 modes; truncating the
series at 500 modes changes the predicted spectrum by less than $10^{-4}$ in
$R/R_\mathrm{bulk}$. The He age neglects parent decay ($\sim$3\% over 200~Myr).

\subsection{Laboratory degassing of non-uniform profiles}
The eigenfunctions $\sin(k\pi x)/x$ form a complete set for radially symmetric profiles that
vanish at the domain boundary, and they do not depend on $D$. The present-day amplitudes
therefore describe the non-uniform natural $^4$He profile exactly, and in the laboratory each
amplitude decays independently as $\exp(-k^2\pi^2\tau)$ (Eq.~\ref{eq:gt_mdd_N4}). To check the
implementation, we solved the same problem without the series, using a conservative
finite-volume discretization on 2000 spherical shells integrated exactly in time, for the
same natural history and laboratory schedule (Fig.~\ref{fig:ch2-si-nonuniform-check}). The two
spectra agree to $8\times10^{-4}$ in $R/R_\mathrm{bulk}$. Spreading the same amount of $^4$He
uniformly through each domain instead would raise $\chi^2$ from 109 to $\sim$3500, so the
spectrum is controlled by the shape of the natural profiles, mainly the depleted rim of the
dominant domain.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{mdd_free/absolute/chapter/ch2_check_nonuniform_N4.pdf}
\caption{Check of the laboratory degassing of natural $^4$He profiles, for the four-domain
structure on the burial path 190$\rightarrow$74~Ma, 60\,\textdegree C. Left: present-day $^4$He
profiles from the eigenfunction series (lines) and an independent finite-volume solution
(2000 shells, symbols). Middle: cumulative laboratory release on the same schedule, for the
natural profiles and for the same $^4$He spread uniformly. Right: the series and
finite-volume spectra agree to $8\times10^{-4}$ in $R/R_\mathrm{bulk}$; assuming uniform
$^4$He would raise $\chi^2$ from 109 to $\sim$3500.}
\label{fig:ch2-si-nonuniform-check}
\end{figure}

\subsection{Multiple diffusion domain fits for $N=1$--5}
Figure~\ref{fig:ch2-si-mdd-3he-fits} shows the fitted fractional and cumulative $^3$He yields,
and the Arrhenius and delta plots they imply, for one to five domains. The fits for all $N$
are summarized in Table~\ref{tab:ch2-mdd-domains} of the main text.

\begin{figure}[p]
\centering
\includegraphics[width=\textwidth,height=0.85\textheight,keepaspectratio]{mdd_free/absolute/chapter/ch2_mdd_3he_fits_N1-5.pdf}
\caption{Multiple diffusion domain fits to the $^3$He release of HT-Win-06-01b for $N=1$--5
domains (rows). Columns: fitted fractional and cumulative yields, and the Arrhenius and
delta plots implied by each fit. Hollow grey symbols are the six low-signal steps, which
are not fitted and are omitted from the Arrhenius and delta plots.}
\label{fig:ch2-si-mdd-3he-fits}
\end{figure}

\subsection{Two-domain alternative}
The two-domain structure (2.2\% of the $^3$He at $r/r_0=5.4\times10^{-3}$, 97.8\% at 1.05) fits
the $^4$He/$^3$He spectrum better than the adopted four-domain structure: a burial path with
crystallization at 195~Ma and a peak of $\sim$66\,\textdegree C at $\sim$100~Ma gives
$\chi^2_\nu\approx1.3$. However, this structure reproduces the $^3$He Arrhenius array poorly
($\chi^2_\nu=3.3$; Fig.~\ref{fig:ch2-si-mdd-3he-fits}), so we do not adopt it.
```

### H1. Dissertation wrapper Chapter2/chapter2.tex: NEW \input of mdd_free_report_values

- File: `chapter2.tex`; original line 36; operation: after.
- Inserted after: `\input{Chapter2/Writing/chapter2_kinetics_values}`

**Inserted text:**

```latex
% Auto-generated multiple-diffusion-domain and thermal-history tables/values
% (\MDDDomainTableRows, \MDDThermalTableRows, \MDDNfit, \MDDLinGlobal*, \MDDIsoChi) -- see
% Chapter2/Figures/fig_winsor_mdd_report.py. Do not edit the generated file by hand.
\input{Chapter2/Writing/mdd_free_report_values}
```

### H2. Standalone wrapper Chapter2/Writing/chapter2goethite.tex: NEW \input of mdd_free_report_values

- File: `Writing/chapter2goethite.tex`; original line 77; operation: after.
- Inserted after: `\input{chapter2_kinetics_values}`

**Inserted text:**

```latex
% Auto-generated multiple-diffusion-domain and thermal-history tables/values -- see
% Chapter2/Figures/fig_winsor_mdd_report.py. Do not edit the generated file by hand.
\input{mdd_free_report_values}
```

