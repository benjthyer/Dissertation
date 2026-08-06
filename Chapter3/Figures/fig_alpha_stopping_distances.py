"""
Two companion plots on U-Th-Sm-bearing apatite micro-inclusions hosted
within a sulfide grain, as a function of inclusion size: the fraction of
helium that ends up sulfide- vs. inclusion-hosted, and the apparent bulk
He age that mixture would imply.

Physical picture (shared by both plots): U, Th, and Sm decay chains eject
alpha particles (future He atoms) a characteristic stopping distance S
(tabulated per isotope in data/alpha_stopping_distances.csv, Ketcham et
al. 2011-style values) from wherever they decay. If a U-Th-Sm-bearing
inclusion (here, apatite -- the classic accessory phase for this)
sitting inside a sulfide host is much smaller than S, essentially every
decay's alpha recoils clean out of the inclusion and stops in the
surrounding sulfide, so ~all the helium ends up sulfide-hosted. If the
inclusion is much larger than S, only a thin ~S-thick rind near its
surface loses helium to the sulfide, and the bulk of the inclusion
self-implants its own helium. The standard alpha-ejection retention
factor Ft (Farley et al. 1996, Eqn 3 -- thermochr_utils.Ft, used
elsewhere in this dissertation for recoil-correcting measured grain
ages) gives the fraction of helium RETAINED in a grain of a given size;
1-Ft is therefore exactly the fraction ejected into the surroundings --
i.e. sulfide-hosted here, whereas in its usual application it's the
fraction lost to whatever medium (void, epoxy, adjacent grain) surrounds
a dated grain.

Farley (1996)'s closed form Ft = 1 - (3/4)(S/R) + (1/16)(S/R)^3 is only
valid for R >= S (a surface-correction term derived as a small
perturbation from full retention, never intended to extrapolate below
R = S). thermochr_utils.Ft patches this with a hard clamp to Ft=0 for
R < S, which is exact only for R <= S/2: the longest possible ejection
path through a sphere is its diameter 2R, so if S > 2R literally every
decay's alpha must exit regardless of position or direction. But for
S/2 < R < S there IS some real, partial retention -- e.g. a decay at the
grain surface aimed straight through the center has a 2R-long path
available, which for R=0.6S (S=1, R=0.6) comfortably contains a
stopping distance of 1 -- that thermochr_utils.Ft's simple clamp
discards entirely, and that produces artificial jump discontinuities
(not just kinks) at each isotope's R=S threshold, since the Farley
formula's own value AT R=S (0.3125) is reached in one step from the
clamped 0 just below it.

This is fixed here (not in the shared thermochr_utils.Ft, which stays
fast and closed-form for its real use -- recoil-correcting real dated
grains, always R>>S so R<S never arises) with a Monte Carlo estimate of
the exact retention geometry, valid continuously for ALL R/S, not just
R>=S. Scale invariance (Ft depends only on the ratio rho=R/S, not R and
S separately) means this only needs computing once, as a single
universal curve Ft(rho), reused for each isotope via rho_i = R/S_i, and
reused again for the age plot below so it isn't recomputed twice.

Second plot -- helium age vs. inclusion size: assumes all the U-Th-Sm
sits in inclusions sourced/crystallized at AGE_INCLUSION_MYR (2.7 Ga)
ago, but that the inclusion phase (apatite) itself only started
retaining its own self-implanted helium at its cooling age,
COOLING_AGE_MYR (380 Ma) -- before that it was too hot to retain
anything, so any helium produced and staying within the apatite (the Ft
fraction) before 380 Ma was lost. The surrounding sulfide, by contrast,
is assumed to retain every alpha ejected into it (the 1-Ft fraction) for
the ENTIRE 2.7 Gyr history, consistent with this chapter's central
finding that sulfides are exceptionally He-retentive. So at R->0
(Ft->0, virtually everything ejected into the always-retentive sulfide)
the bulk age approaches the full 2.7 Ga source age; at R->infinity
(Ft->1, virtually everything self-implanted, retained only since 380 Ma)
it approaches the apatite's own 380 Ma cooling age.

The mixture is done in HELIUM, not age: total retained He(R) =
Ft(R)*He_forward(...,380 Myr) + (1-Ft(R))*He_forward(...,2700 Myr), then
inverted back to an age via He_forward's own accumulation curve. It is
NOT valid to linearly interpolate age itself between 380 Ma and 2.7 Ga
weighted by Ft, because He_forward(t) (thermochr_utils.He_forward, the
standard U-Th-Sm/He ingrowth equation) is only close to proportional to
t for t below ~500 Myr -- by 2.7 Ga the accumulation rate has climbed
~28% above its t->0 value (radiogenic ingrowth outpaces the still-modest
depletion of parent U/Th/Sm over that time), so the same He-domain
mixture implies a different (generally younger) age than a naive
age-domain mixture would. Inverted via scipy.optimize.brentq (bracketing
root-finder) rather than thermochr_utils.He_Age's home-brewed bisection-
style iterative_solver -- He_forward(t) is smooth and strictly
increasing in t, exactly what a bracketing method wants, and brentq is
both faster and has a firm convergence guarantee.

Reads: data/alpha_stopping_distances.csv
Outputs:
  generated/Fraction_Sulfide_Hosted_He_vs_Apatite_Inclusion_Size.pdf
  generated/He_Age_vs_Apatite_Inclusion_Size.pdf
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.optimize

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from thermochr_utils import He_forward, isotope_fraction
from plot_style import apply_style
apply_style()

DATA_CSV = os.path.join(SCRIPT_DIR, 'data', 'alpha_stopping_distances.csv')
OUTDIR = os.path.join(SCRIPT_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

INCLUSION_PHASE = 'Ca5(PO4)3F'  # fluorapatite, the standard accessory-phase end-member
ISOTOPES = ['238U', '235U', '232Th', '147Sm']

# U:Th:Sm = 1:2:2 (arbitrary consistent units -- Ft and the age inversion
# both only depend on the ratios between these, not their absolute scale:
# He_forward is linear in U/Th/Sm for fixed t, so the implied age is scale
# invariant).
U, TH, SM = 1.0, 2.0, 2.0

R_MAX_UM = 150.0  # apatite half-prism widths up to 150 um
REFERENCE_R_UM = 20.0  # the "~20 um" rule of thumb this pair of plots is built around

MC_N_SAMPLES = 1_000_000
MC_RHO_GRID = np.logspace(-2, np.log10(30), 400)  # covers rho = R/S from 0.01 to 30
MC_SEED = 0

AGE_INCLUSION_MYR = 2700.0  # inclusion source/crystallization age (Ma)
COOLING_AGE_MYR = 380.0     # apatite's own He-retention (cooling) age (Ma)

# Range of accepted Kidd Creek pyrite U-Th/He dates (KiddCreek_Age_vs_Th*
# in fig_geochronology_ages.py), shown as a reference band for comparison
# against this model's predicted apparent age.
PYRITE_AGE_MIN_MYR = 465.0
PYRITE_AGE_MAX_MYR = 860.0


def _sample_unit_ball(n, rng):
    """n decay positions, uniform BY VOLUME within the unit ball (U/Th/Sm
    assumed homogeneously distributed through the inclusion)."""
    direction = rng.normal(size=(n, 3))
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    radius = rng.uniform(size=n) ** (1 / 3)  # not uniform in r -- r=U^(1/3) gives uniform-in-volume
    return direction * radius[:, None]


def _sample_directions(n, rng):
    """n isotropic unit vectors (alpha ejection directions)."""
    direction = rng.normal(size=(n, 3))
    return direction / np.linalg.norm(direction, axis=1, keepdims=True)


def monte_carlo_Ft_curve(rho_grid, n_samples=MC_N_SAMPLES, seed=MC_SEED):
    """Monte Carlo Ft(rho) for rho = R/S, valid for every rho > 0 (unlike
    Farley's closed form, which only holds for rho >= 1). Fixes R=1 and
    varies S=1/rho instead of the other way around, sampling decay
    positions/directions ONCE and reusing them across the whole rho grid
    (common random numbers) so the resulting curve is smooth despite
    finite N, rather than each rho carrying independent MC noise."""
    rng = np.random.default_rng(seed)
    pos = _sample_unit_ball(n_samples, rng)
    direction = _sample_directions(n_samples, rng)

    ft = np.empty_like(rho_grid)
    for i, rho in enumerate(rho_grid):
        stop = pos + (1.0 / rho) * direction
        ft[i] = np.mean(np.sum(stop ** 2, axis=1) <= 1.0)
    return ft


def Ft_via_mc(R, S, X, rho_grid, ft_curve):
    """Isotope-weighted Ft(R), built from the precomputed universal MC
    curve (rho_i = R/S_i per isotope, weighted the same way as
    thermochr_utils.Ft)."""
    R = np.asarray(R, dtype=float)
    sm147_fraction = isotope_fraction('Sm', 147)
    alpha_weights = np.array([8 * X[0], 7 * X[0] / 137.88, 6 * X[1], sm147_fraction * X[2]])
    weights = alpha_weights / alpha_weights.sum()

    ft_per_isotope = np.empty((len(R), len(S)))
    for j, Sj in enumerate(S):
        rho = R / Sj
        ft_per_isotope[:, j] = np.interp(rho, rho_grid, ft_curve, left=0.0)
    return ft_per_isotope @ weights


def solve_He_age_years(U_mol, Th_mol, Sm_mol, target_He, t_bounds_yr=(1.0, 5e9)):
    """Invert He_forward for age t (years) given a target He amount, via
    Brent's method -- see module docstring for why this replaces
    thermochr_utils.He_Age's iterative_solver. He_forward(0)=0 and is
    strictly increasing, so target_He<=0 trivially maps to t=0 and any
    positive target has a unique bracketed root in t_bounds_yr (5 Ga
    comfortably exceeds the oldest age used here, 2.7 Ga)."""
    if target_He <= 0:
        return 0.0
    resid = lambda t: He_forward(U_mol, Th_mol, Sm_mol, t) - target_He
    return scipy.optimize.brentq(resid, *t_bounds_yr, xtol=1.0, rtol=1e-12)


def plot_sulfide_fraction(R, sulfide_fraction):
    fig, ax = plt.subplots()
    ax.plot(R, sulfide_fraction, color='tab:red', linewidth=2)
    ax.axvline(REFERENCE_R_UM, color='black', linestyle='--', linewidth=1.2,
               label=f'{REFERENCE_R_UM:.0f} µm reference')
    ax.set_xlim(0, R_MAX_UM)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel('Apatite Inclusion Half-Prism Radius (µm)')
    ax.set_ylabel(r'Fraction of Sulfide-Hosted He, $1 - F_t$')
    ax.set_title('Sulfide- vs. Inclusion-Hosted Helium\n'
                  f'(fluorapatite inclusions, U:Th:Sm = 1:{TH/U:.0f}:{SM/U:.0f})')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    outpath = os.path.join(OUTDIR, 'Fraction_Sulfide_Hosted_He_vs_Apatite_Inclusion_Size.pdf')
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"At R={REFERENCE_R_UM:.0f} um: 1-Ft = {np.interp(REFERENCE_R_UM, R, sulfide_fraction):.3f}")
    print(f"Wrote {outpath}")


def plot_helium_age(R, ft):
    He_young = He_forward(U, TH, SM, COOLING_AGE_MYR * 1e6)   # apatite-retained: only since cooling age
    He_old = He_forward(U, TH, SM, AGE_INCLUSION_MYR * 1e6)   # sulfide-retained: since source age
    total_He = ft * He_young + (1 - ft) * He_old

    ages_Ma = np.array([solve_He_age_years(U, TH, SM, he) for he in total_He]) / 1e6

    # Demonstrate the "not proportional" claim: a naive age-domain (rather
    # than He-domain) mixture gives a visibly different, generally older,
    # curve at intermediate R.
    naive_ages_Ma = ft * COOLING_AGE_MYR + (1 - ft) * AGE_INCLUSION_MYR
    mid = len(R) // 2
    print(f"At R={R[mid]:.0f} um: full-treatment age = {ages_Ma[mid]:.1f} Ma, "
          f"naive linear-mixing age = {naive_ages_Ma[mid]:.1f} Ma "
          f"(difference = {naive_ages_Ma[mid] - ages_Ma[mid]:.1f} Ma)")

    fig, ax = plt.subplots()
    ax.plot(R, ages_Ma, color='tab:blue', linewidth=2)
    #ax.plot(R, naive_ages_Ma, color='tab:blue', linewidth=1.2, linestyle=':', alpha=0.6)
    ax.axhline(AGE_INCLUSION_MYR, color='gray', linestyle='-.', linewidth=1)
    ax.axhline(COOLING_AGE_MYR, color='gray', linestyle='-.', linewidth=1)
    ax.axhspan(PYRITE_AGE_MIN_MYR, PYRITE_AGE_MAX_MYR, color='tab:orange', alpha=0.15, zorder=0)
    ax.set_xlim(0, R_MAX_UM)
    ax.set_xlabel('Apatite Inclusion Half-Prism Radius (µm)')
    ax.set_ylabel('Apparent Bulk He Age (Ma)')
    ax.set_title('Inclusion Size Age Affect For Kidd Creek Pyrite')
    ax.grid(alpha=0.3)

    # Everything labeled directly on the plot instead of via a legend --
    # the two reference lines with a white background box (so they stay
    # legible regardless of where the age curves sit relative to them,
    # same technique as the Gympie reference lines in
    # fig_geochronology_ages.py), and the two curves with text placed
    # right next to each one where they're already well separated.
    # Placed in the corners the age curves never reach (top-right stays
    # well below 2700 Ma; bottom-left stays well above 380 Ma), rather
    # than right where each line starts (which the curves hug closely).
    trans = ax.get_yaxis_transform()
    label_box = dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5)
    ax.text(0.97, AGE_INCLUSION_MYR, f'Inclusion crystallization age ({AGE_INCLUSION_MYR:.0f} Ma)',
            transform=trans, ha='right', va='center', fontsize=8, bbox=label_box)
    ax.text(0.03, COOLING_AGE_MYR, f'Apatite cooling age ({COOLING_AGE_MYR:.0f} Ma)',
            transform=trans, ha='left', va='center', fontsize=8, bbox=label_box)
    # Placed in the band's left portion, where the age curve is still
    # entirely above it (crosses in at R~90 um, never gets back down to
    # the band's own lower edge within the plotted R range) -- no need
    # for a white box there since the curve never crosses through it.
    ax.text(0.35, (PYRITE_AGE_MIN_MYR + PYRITE_AGE_MAX_MYR) / 2, 'Pyrite U-Th/He age',
            transform=trans, ha='center', va='center', fontsize=8, color='tab:orange')

    label_R = 0.72 * R_MAX_UM
    """ax.annotate('Full treatment\n(He-domain mixing)', xy=(label_R, np.interp(label_R, R, ages_Ma)),
                xytext=(0, 14), textcoords='offset points', ha='center', fontsize=8, color='tab:blue')
    ax.annotate('Naive linear\nage mixing\n(incorrect)', xy=(label_R, np.interp(label_R, R, naive_ages_Ma)),
                xytext=(0, -30), textcoords='offset points', ha='center', fontsize=8, color='tab:blue', alpha=0.7)"""
    fig.tight_layout()
    outpath = os.path.join(OUTDIR, 'He_Age_vs_Apatite_Inclusion_Size.pdf')
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"At R={REFERENCE_R_UM:.0f} um: age = {np.interp(REFERENCE_R_UM, R, ages_Ma):.1f} Ma")
    print(f"Wrote {outpath}")


def main():
    stopping = pd.read_csv(DATA_CSV, index_col=0)
    S = stopping.loc[INCLUSION_PHASE, ISOTOPES].to_numpy(dtype=float)

    print("Running Monte Carlo alpha-ejection simulation "
          f"({MC_N_SAMPLES:,} decays x {len(MC_RHO_GRID)} rho values)...")
    ft_curve = monte_carlo_Ft_curve(MC_RHO_GRID)

    # Validate against Farley (1996)'s closed form where it's valid (rho>=1)
    # and against the analytical exact-zero boundary (rho<=0.5).
    valid = MC_RHO_GRID >= 1.0
    farley = 1 - 0.75 / MC_RHO_GRID[valid] + (1 / 16) / MC_RHO_GRID[valid] ** 3
    max_dev = np.max(np.abs(ft_curve[valid] - farley))
    print(f"  MC vs. Farley closed form (rho>=1): max abs deviation = {max_dev:.4f}")
    below_half = MC_RHO_GRID <= 0.5
    print(f"  MC Ft for rho<=0.5 (should be ~0): max = {ft_curve[below_half].max():.4f}")

    R = np.linspace(0.5, R_MAX_UM, 1000)
    ft = Ft_via_mc(R, S, [U, TH, SM], MC_RHO_GRID, ft_curve)

    plot_sulfide_fraction(R, 1 - ft)
    plot_helium_age(R, ft)


if __name__ == '__main__':
    main()
