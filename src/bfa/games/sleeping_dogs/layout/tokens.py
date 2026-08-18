"""Tokenize Scaleform loc HTML into wrap units."""

from __future__ import annotations

from dataclasses import dataclass
import re

_FONT_ATOM_RE = re.compile(r"(?is)<font\b[^>]*>.*?</font>")
_IMG_RE = re.compile(r"(?is)<img\b[^>]*/?>")
_TAG_RE = re.compile(r"(?is)<[^>]+>")
_ENTITY_RE = re.compile(r"&(?:[A-Za-z]+|#\d+|#x[0-9A-Fa-f]+);", re.IGNORECASE)
_SPACE_RE = re.compile(r"[^\S\n]+")
_BR_SPLIT_RE = re.compile(r"(?i)(<br\s*/?>)")
_FONT_PARTS_RE = re.compile(r"(?is)(<font\b[^>]*>)(.*)(</font>)\Z")


@dataclass(frozen=True, slots=True)
class LocToken:
    """One wrap unit of a Scaleform HTML loc string."""

    kind: str
    source: str
    measure_text: str
    bidi_text: str


def split_break_tags(text: str) -> list[str]:
    """Splits ``text`` into paragraphs and original ``<br>`` spellings."""
    if text == "":
        return [""]
    return _BR_SPLIT_RE.split(text)


def is_break_tag(text: str) -> bool:
    """True when ``text`` is a ``<br>`` tag."""
    return _BR_SPLIT_RE.fullmatch(text) is not None


def tokenize_paragraph(text: str) -> list[LocToken]:
    """Tokenizes one paragraph that contains no ``<br>`` tags."""
    tokens: list[LocToken] = []
    pos = 0
    length = len(text)
    while pos < length:
        font = _FONT_ATOM_RE.match(text, pos)
        if font is not None:
            tokens.append(_font_token(font.group()))
            pos = font.end()
            continue
        img = _IMG_RE.match(text, pos)
        if img is not None:
            tokens.append(
                LocToken(kind="atom", source=img.group(), measure_text="", bidi_text="\ufffc")
            )
            pos = img.end()
            continue
        tag = _TAG_RE.match(text, pos)
        if tag is not None:
            tokens.append(
                LocToken(kind="markup", source=tag.group(), measure_text="", bidi_text="")
            )
            pos = tag.end()
            continue
        entity = _ENTITY_RE.match(text, pos)
        if entity is not None:
            tokens.append(_entity_token(entity.group()))
            pos = entity.end()
            continue
        space = _SPACE_RE.match(text, pos)
        if space is not None:
            tokens.append(
                LocToken(
                    kind="space",
                    source=space.group(),
                    measure_text=" ",
                    bidi_text=" ",
                )
            )
            pos = space.end()
            continue
        end = _word_end(text, pos)
        word = text[pos:end]
        tokens.append(LocToken(kind="word", source=word, measure_text=word, bidi_text=word))
        pos = end
    return _attach_markup(tokens)


def token_is_space(token: LocToken) -> bool:
    """True when the token is wrap-break whitespace."""
    return token.kind in {"space", "nbsp"}


def paragraph_bidi_text(tokens: list[LocToken]) -> str:
    """Concatenates bidi-significant text used to pick paragraph direction."""
    return "".join(token.bidi_text for token in tokens)


def _font_token(source: str) -> LocToken:
    match = _FONT_PARTS_RE.match(source)
    inner = match.group(2) if match is not None else source
    return LocToken(kind="atom", source=source, measure_text=inner, bidi_text=inner)


def _entity_token(source: str) -> LocToken:
    lower = source.lower()
    if lower == "&nbsp;":
        return LocToken(kind="nbsp", source=source, measure_text=" ", bidi_text="\u00a0")
    return LocToken(kind="atom", source=source, measure_text=source, bidi_text=source)


def _word_end(text: str, start: int) -> int:
    index = start + 1
    length = len(text)
    while index < length:
        if text[index] in "<&" or text[index].isspace():
            break
        index += 1
    return index


def _attach_markup(tokens: list[LocToken]) -> list[LocToken]:
    attached: list[LocToken] = []
    pending = ""
    for token in tokens:
        if token.kind == "markup":
            pending += token.source
            continue
        if pending:
            attached.append(
                LocToken(
                    kind=token.kind,
                    source=pending + token.source,
                    measure_text=token.measure_text,
                    bidi_text=token.bidi_text,
                )
            )
            pending = ""
            continue
        attached.append(token)
    if pending:
        if attached:
            last = attached[-1]
            attached[-1] = LocToken(
                kind=last.kind,
                source=last.source + pending,
                measure_text=last.measure_text,
                bidi_text=last.bidi_text,
            )
        else:
            attached.append(LocToken(kind="markup", source=pending, measure_text="", bidi_text=""))
    return attached
