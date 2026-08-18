"""Patch Sleeping Dogs UI.big/UI.bix entries from an isolated overlay.

The stock executable only reads hashed resources from the archives. FileRedirector
requires a third-party exe and a dinput8 loader, which crashes Proton. This
module updates the UI archive pair from a one-time backup instead.
"""

from __future__ import annotations

import os
import shutil
import struct
from pathlib import Path
from typing import Mapping

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.hash import qsymbol_hash

BACKUP_SUFFIX = ".bfa-original"
BIX_ENTRY_OFFSET = 0xC0
BIX_ENTRY_SIZE = 24
BIG_ALIGNMENT = 4
PLUGIN_FILENAMES = ("dinput8.dll", "FileRedirector.asi")


def backup_path(path: Path) -> Path:
    """Returns the sibling backup path for an archive file."""
    return path.with_name(path.name + BACKUP_SUFFIX)


def ensure_archive_backup(bix_path: Path, big_path: Path) -> bool:
    """Copies the original UI archive pair once. Returns True if a backup was created."""
    bix_backup = backup_path(bix_path)
    big_backup = backup_path(big_path)
    if bix_backup.is_file() != big_backup.is_file():
        missing = bix_backup if not bix_backup.is_file() else big_backup
        raise ValueError(f"incomplete BFA archive backup pair: missing {missing}")
    if bix_backup.is_file():
        return False
    shutil.copy2(bix_path, bix_backup)
    shutil.copy2(big_path, big_backup)
    return True


def restore_archive_backup(bix_path: Path, big_path: Path) -> None:
    """Restores UI.bix/UI.big from the BFA backup before a new patch."""
    for working in (bix_path, big_path):
        original = backup_path(working)
        if not original.is_file():
            raise FileNotFoundError(f"missing archive backup: {original}")
        shutil.copy2(original, working)


def remove_incompatible_plugins(game_path: Path) -> list[str]:
    """Deletes the FileRedirector dinput8 loader that crashes the stock exe."""
    removed: list[str] = []
    root = Path(game_path)
    for name in PLUGIN_FILENAMES:
        path = root / name
        if path.is_file():
            path.unlink()
            removed.append(name)
    return removed


def apply_ui_replacements(game_path: Path, replacements: Mapping[str, bytes]) -> int:
    """Replaces hashed UI archive payloads, starting from the original backup.

    New bytes are written uncompressed and 4-byte aligned. Other archive entries
    keep their original payloads.
    """
    if not replacements:
        return 0
    root = Path(game_path)
    bix_path = root / "UI.bix"
    big_path = root / "UI.big"
    if not bix_path.is_file() or not big_path.is_file():
        raise FileNotFoundError(f"UI archive pair not found in {root}")

    ensure_archive_backup(bix_path, big_path)
    restore_archive_backup(bix_path, big_path)

    archive = BigArchive(bix_path, big_path)
    updates: list[tuple[int, int, int, int]] = []
    with big_path.open("r+b") as big:
        big.seek(0, os.SEEK_END)
        for resource_path, payload in replacements.items():
            entry = archive.find_by_path(resource_path)
            if entry is None:
                raise ValueError(f"resource {resource_path} is not in UI.bix")
            if qsymbol_hash(resource_path) != entry.symbol_hash:
                raise ValueError(f"hash mismatch for {resource_path}")
            position = _align_stream(big)
            big.write(payload)
            pad = (BIG_ALIGNMENT - (len(payload) % BIG_ALIGNMENT)) % BIG_ALIGNMENT
            if pad:
                big.write(b"\x00" * pad)
            updates.append((entry.index, entry.symbol_hash, position, len(payload)))

    with bix_path.open("r+b") as bix:
        for index, symbol_hash, position, size in updates:
            if position % BIG_ALIGNMENT:
                raise ValueError(f"payload offset {position} is not 4-byte aligned")
            bix.seek(BIX_ENTRY_OFFSET + index * BIX_ENTRY_SIZE)
            bix.write(struct.pack("<6I", symbol_hash, position // BIG_ALIGNMENT, 0, 0, 0, size))
    return len(updates)


def _align_stream(handle) -> int:
    position = handle.tell()
    pad = (BIG_ALIGNMENT - (position % BIG_ALIGNMENT)) % BIG_ALIGNMENT
    if pad:
        handle.write(b"\x00" * pad)
        position += pad
    return position
