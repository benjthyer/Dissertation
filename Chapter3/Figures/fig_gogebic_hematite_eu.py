"""
Gogebic Iron Range BIF hematite standard (Farley & McKeon, 2015): 4He
(nccSTP/mg) vs. eU (ppm), normalized by the sample mass calculated from
measured Fe content ('Mass (mg) from Fe' in geochronology_compilation_BJT.
xlsx's Data sheet) where available -- Fe stoichiometry is a more reliable
mass estimate than a manual balance reading for these sub-mg fragments --
falling back to the scale-measured mass for the two aliquots (2211HemMSA,
2211HemMSB) that predate the Fe-mass measurement and have no Fe count on
file. Those two are drawn as triangles rather than circles so the plot
itself flags that they sit on a different mass basis than the rest.

Points are colored by mass anomaly -- (scale - Fe-derived)/scale, as a
percent -- on a diverging scale (ANOMALY_CMAP) built rather than taken off
the shelf so 0% lands exactly on neutral gray, not the near-white tint
matplotlib's stock diverging maps put at their midpoint. The two
triangle/fallback aliquots have no Fe-derived mass to compare against, so
no anomaly to color by, and are instead colored NO_FE_COLOR.

Reference lines mark two independently published ages for this same
standard: 453 Ma (Farley & McKeon, 2015; U-Th/21Ne, aliquot MI-45) and 579 Ma
(Hofmann et al., 2020). eU and 4He/mass share the same mass denominator, so
their ratio (4He/eU) is independent of which mass estimate is used --
meaning this suite's own already-reported 'Age (Ma Meas.)' column (computed
upstream of this script) can be used directly to calibrate what ratio
corresponds to a given age, without re-deriving the age equation's decay
constants and production factors from scratch. That re-derivation is worth
avoiding here: the workbook's own U/Th ppm columns are computed with fixed
factors of 298/292 rather than the elemental atomic masses 238/232, and it
is not clear from the sheet alone why, so an independently-derived age
equation risks a unit mismatch against the eU convention actually being
plotted. Concretely: a least-squares fit of ratio = 4He/eU (mass-independent)
vs. this suite's own reported ages, over the eight aliquots with a
well-behaved age (excluding 041323MG16b), evaluated at 453 and 579 Ma, gives
each reference line's slope (4He/mass = slope * eU) in a way that is
guaranteed self-consistent with this workbook's own age pipeline, whatever
its internal ppm convention means. The fit is excellent (R^2 > 0.99) over
this narrow, near-linear age range.

041323MG16b (eU 2.2 ppm at an unremarkable 4He content, apparent age 1540 Ma)
is excluded from that calibration fit as a leverage outlier far outside the
other aliquots' age range, but is still plotted: a low eU alongside
unremarkable 4He is itself a clean picture of U-loss (radiogenic 4He
retained from a formerly higher U budget that has since leached away).

Output: generated/Gogebic_He_vs_eU.pdf
"""
import os
import sys

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(FIG_DIR, '..', 'Tables', 'geochronology_compilation_BJT.xlsx')
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

GOGEBIC_GROUP_HEADER = 'Gogebic Iron Range BIF Hematite, Michigan. (571 Ma)'
MG16B_OUTLIER = '041323MG16b'

# Independently published ages for this same Gogebic hematite standard.
AGE_MI45_21NE = 453.0    # Farley & McKeon (2015); U-Th/21Ne age, aliquot MI-45
AGE_HOFMANN2020 = 579.0  # Hofmann et al. (2020)

# Diverging colormap for mass anomaly, built rather than taken off the shelf
# so 0% anomaly lands on an exactly neutral gray (matplotlib's stock diverging
# maps -- coolwarm, RdBu, etc. -- put a near-white tint at their midpoint, not
# true gray) and each pole is a single, non-cyclic hue (blue below zero, i.e.
# Fe-derived mass under the balance mass; red above).
ANOMALY_CMAP = mcolors.LinearSegmentedColormap.from_list(
    'anomaly_diverging', ['#2166AC', '#808080', '#B2182B'])
