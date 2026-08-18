"""Parse Sleeping Dogs loc HTML into a tag tree.

Scaleform strings mix ``<font>``, ``<cite>``, ``<img>``, and ``<br>``. Vanilla
also closes some ``<font>`` tags as ``</job>``. A close tag always closes the
current open element, and the original close spelling is kept.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

_TAG_RE = re.compile(r"(?is)<(/)?([A-Za-z]+)([^>]*)>")
_VOID_TAGS = frozenset({"br", "img"})


@dataclass(frozen=True, slots=True)
class MarkupNode:
    """One node of a Scaleform loc HTML tree."""

    kind: str
    source: str
    tag: str
    open_source: str
    close_source: str
    children: tuple["MarkupNode", ...]


def parse_loc_markup(text: str) -> tuple[MarkupNode, ...]:
    """Parses ``text`` into markup nodes, preserving every original tag spelling."""
    nodes, pos = _parse_sequence(text, 0, None)
    if pos < len(text):
        nodes.append(
            MarkupNode(
                kind="text",
                source=text[pos:],
                tag="",
                open_source="",
                close_source="",
                children=(),
            )
        )
    return tuple(nodes)


def markup_plain_text(nodes: tuple[MarkupNode, ...] | list[MarkupNode]) -> str:
    """Concatenates visible text, dropping tags and images."""
    pieces: list[str] = []
    for node in nodes:
        if node.kind == "text":
            pieces.append(node.source)
        elif node.kind == "break":
            pieces.append("\n")
        elif node.kind == "element":
            pieces.append(markup_plain_text(node.children))
    return "".join(pieces)


def _parse_sequence(
    text: str, pos: int, open_name: str | None
) -> tuple[list[MarkupNode], int]:
    nodes: list[MarkupNode] = []
    length = len(text)
    while pos < length:
        char = text[pos]
        if char == "\n":
            nodes.append(_break_node("\n"))
            pos += 1
            continue
        if char != "<":
            end = pos + 1
            while end < length and text[end] not in "<\n":
                end += 1
            nodes.append(_text_node(text[pos:end]))
            pos = end
            continue
        match = _TAG_RE.match(text, pos)
        if match is None:
            nodes.append(_text_node("<"))
            pos += 1
            continue
        closing = match.group(1) is not None
        name = match.group(2).lower()
        raw = match.group(0)
        if closing:
            if open_name is not None:
                return nodes, pos
            nodes.append(
                MarkupNode(
                    kind="stray_close",
                    source=raw,
                    tag=name,
                    open_source="",
                    close_source=raw,
                    children=(),
                )
            )
            pos = match.end()
            continue
        if name in _VOID_TAGS:
            if name == "br":
                nodes.append(_break_node(raw))
            else:
                nodes.append(
                    MarkupNode(
                        kind="img",
                        source=raw,
                        tag="img",
                        open_source=raw,
                        close_source="",
                        children=(),
                    )
                )
            pos = match.end()
            continue
        inner, inner_end = _parse_sequence(text, match.end(), name)
        close_source = ""
        if inner_end < length:
            closer = _TAG_RE.match(text, inner_end)
            if closer is not None and closer.group(1) is not None:
                close_source = closer.group(0)
                inner_end = closer.end()
        nodes.append(
            MarkupNode(
                kind="element",
                source="",
                tag=name,
                open_source=raw,
                close_source=close_source,
                children=tuple(inner),
            )
        )
        pos = inner_end
    return nodes, pos


def _text_node(source: str) -> MarkupNode:
    return MarkupNode(
        kind="text",
        source=source,
        tag="",
        open_source="",
        close_source="",
        children=(),
    )


def _break_node(source: str) -> MarkupNode:
    return MarkupNode(
        kind="break",
        source=source,
        tag="br" if source != "\n" else "newline",
        open_source="",
        close_source="",
        children=(),
    )
