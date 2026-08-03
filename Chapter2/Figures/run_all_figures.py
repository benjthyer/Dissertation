#!/usr/bin/env python3
"""
run_all_figures.py — orchestrate runs of all Chapter 2 figure-generating
scripts.

Each figure lives in its own standalone script (fig_*.py) that runs
top-to-bottom and writes PDFs (and sometimes CSVs) into this same
directory. This wrapper discovers those scripts, runs each one as its own
subprocess (so a crash or stray global in one script can't affect the
others), and prints a pass/fail summary at the end.

Unlike Chapter 1's figure scripts, several of these are NOT independent:
fig_decomp_vs_hydrothemal.py, fig_delta_plot.py,
fig_decay_vs_hydrothemal_difftime.py, and fig_winsor_money_plot.py all
read He3/4_HDM/KAFwinsor_diffusion.csv, which is written by
fig_winsor_goethite_analysis.py. That script is therefore always run
first, regardless of alphabetical order -- see PRIORITY_ORDER below. If
you use --jobs > 1, note that this only pins the *start* order; a slow
fig_winsor_goethite_analysis.py run and a fast dependent script could
still overlap. Run with --jobs 1 (the default) if you're not sure the
CSVs are already there from a previous run.

Before any fig_*.py script runs, prepare_regression_cache.py is always
run first (it isn't itself a fig_*.py script, so it's not swept up by
--only/--skip/--list below). It derives the Stage 1 Arrhenius reference
line from the master workbook and writes generated/data/stage1_regression_cache.json;
several scripts (fig_delta_plot.py, fig_decomp_vs_hydrothermal.py,
fig_partial_retention_plots.py) read that cache instead of hardcoding
the regression. Re-run this wrapper (not just a single fig_*.py script)
after any change to the workbook's diffusivity reduction so the cache
doesn't go stale.

Next, fig_naive_isothermal_fits.py runs (it IS a fig_*.py script by name,
but is pinned to run here, before write_chapter2_macros.py, rather than
in its alphabetical slot below). It fits the isothermal 3He permeation
sequences and writes generated/data/naive_lambda_arrhenius_cache.json -- and
write_chapter2_macros.py (next) needs that cache to already exist.

Immediately after that, write_chapter2_macros.py runs (also not a
fig_*.py script). It reads both that cache and the Stage 1 cache above
and writes ../Writing/chapter2_derived_values.tex -- \newcommand macros (\ChTwoEa,
\ChTwoEaErr, \ChTwoTc, \ChTwoTcErr, \ChTwoRtwo, \ChTwoN, \ChTwoPermEa,
\ChTwoPermEaErr, \ChTwoPermRtwo, \ChTwoPermN) that chapter2_body.tex/
chapter2_abstract.tex reference instead of hardcoding the activation
energy, closure temperature, R^2, and n (both the Stage 1 diffusivity
regression's and the isothermal permeation regression's). This is what
keeps those numbers from drifting out of sync across the Abstract,
Results, Discussion, Conclusions, SI, and figure captions the way they
did after the UB/LB diffusivity-inversion fix.

Data-reduction scripts (MC_reducer.py) and simulation scripts that mainly
produce intermediate CSVs (goethite_thermal_sims.py) are deliberately NOT
included -- this only runs scripts that produce the manuscript's figures.
Re-running them is a separate, more consequential/expensive step and
shouldn't happen implicitly as a side effect of "make the figures."

Usage
-----
    python run_all_figures.py                 # run every discovered figure script
    python run_all_figures.py --list           # just show what would run, don't run it
    python run_all_figures.py --only fig_naive_fits.py fig_delta_plot.py
    python run_all_figures.py --skip fig_cumulative_diffusive_time.py
    python run_all_figures.py --jobs 4          # run up to 4 scripts in parallel
    python run_all_figures.py --log-dir logs    # write each script's output to logs/<name>.log
                                                 #   instead of streaming to the terminal
    python run_all_figures.py --stop-on-error   # abort the run at the first failure

Exit code is 0 if every script succeeded, 1 if any script failed.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

FIGURES_DIR = Path(__file__).resolve().parent

# Discover figure scripts by naming convention. The data-reduction script
# (MC_reducer.py), the simulation script (goethite_thermal_sims.py), and
# shared utility/style modules (diffusion_utils.py, thermochr_utils.py,
# plot_style.py) don't match this pattern and are excluded.
FIGURE_SCRIPT_PATTERNS = ("fig_*.py",)

# fig_winsor_goethite_analysis.py writes CSVs several other scripts read;
# it must run before them. Pinned first regardless of alphabetical order.
PRIORITY_ORDER = ["fig_winsor_goethite_analysis.py"]

# Always run before any fig_*.py script (see module docstring). Not a
# fig_*.py script itself, so --only/--skip/--list below don't apply to it.
PREP_SCRIPT = "prepare_regression_cache.py"

# Runs after PREP_SCRIPT but before MACRO_SCRIPT (see module docstring).
# This IS one of the discovered fig_*.py scripts, but write_chapter2_macros.py
# depends on the cache it writes, so it's pulled out of the normal
# alphabetical fig_*.py loop and run here instead -- it is NOT run a
# second time in that loop (see main()).
ISOTHERMAL_FIT_SCRIPT = "fig_naive_isothermal_fits.py"

# Always run immediately after ISOTHERMAL_FIT_SCRIPT, before any other
# fig_*.py script (see module docstring). Not a fig_*.py script itself.
MACRO_SCRIPT = "write_chapter2_macros.py"


def discover_scripts() -> list[Path]:
    found: dict[str, Path] = {}
    for pattern in FIGURE_SCRIPT_PATTERNS:
        for path in FIGURES_DIR.glob(pattern):
            found[path.name] = path
    ordered_names = [n for n in PRIORITY_ORDER if n in found] + \
        sorted(n for n in found if n not in PRIORITY_ORDER)
    return [found[name] for name in ordered_names]


@dataclass
class RunResult:
    name: str
    ok: bool
    seconds: float
    returncode: int | None
    log_path: Path | None
    error_tail: str = ""


def run_one(script: Path, log_dir: Path | None) -> RunResult:
    start = time.monotonic()
    log_path = None
    stderr_target = subprocess.STDOUT

    try:
        if log_dir is not None:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"{script.stem}.log"
            with open(log_path, "w", encoding="utf-8") as logfile:
                proc = subprocess.run(
                    [sys.executable, script.name],
                    cwd=FIGURES_DIR,
                    stdout=logfile,
                    stderr=stderr_target,
                    text=True,
                )
            error_tail = ""
            if proc.returncode != 0:
                error_tail = _tail(log_path)
        else:
            # Stream straight to the console (lets tqdm progress bars etc.
            # render normally) and also capture output so we can show a
            # tail on failure.
            proc = subprocess.run(
                [sys.executable, script.name],
                cwd=FIGURES_DIR,
                capture_output=True,
                text=True,
            )
            sys.stdout.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            error_tail = "" if proc.returncode == 0 else _last_lines(proc.stderr or proc.stdout)
        ok = proc.returncode == 0
        returncode = proc.returncode
    except Exception as exc:  # e.g. script.name not found, permissions, etc.
        ok = False
        returncode = None
        error_tail = f"{type(exc).__name__}: {exc}"

    elapsed = time.monotonic() - start
    return RunResult(script.name, ok, elapsed, returncode, log_path, error_tail)


def _tail(log_path: Path, n: int = 15) -> str:
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-n:])


def _last_lines(text: str, n: int = 15) -> str:
    return "\n".join(text.splitlines()[-n:])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all Chapter 2 figure-generating scripts and report which succeeded.",
    )
    parser.add_argument(
        "--only", nargs="+", metavar="SCRIPT",
        help="Only run these scripts (by filename, e.g. fig_delta_plot.py).",
    )
    parser.add_argument(
        "--skip", nargs="+", metavar="SCRIPT", default=[],
        help="Skip these scripts (by filename).",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List discovered figure scripts and exit without running anything.",
    )
    parser.add_argument(
        "--jobs", type=int, default=1, metavar="N",
        help="Run up to N scripts concurrently (default: 1, sequential). "
             "fig_winsor_goethite_analysis.py is still scheduled first, but "
             "with N > 1 a dependent script could start running before it "
             "finishes writing its CSVs -- prefer the default unless you "
             "know those CSVs already exist.",
    )
    parser.add_argument(
        "--log-dir", type=Path, default=None, metavar="DIR",
        help="Write each script's stdout/stderr to DIR/<script>.log instead "
             "of streaming it to the terminal. Recommended when using --jobs > 1.",
    )
    parser.add_argument(
        "--stop-on-error", action="store_true",
        help="Abort the run as soon as a script fails (default: run every "
             "script regardless of earlier failures, then report a summary).",
    )
    args = parser.parse_args()

    all_scripts = discover_scripts()
    if not all_scripts:
        print(f"No figure scripts found in {FIGURES_DIR} "
              f"(looked for {', '.join(FIGURE_SCRIPT_PATTERNS)}).", file=sys.stderr)
        return 1

    if args.only:
        wanted = set(args.only)
        missing = wanted - {s.name for s in all_scripts}
        if missing:
            print(f"--only named scripts that weren't discovered: {', '.join(sorted(missing))}",
                  file=sys.stderr)
            return 1
        scripts = [s for s in all_scripts if s.name in wanted]
        # If the caller explicitly asked for the isothermal-fit script by
        # name, let it run in its normal slot instead of being pulled out
        # (it's already about to run early below in that case would just
        # duplicate it) -- so drop it from the pinned-early step only when
        # it wasn't explicitly requested on its own.
        run_isothermal_early = ISOTHERMAL_FIT_SCRIPT not in wanted
    else:
        skip = set(args.skip)
        scripts = [s for s in all_scripts if s.name not in skip
                   and s.name != ISOTHERMAL_FIT_SCRIPT]
        run_isothermal_early = ISOTHERMAL_FIT_SCRIPT not in skip

    if args.list:
        print(f"Always run first: {PREP_SCRIPT}, then {ISOTHERMAL_FIT_SCRIPT}, then {MACRO_SCRIPT}")
        print(f"Discovered {len(scripts)} figure script(s) in {FIGURES_DIR}:")
        for s in scripts:
            print(f"  {s.name}")
        return 0

    prep_path = FIGURES_DIR / PREP_SCRIPT
    print(f"--- {PREP_SCRIPT} (always runs first) " + "-" * max(0, 40 - len(PREP_SCRIPT)))
    prep_result = run_one(prep_path, args.log_dir)
    _print_result(prep_result)
    if not prep_result.ok:
        print(f"{PREP_SCRIPT} failed -- downstream scripts that read its cache "
              "will likely fail too. Continuing anyway so the summary shows everything.")

    results: list[RunResult] = [prep_result]

    if run_isothermal_early:
        iso_path = FIGURES_DIR / ISOTHERMAL_FIT_SCRIPT
        print(f"--- {ISOTHERMAL_FIT_SCRIPT} (always runs second) " + "-" * max(0, 40 - len(ISOTHERMAL_FIT_SCRIPT)))
        iso_result = run_one(iso_path, args.log_dir)
        _print_result(iso_result)
        if not iso_result.ok:
            print(f"{ISOTHERMAL_FIT_SCRIPT} failed -- write_chapter2_macros.py's "
                  "isothermal-permeation macros will likely fail or be stale too.")
        results.append(iso_result)

    macro_path = FIGURES_DIR / MACRO_SCRIPT
    print(f"--- {MACRO_SCRIPT} (always runs third) " + "-" * max(0, 40 - len(MACRO_SCRIPT)))
    macro_result = run_one(macro_path, args.log_dir)
    _print_result(macro_result)
    if not macro_result.ok:
        print(f"{MACRO_SCRIPT} failed -- chapter2_derived_values.tex may be stale or missing.")
    results.append(macro_result)

    pre_loop_count = len(results)  # prep + (isothermal-fit, if pulled forward) + macro
    print(f"Running {len(scripts)} figure script(s) ({args.jobs} at a time)...\n")
    if args.jobs <= 1:
        for script in scripts:
            print(f"--- {script.name} " + "-" * max(0, 60 - len(script.name)))
            result = run_one(script, args.log_dir)
            results.append(result)
            _print_result(result)
            if not result.ok and args.stop_on_error:
                print("\nStopping early (--stop-on-error).")
                break
    else:
        with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            future_to_script = {pool.submit(run_one, s, args.log_dir): s for s in scripts}
            for future in cf.as_completed(future_to_script):
                result = future.result()
                results.append(result)
                _print_result(result)
                if not result.ok and args.stop_on_error:
                    print("\n--stop-on-error set, but jobs already in flight will "
                          "still finish; no new scripts will be scheduled.")
                    for f in future_to_script:
                        f.cancel()

    total_expected = len(scripts) + pre_loop_count
    _print_summary(results, total_expected)
    return 0 if all(r.ok for r in results) and len(results) == total_expected else 1


def _print_result(result: RunResult) -> None:
    status = "OK" if result.ok else "FAILED"
    print(f"[{status}] {result.name} ({result.seconds:.1f}s)")
    if not result.ok:
        if result.log_path is not None:
            print(f"  see log: {result.log_path}")
        if result.error_tail:
            print("  --- last lines of output ---")
            for line in result.error_tail.splitlines():
                print(f"  {line}")
            print("  -----------------------------")
    print()


def _print_summary(results: list[RunResult], total_expected: int) -> None:
    ok = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    total_time = sum(r.seconds for r in results)

    print("=" * 70)
    print(f"Summary: {len(ok)}/{total_expected} succeeded, "
          f"{len(failed)} failed, {total_time:.1f}s total")
    if failed:
        print("Failed scripts:")
        for r in failed:
            print(f"  - {r.name}")
    print("=" * 70)


if __name__ == "__main__":
    raise SystemExit(main())
