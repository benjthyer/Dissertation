"""
Builds the Chapter 5 SI field-photo album (Writing/chapter5_photo_album.tex)
from the raw field photos and the Word caption document.

Inputs
  Figures/source/Draaikraal_Photos/DrBV<n>.jpg      full-resolution originals
  Workspace/Draaikraal Photo Captions.docx          "<n>: caption" paragraphs
Outputs
  Figures/generated/field_photos/DrBV<n>.jpg        print-resolution copies
  Writing/chapter5_photo_album.tex                  AUTO-GENERATED album

Layout: one "plate" per page, as in a journal photo plate: photos numbered
beneath, then their captions in balanced columns, each caption starting with
its bold photo number. Landscape-orientation (wide) photos go on portrait
pages, up to three rows of two; portrait-orientation (tall) photos are
gathered at the end of the album on landscape pages, up to three side by
side at ~2.7 in high with their captions in three columns beneath, instead
of being shrunk into a 16:9 slot. (Four per page with four caption columns
was tried; with these captions only three fitted anyway.) TeX itself decides
how much goes on each page (\\ChFiveLayout, below): it grows each plate one
item at a time in a box while it still fits, so caption edits never need
re-tuning here. (Earlier layouts -- each caption directly under its own
photo, and an all-landscape album -- left most pages half empty: a landscape
page between Caltech's 1.5 in side margins is only ~5.5 in tall.)
Every photo carries a hyperref anchor (ch5-photo-<n>), so \\ChFivePhoto{<n>}
anywhere in the chapter links here.

Caption-document conventions honoured:
  * "16-17:", "25 and 26:", "72-75:" -- one caption shared by several photos;
    it is printed under the first, and the others point back to it.
  * Captions set in italics in Word are the "for-fun" (non-geological) photos
    and stay italic here; italic runs inside a roman caption become \\emph.
  * A paragraph without a leading number continues the previous caption.
  * Captions after the "The following photos are not geolocated." line are
    tagged as such. Parsing stops at "Works Cited" (those references are in
    references.bib and cited via \\citet/\\citep -- see CITATIONS below).
Photos without a caption get a \\todo; captions without a photo get a
placeholder frame (drop the JPG into Draaikraal_Photos and rerun).

Downsampling: long edge 1400 px (~480 dpi at the printed width), JPEG q=82,
EXIF orientation applied, EXIF (incl. GPS) stripped. Only redone when the
source is newer than the copy.

Regenerate after editing the captions or adding photos:
    python3 Chapter5/Figures/write_chapter5_photo_album.py
Requires python-docx and Pillow.
"""
import os
import re
import sys

import docx
from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ch5_photo_refs import link_photo_refs  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CH5 = os.path.normpath(os.path.join(HERE, '..'))
SRC_DIR = os.path.join(HERE, 'source', 'Draaikraal_Photos')
OUT_DIR = os.path.join(HERE, 'generated', 'field_photos')
DOCX = os.path.join(CH5, 'Workspace', 'Draaikraal Photo Captions.docx')
OUT_TEX = os.path.join(CH5, 'Writing', 'chapter5_photo_album.tex')
# path as seen by LaTeX (compiled from the repository root)
TEX_IMG_DIR = 'Chapter5/Figures/generated/field_photos'

LONG_EDGE = 1400
QUALITY = 82

