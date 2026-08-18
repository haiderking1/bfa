"""Greedy wrap of measured tokens to a pixel width."""

from __future__ import annotations

from typing import Callable, Sequence, TypeVar

T = TypeVar("T")


def wrap_tokens(
    tokens: Sequence[T],
    widths: Sequence[float],
    max_width_px: float,
    *,
    is_discardable_break: Callable[[T], bool],
) -> list[list[T]]:
    """Packs tokens into lines that do not exceed ``max_width_px``.

    A token wider than the box is placed on its own line rather than split.
    ``is_discardable_break`` tokens (spaces) are dropped at line edges.
    """
    if len(tokens) != len(widths):
        raise ValueError("token and width counts must match")
    if max_width_px <= 0:
        raise ValueError("max_width_px must be positive")
    lines: list[list[T]] = []
    current: list[T] = []
    current_width = 0.0

    def flush() -> None:
        nonlocal current, current_width
        while current and is_discardable_break(current[-1]):
            current = current[:-1]
        if current:
            lines.append(current)
        current = []
        current_width = 0.0

    for token, width in zip(tokens, widths):
        if is_discardable_break(token) and not current:
            continue
        fits = current_width + width <= max_width_px
        if current and not fits:
            flush()
            if is_discardable_break(token):
                continue
        current.append(token)
        current_width += width
        if not current[1:] and width > max_width_px:
            flush()
    flush()
    return lines
