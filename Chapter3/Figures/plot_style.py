"""
Shared matplotlib style for dissertation figures.

This module is duplicated (byte-identical) into each chapter's Figures/
directory rather than imported from one shared location, so that every
chapter's figure scripts stay standalone and independently runnable/
debuggable (per the dissertation's chapter-by-chapter workspace layout).
If you tune the sizes below, copy the updated file into every chapter
that uses it (currently Chapter1/Figures, Chapter2/Figures,
and Chapter3/Figures) so the whole dissertation stays visually consistent.

NOTE (this copy only): at the user's request, this Chapter3/Figures copy
was deliberately bumped to larger non-legend sizes than Chapter1/Figures
and Chapter2/Figures's copies (Ch3's in-plot text -- titles, axis labels,
tick labels -- was reported too small; legends were reported fine and are
unchanged). Chapter 1 and 2's copies were intentionally left at the
original sizes below. Do NOT copy this file's sizes back into those
chapters without checking with the user first -- the three copies are no
longer expected to be identical.

All figures using this style are generated at matplotlib's default
figure size (6.4 x 4.8 in, i.e. a bare `plt.subplots()`/`plt.figure()`
call with no `figsize=` argument) and are then placed in the LaTeX
manuscript at a fixed printed width of 8.3 cm. Because every figure is
scaled down to the *same* final width, using the *same* absolute font
sizes (in points) across all scripts is what makes the text come out
a consistent, legible size on the page -- matplotlib's own defaults
were never set with this much shrinkage in mind, which is why figures
previously looked inconsistent (a handful of scripts had manually tuned
legend sizes down to 7-8 pt to squeeze in crowded legends, while most
titles/labels were left at matplotlib's small defaults).

Usage: import this module and call `apply_style()` once near the top
of a figure script, before creating any figures:

    from plot_style import apply_style
    apply_style()

For a figure built at a non-default figsize (wider or taller than the
6.4 x 4.8 in baseline), call `apply_style(scale=W/6.4)` where W is
that figure's width in inches, so its fonts are enlarged by the same
factor it will be additionally shrunk by when placed at 8.3 cm. This
is only needed for `fig_predicting_permeation.py`'s two multi-panel
histogram figures (figsize=(8,10) and (8,8), i.e. scale ~1.25).
"""
import matplotlib as mpl
import numpy as np

BASE_FIGWIDTH_IN = 6.4  # matplotlib default figure width, used as the
                         # reference scale=1.0 point for this style.

# Sizes (points) tuned to be legible once printed at 8.3 cm width from
# a 6.4 x 4.8 in default-sized figure.
# Chapter 3 only (see NOTE above): TITLE/LABEL/TICK/SUPTITLE bumped up from
# the original 16/14/12/16 at the user's request; LEGEND_SIZE left at its
# original value since legends were reported as already fine.
TITLE_SIZE = 20
LABEL_SIZE = 17
TICK_SIZE = 15
LEGEND_SIZE = 11
SUPTITLE_SIZE = 20


def apply_style(scale: float = 1.0) -> None:
    """Apply the shared, legible font-size scheme to matplotlib rcParams.

    Parameters
    ----------
    scale : float
        Multiplier applied to all sizes below. Use scale=1.0 (default)
        for any figure built at matplotlib's default figsize. For a
        figure built wider than 6.4 in, pass scale=width_in/6.4 so its
        text ends up the same apparent size once both figures are
        placed at the same final printed width in the manuscript.
    """
    mpl.rcParams.update({
        'font.size': LABEL_SIZE * scale,
        'axes.titlesize': TITLE_SIZE * scale,
        'axes.labelsize': LABEL_SIZE * scale,
        'xtick.labelsize': TICK_SIZE * scale,
        'ytick.labelsize': TICK_SIZE * scale,
        'legend.fontsize': LEGEND_SIZE * scale,
        'figure.titlesize': SUPTITLE_SIZE * scale,
    })


# Chapter 3 only: the sulfide step-heat "treatment as uncertainty" reduction
# (Chapter3/Tables/build_plotable_cache.py, from the Reduced01_*.xlsx
# workbooks) sometimes can't compute a real lower bound on ln(D/a^2) -- the
# permeation-lag correction leaves the diffusivity consistent with zero --
# and the workbook stands in an arbitrary LB_dln(d/a^2) = 5 sentinel for
# "unconstrained" rather than a real 5-natural-log-unit uncertainty. Plotted
# literally, that produces a giant, physically meaningless whisker. The
# upper bound never hits this sentinel (checked across the whole cache), so
# only the lower side needs this treatment.
LB_SENTINEL_THRESHOLD = 4.9  # matches the workbook's literal 5 (one point at 5.09), safely above any real uncertainty seen in this dataset


def diffusivity_errorbar(ax, x, y, lb, ub, color, marker, label=None,
                          ghost_alpha=0.25, normal_alpha=0.7, capsize=4,
                          markersize=5, arrow_length=1.3, linestyle='none',
                          zorder=2, **kwargs):
    """Plot ln(D/a^2) (or a delta of it) with asymmetric LB/UB error bars,
    routing points whose LB_dln(d/a^2) hits the workbook's unconstrained-
    lower-bound sentinel (see LB_SENTINEL_THRESHOLD above) to a distinct
    low-alpha "ghost" style instead of either a giant -5 whisker or
    silently dropping the point -- some of these are real regression-
    window steps (e.g. step 31 of the CCp chalcopyrite fit), so dropping
    them would make a "point used in regression" vanish from its own
    Arrhenius plot even though the fit itself (which only uses the
    central value) is unaffected either way.

    Normal points get a standard two-sided errorbar at normal_alpha.
    Ghost points get a low-alpha marker, a normal (upper-only) whisker if
    UB is itself finite, and a short low-alpha downward arrow standing in
    for the open-ended lower bound.

    Returns the number of ghost points plotted (for a caller that wants
    to e.g. add a "n unconstrained" note).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    lb = np.asarray(lb, dtype=float)
    ub = np.asarray(ub, dtype=float)
    ghost = lb >= LB_SENTINEL_THRESHOLD
    normal = ~ghost

    if normal.any():
        yerr = np.clip(np.vstack([lb[normal], ub[normal]]), 0, None)
        ax.errorbar(x[normal], y[normal], yerr=yerr, fmt=marker, color=color,
                    ecolor=color, capsize=capsize, alpha=normal_alpha,
                    markersize=markersize, markeredgecolor='black', markeredgewidth=0.4,
                    linestyle=linestyle, zorder=zorder, label=label, **kwargs)

    if ghost.any():
        ub_ghost = np.clip(ub[ghost], 0, None)
        ax.errorbar(x[ghost], y[ghost], yerr=np.vstack([np.zeros(int(ghost.sum())), ub_ghost]),
                    fmt=marker, color=color, ecolor=color, capsize=capsize,
                    alpha=ghost_alpha, markersize=markersize, linestyle=linestyle,
                    zorder=zorder, label=(None if normal.any() else label), **kwargs)
        for xi, yi in zip(x[ghost], y[ghost]):
            ax.annotate('', xy=(xi, yi - arrow_length), xytext=(xi, yi),
                        arrowprops=dict(arrowstyle='-|>', color=color, alpha=ghost_alpha, lw=1.2),
                        zorder=zorder)

    return int(ghost.sum())
