"""Legal and currency glyph builders."""

from __future__ import annotations

from typing import Any
from tooling.geometry import (
    draw_annulus,
    draw_circle,
    draw_polygon,
    draw_rect,
    round_pt,
)
from tooling.models import GlyphSpec


def draw_copyright(pen: Any) -> None:
    # Outer circle annulus: cx=650, cy=670, ro=470, ri=360
    draw_annulus(pen, 650.0, 670.0, r_outer=470.0, r_inner=360.0)

    # Inner 'C'
    # Outer arc CCW
    pen.moveTo(round_pt((810.0, 850.0)))
    pen.curveTo(
        round_pt((760.0, 920.0)),
        round_pt((690.0, 950.0)),
        round_pt((620.0, 950.0)),
    )
    pen.curveTo(
        round_pt((500.0, 950.0)),
        round_pt((440.0, 830.0)),
        round_pt((440.0, 670.0)),
    )
    pen.curveTo(
        round_pt((440.0, 510.0)),
        round_pt((500.0, 390.0)),
        round_pt((620.0, 390.0)),
    )
    pen.curveTo(
        round_pt((690.0, 390.0)),
        round_pt((760.0, 420.0)),
        round_pt((810.0, 490.0)),
    )
    pen.lineTo(round_pt((760.0, 550.0)))
    pen.curveTo(
        round_pt((720.0, 500.0)),
        round_pt((670.0, 480.0)),
        round_pt((620.0, 480.0)),
    )
    pen.curveTo(
        round_pt((540.0, 480.0)),
        round_pt((520.0, 570.0)),
        round_pt((520.0, 670.0)),
    )
    pen.curveTo(
        round_pt((520.0, 770.0)),
        round_pt((540.0, 860.0)),
        round_pt((620.0, 860.0)),
    )
    pen.curveTo(
        round_pt((670.0, 860.0)),
        round_pt((720.0, 840.0)),
        round_pt((760.0, 790.0)),
    )
    pen.closePath()


def draw_registered(pen: Any) -> None:
    # Outer circle annulus
    draw_annulus(pen, 650.0, 670.0, r_outer=470.0, r_inner=360.0)

    # Inner 'R'
    # Main outer contour of R
    pen.moveTo(round_pt((470.0, 410.0)))
    pen.lineTo(round_pt((560.0, 410.0)))
    pen.lineTo(round_pt((560.0, 660.0)))
    pen.lineTo(round_pt((680.0, 660.0)))
    pen.lineTo(round_pt((780.0, 410.0)))
    pen.lineTo(round_pt((870.0, 410.0)))
    pen.lineTo(round_pt((760.0, 680.0)))
    pen.curveTo(
        round_pt((810.0, 720.0)),
        round_pt((840.0, 780.0)),
        round_pt((840.0, 830.0)),
    )
    pen.curveTo(
        round_pt((840.0, 890.0)),
        round_pt((790.0, 930.0)),
        round_pt((700.0, 930.0)),
    )
    pen.lineTo(round_pt((470.0, 930.0)))
    pen.closePath()

    # Inner bowl hole of R (CW)
    pen.moveTo(round_pt((560.0, 740.0)))
    pen.lineTo(round_pt((560.0, 850.0)))
    pen.lineTo(round_pt((690.0, 850.0)))
    pen.curveTo(
        round_pt((730.0, 850.0)),
        round_pt((750.0, 830.0)),
        round_pt((750.0, 795.0)),
    )
    pen.curveTo(
        round_pt((750.0, 760.0)),
        round_pt((730.0, 740.0)),
        round_pt((690.0, 740.0)),
    )
    pen.closePath()


def draw_trademark(pen: Any) -> None:
    # Superscript 'T'
    draw_rect(pen, 100.0, 1280.0, 560.0, 1402.0, ccw=True)
    draw_rect(pen, 275.0, 750.0, 385.0, 1280.0, ccw=True)

    # Superscript 'M'
    m_verts = [
        (620.0, 750.0),
        (720.0, 750.0),
        (720.0, 1220.0),
        (825.0, 910.0),
        (895.0, 910.0),
        (1000.0, 1220.0),
        (1000.0, 750.0),
        (1100.0, 750.0),
        (1100.0, 1402.0),
        (980.0, 1402.0),
        (860.0, 1040.0),
        (740.0, 1402.0),
        (620.0, 1402.0),
    ]
    draw_polygon(pen, m_verts, ccw=True)


