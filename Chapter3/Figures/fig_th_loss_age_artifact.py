"""
Apparent (U-Th)/He age inflation from post-accumulation Th loss, for a
Th-only phase (no U, no Sm) with a TRUE age of 400 Ma.

Physical scenario: a phase accumulates radiogenic He from Th decay alone
over 400 Myr, then at some point loses a fraction of its THORIUM (not
its already-accumulated helium) -- e.g. leaching, alteration, or simply
digesting/measuring a sub-sample of parent material that isn't fully
representative of what actually grew the He. The measured He is
unaffected (still the full 400-Myr accumulation), but the measured Th is
smaller than the Th that actually produced it, so computing an age from
the measured He/Th ratio the ordinary way (assuming continuous single-
stage accumulation, i.e. thermochr_utils.He_forward inverted for t)
overestimates the true age -- the same He divided by less Th looks like
it took longer to grow.

Th loss is expressed as a dimensionless factor L = (true Th) / (measured
Th), swept in logspace from 1 (no loss) to 15 (only 1/15 of the true Th
remains, i.e. ~93.3% lost). Age inversion uses scipy.optimize.brentq
(bracketing root-finder) rather than thermochr_utils.He_Age's home-brewed
iterative_solver, for the same reasons given in
fig_alpha_stopping_distances.py: He_forward(t) is smooth and strictly
increasing in t, exactly what a bracketing method wants.

Th's decay constant is tiny (half-life 14.05 Byr) relative to the ages
involved here, so He_forward(t) is close to but not exactly linear in t
over these timescales -- apparent age still comes out measurably below
a naive L*400 Ma prediction (e.g. ~5300 Ma vs. 6000 Ma at L=15, a ~12%
difference), a smaller deviation than the ~28% seen for the mixed
U-Th-Sm case in fig_alpha_stopping_distances.py (Th's much longer half-
life keeps it closer to the small-t linear regime for longer), but not
negligible.

Reads: nothing (self-contained; Th abundance is an arbitrary consistent
unit since only the loss ratio and true age matter -- He_forward is
linear in Th for fixed t, so the implied age is scale invariant, same
argument as fig_alpha_stopping_distances.py).
Output: generated/Th_Loss_Apparent_Age.pdf
"""
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from thermochr_utils import He_forward
from plot_style import apply_style
apply_style()

OUTDIR = os.path.join(SCRIPT_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

TRUE_AGE_MYR = 400.0
TH_TRUE = 1.0  # arbitrary consistent unit -- only the loss ratio matters
LOSS_FACTOR_MAX = 15.0
N_POINTS = 500


def solve_He_age_years(Th_mol, target_He, t_bounds_yr=(1.0, 1e10)):
    """Invert He_forward (Th-only: U=Sm=0) for age t (years) given a
    target He amount, via Brent's method. Upper bound (10 Ga) comfortably
    exceeds the ~5.3 Ga root reached at the maximum loss factor (15x)
    used in this script."""
    if target_He <= 0:
        return 0.0
    resid = lambda t: He_forward(0.0, Th_mol, 0.0, t) - target_He
    return scipy.optimize.brentq(resid, *t_bounds_yr, xtol=1.0, rtol=1e-12)


def _add_pct_lost_axis(ax1):
    """Secondary top axis: percent of Th lost (1 - 1/L) x 100, sharing
    the same log-spaced loss-factor x-position as the primary axis."""
    ax2 = ax1.twiny()
    ticks = np.array([1, 2, 3, 5, 7, 10, 15])
    ax2.set_xscale('log')
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f'{100*(1-1/t):.0f}%' for t in ticks])
    ax2.set_xlabel('Th Lost (%)')
    return ax2


def main():
    he_true = He_forward(0.0, TH_TRUE, 0.0, TRUE_AGE_MYR * 1e6)

    loss_factor = np.logspace(0, np.log10(LOSS_FACTOR_MAX), N_POINTS)
    apparent_age_Ma = np.array([
        solve_He_age_years(TH_TRUE / L, he_true) for L in loss_factor
    ]) / 1e6

    fig, ax1 = plt.subplots()
    ax1.plot(loss_factor, apparent_age_Ma, color='tab:purple', linewidth=2)
    ax1.axhline(TRUE_AGE_MYR, color='gray', linestyle='-.', linewidth=1)
    ax1.set_xscale('log')
    ax1.set_xlim(1, LOSS_FACTOR_MAX)
    ax1.set_xlabel('Th Loss Factor (True Th / Measured Th)')
    ax1.set_ylabel('Apparent He Age (Ma)')
    ax1.grid(alpha=0.3, which='both')
    _add_pct_lost_axis(ax1)
    ax1.set_title('Apparent Age Inflation from Post-Accumulation Th Loss\n'
                   f'(Th-only phase, true age = {TRUE_AGE_MYR:.0f} Ma)')

    trans = ax1.get_yaxis_transform()
    ax1.text(0.02, TRUE_AGE_MYR, f'True age ({TRUE_AGE_MYR:.0f} Ma)',
              transform=trans, ha='left', va='bottom', fontsize=9,
              bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5))

    fig.tight_layout()
    outpath = os.path.join(OUTDIR, 'Th_Loss_Apparent_Age.pdf')
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)

    for L in (1, 2, 5, 10, 15):
        idx = int(np.argmin(np.abs(loss_factor - L)))
        print(f"Loss factor {L:>4.0f}x ({100*(1-1/L):5.1f}% Th lost): "
              f"apparent age = {apparent_age_Ma[idx]:.0f} Ma")
    print(f"Wrote {outpath}")


if __name__ == '__main__':
    main()
