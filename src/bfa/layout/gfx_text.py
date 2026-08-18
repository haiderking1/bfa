"""Decode Scaleform DefineEditText fields and the PlaceObject names that wrap them."""

from __future__ import annotations

import struct
from typing import Iterable, List, Sequence

from bfa.fonts.swf import BitReader, SwfTag, decode_rect, parse_swf_tags
from bfa.layout.models import TextFieldBox
from bfa.layout.twips import twips_to_pixels

SWF_DEFINE_EDIT_TEXT = 37
SWF_DEFINE_SPRITE = 39
SWF_PLACE_OBJECT2 = 26
SWF_PLACE_OBJECT3 = 70

_ALIGN = {0: "left", 1: "right", 2: "center", 3: "justify"}


def parse_define_edit_text(payload: bytes) -> dict:
    """Decodes one DefineEditText tag payload."""
    if len(payload) < 4:
        raise ValueError("DefineEditText payload is truncated")
    character_id = struct.unpack_from("<H", payload, 0)[0]
    (xmin, xmax, ymin, ymax), consumed = decode_rect(payload, 2)
    reader = BitReader(payload, 2 + consumed)
    has_text = reader.read(1)
    word_wrap = reader.read(1)
    multiline = reader.read(1)
    _password = reader.read(1)
    _read_only = reader.read(1)
    has_text_color = reader.read(1)
    has_max_length = reader.read(1)
    has_font = reader.read(1)
    has_font_class = reader.read(1)
    _auto_size = reader.read(1)
    has_layout = reader.read(1)
    _no_select = reader.read(1)
    _border = reader.read(1)
    _was_static = reader.read(1)
    html = reader.read(1)
    _use_outlines = reader.read(1)
    pos = reader.byte_position
    font_height = None
    if has_font:
        pos += 2
    if has_font_class:
        _name, pos = _read_cstring(payload, pos)
    if has_font:
        font_height = struct.unpack_from("<H", payload, pos)[0]
        pos += 2
    if has_text_color:
        pos += 4
    if has_max_length:
        pos += 2
    align = "left"
    if has_layout:
        align = _ALIGN.get(payload[pos], "unknown")
        pos += 9
    _variable, pos = _read_cstring(payload, pos)
    initial = ""
    if has_text:
        initial, pos = _read_cstring(payload, pos)
    width_twips = xmax - xmin
    height_twips = ymax - ymin
    return {
        "character_id": character_id,
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
        "width_twips": width_twips,
        "height_twips": height_twips,
        "word_wrap": bool(word_wrap),
        "multiline": bool(multiline),
        "html": bool(html),
        "align": align,
        "font_height_twips": font_height,
        "initial_text": initial,
    }


def instance_paths_for_character(tags: Sequence[SwfTag], character_id: int) -> List[str]:
    """Returns PlaceObject2/3 name paths from the movie timeline down to ``character_id``."""
    children: dict[int, list[tuple[int | None, str]]] = {}
    for parent_id, child_id, name in _iter_placements(tags):
        children.setdefault(parent_id, []).append((child_id, name))
    found: list[str] = []
    _walk_paths(children, parent_id=0, prefix=(), target=character_id, found=found)
    return found


def text_field_boxes(
    tags: Sequence[SwfTag],
    *,
    screen_path: str,
    screen_name: str,
    stage_width_px: float,
    stage_height_px: float,
) -> List[TextFieldBox]:
    """Builds a TextFieldBox for every DefineEditText, with every instance path."""
    boxes: list[TextFieldBox] = []
    for tag in tags:
        if tag.code != SWF_DEFINE_EDIT_TEXT:
            continue
        parsed = parse_define_edit_text(tag.payload)
        paths = instance_paths_for_character(tags, parsed["character_id"])
        if not paths:
            paths = [f"id{parsed['character_id']}"]
        font_size = parsed["font_height_twips"]
        for path in paths:
            boxes.append(
                TextFieldBox(
                    screen_path=screen_path,
                    screen_name=screen_name,
                    instance_path=path,
                    character_id=parsed["character_id"],
                    width_twips=parsed["width_twips"],
                    height_twips=parsed["height_twips"],
                    width_px=twips_to_pixels(parsed["width_twips"]),
                    height_px=twips_to_pixels(parsed["height_twips"]),
                    word_wrap=parsed["word_wrap"],
                    multiline=parsed["multiline"],
                    html=parsed["html"],
                    align=parsed["align"],
                    font_size_px=None if font_size is None else twips_to_pixels(font_size),
                    stage_width_px=stage_width_px,
                    stage_height_px=stage_height_px,
                )
            )
    boxes.sort(key=lambda item: (item.screen_path, item.instance_path, item.character_id))
    return boxes


