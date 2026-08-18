"""Sleeping Dogs Definitive Edition UILocalizationChunk decoder and encoder.

On-disk layout after QCMP (if any) is removed:

    qChunk (16 bytes)
        u32 Id           = 0x90CE6B7A  (qSymbol of "UILocalizationChunk")
        u32 ChunkSize
        u32 DataSize
        u32 DataOffset
    qResourceData (0x58 bytes, file offset 0x10)
        +0x18  u32 mNameUID          (qSymbol of the debug name)
        +0x30  u32 mTypeUID          (0x90CE6B7A)
        +0x34  char debug_name[36]
    UILocalizationChunk extras (file offset 0x68)
        u32 mChunkSize
        u32 mPadding
        qOffset64 mChunkData         (byte offset from this field; low 2 bits are flags)
    chunk payload (typically at 0x78 when qOffset == 8)
        u32 hash_table_size          (entry_count * 4)
        u32 string_pool_size
        u32 hashes[entry_count]      (sorted ascending; qStringHashUpper32 of the key)
        char strings[]               (UTF-8, null-terminated, same order as hashes)

Control tags such as <br>, <font ...>, and <img ...> are stored as literal UTF-8
text inside the string pool and are preserved exactly.
"""

from __future__ import annotations

import re
import struct
from typing import List, Tuple

from bfa.games.sleeping_dogs.hash import qsymbol_hash
from bfa.games.sleeping_dogs.models import LocalizationEntry, LocalizationTable

UI_LOCALIZATION_CHUNK_UID = 0x90CE6B7A
QRESOURCE_DATA_SIZE = 0x58
QCHUNK_SIZE = 0x10
CHUNK_EXTRAS_OFFSET = QCHUNK_SIZE + QRESOURCE_DATA_SIZE  # 0x68
NAME_UID_OFFSET = 0x28
TYPE_UID_OFFSET = 0x40
DEBUG_NAME_OFFSET = 0x44
DEBUG_NAME_SIZE = 36
QOFFSET_FLAG_MASK = 0x3
FILE_ALIGNMENT = 8
QCHUNK_SIZE_FIELD_OFFSET = 4
QCHUNK_DATA_SIZE_FIELD_OFFSET = 8
_ENTITY_RE = re.compile(r"&(?:[A-Za-z]+|#\d+|#x[0-9A-Fa-f]+);", re.IGNORECASE)


def is_uilocalization_chunk(data: bytes) -> bool:
    """Returns True if data starts with a UILocalizationChunk qChunk header."""
    if len(data) < 4:
        return False
    return struct.unpack_from("<I", data, 0)[0] == UI_LOCALIZATION_CHUNK_UID


def _read_cstring(data: bytes, pos: int, limit: int) -> Tuple[str, int]:
    if pos >= limit:
        raise ValueError("Localization string pool is truncated")
    end = data.find(b"\x00", pos, limit)
    if end < 0:
        raise ValueError("Localization string is missing a null terminator")
    raw = data[pos:end]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Localization string is not valid UTF-8") from exc
    return text, end + 1


def parse_uilocalization_chunk(data: bytes) -> LocalizationTable:
    """Decodes a decompressed UILocalizationChunk into hashed UTF-8 strings.

    Raises ValueError if the buffer is not a well-formed localization chunk or
    if the string pool is not valid UTF-8.
    """
    if not is_uilocalization_chunk(data):
        raise ValueError("Buffer is not a UILocalizationChunk (missing 0x90CE6B7A)")
    if len(data) < CHUNK_EXTRAS_OFFSET + 16:
        raise ValueError("UILocalizationChunk is truncated before the string table")

    qchunk_id, qchunk_size, qchunk_data_size, qchunk_data_offset = struct.unpack_from(
        "<IIII", data, 0
    )
    name_uid = struct.unpack_from("<I", data, NAME_UID_OFFSET)[0]
    type_uid = struct.unpack_from("<I", data, TYPE_UID_OFFSET)[0]
    debug_name = (
        data[DEBUG_NAME_OFFSET : DEBUG_NAME_OFFSET + DEBUG_NAME_SIZE]
        .split(b"\x00", 1)[0]
        .decode("latin1")
    )

    m_chunk_size, m_padding = struct.unpack_from("<II", data, CHUNK_EXTRAS_OFFSET)
    qoffset = struct.unpack_from("<Q", data, CHUNK_EXTRAS_OFFSET + 8)[0]
    payload_off = (CHUNK_EXTRAS_OFFSET + 8) + (qoffset & ~QOFFSET_FLAG_MASK)

    if payload_off + 8 > len(data):
        raise ValueError("UILocalizationChunk qOffset points past the buffer")
    if m_chunk_size < 8 or payload_off + m_chunk_size > len(data):
        raise ValueError("UILocalizationChunk mChunkSize is invalid")

    hash_table_size, string_pool_size = struct.unpack_from("<II", data, payload_off)
    if hash_table_size % 4 != 0:
        raise ValueError("Localization hash table size is not a multiple of 4")

    entry_count = hash_table_size // 4
    expected_payload = 8 + hash_table_size + string_pool_size
    if expected_payload > m_chunk_size:
        raise ValueError("Localization hash table and string pool exceed mChunkSize")

    hashes_off = payload_off + 8
    pool_off = hashes_off + hash_table_size
    pool_end = pool_off + string_pool_size
    if pool_end > payload_off + m_chunk_size:
        raise ValueError("Localization string pool exceeds mChunkSize")

    hashes = list(struct.unpack_from(f"<{entry_count}I", data, hashes_off)) if entry_count else []
    if hashes != sorted(hashes):
        raise ValueError("Localization hash table is not sorted ascending")

    entries: List[LocalizationEntry] = []
    cursor = pool_off
    for key_hash in hashes:
        text, cursor = _read_cstring(data, cursor, pool_end)
        key_string = text if qsymbol_hash(text) == key_hash else None
        entries.append(
            LocalizationEntry(key_hash=key_hash, text=text, key_string=key_string)
        )

    string_pool_padding = data[cursor:pool_end]
    chunk_payload_padding = data[pool_end : payload_off + m_chunk_size]
    tail_padding = data[payload_off + m_chunk_size :]
    prefix = data[:payload_off]

    return LocalizationTable(
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
        encoding="UTF-8",
        entries=entries,
        string_pool_padding=string_pool_padding,
        chunk_payload_padding=chunk_payload_padding,
        tail_padding=tail_padding,
        prefix=prefix,
        source_size=len(data),
    )


