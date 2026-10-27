# Chapter 4 (nGibbs) literature notes

Notes from the papers attached to the DissertationBJT project (Oct 2026), grouped by where they are used in the Ch. 4 Introduction and Application sections. Cite keys match the entries appended to `references.bib` on 2026-10-25.

## Cost of minimization and the lookup-table workaround
- **riel2022 (MAGEMin):** Parallel C library with a Julia wrapper, built for coupling to geodynamic codes. One point takes about 100–200 ms, depending on water content (as cited by Candioti 2026).
- **connolly2005, zunino2011, rummel2020:** Precomputed tables for a fixed composition. If the composition evolves, the table has to be interpolated in 10 or more dimensions.
- **gleeson2025 (PetThermoTools):** One Python interface to alphaMELTS for Python and to MAGEMin; only the `Model` keyword changes. Each MELTS calculation runs in its own child process, because a single convergence failure can otherwise halt a whole batch, and this fragility has limited Monte Carlo use of MELTS. Running MAGEMin from Python adds Julia start-up overhead. The H&P models do not include CO2.
- **ghiorsosack1995 (MELTS):** Calibrated on more than 2,500 liquid–solid experiments. Valid up to about 4 GPa and 900–1700 °C. The calibration database leans toward low-pressure, anhydrous, basalt-like liquids.

## Existing ML surrogates (Previous Work)
- **candioti2026 (ETH Zurich group)**
  - Uses MAGEMin with the Holland et al. (2018) database. The database was first validated against 484 arc-magma experiments.
  - Training data: 100 synthetic compositions along arc trends (47–66 wt% SiO2), all at a fixed 4 wt% H2O, over 0.1–10 kbar and 650–1300 °C. That gives about 980,000 equilibria.
  - The "fl" phase is excluded, so the fluid is pure H2O. Na2O and K2O are merged into one input.
  - The network predicts liquid and fluid presence, fraction and density, the liquid composition, and the system density. It does not predict minerals.
  - Solid properties are computed by difference (their Eq. 1). Mass balance therefore holds for the bulk solid by construction, but nothing constrains the liquid composition or liquid fraction to match the input bulk. Errors exceed 10% once liquid plus fluid exceeds 80 wt%.
  - Speed: about 3,000× faster than MAGEMin on 64 threads, and under 1 ms for 10,000 points on a GPU.
  - The authors argue that a single general surrogate across flow regimes is impractical, and they recommend retraining for each application.
  - Ben J. Thyer is thanked as a reviewer.
- **hartmeier2026**
  - Uses MAGEMin with the Stixrude & Lithgow-Bertelloni 2022 (SLB2022) database, which has no melt, no Fe3+ and no Cr.
  - The system is NCFMAS, covering 1–40 GPa and 500–2500 °C, with 2 million training points.
  - Compositions are sampled along the basalt–harzburgite join, with Dirichlet noise (λ = 100).
  - A classifier plus regressor predicts the fractions of 20 phases and the compositions of the solid solutions. Mass balance and closure enter only as soft loss penalties.
  - Accuracy is about ±0.01 mol/mol for phase fractions and ±0.005 mol/mol for compositions. Speed is about 35 ns per point on a GPU.
  - Gradient sensitivity: the 520-km transition is sensitive to fertility, and depleted mantle favors akimotoite near 660 km, which may depress the 660.
  - It predicts no physical properties.
- **yuan2025igythem (IGyTheM)**
  - Yuan, Asimow, Gurnis, Antoshechkina & Dong, AGU25 abstract; described in the geodynamics.org February 2026 highlight.
  - Trained on HeFESTo, treating the mantle as a mechanical mixture of basalt and harzburgite.
  - Covers 0–140 GPa and 273–4273 K, with 5.8 million points.
  - Coupled to Citcom, with the predicted density entering the momentum equation.
  - Ben's notes call this "Yuan2026"; swap in the journal article when it is out.
- **kerswell2024 (RocMLMs):** Predicts bulk density and seismic velocities of peridotite.