def movie_stage_pixels(header: bytes) -> tuple[float, float]:
    """Returns (width_px, height_px) from a SWF/CFX movie header RECT."""
    (xmin, xmax, ymin, ymax), _consumed = decode_rect(header, 0)
    return twips_to_pixels(xmax - xmin), twips_to_pixels(ymax - ymin)


def _iter_placements(tags: Sequence[SwfTag]) -> Iterable[tuple[int, int | None, str]]:
    for tag in tags:
        parsed = _parse_placement_tag(tag)
        if parsed is not None:
            child_id, name = parsed
            yield 0, child_id, name
        elif tag.code == SWF_DEFINE_SPRITE:
            sprite_id = struct.unpack_from("<H", tag.payload, 0)[0]
            inner, _end = parse_swf_tags(tag.payload, 4)
            for inner_tag in inner:
                inner_parsed = _parse_placement_tag(inner_tag)
                if inner_parsed is None:
                    continue
                child_id, name = inner_parsed
                yield sprite_id, child_id, name


def _parse_placement_tag(tag: SwfTag) -> tuple[int | None, str] | None:
    if tag.code == SWF_PLACE_OBJECT2:
        return _parse_place_object2(tag.payload)
    if tag.code == SWF_PLACE_OBJECT3:
        return _parse_place_object3(tag.payload)
    return None


def _walk_paths(
    children: dict[int, list[tuple[int | None, str]]],
    *,
    parent_id: int,
    prefix: tuple[str, ...],
    target: int,
    found: list[str],
    seen: frozenset[int] = frozenset(),
) -> None:
    if parent_id in seen:
        return
    next_seen = seen | {parent_id}
    for child_id, name in children.get(parent_id, []):
        next_prefix = prefix + ((name,) if name else ())
        if child_id == target:
            found.append("/".join(next_prefix) if next_prefix else f"id{target}")
            continue
        if child_id is None:
            continue
        _walk_paths(
            children,
            parent_id=child_id,
            prefix=next_prefix,
            target=target,
            found=found,
            seen=next_seen,
        )


def _parse_place_object2(payload: bytes) -> tuple[int | None, str]:
    if len(payload) < 3:
        return None, ""
    flags = payload[0]
    pos = 3
    character_id = None
    if flags & 0x02:
        character_id = struct.unpack_from("<H", payload, pos)[0]
        pos += 2
    if flags & 0x04:
        pos = _skip_matrix(payload, pos)
    if flags & 0x08:
        pos = _skip_color_transform(payload, pos)
    if flags & 0x10:
        pos += 2
    name = ""
    if flags & 0x20:
        name, _end = _read_cstring(payload, pos)
    return character_id, name


def _parse_place_object3(payload: bytes) -> tuple[int | None, str]:
    """Reads CharacterId and Name from a PlaceObject3 tag."""
    if len(payload) < 4:
        return None, ""
    flags = payload[0]
    extra = payload[1]
    pos = 4
    has_class_name = bool(extra & 0x08) or (bool(extra & 0x10) and bool(flags & 0x02))
    if has_class_name:
        _class_name, pos = _read_cstring(payload, pos)
    character_id = None
    if flags & 0x02:
        character_id = struct.unpack_from("<H", payload, pos)[0]
        pos += 2
    if flags & 0x04:
        pos = _skip_matrix(payload, pos)
    if flags & 0x08:
        pos = _skip_color_transform(payload, pos)
    if flags & 0x10:
        pos += 2
    name = ""
    if flags & 0x20:
        name, _end = _read_cstring(payload, pos)
    return character_id, name


def _skip_matrix(payload: bytes, pos: int) -> int:
    reader = BitReader(payload, pos)
    if reader.read(1):
        nbits = reader.read(5)
        reader.read_signed(nbits)
        reader.read_signed(nbits)
    if reader.read(1):
        nbits = reader.read(5)
        reader.read_signed(nbits)
        reader.read_signed(nbits)
    nbits = reader.read(5)
    reader.read_signed(nbits)
    reader.read_signed(nbits)
    reader.align()
    return reader.byte_position


def _skip_color_transform(payload: bytes, pos: int) -> int:
    reader = BitReader(payload, pos)
    has_add = reader.read(1)
    has_mult = reader.read(1)
    nbits = reader.read(4)
    count = 4 if has_mult else 0
    count += 4 if has_add else 0
    for _ in range(count):
        reader.read_signed(nbits)
    reader.align()
    return reader.byte_position


def _read_cstring(data: bytes, pos: int) -> tuple[str, int]:
    if pos >= len(data):
        raise ValueError("DefineEditText string is truncated")
    end = data.find(b"\x00", pos)
    if end < 0:
        raise ValueError("DefineEditText string is missing a null terminator")
    return data[pos:end].decode("latin1"), end + 1
