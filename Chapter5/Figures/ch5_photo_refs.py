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