# --- citations in the captions -> natbib commands ----------------------------
# Applied in order to the LaTeX-escaped caption text. Each pattern is reported
# if it no longer matches anything (e.g. after the Word file is edited).
CITATIONS = [
    ('Mitchell and Scoon, 2023 argue .',
     r'\citet{mitchell2023} argue \todo{sentence left unfinished in the caption document}.'),
    ('(UG-1 stringers are below: Voordouw et al., 2009; Mukherjee et al., 2017)',
     r'(UG-1 stringers are below: \citealp{voordouw2009,mukherjee2017})'),
    ('(Voordouw et al., 2009; Mukherjee et al., 2017)', r'\citep{voordouw2009,mukherjee2017}'),
    ('(Van De Merwe, 2007; Latypov et al., 2022)', r'\citep{vandermerwe2007,latypovetal2022}'),
    ('(Von Gruenewaldt et al., 1985; SACS, 1980)', r'\citep{vongruenewaldt1985,sacs1980}'),
    ('(Leelo Mt gabbronorite: Von Gruenewaldt et al., 1985)',
     r'(Leelo Mt gabbronorite: \citealp{vongruenewaldt1985})'),
    ('(see zircon geochronology: Mungall et al., 2016; Scoates et al., 2021)',
     r'(see zircon geochronology: \citealp{mungall2016,scoates2021})'),
    ('(Coleman et al., 2004; Bartley et al., 2006; Scoon and Mitchell, 2023).',
     r'\citep{coleman2004,bartley2006,scoon2023}. '),
    ('(Cameron, 1982)', r'\citep{cameron1982}'),
    # "Cawthorn, 2016" in the caption document; the same claim is cited to
    # cawthorn2015 (Layered Intrusions chapter) in the chapter text.
    ('(Cawthorn, 2016)', r'\citep{cawthorn2015}'),
    ('as in the model of Lee and Sharpe, 1979.', r'as in the model of \citet{lee1979}.'),
    # caption 10: the opening parenthesis is never closed in the Word file
    ('magma (Khoza, 2021, suggesting', r'magma \citep{khoza2021}, suggesting'),
    ('most famously by Sharpe, 1981.', r'most famously by \citet{sharpe1981}.'),
    ('(Mitchell and Scoon, 2023)', r'\citep{mitchell2023}'),
    ('(Cawthorn, 1998)', r'\citep{cawthorn1998}'),
    ('(Webb et al., 2004)', r'\citep{webb2004}'),
    ('(Van de Merwe, 2007)', r'\citep{vandermerwe2007}'),
    ('Van De Merwe (2007)', r'\citet{vandermerwe2007}'),
    ('(Kinnaird et al., 2005)', r'\citep{kinnaird2005}'),
    ('(Merwe, 2007)', r'\citep{vandermerwe2007}'),
    ('Maier et al. (2020)', r'\citet{maier2020}'),
    ('Latypov et al., 2022', r'\citet{latypovetal2022}'),
    ('(Molyneux, 2008)', r'\citep{molyneux2008}'),
    ('(Hill, 1990)', r'\citep{hill1990}'),
    ('Khoza (2021)', r'\citet{khoza2021}'),
    ('Lee and Sharpe (1979)', r'\citet{lee1979}'),
    ('Mitchell and Scoon (2023)', r'\citet{mitchell2023}'),
]

HEAD_RE = re.compile(r'^\s*(\d+)\s*(?:(?:-|\u2013|and|&)\s*(\d+))?\s*:\s*')


# --- images --------------------------------------------------------------------
def photo_numbers():
    nums = []
    for f in os.listdir(SRC_DIR):
        m = re.fullmatch(r'DrBV(\d+)\.jpe?g', f, re.I)
        if m:
            nums.append((int(m.group(1)), f))
    return dict(nums)


def downsample(n, fname):
    src = os.path.join(SRC_DIR, fname)
    dst = os.path.join(OUT_DIR, f'DrBV{n}.jpg')
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return dst, False
    im = Image.open(src)
    im.draft('RGB', (LONG_EDGE, LONG_EDGE))   # fast DCT-domain pre-scaling
    im = ImageOps.exif_transpose(im)
    im = im.convert('RGB')
    im.thumbnail((LONG_EDGE, LONG_EDGE), Image.LANCZOS)
    im.save(dst, 'JPEG', quality=QUALITY, optimize=True, progressive=True)
    return dst, True


# --- captions --------------------------------------------------------------------
def tex_escape(s):
    out = []
    for ch in s:
        out.append({
            '\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '&': r'\&',
            '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
            '~': r'$\sim$', '^': r'\textasciicircum{}',
            '<': r'$<$', '>': r'$>$',
        }.get(ch, ch))
    return ''.join(out)


def run_italic(r):
    return bool(r.italic or r.font.italic)


def para_parts(p):
    """[(text, italic)] for the paragraph's non-empty runs, adjacent runs of
    equal style merged."""
    parts = []
    for r in p.runs:
        if not r.text:
            continue
        it = run_italic(r)
        if parts and parts[-1][1] == it:
            parts[-1] = (parts[-1][0] + r.text, it)
        else:
            parts.append((r.text, it))
    return parts


def parse_captions():
    d = docx.Document(DOCX)
    caps = []           # dicts: first, last, paras(list of parts), italic, geoloc
    geoloc = True
    started = False
    for p in d.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        if text.lower().startswith('works cited'):
            break
        if text.lower().startswith('the following photos are not geolocated'):
            geoloc = False
            continue
        m = HEAD_RE.match(text)
        parts = para_parts(p)
        if m:
            started = True
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            # strip the "<n>:" header from the first part(s)
            cut = m.end()
            # header length measured on the joined raw text
            raw = ''.join(t for t, _ in parts)
            lead = len(raw) - len(raw.lstrip())
            cut += lead
            new, seen = [], 0
            for t, it in parts:
                if seen + len(t) <= cut:
                    seen += len(t)
                    continue
                new.append((t[max(0, cut - seen):], it))
                seen += len(t)
            chars = [(len(t.strip()), it) for t, it in new]
            tot = sum(c for c, _ in chars) or 1
            ital = sum(c for c, it in chars if it) / tot > 0.5
            caps.append(dict(first=a, last=b, paras=[new], italic=ital, geoloc=geoloc))
        elif started:
            caps[-1]['paras'].append(parts)
        # else: the intro line ("Captions in Italics refer to ...") -- skipped
    return caps


