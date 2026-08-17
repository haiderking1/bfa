"""UFG (United Front Games) symbol hash implementation (qSymbol / qStringHashUpper32).

Sleeping Dogs: Definitive Edition hashes internal asset paths and identifiers using
a 32-bit CRC with polynomial 0x04C11DB7, non-reflected table, initial value 0xFFFFFFFF,
and uppercase Latin-1 normalization with backslashes.
"""

from __future__ import annotations

from typing import List


def _generate_crc32_table() -> List[int]:
    """Generates the 256-entry CRC32 table used by United Front Games engine."""
    poly = 0x04C11DB7
    table: List[int] = []
    for i in range(256):
        curr = (i << 24) & 0xFFFFFFFF
        for _ in range(8):
            if curr & 0x80000000:
                curr = ((curr << 1) ^ poly) & 0xFFFFFFFF
            else:
                curr = (curr << 1) & 0xFFFFFFFF
        table.append(curr)
    return table


CRC32_TABLE: List[int] = _generate_crc32_table()


def normalize_path(path: str) -> str:
    """Normalizes an asset path for Sleeping Dogs symbol hashing.

    The engine converts forward slashes to backslashes and matches case-insensitively.
    """
    return path.replace("/", "\\")


def qsymbol_hash(text: str, init_val: int = 0xFFFFFFFF) -> int:
    """Computes the UFG qSymbol / qSymbolUC / qStringHashUpper32 integer hash.

    Args:
        text: String or path to hash.
        init_val: Initial seed value (default 0xFFFFFFFF).

    Returns:
        32-bit unsigned integer symbol hash.
    """
    normalized = normalize_path(text).upper()
    data = normalized.encode("latin1", errors="replace")

    h = init_val & 0xFFFFFFFF
    for b in data:
        idx = ((h >> 24) ^ b) & 0xFF
        h = ((h << 8) & 0xFFFFFFFF) ^ CRC32_TABLE[idx]

    return h & 0xFFFFFFFF


def qsymbol_hex(text: str, init_val: int = 0xFFFFFFFF) -> str:
    """Computes the UFG qSymbol hash formatted as a 0x-prefixed 8-character hex string."""
    return f"0x{qsymbol_hash(text, init_val):08x}"
