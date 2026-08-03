#!/usr/bin/env python3
"""
run_all_figures.py — orchestrate runs of all Chapter 1 figure-generating
scripts.

Each figure lives in its own standalone script (fig_*.py / Fig1.py) that
runs top-to-bottom and writes PDFs (and sometimes CSVs) into this same
directory. This wrapper discovers those scripts, runs each one as its own
subprocess (so a crash or stray global in one script can't affect the
others), and prints a pass/fail summary at the end.

Data-reduction scripts (reduce_*.py) and one-off dev/debug scripts
(sanity_check_*.py) are deliberately NOT included -- this only runs
scripts that produce the manuscript's figures. Re-running data reduction
is a separate, more consequential step (it can overwrite curated
distilled-data tables) and shouldn't happen implicitly as a side effect
of "make the figures."

Usage
-----
    python run_all_figures.py                 # run every discovered figure script
    python run_all_figures.py --list           # just show what would run, don't run it
    python run_all_figures.py --only fig_encapsulated_apatite.py fig_timescale_ratios.py
    python run_all_figures.py --skip fig_predicting_permeation.py
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

# Discover figure scripts by naming convention. Data-reduction scripts
# (reduce_*.py), shared utility/style modules (diffusion_utils.py,
# thermochr_utils.py, plot_style.py), and one-off dev scripts
# (sanity_check_*.py) don't match these patterns and are excluded.
FIGURE_SCRIPT_PATTERNS = ("fig_*.py", "Fig[0-9]*.py")


def discover_scripts() -> list[Path]:
    found: dict[str, Path] = {}
    for pattern in FIGURE_SCRIPT_PATTERNS:
        for path in FIGURES_DIR.glob(pattern):
            found[path.name] = path
    return [found[name] for name in sorted(found)]


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
    stdout_target = None
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
        description="Run all Chapter 1 figure-generating scripts and report which succeeded.",
    )
    parser.add_argument(
        "--only", nargs="+", metavar="SCRIPT",
        help="Only run these scripts (by filename, e.g. fig_timescale_ratios.py).",
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
             "Scripts are independent (each writes its own output files), "
             "so this is safe, but console output will interleave unless "
             "you also pass --log-dir.",
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
    else:
        skip = set(args.skip)
        scripts = [s for s in all_scripts if s.name not in skip]

    if args.list:
        print(f"Discovered {len(scripts)} figure script(s) in {FIGURES_DIR}:")
        for s in scripts:
            print(f"  {s.name}")
        return 0

    print(f"Running {len(scripts)} figure script(s) ({args.jobs} at a time)...\n")

    results: list[RunResult] = []
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

    _print_summary(results, len(scripts))
    return 0 if all(r.ok for r in results) and len(results) == len(scripts) else 1


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
