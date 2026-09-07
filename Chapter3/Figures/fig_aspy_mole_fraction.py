"""
Compare two independent estimates of the arsenopyrite mole fraction x on
the pyrite (FeS2) - arsenopyrite (FeAsS) binary, for the Kidd Creek and
Gympie sulfide suites in Chapter3/Tables/geochronology_compilation_BJT.xlsx.

Both endmembers carry exactly one Fe atom per formula unit, so on this
binary:
    n_Fe  = 1                         (per formula unit, any x)
    n_As  = x                         (only the FeAsS component has As)
    MM(x) = (1-x)*MM_FeS2 + x*MM_FeAsS

Estimate 1 -- mass balance (x_mass):
    Given a measured Fe content (Fe moles, an independent ICPMS/isotope-
    dilution measurement in the workbook -- not derived here) and the
    measured aliquot mass, solve n_Fe * MM(x) = mass for x:
        MM(x) = mass / n_Fe
        x_mass = (MM(x) - MM_FeS2) / (MM_FeAsS - MM_FeS2)

Estimate 2 -- As stoichiometry (x_As):
    Convert the measured As concentration (ppm, i.e. ug As / g sample) to
    As moles using the aliquot mass and As's atomic weight, then use the
    same n_As = x relation, approximating total moles (n_Fe, denominator
    of a true mole fraction) by mass / MM_FeAsS -- i.e. treat every mole
    of As as sitting in a full FeAsS formula unit of that molar mass, so
    x_As depends only on measured mass and As content, not on the
    independently-measured (and noisier, see below) Fe moles:
        n_As = (As_ppm * 1e-6) * mass_g / AtomicWeight[As]
        x_As = (n_As * MM_FeAsS) / mass_g

x_mass is workbook column 'Mass (mg) from Fe' run in reverse (that column
instead fixes x = x_As and *predicts* a mass -- 'Mass Deficit' is its
residual against the measured mass); here we invert the same mass-balance
relation to get a second, independent x estimate to compare against x_As
directly.

Note on noise: x_mass is a much noisier estimate than x_As. Fe (moles) is
an independent whole-aliquot Fe assay (not derived from mass/As here),
and the FeS2-FeAsS molar mass range is narrow (~120-163 g/mol, i.e. x
maps to only a ~43 g/mol span) -- so the same few-percent measurement
uncertainty on Fe moles/mass that is unremarkable for the workbook's own
'Mass Deficit' diagnostic (predicted-vs-measured mass, using x_As) turns
into an O(1) swing once inverted into x_mass. Plotted on linear axes,
this shows up as scatter around the 1:1 line rather than a clean match.

The first four Gympie aliquots (013023PVGyPy-1..4) are excluded, matching
the rest of this chapter's treatment of the Gympie suite (an earlier,
differently-prepared batch; see GYMPIE_NOTES in
write_chapter3_geochron_tables.py and GYMPIE_EXCLUDE in
fig_geochronology_ages.py) -- their x_mass values are extreme outliers
(one exceeds 4) that would otherwise swamp the axis range.

Output: Chapter3/Figures/generated/AsPy_MoleFraction_Comparison.pdf
"""
import os
import sys

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

# Standard atomic weights (g/mol; IUPAC conventional values).
ATOMIC_WEIGHT = dict(Fe=55.845, As=74.9216, S=32.06)

MM_FEs2 = ATOMIC_WEIGHT['Fe'] + 2 * ATOMIC_WEIGHT['S']                  # pyrite, FeS2
MM_FEASS = ATOMIC_WEIGHT['Fe'] + ATOMIC_WEIGHT['As'] + ATOMIC_WEIGHT['S']  # arsenopyrite, FeAsS


