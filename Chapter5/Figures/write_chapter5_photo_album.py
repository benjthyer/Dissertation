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
    it is printed once, with the first of them (labelled "Photos 16-17"), and
    the group is kept on the same pages even if it mixes orientations.
  * Photos in ch5_photo_refs.EXCLUDED_PHOTOS are left out altogether.
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
from ch5_spelling import fix as fix_spelling  # noqa: E402
from ch5_photo_refs import (APPENDIX_PHOTOS, EXCLUDED_PHOTOS,  # noqa: E402
                            MAIN_TEXT_PHOTOS, link_photo_refs)

HERE = os.path.dirname(os.path.abspath(__file__))
CH5 = os.path.normpath(os.path.join(HERE, '..'))
SRC_DIR = os.path.join(HERE, 'source', 'Draaikraal_Photos')
OUT_DIR = os.path.join(HERE, 'generated', 'field_photos')
DOCX = os.path.join(CH5, 'Workspace', 'Draaikraal Photo Captions.docx')
OUT_TEX = os.path.join(CH5, 'Writing', 'chapter5_photo_album.tex')            # Appendix A
OUT_INDEX = os.path.join(CH5, 'Writing', 'chapter5_photo_index.tex')          # thesis links
OUT_SUPP = os.path.join(CH5, 'Writing', 'chapter5_photo_supplement_album.tex')
OUT_SUPP_INDEX = os.path.join(CH5, 'Writing', 'chapter5_photo_supplement_index.tex')
BODY_TEX = os.path.join(CH5, 'Writing', 'chapter5_body.tex')
# path as seen by LaTeX (compiled from the repository root)
TEX_IMG_DIR = 'Chapter5/Figures/generated/field_photos'

LONG_EDGE = 1400
QUALITY = 82

