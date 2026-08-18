"""Paragraph-direction token reordering for visual-LTR emission."""

from __future__ import annotations

import unicodedata
from typing import Sequence, TypeVar

T = TypeVar("T")


def first_strong_is_rtl(text: str) -> bool:
    """True when the first strong Unicode character is Arabic or Hebrew."""
    for char in text:
        category = unicodedata.bidirectional(char)
        if category in {"R", "AL"}:
            return True
        if category == "L":
            return False
    return False


def visual_ltr_tokens(tokens: Sequence[T], *, rtl: bool) -> list[T]:
    """Returns tokens in the order an LTR renderer should paint them."""
    if not rtl:
        return list(tokens)
    return list(reversed(tokens))
