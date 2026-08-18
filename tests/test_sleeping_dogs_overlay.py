"""Tests for isolated overlay packaging and stock-exe archive install."""

from __future__ import annotations

import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.discover import discover_localization_resources
from bfa.games.sleeping_dogs.hash import qsymbol_hash
from bfa.games.sleeping_dogs.inspector import DEFAULT_GAME_PATH
from bfa.games.sleeping_dogs.localization import parse_uilocalization_chunk
from bfa.games.sleeping_dogs.display_text import shape_localization_text
from bfa.games.sleeping_dogs.publish import publish_sleeping_dogs
from bfa.games.sleeping_dogs.redirector import (
    install_game_overlay,
    packaged_replacements,
    redirector_output_path,
    resource_output_path,
    write_packaged_resource,
)
from bfa.games.sleeping_dogs.repository import SleepingDogsDatabase

LOC_PATH = r"Data\UI\Localization\EN_Store.bin"
FONT_PATH = r"Data\UI\Screens\FontsEnglish.bin"


def write_ui_archive(root: Path, resources: dict[str, bytes]) -> None:
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract(root: Path, resource_path: str) -> bytes:
    archive = BigArchive(root / "UI.bix", root / "UI.big")
    entry = archive.find_by_path(resource_path)
    if entry is None:
        raise AssertionError(f"missing {resource_path}")
    return archive.extract_entry(entry, decompress=False)


class RedirectorPathTests(unittest.TestCase):
    def test_data_and_redirector_paths(self) -> None:
        root = Path("/tmp/bfa-overlay")
        resource = r"Data\UI\Localization\EN_Front-End.bin"
        self.assertEqual(
            resource_output_path(root, resource),
            root / "Data" / "UI" / "Localization" / "EN_Front-End.bin",
        )
        self.assertEqual(
            redirector_output_path(root, resource),
            root / "RedirectorData" / "UI" / "Localization" / "EN_Front-End.bin",
        )

    def test_rejects_parent_segments(self) -> None:
        with self.assertRaises(ValueError):
            resource_output_path(Path("/tmp"), r"Data\..\UI.big")
        with self.assertRaises(ValueError):
            redirector_output_path(Path("/tmp"), r"Data\..\UI.big")

    def test_write_packaged_resource_duplicates_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path, redirector_path = write_packaged_resource(
                root,
                r"Data\UI\Localization\EN_BA_3b_Store.bin",
                b"loc-bytes",
            )
            self.assertEqual(data_path.read_bytes(), b"loc-bytes")
            self.assertEqual(redirector_path.read_bytes(), b"loc-bytes")
            self.assertEqual(
                packaged_replacements(root),
                {r"Data\UI\Localization\EN_BA_3b_Store.bin": b"loc-bytes"},
            )


class OverlayInstallTests(unittest.TestCase):
    def test_install_patches_archives_and_strips_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output = root / "out"
            game = root / "game"
            game.mkdir()
            write_ui_archive(
                game,
                {
                    LOC_PATH: b"old-loc",
                    FONT_PATH: b"old-font",
                },
            )
            (game / "sdhdship.exe").write_bytes(b"exe")
            (game / "dinput8.dll").write_bytes(b"loader")
            (game / "FileRedirector.asi").write_bytes(b"plugin")
            write_packaged_resource(output, LOC_PATH, b"arabic")
            write_packaged_resource(output, FONT_PATH, b"bfa-font")
            summary = install_game_overlay(output, game)
            self.assertEqual(summary.files_installed, 2)
            self.assertEqual(set(summary.removed_plugin_files), {"dinput8.dll", "FileRedirector.asi"})
            self.assertEqual(_extract(game, LOC_PATH), b"arabic")
            self.assertEqual(_extract(game, FONT_PATH), b"bfa-font")
            self.assertEqual((game / "sdhdship.exe").read_bytes(), b"exe")
            self.assertFalse((game / "dinput8.dll").exists())
            self.assertFalse((game / "FileRedirector.asi").exists())
            self.assertFalse((game / "RedirectorData").exists())

    def test_install_requires_ui_archives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output = root / "out"
            game = root / "game"
            game.mkdir()
            write_packaged_resource(output, LOC_PATH, b"arabic")
            with self.assertRaises(FileNotFoundError):
                install_game_overlay(output, game)


class PublishOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.game_dir = DEFAULT_GAME_PATH
        if not cls.game_dir.is_dir():
            raise unittest.SkipTest(f"Game directory does not exist: {cls.game_dir}")
        cls.ui_archive = BigArchive(cls.game_dir / "UI.bix")
        cls.store = next(
            item
            for item in discover_localization_resources([cls.ui_archive], language="EN")
            if item.debug_name == "EN_BA_3b_Store"
        )

    def test_publish_installs_loc_and_font_into_temp_game(self) -> None:
        before_bix = _sha256(self.game_dir / "UI.bix")
        before_big = _sha256(self.game_dir / "UI.big")
        store_path = self.store.resource_path
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output = root / "out"
            fake_game = root / "game"
            fake_game.mkdir()
            write_ui_archive(
                fake_game,
                {
                    store_path: b"old-store",
                    FONT_PATH: b"old-font",
                },
            )
            (fake_game / "sdhdship.exe").write_bytes(b"exe")
            with SleepingDogsDatabase(root / "db.sqlite") as database:
                database.import_resources([self.store], source_language="EN")
                pending = database.pending_strings("Arabic")
                database.save_translations({item.id: "اللعنة!" for item in pending}, "Arabic")
                published = publish_sleeping_dogs(
                    database,
                    output,
                    game_path=self.game_dir,
                    install=False,
                )
                self.assertEqual(published.pack.resources_written, 1)
                self.assertIsNotNone(published.font)
                overlay = output / "RedirectorData" / "UI" / "Localization" / "EN_BA_3b_Store.bin"
                self.assertEqual(
                    parse_uilocalization_chunk(overlay.read_bytes()).entries[0].text,
                    shape_localization_text("اللعنة!"),
                )
                font = output / "Data" / "UI" / "Screens" / "FontsEnglish.bin"
                self.assertTrue(font.is_file())
                installed = install_game_overlay(output, fake_game)
                self.assertGreaterEqual(installed.files_installed, 2)
                self.assertEqual(
                    parse_uilocalization_chunk(_extract(fake_game, store_path)).entries[0].text,
                    shape_localization_text("اللعنة!"),
                )
                self.assertEqual(_extract(fake_game, FONT_PATH), font.read_bytes())
                self.assertEqual((fake_game / "sdhdship.exe").read_bytes(), b"exe")
                self.assertFalse((fake_game / "dinput8.dll").exists())
        self.assertEqual(_sha256(self.game_dir / "UI.bix"), before_bix)
        self.assertEqual(_sha256(self.game_dir / "UI.big"), before_big)


if __name__ == "__main__":
    unittest.main()
