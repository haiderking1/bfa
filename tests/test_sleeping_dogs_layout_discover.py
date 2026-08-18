"""Tests for Scaleform text-box discovery from Sleeping Dogs UI screens."""

from __future__ import annotations

import struct
import unittest

from bfa.fonts.swf import SwfTag, encode_swf_tag
from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.font_package import is_uiscreen_chunk, parse_uiscreen_font_package
from bfa.games.sleeping_dogs.inspector import DEFAULT_GAME_PATH
from bfa.games.sleeping_dogs.layout import boxes_for_instance, discover_text_field_boxes
from bfa.games.sleeping_dogs.layout.profile import (
    HUD_INFO_FLASHER_INSTANCE_PATH,
    HUD_INFO_FLASHER_WIDTH_PX,
    PHONE_MESSAGE_INSTANCE_PATH,
    PHONE_MESSAGE_WIDTH_PX,
    SUBTITLE_FONT_SIZE_PX,
    SUBTITLE_INSTANCE_PATH,
    SUBTITLE_WIDTH_PX,
    SUBTITLE_WIDTH_TWIPS,
)
from bfa.games.sleeping_dogs.layout.discover import MAX_SCREEN_UNCOMPRESSED_SIZE
from bfa.layout.gfx_text import (
    instance_paths_for_character,
    movie_stage_pixels,
    parse_define_edit_text,
    text_field_boxes,
)
from bfa.layout.twips import TWIPS_PER_PIXEL, twips_to_pixels


HUD_PATH = r"Data\UI\Screens\HUD.BIN"
INFO_FLASHER = HUD_INFO_FLASHER_INSTANCE_PATH
SECONDARY_TUTORIAL = "mc_secondaryTutorial/mc_inner/tf_text"
SUBTITLE_1 = SUBTITLE_INSTANCE_PATH
SUBTITLE_2 = "subtitles_2/m_text/dispTxt"


def _ui_archive() -> BigArchive:
    game_dir = DEFAULT_GAME_PATH
    if not game_dir.is_dir():
        raise unittest.SkipTest(f"Game directory does not exist: {game_dir}")
    original_bix = game_dir / "UI.bix.bfa-original"
    original_big = game_dir / "UI.big.bfa-original"
    if original_bix.is_file() and original_big.is_file():
        return BigArchive(original_bix, original_big)
    return BigArchive(game_dir / "UI.bix")


def _screen_package(archive: BigArchive, debug_name: str):
    for entry in archive.entries:
        if entry.size <= 0 or entry.size > MAX_SCREEN_UNCOMPRESSED_SIZE:
            continue
        try:
            data = archive.extract_entry(entry, decompress=True)
        except (OSError, ValueError):
            continue
        if not is_uiscreen_chunk(data):
            continue
        try:
            package = parse_uiscreen_font_package(data)
        except ValueError:
            continue
        if package.debug_name == debug_name:
            return package
    raise unittest.SkipTest(f"missing UI screen {debug_name}")


def _named_place_object2(character_id: int, name: str) -> bytes:
    return bytes([0x26]) + struct.pack("<HH", 1, character_id) + b"\x00" + name.encode("latin1") + b"\x00"


def _named_place_object3(character_id: int, name: str, *, class_name: str | None = None) -> bytes:
    extra = 0x08 if class_name is not None else 0x00
    payload = bytes([0x26, extra]) + struct.pack("<H", 1)
    if class_name is not None:
        payload += class_name.encode("latin1") + b"\x00"
    payload += struct.pack("<H", character_id) + b"\x00" + name.encode("latin1") + b"\x00"
    return payload


def _sprite(sprite_id: int, *inner: SwfTag) -> SwfTag:
    payload = struct.pack("<HH", sprite_id, 1) + b"".join(encode_swf_tag(tag) for tag in inner)
    return SwfTag(code=39, payload=payload)


class TwipConversionTests(unittest.TestCase):
    def test_twenty_twips_is_one_pixel(self) -> None:
        self.assertEqual(TWIPS_PER_PIXEL, 20)
        self.assertEqual(twips_to_pixels(8920), 446.0)


class HudTextBoxDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.archive = _ui_archive()
        entry = cls.archive.find_by_path(HUD_PATH)
        if entry is None:
            raise unittest.SkipTest(f"missing {HUD_PATH}")
        cls.hud = parse_uiscreen_font_package(
            cls.archive.extract_entry(entry, decompress=True)
        )

    def test_hud_stage_is_1920_by_1080(self) -> None:
        width, height = movie_stage_pixels(self.hud.movie.header)
        self.assertEqual(width, 1920.0)
        self.assertEqual(height, 1080.0)

    def test_info_flasher_box_is_measured_from_define_edit_text(self) -> None:
        boxes = text_field_boxes(
            self.hud.movie.tags,
            screen_path=HUD_PATH,
            screen_name=self.hud.debug_name,
            stage_width_px=1920.0,
            stage_height_px=1080.0,
        )
        flasher = next(box for box in boxes if box.instance_path == INFO_FLASHER)
        self.assertEqual(flasher.width_px, HUD_INFO_FLASHER_WIDTH_PX)
        self.assertEqual(flasher.height_px, 82.0)
        self.assertTrue(flasher.word_wrap)
        self.assertTrue(flasher.multiline)
        self.assertTrue(flasher.html)
        self.assertEqual(flasher.align, "center")
        self.assertEqual(flasher.font_size_px, 20.0)
        self.assertEqual(flasher.stage_width_px, 1920.0)

    def test_secondary_tutorial_box_is_narrower_and_left_aligned(self) -> None:
        boxes = text_field_boxes(
            self.hud.movie.tags,
            screen_path=HUD_PATH,
            screen_name=self.hud.debug_name,
            stage_width_px=1920.0,
            stage_height_px=1080.0,
        )
        tutorial = next(box for box in boxes if box.instance_path == SECONDARY_TUTORIAL)
        self.assertEqual(tutorial.width_px, 327.0)
        self.assertTrue(tutorial.word_wrap)
        self.assertEqual(tutorial.align, "left")
        self.assertEqual(tutorial.font_size_px, 20.0)

    def test_define_edit_text_id_matches_info_flasher_character(self) -> None:
        boxes = text_field_boxes(
            self.hud.movie.tags,
            screen_path=HUD_PATH,
            screen_name="Hud",
            stage_width_px=1920.0,
            stage_height_px=1080.0,
        )
        flasher = next(box for box in boxes if box.instance_path == INFO_FLASHER)
        payload = next(
            tag.payload
            for tag in self.hud.movie.tags
            if tag.code == 37
            and parse_define_edit_text(tag.payload)["character_id"] == flasher.character_id
        )
        parsed = parse_define_edit_text(payload)
        self.assertEqual(twips_to_pixels(parsed["width_twips"]), 446.0)
        self.assertEqual(parsed["align"], "center")


class ArchiveDiscoveryTests(unittest.TestCase):
    def test_discover_finds_hud_info_flasher_without_hardcoded_width(self) -> None:
        archive = _ui_archive()
        boxes = discover_text_field_boxes(archive)
        self.assertGreater(len(boxes), 32)
        hud = [box for box in boxes if box.screen_path == HUD_PATH]
        self.assertGreaterEqual(len(hud), 32)
        flasher = boxes_for_instance(hud, INFO_FLASHER)
        self.assertEqual(len(flasher), 1)
        self.assertEqual(flasher[0].width_px, HUD_INFO_FLASHER_WIDTH_PX)
        self.assertEqual(flasher[0].screen_name, "Hud")

    def test_discover_measures_phone_sms_box(self) -> None:
        archive = _ui_archive()
        boxes = discover_text_field_boxes(archive)
        phone = boxes_for_instance(boxes, PHONE_MESSAGE_INSTANCE_PATH)
        self.assertGreaterEqual(len(phone), 1)
        self.assertEqual(phone[0].width_px, PHONE_MESSAGE_WIDTH_PX)
        self.assertTrue(phone[0].word_wrap)
        self.assertTrue(phone[0].html)
        self.assertEqual(phone[0].align, "left")
        self.assertEqual(phone[0].font_size_px, 19.0)
        self.assertLess(phone[0].width_px, HUD_INFO_FLASHER_WIDTH_PX)

    def test_cfx_version_10_screens_are_included(self) -> None:
        archive = _ui_archive()
        boxes = discover_text_field_boxes(archive)
        race = [box for box in boxes if box.screen_path == r"Data\UI\Screens\RaceHUD.BIN"]
        self.assertGreaterEqual(len(race), 1)
        self.assertEqual(race[0].stage_width_px, 1920.0)

    def test_discover_measures_global_overlay_subtitle_boxes(self) -> None:
        archive = _ui_archive()
        boxes = discover_text_field_boxes(archive)
        primary = boxes_for_instance(boxes, SUBTITLE_1)
        secondary = boxes_for_instance(boxes, SUBTITLE_2)
        self.assertEqual(len(primary), 1)
        self.assertEqual(len(secondary), 1)
        self.assertEqual(primary[0].screen_name, "GlobalOverlay")
        self.assertEqual(primary[0].width_twips, SUBTITLE_WIDTH_TWIPS)
        self.assertEqual(primary[0].height_twips, 1900)
        self.assertEqual(primary[0].width_px, SUBTITLE_WIDTH_PX)
        self.assertEqual(primary[0].font_size_px, SUBTITLE_FONT_SIZE_PX)
        self.assertTrue(primary[0].word_wrap)
        self.assertTrue(primary[0].html)
        self.assertEqual(primary[0].align, "center")
        self.assertEqual(secondary[0].width_twips, 23232)
        self.assertEqual(secondary[0].height_twips, 1767)
        self.assertEqual(secondary[0].width_px, 1161.6)
        self.assertEqual(secondary[0].height_px, 88.35)
        self.assertEqual(secondary[0].font_size_px, 21.0)


class PlaceObject3PathTests(unittest.TestCase):
    def test_instance_path_walks_place_object3_under_named_clips(self) -> None:
        tags = [
            _sprite(
                29,
                SwfTag(code=70, payload=_named_place_object3(28, "dispTxt")),
                SwfTag(code=0, payload=b""),
            ),
            _sprite(
                30,
                SwfTag(code=26, payload=_named_place_object2(29, "m_text")),
                SwfTag(code=0, payload=b""),
            ),
            SwfTag(code=26, payload=_named_place_object2(30, "subtitles_1")),
        ]
        self.assertEqual(
            instance_paths_for_character(tags, 28),
            ["subtitles_1/m_text/dispTxt"],
        )

    def test_place_object3_skips_class_name_before_character_id(self) -> None:
        tags = [
            _sprite(
                29,
                SwfTag(
                    code=70,
                    payload=_named_place_object3(28, "dispTxt", class_name="HKText"),
                ),
                SwfTag(code=0, payload=b""),
            ),
            SwfTag(code=26, payload=_named_place_object2(29, "m_text")),
        ]
        self.assertEqual(instance_paths_for_character(tags, 28), ["m_text/dispTxt"])


class GlobalOverlaySubtitleBoxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.overlay = _screen_package(_ui_archive(), "GlobalOverlay")

    def test_subtitle_fields_are_named_not_anonymous_ids(self) -> None:
        boxes = text_field_boxes(
            self.overlay.movie.tags,
            screen_path=r"Data\UI\Screens\GlobalOverlay.BIN",
            screen_name=self.overlay.debug_name,
            stage_width_px=1920.0,
            stage_height_px=1080.0,
        )
        paths = {box.instance_path for box in boxes}
        self.assertIn(SUBTITLE_1, paths)
        self.assertIn(SUBTITLE_2, paths)
        self.assertNotIn("id28", paths)
        self.assertNotIn("id31", paths)

    def test_subtitle_1_rect_is_measured_from_define_edit_text(self) -> None:
        boxes = text_field_boxes(
            self.overlay.movie.tags,
            screen_path=r"Data\UI\Screens\GlobalOverlay.BIN",
            screen_name=self.overlay.debug_name,
            stage_width_px=1920.0,
            stage_height_px=1080.0,
        )
        box = next(item for item in boxes if item.instance_path == SUBTITLE_1)
        payload = next(
            tag.payload
            for tag in self.overlay.movie.tags
            if tag.code == 37
            and parse_define_edit_text(tag.payload)["character_id"] == box.character_id
        )
        parsed = parse_define_edit_text(payload)
        self.assertEqual(parsed["width_twips"], 22858)
        self.assertEqual(parsed["height_twips"], 1900)
        self.assertEqual(twips_to_pixels(parsed["width_twips"]), 1142.9)
        self.assertEqual(twips_to_pixels(parsed["height_twips"]), 95.0)
        self.assertTrue(parsed["word_wrap"])
        self.assertTrue(parsed["multiline"])
        self.assertTrue(parsed["html"])
        self.assertEqual(parsed["align"], "center")
        self.assertEqual(twips_to_pixels(parsed["font_height_twips"]), 21.0)
        self.assertIn("Subtitles", parsed["initial_text"])

    def test_subtitle_2_rect_is_wider_than_subtitle_1(self) -> None:
        boxes = text_field_boxes(
            self.overlay.movie.tags,
            screen_path=r"Data\UI\Screens\GlobalOverlay.BIN",
            screen_name=self.overlay.debug_name,
            stage_width_px=1920.0,
            stage_height_px=1080.0,
        )
        box = next(item for item in boxes if item.instance_path == SUBTITLE_2)
        self.assertEqual(box.width_twips, 23232)
        self.assertEqual(box.height_twips, 1767)
        self.assertEqual(box.width_px, 1161.6)
        self.assertEqual(box.height_px, 88.35)
        self.assertGreater(box.width_px, 1142.9)
        self.assertTrue(box.word_wrap)
        self.assertEqual(box.align, "center")
        self.assertEqual(box.font_size_px, 21.0)


if __name__ == "__main__":
    unittest.main()
