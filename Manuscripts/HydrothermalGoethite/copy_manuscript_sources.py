"""
Assembles everything hydrothermal_goethite_GCA.tex / _GCA_SI.tex need to
compile on their own -- figures, a trimmed copy of the shared bibliography,
and the auto-generated macro .tex files they \\input from elsewhere in the
dissertation -- into local files in this directory, so the whole
Manuscripts/HydrothermalGoethite/ folder can be zipped up and submitted
standalone, with nothing reaching outside it.

Run this after regenerating any Chapter 1/2 figure, changing a \\citep/
\\citet in the manuscript or SI, or regenerating chapter2_derived_values.tex
/ chapter2_naive_isothermal_tables.tex, and before compiling/submitting.
Everything this script writes -- figures/, references.bib,
chapter2_derived_values.tex, chapter2_naive_isothermal_tables.tex -- is
derived/reproducible and gitignored: rerun the script rather than
hand-editing any of it.

Writes:
  figures/                              - every file the manuscript/SI
                                           \\includegraphics, copied from
                                           Chapter1/2's own
                                           Figures/{generated,source}/
  references.bib                        - only the entries actually
                                           \\citep/\\citet'd by the
                                           manuscript/SI, pulled verbatim out
                                           of the dissertation's shared
                                           ../../references.bib (BibTeX
                                           entries are self-contained blocks,
                                           so lifting the cited ones keeps
                                           the submitted bibliography free of
                                           unrelated dissertation references)
  chapter2_derived_values.tex,
  chapter2_naive_isothermal_tables.tex  - the auto-generated macro files the
                                           wrapper .tex files \\input (update
                                           EXTERNAL_TEX_INPUTS below if a
                                           wrapper ever \\input's a new one
                                           from outside this directory)
"""
import re
import shutil
from pathlib import Path

MANUSCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = MANUSCRIPT_DIR.parent.parent
OUT_FIGURES_DIR = MANUSCRIPT_DIR / 'figures'
SHARED_BIB = REPO_ROOT / 'references.bib'
LOCAL_BIB = MANUSCRIPT_DIR / 'references.bib'

# Files whose \includegraphics/\citep/\citet calls define what this
# manuscript+SI actually needs.
CONTENT_SOURCES = [
    MANUSCRIPT_DIR / 'hydrothermal_goethite_abstract.tex',
    MANUSCRIPT_DIR / 'hydrothermal_goethite_body.tex',
    MANUSCRIPT_DIR / 'hydrothermal_goethite_SI_body.tex',
]

# Same directories, same priority order, the \graphicspath here used before
# figures were copied locally.
SEARCH_DIRS = [
    REPO_ROOT / 'Chapter1' / 'Figures' / 'generated',
    REPO_ROOT / 'Chapter1' / 'Figures' / 'source',
    REPO_ROOT / 'Chapter2' / 'Figures' / 'generated',
    REPO_ROOT / 'Chapter2' / 'Figures' / 'source',
]

# Auto-generated macro files the wrapper .tex files \input from outside this
# directory (hydrothermal_goethite_GCA.tex / _GCA_SI.tex \input them by
# local basename once copied here -- see those files' own comments).
EXTERNAL_TEX_INPUTS = [
    REPO_ROOT / 'Chapter2' / 'Writing' / 'chapter2_derived_values.tex',
    REPO_ROOT / 'Chapter2' / 'Writing' / 'chapter2_naive_isothermal_tables.tex',
]

INCLUDEGRAPHICS_RE = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
CITE_RE = re.compile(r'\\cite[tp]\*?(?:\[[^\]]*\])?(?:\[[^\]]*\])?\{([^}]+)\}')
BIB_ENTRY_START_RE = re.compile(r'@(\w+)\s*\{\s*([^,\s}]+)\s*,')


def _read(path):
    return path.read_text(encoding='utf-8') if path.exists() else ''


# --- Figures -----------------------------------------------------------

