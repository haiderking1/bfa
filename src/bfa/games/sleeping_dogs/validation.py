"""Strict validation for translated Sleeping Dogs localization entries and resources."""

from __future__ import annotations

import re
from collections import Counter
from typing import List, Sequence

from bfa.games.sleeping_dogs.localization import (
    encode_uilocalization_chunk,
    localization_control_tags,
    parse_uilocalization_chunk,
)
from bfa.games.sleeping_dogs.models import LocalizationEntry, LocalizationTable

_PRINTF_RE = re.compile(r"%(?:[-+0#]*\d*(?:\.\d+)?[sdifuxX]|%)")
_BRACE_RE = re.compile(r"\{[^{}]+\}")
_ESCAPE_RE = re.compile(r"\\[nrt]")


class LocalizationValidationError(ValueError):
    """Raised when a translated localization resource or entry is not safe to pack."""


def localization_placeholder_spans(text: str) -> List[tuple[int, int, str]]:
    """Returns (start, end, token) spans for format placeholders and escapes."""
    tokens: List[tuple[int, int, str]] = []
    for match in _PRINTF_RE.finditer(text):
        tokens.append((match.start(), match.end(), match.group()))
    for match in _BRACE_RE.finditer(text):
        tokens.append((match.start(), match.end(), match.group()))
    for match in _ESCAPE_RE.finditer(text):
        tokens.append((match.start(), match.end(), match.group()))
    tokens.sort(key=lambda item: item[0])
    return tokens


def localization_placeholders(text: str) -> List[str]:
    """Returns format placeholders, brace tokens, and C-style escapes in display order."""
    return [token for _start, _end, token in localization_placeholder_spans(text)]


def validate_translated_text(source_text: str, translated_text: str) -> None:
    """Validates one translated string against its source."""
    if not isinstance(translated_text, str):
        raise LocalizationValidationError("translation is not a string")
    try:
        encoded = translated_text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise LocalizationValidationError("translation is not valid UTF-8") from exc
    if b"\x00" in encoded:
        raise LocalizationValidationError("translation contains an embedded null byte")

    source_tags = localization_control_tags(source_text)
    translated_tags = localization_control_tags(translated_text)
    if Counter(source_tags) != Counter(translated_tags):
        raise LocalizationValidationError(
            f"control-tag multiset changed: source={source_tags!r} translated={translated_tags!r}"
        )

    source_placeholders = localization_placeholders(source_text)
    translated_placeholders = localization_placeholders(translated_text)
    if Counter(source_placeholders) != Counter(translated_placeholders):
        raise LocalizationValidationError(
            "placeholder multiset changed: "
            f"source={source_placeholders!r} translated={translated_placeholders!r}"
        )


def validate_translated_entries(
    source_entries: Sequence[LocalizationEntry],
    translated_entries: Sequence[LocalizationEntry],
) -> None:
    """Validates that translated entries match source hashes, order, and protected tokens."""
    if len(source_entries) != len(translated_entries):
        raise LocalizationValidationError(
            f"entry count mismatch: source={len(source_entries)} translated={len(translated_entries)}"
        )
    for index, (source, translated) in enumerate(zip(source_entries, translated_entries)):
        if source.key_hash != translated.key_hash:
            raise LocalizationValidationError(
                f"key hash mismatch at index {index}: "
                f"source=0x{source.key_hash:08x} translated=0x{translated.key_hash:08x}"
            )
        validate_translated_text(source.text, translated.text)


def validate_resource_translations(
    source_texts: Sequence[str],
    translated_texts: Sequence[str | None],
) -> None:
    """Requires exactly one non-null translation for every source string."""
    if len(source_texts) != len(translated_texts):
        raise LocalizationValidationError(
            f"entry count mismatch: source={len(source_texts)} translated={len(translated_texts)}"
        )
    for index, text in enumerate(translated_texts):
        if text is None:
            raise LocalizationValidationError(f"source entry {index} is missing a translation")
        validate_translated_text(source_texts[index], text)


def encode_and_reparse(
    table: LocalizationTable,
    *,
    recompute_layout: bool,
) -> bytes:
    """Encodes a table and proves the result parses back as a UILocalizationChunk."""
    encoded = encode_uilocalization_chunk(table, recompute_layout=recompute_layout)
    parsed = parse_uilocalization_chunk(encoded)
    validate_translated_entries(table.entries, parsed.entries)
    if [entry.key_hash for entry in parsed.entries] != [entry.key_hash for entry in table.entries]:
        raise LocalizationValidationError("re-encoded resource changed key hash order")
    if [entry.text for entry in parsed.entries] != [entry.text for entry in table.entries]:
        raise LocalizationValidationError("re-encoded resource changed string contents")
    return encoded