def caption_tex(cap, hits):
    paras = []
    for parts in cap['paras']:
        s = ''
        for t, it in parts:
            e = tex_escape(t)
            if it and not cap['italic'] and e.strip():
                s += r'\emph{' + e + '}'
            else:
                s += e
        s = re.sub(r'\s+', ' ', s).strip()
        paras.append(s)
    s = r' \par '.join(paras)
    for pat, rep in CITATIONS:
        k = s.count(pat)
        if k:
            hits[pat] = hits.get(pat, 0) + k
            s = s.replace(pat, rep)
    # "18-19: See 15."
    s = re.sub(r'^See (\d+)\.$', r'See photo \1.', s)
    s = link_photo_refs(s)
    if not cap['geoloc']:
        s += r' \textit{(Not geolocated.)}'
    if cap['italic']:
        s = r'\itshape ' + s
    # leftover author--year citations that were not converted
    plain = re.sub(r'\\cite\w*\{[^}]*\}', '', s)
    for mm in re.finditer(r'[A-Z][A-Za-z]+[^()]{0,25}?,? \(?(19|20)\d\d\)?', plain):
        print(f'  WARNING: unconverted citation? photo {cap["first"]}: ...{mm.group(0)}...')
    return s


# --- LaTeX ---------------------------------------------------------------------
# Plate machinery (written once at the top of the generated file).
#   \ChFiveDefItem{k}{photos}{captions}  stores plate item k
#   \ChFiveLayout                        lays items 1..\ChFiveItemN out, one
#                                        plate per page, growing each plate
#                                        item by item while it fits the page
# An item is a row of two photos on the portrait pages (joined vertically,
# at most three per plate), or one tall photo on the landscape pages (joined
# side by side, at most three per plate).
MACROS = r"""% =============================================================
%  chapter5_photo_album.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.
%  Written by Chapter5/Figures/write_chapter5_photo_album.py from
%  Workspace/Draaikraal Photo Captions.docx and
%  Figures/source/Draaikraal_Photos/ (downsampled copies in
%  Figures/generated/field_photos/). Edit the Word file and rerun:
%    python3 Chapter5/Figures/write_chapter5_photo_album.py
%  \input{} by Chapter5/Writing/chapter5_SI_body.tex. Needs multicol,
%  pdflscape.
% =============================================================
\providecommand{\phantomsection}{}
\providecommand{\ChFivePhoto}[1]{#1}
\newlength{\ChFivePhotoW}
\newlength{\ChFivePhotoH}
\newcommand{\ChFivePhotoBox}[2]{%  {n}{image or placeholder}
  \begin{minipage}[t]{\ChFivePhotoW}\centering
  \parbox[c][\ChFivePhotoH][c]{\ChFivePhotoW}{\centering #2}\\[1pt]
  {\scriptsize\bfseries\phantomsection\label{ch5-photo-#1}#1}
  \end{minipage}}
\newcommand{\ChFivePhotoEmpty}{\begin{minipage}[t]{\ChFivePhotoW}\mbox{}\end{minipage}}
\newcommand{\ChFivePhotoMissing}[1]{%
  \fcolorbox{gray}{white}{\parbox[c][0.8\ChFivePhotoH][c]{0.8\ChFivePhotoW}{%
    \centering\color{gray}\scriptsize DrBV#1.jpg not in\\ Draaikraal\_Photos}}}
\newcommand{\ChFiveCapCols}{2}
\newenvironment{ChFivePhotoCaptions}{%
  \par\vspace{6pt}\begin{multicols}{\ChFiveCapCols}\scriptsize\raggedright
  \setlength{\parskip}{2.5pt}\setlength{\parindent}{0pt}}{\end{multicols}}
\newcommand{\ChFiveDefItem}[3]{%
  \expandafter\def\csname ChFiveItemP#1\endcsname{#2}%
  \expandafter\def\csname ChFiveItemC#1\endcsname{#3}}
\newcommand{\ChFiveJoin}{\par\vspace{4pt}}   % between items of a plate
\newcommand{\ChFiveMaxItems}{3}              % items per plate at most
\newcommand{\ChFivePre}{}\newcommand{\ChFivePost}{}  % around a plate's photos
\newcount\ChFiveItemN
\newcount\ChFiveItemI
\newcount\ChFiveItemJ
\newcount\ChFiveItemK
\newsavebox\ChFivePlateBox
\newsavebox\ChFiveTrialBox
\newif\ifChFiveGrow
\newcommand{\ChFiveMakePlate}[2]{%  items {first}..{last}
  \begin{minipage}[t]{\linewidth}\setlength{\parindent}{0pt}%
  \noindent\ChFivePre
  \ChFiveItemK=#1\relax
  \loop
    \csname ChFiveItemP\the\ChFiveItemK\endcsname
    \ifnum\ChFiveItemK<#2 \ChFiveJoin\fi
    \advance\ChFiveItemK by 1
  \ifnum\ChFiveItemK<\numexpr#2+1\relax\repeat
  \ChFivePost
  \begin{ChFivePhotoCaptions}%
  \ChFiveItemK=#1\relax
  \loop
    \csname ChFiveItemC\the\ChFiveItemK\endcsname
    \advance\ChFiveItemK by 1
  \ifnum\ChFiveItemK<\numexpr#2+1\relax\repeat
  \end{ChFivePhotoCaptions}\end{minipage}}
% room left on the current page (glue above a box placed mid-page included)
\newcommand{\ChFiveRoom}{\dimexpr\textheight-\pagetotal-4pt
  \ifdim\pagetotal>0pt -2\baselineskip-\parskip\fi\relax}
\newcommand{\ChFiveLayout}{%
  \ChFiveItemI=1
  \loop
    \par\penalty0 % runs TeX's page builder, so \pagetotal is current
    \global\ChFiveItemJ=\ChFiveItemI
    \global\setbox\ChFivePlateBox\hbox{\ChFiveMakePlate{\the\ChFiveItemI}{\the\ChFiveItemJ}}%
    % the first plate may share its page with the text before the album;
    % if not even one item fits in what is left there, start a fresh page
    \ifdim\pagetotal>0pt
      \ifdim\dimexpr\ht\ChFivePlateBox+\dp\ChFivePlateBox\relax>\ChFiveRoom
        \newpage
      \fi
    \fi
    \ChFiveTryGrow
    \noindent\usebox\ChFivePlateBox\par\newpage
    \ChFiveItemI=\numexpr\ChFiveItemJ+1\relax
  \ifnum\ChFiveItemI<\numexpr\ChFiveItemN+1\relax
  \repeat}
\newcommand{\ChFiveTryGrow}{\begingroup
  \loop
    \global\ChFiveGrowfalse
    \ifnum\ChFiveItemJ<\ChFiveItemN
      \ifnum\numexpr\ChFiveItemJ-\ChFiveItemI+1\relax<\ChFiveMaxItems\relax
        \setbox\ChFiveTrialBox\hbox{\ChFiveMakePlate{\the\ChFiveItemI}{\the\numexpr\ChFiveItemJ+1\relax}}%
        \ifdim\dimexpr\ht\ChFiveTrialBox+\dp\ChFiveTrialBox\relax<\ChFiveRoom
          \global\advance\ChFiveItemJ by 1
          \global\setbox\ChFivePlateBox\copy\ChFiveTrialBox
          \global\ChFiveGrowtrue
        \fi
      \fi
    \fi
  \ifChFiveGrow\repeat
  \endgroup}
"""

