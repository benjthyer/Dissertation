"""Figures for nGibbsEarthMantle.py (not reproduced in the thesis).

run_cached_listing.py runs this right after nGibbsEarthMantle.py, in the same
namespace, so the profiles it computed are already defined. Run on its own, it
imports them (rerunning the calculation) first.

The phase figure compares the emulated profiles with HeFESTo runs of the same
profiles, made by hefesto_earth_mantle_profiles.sh and copied to
source/hefesto_earth_mantle_profiles/. The cache is keyed on the scripts only,
so rerun with --force after replacing those runs.
"""
import csv
from pathlib import Path

import numpy as np
import torch
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from ngibbs.engine.models import HeFESToEmulatorCPU
from ngibbs.utils.file_utils import load_fort99_componentMoles
from ngibbs.deployment_tests._phase_plotting import build_ordered_phases, draw_phase_stack, phase_colors

if 'properties' not in globals():
    from nGibbsEarthMantle import *

plot_rows = np.arange(0, n_profiles, 20)
T_at_lid = properties['temperature'][np.arange(n_profiles), lid_idx]
T_at_TBL = properties['temperature'][np.arange(n_profiles), TBL_idx]

# --- Figure 1: property transects of every 20th profile, and 1:1 plots -------
hefesto_dir = Path(__file__).resolve().parent / 'source' / 'hefesto_earth_mantle_profiles'
with open(hefesto_dir / 'profiles.csv') as f:
    hefesto_runs = sorted(csv.DictReader(f), key=lambda r: int(r['profile_index']))

# HeFESTo bulk properties (fort.56 columns rho, VS, VP) on the same pressure grid
hefesto_columns = {'rho': 3, 'Vs': 5, 'Vp': 6}
hefesto_props = {int(run['profile_index']):
                 {name: np.loadtxt(hefesto_dir / 'profile' / run['simulation'] / 'fort.56', skiprows=2, usecols=col)
                  for name, col in hefesto_columns.items()}
                 for run in hefesto_runs}

# Colored by basalt fraction: silica-rich pyrolite (0) red, basalt (1) blue
cmap = LinearSegmentedColormap.from_list('pyrolite_basalt', ['#b2182b', '#2166ac'])
norm = Normalize(vmin=0, vmax=1)

# Sized so its text stays legible when scaled to the 5.5 in thesis text width
fig = plt.figure(figsize=(7, 7.2), layout='constrained')
top, bottom = fig.subfigures(2, 1, height_ratios=[4, 3])
axes = top.subplots(1, 4, sharey=True)

prop_configs = [  # (property, x-axis label, panel title)
    ('temperature', 'Temperature (K)',    'Temperature'),
    ('rho',         'Density (g/cm$^3$)', 'Density'),
    ('Vp',          '$V_P$ (km/s)',       'P-wave velocity'),
    ('Vs',          '$V_S$ (km/s)',       'S-wave velocity'),
]

for ax, (prop, xlabel, title) in zip(axes, prop_configs):
    for idx in plot_rows:
        ax.plot(properties[prop][idx], pressures, color=cmap(norm(X_basalt[idx])), lw=1.2)
    if prop == 'temperature':  # join the conductive-adiabatic transitions across profiles
        for T_at, P_at in ((T_at_lid, P_lid), (T_at_TBL, P_TBL)):
            ax.plot(T_at[plot_rows], P_at[plot_rows], color='k', lw=1.5, zorder=3)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_title(title, fontsize=11)
    ax.tick_params(labelsize=9.5)
    ax.grid(True, alpha=0.3)

axes[0].set_ylabel('Pressure (GPa)', fontsize=11)
axes[0].set_ylim(P_CMB, 0)
cbar = top.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=axes, orientation='horizontal',
                    fraction=0.05, aspect=40)
cbar.set_label('Basalt fraction', fontsize=11)
cbar.ax.tick_params(labelsize=9.5)

# 1:1 plots: nGibbs against HeFESTo at every node of the six HeFESTo profiles
axes_11 = bottom.subplots(1, 3)
for ax, (prop, xlabel, title) in zip(axes_11, prop_configs[1:]):
    truth = np.concatenate([hefesto_props[int(r['profile_index'])][prop] for r in hefesto_runs])
    pred = np.concatenate([properties[prop][int(r['profile_index'])] for r in hefesto_runs])
    color = np.concatenate([np.full(n_pressures, X_basalt[int(r['profile_index'])]) for r in hefesto_runs])
    ax.scatter(truth, pred, c=color, cmap=cmap, norm=norm, s=1, linewidths=0, zorder=3)
    lims = [min(truth.min(), pred.min()), max(truth.max(), pred.max())]
    ax.plot(lims, lims, color='k', lw=0.3, alpha=0.4, zorder=2)
    ax.set_aspect('equal')
    rmse = np.sqrt(np.mean((pred - truth) ** 2))
    r2 = 1 - np.sum((pred - truth) ** 2) / np.sum((truth - truth.mean()) ** 2)
    ax.text(0.04, 0.96, f'RMSE = {rmse:.3f}\n$R^2$ = {r2:.4f}',
            transform=ax.transAxes, va='top', fontsize=9)
    ax.set_xlabel('HeFESTo ' + xlabel, fontsize=11)
    ax.set_ylabel('nGibbs ' + xlabel, fontsize=11)
    ax.tick_params(labelsize=9.5)
    ax.grid(True, alpha=0.3)

