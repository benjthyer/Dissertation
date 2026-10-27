#!/usr/bin/env bash
# HeFESTo reference runs for the whole-mantle profile demo (nGibbsEarthMantle.py),
# for the profiles with basalt fractions 0, 0.2, 0.4, 0.6, 0.8 and 1.0.
#
# Run inside WSL/Linux (not Git Bash), from anywhere:
#     bash /mnt/c/Git_Repositories/DissertationBJT/Chapter4/Figures/hefesto_earth_mantle_profiles.sh
#
# Each profile gets the same parameters as in the demo (same 201-profile sweep,
# same 175-node pressure grid on 0-135 GPa, same snapping of the transitions to
# grid nodes) and is computed by HeFESTo itself in two stages, mirroring the demo:
#
#   1. isentrope/SimulationN -- HeFESTo's self-consistent isentrope at the
#      profile's entropy (control flag -2, as in the deployment-test standards)
#      over the full grid. Only its temperatures are used downstream.
#   2. profile/SimulationN   -- a P-T path run (control flag -1) on the same grid,
#      reading ad.in: T rises linearly in P from 300 K at the surface to the
#      stage-1 isentrope at P_lid, follows the stage-1 isentrope to P_TBL, and
#      rises linearly to T_CMB at 135 GPa. ad.in holds one row per grid node,
#      so HeFESTo's linear interpolation in ad.in returns exactly those
#      temperatures. This is the reference profile to compare with the emulator.
#
# Compositions are the SILICAadiabat/BASALTadiabat standards mixed exactly as in
# the demo (each normalized to sum 1, blended, then scaled to 24 total moles as
# in the training-data builders). Each mixture uses the control file of the
# nearer standard as its template, for its phase list and starting assemblage.
#
# Outputs, under $WORK:
#   profiles.csv           one row per profile: SimulationN, demo profile index,
#                          parameters and transition nodes
#   isentrope/, profile/   HeFESTo SimulationN trees (fort.56 has P, T, rho, VS,
#                          VP, ...; fort.99 has the component moles)
#   timing.csv             wall time of each stage
#
# Requires the HeFESTo runtime environment in the calling shell (as for
# run_hefesto_parallel.py), GNU parallel, and a Python with numpy.
# Override any setting from the environment, e.g. JOBS=3 WORK=~/hefesto_profiles bash ...
# The sweep below must stay in sync with nGibbsEarthMantle.py.
set -euo pipefail

NGIBBS=${NGIBBS:-$HOME/nGibbs}
PYTHON=${PYTHON:-$HOME/miniconda3/envs/torch-env/bin/python}
HEFESTO_CMD=${HEFESTO_CMD:-'$HOME/HeFESTo/HeFESToRepository/main'}
WORK=${WORK:-$HOME/hefesto_earth_mantle_profiles}
JOBS=${JOBS:-6}
BASALT_FRACTIONS=${BASALT_FRACTIONS:-"0 0.2 0.4 0.6 0.8 1.0"}
STANDARDS=${STANDARDS:-$NGIBBS/src/ngibbs/deployment_tests/HeFESToAdiabatStandards/Earth}

export OPENBLAS_NUM_THREADS=1
export WORK BASALT_FRACTIONS STANDARDS

if [ -e "$WORK" ]; then
    echo "Error: $WORK already exists; remove it or set WORK=..." >&2
    exit 1
fi
mkdir -p "$WORK"
echo "stage,simulations,t_s,hostname,nproc" > "$WORK/timing.csv"

run_stage() {  # run_stage <name>: run every SimulationN under $WORK/<name> and time it
    local t0 t
    echo "Running HeFESTo stage '$1' on $JOBS job(s) ..."
    t0=$(date +%s.%N)
    "$PYTHON" "$NGIBBS/scripts/run_hefesto_parallel.py" --base-dir "$WORK/$1" --jobs "$JOBS" \
        --hefesto-cmd "$HEFESTO_CMD" --joblog "$WORK/$1/joblog.txt"
    t=$(awk -v a="$t0" -v b="$(date +%s.%N)" 'BEGIN { printf "%.2f", b - a }')
    local n
    n=$(find "$WORK/$1" -maxdepth 1 -type d -name 'Simulation*' | wc -l)
    echo "$1,$n,$t,$(hostname),$(nproc)" >> "$WORK/timing.csv"
    echo "  stage '$1': $t s"
}

# --- Setup: profile parameters, compositions and stage-1 control files ---------
"$PYTHON" - <<'EOF'
import csv
import os
from pathlib import Path

import numpy as np

work = Path(os.environ['WORK'])
standards = Path(os.environ['STANDARDS'])
fractions = [float(x) for x in os.environ['BASALT_FRACTIONS'].split()]

# The demo's sweep (nGibbsEarthMantle.py)
n_pressures, n_profiles, P_CMB, T_surface = 175, 201, 135, 300
pressures = np.linspace(0, P_CMB, n_pressures)
X_basalt = np.linspace(1, 0, n_profiles)
S_ad = np.linspace(2.3, 2.8, n_profiles)
P_lid = np.linspace(8, 1, n_profiles)
P_TBL = np.linspace(132, 125, n_profiles)
T_CMB = np.linspace(3500, 5000, n_profiles)
lid_idx = np.abs(pressures - P_lid[:, None]).argmin(axis=1)
TBL_idx = np.abs(pressures - P_TBL[:, None]).argmin(axis=1)

ELEMENTS = ['Si', 'Mg', 'Fe', 'Ca', 'Al', 'Na', 'Cr', 'O']

def read_control(name):
    lines = (standards / f'{name}adiabat' / 'control').read_text().splitlines()
    start = lines.index('oxides') + 1
    moles = {line.split()[0]: float(line.split()[1]) for line in lines[start:start + len(ELEMENTS)]}
    return lines, start, moles