def find_referenced_figures():
    names = []
    for tex_path in CONTENT_SOURCES:
        for match in INCLUDEGRAPHICS_RE.finditer(_read(tex_path)):
            name = match.group(1).strip()
            if name not in names:
                names.append(name)
    return names


def copy_figures():
    OUT_FIGURES_DIR.mkdir(exist_ok=True)
    referenced = find_referenced_figures()

    copied, missing = [], []
    for name in referenced:
        src = next((d / name for d in SEARCH_DIRS if (d / name).exists()), None)
        if src is None:
            missing.append(name)
            continue
        shutil.copyfile(src, OUT_FIGURES_DIR / name)
        copied.append(name)

    stale = sorted(p.name for p in OUT_FIGURES_DIR.iterdir()
                    if p.is_file() and p.name not in referenced)

    print(f"Copied {len(copied)} figure(s) into {OUT_FIGURES_DIR}")
    if missing:
        print(f"WARNING: {len(missing)} referenced figure(s) not found in any of:")
        for d in SEARCH_DIRS:
            print(f"  {d}")
        for name in missing:
            print(f"  MISSING: {name}")
    if stale:
        print(f"NOTE: {len(stale)} file(s) in {OUT_FIGURES_DIR} are no longer "
              "referenced and were left in place (not deleted automatically):")
        for name in stale:
            print(f"  {name}")


# --- Bibliography, trimmed to cited entries -----------------------------

def find_cited_keys():
    keys = set()
    for tex_path in CONTENT_SOURCES:
        for match in CITE_RE.finditer(_read(tex_path)):
            for key in match.group(1).split(','):
                key = key.strip()
                if key:
                    keys.add(key)
    return keys


def parse_bib_entries(text):
    """Yield (key, entry_text) for each brace-balanced @type{key, ...} entry."""
    pos = 0
    while True:
        m = BIB_ENTRY_START_RE.search(text, pos)
        if m is None:
            return
        brace_open = text.index('{', m.start())
        depth, j = 0, brace_open
        while j < len(text):
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        end = j + 1
        yield m.group(2), text[m.start():end]
        pos = end


def write_local_bib():
    cited = find_cited_keys()
    entries = dict(parse_bib_entries(_read(SHARED_BIB)))

    found_keys = sorted(k for k in entries if k in cited)
    missing_keys = sorted(cited - entries.keys())

    header = (
        "% =============================================================\n"
        "%  references.bib -- AUTO-GENERATED, DO NOT EDIT BY HAND.\n"
        "%  Written by copy_manuscript_sources.py: every entry actually\n"
        "%  \\citep/\\citet'd by hydrothermal_goethite_{abstract,body,SI_body}.tex,\n"
        "%  pulled verbatim out of the dissertation's shared ../../references.bib.\n"
        "%  Regenerate with: python copy_manuscript_sources.py\n"
        "% =============================================================\n\n"
    )
    body = "\n\n".join(entries[k] for k in found_keys)
    LOCAL_BIB.write_text(header + body + "\n", encoding='utf-8')

    print(f"Wrote {len(found_keys)} cited entries to {LOCAL_BIB}")
    if missing_keys:
        print(f"WARNING: {len(missing_keys)} cited key(s) not found in {SHARED_BIB}:")
        for key in missing_keys:
            print(f"  MISSING: {key}")


# --- Auto-generated macro .tex files -------------------------------------

def copy_external_inputs():
    copied, missing = [], []
    for src in EXTERNAL_TEX_INPUTS:
        if not src.exists():
            missing.append(src)
            continue
        shutil.copyfile(src, MANUSCRIPT_DIR / src.name)
        copied.append(src.name)

    print(f"Copied {len(copied)} macro .tex file(s): {', '.join(copied) if copied else '(none)'}")
    if missing:
        print(f"WARNING: {len(missing)} EXTERNAL_TEX_INPUTS entr(y/ies) not found:")
        for src in missing:
            print(f"  MISSING: {src}")


def main():
    copy_figures()
    write_local_bib()
    copy_external_inputs()


if __name__ == '__main__':
    main()