## Seismic and geophysical inversion
- **khan2008:** Stochastic inversion of Mars' Love number, Q, density and moment of inertia, with Gibbs minimization inside the sampler (CFMAS). Results: transition zone at about 1100 km depth, no lower mantle, CMB at about 20 GPa, a liquid core about 1680 km in radius, and Fe/Si about 1.2.
- **khan2021:** InSight body waves from 8 marsquakes, constraining structure to 800 km depth. Results: a 400–600 km lithosphere with an S-wave low-velocity zone, and a crust enriched 13–20× in heat-producing elements. The inversion uses **one fixed bulk composition** taken from the meteorites.
- **ishii2019:** The binary post-spinel transition spans 0.01 GPa (about 250 m), which explains the 660's sharpness (under 2 km) without a layered mantle. Latent heat can widen the transition by up to about 7 km where there is vertical flow, so sharpness could be used to map flow.
- **wood1996:** Garnet dissolving into perovskite produces steep but gradual velocity and density gradients between 660 and 750 km.

## Lowermost mantle
- **jackson2021:** Assemblages with Fe-rich (Mg,Fe)O fit many ULVZ case studies. ULVZs likely have diverse origins. Partial melt is probably not dense enough to stay at the base of the mantle (citing Thomas & Asimow 2013).
- **dobson2005:** Subducted banded iron formations (up to 85 wt% Fe oxide) as the source of ULVZs, with a bulk sound speed about 10% below PREM.
- **yuan2023:** Mantle material from Theia is 2.0–3.5% denser than the bulk silicate Earth, and may now form the LLVPs.
- **labrosse2007:** A crystallizing dense magma ocean at the base of the mantle.

## Heterogeneous mantle
- **hart1988:** Isotopes point to four end-members: DMM, HIMU, EMI and EMII. EMII is consistent with recycled sediment. HIMU and EMI are more likely metasomatic, and unlikely to be recycled crust or sediment.
- **stixrude2012, xu2008:** A mechanical mixture has different velocities from an equilibrium assemblage of the same bulk composition. A basalt–harzburgite mixture fits transition-zone seismology better than pyrolite, and about 18% basalt mass-balances to pyrolite.
- **stixrude2024 (HeFESTo III):** Adds Fe3+, the spin transition, native iron and Cr, and treats O as an independent component so that fO2 can be computed.

## Magma oceans
- **elkins-tanton2003, elkins-tanton2011:** Fractional crystallization leaves dense cumulates on top of lighter ones, which then overturn. The models assume complete reshuffling on all scales; in reality viscosity would limit this, leaving lateral heterogeneity.
- **miyazaki2022:** Rayleigh–Taylor instabilities at scales under 100 km leave Fe-rich blobs in a pyroxenite matrix (Mg# 94, about 75% of the mantle). In this scenario plate tectonics can operate, and CO2 is removed more than 10× faster than with a homogeneous pyrolitic mantle, within about 160 Myr.

## Smaller-scale igneous processes
- **boulanger2023:** Proposes the melt-flush process and argues that reactive porous flow is widespread. Their MELTS models are single-step, whereas natural samples record a protracted process.
- **yuan2024:** Slab break-off melting. Melt segregation was omitted because coupling multiphase flow to large-scale convection is computationally expensive.

## Primary magmas and MORB inversion
- **herzberg2008 (PRIMELT2):** Adds or subtracts olivine only. It cannot handle lavas that have fractionated cpx (usually below 7–10% MgO), and forcing it onto them gives MgO and Tp that are too high.
- **hernandezmontenegro2024 (PRIMARSMELT):** States that liquids which fractionated ol + cpx ± plag "cannot be easily inverted ... without a significant increase in computational cost and uncertainty." This is direct motivation for a fast forward model.
- **asimowlonghi2004:** A polybaric aggregate melt can masquerade as a multiple-saturation point (MSP). Even so, MSPs record the average pressure at which melt was extracted.
- **smithasimow2005, asimow2004, asimowlangmuir2003:** pHMELTS uses pMELTS for melting and MELTS for crystallization, and holds H2O in nominally anhydrous minerals as a hidden reservoir. Trace water significantly affects melting.
