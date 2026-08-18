"""Tests for the shared BFA font asset and DefineFont3 builder."""

from __future__ import annotations

import unittest
from pathlib import Path

from bfa.fonts.asset import BFA_FONT_PATH, load_bfa_font, require_bfa_font
from bfa.fonts.define_font3 import (
    build_define_font3,
    font3_scale,
    parse_define_font3,
)
from bfa.fonts.swf import (
    decode_rect,
    encode_dummy_font_bounds,
    encode_empty_glyph_shape,
    encode_rect,
    encode_swf_tag,
    first_style_change_fills,
    parse_swf_tags,
    SwfTag,
)


class BfaFontAssetTests(unittest.TestCase):
    def test_require_bfa_font_points_at_repo_typeface(self) -> None:
        path = require_bfa_font()
        self.assertEqual(path, BFA_FONT_PATH)
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 0)

    def test_missing_font_is_an_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            require_bfa_font(Path("/tmp/bfa-missing-font.ttf"))

    def test_load_bfa_font_has_arabic_and_space(self) -> None:
        font = load_bfa_font()
        cmap = font.getBestCmap()
        self.assertIn(32, cmap)
        arabic = [code for code in cmap if 0x0600 <= code <= 0x06FF]
        self.assertGreaterEqual(len(arabic), 30)
        self.assertEqual(int(font["head"].unitsPerEm), 2048)
        self.assertAlmostEqual(font3_scale(2048), 10.0)


class SwfCodecTests(unittest.TestCase):
    def test_rect_round_trip(self) -> None:
        encoded = encode_rect(-20, 400, -80, 200)
        decoded, consumed = decode_rect(encoded)
        self.assertEqual(decoded, (-20, 400, -80, 200))
        self.assertEqual(consumed, len(encoded))

    def test_zero_rect_and_empty_glyph(self) -> None:
        encoded = encode_rect(0, 0, 0, 0)
        decoded, consumed = decode_rect(encoded)
        self.assertEqual(decoded, (0, 0, 0, 0))
        self.assertEqual(consumed, len(encoded))
        self.assertEqual(encode_empty_glyph_shape(), b"\x10\x00")
        self.assertEqual(first_style_change_fills(b"\x10\x00"), (1, 0, 0))
        self.assertEqual(encode_dummy_font_bounds(), b"\x08\x00")

    def test_swf_tag_round_trip(self) -> None:
        tags = [SwfTag(code=75, payload=b"abc" * 30), SwfTag(code=0, payload=b"")]
        blob = b"".join(encode_swf_tag(tag) for tag in tags)
        parsed, end = parse_swf_tags(blob)
        self.assertEqual(end, len(blob))
        self.assertEqual([(tag.code, tag.payload) for tag in parsed], [(75, b"abc" * 30), (0, b"")])


class DefineFont3FromBfaTests(unittest.TestCase):
    def test_bfa_define_font3_keeps_name_and_arabic(self) -> None:
        payload = build_define_font3(
            BFA_FONT_PATH,
            font_id=3,
            name="DINCondensedTT",
            flags=0x8C,
            language=1,
        )
        parsed = parse_define_font3(payload)
        self.assertEqual(parsed.font_id, 3)
        self.assertEqual(parsed.name, "DINCondensedTT")
        self.assertEqual(parsed.language, 1)
        self.assertTrue(parsed.flags & 0x80)
        self.assertTrue(parsed.flags & 0x08)
        self.assertTrue(parsed.flags & 0x04)
        self.assertIn(32, parsed.codes)
        self.assertIn(ord("A"), parsed.codes)
        self.assertIn(0x0627, parsed.codes)
        self.assertGreaterEqual(sum(1 for code in parsed.codes if 0x0600 <= code <= 0x06FF), 30)
        self.assertEqual(len(parsed.shapes), len(parsed.codes))
        self.assertEqual(len(parsed.advances), len(parsed.codes))
        space_index = parsed.codes.index(32)
        self.assertEqual(parsed.shapes[space_index], b"\x10\x00")
        self.assertGreater(parsed.advances[space_index], 0)
        self.assertGreater(parsed.ascent, 0)
        self.assertGreater(parsed.descent, 0)
        letter_index = parsed.codes.index(ord("A"))
        self.assertGreater(len(parsed.shapes[letter_index]), 2)
        fill_bits, fill0, fill1 = first_style_change_fills(parsed.shapes[letter_index])
        self.assertEqual(fill_bits, 1)
        self.assertEqual(fill0, 1)
        self.assertEqual(fill1, 0)
        arabic_index = parsed.codes.index(0x0627)
        arabic_fills = first_style_change_fills(parsed.shapes[arabic_index])
        self.assertEqual(arabic_fills, (1, 1, 0))


if __name__ == "__main__":
    unittest.main()
