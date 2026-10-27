"""
Run a script that is reproduced verbatim in the thesis and cache its results.

The chapter shows the script's source with \lstinputlisting, followed by what it
printed and the figure(s) it drew. Those results are written to generated/ by this
runner, so LaTeX never runs Python -- it only reads the cached files:

    generated/<stem>/stdout.txt     everything written to stdout (incl. library chatter)
    generated/<stem>/prints.txt     only the script's own print() calls -- what the
                                    thesis shows under the listing
    generated/<stem>/fig1.pdf       each open matplotlib figure, in creation order
    generated/<stem>/fig2.pdf ...
    generated/<stem>/source.sha256  hash of the script source the cache was made from

Plotting code that would only clutter the listing can live in a companion
<stem>_plots.py, which is run right after the script in the same namespace (so it
sees everything the script defined) and is not shown in the thesis.

A rerun is skipped while the hash of the script (and its companion) matches
source.sha256, so editing either triggers a fresh calculation. --force reruns
regardless.

The script is executed unmodified (as if run as __main__), from its own directory,
with the Agg backend and plt.show() disabled.

Usage
    python run_cached_listing.py nGibbsPhaseDiagram.py
    python run_cached_listing.py nGibbsPhaseDiagram.py --force
"""
import argparse
import contextlib
import hashlib
import io
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT_ROOT = HERE / 'generated'


class _Tee(io.TextIOBase):
    """Write to several streams at once (cache file + console)."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
        return len(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def run(script, force=False):
    script = (HERE / script).resolve()
    out_dir = OUT_ROOT / script.stem
    companion = script.with_name(f'{script.stem}_plots.py')
    sources = [script] + ([companion] if companion.exists() else [])
    digest = hashlib.sha256(b''.join(s.read_bytes() for s in sources)).hexdigest()
    hash_file = out_dir / 'source.sha256'

    if not force and hash_file.exists() and hash_file.read_text().strip() == digest:
        print(f'{script.name}: cache up to date ({out_dir.relative_to(HERE)})')
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob('fig*.pdf'):
        old.unlink()
    hash_file.unlink(missing_ok=True)  # only rewritten once the run succeeds

    plt.show = lambda *a, **k: None
    cwd = os.getcwd()
    os.chdir(script.parent)
    try:
        with open(out_dir / 'stdout.txt', 'w', encoding='utf-8') as f, \
                open(out_dir / 'prints.txt', 'w', encoding='utf-8') as fp, \
                contextlib.redirect_stdout(_Tee(f, sys.__stdout__)):
            # The script's global `print` also copies to prints.txt; library code
            # resolves the builtin, so its output lands in stdout.txt only.
            def script_print(*a, **k):
                if k.get('file') is None:
                    print(*a, **{**k, 'file': fp})
                print(*a, **k)

            # exec rather than runpy.run_path: runpy installs the script as
            # sys.modules['__main__'], so on Windows (spawn) every multiprocessing
            # worker re-imports it and, lacking a __main__ guard, reruns the whole
            # calculation. Left as is, workers re-import this (guarded) runner.
            namespace = {'__name__': '__main__', '__file__': str(script), 'print': script_print}
            for source in sources:
                code = compile(source.read_text(encoding='utf-8'), str(source), 'exec')
                exec(code, namespace)
    finally:
        os.chdir(cwd)

    for i, num in enumerate(plt.get_fignums(), start=1):
        plt.figure(num).savefig(out_dir / f'fig{i}.pdf', bbox_inches='tight')
    plt.close('all')
    hash_file.write_text(digest + '\n')
    print(f'{script.name}: cached to {out_dir.relative_to(HERE)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('scripts', nargs='+', help='script(s) in Chapter4/Figures/')
    ap.add_argument('--force', action='store_true', help='rerun even if the cache is current')
    args = ap.parse_args()
    for s in args.scripts:
        run(s, force=args.force)
