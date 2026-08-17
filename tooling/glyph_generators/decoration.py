"""UI decoration glyph builders."""

from __future__ import annotations

from typing import Any
from tooling.geometry import draw_circle, draw_star, draw_star_outline, round_pt
from tooling.models import GlyphSpec


def draw_ellipsis(pen: Any) -> None:
    # 3 dots matching period glyph size and baseline
    radius = 129.0
    cy = 129.0
    for cx in (210.0, 640.0, 1070.0):
        draw_circle(pen, cx, cy, radius, ccw=True)


def draw_black_star(pen: Any) -> None:
    draw_star(pen, 550.0, 670.0, r_outer=450.0, r_inner=172.0, points=5, ccw=True)


def draw_white_star(pen: Any) -> None:
    draw_star_outline(
        pen,
        550.0,
        670.0,
        r_outer=450.0,
        r_inner=172.0,
        r_outer_in=315.0,
        r_inner_in=120.0,
        points=5,
    )


def draw_black_heart(pen: Any) -> None:
    pen.moveTo(round_pt((550.0, 210.0)))
    pen.curveTo(
        round_pt((420.0, 280.0)),
        round_pt((120.0, 520.0)),
        round_pt((120.0, 830.0)),
    )
    pen.curveTo(
        round_pt((120.0, 1020.0)),
        round_pt((220.0, 1130.0)),
        round_pt((330.0, 1130.0)),
    )
    pen.curveTo(
        round_pt((430.0, 1130.0)),
        round_pt((520.0, 1010.0)),
        round_pt((550.0, 890.0)),
    )
    pen.curveTo(
        round_pt((580.0, 1010.0)),
        round_pt((670.0, 1130.0)),
        round_pt((770.0, 1130.0)),
    )
    pen.curveTo(
        round_pt((880.0, 1130.0)),
        round_pt((980.0, 1020.0)),
        round_pt((980.0, 830.0)),
    )
    pen.curveTo(
        round_pt((980.0, 520.0)),
        round_pt((680.0, 280.0)),
        round_pt((550.0, 210.0)),
    )
    pen.closePath()


def draw_white_heart(pen: Any) -> None:
    # Outer contour CCW
    draw_black_heart(pen)

    # Inner cutout contour CW
    pen.moveTo(round_pt((550.0, 360.0)))
    pen.curveTo(
        round_pt((650.0, 420.0)),
        round_pt((860.0, 580.0)),
        round_pt((860.0, 800.0)),
    )
    pen.curveTo(
        round_pt((860.0, 930.0)),
        round_pt((790.0, 1010.0)),
        round_pt((710.0, 1010.0)),
    )
    pen.curveTo(
        round_pt((640.0, 1010.0)),
        round_pt((570.0, 920.0)),
        round_pt((550.0, 770.0)),
    )
    pen.curveTo(
        round_pt((530.0, 920.0)),
        round_pt((460.0, 1010.0)),
        round_pt((390.0, 1010.0)),
    )
    pen.curveTo(
        round_pt((310.0, 1010.0)),
        round_pt((240.0, 930.0)),
        round_pt((240.0, 800.0)),
    )
    pen.curveTo(
        round_pt((240.0, 580.0)),
        round_pt((450.0, 420.0)),
        round_pt((550.0, 360.0)),
    )
    pen.closePath()


def get_decoration_specs() -> list[GlyphSpec]:
    return [
        GlyphSpec(0x2026, "…", "ellipsis", 1280, "UI Decoration", draw_ellipsis, "Horizontal ellipsis"),
        GlyphSpec(0x2605, "★", "blackstar", 1100, "UI Decoration", draw_black_star, "Black star"),
        GlyphSpec(0x2606, "☆", "whitestar", 1100, "UI Decoration", draw_white_star, "White star"),
        GlyphSpec(0x2665, "♥", "blackheart", 1100, "UI Decoration", draw_black_heart, "Black heart"),
        GlyphSpec(0x2661, "♡", "whiteheart", 1100, "UI Decoration", draw_white_heart, "White heart"),
    ]
