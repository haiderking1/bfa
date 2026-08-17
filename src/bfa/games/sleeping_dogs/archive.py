"""Read-only parser and extractor for Sleeping Dogs BIG/BIX archives."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Dict, List, Optional, Union

from bfa.games.sleeping_dogs.compression import decompress_qcmp, is_qcmp
from bfa.games.sleeping_dogs.hash import qsymbol_hash, qsymbol_hex
from bfa.games.sleeping_dogs.models import ArchiveInfo, BigEntry

BIX_CHUNK_MAGIC = 0x2C5C40A8
BIX_SUBCHUNK_MAGIC = 0x2AE784F9


class BigArchive:
    """Read-only inspector and extractor for a paired .big and .bix archive."""

    def __init__(self, bix_path: Union[str, Path], big_path: Optional[Union[str, Path]] = None) -> None:
        self.bix_path = Path(bix_path)
        if big_path is None:
            self.big_path = self.bix_path.with_suffix(".big")
        else:
            self.big_path = Path(big_path)

        if not self.bix_path.is_file():
            raise FileNotFoundError(f"BIX index file not found: {self.bix_path}")
        if not self.big_path.is_file():
            raise FileNotFoundError(f"BIG archive file not found: {self.big_path}")

        self.archive_name = self.bix_path.name
        self.bix_size = self.bix_path.stat().st_size
        self.big_size = self.big_path.stat().st_size

        self.chunk_magic: str = ""
        self.subchunk_magic: str = ""
        self.subchunk_name: str = ""
        self.entry_count: int = 0
        self.entries: List[BigEntry] = []
        self._entries_by_hash: Dict[int, BigEntry] = {}

        self._read_index()

    def _read_index(self) -> None:
        with open(self.bix_path, "rb") as f:
            header_data = f.read(192)  # Read up to 0xc0
            if len(header_data) < 192:
                raise ValueError(f"BIX file {self.bix_path} is too small to contain valid header")

            # Chunk at 0x00
            c_type, c_size, c_usize, _ = struct.unpack_from("<IIII", header_data, 0x00)
            self.chunk_magic = f"0x{c_type:08x}"

            # Subchunk at 0x40
            sc_type, sc_size, sc_usize, _ = struct.unpack_from("<IIII", header_data, 0x40)
            self.subchunk_magic = f"0x{sc_type:08x}"
            name_bytes = header_data[0x44:0x60].split(b"\x00")[0]
            self.subchunk_name = name_bytes.decode("latin1", errors="replace")

            # Entry count at 0x70
            self.entry_count = struct.unpack_from("<I", header_data, 0x70)[0]

            # Read entry table
            f.seek(0xC0)
            table_bytes = f.read(self.entry_count * 24)
            if len(table_bytes) < self.entry_count * 24:
                raise ValueError(f"Truncated entry table in {self.bix_path}")

            for i in range(self.entry_count):
                sym, off, f2, f3, f4, f5 = struct.unpack_from("<6I", table_bytes, i * 24)
                is_comp = (f2 != 0 or f3 != 0)
                entry = BigEntry(
                    index=i,
                    symbol_hash=sym,
                    symbol_hex=f"0x{sym:08x}",
                    offset=off,
                    field2=f2,
                    field3=f3,
                    flags=f4,
                    size=f5,
                    is_compressed=is_comp,
                )
                self.entries.append(entry)
                self._entries_by_hash[sym] = entry

    def resolve_paths(self, path_dict: Dict[int, str]) -> int:
        """Associates resolved path names with entries matching known symbol hashes."""
        resolved = 0
        for entry in self.entries:
            if entry.symbol_hash in path_dict:
                entry.resolved_path = path_dict[entry.symbol_hash]
                resolved += 1
        return resolved

    def find_by_hash(self, symbol_hash: int) -> Optional[BigEntry]:
        """Finds an entry by symbol hash."""
        return self._entries_by_hash.get(symbol_hash)

    def find_by_path(self, path: str) -> Optional[BigEntry]:
        """Finds an entry by computing its symbol hash."""
        h = qsymbol_hash(path)
        return self.find_by_hash(h)

    def get_pmcq_offset(self, entry: BigEntry) -> int:
        """Calculates the exact byte offset of the PMCQ compressed block in the .big file."""
        return (entry.offset * 4) + (entry.field2 & 0xFFF)

    def read_raw_entry(self, entry: BigEntry) -> bytes:
        """Reads the raw bytes for an entry directly from the .big archive (read-only)."""
        if entry.size == 0 and not entry.is_compressed:
            return b""

        with open(self.big_path, "rb") as f:
            if entry.is_compressed and entry.field3 > 0:
                pmcq_off = self.get_pmcq_offset(entry)
                f.seek(pmcq_off)
                data = f.read(entry.field3)
                if len(data) < entry.field3:
                    raise IOError(
                        f"Unexpected EOF reading {entry.field3} bytes at {pmcq_off} in {self.big_path}"
                    )
                return data
            else:
                f.seek(entry.offset)
                data = f.read(entry.size)
                if len(data) < entry.size:
                    raise IOError(
                        f"Unexpected EOF reading {entry.size} bytes at {entry.offset} in {self.big_path}"
                    )
                return data

    def extract_entry(self, entry: BigEntry, decompress: bool = True) -> bytes:
        """Extracts and optionally decompresses an archive entry (read-only)."""
        raw_data = self.read_raw_entry(entry)
        if not decompress or not raw_data:
            return raw_data

        if entry.is_compressed or is_qcmp(raw_data):
            decomp = decompress_qcmp(raw_data, uncompressed_size=entry.size)
            if entry.size > 0 and len(decomp) < entry.size:
                decomp = decomp + bytes(entry.size - len(decomp))
            elif entry.size > 0 and len(decomp) > entry.size:
                decomp = decomp[: entry.size]
            return decomp

        return raw_data

    def get_info(self) -> ArchiveInfo:
        """Generates structured metadata for this archive."""
        comp_count = sum(1 for e in self.entries if e.is_compressed)
        uncomp_count = self.entry_count - comp_count
        return ArchiveInfo(
            archive_name=self.archive_name,
            bix_path=str(self.bix_path),
            big_path=str(self.big_path),
            bix_size=self.bix_size,
            big_size=self.big_size,
            entry_count=self.entry_count,
            compressed_entry_count=comp_count,
            uncompressed_entry_count=uncomp_count,
            chunk_magic=self.chunk_magic,
            subchunk_magic=self.subchunk_magic,
            subchunk_name=self.subchunk_name,
            entries=self.entries,
        )
