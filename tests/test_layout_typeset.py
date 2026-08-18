"""Tests for Scaleform loc typesetting: BiDi atoms, measure, and wrap."""

from __future__ import annotations

import unittest

import uharfbuzz as hb

from bfa.fonts.shape import ShapeContext, load_shape_context, shape_plain_text
from bfa.games.sleeping_dogs.display_text import shape_localization_text
from bfa.games.sleeping_dogs.layout.profile import (
    HUD_INFO_FLASHER_FONT_SIZE_PX,
    HUD_INFO_FLASHER_WIDTH_PX,
    PACK_WRAP_WIDTH_PX,
    PHONE_MESSAGE_FONT_SIZE_PX,
    PHONE_MESSAGE_WIDTH_PX,
    SUBTITLE_FONT_SIZE_PX,
    SUBTITLE_WIDTH_PX,
    wrap_metrics_for,
)
from bfa.games.sleeping_dogs.layout.markup import parse_loc_markup
from bfa.games.sleeping_dogs.layout.tokens import tokenize_paragraph
from bfa.games.sleeping_dogs.layout.typeset import typeset_localization_text
from bfa.layout.measure import measure_text_px
from bfa.layout.wrap import wrap_tokens


def _measure_visual_ltr(text: str, context: ShapeContext, font_size_px: float) -> float:
    """Measures already-shaped presentation forms as LTR glyph advances."""
    if text == "":
        return 0.0
    font = context.font
    upem = font.face.upem
    buf = hb.Buffer()
    buf.add_str(text)
    buf.direction = "ltr"
    hb.shape(font, buf, {"kern": True, "liga": True})
    positions = buf.glyph_positions
    if not positions:
        return 0.0
    return sum(position.x_advance for position in positions) * font_size_px / upem


class MeasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_shape_context()

    def test_empty_text_is_zero_width(self) -> None:
        self.assertEqual(measure_text_px("", self.context, SUBTITLE_FONT_SIZE_PX), 0.0)

    def test_width_scales_linearly_with_font_size(self) -> None:
        text = "الجزار"
        small = measure_text_px(text, self.context, 10.5)
        large = measure_text_px(text, self.context, 21.0)
        self.assertGreater(small, 0.0)
        self.assertAlmostEqual(large, small * 2.0, places=4)

    def test_butcher_name_is_narrower_than_subtitle_box(self) -> None:
        width = measure_text_px("الجزار", self.context, SUBTITLE_FONT_SIZE_PX)
        self.assertLess(width, SUBTITLE_WIDTH_PX)
        self.assertGreater(width, 20.0)


class WrapTokenTests(unittest.TestCase):
    def test_wraps_before_a_token_that_does_not_fit(self) -> None:
        lines = wrap_tokens(
            ["aa", " ", "bbb"],
            [2.0, 1.0, 3.0],
            4.0,
            is_discardable_break=lambda token: token == " ",
        )
        self.assertEqual(lines, [["aa"], ["bbb"]])

    def test_token_wider_than_the_box_stays_on_its_own_line(self) -> None:
        lines = wrap_tokens(
            ["tiny", " ", "enormous"],
            [1.0, 1.0, 10.0],
            4.0,
            is_discardable_break=lambda token: token == " ",
        )
        self.assertEqual(lines, [["tiny"], ["enormous"]])


class TokenizeTests(unittest.TestCase):
    def test_font_element_is_one_atom(self) -> None:
        tokens = tokenize_paragraph("اذهب إلى <font color='#e2c32b'>الجزار</font>")
        kinds = [token.kind for token in tokens]
        sources = [token.source for token in tokens]
        self.assertEqual(kinds, ["word", "space", "word", "space", "atom"])
        self.assertEqual(sources[-1], "<font color='#e2c32b'>الجزار</font>")
        self.assertEqual(tokens[-1].measure_text, "الجزار")

    def test_placeholder_stays_inside_a_word_with_parens(self) -> None:
        tokens = tokenize_paragraph("شكراً (%s)")
        self.assertEqual([token.source for token in tokens], ["شكراً", " ", "(%s)"])


