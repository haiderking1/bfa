"""Minimal SWF/GFX bit and tag codecs used to rebuild Scaleform font movies."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

SWF_END = 0
SWF_DEFINE_FONT3 = 75


class BitWriter:
    """Packs SWF bit fields most-significant-bit first."""

    def __init__(self) -> None:
        self._bits: List[int] = []

    def write(self, value: int, nbits: int) -> None:
        if nbits < 0:
            raise ValueError("bit count must be non-negative")
        if nbits == 0:
            return
        mask = (1 << nbits) - 1
        value &= mask
        for shift in range(nbits - 1, -1, -1):
            self._bits.append((value >> shift) & 1)

    def write_signed(self, value: int, nbits: int) -> None:
        if nbits == 0:
            return
        minimum = -(1 << (nbits - 1))
        maximum = (1 << (nbits - 1)) - 1
        if value < minimum or value > maximum:
            raise ValueError(f"{value} does not fit in {nbits} signed bits")
        if value < 0:
            value = (1 << nbits) + value
        self.write(value, nbits)

    def align(self) -> None:
        while len(self._bits) % 8:
            self._bits.append(0)

    def to_bytes(self) -> bytes:
        self.align()
        out = bytearray()
        for index in range(0, len(self._bits), 8):
            byte = 0
            for bit in self._bits[index : index + 8]:
                byte = (byte << 1) | bit
            out.append(byte)
        return bytes(out)


class BitReader:
    """Reads SWF bit fields most-significant-bit first."""

    def __init__(self, data: bytes, byte_offset: int = 0) -> None:
        self._data = data
        self._bitpos = byte_offset * 8

    @property
    def byte_position(self) -> int:
        return (self._bitpos + 7) // 8

    def read(self, nbits: int) -> int:
        value = 0
        for _ in range(nbits):
            byte = self._data[self._bitpos // 8]
            bit = 7 - (self._bitpos % 8)
            value = (value << 1) | ((byte >> bit) & 1)
            self._bitpos += 1
        return value

    def read_signed(self, nbits: int) -> int:
        if nbits == 0:
            return 0
        value = self.read(nbits)
        if value & (1 << (nbits - 1)):
            value -= 1 << nbits
        return value

    def align(self) -> None:
        remainder = self._bitpos % 8
        if remainder:
            self._bitpos += 8 - remainder


def signed_bit_count(values: Iterable[int], minimum: int = 0) -> int:
    """Returns the number of signed bits needed to store every value."""
    needed = minimum
    for value in values:
        for bits in range(minimum, 33):
            if bits == 0:
                if value == 0:
                    break
                continue
            low = -(1 << (bits - 1))
            high = (1 << (bits - 1)) - 1
            if low <= value <= high:
                needed = max(needed, bits)
                break
        else:
            raise ValueError(f"{value} does not fit in a 32-bit SWF field")
    return needed


def encode_rect(xmin: int, xmax: int, ymin: int, ymax: int) -> bytes:
    """Encodes a SWF RECT."""
    nbits = signed_bit_count((xmin, xmax, ymin, ymax), minimum=0)
    writer = BitWriter()
    writer.write(nbits, 5)
    writer.write_signed(xmin, nbits)
    writer.write_signed(xmax, nbits)
    writer.write_signed(ymin, nbits)
    writer.write_signed(ymax, nbits)
    return writer.to_bytes()


def decode_rect(data: bytes, offset: int = 0) -> Tuple[Tuple[int, int, int, int], int]:
    """Decodes a SWF RECT and returns ((xmin, xmax, ymin, ymax), bytes_consumed)."""
    reader = BitReader(data, offset)
    nbits = reader.read(5)
    coords = tuple(reader.read_signed(nbits) for _ in range(4))
    reader.align()
    return (coords[0], coords[1], coords[2], coords[3]), reader.byte_position - offset


@dataclass(frozen=True, slots=True)
class SwfTag:
    code: int
    payload: bytes


def parse_swf_tags(data: bytes, offset: int = 0) -> Tuple[List[SwfTag], int]:
    """Parses SWF tags until End. Returns (tags, end_offset)."""
    tags: List[SwfTag] = []
    pos = offset
    while pos + 2 <= len(data):
        code_and_length = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        code = code_and_length >> 6
        length = code_and_length & 0x3F
        if length == 0x3F:
            if pos + 4 > len(data):
                raise ValueError("truncated long SWF tag header")
            length = struct.unpack_from("<I", data, pos)[0]
            pos += 4
        if pos + length > len(data):
            raise ValueError("truncated SWF tag payload")
        payload = data[pos : pos + length]
        pos += length
        tags.append(SwfTag(code=code, payload=payload))
        if code == SWF_END:
            break
    return tags, pos


def encode_swf_tag(tag: SwfTag) -> bytes:
    """Encodes one SWF tag header plus payload."""
    length = len(tag.payload)
    if length < 0x3F:
        header = struct.pack("<H", (tag.code << 6) | length)
    else:
        header = struct.pack("<HI", (tag.code << 6) | 0x3F, length)
    return header + tag.payload


def encode_swf_tags(tags: Sequence[SwfTag]) -> bytes:
    """Encodes a complete SWF tag list."""
    return b"".join(encode_swf_tag(tag) for tag in tags)


def encode_dummy_font_bounds() -> bytes:
    """Encodes a zero RECT with nBits=1, matching stock Sleeping Dogs FontBoundsTable entries."""
    writer = BitWriter()
    writer.write(1, 5)
    for _ in range(4):
        writer.write_signed(0, 1)
    return writer.to_bytes()


def first_style_change_fills(shape: bytes) -> Tuple[int, int, int]:
    """Returns (num_fill_bits, fill_style0, fill_style1) for the first style change.

    Empty glyphs have no style change and return (1, 0, 0).
    """
    reader = BitReader(shape)
    num_fill_bits = reader.read(4)
    _num_line_bits = reader.read(4)
    type_flag = reader.read(1)
    if type_flag != 0:
        raise ValueError("glyph shape does not start with a style-change or end record")
    state_new_styles = reader.read(1)
    state_line_style = reader.read(1)
    state_fill_style1 = reader.read(1)
    state_fill_style0 = reader.read(1)
    state_move_to = reader.read(1)
    if not any(
        (state_new_styles, state_line_style, state_fill_style1, state_fill_style0, state_move_to)
    ):
        return num_fill_bits, 0, 0
    if state_move_to:
        move_bits = reader.read(5)
        reader.read_signed(move_bits)
        reader.read_signed(move_bits)
    fill_style0 = reader.read(num_fill_bits) if state_fill_style0 else 0
    fill_style1 = reader.read(num_fill_bits) if state_fill_style1 else 0
    if state_line_style:
        reader.read(_num_line_bits)
    return num_fill_bits, fill_style0, fill_style1


def encode_empty_glyph_shape() -> bytes:
    """Encodes a DefineFont3 glyph with no contours.

    Matches the stock Sleeping Dogs fonts: NumFillBits=1, NumLineBits=0, End.
    """
    writer = BitWriter()
    writer.write(1, 4)
    writer.write(0, 4)
    writer.write(0, 6)
    return writer.to_bytes()


def encode_glyph_shape(contours: Sequence[Sequence[Tuple[str, Tuple[int, int], Tuple[int, int] | None]]]) -> bytes:
    """Encodes a DefineFont3 SHAPE from integer SWF contours.

    Each contour item is one of:
      ("move", (x, y), None)
      ("line", (x, y), None)
      ("curve", (anchor_x, anchor_y), (control_x, control_y))
    """
    writer = BitWriter()
    writer.write(1, 4)
    writer.write(0, 4)
    first_contour = True
    for contour in contours:
        for command, point, control in contour:
            if command == "move":
                _write_style_change(writer, point[0], point[1], set_fill=first_contour)
                first_contour = False
            elif command == "line":
                _write_straight_edge(writer, point[0], point[1])
            elif command == "curve":
                if control is None:
                    raise ValueError("curve command requires a control point")
                _write_curved_edge(writer, control[0], control[1], point[0], point[1])
            else:
                raise ValueError(f"unknown shape command {command!r}")
    writer.write(0, 6)
    return writer.to_bytes()


def _write_style_change(writer: BitWriter, x: int, y: int, *, set_fill: bool) -> None:
    writer.write(0, 1)  # TypeFlag = style change
    writer.write(0, 1)  # StateNewStyles
    writer.write(0, 1)  # StateLineStyle
    writer.write(0, 1)  # StateFillStyle1
    writer.write(1 if set_fill else 0, 1)  # StateFillStyle0
    writer.write(1, 1)  # StateMoveTo
    move_bits = signed_bit_count((x, y), minimum=1)
    writer.write(move_bits, 5)
    writer.write_signed(x, move_bits)
    writer.write_signed(y, move_bits)
    if set_fill:
        writer.write(1, 1)  # FillStyle0 = 1, NumFillBits is 1


def _write_straight_edge(writer: BitWriter, dx: int, dy: int) -> None:
    writer.write(1, 1)  # TypeFlag = edge
    writer.write(1, 1)  # StraightFlag
    nbits = _edge_bit_count((dx, dy))
    writer.write(nbits - 2, 4)
    if dx != 0 and dy != 0:
        writer.write(1, 1)  # GeneralLineFlag
        writer.write_signed(dx, nbits)
        writer.write_signed(dy, nbits)
        return
    writer.write(0, 1)
    if dy != 0:
        writer.write(1, 1)  # VertLineFlag
        writer.write_signed(dy, nbits)
    else:
        writer.write(0, 1)
        writer.write_signed(dx, nbits)


def _write_curved_edge(
    writer: BitWriter,
    control_dx: int,
    control_dy: int,
    anchor_dx: int,
    anchor_dy: int,
) -> None:
    writer.write(1, 1)
    writer.write(0, 1)
    nbits = _edge_bit_count((control_dx, control_dy, anchor_dx, anchor_dy))
    writer.write(nbits - 2, 4)
    writer.write_signed(control_dx, nbits)
    writer.write_signed(control_dy, nbits)
    writer.write_signed(anchor_dx, nbits)
    writer.write_signed(anchor_dy, nbits)


def _edge_bit_count(values: Iterable[int]) -> int:
    nbits = signed_bit_count(values, minimum=2)
    if nbits > 17:
        raise ValueError(f"SWF edge delta requires {nbits} bits; DefineFont3 allows 17")
    return nbits
