"""Typeset Sleeping Dogs loc HTML for Scaleform's LTR renderer."""

from __future__ import annotations

from dataclasses import replace

from bfa.fonts.shape import ShapeContext, has_arabic, shape_plain_text
from bfa.games.sleeping_dogs.layout.markup import MarkupNode, markup_plain_text, parse_loc_markup
from bfa.games.sleeping_dogs.layout.profile import PACK_WRAP_FONT_SIZE_PX, PACK_WRAP_WIDTH_PX
from bfa.games.sleeping_dogs.layout.tokens import (
    LocToken,
    paragraph_bidi_text,
    tokenize_paragraph,
    token_is_space,
)
from bfa.games.sleeping_dogs.localization import localization_control_tag_spans
from bfa.games.sleeping_dogs.validation import localization_placeholder_spans, localization_placeholders
from bfa.layout.bidi import first_strong_is_rtl, visual_ltr_tokens
from bfa.layout.measure import measure_text_px
from bfa.layout.wrap import wrap_tokens

_SHAPED_ATOM = "shaped_atom"


def typeset_localization_text(
    text: str,
    context: ShapeContext,
    *,
    width_px: float = PACK_WRAP_WIDTH_PX,
    font_size_px: float = PACK_WRAP_FONT_SIZE_PX,
) -> str:
    """Shapes, reorders, and wraps one loc string to ``width_px`` at ``font_size_px``."""
    if text == "" or not has_arabic(text):
        return text
    return _typeset_nodes(parse_loc_markup(text), context, width_px, font_size_px)


def shape_protected_text(text: str, context: ShapeContext) -> str:
    """Shapes Arabic around tags and placeholders without reordering or wrapping."""
    spans = _protected_spans(text)
    if not spans:
        return shape_plain_text(text, context)
    pieces: list[str] = []
    cursor = 0
    for start, end in spans:
        if start > cursor:
            pieces.append(shape_plain_text(text[cursor:start], context))
        pieces.append(text[start:end])
        cursor = end
    if cursor < len(text):
        pieces.append(shape_plain_text(text[cursor:], context))
    return "".join(pieces)


def _typeset_nodes(
    nodes: tuple[MarkupNode, ...] | list[MarkupNode],
    context: ShapeContext,
    width_px: float,
    font_size_px: float,
) -> str:
    nodes = _lift_trailing_breaks(list(nodes))
    pieces: list[str] = []
    segment: list[MarkupNode] = []
    for node in nodes:
        if node.kind == "break":
            pieces.append(_typeset_segment(segment, context, width_px, font_size_px))
            pieces.append(node.source)
            segment = []
            continue
        segment.append(node)
    pieces.append(_typeset_segment(segment, context, width_px, font_size_px))
    return "".join(pieces)


def _typeset_segment(
    nodes: list[MarkupNode],
    context: ShapeContext,
    width_px: float,
    font_size_px: float,
) -> str:
    if not nodes:
        return ""
    stray_closes = "".join(node.source for node in nodes if node.kind == "stray_close")
    nodes = [node for node in nodes if node.kind != "stray_close"]
    tokens = _tokens_for_segment(nodes, context, width_px, font_size_px)
    if not tokens:
        return stray_closes
    rtl = first_strong_is_rtl(paragraph_bidi_text(tokens))
    if _tokens_contain_break(tokens):
        return _emit_line(tokens, context) + stray_closes
    widths = [measure_text_px(token.measure_text, context, font_size_px) for token in tokens]
    lines = wrap_tokens(
        tokens,
        widths,
        width_px,
        is_discardable_break=token_is_space,
    )
    emitted: list[str] = []
    for line in lines:
        trimmed = _rstrip_spaces(line)
        if not trimmed:
            continue
        if rtl:
            trimmed = _visual_ltr_preserving_placeholders(trimmed)
        emitted.append(_emit_line(trimmed, context))
    return "<br>".join(line for line in emitted if line != "") + stray_closes


def _tokens_for_segment(
    nodes: list[MarkupNode],
    context: ShapeContext,
    width_px: float,
    font_size_px: float,
) -> list[LocToken]:
    tokens: list[LocToken] = []
    for node in nodes:
        if node.kind == "text":
            tokens.extend(tokenize_paragraph(node.source))
            continue
        if node.kind == "img":
            tokens.append(
                LocToken(
                    kind=_SHAPED_ATOM,
                    source=node.source,
                    measure_text="",
                    bidi_text="\ufffc",
                )
            )
            continue
        if node.kind != "element":
            continue
        inner = _typeset_nodes(node.children, context, width_px, font_size_px)
        source = f"{node.open_source}{inner}{node.close_source}"
        measure = markup_plain_text(node.children)
        tokens.append(
            LocToken(
                kind=_SHAPED_ATOM,
                source=source,
                measure_text=measure,
                bidi_text=measure,
            )
        )
    return tokens


def _lift_trailing_breaks(nodes: list[MarkupNode]) -> list[MarkupNode]:
    """Moves trailing ``<br>``/newlines out of elements so reverse cannot split a line."""
    lifted: list[MarkupNode] = []
    for node in nodes:
        if node.kind != "element":
            lifted.append(node)
            continue
        children = _lift_trailing_breaks(list(node.children))
        trailing: list[MarkupNode] = []
        while children and children[-1].kind == "break":
            trailing.append(children.pop())
        trailing.reverse()
        lifted.append(replace(node, children=tuple(children)))
        lifted.extend(trailing)
    return lifted


def _tokens_contain_break(tokens: list[LocToken]) -> bool:
    return any("<br" in token.source.lower() for token in tokens)


def _visual_ltr_preserving_placeholders(tokens: list[LocToken]) -> list[LocToken]:
    """Reverses tokens for LTR paint, keeping format placeholders in original order."""
    placeholders = [token for token in tokens if _token_has_placeholder(token)]
    visual = visual_ltr_tokens(tokens, rtl=True)
    if not placeholders:
        return visual
    restored = iter(placeholders)
    return [
        next(restored) if _token_has_placeholder(token) else token for token in visual
    ]


def _token_has_placeholder(token: LocToken) -> bool:
    return bool(localization_placeholders(token.source))


def _emit_line(tokens: list[LocToken], context: ShapeContext) -> str:
    pieces: list[str] = []
    for token in tokens:
        if token.kind == _SHAPED_ATOM:
            pieces.append(token.source)
            continue
        pieces.append(shape_protected_text(token.source, context))
    return "".join(pieces)


def _rstrip_spaces(line: list[LocToken]) -> list[LocToken]:
    end = len(line)
    while end > 0 and token_is_space(line[end - 1]):
        end -= 1
    return line[:end]


def _protected_spans(text: str) -> list[tuple[int, int]]:
    spans = [
        (start, end)
        for start, end, _token in localization_control_tag_spans(text)
        + localization_placeholder_spans(text)
    ]
    if not spans:
        return []
    spans.sort()
    merged: list[tuple[int, int]] = [spans[0]]
    for start, end in spans[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged
