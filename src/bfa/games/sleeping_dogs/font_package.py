"""Parse and rebuild Sleeping Dogs UIScreenChunk Scaleform font packages."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from typing import List

from bfa.fonts.define_font3 import parse_define_font3
from bfa.fonts.swf import (
    SWF_DEFINE_FONT3,
    SWF_END,
    SwfTag,
    decode_rect,
    encode_swf_tags,
    parse_swf_tags,
)

UI_SCREEN_CHUNK_UID = 0x442A39D9
QCHUNK_SIZE = 0x10
QRESOURCE_DATA_SIZE = 0x58
CHUNK_EXTRAS_OFFSET = QCHUNK_SIZE + QRESOURCE_DATA_SIZE
CFX_OFFSET = 0x78
FILE_ALIGNMENT = 8
CFX_SIGNATURE = b"CFX"
CFX_VERSION = 8


@dataclass(frozen=True, slots=True)
class GfxFontMovie:
    header: bytes
    tags: List[SwfTag]


@dataclass(frozen=True, slots=True)
class UiScreenFontPackage:
    prefix: bytes
    movie: GfxFontMovie
    debug_name: str
    name_uid: int
    type_uid: int
    qchunk_id: int
    qchunk_size: int
    qchunk_data_size: int
    qchunk_data_offset: int
    m_chunk_size: int
    m_padding: int
    qoffset: int
    source_size: int


def is_uiscreen_chunk(data: bytes) -> bool:
    """Returns True if data starts with a UIScreenChunk qChunk header."""
    if len(data) < 4:
        return False
    return struct.unpack_from("<I", data, 0)[0] == UI_SCREEN_CHUNK_UID


def parse_uiscreen_font_package(data: bytes) -> UiScreenFontPackage:
    """Decodes a FontsEnglish.bin-style UIScreenChunk wrapping a CFX movie."""
    if not is_uiscreen_chunk(data):
        raise ValueError("Buffer is not a UIScreenChunk (missing 0x442A39D9)")
    if len(data) < CFX_OFFSET + 8:
        raise ValueError("UIScreenChunk is truncated before the CFX movie")

    qchunk_id, qchunk_size, qchunk_data_size, qchunk_data_offset = struct.unpack_from(
        "<IIII", data, 0
    )
    name_uid = struct.unpack_from("<I", data, 0x28)[0]
    type_uid = struct.unpack_from("<I", data, 0x40)[0]
    debug_name = data[0x44:0x68].split(b"\x00", 1)[0].decode("latin1")
    m_chunk_size, m_padding = struct.unpack_from("<II", data, CHUNK_EXTRAS_OFFSET)
    qoffset = struct.unpack_from("<Q", data, CHUNK_EXTRAS_OFFSET + 8)[0]
    payload_off = (CHUNK_EXTRAS_OFFSET + 8) + (qoffset & ~0x3)
    if payload_off != CFX_OFFSET:
        raise ValueError(f"UIScreenChunk CFX offset is {payload_off}, expected {CFX_OFFSET}")
    if payload_off + 8 > len(data):
        raise ValueError("UIScreenChunk qOffset points past the buffer")

    cfx = data[payload_off:]
    movie = parse_cfx_movie(cfx)
    return UiScreenFontPackage(
        prefix=data[:payload_off],
        movie=movie,
        debug_name=debug_name,
        name_uid=name_uid,
        type_uid=type_uid,
        qchunk_id=qchunk_id,
        qchunk_size=qchunk_size,
        qchunk_data_size=qchunk_data_size,
        qchunk_data_offset=qchunk_data_offset,
        m_chunk_size=m_chunk_size,
        m_padding=m_padding,
        qoffset=qoffset,
        source_size=len(data),
    )


def encode_uiscreen_font_package(package: UiScreenFontPackage, movie: GfxFontMovie) -> bytes:
    """Wraps a rebuilt GFX movie in the original UIScreenChunk header."""
    cfx = encode_cfx_movie(movie)
    prefix = bytearray(package.prefix)
    if len(prefix) < CHUNK_EXTRAS_OFFSET + 16:
        raise ValueError("UIScreenChunk prefix is too short to re-encode")

    unpadded = len(prefix) + len(cfx)
    pad = (FILE_ALIGNMENT - (unpadded % FILE_ALIGNMENT)) % FILE_ALIGNMENT
    tail = b"\x00" * pad
    struct.pack_into("<I", prefix, CHUNK_EXTRAS_OFFSET, len(cfx))
    struct.pack_into("<I", prefix, CHUNK_EXTRAS_OFFSET + 4, package.m_padding)
    struct.pack_into("<Q", prefix, CHUNK_EXTRAS_OFFSET + 8, package.qoffset)
    qchunk_size = len(prefix) + len(cfx) + len(tail) - QCHUNK_SIZE
    struct.pack_into("<I", prefix, 4, qchunk_size)
    struct.pack_into("<I", prefix, 8, qchunk_size)
    return bytes(prefix) + cfx + tail


def parse_cfx_movie(data: bytes) -> GfxFontMovie:
    """Decompresses a CFX block into SWF tags."""
    if len(data) < 8 or data[:3] != CFX_SIGNATURE:
        raise ValueError("Font package payload is not a CFX movie")
    version = data[3]
    if version not in {8, 10}:
        raise ValueError(f"Unsupported CFX version {version}")
    file_length = struct.unpack_from("<I", data, 4)[0]
    if file_length < 8:
        raise ValueError("CFX fileLength is smaller than the CFX header")
    body = zlib.decompress(data[8:])
    if len(body) < file_length - 8:
        raise ValueError("CFX zlib payload is shorter than fileLength")
    body = body[: file_length - 8]
    _rect, rect_size = decode_rect(body, 0)
    header_size = rect_size + 4
    if header_size > len(body):
        raise ValueError("CFX movie header is truncated")
    tags, end = parse_swf_tags(body, header_size)
    if not tags or tags[-1].code != SWF_END:
        raise ValueError("CFX movie is missing an End tag")
    if end != len(body):
        raise ValueError("CFX movie has trailing bytes after End")
    return GfxFontMovie(header=body[:header_size], tags=tags)


def encode_cfx_movie(movie: GfxFontMovie) -> bytes:
    """Compresses a GFX movie as a version-8 CFX block."""
    body = movie.header + encode_swf_tags(movie.tags)
    file_length = 8 + len(body)
    header = CFX_SIGNATURE + bytes([CFX_VERSION]) + struct.pack("<I", file_length)
    return header + zlib.compress(body, 9)


def font3_tags(movie: GfxFontMovie) -> List[SwfTag]:
    """Returns the DefineFont3 tags inside a font movie."""
    return [tag for tag in movie.tags if tag.code == SWF_DEFINE_FONT3]


def replace_define_font3_payloads(movie: GfxFontMovie, payloads: List[bytes]) -> GfxFontMovie:
    """Replaces DefineFont3 payloads in movie order."""
    expected = len(font3_tags(movie))
    if len(payloads) != expected:
        raise ValueError(
            f"DefineFont3 count mismatch: movie has {expected}, replacement has {len(payloads)}"
        )
    replaced: List[SwfTag] = []
    index = 0
    for tag in movie.tags:
        if tag.code == SWF_DEFINE_FONT3:
            replaced.append(SwfTag(code=SWF_DEFINE_FONT3, payload=payloads[index]))
            index += 1
        else:
            replaced.append(tag)
    return GfxFontMovie(header=movie.header, tags=replaced)


def listed_font_names(movie: GfxFontMovie) -> List[str]:
    """Returns DefineFont3 family names in movie order."""
    return [parse_define_font3(tag.payload).name for tag in font3_tags(movie)]
