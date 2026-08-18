"""Build and parse SWF DefineFont3 tags from an OpenType font."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from bfa.fonts.swf import encode_dummy_font_bounds, encode_empty_glyph_shape, encode_glyph_shape

FONT3_EM = 1024
FONT3_PRECISION = 20
FLAG_HAS_LAYOUT = 0x80
FLAG_WIDE_OFFSETS = 0x08
FLAG_WIDE_CODES = 0x04


@dataclass(frozen=True, slots=True)
class DefineFont3:
    font_id: int
    flags: int
    language: int
    name: str
    codes: List[int]
    shapes: List[bytes]
    ascent: int
    descent: int
    leading: int
    advances: List[int]
    bounds: List[Tuple[int, int, int, int]]


def font3_scale(units_per_em: int) -> float:
    """Maps font units onto DefineFont3's 20x 1024-EM grid."""
    if units_per_em <= 0:
        raise ValueError("unitsPerEm must be positive")
    return FONT3_PRECISION * FONT3_EM / units_per_em


def build_define_font3(
    font_path: Path,
    *,
    font_id: int,
    name: str,
    flags: int,
    language: int,
) -> bytes:
    """Creates a DefineFont3 payload whose outlines come from ``font_path``."""
    font = TTFont(str(font_path))
    try:
        record = define_font3_from_ttfont(
            font,
            font_id=font_id,
            name=name,
            flags=flags,
            language=language,
        )
        return encode_define_font3(record)
    finally:
        font.close()


def define_font3_from_ttfont(
    font: TTFont,
    *,
    font_id: int,
    name: str,
    flags: int,
    language: int,
) -> DefineFont3:
    """Converts a loaded OpenType font into a DefineFont3 description."""
    cmap = font.getBestCmap()
    if not cmap:
        raise ValueError("font has no Unicode cmap")
    codes = sorted(code for code in cmap if 0 < code <= 0xFFFF)
    if 32 not in codes:
        raise ValueError("font cmap is missing U+0020 SPACE")

    scale = font3_scale(int(font["head"].unitsPerEm))
    glyph_set = font.getGlyphSet()
    shapes: List[bytes] = []
    advances: List[int] = []
    bounds: List[Tuple[int, int, int, int]] = []

    for code in codes:
        glyph_name = cmap[code]
        width, _lsb = font["hmtx"][glyph_name]
        advances.append(_round_font3(width * scale))
        recording = RecordingPen()
        glyph_set[glyph_name].draw(
            Cu2QuPen(
                recording,
                max_err=1.0,
                reverse_direction="CFF " in font,
                all_quadratic=True,
            )
        )
        contours, _glyph_bounds = _recording_to_font3_contours(recording.value, scale)
        bounds.append((0, 0, 0, 0))
        if contours:
            shapes.append(encode_glyph_shape(contours))
        else:
            shapes.append(encode_empty_glyph_shape())

    ascent, descent, leading = _layout_metrics(font, scale)
    return DefineFont3(
        font_id=font_id,
        flags=flags | FLAG_HAS_LAYOUT | FLAG_WIDE_OFFSETS | FLAG_WIDE_CODES,
        language=language,
        name=name,
        codes=codes,
        shapes=shapes,
        ascent=ascent,
        descent=descent,
        leading=leading,
        advances=advances,
        bounds=bounds,
    )


def encode_define_font3(font: DefineFont3) -> bytes:
    """Serializes a DefineFont3 payload."""
    if len(font.codes) != len(font.shapes) or len(font.codes) != len(font.advances):
        raise ValueError("DefineFont3 glyph tables are different lengths")
    if len(font.bounds) != len(font.codes):
        raise ValueError("DefineFont3 bounds table is the wrong length")

    name_bytes = font.name.encode("latin1") + b"\x00"
    if len(name_bytes) > 255:
        raise ValueError("DefineFont3 name is longer than 255 bytes")

    offset_table = bytearray()
    glyph_blob = bytearray()
    offset_table_size = (len(font.codes) + 1) * 4
    for shape in font.shapes:
        offset_table.extend(struct.pack("<I", offset_table_size + len(glyph_blob)))
        glyph_blob.extend(shape)
    code_table_offset = offset_table_size + len(glyph_blob)
    offset_table.extend(struct.pack("<I", code_table_offset))

    code_table = struct.pack(f"<{len(font.codes)}H", *font.codes)
    advance_table = struct.pack(f"<{len(font.advances)}h", *font.advances)
    bounds_table = b"".join(encode_dummy_font_bounds() for _ in font.bounds)

    return b"".join(
        [
            struct.pack("<H", font.font_id),
            bytes([font.flags, font.language, len(name_bytes)]),
            name_bytes,
            struct.pack("<H", len(font.codes)),
            bytes(offset_table),
            bytes(glyph_blob),
            code_table,
            struct.pack("<hhh", font.ascent, font.descent, font.leading),
            advance_table,
            bounds_table,
            struct.pack("<H", 0),
        ]
    )


