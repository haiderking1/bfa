"""HarfBuzz shaping for engines that draw UTF-8 left-to-right with no layout.

Sleeping Dogs Scaleform has no Arabic shaper. Isolated letters stored in logical
order render backwards and unjoined. This module turns logical Arabic into
visually ordered presentation-form codepoints that the BFA cmap already contains.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from bfa.fonts.asset import BFA_FONT_PATH, require_bfa_font

_ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)
_CJK_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
# Brackets stay outside the run. Sleeping Dogs uses "(emotion) spoken line"
# as subtitle markup; RTL-mirroring the closers produced a leftover "((" and
# hid the spoken text.
_ARABIC_PUNCT = set("!?.،؛:…,;\"'«»")
_UNI_NAME_RE = re.compile(r"^uni([0-9A-Fa-f]{4})$")
_U_NAME_RE = re.compile(r"^u([0-9A-Fa-f]{4,6})$")


@dataclass(frozen=True, slots=True)
class ShapeContext:
    font: object
    reverse_cmap: dict[int, int]
    _keep_alive: tuple[object, ...]


def load_shape_context(font_path: Path | None = None) -> ShapeContext:
    """Loads HarfBuzz + a gid-to-Unicode map for the BFA font."""
    path = require_bfa_font(font_path or BFA_FONT_PATH)
    blob = hb.Blob.from_file_path(str(path))
    face = hb.Face(blob)
    font = hb.Font(face)
    ttfont = TTFont(str(path))
    try:
        reverse_cmap = _reverse_cmap(ttfont)
    finally:
        ttfont.close()
    return ShapeContext(font=font, reverse_cmap=reverse_cmap, _keep_alive=(blob, face))


def has_arabic(text: str) -> bool:
    """True when the string contains an Arabic letter or mark."""
    return _ARABIC_RE.search(text) is not None


def strip_cjk(text: str) -> str:
    """Removes CJK unified ideographs that Scaleform may substitute from a system font."""
    return _CJK_RE.sub("", text)


def shape_arabic_run(text: str, context: ShapeContext) -> str:
    """Shapes one Arabic run into visual-LTR presentation forms."""
    if not text:
        return text
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.direction = "rtl"
    buf.script = "Arab"
    hb.shape(context.font, buf, {"kern": True, "liga": True})
    chars: list[str] = []
    for info in buf.glyph_infos:
        gid = info.codepoint
        code = None if gid == 0 else context.reverse_cmap.get(gid)
        if code is None and gid != 0:
            code = _code_from_glyph_name(context.font.glyph_to_string(gid))
        if code is None:
            cluster = info.cluster
            if 0 <= cluster < len(text):
                chars.append(text[cluster])
            continue
        chars.append(chr(code))
    return "".join(chars)


def shape_plain_text(text: str, context: ShapeContext) -> str:
    """Shapes Arabic runs inside a tag-free string and leaves other scripts alone."""
    if not has_arabic(text):
        return text
    pieces: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if _is_arabic_char(text[index]):
            end = _arabic_run_end(text, index)
            pieces.append(shape_arabic_run(text[index:end], context))
            index = end
            continue
        end = index + 1
        while end < length and not _is_arabic_char(text[end]):
            end += 1
        pieces.append(text[index:end])
        index = end
    return "".join(pieces)


def _is_arabic_char(char: str) -> bool:
    return _ARABIC_RE.fullmatch(char) is not None


def _arabic_run_end(text: str, start: int) -> int:
    index = start + 1
    length = len(text)
    while index < length:
        if _is_arabic_char(text[index]):
            index += 1
            continue
        if text[index] in _ARABIC_PUNCT:
            index += 1
            continue
        if text[index] not in " \u00a0":
            break
        lookahead = index
        while lookahead < length and text[lookahead] in " \u00a0":
            lookahead += 1
        if lookahead < length and _is_arabic_char(text[lookahead]):
            index = lookahead
            continue
        break
    return index


def _reverse_cmap(font: TTFont) -> dict[int, int]:
    cmap = font.getBestCmap()
    if not cmap:
        raise ValueError("font has no Unicode cmap")
    reverse: dict[int, int] = {}
    for code, name in cmap.items():
        gid = font.getGlyphID(name)
        previous = reverse.get(gid)
        if previous is None or _presentation_score(code) > _presentation_score(previous):
            reverse[gid] = code
    return reverse


def _presentation_score(code: int) -> int:
    if 0xFE70 <= code <= 0xFEFF:
        return 3
    if 0xFB50 <= code <= 0xFDFF:
        return 2
    return 1


def _code_from_glyph_name(name: str) -> int | None:
    match = _UNI_NAME_RE.fullmatch(name) or _U_NAME_RE.fullmatch(name)
    if match is None:
        return None
    return int(match.group(1), 16)
