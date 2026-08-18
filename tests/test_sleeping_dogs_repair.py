"""Repair of model translations that drop or rewrite Sleeping Dogs markup."""

from __future__ import annotations

import unittest

from bfa.games.sleeping_dogs.repair import is_markup_only, repair_translated_text
from bfa.games.sleeping_dogs.validation import validate_translated_text


class SleepingDogsRepairTests(unittest.TestCase):
    def test_markup_only_strings_are_copied(self) -> None:
        self.assertTrue(is_markup_only("<br>"))
        self.assertTrue(is_markup_only("%s"))
        self.assertTrue(is_markup_only("  "))
        self.assertFalse(is_markup_only("Call from %s"))
        self.assertFalse(is_markup_only("CLOSE NEWS &AMP; UPDATES"))

    def test_restores_dropped_nbsp(self) -> None:
        source = "Take the parked car out front.&nbsp; Bring it back in one piece."
        translated = "خذ السيارة المتوقفة في الأمام. أعدها قطعة واحدة."
        repaired = repair_translated_text(source, translated)
        validate_translated_text(source, repaired)
        self.assertIn("&nbsp;", repaired)

    def test_restores_amp_entity_case(self) -> None:
        source = "CLOSE NEWS &AMP; UPDATES"
        translated = "إغلاق الأخبار والتحديثات"
        repaired = repair_translated_text(source, translated)
        validate_translated_text(source, repaired)
        self.assertIn("&AMP;", repaired)

    def test_rewrites_font_case_and_nbsp(self) -> None:
        source = "Defeat the&nbsp;<font color='#ad2f23'>Thugs</font>"
        translated = "اهزم <Font color='#ad2f23'>البلطجية</Font>"
        repaired = repair_translated_text(source, translated)
        validate_translated_text(source, repaired)
        self.assertIn("&nbsp;", repaired)
        self.assertIn("<font color='#ad2f23'>", repaired)
        self.assertIn("</font>", repaired)

    def test_rewrites_img_whitespace_and_case(self) -> None:
        source = "<IMG  SRC='ICON_REWARD_BIO' HEIGHT='24' VSPACE='-8' WIDTH='24'>FIELD REPORT"
        translated = "<IMG SRC='ICON_REWARD_BIO' HEIGHT='24' VSPACE='-8' WIDTH='24'>تقرير ميداني"
        repaired = repair_translated_text(source, translated)
        validate_translated_text(source, repaired)
        self.assertTrue(repaired.startswith("<IMG  SRC='ICON_REWARD_BIO'"))

    def test_rewrites_mismatched_job_closer(self) -> None:
        source = "<font color='#f08728'>Aberdeen Derby</job>"
        translated = "<font color='#f08728'>ديربي أبردين</font>"
        repaired = repair_translated_text(source, translated)
        validate_translated_text(source, repaired)
        self.assertIn("</job>", repaired)
        self.assertNotIn("</font>", repaired)

    def test_restores_missing_font_wrapper(self) -> None:
        source = "Rendezvous with the <font color='#1D6BA9'>patrol</font> under fire"
        translated = "التقي بالدورية تحت النار"
        repaired = repair_translated_text(source, translated)
        validate_translated_text(source, repaired)
        self.assertIn("<font color='#1D6BA9'>", repaired)
        self.assertIn("</font>", repaired)

    def test_restores_placeholders(self) -> None:
        source = "Upgrades: %d of %d, %d%%"
        translated = "الترقيات: %d من %d، %d%"
        repaired = repair_translated_text(source, translated)
        validate_translated_text(source, repaired)
        self.assertIn("%%", repaired)

        dropped = repair_translated_text("Call from %s", "مكالمة من")
        validate_translated_text("Call from %s", dropped)
        self.assertIn("%s", dropped)

        extra = repair_translated_text("Call from %s", "مكالمة من %s %%")
        validate_translated_text("Call from %s", extra)
        self.assertNotIn("%%", extra)

    def test_empty_translation_is_not_faked(self) -> None:
        source = "Don't kill anyone"
        self.assertEqual(repair_translated_text(source, ""), "")

    def test_complex_button_prompt(self) -> None:
        source = (
            "Press <img  src='BUTTON_BUTTON1' height='52' width='52' vspace='-26'> "
            "while vaulting"
        )
        translated = "اضغط <img src='BUTTON_BUTTON1' height='52' width='52' vspace='-26'> أثناء القفز"
        repaired = repair_translated_text(source, translated)
        validate_translated_text(source, repaired)
        self.assertIn("<img  src='BUTTON_BUTTON1' height='52' width='52' vspace='-26'>", repaired)


if __name__ == "__main__":
    unittest.main()
