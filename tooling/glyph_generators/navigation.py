"""Navigation symbol glyph builders."""

from __future__ import annotations

from typing import Any
from tooling.geometry import draw_polygon, draw_rect
from tooling.models import GlyphSpec


def draw_house(pen: Any) -> None:
    outer_verts = [
        (600.0, 1170.0),
        (110.0, 750.0),
        (220.0, 750.0),
        (220.0, 170.0),
        (980.0, 170.0),
        (980.0, 750.0),
        (1090.0, 750.0),
    ]
    inner_verts = [
        (600.0, 970.0),
        (850.0, 680.0),
        (850.0, 300.0),
        (350.0, 300.0),
        (350.0, 680.0),
    ]
    draw_polygon(pen, outer_verts, ccw=True)
    draw_polygon(pen, inner_verts, ccw=False)


def draw_backspace(pen: Any) -> None:
    outer_verts = [
        (100.0, 670.0),
        (450.0, 230.0),
        (1200.0, 230.0),
        (1200.0, 1110.0),
        (450.0, 1110.0),
    ]
    inner_verts = [
        (270.0, 670.0),
        (530.0, 980.0),
        (1070.0, 980.0),
        (1070.0, 360.0),
        (530.0, 360.0),
    ]
    draw_polygon(pen, outer_verts, ccw=True)
    draw_polygon(pen, inner_verts, ccw=False)

    # Inner X symbol in badge
    # Draw two diagonal bars centered at (800, 670)
    w = 32.0  # half-thickness of stroke (total ~90 diagonal)
    diag1 = [
        (680.0 - w, 550.0 + w),
        (680.0 + w, 550.0 - w),
        (920.0 + w, 790.0 - w),
        (920.0 - w, 790.0 + w),
    ]
    diag2 = [
        (680.0 - w, 790.0 - w),
        (920.0 - w, 550.0 - w),
        (920.0 + w, 550.0 + w),
        (680.0 + w, 790.0 + w),
    ]
    draw_polygon(pen, diag1, ccw=True)
    draw_polygon(pen, diag2, ccw=True)


def draw_return(pen: Any) -> None:
    verts = [
        (100.0, 420.0),
        (380.0, 170.0),
        (380.0, 350.0),
        (950.0, 350.0),
        (950.0, 1050.0),
        (680.0, 1050.0),
        (680.0, 910.0),
        (810.0, 910.0),
        (810.0, 490.0),
        (380.0, 490.0),
        (380.0, 670.0),
    ]
    draw_polygon(pen, verts, ccw=True)


def draw_carriage_return(pen: Any) -> None:
    verts = [
        (100.0, 420.0),
        (380.0, 170.0),
        (380.0, 350.0),
        (850.0, 350.0),
        (850.0, 1150.0),
        (710.0, 1150.0),
        (710.0, 490.0),
        (380.0, 490.0),
        (380.0, 670.0),
    ]
    draw_polygon(pen, verts, ccw=True)


def draw_shift(pen: Any) -> None:
    outer_verts = [
        (550.0, 1140.0),
        (150.0, 650.0),
        (370.0, 650.0),
        (370.0, 200.0),
        (730.0, 200.0),
        (730.0, 650.0),
        (950.0, 650.0),
    ]
    inner_verts = [
        (550.0, 940.0),
        (780.0, 600.0),
        (600.0, 600.0),
        (600.0, 330.0),
        (500.0, 330.0),
        (500.0, 600.0),
        (320.0, 600.0),
    ]
    draw_polygon(pen, outer_verts, ccw=True)
    draw_polygon(pen, inner_verts, ccw=False)


def draw_tab(pen: Any) -> None:
    # Right vertical stop bar
    draw_rect(pen, 1020.0, 250.0, 1140.0, 1090.0, ccw=True)
    # Left arrow pointing right
    arrow_verts = [
        (900.0, 670.0),
        (600.0, 370.0),
        (600.0, 600.0),
        (80.0, 600.0),
        (80.0, 740.0),
        (600.0, 740.0),
        (600.0, 970.0),
    ]
    draw_polygon(pen, arrow_verts, ccw=True)


def get_navigation_specs() -> list[GlyphSpec]:
    return [
        GlyphSpec(0x2302, "⌂", "house", 1200, "Navigation", draw_house, "House symbol"),
        GlyphSpec(0x232B, "⌫", "eraseleft", 1300, "Navigation", draw_backspace, "Erase to the left"),
        GlyphSpec(0x23CE, "⏎", "return", 1200, "Navigation", draw_return, "Return symbol"),
        GlyphSpec(0x21B5, "↵", "carriagereturn", 1100, "Navigation", draw_carriage_return, "Carriage return"),
        GlyphSpec(0x21E7, "⇧", "arrowupoutline", 1100, "Navigation", draw_shift, "Upwards white arrow"),
        GlyphSpec(0x21E5, "⇥", "arrowrightbar", 1200, "Navigation", draw_tab, "Rightwards arrow to bar"),
    ]
