"""Tests for BFA HarfBuzz pre-shaping used by LTR game engines."""

from __future__ import annotations

import unittest

from bfa.fonts.shape import (
    has_arabic,
    load_shape_context,
    shape_arabic_run,
    shape_plain_text,
    strip_cjk,
)
from bfa.games.sleeping_dogs.display_text import shape_localization_text, strip_stage_directions


class ShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_shape_context()

    def test_menu_title_uses_joined_presentation_forms(self) -> None:
        logical = "القائمة الرئيسية"
        shaped = shape_arabic_run(logical, self.context)
        self.assertNotEqual(shaped, logical)
        self.assertTrue(any(0xFE70 <= ord(char) <= 0xFEFF for char in shaped))
        self.assertNotEqual(shaped[0], "ا")
        self.assertIn(" ", shaped)

    def test_lam_alef_becomes_a_ligature(self) -> None:
        shaped = shape_arabic_run("لا", self.context)
        self.assertEqual(len(shaped), 1)
        self.assertIn(ord(shaped), {0xFEFB, 0xFEFC})

    def test_mixed_latin_stays_in_place(self) -> None:
        shaped = shape_plain_text("Wei القتال", self.context)
        self.assertTrue(shaped.startswith("Wei "))
        self.assertNotIn("القتال", shaped)

    def test_tags_and_placeholders_are_preserved(self) -> None:
        source = "<br>اللعنة! %s"
        shaped = shape_localization_text(source, self.context)
        self.assertTrue(shaped.startswith("<br>"))
        self.assertIn("%s", shaped)
        self.assertNotEqual(shaped, source)

    def test_placeholder_parens_are_kept(self) -> None:
        self.assertEqual(strip_stage_directions("Thanks (%s)"), "Thanks (%s)")
        self.assertEqual(strip_stage_directions("(ملاحظة) القيمة %s"), "القيمة %s")
        self.assertEqual(strip_stage_directions("جمع %s (ليس %d)"), "جمع %s (ليس %d)")
        shaped = shape_localization_text("شكراً (%s)", self.context)
        thanks = shape_plain_text("شكراً", self.context)
        self.assertTrue(shaped.startswith("(%s)"))
        self.assertIn(thanks, shaped)
        self.assertEqual(shaped.count("("), 1)
        self.assertEqual(shaped.count(")"), 1)

    def test_mixed_placeholder_order_is_kept(self) -> None:
        shaped = shape_localization_text("خذ %s واحصل على %d", self.context)
        self.assertLess(shaped.index("%s"), shaped.index("%d"))

    def test_english_is_unchanged(self) -> None:
        self.assertEqual(shape_localization_text("MAIN MENU", self.context), "MAIN MENU")
        self.assertFalse(has_arabic("MAIN MENU"))

    def test_stage_direction_only_line_is_removed(self) -> None:
        self.assertEqual(strip_stage_directions("(ضحك)"), "")
        self.assertEqual(shape_localization_text("(ضحك)", self.context), "")

    def test_spoken_line_keeps_text_and_drops_stage_direction(self) -> None:
        self.assertEqual(strip_stage_directions("(باستغراب) هو لم يكن يعلم"), "هو لم يكن يعلم")
        shaped = shape_localization_text("(باستغراب) هو لم يكن يعلم", self.context)
        self.assertNotIn("(", shaped)
        self.assertNotIn(")", shaped)
        self.assertTrue(any(0xFE70 <= ord(char) <= 0xFEFF for char in shaped))
        self.assertEqual(shaped, shape_localization_text("هو لم يكن يعلم", self.context))

    def test_english_nis_prefix_and_tags_are_stripped_safely(self) -> None:
        self.assertEqual(
            strip_stage_directions("(in Cantonese )Thanks…"),
            "Thanks…",
        )
        self.assertEqual(
            strip_stage_directions("(quizzically) He didn't actually know…"),
            "He didn't actually know…",
        )
        self.assertEqual(
            strip_stage_directions("<br>(laughs)<br>Hello %s"),
            "<br><br>Hello %s",
        )
        self.assertEqual(strip_stage_directions("Hello (on phone) there"), "Hello there")

    def test_cjk_prefix_is_stripped(self) -> None:
        self.assertEqual(strip_cjk("主目錄القائمة"), "القائمة")
        shaped = shape_localization_text("主目錄القائمة الرئيسية", self.context)
        self.assertFalse(any(0x4E00 <= ord(char) <= 0x9FFF for char in shaped))
        self.assertTrue(any(0xFE70 <= ord(char) <= 0xFEFF for char in shaped))


if __name__ == "__main__":
    unittest.main()