templates = {name: read_control(name) for name in ('SILICA', 'BASALT')}

def write_control(path, template, first_line, moles):
    lines, start, _ = template
    lines = list(lines)
    lines[0] = first_line
    for i, el in enumerate(ELEMENTS):
        lines[start + i] = f'{el:>2} {moles[el]:17.5f} {moles[el]:11.5f}    0'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')

rows = []
for sim, X in enumerate(fractions, start=1):
    i = int(round((1 - X) * (n_profiles - 1)))
    if not np.isclose(X_basalt[i], X):
        raise SystemExit(f'Basalt fraction {X} is not on the demo sweep')

    # Mixed as by ngibbs mix_compositions, then scaled to 24 total moles
    silica, basalt = templates['SILICA'][2], templates['BASALT'][2]
    moles = {el: (1 - X) * silica[el] / sum(silica.values()) + X * basalt[el] / sum(basalt.values())
             for el in ELEMENTS}
    moles = {el: 24 * v / sum(moles.values()) for el, v in moles.items()}
    template = 'BASALT' if X >= 0.5 else 'SILICA'

    # P1,P2,nP,T1,T2,nT,iensem,superad,tfreeze: with iensem = -2 the T fields hold
    # the target entropy; with -1 the temperatures come from ad.in (superad = 0).
    write_control(work / 'isentrope' / f'Simulation{sim}' / 'control', templates[template],
                  f'0,{P_CMB},{n_pressures - 1},{S_ad[i]:.6f},{S_ad[i]:.6f},0,-2,0,0,0,0', moles)
    write_control(work / 'profile' / f'Simulation{sim}' / 'control', templates[template],
                  f'0,{P_CMB},{n_pressures - 1},0,0,0,-1,0,0,0,0', moles)

    rows.append({'simulation': f'Simulation{sim}', 'profile_index': i, 'X_basalt': X_basalt[i],
                 'S_ad': S_ad[i], 'P_lid': pressures[lid_idx[i]], 'P_TBL': pressures[TBL_idx[i]],
                 'T_CMB': T_CMB[i], 'T_surface': T_surface, 'lid_idx': lid_idx[i],
                 'TBL_idx': TBL_idx[i], 'template': template,
                 **{f'{el}_moles': moles[el] for el in ELEMENTS}})

with open(work / 'profiles.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
for r in rows:
    print(f"{r['simulation']}: profile {r['profile_index']}, X_basalt = {r['X_basalt']:.2f}, "
          f"S = {r['S_ad']:.4f} J/g/K, P_lid = {r['P_lid']:.2f} GPa, P_TBL = {r['P_TBL']:.2f} GPa, "
          f"T_CMB = {r['T_CMB']:.1f} K ({r['template']} template)")
EOF

# --- Stage 1: isentropes -------------------------------------------------------
run_stage isentrope

# --- Build each profile's ad.in from its stage-1 isentrope ------------------------
"$PYTHON" - <<'EOF'
import csv
import os
from pathlib import Path

import numpy as np

work = Path(os.environ['WORK'])
n_pressures, P_CMB = 175, 135
pressures = np.linspace(0, P_CMB, n_pressures)

with open(work / 'profiles.csv') as f:
    rows = list(csv.DictReader(f))

for r in rows:
    fort56 = work / 'isentrope' / r['simulation'] / 'fort.56'
    if not fort56.exists():
        raise SystemExit(f'{fort56} is missing: stage 1 failed for {r["simulation"]}')
    P, T_isentrope = np.loadtxt(fort56, skiprows=2, usecols=(0, 2), unpack=True, ndmin=2)
    if len(P) != n_pressures or not np.allclose(P, pressures, atol=1e-6):
        raise SystemExit(f'{fort56}: expected {n_pressures} nodes on 0-{P_CMB} GPa, found {len(P)}')

    lid, TBL = int(r['lid_idx']), int(r['TBL_idx'])
    T = T_isentrope.copy()
    T[:lid + 1] = np.linspace(float(r['T_surface']), T_isentrope[lid], lid + 1)
    T[TBL:] = np.linspace(T_isentrope[TBL], float(r['T_CMB']), n_pressures - TBL)

    # Rows of (P, unused depth, T), one per grid node
    np.savetxt(work / 'profile' / r['simulation'] / 'ad.in',
               np.column_stack([pressures, np.zeros(n_pressures), T]), fmt='%20.12f')
    print(f"{r['simulation']}: T = {T[lid]:.1f} K at P_lid, {T[TBL]:.1f} K at P_TBL")
EOF

# --- Stage 2: full profiles ---------------------------------------------------------
run_stage profile

# --- Check that every profile ran to completion -------------------------------------
"$PYTHON" - <<'EOF'
import csv
import os
from pathlib import Path

import numpy as np

work = Path(os.environ['WORK'])
with open(work / 'profiles.csv') as f:
    rows = list(csv.DictReader(f))

failed = 0
for r in rows:
    sim_dir = work / 'profile' / r['simulation']
    target = np.loadtxt(sim_dir / 'ad.in')[:, 2]
    fort56 = sim_dir / 'fort.56'
    if not fort56.exists():
        print(f"{r['simulation']}: no fort.56 -- HeFESTo failed")
        failed += 1
        continue
    T = np.loadtxt(fort56, skiprows=2, usecols=(2,), ndmin=1)
    if len(T) != len(target):
        print(f"{r['simulation']}: {len(T)} of {len(target)} nodes computed")
        failed += 1
        continue
    print(f"{r['simulation']}: {len(T)} nodes, max |T - ad.in| = {np.abs(T - target).max():.3f} K")
print(f'{len(rows) - failed} of {len(rows)} profiles complete; results in {work}')
EOF