NO_FE_COLOR = 'black'  # aliquots with no Fe-derived mass on file: anomaly undefined
POINT_ALPHA = 0.8


def _load_gogebic_rows():
    """Read the Gogebic hematite block of the 'Data' sheet (the group-header
    row 'Gogebic Iron Range BIF Hematite...' through the row before the next
    group header), keyed by header text so a future column insertion fails
    loudly instead of silently reading the wrong field."""
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb['Data']
    header = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]

    def col(text):
        return header.index(text) + 1

    c_name, c_mass, c_he4mg, c_eu, c_age, c_he_ncc, c_he_ncc_err, c_massfe, c_massfe_err, \
        c_umol, c_umol_err, c_thmol, c_thmol_err = (
        col('Sample name'), col('mass (mg)'), col('4He ncc/mg meas.'), col('eU (ppm) meas.'),
        col('Age  (Ma Meas.)'), col('4He ncc (meas.)'), col('4He ncc (meas.)') + 1,
        col('Mass (mg) from Fe'), col('Mass (mg) from Fe') + 1,
        col('U (moles)'), col('U (moles)') + 1, col('Th (moles)'), col('Th (moles)') + 1)

    rows = []
    in_block = False
    for r in range(2, ws.max_row + 1):
        name = ws.cell(row=r, column=c_name).value
        mass = ws.cell(row=r, column=c_mass).value
        if name == GOGEBIC_GROUP_HEADER:
            in_block = True
            continue
        if not in_block:
            continue
        if not isinstance(name, str) or mass is None:
            break  # next group-header row, blank row, or end of block
        rows.append(dict(
            name=name, mass=mass,
            he4_mg_scale=ws.cell(row=r, column=c_he4mg).value,
            eu_scale=ws.cell(row=r, column=c_eu).value,
            age=ws.cell(row=r, column=c_age).value,
            he_ncc=ws.cell(row=r, column=c_he_ncc).value,
            he_ncc_err=ws.cell(row=r, column=c_he_ncc_err).value,
            mass_fe=ws.cell(row=r, column=c_massfe).value,
            mass_fe_err=ws.cell(row=r, column=c_massfe_err).value,
            u_mol=ws.cell(row=r, column=c_umol).value,
            u_mol_err=ws.cell(row=r, column=c_umol_err).value,
            th_mol=ws.cell(row=r, column=c_thmol).value,
            th_mol_err=ws.cell(row=r, column=c_thmol_err).value,
        ))
    return rows


def _line_angle_deg(ax, x0, y0, x1, y1):
    """Angle (degrees) of the line from (x0,y0) to (x1,y1) as it will
    actually appear on screen -- computed in display (pixel) space via the
    axes' current data<->display transform, since eU and 4He/mass span very
    different numeric ranges and a naive atan2 in data units would not match
    the line's rendered slope."""
    p0 = ax.transData.transform((x0, y0))
    p1 = ax.transData.transform((x1, y1))
    return np.degrees(np.arctan2(p1[1] - p0[1], p1[0] - p0[0]))


