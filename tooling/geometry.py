"""Geometric primitives and vector drawing helpers for Type 2 CharStrings."""

from __future__ import annotations

import math
from typing import Any, Sequence

# Standard cubic bezier control point factor for 90-degree circular arcs
# 4 * (sqrt(2) - 1) / 3 ≈ 0.552284749830793396
KAPPA = 0.5522847498307935


def round_pt(pt: tuple[float, float]) -> tuple[int, int]:
    """Round float coordinates to nearest integer for TrueType/CFF."""
    return (int(round(pt[0])), int(round(pt[1])))


def draw_polygon(pen: Any, points: Sequence[tuple[float, float]], ccw: bool = True) -> None:
    """Draw a closed polygon from a sequence of vertices.
    
    If ccw is True, points are drawn as given (assuming they are already CCW for outer contour).
    If ccw is False, points are reversed (for hole cutout).
    """
    if not points:
        return
    pts = [round_pt(p) for p in points]
    if not ccw:
        pts = list(reversed(pts))
    pen.moveTo(pts[0])
    for pt in pts[1:]:
        pen.lineTo(pt)
    pen.closePath()


def draw_rect(pen: Any, x_min: float, y_min: float, x_max: float, y_max: float, ccw: bool = True) -> None:
    """Draw a closed axis-aligned rectangle."""
    if ccw:
        points = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
    else:
        points = [(x_min, y_min), (x_min, y_max), (x_max, y_max), (x_max, y_min)]
    draw_polygon(pen, points, ccw=True)


def draw_rounded_rect(
    pen: Any,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
    radius: float,
    ccw: bool = True,
) -> None:
    """Draw a rounded rectangle using cubic Bezier corners."""
    r = min(radius, (x_max - x_min) / 2.0, (y_max - y_min) / 2.0)
    k = KAPPA * r

    if ccw:
        pen.moveTo(round_pt((x_min + r, y_min)))
        pen.lineTo(round_pt((x_max - r, y_min)))
        pen.curveTo(
            round_pt((x_max - r + k, y_min)),
            round_pt((x_max, y_min + r - k)),
            round_pt((x_max, y_min + r)),
        )
        pen.lineTo(round_pt((x_max, y_max - r)))
        pen.curveTo(
            round_pt((x_max, y_max - r + k)),
            round_pt((x_max - r + k, y_max)),
            round_pt((x_max - r, y_max)),
        )
        pen.lineTo(round_pt((x_min + r, y_max)))
        pen.curveTo(
            round_pt((x_min + r - k, y_max)),
            round_pt((x_min, y_max - r + k)),
            round_pt((x_min, y_max - r)),
        )
        pen.lineTo(round_pt((x_min, y_min + r)))
        pen.curveTo(
            round_pt((x_min, y_min + r - k)),
            round_pt((x_min + r - k, y_min)),
            round_pt((x_min + r, y_min)),
        )
        pen.closePath()
    else:
        pen.moveTo(round_pt((x_min + r, y_min)))
        pen.curveTo(
            round_pt((x_min + r - k, y_min)),
            round_pt((x_min, y_min + r - k)),
            round_pt((x_min, y_min + r)),
        )
        pen.lineTo(round_pt((x_min, y_max - r)))
        pen.curveTo(
            round_pt((x_min, y_max - r + k)),
            round_pt((x_min + r - k, y_max)),
            round_pt((x_min + r, y_max)),
        )
        pen.lineTo(round_pt((x_max - r, y_max)))
        pen.curveTo(
            round_pt((x_max - r + k, y_max)),
            round_pt((x_max, y_max - r + k)),
            round_pt((x_max, y_max - r)),
        )
        pen.lineTo(round_pt((x_max, y_min + r)))
        pen.curveTo(
            round_pt((x_max, y_min + r - k)),
            round_pt((x_max - r + k, y_min)),
            round_pt((x_max - r, y_min)),
        )
        pen.lineTo(round_pt((x_min + r, y_min)))
        pen.closePath()


