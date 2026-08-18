"""Prepare Sleeping Dogs loc strings for Scaleform's LTR text renderer."""

from __future__ import annotations

from dataclasses import replace
import re

from bfa.fonts.shape import ShapeContext, has_arabic, load_shape_context, strip_cjk
from bfa.games.sleeping_dogs.layout.profile import wrap_metrics_for
from bfa.games.sleeping_dogs.layout.typeset import typeset_localization_text
from bfa.games.sleeping_dogs.localization import localization_control_tag_spans
from bfa.games.sleeping_dogs.models import LocalizationEntry, LocalizationTable
from bfa.games.sleeping_dogs.validation import localization_placeholder_spans

_STAGE_DIRECTION_RE = re.compile(r"\([^()]*\)")
_HORIZONTAL_SPACE_RE = re.compile(r"[^\S\n]{2,}")


def strip_stage_directions(text: str) -> str:
    """Removes (acting notes) without touching tags or format placeholders."""
    if "(" not in text:
        return text
    while True:
        protected = _protected_spans(text)
        match = next(
            (
                candidate
                for candidate in _STAGE_DIRECTION_RE.finditer(text)
                if not _overlaps_protected(candidate.start(), candidate.end(), protected)
            ),
            None,
        )
        if match is None:
            break
        text = f"{text[: match.start()]}{text[match.end() :]}"
    return _HORIZONTAL_SPACE_RE.sub(" ", text).strip()


def shape_localization_text(
    text: str,
    context: ShapeContext | None = None,
    *,
    resource_debug_name: str = "",
    key_string: str | None = None,
) -> str:
    """Strips leaked CJK/stage notes, then typesets Arabic for LTR Scaleform."""
    cleaned = strip_stage_directions(strip_cjk(text))
    if cleaned == "":
        return cleaned
    ctx = context or load_shape_context()
    if not has_arabic(cleaned):
        return cleaned
    metrics = wrap_metrics_for(
        resource_debug_name=resource_debug_name,
        key_string=key_string,
    )
    return typeset_localization_text(
        cleaned,
        ctx,
        width_px=metrics.width_px,
        font_size_px=metrics.font_size_px,
    )


def shape_localization_table(
    table: LocalizationTable,
    context: ShapeContext | None = None,
    *,
    resource_debug_name: str = "",
) -> LocalizationTable:
    """Returns a copy whose entry texts are shaped for in-game display."""
    ctx = context or load_shape_context()
    return replace(
        table,
        entries=[
            LocalizationEntry(
                key_hash=entry.key_hash,
                text=shape_localization_text(
                    entry.text,
                    ctx,
                    resource_debug_name=resource_debug_name,
                    key_string=entry.key_string,
                ),
                key_string=entry.key_string,
            )
            for entry in table.entries
        ],
    )


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


def _overlaps_protected(start: int, end: int, protected: list[tuple[int, int]]) -> bool:
    return any(start < pend and end > pstart for pstart, pend in protected)
