"""
Geochronology results plots: individual-aliquot U-Th/He ages (with error
bars) for the three sample suites reduced in Chapter3/Tables/
geochronology_compilation_BJT.xlsx -- Durango apatite (a known-age
standard, used here to show the effect of atmospheric He contamination),
Kidd Creek VMS pyrite, and Gympie pyrite/arsenopyrite.

All ages are the "Age (Ma Atm=1Ra Corr.)" column -- the second age column
in each *Distilled sheet, atmospheric-He-corrected assuming the tube
blank has a 1 Ra (atmospheric) isotope ratio -- not the raw "Age (Ma
Meas.)" column, per the convention used throughout this chapter's
geochronology discussion.

Reads Chapter3/Tables/geochronology_compilation_BJT.xlsx, sheets
'DurangoDistilled', 'KiddCreekDistilled', 'GympieDistilled' (all three
share an identical column layout; see _load_distilled_sheet).

Outputs, all -> generated/:
    Durango_Age_vs_Ra.pdf
        Age (Ma, atm-corrected) vs. measured 3/4He (Ra). Durango's
        accepted age (Farley 2000: 32.1 Ma) is drawn as a horizontal
        reference line; atmospheric composition (Ra=1) as a vertical
        one, since it's the natural way to read contamination off this
        plot: aliquots trend from the accepted age (retentive, low
        atmospheric contribution) towards the atmospheric endpoint as Ra
        increases.
    KiddCreek_Age_vs_Sm.pdf
        Age vs. Sm content, with Sturrock et al. (2024)'s independent
        392 +/- 32 Ma regional apatite cooling-age estimate as a shaded
        horizontal reference band.
    Gympie_Age_vs_eU.pdf
        Age vs. eU, split by sample preparation (HCl-leached vs. not --
        identified by 'HCl' in the sample name), with the 235 Ma K/Ar
        syntectonic quartz-vein age (Cuneen 1994; Holcombe et al. 1997)
        and 307 Ma Ar/Ar regional-pluton age (Little et al. 1995) drawn
        as horizontal reference lines. The first 4 aliquots (013023PVGyPy-
        1..4, an earlier/differently-prepared batch) and the outlier
        0413PyGy-4 are excluded, per the chapter's own treatment of this
        dataset.
"""
import os
import sys

import matplotlib.pyplot as plt
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = os.path.join(FIG_DIR, '..', 'Tables', 'geochronology_compilation_BJT.xlsx')
OUTDIR = os.path.join(FIG_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)

# Column layout is identical across DurangoDistilled/KiddCreekDistilled/
# GympieDistilled (verified against each sheet's header row); located by
# header text below rather than hardcoded so a future column insertion
# fails loudly instead of silently reading the wrong field.
COLUMN_HEADERS = {
    'name': 'Sample name',
    'eU': 'eU (ppm) meas.',
    'Ra': '3/4He (Ra)',
    'Ra_err': None,  # header text is identical to age/other '±2σ' columns; resolved positionally below
    'age_corr': 'Age (Ma Atm=1Ra Corr.)',
    'age_corr_err': None,
    'Sm': 'Sm ppm',
    'Sm_err': None,
}