def parse_define_font3(payload: bytes) -> DefineFont3:
    """Parses a DefineFont3 payload far enough to verify names, codes, and layout."""
    if len(payload) < 8:
        raise ValueError("DefineFont3 payload is truncated")
    font_id = struct.unpack_from("<H", payload, 0)[0]
    flags = payload[2]
    language = payload[3]
    name_len = payload[4]
    name = payload[5 : 5 + name_len].split(b"\x00", 1)[0].decode("latin1")
    offset = 5 + name_len
    count = struct.unpack_from("<H", payload, offset)[0]
    offset += 2
    if not (flags & FLAG_WIDE_OFFSETS) or not (flags & FLAG_WIDE_CODES):
        raise ValueError("DefineFont3 parser requires wide offsets and wide codes")

    offset_table_start = offset
    offsets = [struct.unpack_from("<I", payload, offset + index * 4)[0] for index in range(count)]
    code_table_offset = struct.unpack_from("<I", payload, offset + count * 4)[0]
    shapes = []
    for index, glyph_offset in enumerate(offsets):
        start = offset_table_start + glyph_offset
        if index + 1 < count:
            end = offset_table_start + offsets[index + 1]
        else:
            end = offset_table_start + code_table_offset
        shapes.append(payload[start:end])

    codes_at = offset_table_start + code_table_offset
    codes = list(struct.unpack_from(f"<{count}H", payload, codes_at))
    layout_at = codes_at + count * 2
    ascent = descent = leading = 0
    advances: List[int] = [0] * count
    bounds: List[Tuple[int, int, int, int]] = [(0, 0, 0, 0)] * count
    if flags & FLAG_HAS_LAYOUT:
        ascent, descent, leading = struct.unpack_from("<hhh", payload, layout_at)
        advances = list(struct.unpack_from(f"<{count}h", payload, layout_at + 6))

    return DefineFont3(
        font_id=font_id,
        flags=flags,
        language=language,
        name=name,
        codes=codes,
        shapes=shapes,
        ascent=ascent,
        descent=descent,
        leading=leading,
        advances=advances,
        bounds=bounds,
    )


def _layout_metrics(font: TTFont, scale: float) -> Tuple[int, int, int]:
    hhea = font["hhea"]
    ascent = _round_font3(int(hhea.ascent) * scale)
    descent = _round_font3(abs(int(hhea.descent)) * scale)
    leading = _round_font3(int(hhea.lineGap) * scale)
    return ascent, descent, leading


def _round_font3(value: float) -> int:
    rounded = int(round(value))
    if rounded < -32768 or rounded > 32767:
        raise ValueError(f"DefineFont3 metric {rounded} is outside SI16")
    return rounded


def _recording_to_font3_contours(
    operations: Sequence[tuple],
    scale: float,
) -> Tuple[List[List[Tuple[str, Tuple[int, int], Tuple[int, int] | None]]], Tuple[int, int, int, int]]:
    contours: List[List[Tuple[str, Tuple[int, int], Tuple[int, int] | None]]] = []
    current: List[Tuple[str, Tuple[int, int], Tuple[int, int] | None]] = []
    cursor: Tuple[int, int] | None = None
    start: Tuple[int, int] | None = None
    xs: List[int] = []
    ys: List[int] = []

    def map_point(point: Tuple[float, float]) -> Tuple[int, int]:
        x = int(round(point[0] * scale))
        y = int(round(-point[1] * scale))
        xs.append(x)
        ys.append(y)
        return x, y

    for op, args in operations:
        if op == "moveTo":
            if current:
                contours.append(current)
                current = []
            cursor = start = map_point(args[0])
            current.append(("move", cursor, None))
        elif op == "lineTo":
            if cursor is None:
                raise ValueError("lineTo without a current point")
            dest = map_point(args[0])
            current.append(("line", (dest[0] - cursor[0], dest[1] - cursor[1]), None))
            cursor = dest
        elif op == "qCurveTo":
            if cursor is None:
                raise ValueError("qCurveTo without a current point")
            cursor = _append_quadratic(current, cursor, args, map_point, start)
        elif op == "closePath":
            if cursor is not None and start is not None and cursor != start:
                current.append(("line", (start[0] - cursor[0], start[1] - cursor[1]), None))
                cursor = start
            if current:
                contours.append(current)
                current = []
                start = None
        else:
            raise ValueError(f"unsupported outline command {op!r}")

    if current:
        contours.append(current)
    if not xs:
        return [], (0, 0, 0, 0)
    return contours, (min(xs), max(xs), min(ys), max(ys))


def _append_quadratic(
    current: List[Tuple[str, Tuple[int, int], Tuple[int, int] | None]],
    cursor: Tuple[int, int],
    args: Sequence,
    map_point,
    start: Tuple[int, int] | None,
) -> Tuple[int, int]:
    points = list(args)
    implied_close = points and points[-1] is None
    if implied_close:
        points = points[:-1]
    if not points:
        return cursor

    off_curve = [map_point(point) for point in (points[:-1] if not implied_close else points)]
    final_on = None if implied_close else map_point(points[-1])
    if implied_close:
        if start is None:
            raise ValueError("closed qCurveTo is missing a contour start")
        final_on = start

    for index, control in enumerate(off_curve):
        if index + 1 < len(off_curve):
            on_point = _midpoint(control, off_curve[index + 1])
        else:
            assert final_on is not None
            on_point = final_on
        current.append(
            (
                "curve",
                (on_point[0] - control[0], on_point[1] - control[1]),
                (control[0] - cursor[0], control[1] - cursor[1]),
            )
        )
        cursor = on_point
    return cursor


def _midpoint(left: Tuple[int, int], right: Tuple[int, int]) -> Tuple[int, int]:
    return (left[0] + right[0]) // 2, (left[1] + right[1]) // 2