def _load_distilled_sheet(sheet_name):
    """Read one *Distilled sheet, returning per-aliquot mass, As ppm, and
    Fe moles. Columns are located by header text (not fixed index) -- the
    *Distilled sheets drop one blank spacer column present in the master
    'Data' sheet, so a fixed offset silently reads the wrong field."""
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb[sheet_name]
    header = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]

    def col(text):
        return header.index(text) + 1

    name_col = col('Sample name')
    mass_col = col('mass (mg)')
    as_mol_col = col('As (moles)')
    fe_mol_col = col('Fe (moles)')

    def num(v):
        return float(v) if isinstance(v, (int, float)) else None

    def num_as(v):
        # A literal 0 in this column is this workbook's convention for
        # "As not measured" (early-batch aliquots), not a real zero-ppm
        # measurement -- treat it the same as a blank cell.
        x = num(v)
        return None if x == 0 else x

    rows = []
    for r in range(2, ws.max_row + 1):
        name = ws.cell(row=r, column=name_col).value
        if not isinstance(name, str):
            continue  # section-header/blank rows
        rows.append(dict(
            name=name,
            mass_mg=num(ws.cell(row=r, column=mass_col).value),
            As_mol=num_as(ws.cell(row=r, column=as_mol_col).value),
            Fe_mol=num(ws.cell(row=r, column=fe_mol_col).value),
        ))
        print(num_as(ws.cell(row=r, column=as_mol_col).value))
    return rows


def compute_mole_fractions(rows):
    """Add x_mass and x_As to each row dict; rows lacking mass, As, or Fe
    moles are dropped (x cannot be computed for either scheme)."""
    out = []
    for r in rows:
        if r['mass_mg'] is None or r['As_mol'] is None or not r['Fe_mol']:
            continue
        mass_g = r['mass_mg'] / 1000.0
        fe_mol = r['Fe_mol']

        mm_x = mass_g / fe_mol  # measured molar mass implied by Fe*MM(x) = mass
        x_mass = (mm_x - MM_FEs2) / (MM_FEASS - MM_FEs2)

        as_mol = r['As_mol']
        x_As = ((((mass_g/as_mol)-MM_FEASS)/MM_FEs2)+1)**-1

        r = dict(r, x_mass=x_mass, x_As=x_As)
        out.append(r)
    return out


# Earlier, differently-prepared Gympie batch, excluded elsewhere in this
# chapter (fig_geochronology_ages.py's GYMPIE_EXCLUDE/GYMPIE_FIRST_BATCH;
# write_chapter3_geochron_tables.py's GYMPIE_NOTES) -- their x_mass values
# are extreme outliers (see module docstring) that swamp the axis range
# for the rest of the suite.
GYMPIE_EARLY_BATCH = {'013023PVGyPy-1', '013023PVGyPy-2', '013023PVGyPy-3', '013023PVGyPy-4'}


def plot_comparison():
    kidd_creek = compute_mole_fractions(_load_distilled_sheet('KiddCreekDistilled'))
    gympie = compute_mole_fractions(_load_distilled_sheet('GympieDistilled'))
    gympie = [r for r in gympie if r['name'] not in GYMPIE_EARLY_BATCH]

    fig, ax = plt.subplots()

    for rows, color, marker, label in (
        (kidd_creek, 'steelblue', 'o', 'Kidd Creek'),
        (gympie, 'firebrick', 'D', 'Gympie'),
    ):
        x = [r['x_As'] for r in rows]
        y = [r['x_mass'] for r in rows]
        ax.scatter(x, y, color=color, marker=marker, s=60, alpha=0.75,
                   edgecolor='black', linewidth=0.5, label=label, zorder=3)

    all_rows = kidd_creek + gympie
    hi = max(max(r['x_As'] for r in all_rows), max(r['x_mass'] for r in all_rows))
    lims = (-0.2, hi * 1.05)
    ax.plot(lims, lims, color='dimgray', linestyle='--', linewidth=1.2,
            zorder=1, label='1:1')
    ax.set_xlim(lims)
    ax.set_ylim(lims)

    ax.set_xlabel(r'$x_{\mathrm{As}}$ ($n_{\mathrm{As}}\times$MM(FeAsS) / mass)')
    ax.set_ylabel(r'$x_{\mathrm{mass}}$ (Fe moles $\times$ MM($x$) = mass)')
    ax.set_title('Arsenopyrite Mole Fraction:\nMass-Balance vs. As Content')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    outpath = os.path.join(OUTDIR, 'AsPy_MoleFraction_Comparison.pdf')
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Kidd Creek: {len(kidd_creek)} aliquots plotted")
    print(f"Gympie: {len(gympie)} aliquots plotted "
          f"(excluded {len(GYMPIE_EARLY_BATCH)} early-protocol aliquots)")
    print(f"Wrote {outpath}")


if __name__ == '__main__':
    plot_comparison()
