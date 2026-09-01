"""
Shared matplotlib style for dissertation figures.

This module is duplicated (byte-identical) into each chapter's Figures/
directory rather than imported from one shared location, so that every
chapter's figure scripts stay standalone and independently runnable/
debuggable (per the dissertation's chapter-by-chapter workspace layout).
If you tune the sizes below, copy the updated file into every chapter
that uses it (currently Chapter1/Paper/Figures, Chapter2/Workspace/Figures,
and Chapter3) so the whole dissertation stays visually consistent.

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

BASE_FIGWIDTH_IN = 6.4  # matplotlib default figure width, used as the
                         # reference scale=1.0 point for this style.

# Sizes (points) tuned to be legible once printed at 8.3 cm width from
# a 6.4 x 4.8 in default-sized figure.
TITLE_SIZE = 16
LABEL_SIZE = 14
TICK_SIZE = 12
LEGEND_SIZE = 11
SUPTITLE_SIZE = 16


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