# --- citations in the captions -> natbib commands ----------------------------
# Applied in order to the LaTeX-escaped caption text. Each pattern is reported
# if it no longer matches anything (e.g. after the Word file is edited).
CITATIONS = [
    ('(Mitchell and Scoon, 2023)',
     r'\citep{mitchell2023}'),
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
    s = fix_spelling(s)
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
    photos = {n: f for n, f in photo_numbers().items() if n not in EXCLUDED_PHOTOS}
    print(f'  left out (EXCLUDED_PHOTOS in ch5_photo_refs.py): {sorted(EXCLUDED_PHOTOS)}')
    redone, tall = 0, set()
    for n, f in sorted(photos.items()):
        dst, did = downsample(n, f)
        redone += did
        with Image.open(dst) as im:
            if im.height > im.width:
                tall.add(n)
    print(f'{len(photos)} photos ({redone} downsampled this run) -> {OUT_DIR}')
    print(f'  portrait-orientation photos: {sorted(tall)}')

    caps = [c for c in parse_captions()
            if not set(range(c['first'], c['last'] + 1)) <= EXCLUDED_PHOTOS]
    by_photo = {}
    for c in caps:
        for n in range(c['first'], c['last'] + 1):
            if n in EXCLUDED_PHOTOS:
                continue
            if n in by_photo:
                print(f'  WARNING: photo {n} has more than one caption')
            by_photo[n] = c
    hits = {}
    tex_of = {id(c): caption_tex(c, hits) for c in caps}
    for pat, _ in CITATIONS:
        if pat not in hits:
            print(f'  NOTE: citation pattern no longer found: {pat!r}')

    all_n = sorted(set(photos) | set(by_photo))
    in_app = sorted(n for n in all_n if n in APPENDIX_PHOTOS and n not in MAIN_TEXT_PHOTOS)
    in_supp = [n for n in all_n if n not in APPENDIX_PHOTOS and n not in MAIN_TEXT_PHOTOS]
    missing = sorted(APPENDIX_PHOTOS - set(all_n))
    if missing:
        print(f'  WARNING: APPENDIX_PHOTOS not in the album: {missing}')

    # Both albums: two large photos per page, in numerical order, landscape
    # photos first, then portrait photos (author's choice, 2026-10-28).
    def key(n):
        return (n in tall, n)

    # --- Appendix A (in the thesis) ---------------------------------------------
    app_order = sorted(in_app, key=key)
    app_caps = doc_captions(in_app, by_photo, tex_of, tall)
    write_index(OUT_INDEX, {n: f'ch5-photo-{n}' for n in in_app} | dict(MAIN_TEXT_PHOTOS),
                'the thesis (Appendix A album + main-text figures)')
    with open(OUT_TEX, 'w', encoding='utf-8') as f:
        f.write(appendix_tex(app_order, app_caps, tall, photos, APP_HEADER))
    print(f'Wrote {OUT_TEX}: {len(in_app)} photos, order {app_order}')

    # --- supplementary photo album (separate document): everything else ----------
    supp_order = sorted(in_supp, key=key)
    supp_caps = doc_captions(in_supp, by_photo, tex_of, tall)
    write_index(OUT_SUPP_INDEX, {n: f'ch5-photo-{n}' for n in in_supp},
                'the supplementary photo album')
    with open(OUT_SUPP, 'w', encoding='utf-8') as f:
        f.write(appendix_tex(supp_order, supp_caps, tall, photos, SUPP_HEADER))
    print(f'Wrote {OUT_SUPP}: {len(in_supp)} photos '
          f'({sum(n in tall for n in in_supp)} portrait)')
    print(f'  photos without a caption: {[n for n in all_n if n not in by_photo]}')
    print(f'  captions without a photo: {[n for n in all_n if n not in photos]}')
    print(f'  italic (for-fun) captions: {[c["first"] for c in caps if c["italic"]]}')


# --- per-document captions -------------------------------------------------------
def _span(ns):
    if len(ns) == 1:
        return f'photo {ns[0]}', rf'photo~\ChFivePhoto{{{ns[0]}}}'
    if ns == list(range(ns[0], ns[-1] + 1)):
        return (f'photos {ns[0]}\\textendash{ns[-1]}',
                rf'photos~\ChFivePhoto{{{ns[0]}}}--\ChFivePhoto{{{ns[-1]}}}')
    return ('photos ' + ', '.join(map(str, ns)),
            'photos~' + ', '.join(rf'\ChFivePhoto{{{n}}}' for n in ns))


def doc_captions(doc_ns, by_photo, tex_of, tall):
    """n -> (label, body) for the photos of one document (Appendix A or the
    supplement). A caption shared by several photos is printed once, with the
    first of its photos *in this document* in the landscape-photo sequence,
    labelled with just those photos ("Photos 101-102"); every other photo of
    the group here gets a pointer to it (each photo has its own caption slot
    in the two-per-page layout)."""
    doc = set(doc_ns)
    out = {}
    for n in doc_ns:
        c = by_photo.get(n)
        if c is None:
            out[n] = (f'Photo {n}.', r'\todo{No caption for this photo in the caption document.}')
            continue
        grp = [m for m in range(c['first'], c['last'] + 1) if m in doc]
        home = [m for m in grp if m not in tall] or grp
        if n == home[0]:
            txt = _span(home)[0]
            out[n] = (txt[0].upper() + txt[1:] + '.', tex_of[id(c)])
        else:
            out[n] = (f'Photo {n}.', r'\textit{See the caption of ' + _span(home)[1] + '.}')
    return out


def first_mentions():
    """photo -> character offset of its first \ChFivePhoto citation in the
    chapter text (comment lines ignored; ranges count for every photo)."""
    txt = open(BODY_TEX, encoding='utf-8').read()
    txt = '\n'.join('' if l.lstrip().startswith('%') else l for l in txt.split('\n'))
    first = {}
    for m in re.finditer(r'\\ChFivePhoto\{(\d+)\}(?:--\\ChFivePhoto\{(\d+)\})?', txt):
        a = int(m.group(1)); b = int(m.group(2) or a)
        for n in range(a, b + 1):
            first.setdefault(n, m.start())
    return first


def write_index(path, targets, where):
    lines = [
        '% ' + '=' * 61,
        f'%  {os.path.basename(path)} -- AUTO-GENERATED by',
        '%  Chapter5/Figures/write_chapter5_photo_album.py, DO NOT EDIT BY HAND.',
        f'%  Defines \\ChFivePhoto{{N}} for {where}: photo numbers',
        '%  reproduced in this document print as links to them; the others',
        '%  print as plain numbers.',
        '% ' + '=' * 61,
        r'\providecommand{\ChFivePhotoLink}[2]{\ifcsname hyperref\endcsname'
        r'\expandafter\hyperref\expandafter[#1]{#2}\else#2\fi}',
        r'\DeclareRobustCommand{\ChFivePhoto}[1]{%',
        r'  \ifcsname ChFivePhotoTarget-#1\endcsname',
        r'    \expandafter\ChFivePhotoLink\csname ChFivePhotoTarget-#1\endcsname{#1}%',
        r'  \else #1\fi}',
    ]
    for n, lab in sorted(targets.items()):
        lines.append(rf'\expandafter\def\csname ChFivePhotoTarget-{n}\endcsname{{{lab}}}')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Wrote {path}: {len(targets)} link targets')


APP_HEADER = r"""% =============================================================
%  chapter5_photo_album.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.
%  Appendix A photo album: the photos in ch5_photo_refs.APPENDIX_PHOTOS,
%  two large photos per page, in numerical order, landscape photos first
%  and portrait photos after them. Written by
%  Chapter5/Figures/write_chapter5_photo_album.py from
%  Workspace/Draaikraal Photo Captions.docx; rerun it after editing the
%  captions or the selection. The other photos are in
%  chapter5_photo_supplement_album.tex (Chapter5/chapter5_photo_supplement.tex).
% =============================================================
"""
SUPP_HEADER = r"""% =============================================================
%  chapter5_photo_supplement_album.tex -- AUTO-GENERATED, DO NOT EDIT BY HAND.
%  Supplementary photo album: every kept field photo NOT reproduced in the
%  thesis, same two-per-page layout as the Appendix A album, numerical order,
%  landscape photos first. Written by
%  Chapter5/Figures/write_chapter5_photo_album.py; \input{} by
%  Chapter5/chapter5_photo_supplement.tex.
% =============================================================
"""
APP_MACROS = r"""\providecommand{\phantomsection}{}
\providecommand{\ChFivePhoto}[1]{#1}
% Two photos per page, photos at full size: landscape photos at the full text
% width (at most \ChFiveBigMax tall), portrait photos at 0.48 of it (at most
% \ChFiveTallMax tall). The captions (single-spaced) take the room that is left:
% TeX tries \small, \footnotesize, \scriptsize in turn and keeps the largest size
% at which both captions fit (the same size for both captions of a page). Only
% if even \scriptsize does not fit are the photos shrunk, just enough to make room.
% Each trial sets the whole page in a box and measures it.
\newsavebox\ChFiveImgA
\newsavebox\ChFivePageBox
\newsavebox\ChFiveImgB
\newsavebox\ChFiveCapA
\newsavebox\ChFiveCapB
\newlength\ChFiveImgH
\newlength\ChFiveImgW
\newlength\ChFiveCapW
\newif\ifChFiveFits
\newcommand{\ChFiveBigMax}{0.45\textheight}
\newcommand{\ChFiveTallMax}{0.62\textheight}
\newcommand{\ChFiveCapFont}{\small}
\newcommand{\ChFiveTotal}[1]{\dimexpr\ht#1+\dp#1\relax}
\newcommand{\ChFiveSetImg}[2]{%  {box}{image}
  \sbox#1{\includegraphics[width=\ChFiveImgW,height=\ChFiveImgH,keepaspectratio]{#2}}}
\newcommand{\ChFiveSetCaps}{%
  \sbox\ChFiveCapA{\parbox[t]{\ChFiveCapW}{\def\baselinestretch{1}\ChFiveCapFont\raggedright
    \setlength{\parskip}{2pt}\ChFiveCapTextA}}%
  \sbox\ChFiveCapB{\parbox[t]{\ChFiveCapW}{\def\baselinestretch{1}\ChFiveCapFont\raggedright
    \setlength{\parskip}{2pt}\ChFiveCapTextB}}}
\newcommand{\ChFiveCapsHeight}{% stacked (landscape) or side by side (portrait)
  \ifChFiveSideBySide
    \ifdim\ChFiveTotal\ChFiveCapA>\ChFiveTotal\ChFiveCapB \ChFiveTotal\ChFiveCapA
    \else\ChFiveTotal\ChFiveCapB\fi
  \else\dimexpr\ChFiveTotal\ChFiveCapA+\ChFiveTotal\ChFiveCapB\relax\fi}
\newif\ifChFiveSideBySide
\newcommand{\ChFiveTryFont}[1]{%  fits = the finished page (\ChFivePage) is no taller than the text block
  \ifChFiveFits\else
    \renewcommand{\ChFiveCapFont}{#1}\ChFiveSetCaps
    \setbox\ChFivePageBox\vbox{\ChFivePage}%
    \ifdim\dimexpr\ht\ChFivePageBox+\dp\ChFivePageBox+\topskip+2pt\relax<\textheight
      \ChFiveFitstrue\fi
  \fi}
\newcommand{\ChFiveFit}{%
  \ChFiveFitsfalse
  \ChFiveTryFont{\small}\ChFiveTryFont{\footnotesize}%
  \ChFiveTryFont{\scriptsize}}
\newcommand{\ChFiveBigOne}[4]{%  {width}{n}{image box}{caption box}
  \begin{minipage}[t]{#1}\centering
  \phantomsection\label{ch5-photo-#2}%
  \usebox#3\par
  \vspace{4pt}\raggedright\usebox#4\par
  \end{minipage}}
% Final check: the page is set in a trial box and, if it is still taller than
% the text block, both photos are shrunk by exactly the excess (a few passes).
\newcount\ChFiveIter
\newif\ifChFiveTooTall
\newlength\ChFiveExcess
\newcommand{\ChFiveSettle}[3]{%  {page content}{img1}{img2}
  \ChFiveIter=0
  \loop
    \setbox\ChFivePageBox\vbox{#1}%
    \setlength\ChFiveExcess{\dimexpr\ht\ChFivePageBox+\dp\ChFivePageBox-\textheight+\topskip+2pt\relax}%
    \ChFiveTooTallfalse
    \ifnum\ChFiveIter<6 \ifdim\ChFiveExcess>0pt \ChFiveTooTalltrue\fi\fi
  \ifChFiveTooTall
    \ifdim\ht\ChFiveImgA>\ht\ChFiveImgB
      \setlength\ChFiveImgH{\ht\ChFiveImgA}\else\setlength\ChFiveImgH{\ht\ChFiveImgB}\fi
    \ifChFiveSideBySide\else\setlength\ChFiveExcess{0.5\ChFiveExcess}\fi
    \setlength\ChFiveImgH{\dimexpr\ChFiveImgH-\ChFiveExcess-1pt\relax}%
    \ChFiveSetImg\ChFiveImgA{#2}\ChFiveSetImg\ChFiveImgB{#3}%
    \advance\ChFiveIter by 1
  \repeat}
\newcommand{\ChFiveReport}[2]{\typeout{ChFive album: photos #1 and #2, captions
  \expandafter\string\ChFiveCapFont\ifnum\ChFiveIter>0 \space (photos shrunk)\fi}}
% landscape-orientation photos: one above the other, full text width
\newcommand{\ChFiveWidePair}[6]{%  {n1}{img1}{cap1}{n2}{img2}{cap2}
  \ChFiveSideBySidefalse
  \setlength\ChFiveImgW{\linewidth}\setlength\ChFiveImgH{\ChFiveBigMax}%
  \setlength\ChFiveCapW{\linewidth}%
  \ChFiveSetImg\ChFiveImgA{#2}\ChFiveSetImg\ChFiveImgB{#5}%
  \def\ChFiveCapTextA{#3}\def\ChFiveCapTextB{#6}%
  \def\ChFivePage{\noindent\ChFiveBigOne{\linewidth}{#1}\ChFiveImgA\ChFiveCapA\par\vfill
    \noindent\ChFiveBigOne{\linewidth}{#4}\ChFiveImgB\ChFiveCapB\par}%
  \ChFiveFit
  \ChFiveSettle{\ChFivePage}{#2}{#5}\ChFiveReport{#1}{#4}%
  \ChFivePage\vfill\clearpage}
\newcommand{\ChFiveWideOne}[3]{%
  \setlength\ChFiveImgW{\linewidth}\setlength\ChFiveImgH{\ChFiveBigMax}%
  \setlength\ChFiveCapW{\linewidth}\renewcommand{\ChFiveCapFont}{\small}%
  \ChFiveSetImg\ChFiveImgA{#2}\def\ChFiveCapTextA{#3}\def\ChFiveCapTextB{}\ChFiveSetCaps
  \noindent\ChFiveBigOne{\linewidth}{#1}\ChFiveImgA\ChFiveCapA\par\clearpage}
% portrait-orientation photos: side by side, each 0.48 of the text width
\newcommand{\ChFiveTallPair}[6]{%
  \ChFiveSideBySidetrue
  \setlength\ChFiveImgW{0.48\linewidth}\setlength\ChFiveImgH{\ChFiveTallMax}%
  \setlength\ChFiveCapW{0.48\linewidth}%
  \ChFiveSetImg\ChFiveImgA{#2}\ChFiveSetImg\ChFiveImgB{#5}%
  \def\ChFiveCapTextA{#3}\def\ChFiveCapTextB{#6}%
  \def\ChFivePage{\noindent\ChFiveBigOne{0.48\linewidth}{#1}\ChFiveImgA\ChFiveCapA\hfill
    \ChFiveBigOne{0.48\linewidth}{#4}\ChFiveImgB\ChFiveCapB\par}%
  \ChFiveFit
  \ChFiveSettle{\ChFivePage}{#2}{#5}\ChFiveReport{#1}{#4}%
  \ChFivePage\clearpage}
\newcommand{\ChFiveTallOne}[3]{%
  \setlength\ChFiveImgW{0.48\linewidth}\setlength\ChFiveImgH{\ChFiveTallMax}%
  \setlength\ChFiveCapW{0.48\linewidth}\renewcommand{\ChFiveCapFont}{\small}%
  \ChFiveSetImg\ChFiveImgA{#2}\def\ChFiveCapTextA{#3}\def\ChFiveCapTextB{}\ChFiveSetCaps
  \noindent\ChFiveBigOne{0.48\linewidth}{#1}\ChFiveImgA\ChFiveCapA\par\clearpage}
"""


def appendix_tex(order, caps, tall, photos, header):
    def img(n):
        return f'{TEX_IMG_DIR}/DrBV{n}.jpg' if n in photos else 'example-image'

    def cap(n):
        label, body = caps[n]
        return rf'\textbf{{{label}}} {body}' if label else ''

    wide = [n for n in order if n not in tall]
    talls = [n for n in order if n in tall]
    out = [header + APP_MACROS, r'\clearpage']
    for seq, kind in ((wide, 'Wide'), (talls, 'Tall')):
        for i in range(0, len(seq), 2):
            pair = seq[i:i + 2]
            args = ''.join(rf'{{{n}}}{{{img(n)}}}{{{cap(n)}}}' for n in pair)
            out.append(rf'\ChFive{kind}{"Pair" if len(pair) == 2 else "One"}' + args)
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    main()