def _load_distilled_sheet(sheet_name):
    """Read one *Distilled sheet into a list of dicts (one per sample row),
    with numeric fields coerced to float and non-numeric/blank values
    (Excel formula errors like '#DIV/0!', section-header rows, blank
    rows) turned into None."""
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb[sheet_name]
    header = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]

    def col(text):
        return header.index(text) + 1

    name_col = col('Sample name')
    he4_col = col('4He ncc/mg meas.')  # no adjacent '±2σ' column for this field
    eU_col = col('eU (ppm) meas.')
    ra_col = col('3/4He (Ra)')
    ra_err_col = ra_col + 1  # '±2σ' immediately follows its value column throughout this workbook
    age_col = col('Age (Ma Atm=1Ra Corr.)')
    age_err_col = age_col + 1
    sm_col = col('Sm ppm')
    sm_err_col = sm_col + 1
    Th_col = col('Th ppm')
    Th_err_col = Th_col + 1

    def num(v):
        return float(v) if isinstance(v, (int, float)) else None

    rows = []
    for r in range(2, ws.max_row + 1):
        name = ws.cell(row=r, column=name_col).value
        if not isinstance(name, str):
            continue  # section-header/blank rows (e.g. KiddCreekDistilled row 2)
        rows.append(dict(
            name=name,
            He4_nccmg=num(ws.cell(row=r, column=he4_col).value),
            eU=num(ws.cell(row=r, column=eU_col).value),
            Ra=num(ws.cell(row=r, column=ra_col).value),
            Ra_err=num(ws.cell(row=r, column=ra_err_col).value),
            age_corr=num(ws.cell(row=r, column=age_col).value),
            age_corr_err=num(ws.cell(row=r, column=age_err_col).value),
            Sm=num(ws.cell(row=r, column=sm_col).value),
            Sm_err=num(ws.cell(row=r, column=sm_err_col).value),
            Th=num(ws.cell(row=r, column=Th_col).value),
            Th_err=num(ws.cell(row=r, column=Th_err_col).value),
        ))
    return rows


def _errorbar(ax, rows, xkey, xerr_key, color, marker, label, y_key='age_corr', y_err_key='age_corr_err'):
    x = [r[xkey] for r in rows]
    y = [r[y_key] for r in rows]
    yerr = [r[y_err_key] for r in rows]
    xerr = [r[xerr_key] for r in rows] if xerr_key else None
    ax.errorbar(x, y, yerr=yerr, xerr=xerr, fmt=marker, color=color, ecolor=color,
                capsize=4, alpha=0.75, markersize=7, markeredgecolor='black',
                markeredgewidth=0.5, linestyle='none', label=label)


def plot_durango():
    rows = _load_distilled_sheet('DurangoDistilled')
    rows = [r for r in rows if r['Ra'] is not None and r['age_corr'] is not None]

    fig, ax = plt.subplots()
    _errorbar(ax, rows, 'Ra', None, 'darkorange', 'o', 'Durango Apatite')

    ax.axhline(32.1, color='black', linestyle='--', linewidth=1.5,
               label='Accepted age: 32.1 Ma (Farley, 2000)')
    #ax.axvline(1.0, color='gray', linestyle=':', linewidth=1.5,
    #           label='Atmospheric composition ($R_a$ = 1)')

    ax.set_xscale('log')
    ax.set_xlabel(r'$^3$He/$^4$He (Ra)')
    ax.set_ylabel('Atm. Corrected Age (Ma)')
    ax.set_title('Durango Apatite and Atmospheric Helium')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'Durango_Age_vs_Ra.pdf'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Durango: plotted {len(rows)} aliquots")


def plot_kidd_creek():
    rows = _load_distilled_sheet('KiddCreekDistilled')
    #rows = [r for r in rows if r['Sm'] is not None and r['age_corr'] is not None]

    rows = [r for r in rows if r['Th'] is not None and r['age_corr'] is not None]

    fig, ax = plt.subplots()
    _errorbar(ax, rows, 'Th', 'Th_err', 'steelblue', 'o', 'Kidd Creek VMS Pyrite')

    ax.axhspan(392 - 32, 392 + 32, color='black', alpha=0.12, zorder=0)
    ax.axhline(392, color='black', linestyle='--', linewidth=1.5,
               label='Regional apatite cooling age:\n392 $\\pm$ 32 Ma (Sturrock et al., 2024)')

    ax.set_xscale('log')
    ax.set_xlabel('Th (ppm)')
    ax.set_ylabel('Age (Ma, atm. corrected)')
    ax.set_title('Kidd Creek Pyrite: Age vs. Th Content')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'KiddCreek_Age_vs_Th.pdf'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Kidd Creek: plotted {len(rows)} aliquots")


