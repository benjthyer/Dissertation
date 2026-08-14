"""
Per-step measured/true yield ratio, m/omega, for the real encapsulated
Durango apatite helium step-heat experiment (Table tab:apatite-stepheat),
where m is the measured fractional-of-total helium yield collected outside
the ampoule for a step and omega is the permeation lag-corrected yield
actually evolved from the apatite during that step.

Plotted on a true log y-axis (bars anchored at the ratio's no-anomaly value
of 1) rather than a symlog percent-difference axis, so decades get uniform
spacing all the way through -- a plain percent anomaly, (m-omega)/omega,
has no way to log-scale through its own zero crossing without a
disproportionately wide linear region there.

Truncated to the first 13 steps: the initial prograde ramp (100-300C)
through the isothermal 300C triplicate used to check step-duration effects,
dropping the later, more erratic prograde/retrograde cycling.

Reads: data/durango_apatite_stepheat_experimental.csv (the 25 "Experimental"
rows of Table tab:apatite-stepheat, transcribed directly from
chapter1_body.tex).

Output: DurangoStepYields_RelativeAnomaly.pdf
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style, LEGEND_SIZE
FIGWIDTH_IN = 7.5
apply_style(scale=FIGWIDTH_IN / 6.4)

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)

data = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'data', 'durango_apatite_stepheat_experimental.csv'))

# Cut after the third step of the isothermal 300C triplicate (order 11-13).
data = data[data['order'] <= 13]

order = data['order'].to_numpy()
temp_C = data['temp_C'].to_numpy()
m = data['m_nccSTP'].to_numpy()
omega = data['omega_nccSTP'].to_numpy()

ratio = m / omega
bar_bottom = np.minimum(ratio, 1.0)
bar_height = np.abs(ratio - 1.0)
bar_colors = np.where(ratio >= 1, 'firebrick', 'steelblue')

fig, ax = plt.subplots(figsize=(FIGWIDTH_IN, 4.8))
ax.bar(order, bar_height, bottom=bar_bottom, width=0.6, color=bar_colors)
ax.axhline(1, color='black', linewidth=1)
ax.set_yscale('log')
ax.yaxis.set_major_locator(mticker.LogLocator(base=10))
ax.yaxis.set_minor_locator(mticker.LogLocator(base=10, subs=np.arange(2, 10)))
ax.grid(True, which='major', axis='y', color='lightgrey', linewidth=0.8)
ax.grid(True, which='minor', axis='y', color='lightgrey', linewidth=0.4)
ax.set_axisbelow(True)
ax.set_xticks(order)
ax.set_xticklabels([f'{T:g}°C' for T in temp_C], rotation=45, ha='right')
ax.set_xlabel('Measurement Order (Step Temperature)')
ax.set_ylabel(r'Measured / True Yield Ratio, $m/\omega$')
ax.set_title('Measured / True Yield Ratio\nDurango Apatite Step-Heat Experiment')
legend_handles = [
    plt.Rectangle((0, 0), 1, 1, color='steelblue', label='Undermeasured'),
    plt.Rectangle((0, 0), 1, 1, color='firebrick', label='Overmeasured'),
]
ax.legend(handles=legend_handles, fontsize=LEGEND_SIZE)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'DurangoStepYields_RelativeAnomaly.pdf'), dpi=300,
            bbox_inches='tight')
plt.close(fig)
