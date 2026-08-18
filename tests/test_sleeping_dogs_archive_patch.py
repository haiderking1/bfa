"""Tests for stock-exe UI.big/UI.bix patching without FileRedirector."""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.archive_patch import (
    BACKUP_SUFFIX,
    apply_ui_replacements,
    backup_path,
    ensure_archive_backup,
    remove_incompatible_plugins,
)
from bfa.games.sleeping_dogs.hash import qsymbol_hash

KEEP_PATH = r"Data\UI\Localization\EN_Keep.bin"
LOC_PATH = r"Data\UI\Localization\EN_Store.bin"
PLUGIN_FILES = ("dinput8.dll", "FileRedirector.asi")


def write_ui_archive(root: Path, resources: dict[str, bytes]) -> None:
    """Writes a minimal UI.bix/UI.big pair that BigArchive can parse."""
    header = bytearray(0xC0)
    struct.pack_into("<I", header, 0x00, 0x2C5C40A8)
    struct.pack_into("<I", header, 0x40, 0x2AE784F9)
    header[0x44:0x4B] = b"UIIndex"
    items = list(resources.items())
    struct.pack_into("<I", header, 0x70, len(items))

    big = bytearray()
    table = bytearray()
    for resource_path, payload in items:
        pad = (4 - (len(big) % 4)) % 4
        big.extend(b"\x00" * pad)
        offset = len(big)
        big.extend(payload)
        table.extend(
            struct.pack(
                "<6I",
                qsymbol_hash(resource_path),
                offset // 4,
                0,
                0,
                0,
                len(payload),
            )
        )
    (root / "UI.bix").write_bytes(bytes(header) + bytes(table))
    (root / "UI.big").write_bytes(bytes(big))


def _extract(root: Path, resource_path: str) -> bytes:
    archive = BigArchive(root / "UI.bix", root / "UI.big")
    entry = archive.find_by_path(resource_path)
    if entry is None:
        raise AssertionError(f"missing {resource_path}")
    return archive.extract_entry(entry, decompress=False)


class ArchivePatchTests(unittest.TestCase):
    def test_replaces_one_entry_and_leaves_the_other(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            game = Path(temporary_directory)
            write_ui_archive(
                game,
                {
                    KEEP_PATH: b"KEEP-BYTES",
                    LOC_PATH: b"OLD-LOC",
                },
            )
            (game / "sdhdship.exe").write_bytes(b"stock-exe")
            replaced = apply_ui_replacements(game, {LOC_PATH: b"NEW-LOC-AR"})
            self.assertEqual(replaced, 1)
            self.assertEqual(_extract(game, KEEP_PATH), b"KEEP-BYTES")
            self.assertEqual(_extract(game, LOC_PATH), b"NEW-LOC-AR")
            self.assertEqual((game / "sdhdship.exe").read_bytes(), b"stock-exe")
            self.assertTrue((game / f"UI.bix{BACKUP_SUFFIX}").is_file())
            self.assertTrue((game / f"UI.big{BACKUP_SUFFIX}").is_file())
            self.assertFalse((game / "dinput8.dll").exists())
            self.assertFalse((game / "FileRedirector.asi").exists())

    def test_second_patch_does_not_grow_unbounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            game = Path(temporary_directory)
            write_ui_archive(game, {LOC_PATH: b"OLD"})
            apply_ui_replacements(game, {LOC_PATH: b"NEW1"})
            first_size = (game / "UI.big").stat().st_size
            apply_ui_replacements(game, {LOC_PATH: b"NEW2"})
            second_size = (game / "UI.big").stat().st_size
            self.assertEqual(first_size, second_size)
            self.assertEqual(_extract(game, LOC_PATH), b"NEW2")
            self.assertEqual(backup_path(game / "UI.big").read_bytes(), b"OLD")

    def test_unknown_resource_does_not_rewrite_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            game = Path(temporary_directory)
            write_ui_archive(game, {KEEP_PATH: b"KEEP-BYTES"})
            original_bix = (game / "UI.bix").read_bytes()
            with self.assertRaises(ValueError):
                apply_ui_replacements(game, {LOC_PATH: b"nope"})
            self.assertEqual((game / "UI.bix").read_bytes(), original_bix)
            self.assertEqual(_extract(game, KEEP_PATH), b"KEEP-BYTES")

    def test_incomplete_backup_pair_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            game = Path(temporary_directory)
            write_ui_archive(game, {LOC_PATH: b"OLD"})
            ensure_archive_backup(game / "UI.bix", game / "UI.big")
            backup_path(game / "UI.big").unlink()
            with self.assertRaises(ValueError):
                apply_ui_replacements(game, {LOC_PATH: b"NEW"})

    def test_removes_incompatible_plugins_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            game = Path(temporary_directory)
            (game / "dinput8.dll").write_bytes(b"loader")
            (game / "FileRedirector.asi").write_bytes(b"plugin")
            (game / "sdhdship.exe").write_bytes(b"exe")
            removed = remove_incompatible_plugins(game)
            self.assertEqual(set(removed), set(PLUGIN_FILES))
            self.assertFalse((game / "dinput8.dll").exists())
            self.assertFalse((game / "FileRedirector.asi").exists())
            self.assertEqual((game / "sdhdship.exe").read_bytes(), b"exe")


if __name__ == "__main__":
    unittest.main()
