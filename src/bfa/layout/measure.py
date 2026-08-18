"""HarfBuzz advance widths at a Scaleform pixel font size."""

from __future__ import annotations

import uharfbuzz as hb

from bfa.fonts.shape import ShapeContext, has_arabic


def measure_text_px(text: str, context: ShapeContext, font_size_px: float) -> float:
    """Returns the ink width of ``text`` in pixels at ``font_size_px``.

    Uses the same HarfBuzz features as Arabic pre-shaping. Positions stay in
    font units (the shared ShapeContext scale is not mutated).
    """
    if text == "" or font_size_px == 0:
        return 0.0
    upem = context.font.face.upem
    if upem <= 0:
        raise ValueError("font unitsPerEm must be positive")
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if has_arabic(text):
        buf.direction = "rtl"
        buf.script = "Arab"
    hb.shape(context.font, buf, {"kern": True, "liga": True})
    positions = buf.glyph_positions
    if not positions:
        return 0.0
    return sum(position.x_advance for position in positions) * font_size_px / upem
