# ==============================================================================
# Makefile for "From Surface to Core" dissertation
#
# Two kinds of targets:
#
#   1. Figure targets -- run each chapter's Figures/run_all_figures.py (or,
#      for chapters that don't have that orchestrator yet, every fig_*.py
#      directly) to (re)populate Figures/generated/ and the derived-value
#      caches in Figures/data/. Nothing under generated/ is tracked in git
#      (see .gitignore) -- it's always reproducible from source/ + data/ +
#      the scripts, which is the whole point of the split.
#
#   2. LaTeX targets -- compile the full dissertation, or a single chapter's
#      standalone journal-draft manuscript, via latexmk (handles the
#      pdflatex -> biber -> pdflatex -> pdflatex cycle automatically; no
#      need to chain those by hand).
#
# Usage:
#   make figures          # regenerate every chapter's figures/value caches
#   make figures-ch1      # regenerate just Chapter 1's
#   make thesis           # build dissertation.pdf from whatever is
#                          #   currently in each chapter's Figures/generated/
#                          #   (does NOT rerun any python -- fast, use this
#                          #   for ordinary text/equation edits)
#   make listings          # run + cache scripts shown as code listings (Ch4)
#   make all               # figures, listings, then thesis -- the "fresh clone" build
#   make chapter1           # standalone Chapter 1 manuscript (TubeMethodPaper.pdf)
#   make chapter2            # standalone Chapter 2 manuscript (chapter2goethite.pdf)
#   make clean                # remove LaTeX aux/intermediate files
#   make clean-figures         # remove all Figures/generated/ output
#   make distclean               # clean + clean-figures
#
# Note: this needs a full TeX Live/MacTeX/MiKTeX install with latexmk and
# biber on PATH. All filesystem/orchestration logic below is delegated to
# Python (tools/run_chapter_figures.py, and inline `python -c` for
# clean-figures) rather than shell utilities like rm/[ -f ]/for, because
# native Windows `make` (e.g. the one bundled in a conda env, run from
# PowerShell) invokes cmd.exe as its shell, not a POSIX shell -- so rm,
# test, and POSIX for-loops all fail there with "CreateProcess ... failed".
# Python is portable across Windows/macOS/Linux and already a hard
# dependency of this repo, so it's the common denominator instead.
# ==============================================================================

PYTHON ?= python3
LATEXMK ?= latexmk
LATEXMK_FLAGS := -pdf -interaction=nonstopmode

# Chapters with a figure-generation pipeline under Chapter<N>/Figures/.
# Add a chapter's number here once its pipeline is wired up the same way
# (Figures/{source,generated,data}/ + fig_*.py scripts). Verified for 1-3
# as of this writing; Chapter 4 (DustMAP), Chapter 5 (nGibbs), and
# Chapter A (Draaikraal -- mostly field photos, may never need a real
# pipeline) haven't been confirmed to follow this layout yet.
FIGURE_CHAPTERS := 1 2 3

# figures-ch1/figures-ch2/figures-ch3 are deliberately NOT listed here,
# even though they're conceptually phony too: they only exist via the
# figures-ch% PATTERN rule below, and GNU Make will not fall back to
# implicit/pattern-rule search for a name that already appears as a
# .PHONY prerequisite (that mention alone counts as "an explicit rule
# with no recipe", which wins over pattern matching) -- so declaring them
# phony here silently made "make figures" print "Nothing to be done"
# instead of running anything. They still behave correctly as phony in
# practice without the declaration: nothing ever creates a file actually
# named figures-ch1/2/3, so make always finds them "missing" and reruns
# their recipe regardless.
.PHONY: all thesis figures listings clean clean-figures distclean \
        chapter1 chapter2 dissertation.pdf \
        Chapter1/Writing/TubeMethodPaper.pdf Chapter2/Writing/chapter2goethite.pdf

all: figures listings thesis

# --- Figures ------------------------------------------------------------------

figures: $(foreach n,$(FIGURE_CHAPTERS),figures-ch$(n))

# Delegates to tools/run_chapter_figures.py (see that file for why): it
# prefers Chapter<N>/Figures/run_all_figures.py when present (Chapter 2's
# encodes real ordering dependencies between scripts that must be
# respected) and falls back to running every fig_*.py directly otherwise
# (currently Chapter 3, which has no orchestrator yet).
figures-ch%:
	$(PYTHON) tools/run_chapter_figures.py Chapter$*

# Scripts reproduced verbatim in the thesis (\lstinputlisting) whose printed
# output and figures sit under the code. run_cached_listing.py caches each to
# Chapter4/Figures/generated/<stem>/ and skips the rerun while the script's
# source hash is unchanged, so this is cheap to call every time. Needs the
# environment with petthermotools/nGibbs (PYTHON=... make listings).
LISTING_SCRIPTS := nGibbsPhaseDiagram.py

listings:
	cd Chapter4/Figures && $(PYTHON) run_cached_listing.py $(LISTING_SCRIPTS)

# --- LaTeX ----------------------------------------------------------------------

thesis: dissertation.pdf

# .PHONY (declared above), not a real prerequisite list, because
# dissertation.tex \input{}s ~10 chapter-level files, each of which in
# turn \input{}s dozens more (chapter bodies, abstracts, derived-value
# macro files, tables, SI documents...). Enumerating that whole tree by
# hand here would be both impractical and guaranteed to drift out of
# date as chapters change. latexmk already solves exactly this problem
# properly: it tracks every file it actually reads via its own
# .fdb_latexmk database from the previous run, and only redoes the
# passes that are actually needed -- so letting it run every time and
# decide for itself is both correct and still fast when nothing changed.
# Without .PHONY here, Make's own (necessarily incomplete) up-to-date
# check silently skipped real rebuilds -- e.g. editing a chapter body
# .tex file with no change to dissertation.tex itself left "make thesis"
# quietly serving a stale PDF with no warning that anything was wrong.
dissertation.pdf:
	$(LATEXMK) $(LATEXMK_FLAGS) dissertation.tex

chapter1: Chapter1/Writing/TubeMethodPaper.pdf

# Same reasoning as dissertation.pdf above.
Chapter1/Writing/TubeMethodPaper.pdf:
	cd Chapter1/Writing && $(LATEXMK) $(LATEXMK_FLAGS) TubeMethodPaper.tex

chapter2: Chapter2/Writing/chapter2goethite.pdf

# Same reasoning as dissertation.pdf above.
Chapter2/Writing/chapter2goethite.pdf:
	cd Chapter2/Writing && $(LATEXMK) $(LATEXMK_FLAGS) chapter2goethite.tex

# --- Cleanup ----------------------------------------------------------------------

clean:
	$(LATEXMK) -c dissertation.tex
	-cd Chapter1/Writing && $(LATEXMK) -c TubeMethodPaper.tex SI.tex
	-cd Chapter2/Writing && $(LATEXMK) -c chapter2goethite.tex chapter2goethite_SI.tex

# Portable rmtree via python -c instead of `rm -rf` (see header note).
clean-figures:
	$(PYTHON) -c "import shutil, sys; [shutil.rmtree(p, ignore_errors=True) for p in sys.argv[1:]]" $(foreach n,$(FIGURE_CHAPTERS),Chapter$(n)/Figures/generated)

distclean: clean clean-figures