def draw_circle(pen: Any, cx: float, cy: float, radius: float, ccw: bool = True) -> None:
    """Draw a smooth circle using 4 cubic Bezier segments."""
    r = radius
    k = KAPPA * r

    if ccw:
        # Counter-clockwise: (cx+r, cy) -> (cx, cy+r) -> (cx-r, cy) -> (cx, cy-r) -> (cx+r, cy)
        pen.moveTo(round_pt((cx + r, cy)))
        pen.curveTo(
            round_pt((cx + r, cy + k)),
            round_pt((cx + k, cy + r)),
            round_pt((cx, cy + r)),
        )
        pen.curveTo(
            round_pt((cx - k, cy + r)),
            round_pt((cx - r, cy + k)),
            round_pt((cx - r, cy)),
        )
        pen.curveTo(
            round_pt((cx - r, cy - k)),
            round_pt((cx - k, cy - r)),
            round_pt((cx, cy - r)),
        )
        pen.curveTo(
            round_pt((cx + k, cy - r)),
            round_pt((cx + r, cy - k)),
            round_pt((cx + r, cy)),
        )
        pen.closePath()
    else:
        # Clockwise (hole)
        pen.moveTo(round_pt((cx + r, cy)))
        pen.curveTo(
            round_pt((cx + r, cy - k)),
            round_pt((cx + k, cy - r)),
            round_pt((cx, cy - r)),
        )
        pen.curveTo(
            round_pt((cx - k, cy - r)),
            round_pt((cx - r, cy - k)),
            round_pt((cx - r, cy)),
        )
        pen.curveTo(
            round_pt((cx - r, cy + k)),
            round_pt((cx - k, cy + r)),
            round_pt((cx, cy + r)),
        )
        pen.curveTo(
            round_pt((cx + k, cy + r)),
            round_pt((cx + r, cy + k)),
            round_pt((cx + r, cy)),
        )
        pen.closePath()


def draw_annulus(pen: Any, cx: float, cy: float, r_outer: float, r_inner: float) -> None:
    """Draw a circular ring (outer CCW circle and inner CW hole)."""
    draw_circle(pen, cx, cy, r_outer, ccw=True)
    draw_circle(pen, cx, cy, r_inner, ccw=False)


def rotate_point(x: float, y: float, cx: float, cy: float, angle_deg: float) -> tuple[float, float]:
    """Rotate point (x, y) around center (cx, cy) by angle in degrees."""
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    dx = x - cx
    dy = y - cy
    return (cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a)


def rotate_points(
    points: Sequence[tuple[float, float]], cx: float, cy: float, angle_deg: float
) -> list[tuple[float, float]]:
    """Rotate a list of points around center (cx, cy)."""
    return [rotate_point(p[0], p[1], cx, cy, angle_deg) for p in points]


def star_vertices(
    cx: float, cy: float, r_outer: float, r_inner: float, points: int = 5, start_angle_deg: float = 90.0
) -> list[tuple[float, float]]:
    """Compute vertices of an n-pointed regular star in CCW order."""
    vertices = []
    total_steps = points * 2
    step_deg = 360.0 / total_steps

    for i in range(total_steps):
        angle = start_angle_deg + i * step_deg
        r = r_outer if (i % 2 == 0) else r_inner
        rad = math.radians(angle)
        x = cx + r * math.cos(rad)
        y = cy + r * math.sin(rad)
        vertices.append((x, y))
    return vertices


def draw_star(
    pen: Any,
    cx: float,
    cy: float,
    r_outer: float,
    r_inner: float,
    points: int = 5,
    ccw: bool = True,
) -> None:
    """Draw a solid n-pointed star."""
    verts = star_vertices(cx, cy, r_outer, r_inner, points)
    draw_polygon(pen, verts, ccw=ccw)


def draw_star_outline(
    pen: Any,
    cx: float,
    cy: float,
    r_outer: float,
    r_inner: float,
    r_outer_in: float,
    r_inner_in: float,
    points: int = 5,
) -> None:
    """Draw an outlined n-pointed star with uniform visual stroke."""
    outer_verts = star_vertices(cx, cy, r_outer, r_inner, points)
    inner_verts = star_vertices(cx, cy, r_outer_in, r_inner_in, points)
    draw_polygon(pen, outer_verts, ccw=True)
    draw_polygon(pen, inner_verts, ccw=False)
