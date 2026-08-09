"""
Alpha-ejection loss from a FRACTURED pyrite host: Monte Carlo Ft for a
fracture-bounded block, and the apparent U-Th/He age it implies for the
Rustenburg (Bushveld) pyrite suite.

WHY THIS FIGURE EXISTS
----------------------
The Rustenburg pyrite aliquots in Tables/geochronology_compilation_BJT.xlsx
retain only ~30% of the radiogenic 4He they should have accumulated since
the 2054 Ma emplacement of the Rustenburg Layered Suite, and that retention
is roughly CONSTANT (0.20-0.56) across a ~50x spread in eU. Two things rule
out the obvious explanations:

  * It is not thermal. Using this chapter's own Rustenburg step-heat
    kinetics (Ea = 300.6 kJ/mol, Tc = 323 degC -- and that regression is
    fit to the FAST short-circuit retrograde array, so it is an upper
    bound on loss), 70% loss over 2054 Ma requires holding the sample at
    ~267 degC continuously. RLS plagioclase 40Ar/39Ar plateaus
    (1998-2051 Ma, Tc 151-310 degC) put it through that window by ~2.0 Ga,
    and Kaapvaal craton-interior AFT ages (331-379 Ma, <60 degC since
    300 Ma) leave no later reheating. At 60 degC the predicted loss is ~0%.

  * It is not a parent-loss / digestion artifact. Incomplete digestion
    makes ages too OLD (and does, for two aliquots -- see the Zr
    diagnostic in the Results section), not too young.

What is left is a PRODUCTION-SIDE, temperature-independent loss: the
Rustenburg pyrite is pervasively cut by micron-scale fractures
(fig:ch3-rustenburg-control-fractures), and the alpha stopping distance in
pyrite is only ~13 um. If the fracture spacing is comparable to the
stopping distance, a large and essentially fixed fraction of every alpha
produced anywhere in the grain terminates in (or immediately adjacent to)
a fracture rather than in intact sulfide. That is a geometric property of
the fracture network, NOT of the U-Th budget -- which is exactly why the
retention clusters while eU does not.

This is the same alpha-ejection retention framework as
fig_alpha_stopping_distances.py (Farley et al. 1996), with the spherical
inclusion swapped for a fracture-bounded block of intact pyrite.

MODEL
-----
Decay sites are uniform BY VOLUME within a block of intact pyrite of
characteristic dimension L, bounded by fractures. Alphas are emitted
isotropically and travel a fixed, per-isotope stopping distance S_i
(238U/235U/232Th/147Sm), weighted by the alpha yield of each chain and
the aliquot's own U:Th:Sm ratio. Three block geometries x two fracture
treatments are computed:

  Geometry
    'slab'  -- one fracture set: parallel planes, spacing L (loss through
               2 faces). Least efficient geometry for a given L.
    'cube'  -- three orthogonal fracture sets: cubic blocks of edge L
               (loss through 6 faces). The realistic end-member for a
               pervasively fractured grain.

  Fracture treatment
    absorbing    -- any alpha crossing a fracture wall is lost. This is
                    the hard geometric UPPER BOUND on ejection loss, and
                    is the right model if the fracture is wide compared
                    to the stopping distance, or if the alpha is stopped
                    by fracture-filling material.
    transmissive -- fractures are thin open/fluid-filled gaps of aperture
                    w. An alpha crossing a gap loses only
                    w * (rho_fill / rho_pyrite) of its range, so for
                    w ~ 1 um it crosses almost freely and can be RETAINED
                    in the next block along. Only alphas that come to rest
                    INSIDE a gap are lost.

The transmissive case matters, and it is the honest one to show: it is
the physical reason this mechanism is not a free lunch. With 1 um
apertures, direct ejection into voids alone struggles to reach 70% loss
unless blocks are very small, which is a falsifiable statement about
fracture spacing that can be tested directly against the existing SEM
image (BVPY_control_2um2).

VALIDATION
----------
The 'slab' + absorbing case has a closed form, derived by integrating the
isotropic escape probability over depth z in a slab of thickness L with
single stopping distance S:
      Ft = 1 - S/(2L)          for L >= 2S
      Ft = L/(2S)              for L <= S
(and a smooth interpolation between). Note the L >= 2S branch is exactly
Farley et al. (1996)'s general surface-area result Ft ~ 1 - (1/4)*S*(A/V)
with A/V = 2/L for a slab -- a slab has no curvature, so there is no
higher-order term, unlike the sphere's cubic. The MC is checked against
this analytically at runtime (see _validate_slab).

PYRITE STOPPING DISTANCES ARE DERIVED, NOT TABULATED
----------------------------------------------------
Ketcham et al. (2011) does not tabulate FeS2, and
data/alpha_stopping_distances.csv accordingly has no pyrite row. Rather
than hand-wave a density scaling (stopping distance is NOT simply
proportional to 1/rho -- barite is denser than apatite yet stops alphas
over a comparable distance, because heavy elements are poor stoppers per
unit mass), this script calibrates the MASS range R*rho against the
formula's mean mass-per-electron A/Z across all ten tabulated phases,
which is the leading-order composition dependence of electronic stopping
power, and interpolates FeS2 onto that fit. The regression quality and
the resulting pyrite stopping distances are printed at runtime, and the
fit residual is propagated into a shaded uncertainty on the curves.
This is an approximation -- a SRIM/TRIM calculation for FeS2 would be
better and is worth doing before publication.

Outputs -> generated/:
    Fractured_Pyrite_Alpha_Loss.pdf
        (a) Ft vs block size L for both geometries and both fracture
            treatments, with the observed Rustenburg retention band and
            individual aliquots overlaid.
        (b) apparent U-Th/He age vs L for a true age of 2054 Ma, with the
            observed Rustenburg ages overlaid, so the block size each
            aliquot's age implies can be read off directly.
"""
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import openpyxl
from matplotlib.lines import Line2D
from molmass import ELEMENTS, Formula

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from plot_style import apply_style  # noqa: E402
from thermochr_utils import He_forward, isotope_fraction  # noqa: E402