# Wide (landscape-orientation) photos: portrait pages, rows of two.
WIDE_SETUP = r"""
\par
\begingroup
\setlength{\parindent}{0pt}
\setlength{\columnsep}{0.04\linewidth}
\setlength{\multicolsep}{0pt}
\setlength{\ChFivePhotoW}{\dimexpr(\linewidth-\columnsep)/2\relax}
\setlength{\ChFivePhotoH}{0.5625\ChFivePhotoW}% 16:9
\renewcommand{\ChFiveCapCols}{2}
\renewcommand{\ChFiveJoin}{\par\vspace{4pt}\noindent}
\renewcommand{\ChFiveMaxItems}{3}
"""
WIDE_END = '\\endgroup\n\\clearpage\n'

# Tall (portrait-orientation) photos: landscape pages, up to three side by side.
TALL_SETUP = r"""
\begin{landscape}
\setlength{\parindent}{0pt}
\setlength{\columnsep}{0.025\linewidth}
\setlength{\multicolsep}{0pt}
\setlength{\ChFivePhotoW}{\dimexpr(\linewidth-2\columnsep)/3\relax}
\setlength{\ChFivePhotoH}{0.5\textheight}
\renewcommand{\ChFiveCapCols}{3}
\renewcommand{\ChFiveJoin}{\hfill}
\renewcommand{\ChFivePre}{\hspace*{\fill}}%  fewer than four photos: spread evenly
\renewcommand{\ChFivePost}{\hspace*{\fill}}
\renewcommand{\ChFiveMaxItems}{3}
"""
TALL_END = '\\end{landscape}\n'


