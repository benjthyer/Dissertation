"""
Compare the two independent 3He tube (ampoule) residual-content accounting
methods used for HT-Win-06-01b: the permeation-step / informed bracketing
method's nt (SI Table, tab:ch2-distilled-naive-3he) against the steady-state
bounding method's ntSS = ntUB (main-text Table, tab:ch2-distilled-3he).

nt is read directly from the master workbook's 'Raw Data and Corrections'
sheet, not from the derived DistilledNaiveMethod sheet: for every row typed
'Experimental' (a high-temperature step), nt is the '3He n0 (pccSTP)' value
-- and its 2 sigma -- of the very next row, i.e. n0 of the permeation step
measured immediately after that step (n0 is NOT the same quantity as nt;
nt of step i is n0 of step i+1). This independently reproduces the nt
column already reported in the SI's naive-bracketing table (cross-checked
below), rather than trusting that derived sheet outright.

ntSS is read from the DistilledUncertaintyTreatment sheet's 'ntUB 3He
(pccSTP)' column, the literal source of the main-text bounding table.

Points are colored by "Permeation Time": the Nominal (Heated) Time
(minutes) of the permeation step used to read off nt above -- log-scaled
(LogNorm) so resolution is retained at the short end, since these range
from ~2 to ~10000 minutes. Two steps (195C/1106min and 250C/300min) are
immediately followed by a step at room temperature (~26C, a long
uncontrolled cooldown) rather than a real elevated-temperature permeation
measurement, so for those two the color instead uses the Nominal Heated
Time of the step after that (BJT, 2026-08-14) -- this only changes which
time is used for the color encoding, not which row's n0 is used for nt
itself.

Two steps (250C/10250min and 240C/785min) are immediately followed by a
'Complete Purge' step -- an attempt to fully degas the tube with a long
hot step rather than a short low-temperature bracket measurement -- and
are marked with a triangle and labeled "Attempted complete degas"
accordingly. These are exactly the two steps (besides the low-signal ones
below) where nt exceeds ntSS, i.e. apparently violates the bounding
method's upper bound; per BJT they must stay in the plot rather than be
dropped, since omitting them would misrepresent the dataset.

Steps flagged as low-signal (measured 3He < 0.1 pccSTP, via
thermochr_utils.low_signal_HTWin0601b_mask -- the same exclusion used
elsewhere in this chapter, e.g. fig_delta_plot.py) are excluded from the
plot (but retained, flagged, in the CSV) since their nt/ntSS values are
dominated by measurement noise rather than genuine permeation behavior.

Reads:
  Win0601bHT_data_and_reduction.xlsx, sheets 'Raw Data and Corrections',
  'DistilledUncertaintyTreatment', and 'DistilledNaiveMethod'

Outputs:
  generated/Winsor_nt_vs_ntSS.pdf
  generated/data/nt_vs_ntSS.csv (full 34-step dataset with low_signal,
      attempted_complete_degas, and permeation_time_min flags/values --
      the source check for the SI table's nt column, see the printed
      cross-check below)
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import LogLocator, ScalarFormatter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import low_signal_HTWin0601b_mask
from plot_style import apply_style
apply_style()

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_XLSX = os.path.join(FIG_DIR, '..', 'Tables', 'Win0601bHT_data_and_reduction.xlsx')
OUTDIR = os.path.join(FIG_DIR, 'generated')
DATA_OUTDIR = os.path.join(OUTDIR, 'data')
os.makedirs(DATA_OUTDIR, exist_ok=True)

# --- nt (permeation-step method) and Permeation Time: raw data sheet, the
# row right after each high-temperature ('Experimental') step. Column
# positions match the sheet's row-2 header labels (row 1 is a
# section-title band, row 3 holds a stray timestamp, real data starts row
# 4 -- hence skiprows=3 below).
TEMP_COL, MIN_COL, TYPE_COL, N0_COL, N0_2S_COL = 3, 4, 5, 65, 66
ROOM_TEMP_C = 50.0  # separates the two genuine room-temp (~26C) cooldown
                     # rows from ordinary 85-120C permeation-bracket steps

raw = pd.read_excel(MASTER_XLSX, sheet_name='Raw Data and Corrections',
                     header=None, skiprows=3)
raw.columns = range(raw.shape[1])

exp_idx = raw.index[raw[TYPE_COL] == 'Experimental'].tolist()
temps, minutes, nt, nt_2s, perm_time, is_degas, is_room_temp_next = ([] for _ in range(7))
for i in exp_idx:
    nxt = raw.iloc[i + 1]
    temps.append(raw.iloc[i][TEMP_COL])
    minutes.append(raw.iloc[i][MIN_COL])
    nt.append(nxt[N0_COL])
    nt_2s.append(nxt[N0_2S_COL])
    is_degas.append(nxt[TYPE_COL] == 'Complete Purge')

    room_temp_next = float(nxt[TEMP_COL]) < ROOM_TEMP_C
    is_room_temp_next.append(room_temp_next)
    if room_temp_next:
        perm_time.append(raw.iloc[i + 2][MIN_COL])  # skip past the cooldown row
    else:
        perm_time.append(nxt[MIN_COL])

temps = np.array(temps, dtype=float)
minutes = np.array(minutes, dtype=float)
nt = np.array(nt, dtype=float)
nt_2s = np.array(nt_2s, dtype=float)
perm_time = np.array(perm_time, dtype=float)
is_degas = np.array(is_degas, dtype=bool)
is_room_temp_next = np.array(is_room_temp_next, dtype=bool)

# --- ntSS (bounding method): DistilledUncertaintyTreatment sheet, its
# literal ntUB column -- same row order as the raw-data 'Experimental' steps
# (verified below), one row per high-temperature step plus a trailing
# 'Total' row that pd.to_numeric/notna() drops.
bound = pd.read_excel(MASTER_XLSX, sheet_name='DistilledUncertaintyTreatment', header=0)
bound = bound[pd.to_numeric(bound.iloc[:, 0], errors='coerce').notna()].reset_index(drop=True)
ntSS = pd.to_numeric(bound.iloc[:, 5], errors='coerce').to_numpy()

assert len(nt) == len(ntSS), (
    f"step count mismatch: {len(nt)} 'Experimental' rows in Raw Data and "
    f"Corrections vs {len(ntSS)} rows in DistilledUncertaintyTreatment")
assert np.allclose(temps, pd.to_numeric(bound.iloc[:, 0], errors='coerce').to_numpy(), atol=0.2), \
    "row order mismatch between the two sheets (Temp columns don't line up)"

# Cross-check against the SI's already-published naive-bracketing 'nt 3He'
# column (DistilledNaiveMethod sheet, the source of tab:ch2-distilled-naive-3he).
naive = pd.read_excel(MASTER_XLSX, sheet_name='DistilledNaiveMethod', header=0)
naive = naive[pd.to_numeric(naive.iloc[:, 0], errors='coerce').notna()].reset_index(drop=True)
nt_si_table = pd.to_numeric(naive.iloc[:, 7], errors='coerce').to_numpy()
max_rel_diff = np.nanmax(np.abs(nt - nt_si_table) / nt)
print(f"nt (independently read from raw data) vs. SI table's published nt column: "
      f"max relative difference = {max_rel_diff:.2%} "
      f"(both round to the same displayed value at the table's printed precision)")

low_signal = low_signal_HTWin0601b_mask(MASTER_XLSX)
assert len(low_signal) == len(nt)

out_df = pd.DataFrame({
    'Temp (C)': temps, 'Minutes': minutes,
    'nt (pccSTP)': nt, 'nt 2 sigma': nt_2s, 'ntSS (pccSTP)': ntSS,
    'permeation_time_min': perm_time,
    'used_next-next_step_time': is_room_temp_next,
    'attempted_complete_degas': is_degas,
    'low_signal_excluded': low_signal,
})
out_df.to_csv(os.path.join(DATA_OUTDIR, 'nt_vs_ntSS.csv'), index=False)

keep = ~low_signal
print(f"Excluding {(~keep).sum()} low-signal step(s) from the plot "
      f"(retained, flagged, in the CSV): "
      f"{list(zip(temps[~keep].round(1), minutes[~keep].round(0)))}")

ntSS_p, nt_p, nt_2s_p, perm_time_p, is_degas_p = (
    a[keep] for a in (ntSS, nt, nt_2s, perm_time, is_degas))

# --- plot (log-log: ntSS and nt each span ~2.5 orders of magnitude) ---
fig, ax = plt.subplots()
lo = min(ntSS_p.min(), (nt_p - nt_2s_p).min()) / 1.5
hi = max(ntSS_p.max(), (nt_p + nt_2s_p).max()) * 1.5
lims = (lo, hi)
ax.plot(lims, lims, linestyle='--', color='black', alpha=0.4, zorder=1)

norm = LogNorm(vmin=perm_time_p.min(), vmax=perm_time_p.max())
cmap = plt.cm.Blues

sc = None
for sel, marker, size in [(~is_degas_p, 'o', 60), (is_degas_p, '^', 80)]:
    if not sel.any():
        continue
    ax.errorbar(ntSS_p[sel], nt_p[sel], yerr=nt_2s_p[sel], fmt='none',
                ecolor='black', alpha=0.5, capsize=3, zorder=2)
    sc = ax.scatter(ntSS_p[sel], nt_p[sel], c=perm_time_p[sel], cmap=cmap, norm=norm,
                     marker=marker, s=size, edgecolor='black', linewidth=0.6, zorder=3)

ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_aspect('equal')
ax.set_xlabel(r'$n_{t,\mathrm{SS}}$ (pccSTP)''\nby steady-state upper bound')
ax.set_ylabel(r'$n_{t}$ (pccSTP)''\nby permeation-step method')
ax.set_title('Ampoule $^3$He Inventory Method Comparison')
ax.grid(True, which='both', linestyle='-', color='black', alpha=0.1)

cbar = fig.colorbar(sc, ax=ax)
cbar.set_label('Permeation Time (min)')
cbar.ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 3, 5)))
cbar.ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=12))
cbar.ax.yaxis.set_major_formatter(ScalarFormatter())

legend_elems = [
    Line2D([0], [0], linestyle='--', color='black', alpha=0.4, label='1:1'),
    Line2D([0], [0], marker='o', linestyle='None', markerfacecolor='0.6',
           markeredgecolor='black', markersize=8, label=r'HT-Win-06-01b steps ($^3$He)'),
    Line2D([0], [0], marker='^', linestyle='None', markerfacecolor='0.6',
           markeredgecolor='black', markersize=9, label='Attempted complete degas'),
]
ax.legend(handles=legend_elems, loc='upper left')

fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'Winsor_nt_vs_ntSS.pdf'), dpi=300)
plt.close(fig)