def plot_kidd_creek_th_he():
    """Two-column companion to plot_kidd_creek(): Th (left panel) and 4He
    (right panel) each vs. Age, sharing one Age y-axis (sharey=True, with
    the right panel's tick labels suppressed) so the two proxies read as
    one figure instead of two separate plots."""
    rows = _load_distilled_sheet('KiddCreekDistilled')
    rows = [r for r in rows if r['Th'] is not None and r['He4_nccmg'] is not None
            and r['age_corr'] is not None]

    fig, (ax_th, ax_he) = plt.subplots(1, 2, sharey=True, figsize=(9, 5))

    _errorbar(ax_th, rows, 'Th', 'Th_err', 'steelblue', 'o', 'Kidd Creek VMS Pyrite')
    _errorbar(ax_he, rows, 'He4_nccmg', None, 'steelblue', 'o', 'Kidd Creek VMS Pyrite')

    for ax in (ax_th, ax_he):
        ax.axhspan(392 - 32, 392 + 32, color='black', alpha=0.12, zorder=0)
        ax.axhline(392, color='black', linestyle='--', linewidth=1.5)
        ax.set_xscale('log')
        ax.grid(alpha=0.3)

    ax_th.set_xlabel('Th (ppm)')
    ax_he.set_xlabel(r'$^4$He (nccSTP/mg)')
    ax_th.set_ylabel('Age (Ma, atm. corrected)')
    ax_he.tick_params(labelleft=False)  # shared y axis -- right panel doesn't need its own tick labels

    # Labeled directly (white background box) rather than via a legend,
    # same convention as plot_gympie() -- only on the left panel, since
    # the reference band means the same thing on both and a second copy
    # of the same label on the right would just be clutter.
    trans = ax_th.get_yaxis_transform()
    ax_th.text(0.04, 392 + 32, '392 $\\pm$ 32 Ma (Sturrock et al., 2024)',
               transform=trans, ha='left', va='bottom', fontsize=10,
               bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5))

    fig.suptitle('Kidd Creek Pyrite: Age vs. Th and He Content')
    fig.tight_layout()
    outpath = os.path.join(OUTDIR, 'KiddCreek_Age_vs_Th_and_He.pdf')
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Kidd Creek Th+He: plotted {len(rows)} aliquots")


# First 4 aliquots (differently-prepared/earlier batch) and one outlier,
# excluded per the chapter's own treatment of this dataset.
GYMPIE_EXCLUDE = {'013023PVGyPy-1', '013023PVGyPy-2', '013023PVGyPy-3', '013023PVGyPy-4',
                  '0413PyGy-4'}


def plot_gympie():
    rows = _load_distilled_sheet('GympieDistilled')
    rows = [r for r in rows if r['name'] not in GYMPIE_EXCLUDE
            and r['eU'] is not None and r['age_corr'] is not None]
    hcl_rows = [r for r in rows if 'HCl' in r['name']]
    other_rows = [r for r in rows if 'HCl' not in r['name']]

    fig, ax = plt.subplots()
    _errorbar(ax, hcl_rows, 'eU', None, 'firebrick', 'D', 'HCl-leached')
    _errorbar(ax, other_rows, 'eU', None, 'navy', 'o', 'Not HCl-leached')

    ax.axhline(235, color='dimgray', linestyle='-', linewidth=0.5)
    ax.axhline(307, color='dimgray', linestyle='-', linewidth=0.5)

    # Labeled directly on the plot (rather than via the legend) so the
    # legend itself can shrink to just the two sample-group markers. Text
    # x-position is in axes-fraction (independent of eU's data range) via
    # get_yaxis_transform(); y stays in data coords so each label tracks
    # its own line, centered right on it. A white background box (rather
    # than relying on nearby empty space, which isn't guaranteed -- ages
    # here can land anywhere from ~0 to >300 Ma depending on the sample
    # suite) keeps each label legible even if a data point ends up
    # directly behind it.
    trans = ax.get_yaxis_transform()
    label_box = dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5)
    ax.text(0.02, 235, 'syntectonic quartz veins:\n235 Ma(Cuneen, 1994)',
            transform=trans, ha='left', va='center', fontsize=10, color='black')
    ax.text(0.98, 307, 'Ar/Ar, regional plutonism: 307 Ma\n(Little et al., 1995)',
            transform=trans, ha='right', va='center', fontsize=10, color='black')

    ax.set_xlabel('eU (ppm)')
    ax.set_ylabel('Age (Ma, atm. corrected)')
    ax.set_title('Gympie Pyrite/Arsenopyrite: Age vs. eU')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, loc='lower left')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'Gympie_Age_vs_eU.pdf'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gympie: plotted {len(hcl_rows)} HCl-leached + {len(other_rows)} other aliquots "
          f"(excluded {len(GYMPIE_EXCLUDE)} by name)")