# --- Figure 2: phase abundances, HeFESTo (left) vs. emulator (right) ---------
# HeFESTo profiles: phase mass fractions from each run's fort.99 component moles,
# through the same component -> phase-mass conversion the emulator uses

emulator = HeFESToEmulatorCPU.isentropic_emulator
hefesto_fractions = {}
for run in hefesto_runs:
    component_moles = load_fort99_componentMoles(hefesto_dir / 'profile' / run['simulation'], emulator.ml_indexer)
    with torch.no_grad():
        mass_percent = emulator.make_phase_tables(torch.tensor(component_moles, dtype=torch.float32))[1]
    hefesto_fractions[int(run['profile_index'])] = mass_percent.numpy() / 100

# The pressure axis has three equal-width sections, 0-30, 30-105 and 105-135 GPa,
# so the upper mantle and the CMB region share one scale and the mid mantle is compressed.
P_breaks = [0, 30, 105, P_CMB]
x_breaks = [0, 1 / 3, 2 / 3, 1]
pressure_scale = (lambda P: np.interp(P, P_breaks, x_breaks),
                  lambda x: np.interp(x, x_breaks, P_breaks))

def draw_scale_breaks(ax, dx=0.008, dy=0.05):
    """Double slashes ("railroad tracks") on both horizontal spines at each change of scale."""
    for xb in x_breaks[1:-1]:
        for y in (0, 1):
            ax.plot([xb - dx, xb + dx], [y, y], color='w', lw=3, transform=ax.transAxes, clip_on=False, zorder=5)
            for offset in (-dx, dx):
                ax.plot([xb + offset - dx / 2, xb + offset + dx / 2], [y - dy, y + dy],
                        color='k', lw=0.8, transform=ax.transAxes, clip_on=False, zorder=6)

ordered_phases = build_ordered_phases(mass_phasedict)
colors = phase_colors()

# Sized to fill a thesis page (5.5 x ~8.5 in text block) below a short caption
fig2, axes2 = plt.subplots(len(hefesto_runs), 2, figsize=(6.5, 9), sharex=True, sharey=True,
                           layout='constrained')

for row, run in zip(axes2, hefesto_runs):
    idx = int(run['profile_index'])
    params = (f'$X_{{bas}}$ = {X_basalt[idx]:.1f}, $S$ = {S_ad[idx]:.2f}, '
              f'$P_{{lid}}$ = {P_lid[idx]:.1f}, $P_{{TBL}}$ = {P_TBL[idx]:.1f}')
    for ax, fractions, source in ((row[0], hefesto_fractions[idx], 'HeFESTo'),
                                  (row[1], phase_fractions[idx], 'nGibbs')):
        draw_phase_stack(ax, fractions, np.arange(n_pressures), pressures,
                         ordered_phases, mass_phasedict, colors, f'{source}: {params}')
        ax.title.set_fontsize(8)
        for P_transition in (P_lid[idx], P_TBL[idx]):
            ax.axvline(P_transition, color='k', ls='-', lw=1.0, zorder=4)
        ax.set_xscale('function', functions=pressure_scale)
        ax.set_xticks([0, 10, 20, 30, 55, 80, 105, 115, 125, 135])
        ax.tick_params(labelsize=7)
        draw_scale_breaks(ax)

for ax in axes2[:, 1]:
    ax.set_ylabel('')
for ax in axes2[-1]:
    ax.set_xlabel('Pressure (GPa)')

# Legend below the grid: the phases present in any panel, grouped by color
phases_by_color = {}
for long_name, abbrev in ordered_phases:
    col = mass_phasedict[long_name]
    if max(phase_fractions[plot_rows][..., col].max(),
           max(f[:, col].max() for f in hefesto_fractions.values())) > 0.01:
        phases_by_color.setdefault(colors.get(abbrev, '#aaaaaa'), []).append(abbrev)
fig2.legend([Line2D([], [], color=c, lw=6) for c in phases_by_color],
            [', '.join(abbrevs) for abbrevs in phases_by_color.values()],
            loc='outside lower center', ncol=4, fontsize=8, frameon=False)

plt.show()
