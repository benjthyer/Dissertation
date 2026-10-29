"""
Shared helper for Chapter 5: turn plain-text photo references ("photo 95",
"photos 61,62, 72-78", "picture 106") into \\ChFivePhoto{N} hyperlinks to
the field-photo album in the Chapter 5 SI.

Used by write_chapter5_photo_album.py (for cross-references inside the
captions themselves). It was also run once over Writing/chapter5_body.tex
when the album was added (2026-10-24); new prose can simply write
photo~\\ChFivePhoto{N} by hand.
"""
import re

# Field photos left out of the album and the station table (2026-10-27, at the
# author's request): photographs without geological content (1, 7, 20, 31, 33,
# 56, 83) and uncaptioned frames (9, 39, 43-47). Their DrBV<n>.jpg files stay
# in Figures/source/Draaikraal_Photos; the remaining photos keep their field
# numbers, so the album's numbering has gaps.
EXCLUDED_PHOTOS = frozenset({1, 7, 9, 20, 31, 33, 39, 43, 44, 45, 46, 47, 56, 83})

# The thesis reproduces only these photos (Appendix A photo album, two per page,
# in order of first citation in Chapter 5, portrait photos last); the others go
# to the separate supplementary photo album (Chapter5/chapter5_photo_supplement.tex).
# Author's selection, 2026-10-27.
APPENDIX_PHOTOS = frozenset({111, 53, 29, 59, 61, 62, 65, 66, 72, 76, 77, 4, 2, 95,
                             96, 98, 100, 86, 87, 90, 49, 109})
# 2026-10-28: 119 -> supplement. 2026-10-29: 86, 87, 90 back from the (removed)
# anorthosite mosaic, plus 49 and 109 from it.
# Photos shown as main-text figures instead: photo -> figure label.
MAIN_TEXT_PHOTOS = {60: 'fig:ch5-photo60-deformation',
                    115: 'fig:ch5-ma-cleavage-photo'}   # annotated photo 115 (Results)

_NUM = r'\d{1,3}'
_ITEM = rf'{_NUM}(?:\s*[-–]\s*{_NUM})?'
_SEP = r'(?:\s*,\s*and\s+|\s*,\s*|\s+and\s+|\s*&\s*|\s+)'
# The list after "photo(s)" is a run of items separated by commas/"and".
# A bare-space separator is only accepted when the next token is another
# number (handles "photos 61,62, 72-78"), never a word.
PHOTO_LIST_RE = re.compile(
    rf'\b(?P<word>[Pp]hotos?|[Pp]ictures?)(?P<sp>\s+|~)(?P<list>{_ITEM}(?:{_SEP}{_ITEM})*)'
)
_ITEM_RE = re.compile(rf'({_NUM})(\s*[-–]\s*)({_NUM})|({_NUM})')


def _link_list(lst, max_photo):
    def one(m):
        if m.group(4):
            n = int(m.group(4))
            return rf'\ChFivePhoto{{{n}}}' if 1 <= n <= max_photo else m.group(0)
        a, b = int(m.group(1)), int(m.group(3))
        if not (1 <= a < b <= max_photo):
            return m.group(0)
        return rf'\ChFivePhoto{{{a}}}--\ChFivePhoto{{{b}}}'
    return _ITEM_RE.sub(one, lst)


def link_photo_refs(text, max_photo=125):
    def repl(m):
        lst = m.group('list')
        # trim a trailing bare-space separator that the greedy match may have
        # swallowed (e.g. "photo 51 3" is not a list) -- only keep items
        # joined by space if the joined token is a number
        return m.group('word') + '~' + _link_list(lst, max_photo)
    return PHOTO_LIST_RE.sub(repl, text)