def _encode_string_pool(entries: List[LocalizationEntry]) -> bytes:
    parts: List[bytes] = []
    for entry in entries:
        raw = entry.text.encode("utf-8")
        if b"\x00" in raw:
            raise ValueError("Localization string contains an embedded null byte")
        parts.append(raw + b"\x00")
    return b"".join(parts)


def encode_uilocalization_chunk(
    table: LocalizationTable,
    *,
    recompute_layout: bool = False,
) -> bytes:
    """Re-encodes a parsed UILocalizationChunk.

    A no-op decode/encode of an unmodified table must reproduce the original
    bytes, including control tags, null terminators, and padding.

    When string lengths change, pass recompute_layout=True so the string pool
    size, mChunkSize, qChunk size/data-size, and 8-byte file padding are
    rewritten for the new payload.
    """
    hash_blob = b"".join(struct.pack("<I", entry.key_hash) for entry in table.entries)
    pool = _encode_string_pool(table.entries)
    if recompute_layout:
        string_pool_padding = b""
        chunk_payload_padding = b""
    else:
        string_pool_padding = table.string_pool_padding
        chunk_payload_padding = table.chunk_payload_padding
    pool += string_pool_padding
    payload = (
        struct.pack("<II", len(hash_blob), len(pool))
        + hash_blob
        + pool
        + chunk_payload_padding
    )

    prefix = bytearray(table.prefix)
    if len(prefix) < CHUNK_EXTRAS_OFFSET + 16:
        raise ValueError("Localization table prefix is too short to re-encode")

    if recompute_layout:
        unpadded = len(prefix) + len(payload)
        pad = (FILE_ALIGNMENT - (unpadded % FILE_ALIGNMENT)) % FILE_ALIGNMENT
        tail_padding = b"\x00" * pad
    else:
        tail_padding = table.tail_padding

    struct.pack_into("<I", prefix, CHUNK_EXTRAS_OFFSET, len(payload))
    struct.pack_into("<I", prefix, CHUNK_EXTRAS_OFFSET + 4, table.m_padding)
    struct.pack_into("<Q", prefix, CHUNK_EXTRAS_OFFSET + 8, table.qoffset)

    qchunk_size = len(prefix) + len(payload) + len(tail_padding) - QCHUNK_SIZE
    struct.pack_into("<I", prefix, QCHUNK_SIZE_FIELD_OFFSET, qchunk_size)
    struct.pack_into("<I", prefix, QCHUNK_DATA_SIZE_FIELD_OFFSET, qchunk_size)
    return bytes(prefix) + payload + tail_padding


def localization_control_tag_spans(text: str) -> List[Tuple[int, int, str]]:
    """Returns (start, end, tag) spans in the same order as localization_control_tags."""
    tags: List[Tuple[int, int, str]] = []
    lower = text.lower()
    start = 0
    while True:
        open_at = lower.find("<", start)
        if open_at < 0:
            break
        close_at = lower.find(">", open_at + 1)
        if close_at < 0:
            break
        tags.append((open_at, close_at + 1, text[open_at : close_at + 1]))
        start = close_at + 1
    for match in _ENTITY_RE.finditer(text):
        tags.append((match.start(), match.end(), match.group()))
    return tags


def localization_control_tags(text: str) -> List[str]:
    """Returns literal control-tag substrings present in a decoded string."""
    return [tag for _start, _end, tag in localization_control_tag_spans(text)]


def table_binary_evidence(table: LocalizationTable) -> dict:
    """Machine-readable binary evidence that does not claim printable leftovers are strings."""
    return {
        "qchunk_id_hex": f"0x{table.qchunk_id:08x}",
        "qchunk_size": table.qchunk_size,
        "qchunk_data_size": table.qchunk_data_size,
        "qchunk_data_offset": table.qchunk_data_offset,
        "type_uid_hex": f"0x{table.type_uid:08x}",
        "name_uid_hex": f"0x{table.name_uid:08x}",
        "debug_name": table.debug_name,
        "m_chunk_size": table.m_chunk_size,
        "m_padding": table.m_padding,
        "qoffset": table.qoffset,
        "entry_count": len(table.entries),
        "string_pool_padding_size": len(table.string_pool_padding),
        "chunk_payload_padding_size": len(table.chunk_payload_padding),
        "tail_padding_size": len(table.tail_padding),
        "encoding": table.encoding,
        "hashes_are_qsymbol_keys": all(e.key_string is not None for e in table.entries),
    }
