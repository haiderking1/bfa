"""Arrow glyph builders."""

from __future__ import annotations

from typing import Any
from tooling.geometry import draw_polygon, rotate_points
from tooling.models import GlyphSpec

ARROW_ADVANCE = 1100
ARROW_CX = 550
ARROW_CY = 670

# Base up-arrow polygon vertices (CCW)
UP_ARROW_VERTICES = [
    (550.0, 1120.0),
    (190.0, 760.0),
    (480.0, 760.0),
    (480.0, 220.0),
    (620.0, 220.0),
    (620.0, 760.0),
    (910.0, 760.0),
]


def draw_arrow_left(pen: Any) -> None:
    verts = [
        (100.0, 670.0),
        (460.0, 310.0),
        (460.0, 600.0),
        (1000.0, 600.0),
        (1000.0, 740.0),
        (460.0, 740.0),
        (460.0, 1030.0),
    ]
    draw_polygon(pen, verts, ccw=True)


def draw_arrow_right(pen: Any) -> None:
    verts = [
        (1000.0, 670.0),
        (640.0, 1030.0),
        (640.0, 740.0),
        (100.0, 740.0),
        (100.0, 600.0),
        (640.0, 600.0),
        (640.0, 310.0),
    ]
    draw_polygon(pen, verts, ccw=True)


def draw_arrow_up(pen: Any) -> None:
    draw_polygon(pen, UP_ARROW_VERTICES, ccw=True)


def draw_arrow_down(pen: Any) -> None:
    verts = rotate_points(UP_ARROW_VERTICES, ARROW_CX, ARROW_CY, 180.0)
    draw_polygon(pen, verts, ccw=True)


def draw_arrow_north_west(pen: Any) -> None:
    verts = rotate_points(UP_ARROW_VERTICES, ARROW_CX, ARROW_CY, 45.0)
    draw_polygon(pen, verts, ccw=True)


def draw_arrow_north_east(pen: Any) -> None:
    verts = rotate_points(UP_ARROW_VERTICES, ARROW_CX, ARROW_CY, -45.0)
    draw_polygon(pen, verts, ccw=True)


def draw_arrow_south_east(pen: Any) -> None:
    verts = rotate_points(UP_ARROW_VERTICES, ARROW_CX, ARROW_CY, -135.0)
    draw_polygon(pen, verts, ccw=True)


def draw_arrow_south_west(pen: Any) -> None:
    verts = rotate_points(UP_ARROW_VERTICES, ARROW_CX, ARROW_CY, 135.0)
    draw_polygon(pen, verts, ccw=True)


def draw_arrow_left_right(pen: Any) -> None:
    verts = [
        (100.0, 670.0),
        (380.0, 370.0),
        (380.0, 600.0),
        (720.0, 600.0),
        (720.0, 370.0),
        (1000.0, 670.0),
        (720.0, 970.0),
        (720.0, 740.0),
        (380.0, 740.0),
        (380.0, 970.0),
    ]
    draw_polygon(pen, verts, ccw=True)


def draw_arrow_up_down(pen: Any) -> None:
    verts = [
        (550.0, 1120.0),
        (250.0, 840.0),
        (480.0, 840.0),
        (480.0, 500.0),
        (250.0, 500.0),
        (550.0, 220.0),
        (850.0, 500.0),
        (620.0, 500.0),
        (620.0, 840.0),
        (850.0, 840.0),
    ]
    draw_polygon(pen, verts, ccw=True)


def get_arrow_specs() -> list[GlyphSpec]:
    return [
        GlyphSpec(0x2190, "←", "arrowleft", ARROW_ADVANCE, "Arrows", draw_arrow_left, "Leftwards arrow"),
        GlyphSpec(0x2192, "→", "arrowright", ARROW_ADVANCE, "Arrows", draw_arrow_right, "Rightwards arrow"),
        GlyphSpec(0x2191, "↑", "arrowup", ARROW_ADVANCE, "Arrows", draw_arrow_up, "Upwards arrow"),
        GlyphSpec(0x2193, "↓", "arrowdown", ARROW_ADVANCE, "Arrows", draw_arrow_down, "Downwards arrow"),
        GlyphSpec(0x2196, "↖", "arrownorthwest", ARROW_ADVANCE, "Arrows", draw_arrow_north_west, "North west arrow"),
        GlyphSpec(0x2197, "↗", "arrownortheast", ARROW_ADVANCE, "Arrows", draw_arrow_north_east, "North east arrow"),
        GlyphSpec(0x2198, "↘", "arrowsoutheast", ARROW_ADVANCE, "Arrows", draw_arrow_south_east, "South east arrow"),
        GlyphSpec(0x2199, "↙", "arrowsouthwest", ARROW_ADVANCE, "Arrows", draw_arrow_south_west, "South west arrow"),
        GlyphSpec(0x2194, "↔", "arrowboth", ARROW_ADVANCE, "Arrows", draw_arrow_left_right, "Left right arrow"),
        GlyphSpec(0x2195, "↕", "arrowupdown", ARROW_ADVANCE, "Arrows", draw_arrow_up_down, "Up down arrow"),
    ]