def draw_euro(pen: Any) -> None:
    # Main C-shaped curve
    pen.moveTo(round_pt((1050.0, 1160.0)))
    pen.curveTo(
        round_pt((960.0, 1290.0)),
        round_pt((840.0, 1402.0)),
        round_pt((680.0, 1402.0)),
    )
    pen.curveTo(
        round_pt((410.0, 1402.0)),
        round_pt((200.0, 1110.0)),
        round_pt((200.0, 701.0)),
    )
    pen.curveTo(
        round_pt((200.0, 292.0)),
        round_pt((410.0, 0.0)),
        round_pt((680.0, 0.0)),
    )
    pen.curveTo(
        round_pt((840.0, 0.0)),
        round_pt((960.0, 112.0)),
        round_pt((1050.0, 242.0)),
    )
    pen.lineTo(round_pt((960.0, 360.0)))
    pen.curveTo(
        round_pt((880.0, 270.0)),
        round_pt((790.0, 200.0)),
        round_pt((680.0, 200.0)),
    )
    pen.curveTo(
        round_pt((490.0, 200.0)),
        round_pt((390.0, 420.0)),
        round_pt((390.0, 701.0)),
    )
    pen.curveTo(
        round_pt((390.0, 982.0)),
        round_pt((490.0, 1202.0)),
        round_pt((680.0, 1202.0)),
    )
    pen.curveTo(
        round_pt((790.0, 1202.0)),
        round_pt((880.0, 1132.0)),
        round_pt((960.0, 1042.0)),
    )
    pen.closePath()

    # Double crossbars
    draw_rect(pen, 60.0, 770.0, 680.0, 890.0, ccw=True)
    draw_rect(pen, 60.0, 530.0, 680.0, 650.0, ccw=True)


def draw_pound(pen: Any) -> None:
    # Classic Pound sterling shape
    # Top arch and spine
    pen.moveTo(round_pt((120.0, 140.0)))
    pen.curveTo(
        round_pt((230.0, 300.0)),
        round_pt((380.0, 600.0)),
        round_pt((380.0, 850.0)),
    )
    pen.curveTo(
        round_pt((380.0, 1080.0)),
        round_pt((480.0, 1402.0)),
        round_pt((680.0, 1402.0)),
    )
    pen.curveTo(
        round_pt((810.0, 1402.0)),
        round_pt((900.0, 1310.0)),
        round_pt((900.0, 1180.0)),
    )
    pen.curveTo(
        round_pt((900.0, 1080.0)),
        round_pt((830.0, 1010.0)),
        round_pt((740.0, 1010.0)),
    )
    pen.curveTo(
        round_pt((670.0, 1010.0)),
        round_pt((610.0, 1060.0)),
        round_pt((610.0, 1130.0)),
    )
    pen.curveTo(
        round_pt((610.0, 1160.0)),
        round_pt((630.0, 1190.0)),
        round_pt((650.0, 1210.0)),
    )
    pen.curveTo(
        round_pt((630.0, 1240.0)),
        round_pt((590.0, 1250.0)),
        round_pt((560.0, 1250.0)),
    )
    pen.curveTo(
        round_pt((470.0, 1250.0)),
        round_pt((460.0, 1060.0)),
        round_pt((460.0, 850.0)),
    )
    pen.curveTo(
        round_pt((460.0, 650.0)),
        round_pt((340.0, 360.0)),
        round_pt((250.0, 140.0)),
    )
    pen.lineTo(round_pt((920.0, 140.0)))
    pen.lineTo(round_pt((920.0, 0.0)))
    pen.lineTo(round_pt((90.0, 0.0)))
    pen.lineTo(round_pt((90.0, 140.0)))
    pen.closePath()

    # Waist crossbar
    draw_rect(pen, 150.0, 600.0, 680.0, 720.0, ccw=True)


def draw_yen(pen: Any) -> None:
    # Upper V arms
    v_verts = [
        (90.0, 1402.0),
        (260.0, 1402.0),
        (550.0, 880.0),
        (840.0, 1402.0),
        (1010.0, 1402.0),
        (630.0, 720.0),
        (630.0, 0.0),
        (470.0, 0.0),
        (470.0, 720.0),
    ]
    draw_polygon(pen, v_verts, ccw=True)

    # Double crossbars
    draw_rect(pen, 180.0, 740.0, 920.0, 860.0, ccw=True)
    draw_rect(pen, 180.0, 520.0, 920.0, 640.0, ccw=True)


def get_legal_currency_specs() -> list[GlyphSpec]:
    return [
        GlyphSpec(0x00A9, "©", "copyright", 1300, "Legal & Currency", draw_copyright, "Copyright sign"),
        GlyphSpec(0x00AE, "®", "registered", 1300, "Legal & Currency", draw_registered, "Registered sign"),
        GlyphSpec(0x2122, "™", "trademark", 1200, "Legal & Currency", draw_trademark, "Trade mark sign"),
        GlyphSpec(0x20AC, "€", "Euro", 1200, "Legal & Currency", draw_euro, "Euro sign"),
        GlyphSpec(0x00A3, "£", "sterling", 1050, "Legal & Currency", draw_pound, "Pound sterling sign"),
        GlyphSpec(0x00A5, "¥", "yen", 1100, "Legal & Currency", draw_yen, "Yen sign"),
    ]
