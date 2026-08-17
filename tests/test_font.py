"""Unit tests for BFA font extension and verification."""

from __future__ import annotations

import unittest
from pathlib import Path

from tooling.validator import REQUESTED_UNICODES, validate_font


class BFAFontExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.font_path = Path(__file__).parent.parent / "fonts" / "bfa.ttf"

    def test_font_file_exists(self) -> None:
        self.assertTrue(self.font_path.exists(), f"Font file not found at {self.font_path}")

    def test_full_font_validation_suite(self) -> None:
        report = validate_font(self.font_path)
        self.assertTrue(
            report.is_valid,
            f"Font validation failed with errors: {report.failed_checks}",
        )
        self.assertEqual(len(report.failed_checks), 0)

    def test_all_requested_characters_count(self) -> None:
        self.assertEqual(len(REQUESTED_UNICODES), 51)


if __name__ == "__main__":
    unittest.main()
