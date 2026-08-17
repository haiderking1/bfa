"""Math and basic control glyph builders."""

from __future__ import annotations

from typing import Any
from tooling.geometry import draw_polygon, draw_rect
from tooling.models import GlyphSpec


def draw_minus(pen: Any) -> None:
    # Matches existing `plus` glyph horizontal bar exactly
    draw_rect(pen, 100.0, 606.0, 958.0, 739.0, ccw=True)


def draw_less_equal(pen: Any) -> None:
    chevron_verts = [
        (1059.0, 1120.0),
        (1059.0, 1270.0),
        (110.0, 825.0),
        (110.0, 735.0),
        (1059.0, 390.0),
        (1059.0, 540.0),
        (320.0, 780.0),
    ]
    draw_polygon(pen, chevron_verts, ccw=True)
    draw_rect(pen, 110.0, 140.0, 1059.0, 275.0, ccw=True)


def draw_greater_equal(pen: Any) -> None:
    chevron_verts = [
        (110.0, 1120.0),
        (110.0, 1270.0),
        (1059.0, 825.0),
        (1059.0, 735.0),
        (110.0, 390.0),
        (110.0, 540.0),
        (849.0, 780.0),
    ]
    draw_polygon(pen, chevron_verts, ccw=True)
    draw_rect(pen, 110.0, 140.0, 1059.0, 275.0, ccw=True)


def get_control_specs() -> list[GlyphSpec]:
    return [
        GlyphSpec(0x2212, "−", "minus", 1058, "Basic Controls", draw_minus, "Minus sign"),
        GlyphSpec(0x2264, "≤", "lessequal", 1169, "Basic Controls", draw_less_equal, "Less-than or equal to"),
        GlyphSpec(0x2265, "≥", "greaterequal", 1169, "Basic Controls", draw_greater_equal, "Greater-than or equal to"),
    ]