# Only the first-4 (differently-prepared) batch is excluded here -- the
# outlier 0413PyGy-4 that plot_gympie() also drops is deliberately put
# back in, so this SI figure can show why it was excluded from the main
# text figure.
GYMPIE_FIRST_BATCH = {'013023PVGyPy-1', '013023PVGyPy-2', '013023PVGyPy-3', '013023PVGyPy-4'}
GYMPIE_OUTLIER = '0413PyGy-4'


def plot_gympie_supplement():
    """SI companion to plot_gympie(): same sample suite and HCl/non-HCl
    split, but with the 0413PyGy-4 outlier put back in, no reference-age
    lines, and age plotted against measured 4He content (nccSTP/g, i.e.
    'ncc/mg meas.' * 1000) rather than eU -- to visually justify excluding
    0413PyGy-4 from the main-text figure."""
    rows = _load_distilled_sheet('GympieDistilled')
    rows = [r for r in rows if r['name'] not in GYMPIE_FIRST_BATCH
            and r['He4_nccmg'] is not None and r['age_corr'] is not None]
    """for r in rows:
        r['He4_nccg'] = r['He4_nccmg'] """

    hcl_rows = [r for r in rows if 'HCl' in r['name']]
    other_rows = [r for r in rows if 'HCl' not in r['name']]

    fig, ax = plt.subplots()
    _errorbar(ax, hcl_rows, 'He4_nccmg', None, 'firebrick', 'D', 'HCl-leached')
    _errorbar(ax, other_rows, 'He4_nccmg', None, 'navy', 'o', 'Unabraded')
    """
    outlier = next((r for r in rows if r['name'] == GYMPIE_OUTLIER), None)
    if outlier is not None:
        ax.annotate(f'(excluded from main figure)',
                    xy=(outlier['He4_nccmg'], outlier['age_corr']),
                    xytext=(15, 15), textcoords='offset points', fontsize=8,
                    arrowprops=dict(arrowstyle='->', color='black'))
    else:
        print(f'  WARNING: GYMPIE_OUTLIER not found in GympieDistilled -- can't annotate it')
    """
    ax.set_xlabel(r'$^4$He (nccSTP/g)')
    ax.set_ylabel('Age (Ma, atm. corrected)')
    ax.set_title('Gympie Pyrite/Arsenopyrite: Helium Implantation')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'Gympie_Age_vs_4He_SI.pdf'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gympie SI (4He, outlier included): plotted {len(hcl_rows)} HCl-leached + "
          f"{len(other_rows)} other aliquots")


if __name__ == '__main__':
    plot_durango()
    plot_kidd_creek()
    plot_kidd_creek_th_he()
    plot_gympie()
    plot_gympie_supplement()
    print(f"Wrote figures to {OUTDIR}")