def _compute_points(rows):
    """eu/he (+ propagated 2-sigma errors) for every aliquot, normalized by
    the Fe-derived mass where available, falling back to the scale-measured
    mass otherwise (2 aliquots, both predating the Fe-mass measurement --
    the scale mass has no propagated uncertainty column in the workbook, so
    their mass_err is treated as 0). Each point carries 'is_fe' (which mass
    was used, i.e. circle vs. triangle) and 'anomaly': the mass anomaly
    (scale - Fe-derived)/scale, as a percent -- only defined (non-None) when
    a Fe-derived mass exists to compare the scale mass against."""
    pts = []
    for r in rows:
        if r['mass_fe'] is not None:
            mass, mass_err, is_fe = r['mass_fe'], r['mass_fe_err'], True
        else:
            mass, mass_err, is_fe = r['mass'], 0.0, False
        he = r['he_ncc'] / mass
        u_ppm = 1e6 * (r['u_mol'] * 298) / (mass / 1000)
        th_ppm = 1e6 * (r['th_mol'] * 292) / (mass / 1000)
        eu = u_ppm + 0.24 * th_ppm

        # eu = K/mass, K = 2.98e8*U_mol + 0.24*2.92e8*Th_mol
        k_num = 2.98e8 * r['u_mol'] + 0.24 * 2.92e8 * r['th_mol']
        k_err = np.hypot(2.98e8 * r['u_mol_err'], 0.24 * 2.92e8 * r['th_mol_err'])
        eu_err = abs(eu) * np.hypot(k_err / k_num, mass_err / mass) if k_num else 0.0
        he_err = he * np.hypot(r['he_ncc_err'] / r['he_ncc'], mass_err / mass)

        anomaly = (r['mass_fe'] - r['mass']) / r['mass_fe'] * 100 if r['mass_fe'] is not None else None

        pts.append(dict(name=r['name'], eu=eu, he=he, eu_err=eu_err, he_err=he_err,
                         anomaly=anomaly, is_fe=is_fe))
    return pts