class WrapMetricsTests(unittest.TestCase):
    def test_sms_key_uses_the_phone_box(self) -> None:
        metrics = wrap_metrics_for(
            resource_debug_name="EN_Gameplay",
            key_string="SMS_PRE_TRANS_DELIVERIES",
        )
        self.assertEqual(metrics.width_px, PHONE_MESSAGE_WIDTH_PX)
        self.assertEqual(metrics.font_size_px, PHONE_MESSAGE_FONT_SIZE_PX)

    def test_embedded_sms_token_uses_the_phone_box(self) -> None:
        metrics = wrap_metrics_for(key_string="JOB_DC4_SMS_TOMMY")
        self.assertEqual(metrics.width_px, PHONE_MESSAGE_WIDTH_PX)

    def test_gameplay_objective_uses_the_hud_box(self) -> None:
        metrics = wrap_metrics_for(
            resource_debug_name="EN_GameplayAct1",
            key_string="CASE_POLITICIAN2_OBJECTIVE_001",
        )
        self.assertEqual(metrics.width_px, HUD_INFO_FLASHER_WIDTH_PX)
        self.assertEqual(metrics.font_size_px, HUD_INFO_FLASHER_FONT_SIZE_PX)
        self.assertEqual(PACK_WRAP_WIDTH_PX, HUD_INFO_FLASHER_WIDTH_PX)

    def test_spoken_nis_table_uses_the_subtitle_box(self) -> None:
        metrics = wrap_metrics_for(resource_debug_name="EN_NIS", key_string="C_HS_ACE.PHONE_ANSWER_SCRIPTED.001.A")
        self.assertEqual(metrics.width_px, SUBTITLE_WIDTH_PX)
        self.assertEqual(metrics.font_size_px, SUBTITLE_FONT_SIZE_PX)


class TypesetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_shape_context()

    def test_tagged_name_moves_to_the_ltr_start(self) -> None:
        logical = "اذهب إلى <font color='#e2c32b'>الجزار</font>"
        typeset = shape_localization_text(logical, self.context)
        name = shape_plain_text("الجزار", self.context)
        go = shape_plain_text("اذهب", self.context)
        self.assertIn("<font color='#e2c32b'>", typeset)
        self.assertIn("</font>", typeset)
        self.assertLess(typeset.index(name), typeset.index(go))
        open_at = typeset.index("<font color='#e2c32b'>")
        close_at = typeset.index("</font>")
        self.assertLess(open_at, typeset.index(name))
        self.assertLess(typeset.index(name), close_at)

    def test_placeholder_moves_with_rtl_sentence(self) -> None:
        typeset = typeset_localization_text("شكراً (%s)", self.context)
        thanks = shape_plain_text("شكراً", self.context)
        self.assertTrue(typeset.startswith("(%s)"))
        self.assertIn(thanks, typeset)
        self.assertEqual(typeset.count("("), 1)
        self.assertEqual(typeset.count(")"), 1)

    def test_mixed_placeholders_keep_sprintf_order(self) -> None:
        logical = "خذ %s واحصل على %d"
        typeset = typeset_localization_text(logical, self.context)
        take = shape_plain_text("خذ", self.context)
        self.assertLess(typeset.index("%s"), typeset.index("%d"))
        self.assertLess(typeset.index("%s"), typeset.index(take))
        self.assertEqual(typeset.count("%s"), 1)
        self.assertEqual(typeset.count("%d"), 1)

    def test_font_atom_is_not_split_across_lines(self) -> None:
        logical = "اذهب إلى <font color='#e2c32b'>الجزار</font>"
        typeset = typeset_localization_text(
            logical,
            self.context,
            width_px=1.0,
            font_size_px=SUBTITLE_FONT_SIZE_PX,
        )
        self.assertIn("<font color='#e2c32b'>الجزار</font>".replace("الجزار", shape_plain_text("الجزار", self.context)), typeset)
        self.assertNotRegex(typeset, r"<font[^>]*>.*<br>.*</font>")

    def test_long_arabic_wraps_inside_the_measured_subtitle_box(self) -> None:
        phrase = "السمكة الذهبية"
        logical = " ".join([phrase] * 12)
        full_width = measure_text_px(logical, self.context, SUBTITLE_FONT_SIZE_PX)
        self.assertGreater(full_width, SUBTITLE_WIDTH_PX)
        typeset = typeset_localization_text(
            logical,
            self.context,
            width_px=SUBTITLE_WIDTH_PX,
            font_size_px=SUBTITLE_FONT_SIZE_PX,
        )
        self.assertIn("<br>", typeset)
        for line in typeset.split("<br>"):
            self.assertNotEqual(line, "")
            width = _measure_visual_ltr(line, self.context, SUBTITLE_FONT_SIZE_PX)
            self.assertLessEqual(width, SUBTITLE_WIDTH_PX + 0.5)

    def test_existing_break_tags_are_kept(self) -> None:
        typeset = typeset_localization_text("اللعنة!<br>هو هنا", self.context)
        self.assertIn("<br>", typeset)
        self.assertEqual(typeset.count("<br>"), 1)

    def test_english_is_not_wrapped_or_reordered(self) -> None:
        source = "Go to the <font color='#e2c32b'>Temple</font>"
        self.assertEqual(shape_localization_text(source, self.context), source)

    def test_nested_font_keeps_valid_tag_order(self) -> None:
        logical = (
            "مقياس الوجه\n"
            "<font color='#e1e1e1'>زيادة <font color='#e2c32b'>مستوى الوجه</font>"
            " تفتح <font color='#e2c32b'>قدرات</font> جديدة</font>"
        )
        typeset = typeset_localization_text(logical, self.context)
        title = shape_plain_text("مقياس الوجه", self.context)
        abilities = shape_plain_text("قدرات", self.context)
        self.assertTrue(typeset.startswith(title + "\n"))
        self.assertLess(typeset.index("\n"), typeset.index(abilities))
        self.assertLess(typeset.lower().find("<font"), typeset.lower().find("</font>"))
        self.assertEqual(typeset.lower().count("<font"), 3)
        self.assertEqual(typeset.lower().count("</font>"), 3)
        self.assertEqual(_font_depth_min(typeset), 0)
        self.assertEqual(_font_depth_end(typeset), 0)
        outer = typeset.split("\n", 1)[1]
        self.assertTrue(outer.startswith("<font color='#e1e1e1'>"))
        self.assertTrue(outer.endswith("</font>"))

    def test_mismatched_job_close_is_preserved(self) -> None:
        logical = "<font color='#f08728'>ديربي نورث بوينت</job>"
        typeset = typeset_localization_text(logical, self.context)
        self.assertTrue(typeset.startswith("<font color='#f08728'>"))
        self.assertTrue(typeset.endswith("</job>"))
        self.assertNotIn("</font>", typeset)

    def test_cite_wrapper_stays_around_its_body(self) -> None:
        logical = (
            "<cite>قفزة سريعة\n"
            "<font color='#e1e1e1'>اضغط </font>"
            "<img  src='BUTTON_ACCEPT' height='52' vspace='-26' width='52'>"
            "<font color='#e1e1e1'> قبل الوصول إلى العائق مباشرة</font></cite>"
        )
        typeset = typeset_localization_text(logical, self.context)
        self.assertTrue(typeset.startswith("<cite>"))
        self.assertTrue(typeset.endswith("</cite>"))
        self.assertIn("<img  src='BUTTON_ACCEPT'", typeset)
        self.assertEqual(_font_depth_min(typeset), 0)
        self.assertEqual(_font_depth_end(typeset), 0)

    def test_stray_font_close_stays_at_the_end(self) -> None:
        logical = (
            "اعتقال المشتبه بهم\n"
            "اضغط <img  src='BUTTON_BACK' height='52' vspace='-26' width='52'> "
            "مرة أخرى</font> لاعتقالهم"
        )
        typeset = typeset_localization_text(logical, self.context)
        self.assertTrue(typeset.endswith("</font>"))
        self.assertGreater(typeset.lower().find("</font>"), typeset.find("\n"))
        self.assertEqual(_font_depth_min(typeset[: typeset.lower().rfind("</font>")]), 0)

    def test_trailing_break_inside_font_keeps_the_objective_on_one_line(self) -> None:
        logical = "قد إلى <font color='#34b76f'>مستوردات توب غلامور<br></font>"
        typeset = shape_localization_text(logical, self.context)
        drive = shape_plain_text("قد", self.context)
        name = shape_plain_text("مستوردات", self.context)
        br_at = typeset.lower().find("<br")
        self.assertGreater(br_at, 0)
        content = typeset[:br_at]
        self.assertIn(drive, content)
        self.assertIn(name, content)
        self.assertLess(content.index("<font"), content.index(drive))
        self.assertLess(content.index(name), content.index(drive))
        self.assertLess(typeset.lower().find("</font>"), br_at)
        self.assertEqual(_font_depth_min(content), 0)
        self.assertEqual(_font_depth_end(content), 0)
        width = _measure_visual_ltr(
            content.replace("<font color='#34b76f'>", "").replace("</font>", ""),
            self.context,
            HUD_INFO_FLASHER_FONT_SIZE_PX,
        )
        self.assertLessEqual(width, HUD_INFO_FLASHER_WIDTH_PX + 0.5)
        self.assertEqual(content.count("<br>"), 0)

    def test_long_phone_message_keeps_sentence_start_on_the_first_line(self) -> None:
        logical = "سمعت بما حدث، أتمنى أن يكون كل شيء بخير. عمي يثق بك الآن، لذا يجب أن تتصل به"
        typeset = shape_localization_text(
            logical,
            self.context,
            key_string="SMS_PRE_TRANS_DELIVERIES",
        )
        heard = shape_plain_text("سمعت", self.context)
        call = shape_plain_text("تتصل", self.context)
        lines = [line for line in typeset.split("<br>") if line != ""]
        self.assertGreater(len(lines), 1)
        self.assertIn(heard, lines[0])
        self.assertNotIn(heard, lines[-1])
        self.assertNotIn(call, lines[0])
        self.assertLess(typeset.index(heard), typeset.index(call))
        for line in lines:
            width = _measure_visual_ltr(line, self.context, PHONE_MESSAGE_FONT_SIZE_PX)
            self.assertLessEqual(width, PHONE_MESSAGE_WIDTH_PX + 0.5)

    def test_hud_default_wraps_wider_than_phone_sms(self) -> None:
        logical = "سمعت بما حدث، أتمنى أن يكون كل شيء بخير. عمي يثق بك الآن، لذا يجب أن تتصل به"
        phone = shape_localization_text(
            logical,
            self.context,
            key_string="SMS_PRE_TRANS_DELIVERIES",
        )
        hud = shape_localization_text(
            logical,
            self.context,
            resource_debug_name="EN_GameplayAct1",
            key_string="CASE_POLITICIAN2_OBJECTIVE_001",
        )
        self.assertGreater(phone.count("<br>"), hud.count("<br>"))
        for line in hud.split("<br>"):
            if line == "":
                continue
            width = _measure_visual_ltr(line, self.context, HUD_INFO_FLASHER_FONT_SIZE_PX)
            self.assertLessEqual(width, HUD_INFO_FLASHER_WIDTH_PX + 0.5)

    def test_subtitle_resource_does_not_wrap_a_phone_length_line(self) -> None:
        logical = "سمعت بما حدث، أتمنى أن يكون كل شيء بخير. عمي يثق بك الآن، لذا يجب أن تتصل به"
        typeset = shape_localization_text(
            logical,
            self.context,
            resource_debug_name="EN_NIS",
        )
        self.assertNotIn("<br>", typeset)
        width = _measure_visual_ltr(typeset, self.context, SUBTITLE_FONT_SIZE_PX)
        self.assertLessEqual(width, SUBTITLE_WIDTH_PX + 0.5)

    def test_newline_is_not_reversed_across_title_and_body(self) -> None:
        nodes = parse_loc_markup("عنوان\nسطر")
        kinds = [node.kind for node in nodes]
        self.assertEqual(kinds, ["text", "break", "text"])
        self.assertEqual(nodes[1].source, "\n")
        self.assertEqual([node.source for node in nodes], ["عنوان", "\n", "سطر"])


def _font_depth_min(text: str) -> int:
    depth = 0
    lowest = 0
    lower = text.lower()
    index = 0
    while index < len(lower):
        if lower.startswith("</font>", index):
            depth -= 1
            lowest = min(lowest, depth)
            index += 7
            continue
        if lower.startswith("<font", index):
            depth += 1
            index += 5
            continue
        index += 1
    return lowest


def _font_depth_end(text: str) -> int:
    depth = 0
    lower = text.lower()
    index = 0
    while index < len(lower):
        if lower.startswith("</font>", index):
            depth -= 1
            index += 7
            continue
        if lower.startswith("<font", index):
            depth += 1
            index += 5
            continue
        index += 1
    return depth


if __name__ == "__main__":
    unittest.main()
