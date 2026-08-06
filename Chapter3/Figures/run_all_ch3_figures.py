#!/usr/bin/env python3
"""
run_all_ch3_figures.py -- orchestrate runs of all Chapter 3 figure-generating
scripts, mirroring Chapter 2's run_all_figures.py.

Before any fig_*.py script runs, prepare_ch3_regression_cache.py always runs
first: it fits the three named Arrhenius regions (LVCO, Rust, CCp -- see
that script's docstring) from Tables/plotable_sulfides_cache.pkl and writes
generated/data/ch3_regression_cache.json. fig_sulfide_arrhenius.py and
fig_ch3_step_heat_regressions.py both read that cache instead of
hardcoding regression lines.

Immediately after, write_chapter3_macros.py runs (also not a fig_*.py
script). It reads that cache and writes ../Writing/chapter3_derived_values.tex
-- the \\newcommand macros chapter3.tex \\input{}s ahead of the Abstract and
body text, so the activation energies/R^2/closure temperatures quoted there
can never drift out of sync with the underlying regression the way they
had before (see write_chapter3_macros.py's docstring for the Abstract/
Results inconsistency this replaced).

Usage
-----
    python run_all_ch3_figures.py                 # run every discovered figure script
    python run_all_ch3_figures.py --list           # just show what would run
    python run_all_ch3_figures.py --only fig_sulfide_arrhenius.py
    python run_all_ch3_figures.py --skip fig_cumulative_diffusive_time.py
    python run_all_ch3_figures.py --stop-on-error

Exit code is 0 if every script succeeded, 1 if any script failed.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

FIGURES_DIR = Path(__file__).resolve().parent
FIGURE_SCRIPT_PATTERNS = ("fig_*.py",)

PREP_SCRIPT = "prepare_ch3_regression_cache.py"
MACRO_SCRIPT = "write_chapter3_macros.py"


def discover_scripts() -> list[Path]:
    found = {p.name: p for pattern in FIGURE_SCRIPT_PATTERNS for p in FIGURES_DIR.glob(pattern)}
    return [found[name] for name in sorted(found)]


@dataclass
class RunResult:
    name: str
    ok: bool
    seconds: float
    returncode: int | None
    error_tail: str = ""


def run_one(script: Path) -> RunResult:
    start = time.monotonic()
    try:
        proc = subprocess.run([sys.executable, script.name], cwd=FIGURES_DIR,
                               capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        ok = proc.returncode == 0
        error_tail = "" if ok else "\n".join((proc.stderr or proc.stdout).splitlines()[-15:])
        returncode = proc.returncode
    except Exception as exc:
        ok, returncode, error_tail = False, None, f"{type(exc).__name__}: {exc}"
    return RunResult(script.name, ok, time.monotonic() - start, returncode, error_tail)


def _print_result(result: RunResult) -> None:
    status = "OK" if result.ok else "FAILED"
    print(f"[{status}] {result.name} ({result.seconds:.1f}s)")
    if not result.ok and result.error_tail:
        print("  --- last lines of output ---")
        for line in result.error_tail.splitlines():
            print(f"  {line}")
        print("  -----------------------------")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", metavar="SCRIPT")
    parser.add_argument("--skip", nargs="+", metavar="SCRIPT", default=[])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    args = parser.parse_args()

    all_scripts = discover_scripts()
    if args.only:
        wanted = set(args.only)
        missing = wanted - {s.name for s in all_scripts}
        if missing:
            print(f"--only named scripts that weren't discovered: {', '.join(sorted(missing))}", file=sys.stderr)
            return 1
        scripts = [s for s in all_scripts if s.name in wanted]
    else:
        skip = set(args.skip)
        scripts = [s for s in all_scripts if s.name not in skip]

    if args.list:
        print(f"Always run first: {PREP_SCRIPT}, then {MACRO_SCRIPT}")
        print(f"Discovered {len(scripts)} figure script(s) in {FIGURES_DIR}:")
        for s in scripts:
            print(f"  {s.name}")
        return 0

    results: list[RunResult] = []

    print(f"--- {PREP_SCRIPT} (always runs first) " + "-" * 20)
    prep_result = run_one(FIGURES_DIR / PREP_SCRIPT)
    _print_result(prep_result)
    results.append(prep_result)
    if not prep_result.ok:
        print(f"{PREP_SCRIPT} failed -- downstream scripts that read its cache will likely fail too.")

    print(f"--- {MACRO_SCRIPT} (always runs second) " + "-" * 20)
    macro_result = run_one(FIGURES_DIR / MACRO_SCRIPT)
    _print_result(macro_result)
    results.append(macro_result)
    if not macro_result.ok:
        print(f"{MACRO_SCRIPT} failed -- chapter3_derived_values.tex may be stale or missing.")

    print(f"Running {len(scripts)} figure script(s)...\n")
    for script in scripts:
        print(f"--- {script.name} " + "-" * max(0, 60 - len(script.name)))
        result = run_one(script)
        results.append(result)
        _print_result(result)
        if not result.ok and args.stop_on_error:
            print("\nStopping early (--stop-on-error).")
            break

    ok = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    print("=" * 70)
    print(f"Summary: {len(ok)} succeeded, {len(failed)} failed, "
          f"{sum(r.seconds for r in results):.1f}s total")
    if failed:
        print("Failed scripts:")
        for r in failed:
            print(f"  - {r.name}")
    print("=" * 70)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
