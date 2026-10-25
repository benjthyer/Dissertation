#!/usr/bin/env bash
# Wall-time benchmark of HeFESTo itself on whole-mantle adiabats, for 8, 4 and 1 parallel jobs.
#
# Run inside WSL (not Git Bash), from anywhere:
#     bash /mnt/c/Git_Repositories/DissertationBJT/Chapter4/Figures/benchmark_hefesto.sh
#
# 1. Builds one tree of ADIABATS_PER_JOB * max(JOBS) adiabats with
#    nGibbs/scripts/prepare_hefesto_tree_fulladiabat.py (untimed).
# 2. For each job count j, copies the first ADIABATS_PER_JOB * j SimulationN folders
#    into a fresh run directory (untimed), so the compositions are nested: every
#    smaller run is a subset of the larger ones.
# 3. Times nGibbs/scripts/run_hefesto_parallel.py --jobs j on that directory
#    (GNU parallel, one HeFESTo process per adiabat), and appends a row to
#    Chapter4/Figures/generated/benchmark_results_hefesto.csv.
#
# Output is not read back: every adiabat is assumed to succeed and to yield
# ASSEMBLAGES_PER_ADIABAT assemblages. OPENBLAS_NUM_THREADS=1 keeps each HeFESTo
# process on one core, as on the cluster (hefesto_prep.sh).
#
# Override any setting from the environment, e.g. JOBS="8 4 1" WORK=~/hefesto_benchmark bash ...
set -euo pipefail

NGIBBS=${NGIBBS:-$HOME/nGibbs}
PYTHON=${PYTHON:-$HOME/miniconda3/envs/torch-env/bin/python}
HEFESTO_CMD=${HEFESTO_CMD:-'$HOME/HeFESTo/HeFESToRepository/main'}
WORK=${WORK:-$HOME/hefesto_benchmark}
JOBS=${JOBS:-"8 4 1"}
ADIABATS_PER_JOB=${ADIABATS_PER_JOB:-3}
ASSEMBLAGES_PER_ADIABAT=${ASSEMBLAGES_PER_ADIABAT:-141}
GEOROC=${GEOROC:-$NGIBBS/data/MELTStables/GEOROC/GEOROC_PETDB_UNFILTERED_WHOLEROCK_TRAIN.csv}
CONTROL=${CONTROL:-$NGIBBS/src/builder/HeFESTo/batch/shallowHeFESTo}
CSV=${CSV:-"$(cd "$(dirname "$0")" && pwd)/generated/benchmark_results_hefesto.csv"}

export OPENBLAS_NUM_THREADS=1

if [ -e "$WORK" ]; then
    echo "Error: $WORK already exists; remove it or set WORK=..." >&2
    exit 1
fi

max_jobs=$(printf '%s\n' $JOBS | sort -n | tail -1)
n_total=$((ADIABATS_PER_JOB * max_jobs))

echo "Building $n_total adiabats in $WORK/tree (untimed) ..."
"$PYTHON" "$NGIBBS/scripts/prepare_hefesto_tree_fulladiabat.py" \
    --directory "$WORK/tree" --georoc-dir "$GEOROC" --control-path "$CONTROL" --n "$n_total"
mapfile -t sims < <(find "$WORK/tree" -type d -name 'Simulation*' | sort -V)
if [ "${#sims[@]}" -lt "$n_total" ]; then
    echo "Error: expected $n_total SimulationN folders, found ${#sims[@]}" >&2
    exit 1
fi

[ -f "$CSV" ] || echo "jobs,adiabats,assemblages,t_s,hostname,nproc" > "$CSV"

for j in $JOBS; do
    n=$((ADIABATS_PER_JOB * j))
    run_dir="$WORK/run_j$j"
    mkdir -p "$run_dir"
    cp -r "${sims[@]:0:n}" "$run_dir/"

    echo "Running $n adiabats on $j job(s) ..."
    t0=$(date +%s.%N)
    "$PYTHON" "$NGIBBS/scripts/run_hefesto_parallel.py" --base-dir "$run_dir" --jobs "$j" \
        --hefesto-cmd "$HEFESTO_CMD" --joblog "$run_dir/joblog.txt"
    t=$(awk -v a="$t0" -v b="$(date +%s.%N)" 'BEGIN { printf "%.2f", b - a }')

    echo "$j,$n,$((n * ASSEMBLAGES_PER_ADIABAT)),$t,$(hostname),$(nproc)" >> "$CSV"
    echo "  $j job(s): $t s  ->  $CSV"
done
