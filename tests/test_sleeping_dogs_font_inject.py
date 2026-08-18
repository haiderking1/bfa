"""Tests for injecting BFA into Sleeping Dogs FontsEnglish.bin."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from bfa.fonts.asset import BFA_FONT_PATH
from bfa.fonts.define_font3 import parse_define_font3
from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.font_inject import (
    FONTS_ENGLISH_RESOURCE,
    extract_font_package,
    inject_bfa_into_font_package,
    inject_sleeping_dogs_font,
)
from bfa.fonts.swf import first_style_change_fills
from bfa.games.sleeping_dogs.font_package import (
    encode_uiscreen_font_package,
    font3_tags,
    listed_font_names,
    parse_uiscreen_font_package,
)
from bfa.games.sleeping_dogs.inspector import DEFAULT_GAME_PATH


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SleepingDogsFontInjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.game_dir = DEFAULT_GAME_PATH
        if not cls.game_dir.is_dir():
            raise unittest.SkipTest(f"Game directory does not exist: {cls.game_dir}")
        cls.original = extract_font_package(cls.game_dir)

    def test_original_fonts_english_has_three_named_faces(self) -> None:
        package = parse_uiscreen_font_package(self.original)
        self.assertEqual(package.debug_name, "FontsEnglish")
        self.assertEqual(package.qchunk_id, 0x442A39D9)
        self.assertEqual(
            listed_font_names(package.movie),
            ["Proxima Nova Lt Cyr", "DINCondensedTT", "Magistral Medium"],
        )
        proxima = parse_define_font3(font3_tags(package.movie)[0].payload)
        self.assertEqual(proxima.font_id, 1)
        self.assertIn(32, proxima.codes)
        self.assertFalse(any(0x0600 <= code <= 0x06FF for code in proxima.codes))
        letter = proxima.shapes[proxima.codes.index(ord("A"))]
        self.assertEqual(first_style_change_fills(letter), (1, 1, 0))

    def test_inject_bfa_keeps_names_and_adds_arabic(self) -> None:
        before_bix = _sha256(self.game_dir / "UI.bix")
        before_big = _sha256(self.game_dir / "UI.big")
        injected = inject_bfa_into_font_package(self.original, BFA_FONT_PATH)
        self.assertNotEqual(injected, self.original)
        self.assertEqual(len(injected) % 8, 0)

        package = parse_uiscreen_font_package(injected)
        fonts = [parse_define_font3(tag.payload) for tag in font3_tags(package.movie)]
        self.assertEqual(
            [item.name for item in fonts],
            ["Proxima Nova Lt Cyr", "DINCondensedTT", "Magistral Medium"],
        )
        self.assertEqual([item.font_id for item in fonts], [1, 3, 5])
        self.assertTrue(all(32 in item.codes for item in fonts))
        self.assertTrue(all(0x0627 in item.codes for item in fonts))
        self.assertGreaterEqual(
            sum(1 for code in fonts[0].codes if 0x0600 <= code <= 0x06FF),
            30,
        )
        self.assertEqual(fonts[0].codes, fonts[1].codes)
        self.assertEqual(fonts[1].codes, fonts[2].codes)
        injected_letter = fonts[0].shapes[fonts[0].codes.index(ord("A"))]
        self.assertEqual(first_style_change_fills(injected_letter), (1, 1, 0))
        injected_alef = fonts[0].shapes[fonts[0].codes.index(0x0627)]
        self.assertEqual(first_style_change_fills(injected_alef), (1, 1, 0))
        self.assertEqual(_sha256(self.game_dir / "UI.bix"), before_bix)
        self.assertEqual(_sha256(self.game_dir / "UI.big"), before_big)

    def test_noop_rewrap_keeps_original_faces(self) -> None:
        package = parse_uiscreen_font_package(self.original)
        rebuilt = encode_uiscreen_font_package(package, package.movie)
        parsed = parse_uiscreen_font_package(rebuilt)
        self.assertEqual(listed_font_names(parsed.movie), listed_font_names(package.movie))
        self.assertEqual(len(font3_tags(parsed.movie)), 3)

    def test_isolated_output_and_game_archives_untouched(self) -> None:
        before_bix = _sha256(self.game_dir / "UI.bix")
        before_big = _sha256(self.game_dir / "UI.big")
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "sleeping_dogs_ar"
            summary = inject_sleeping_dogs_font(self.game_dir, output_dir)
            written = Path(summary.output_path)
            self.assertTrue(written.is_file())
            self.assertEqual(
                written,
                output_dir / "Data" / "UI" / "Screens" / "FontsEnglish.bin",
            )
            redirector = output_dir / "RedirectorData" / "UI" / "Screens" / "FontsEnglish.bin"
            self.assertTrue(redirector.is_file())
            self.assertEqual(redirector.read_bytes(), written.read_bytes())
            self.assertEqual(summary.resource_path, FONTS_ENGLISH_RESOURCE)
            self.assertGreaterEqual(summary.arabic_codepoint_count, 30)
            self.assertEqual(
                summary.replaced_fonts,
                ["Proxima Nova Lt Cyr", "DINCondensedTT", "Magistral Medium"],
            )
            package = parse_uiscreen_font_package(written.read_bytes())
            self.assertEqual(package.debug_name, "FontsEnglish")
        self.assertEqual(_sha256(self.game_dir / "UI.bix"), before_bix)
        self.assertEqual(_sha256(self.game_dir / "UI.big"), before_big)
        ui_archive = BigArchive(self.game_dir / "UI.bix")
        entry = ui_archive.find_by_path(FONTS_ENGLISH_RESOURCE)
        assert entry is not None
        self.assertEqual(ui_archive.extract_entry(entry, decompress=True), self.original)


if __name__ == "__main__":
    unittest.main()
