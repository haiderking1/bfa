"""Restore exact Sleeping Dogs control tags and placeholders after translation."""

from __future__ import annotations

import re
from collections import Counter

from bfa.games.sleeping_dogs.localization import (
    localization_control_tag_spans,
    localization_control_tags,
)
from bfa.games.sleeping_dogs.validation import (
    localization_placeholder_spans,
    localization_placeholders,
)

_WHITESPACE_RE = re.compile(r"[\s\xa0]+")


def is_markup_only(text: str) -> bool:
    """True when the string has no translatable payload — only tags, placeholders, or space."""
    remainder = text
    for token in sorted(localization_control_tags(text), key=len, reverse=True):
        remainder = remainder.replace(token, "", 1)
    for token in localization_placeholders(remainder):
        remainder = remainder.replace(token, "", 1)
    return remainder.strip() == ""


def repair_translated_text(source_text: str, translated_text: str) -> str:
    """Rewrite a model translation so its protected tokens match the source exactly.

    Does not invent wording. Empty translations of real sentences are left empty
    so validation still rejects them.
    """
    if not isinstance(translated_text, str):
        return translated_text
    if "\x00" in translated_text:
        return translated_text
    if not translated_text.strip() and not is_markup_only(source_text):
        return translated_text
    if is_markup_only(source_text):
        return source_text

    repaired = _restore_control_tags(source_text, translated_text)
    return _restore_placeholders(source_text, repaired)


def _normalize_tag(tag: str) -> str:
    return _WHITESPACE_RE.sub(" ", tag).strip().lower()


def _tag_name(tag: str) -> str:
    if tag.startswith("&"):
        return tag.lower()
    body = tag[1:-1].strip() if tag.startswith("<") and tag.endswith(">") else tag
    if not body:
        return ""
    return body.split(None, 1)[0].lower()


def _is_angle_closer(tag: str) -> bool:
    return tag.startswith("</")


def _is_angle_opener(tag: str) -> bool:
    return tag.startswith("<") and not tag.startswith("</") and not tag.startswith("&")


def _restore_control_tags(source_text: str, translated_text: str) -> str:
    source_tags = localization_control_tags(source_text)
    translated_spans = localization_control_tag_spans(translated_text)
    if not source_tags and not translated_spans:
        return translated_text

    unused = list(source_tags)
    replacements: list[tuple[int, int, str]] = []
    unmatched_translated: list[tuple[int, int, str]] = []

    for start, end, tag in translated_spans:
        match_index = _take_unused(unused, lambda item: item == tag)
        if match_index is None:
            match_index = _take_unused(
                unused, lambda item, current=tag: _normalize_tag(item) == _normalize_tag(current)
            )
        if match_index is None:
            match_index = _take_unused(
                unused, lambda item, current=tag: _tag_name(item) == _tag_name(current)
            )
        if match_index is None:
            unmatched_translated.append((start, end, tag))
            continue
        replacements.append((start, end, unused.pop(match_index)))

    leftover_closers = [tag for tag in unused if _is_angle_closer(tag)]
    leftover_openers = [tag for tag in unused if _is_angle_opener(tag)]
    still_unmatched: list[tuple[int, int, str]] = []
    for start, end, tag in unmatched_translated:
        paired: str | None = None
        if _is_angle_closer(tag) and leftover_closers:
            paired = leftover_closers.pop(0)
            unused.remove(paired)
        elif _is_angle_opener(tag) and leftover_openers:
            paired = leftover_openers.pop(0)
            unused.remove(paired)
        if paired is None:
            still_unmatched.append((start, end, tag))
            continue
        replacements.append((start, end, paired))

    repaired = translated_text
    for start, end, replacement in sorted(
        replacements + [(start, end, "") for start, end, _tag in still_unmatched],
        key=lambda item: item[0],
        reverse=True,
    ):
        repaired = repaired[:start] + replacement + repaired[end:]

    return _insert_missing_tags(source_text, repaired, unused)


def _take_unused(unused: list[str], predicate) -> int | None:
    for index, item in enumerate(unused):
        if predicate(item):
            return index
    return None


def _insert_missing_tags(source_text: str, translated_text: str, missing: list[str]) -> str:
    if not missing:
        return translated_text
    remaining = Counter(missing)
    insertions: list[tuple[float, str]] = []
    for start, _end, tag in localization_control_tag_spans(source_text):
        if remaining[tag] <= 0:
            continue
        remaining[tag] -= 1
        ratio = start / max(len(source_text), 1)
        insertions.append((ratio, tag))
    repaired = translated_text
    for ratio, tag in sorted(insertions, key=lambda item: item[0], reverse=True):
        pos = _snap_insert(repaired, int(ratio * len(repaired)), tag)
        repaired = repaired[:pos] + tag + repaired[pos:]
    return repaired


def _outside_angle_tag(text: str, pos: int) -> int:
    last_open = text.rfind("<", 0, pos)
    if last_open < 0:
        return pos
    close = text.find(">", last_open)
    if close < 0 or close >= pos:
        return last_open
    return pos


def _snap_insert(text: str, pos: int, tag: str) -> int:
    if not text:
        return 0
    pos = _outside_angle_tag(text, max(0, min(pos, len(text))))
    window = 24
    for delta in range(0, window + 1):
        for candidate in (pos, pos - delta, pos + delta):
            if candidate <= 0:
                return 0
            if candidate >= len(text):
                return len(text)
            if _outside_angle_tag(text, candidate) != candidate:
                continue
            if text[candidate].isspace():
                return candidate + (1 if tag.startswith("&") else 0)
    return pos


def _restore_placeholders(source_text: str, translated_text: str) -> str:
    source_tokens = localization_placeholders(source_text)
    translated_spans = localization_placeholder_spans(translated_text)
    unused = list(source_tokens)
    extras: list[tuple[int, int]] = []
    for start, end, token in translated_spans:
        if token in unused:
            unused.remove(token)
            continue
        extras.append((start, end))

    repaired = translated_text
    for start, end in reversed(extras):
        repaired = repaired[:start] + repaired[end:]

    if not unused:
        return repaired

    remaining = Counter(unused)
    insertions: list[tuple[float, str]] = []
    for start, _end, token in localization_placeholder_spans(source_text):
        if remaining[token] <= 0:
            continue
        remaining[token] -= 1
        insertions.append((start / max(len(source_text), 1), token))
    for ratio, token in sorted(insertions, key=lambda item: item[0], reverse=True):
        pos = _snap_insert(repaired, int(ratio * len(repaired)), token)
        repaired = repaired[:pos] + token + repaired[pos:]
    return repaired
