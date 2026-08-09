#!/usr/bin/env python3
"""
run_chapter_figures.py -- regenerate one chapter's figures.

Usage:
    python tools/run_chapter_figures.py Chapter1

Prefers Chapter<N>/Figures/run_all_figures.py when it exists -- it may
encode ordering dependencies between scripts (e.g. Chapter 2's
fig_winsor_goethite_analysis.py must run before several others that read
its output CSVs). Falls back to running every fig_*.py / Fig[0-9]*.py
directly, in sorted order, when no orchestrator is present yet (currently
Chapter 3).

This exists so the Makefile doesn't depend on a POSIX shell: native
Windows `make` (e.g. the one bundled in a conda env, invoked from
PowerShell) runs recipes through cmd.exe, not bash/sh, so shell
constructs like `rm`, `[ -f ... ]`, and `for f in ...; do ... done` all
fail there with "CreateProcess(...) failed". Python is already a hard
dependency of this repo and behaves identically on Windows/macOS/Linux,
so all of that logic lives here instead of in the Makefile.
"""
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python tools/run_chapter_figures.py <ChapterDir>", file=sys.stderr)
        return 2

    chapter_dir = Path(sys.argv[1])
    figures_dir = chapter_dir / "Figures"
    if not figures_dir.is_dir():
        print(f"No Figures/ directory at {figures_dir}", file=sys.stderr)
        return 1

    orchestrator = figures_dir / "run_all_figures.py"
    if orchestrator.is_file():
        print(f"==> {chapter_dir.name}: running run_all_figures.py")
        result = subprocess.run([sys.executable, orchestrator.name], cwd=figures_dir)
        return result.returncode

    scripts = sorted(figures_dir.glob("fig_*.py")) + sorted(figures_dir.glob("Fig[0-9]*.py"))
    if not scripts:
        print(f"No fig_*.py scripts found in {figures_dir}", file=sys.stderr)
        return 1

    print(f"==> {chapter_dir.name}: no run_all_figures.py yet, "
          f"running {len(scripts)} fig_*.py script(s) directly")
    for script in scripts:
        print(f"--- {script.name} ---")
        result = subprocess.run([sys.executable, script.name], cwd=figures_dir)
        if result.returncode != 0:
            print(f"{script.name} failed (exit {result.returncode})", file=sys.stderr)
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