# Two-panel, built wide and placed at ~0.95\textwidth -- the same
# treatment as fig_geochronology_ages.py's two-panel KiddCreek figure,
# which uses a plain apply_style() at figsize=(9, 5). The net shrink to
# the printed page is close enough to the 6.4in -> 8.3cm baseline that no
# scale= correction is wanted here; passing scale=W/6.4 (appropriate only
# for a wide figure still placed at 8.3 cm) makes the text enormous.
apply_style()
FIGSIZE = (11, 4.8)

XLSX_PATH = os.path.join(SCRIPT_DIR, '..', 'Tables', 'geochronology_compilation_BJT.xlsx')
STOPPING_CSV = os.path.join(SCRIPT_DIR, 'data', 'alpha_stopping_distances.csv')
OUTDIR = os.path.join(SCRIPT_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

ISOTOPES = ['238U', '235U', '232Th', '147Sm']

# Densities (g/cm3) for the phases tabulated in alpha_stopping_distances.csv,
# plus pyrite. Used only to convert tabulated ranges (um) into mass ranges
# (ug/cm2) for the A/Z calibration described in the module docstring.
DENSITY = {
    'Ca5(PO4)3F': 3.19,   # fluorapatite
    'ZrSiO4': 4.65,       # zircon
    'CaTiSiO5': 3.48,     # titanite
    'CePO4': 5.22,        # monazite (synthetic CePO4)
    'YPO4': 4.55,         # xenotime
    'TiO2': 4.25,         # rutile
    'Fe3O4': 5.15,        # magnetite
    'Fe2O3': 5.26,        # hematite
    'FeOOH': 4.27,        # goethite
    'BaSO4': 4.48,        # barite
}
PYRITE = 'FeS2'
PYRITE_DENSITY = 5.01

# --- Rustenburg / Bushveld geologic constants -------------------------------
RLS_AGE_MYR = 2054.0   # Rustenburg Layered Suite emplacement (U-Pb zircon,
                       # 2055.4 +/- 0.4 Upper Zone; 2059-2060 Upper Critical
                       # Zone). The true age the pyrite's inclusions should
                       # be recording.

# The 1.2523x / 1.2584x correction below: the workbook's ppm columns are
# derived from the (primary) mole columns using molar masses of 298 and 292
# for U and Th instead of 238.05 and 232.04. The mole columns and the age
# column are correct (they reproduce Durango's accepted 32.1 Ma); the ppm
# columns are ~25% high. Concentrations are therefore read from the MOLE
# columns here rather than the ppm columns. Delete this once the workbook
# formulae are fixed.
DATA_SHEET = 'Data'
RUSTENBURG_ROWS = range(68, 76)   # 8 aliquots under the 'Rustenberg' header

MC_N_SAMPLES = 400_000
L_GRID_UM = np.logspace(np.log10(0.5), np.log10(500.0), 160)
MC_SEED = 0

# The transmissive case has to trace each alpha through the solid/gap
# lattice rather than doing a single endpoint test, so it is run at lower
# sample count on a coarser L grid and interpolated onto L_GRID_UM. Its
# curve is smooth (common random numbers across L), so this costs very
# little accuracy; the absorbing cases keep the full grid and sample count.
TRANSMISSIVE_N_SAMPLES = 30_000
TRANSMISSIVE_L_GRID_UM = np.logspace(np.log10(0.5), np.log10(500.0), 40)
TRANSMISSIVE_STEPS = 220
TRANSMISSIVE_CHUNK = 4_000

# TODO(measure): fracture spacing read directly off the Rustenburg control
# SEM image (source/BVPY_control_2um2). Set to an (lo, hi) tuple in um and
# both panels will shade it, turning this figure into a direct test of the
# mechanism rather than an inference. Left None until actually measured --
# do not guess this number, it is the whole falsifiable content of the model.
SEM_SPACING_UM = None

APERTURE_UM = 1.0        # fracture aperture for the transmissive case,
                         # from the micron-scale widths visible in
                         # BVPY_control_2um2 (fig:ch3-rustenburg-control-fractures)
FILL_DENSITY = 1.0       # g/cm3, aqueous fluid filling the fractures


# ---------------------------------------------------------------------------
# Stopping distances in pyrite
# ---------------------------------------------------------------------------

def _composition_items(formula):
    """(symbol, count) pairs for a formula, tolerant of molmass version
    differences: Formula.composition() iterates as CompositionItem objects
    in some versions and as bare symbol strings (keyed lookup) in others."""
    comp = Formula(formula).composition()
    items = []
    for entry in comp:
        if isinstance(entry, str):
            item = comp[entry]
            items.append((item.symbol, item.count))
        elif hasattr(entry, 'symbol'):
            items.append((entry.symbol, entry.count))
        else:
            items.append((entry[0], entry[1]))
    return items


def _atomic_number(symbol):
    return ELEMENTS[symbol].number


def _mass_per_electron(formula):
    """A/Z for a formula unit: total molar mass / total atomic number.

    This is the leading-order composition dependence of electronic
    stopping power -- stopping is per-electron, so a formula with more
    mass per electron (i.e. heavier, more neutron-rich constituents) is
    a poorer stopper per unit mass and gives a longer MASS range. It is
    why barite (rho 4.48) stops alphas over almost the same distance as
    the much lighter apatite (rho 3.19), and why a naive 1/rho scaling
    of tabulated stopping distances is not good enough here.
    """
    total_Z = sum(_atomic_number(sym) * count
                  for sym, count in _composition_items(formula))
    return Formula(formula).mass / total_Z


def load_stopping_csv():
    import csv
    rows = {}
    with open(STOPPING_CSV, encoding='utf-8-sig') as fh:
        reader = csv.reader(fh)
        header = next(reader)
        cols = header[1:]
        assert cols == ISOTOPES, f'unexpected stopping-distance columns: {cols}'
        for row in reader:
            if not row or not row[0]:
                continue
            rows[row[0]] = np.array([float(x) for x in row[1:]])
    return rows


def pyrite_stopping_distances(verbose=True):
    """Predict FeS2 alpha stopping distances (um) per isotope.

    Calibrates mass range (R * rho, ug/cm2) against A/Z across the ten
    tabulated phases, then evaluates at FeS2's A/Z and divides by pyrite
    density. Returns (S_um[4], S_um_1sigma[4]).
    """
    table = load_stopping_csv()
    phases = [p for p in table if p in DENSITY]
    az = np.array([_mass_per_electron(p) for p in phases])
    az_pyrite = _mass_per_electron(PYRITE)

    S = np.empty(4)
    S_err = np.empty(4)
    if verbose:
        print(f'Pyrite ({PYRITE}, rho={PYRITE_DENSITY} g/cm3) alpha stopping '
              f'distances, calibrated on A/Z across {len(phases)} phases:')
        print(f'   A/Z(FeS2) = {az_pyrite:.4f}   '
              f'(calibration range {az.min():.3f}-{az.max():.3f})')
    for j, iso in enumerate(ISOTOPES):
        # mass range in ug/cm2 = um * (g/cm3) * 100
        mass_range = np.array([table[p][j] * DENSITY[p] * 100 for p in phases])
        slope, intercept = np.polyfit(az, mass_range, 1)
        pred = slope * az + intercept
        resid = mass_range - pred
        r2 = 1 - np.sum(resid ** 2) / np.sum((mass_range - mass_range.mean()) ** 2)
        mr_pyrite = slope * az_pyrite + intercept
        sd = np.std(resid, ddof=2)
        S[j] = mr_pyrite / (PYRITE_DENSITY * 100)
        S_err[j] = sd / (PYRITE_DENSITY * 100)
        if verbose:
            print(f'   {iso:>6s}: {S[j]:5.2f} +/- {S_err[j]:.2f} um   '
                  f'(A/Z fit R2 = {r2:.3f})')
    return S, S_err


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

def _sample_unit_cube(n, rng, ndim):
    """Decay positions uniform by volume in the unit block. `ndim` is the
    number of directions bounded by fractures: 1 -> slab (only x bounded),
    3 -> cube. Unbounded axes are irrelevant to the retention test and are
    simply not checked."""
    return rng.uniform(size=(n, ndim))


def _sample_directions(n, rng):
    d = rng.normal(size=(n, 3))
    return d / np.linalg.norm(d, axis=1, keepdims=True)


def mc_retention_curve(L_grid, S, ndim, aperture_um=None,
                       n_samples=MC_N_SAMPLES, seed=MC_SEED):
    """Fraction of alphas of stopping distance S (um, scalar) retained in
    intact pyrite, as a function of block size L (um).

    ndim=1 -> parallel-plane fracture set (slab); ndim=3 -> three
    orthogonal sets (cubic blocks).

    aperture_um=None  -> absorbing fractures: any wall crossing is loss.
    aperture_um=w     -> transmissive fractures: the medium is a periodic
                         lattice of solid blocks of size L separated by
                         gaps of width w. The alpha's path is traced
                         through the lattice, spending range at a rate
                         reduced by FILL_DENSITY/PYRITE_DENSITY while
                         inside a gap; it is lost only if it comes to rest
                         inside a gap.

    Uses common random numbers across the L grid so the curve is smooth.
    """
    if aperture_um is not None:
        n_samples = min(n_samples, TRANSMISSIVE_N_SAMPLES)
    rng = np.random.default_rng(seed)
    pos = _sample_unit_cube(n_samples, rng, ndim)
    direction = _sample_directions(n_samples, rng)[:, :ndim]

    out = np.empty_like(L_grid)
    for i, L in enumerate(L_grid):
        if aperture_um is None:
            # positions in um within the block, displaced by S
            stop = pos * L + S * direction
            inside = np.all((stop >= 0.0) & (stop <= L), axis=1)
            out[i] = inside.mean()
        else:
            out[i] = _transmissive_retention(pos, direction, L, S, aperture_um)
    return out


def _transmissive_retention(pos, direction, L, S, w,
                            n_steps=TRANSMISSIVE_STEPS,
                            chunk=TRANSMISSIVE_CHUNK):
    """Retention for a periodic solid/gap lattice, integrated along the ray.

    Traces each alpha along its direction, accumulating 'range consumed'
    at 1.0 per um inside pyrite and at FILL_DENSITY/PYRITE_DENSITY per um
    inside a fracture gap, and reports whether the point at which the
    accumulated range first reaches S lies in solid (retained) or in a gap
    (lost). An alpha can therefore cross a thin gap and be retained in the
    next block along -- which is the whole point of this end-member.

    Vectorised over BOTH alphas and steps (chunked to bound memory); the
    per-step loop this replaces was ~3 orders of magnitude too slow to
    sweep the L grid.
    """
    period = L + w
    slow = FILL_DENSITY / PYRITE_DENSITY   # range consumed per um inside a gap
    # Physical path length can exceed S where part of it lies in low-density
    # fill; S/slow is the worst case (entire path in fill) and so always
    # long enough to reach consumed range S.
    max_path = S / slow
    ds = max_path / n_steps
    t = (np.arange(n_steps) + 0.5) * ds        # (n_steps,)

    retained = np.empty(len(pos), dtype=bool)
    for lo in range(0, len(pos), chunk):
        hi = min(lo + chunk, len(pos))
        start = pos[lo:hi] * L                              # (n, ndim)
        # (n, n_steps, ndim) positions along each ray
        p = start[:, None, :] + t[None, :, None] * direction[lo:hi][:, None, :]
        in_solid = np.all(np.mod(p, period) <= L, axis=2)   # (n, n_steps)
        consumed = np.cumsum(np.where(in_solid, 1.0, slow) * ds, axis=1)
        reached = consumed >= S
        # first step at which range S is consumed
        idx = np.argmax(reached, axis=1)
        ever = reached[:, -1]
        r = in_solid[np.arange(hi - lo), idx]
        # an alpha that never accumulates S (shouldn't happen given max_path)
        # is counted as retained rather than silently lost
        retained[lo:hi] = np.where(ever, r, True)
    return retained.mean()


def _validate_slab(S, tol=0.01):
    """Check the MC 'slab + absorbing' case against the closed form."""
    L = np.array([0.25, 0.5, 0.9, 1.0, 1.5, 2.0, 3.0, 6.0, 20.0]) * S
    mc = mc_retention_curve(L, S, ndim=1, n_samples=400_000, seed=1)
    analytic = np.where(L >= 2 * S, 1 - S / (2 * L),
                        np.where(L <= S, L / (2 * S), np.nan))
    ok = ~np.isnan(analytic)
    err = np.abs(mc[ok] - analytic[ok])
    print('Slab MC vs closed form  Ft = 1 - S/(2L) [L>=2S] / L/(2S) [L<=S]:')
    for Li, m, a in zip(L[ok], mc[ok], analytic[ok]):
        print(f'   L/S = {Li / S:5.2f}   MC {m:.4f}   analytic {a:.4f}')
    assert err.max() < tol, f'slab MC disagrees with closed form by {err.max():.4f}'
    print(f'   max |MC - analytic| = {err.max():.4f}  OK\n')


def isotope_weighted_curve(L_grid, S_vec, X, ndim, aperture_um=None):
    """Alpha-yield- and composition-weighted Ft(L), weighting the four
    per-isotope curves exactly as thermochr_utils.Ft does.

    For the transmissive case the curve is computed on the coarser
    TRANSMISSIVE_L_GRID_UM and interpolated (in log L) onto L_grid.
    """
    U, Th, Sm = X
    alpha_weights = np.array([8 * U, 7 * U / 137.88, 6 * Th,
                              isotope_fraction('Sm', 147) * Sm])
    weights = alpha_weights / alpha_weights.sum()
    work_grid = L_grid if aperture_um is None else TRANSMISSIVE_L_GRID_UM
    curves = np.array([mc_retention_curve(work_grid, S, ndim, aperture_um)
                       for S in S_vec])
    ft = weights @ curves
    if aperture_um is None:
        return ft
    return np.interp(np.log(L_grid), np.log(work_grid), ft)


# ---------------------------------------------------------------------------
# Rustenburg data
# ---------------------------------------------------------------------------

def load_rustenburg():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb[DATA_SHEET]
    header = [c if c else '' for c in next(ws.iter_rows(min_row=1, max_row=1,
                                                        values_only=True))]
    col = {}
    for j, h in enumerate(header):
        if h and h not in col:
            col[h] = j

    out = []
    for r in RUSTENBURG_ROWS:
        row = list(ws.iter_rows(min_row=r, max_row=r, values_only=True))[0]

        def g(key, default=0.0):
            v = row[col[key]]
            return float(v) if isinstance(v, (int, float)) else default

        he_ncc = g('1Ra atm-corrected 4He (ncc)')
        rec = dict(
            name=str(row[0]).strip(),
            mass_mg=g('mass (mg)'),
            he_ncc=he_ncc,
            U_mol=g('U (moles)'), Th_mol=g('Th (moles)'), Sm_mol=g('Sm (moles)'),
            age=g('Age (Ma Atm=1Ra Corr.)'),
            age_2s=0.0,
            Zr_ppm=g('Zr (ppm)'),
        )
        rec['he_closed'] = He_forward(rec['U_mol'], rec['Th_mol'], rec['Sm_mol'],
                                      RLS_AGE_MYR * 1e6)
        rec['retention'] = rec['he_ncc'] / rec['he_closed'] if rec['he_closed'] else np.nan
        out.append(rec)
    return out


def apparent_age_from_Ft(ft_grid, U, Th, Sm, true_age_myr=RLS_AGE_MYR):
    """Apparent U-Th/He age for a grain that produced He for `true_age_myr`
    but retained only fraction ft of it (production-side loss, so the loss
    is instantaneous at production and does not accumulate with time)."""
    he_full = He_forward(U, Th, Sm, true_age_myr * 1e6)
    t_grid = np.logspace(0, np.log10(true_age_myr), 3000)
    he_grid = np.array([He_forward(U, Th, Sm, t * 1e6) for t in t_grid])
    return np.interp(ft_grid * he_full, he_grid, t_grid)


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def main():
    S_vec, S_err = pyrite_stopping_distances()
    print()
    _validate_slab(S_vec[0])

    data = load_rustenburg()
    kept = [d for d in data if 0 < d['retention'] < 1.0]
    excluded = [d for d in data if not (0 < d['retention'] < 1.0)]
    ret = np.array([d['retention'] for d in kept])
    print(f'Rustenburg aliquots with retention < 1 (n={len(kept)}): '
          f'mean {ret.mean():.2f} +/- {ret.std(ddof=1):.2f} (1sd), '
          f'range {ret.min():.2f}-{ret.max():.2f}')
    print('Excluded (retention > 1, i.e. impossible -- undigested Zr-U phase): '
          + ', '.join(f"{d['name']} ({d['retention']:.1f})" for d in excluded))
    print()

    # Composition weights: median U:Th:Sm RATIOS across the retained
    # aliquots. Note this is the median of each ratio, not the ratio of the
    # medians -- the latter is dominated by whichever aliquot happens to sit
    # mid-rank in each element separately and gave Th/U = 0.50 rather than
    # the correct 0.28 for this suite. Only the ratios matter: the alpha
    # weighting normalises them out of absolute scale.
    th_u = float(np.median([d['Th_mol'] / d['U_mol'] for d in kept]))
    sm_u = float(np.median([d['Sm_mol'] / d['U_mol'] for d in kept]))
    U, Th, Sm = 1.0, th_u, sm_u
    print(f'Weighting composition (median ratios across retained aliquots): '
          f'Th/U = {th_u:.2f}, Sm/U = {sm_u:.2f} (molar)')

    curves = {}
    print('\nrunning Monte Carlo ...')
    curves['slab_abs'] = isotope_weighted_curve(L_GRID_UM, S_vec, (U, Th, Sm),
                                                ndim=1, aperture_um=None)
    curves['cube_abs'] = isotope_weighted_curve(L_GRID_UM, S_vec, (U, Th, Sm),
                                                ndim=3, aperture_um=None)
    curves['cube_trans'] = isotope_weighted_curve(L_GRID_UM, S_vec, (U, Th, Sm),
                                                  ndim=3, aperture_um=APERTURE_UM)

    style = {
        'slab_abs': dict(color='#4C72B0', ls='--',
                         label='1 fracture set (slabs), absorbing'),
        'cube_abs': dict(color='#C44E52', ls='-',
                         label='3 fracture sets (cubes), absorbing'),
        'cube_trans': dict(color='#DD8452', ls='-.',
                           label=f'3 sets, transmissive ({APERTURE_UM:.0f} '
                                 r'$\mu$m aperture)'),
    }

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=FIGSIZE)

    # ---- panel (a): Ft vs block size -------------------------------------
    for key, c in curves.items():
        ax.plot(L_GRID_UM, c, lw=2, **style[key])

    ret_lo, ret_hi = ret.mean() - ret.std(ddof=1), ret.mean() + ret.std(ddof=1)
    ax.axhspan(ret_lo, ret_hi, color='0.6', alpha=0.30, zorder=0)
    ax.axhline(ret.mean(), color='0.35', lw=1.1, zorder=1)
    for d in kept:
        ax.plot(L_GRID_UM[0], d['retention'], marker='<', ms=5, color='k',
                clip_on=False, zorder=5)
    ax.text(0.03, 0.97,
            f'Rustenburg observed\n$F_T$ = {ret.mean():.2f} $\\pm$ '
            f'{ret.std(ddof=1):.2f} (1sd, n={len(kept)})',
            transform=ax.transAxes, ha='left', va='top',
            fontsize=9.5, color='0.2')

    # where each curve crosses the observed mean retention, staggered
    # vertically so the callouts don't collide with each other or the legend
    for (key, c), y_lab in zip(curves.items(), (0.52, 0.64, 0.76)):
        if not (c.min() <= ret.mean() <= c.max()):
            continue
        L_cross = float(np.interp(ret.mean(), c, L_GRID_UM))
        ax.plot([L_cross], [ret.mean()], marker='o', ms=6,
                mfc='w', mec=style[key]['color'], mew=1.8, zorder=6)
        fmt = f'{L_cross:.1f}' if L_cross < 10 else f'{L_cross:.0f}'
        ax.annotate(f'$L$ = {fmt} ' + r'$\mu$m',
                    xy=(L_cross, ret.mean()), xytext=(L_cross, y_lab),
                    ha='center', fontsize=9.5, color=style[key]['color'],
                    arrowprops=dict(arrowstyle='-', color=style[key]['color'],
                                    lw=0.9, ls=':'))

    # L below the fracture aperture is not a physical configuration -- the
    # "blocks" would be thinner than the gaps between them. Hatch it out so
    # the transmissive curve's crossing there is not read as a real answer.
    ax.axvspan(L_GRID_UM[0], APERTURE_UM, color='0.5', alpha=0.13, zorder=0)
    ax.text(APERTURE_UM * 0.92, 0.015, r'$L<$ aperture', rotation=90,
            ha='right', va='bottom', fontsize=8, color='0.35')

    if SEM_SPACING_UM is not None:
        ax.axvspan(*SEM_SPACING_UM, color='#55A868', alpha=0.18, zorder=0)

    ax.set_xscale('log')
    ax.set_xlim(L_GRID_UM[0], L_GRID_UM[-1])
    ax.set_ylim(0, 1.02)
    ax.set_xlabel(r'fracture-bounded block size $L$ ($\mu$m)')
    ax.set_ylabel(r'$F_T$ ($\alpha$ retained in intact pyrite)')
    ax.set_title(r'(a) fracture-controlled $\alpha$ retention')
    ax.legend(loc='lower right', fontsize=8.5, framealpha=0.95)
    ax.grid(alpha=0.25)

    # ---- panel (b): apparent age vs block size ---------------------------
    for key, c in curves.items():
        ax2.plot(L_GRID_UM, apparent_age_from_Ft(c, U, Th, Sm), lw=2, **style[key])

    obs_ages = np.array([d['age'] for d in kept])
    ax2.axhspan(obs_ages.min(), obs_ages.max(), color='0.6', alpha=0.30, zorder=0)
    ax2.axhline(RLS_AGE_MYR, color='k', lw=1.3, ls=':', zorder=1)
    ax2.text(0.97, RLS_AGE_MYR + 35, f'RLS emplacement, {RLS_AGE_MYR:.0f} Ma',
             transform=ax2.get_yaxis_transform(), ha='right', va='bottom',
             fontsize=9.5)
    for d in kept:
        ax2.plot(L_GRID_UM[0], d['age'], marker='<', ms=5, color='k',
                 clip_on=False, zorder=5)
    ax2.text(0.97, 0.44,
             f'Rustenburg apparent ages\n{obs_ages.min():.0f}'
             f'-{obs_ages.max():.0f} Ma (n={len(kept)})',
             transform=ax2.transAxes, ha='right', va='bottom',
             fontsize=9.5, color='0.2')

    ax2.axvspan(L_GRID_UM[0], APERTURE_UM, color='0.5', alpha=0.13, zorder=0)
    if SEM_SPACING_UM is not None:
        ax2.axvspan(*SEM_SPACING_UM, color='#55A868', alpha=0.18, zorder=0)

    ax2.set_xscale('log')
    ax2.set_xlim(L_GRID_UM[0], L_GRID_UM[-1])
    ax2.set_ylim(0, RLS_AGE_MYR * 1.18)
    ax2.set_xlabel(r'fracture-bounded block size $L$ ($\mu$m)')
    ax2.set_ylabel('apparent U-Th/He age (Ma)')
    ax2.set_title('(b) implied apparent age')
    ax2.grid(alpha=0.25)

    fig.tight_layout()
    out = os.path.join(OUTDIR, 'Fractured_Pyrite_Alpha_Loss.pdf')
    fig.savefig(out, bbox_inches='tight')
    fig.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f'\nwrote {out}')

    # ---- numbers for the caption / text ----------------------------------
    print('\nblock size implied by the observed retention band:')
    for key, c in curves.items():
        lo, mid, hi = [np.interp(v, c, L_GRID_UM) for v in
                       (ret.mean() - ret.std(ddof=1), ret.mean(),
                        ret.mean() + ret.std(ddof=1))]
        reach = c.max()
        note = '' if reach >= ret.mean() else '  (CANNOT reach observed Ft)'
        print(f"   {style[key]['label']:<52s} L = {mid:6.1f} um "
              f"({lo:.1f}-{hi:.1f}){note}")
    print(f"\n   transmissive-case maximum loss over the whole L grid: "
          f"{1 - curves['cube_trans'].min():.2f}")


if __name__ == '__main__':
    main()