def main():
    rows = _load_gogebic_rows()
    print(f"Loaded {len(rows)} Gogebic hematite aliquots")

    # --- ratio/age calibration for the reference lines (mass-independent;
    # uses every aliquot with a valid scale-based eU/4He/age, excluding the
    # MG16b leverage outlier) ---
    fit_rows = [r for r in rows if r['name'] != MG16B_OUTLIER
                and r['eu_scale'] and r['he4_mg_scale'] and r['age']]
    ages = np.array([r['age'] for r in fit_rows])
    ratios = np.array([r['he4_mg_scale'] / r['eu_scale'] for r in fit_rows])
    b, a = np.polyfit(ages, ratios, 1)  # ratio = a + b*age
    r2 = np.corrcoef(ages, ratios)[0, 1] ** 2
    slope_mi45 = a + b * AGE_MI45_21NE
    slope_hof2020 = a + b * AGE_HOFMANN2020
    print(f"Age-ratio calibration fit ({len(fit_rows)} aliquots, R^2={r2:.4f}): "
          f"ratio = {a:.3f} + {b:.5f}*Age")
    print(f"  -> 453 Ma (MI-45) line slope: {slope_mi45:.2f} ncc/mg per ppm eU")
    print(f"  -> 579 Ma (Hofmann et al., 2020) line slope: {slope_hof2020:.2f} ncc/mg per ppm eU")

    pts = _compute_points(rows)
    n_fe = sum(p['is_fe'] for p in pts)
    print(f"  {n_fe} aliquots normalized by Fe-derived mass, "
          f"{len(pts) - n_fe} falling back to scale mass")

    # Symmetric about 0 (+/- the largest |anomaly|) rather than independently
    # scaled per side: the anomalies here are lopsided (small negative values,
    # a couple of large positive ones), and TwoSlopeNorm's default per-side
    # scaling would stretch that small negative range to the same full-blue
    # saturation as the large positive range gets in full red -- making a
    # -13% anomaly look as extreme as a +37% one. A symmetric range instead
    # keeps color intensity proportional to |anomaly| on both sides, at the
    # cost of the blues never reaching full saturation.
    anomalies = np.array([p['anomaly'] for p in pts if p['anomaly'] is not None])
    anomaly_bound = np.abs(anomalies).max()
    norm = mcolors.TwoSlopeNorm(vcenter=0, vmin=-anomaly_bound, vmax=anomaly_bound)

    eu = np.array([p['eu'] for p in pts])
    he = np.array([p['he'] for p in pts])
    eu_err = np.array([p['eu_err'] for p in pts])
    he_err = np.array([p['he_err'] for p in pts])
    fe_mask = np.array([p['is_fe'] for p in pts])
    fe_anomaly = np.array([p['anomaly'] for p in pts if p['is_fe']])

    x_max, y_max = 15.0, 950.0
    fig, ax = plt.subplots()

    ax.errorbar(eu, he, xerr=eu_err, yerr=he_err, fmt='none', ecolor='black',
                elinewidth=0.8, capsize=3, alpha=0.6, zorder=2)
    ax.scatter(eu[fe_mask], he[fe_mask], c=fe_anomaly, cmap=ANOMALY_CMAP, norm=norm,
               marker='o', s=70, edgecolor='black', linewidth=0.6, alpha=POINT_ALPHA, zorder=3)
    ax.scatter(eu[~fe_mask], he[~fe_mask], facecolor=NO_FE_COLOR, marker='^', s=90,
               edgecolor='black', linewidth=0.6, alpha=POINT_ALPHA, zorder=3)

    x_line = np.array([0, x_max])
    ax.plot(x_line, slope_mi45 * x_line, color='dimgray', linestyle='--', linewidth=1.2, zorder=1)
    ax.plot(x_line, slope_hof2020 * x_line, color='dimgray', linestyle='-.', linewidth=1.2, zorder=1)
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel('eU (ppm)')
    ax.set_ylabel(r'$^4$He (nccSTP/mg)')
    ax.set_title('Gogebic Hematite Standard MI-43: $^4$He vs. eU')
    ax.grid(alpha=0.3)

    # tight_layout is called (reserving a right-hand strip for the colorbar)
    # *before* the colorbar axes is added -- tight_layout doesn't know how to
    # account for a colorbar and warns/mis-lays-out if one already exists, so
    # the colorbar is instead added afterward as a manually-positioned axes
    # that doesn't disturb ax's now-finalized position (which the rotation
    # calc below relies on).
    fig.tight_layout(rect=(0, 0, 0.88, 1))
    cax = fig.add_axes((0.90, 0.15, 0.03, 0.7))
    cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=ANOMALY_CMAP), cax=cax)
    cbar.set_label('mass anomaly (%)')

    # Labeled close to the origin (rather than out under the cluster) so the
    # upper-right stays uncluttered; still hugging each line (Hofmann et al.
    # 2020 above it, 453 Ma below it), with a small offset off the line
    # itself. Rotation is computed in display space (see _line_angle_deg) so
    # the text visually tracks the rendered line despite eU and 4He/mass
    # spanning very different numeric ranges.
    label_kwargs = dict(fontsize=7, ha='left', color='dimgray', rotation_mode='anchor')
    label_gap = 22
    x_lbl = 3.0
    ax.text(x_lbl, slope_hof2020 * x_lbl + label_gap, '579 Ma (MI-43, U-Th/He, Hofmann et al., 2020)',
            va='bottom', rotation=_line_angle_deg(ax, 0, 0, x_max, slope_hof2020 * x_max),
            **label_kwargs)
    ax.text(x_lbl, slope_mi45 * x_lbl - label_gap, '453 Ma (MI-45, U-Th/$^{21}$Ne, Farley & McKeon, 2015)',
            va='top', rotation=_line_angle_deg(ax, 0, 0, x_max, slope_mi45 * x_max),
            **label_kwargs)

    # Label the MG16b outlier directly (excluded from the calibration fit
    # above, but plotted -- see module docstring).
    mg16b = next(p for p in pts if p['name'] == MG16B_OUTLIER)
    ax.annotate('MG16b', xy=(mg16b['eu'], mg16b['he']),
                xytext=(10, -18), textcoords='offset points', fontsize=7,
                arrowprops=dict(arrowstyle='->', color='black', lw=0.8))

    # NOTE: the process-direction arrows ("U-loss" / "Incomplete
    # dissolution") previously annotated here, anchored at the main
    # cluster's centroid, were removed at the user's request (2026-09-01)
    # to declutter the plot; the U-loss interpretation of the MG16b
    # outlier is still made in the caption/body text.

    outpath = os.path.join(OUTDIR, 'Gogebic_He_vs_eU.pdf')
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Wrote {outpath}")


if __name__ == '__main__':
    main()