def photo_tex(n, have_photo):
    if have_photo:
        img = (r'\includegraphics[width=\ChFivePhotoW,height=\ChFivePhotoH,'
               rf'keepaspectratio]{{{TEX_IMG_DIR}/DrBV{n}.jpg}}')
    else:
        img = rf'\ChFivePhotoMissing{{{n}}}'
    return rf'\ChFivePhotoBox{{{n}}}{{{img}}}'


def caption_par(label, body):
    return '{' + rf'\textbf{{{label}}} {body}' + r'\par}'


def items_tex(items):
    """items: list of (photos_tex, captions_tex) -> \\ChFiveDefItem lines."""
    out = []
    for k, (p, c) in enumerate(items, 1):
        out.append(f'\\ChFiveDefItem{{{k}}}\n{{{p}}}\n{{{c}}}')
    return '\n\n'.join(out) + f'\n\n\\ChFiveItemN={len(items)}\n\\ChFiveLayout\n'


def fmt_list(ns):
    ns = [rf'\ChFivePhoto{{{n}}}' for n in ns]
    return ns[0] if len(ns) == 1 else ', '.join(ns[:-1]) + (', and ' if len(ns) > 2 else ' and ') + ns[-1]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    photos = photo_numbers()
    redone, tall = 0, set()
    for n, f in sorted(photos.items()):
        dst, did = downsample(n, f)
        redone += did
        with Image.open(dst) as im:
            if im.height > im.width:
                tall.add(n)
    print(f'{len(photos)} photos ({redone} downsampled this run) -> {OUT_DIR}')
    print(f'  portrait-orientation photos: {sorted(tall)}')

    caps = parse_captions()
    by_photo = {}
    for c in caps:
        for n in range(c['first'], c['last'] + 1):
            if n in by_photo:
                print(f'  WARNING: photo {n} has more than one caption')
            by_photo[n] = c
    hits = {}
    tex_of = {id(c): caption_tex(c, hits) for c in caps}
    for pat, _ in CITATIONS:
        if pat not in hits:
            print(f'  NOTE: citation pattern no longer found: {pat!r}')

    all_n = sorted(set(photos) | set(by_photo))
    cells = {}
    no_caption, no_photo = [], []
    for n in all_n:
        c = by_photo.get(n)
        if c is None:
            no_caption.append(n)
            label, body = f'Photo {n}.', r'\todo{No caption for this photo in the caption document.}'
        elif c['first'] == n:
            label = (f'Photo {n}.' if c['last'] == n else
                     f'Photos {c["first"]}\\textendash{c["last"]}.')
            body = tex_of[id(c)]
        else:
            label = f'Photo {n}.'
            body = (r'\textit{See the caption of photo~\ChFivePhoto{' + str(c['first']) + '}.}')
        if n not in photos:
            no_photo.append(n)
        cells[n] = (photo_tex(n, n in photos), caption_par(label, body))

    wide_n = [n for n in all_n if n not in tall]
    tall_n = [n for n in all_n if n in tall]
    wide_items = []
    for i in range(0, len(wide_n), 2):
        row = wide_n[i:i + 2]
        ps = [cells[n][0] for n in row] + [r'\ChFivePhotoEmpty'] * (2 - len(row))
        wide_items.append(('\\hfill\n'.join(ps), '\n'.join(cells[n][1] for n in row)))
    tall_items = [(cells[n][0], cells[n][1]) for n in tall_n]

    parts = [MACROS]
    if tall_n:
        parts.append(f'Photographs taken in portrait orientation (photos~{fmt_list(tall_n)}) '
                     'are gathered on landscape pages at the end of the album, so that they '
                     'print at full height.\n')
    parts += [WIDE_SETUP, items_tex(wide_items), WIDE_END]
    if tall_n:
        parts += [TALL_SETUP, items_tex(tall_items), TALL_END]
    with open(OUT_TEX, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
    print(f'Wrote {OUT_TEX}: {len(wide_n)} wide + {len(tall_n)} tall photos, {len(caps)} captions')
    print(f'  photos without a caption: {no_caption}')
    print(f'  captions without a photo: {no_photo}')
    print(f'  italic (for-fun) captions: {[c["first"] for c in caps if c["italic"]]}')


if __name__ == '__main__':
    main()
