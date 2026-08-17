"""QCMP (qcmp1) decompression implementation for United Front Games engine."""

from __future__ import annotations

import struct
from typing import Optional, Tuple


def is_qcmp(data: bytes) -> bool:
    """Checks if a byte sequence starts with a QCMP / PMCQ header."""
    if len(data) >= 4:
        return data[:4] in (b"QCMP", b"PMCQ")
    return False


def parse_qcmp_header(data: bytes) -> Optional[Tuple[str, int, int, int]]:
    """Parses a QCMP / PMCQ header if present.

    Returns:
        Tuple of (magic_str, uncompressed_size, compressed_size, data_offset) or None.
    """
    if len(data) >= 16 and is_qcmp(data):
        magic_bytes = data[:4]
        magic_str = magic_bytes.decode("latin1", errors="replace")
        if len(data) >= 40:
            # 40-byte PMCQ header format (used in Sleeping Dogs Definitive Edition)
            _, typ, ver, data_off, extra_sz, csize, usize, uhash = struct.unpack_from("<4sHHIIQQQ", data, 0)
            return magic_str, int(usize), int(csize), int(data_off)
        else:
            magic, usize, csize, extra = struct.unpack_from("<IIII", data, 0)
            return magic_str, usize, csize, 16
    return None


def decompress_qcmp(data: bytes, uncompressed_size: Optional[int] = None) -> bytes:
    """Decompresses a QCMP (qcmp1) compressed data stream.

    Args:
        data: Compressed bytes (starting with PMCQ/QCMP header or raw compressed payload).
        uncompressed_size: Expected uncompressed size if known.

    Returns:
        Decompressed byte array.
    """
    pos = 0
    src_len = len(data)

    if src_len >= 16 and is_qcmp(data):
        hdr = parse_qcmp_header(data)
        if hdr is not None:
            _, usize, csize, data_off = hdr
            pos = data_off
            if csize > 0 and csize < src_len:
                src_len = csize
            if uncompressed_size is None:
                uncompressed_size = usize

    # 32-entry circular history buffer holding packed (length << 16) | offset
    history = [0] * 32
    hist_idx = 0

    out = bytearray()

    while pos < src_len:
        tag = data[pos]
        pos += 1

        if tag < 0x20:
            # Literal run of length = tag + 1
            lit_len = tag + 1
            if pos + lit_len > src_len:
                lit_len = src_len - pos
            out.extend(data[pos : pos + lit_len])
            pos += lit_len
        else:
            mode = tag >> 5
            if mode == 1:
                # Retrieve match parameters from history slot
                hist_val = history[tag & 0x1F]
                match_off = hist_val & 0xFFFF
                match_len = hist_val >> 16
            else:
                # Read 2nd byte for 13-bit offset
                if pos >= src_len:
                    break
                byte2 = data[pos]
                pos += 1
                match_off = ((tag & 0x1F) << 8) | byte2

                if mode == 7:
                    # Extended length from 3rd byte
                    if pos >= src_len:
                        break
                    match_len = data[pos] + 1
                    pos += 1
                else:
                    # Match length is (tag >> 5) + 1. Verified against
                    # UILocalizationChunk resources whose uncompressed size
                    # and qResourceData header layout are independently known.
                    match_len = mode + 1

                # Update circular history cache
                history[hist_idx] = (match_len << 16) | (match_off & 0xFFFF)
                hist_idx = (hist_idx + 1) & 0x1F

            # Copy match from output history
            src_start = len(out) - match_off
            for i in range(match_len):
                if 0 <= src_start + i < len(out):
                    out.append(out[src_start + i])
                else:
                    out.append(0)

    return bytes(out)
