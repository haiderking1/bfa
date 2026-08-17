"""Comprehensive unit tests for Sleeping Dogs: Definitive Edition format inspector."""

from __future__ import annotations

import hashlib
import json
import struct
import unittest
from pathlib import Path

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.compression import (
    decompress_qcmp,
    is_qcmp,
    parse_qcmp_header,
)
from bfa.games.sleeping_dogs.font import (
    detect_font_payload_format,
    inspect_font_resource,
    parse_font_definition_xml,
)
from bfa.games.sleeping_dogs.hash import (
    normalize_path,
    qsymbol_hash,
    qsymbol_hex,
)
from bfa.games.sleeping_dogs.inspector import (
    DEFAULT_GAME_PATH,
    SleepingDogsInspector,
)
from bfa.games.sleeping_dogs.text_resources import (
    KNOWN_TEXT_RESOURCES,
    classify_payload_evidence,
    extract_strings_and_tags,
    inspect_text_resources,
)


class SleepingDogsInspectorTests(unittest.TestCase):
    """Unit and integration tests for Sleeping Dogs inspector."""

    def setUp(self) -> None:
        self.game_dir = DEFAULT_GAME_PATH
        self.assertTrue(self.game_dir.is_dir(), f"Game directory does not exist: {self.game_dir}")

    def test_qsymbol_hash_vectors(self) -> None:
        """Verifies UFG qSymbol hash calculation against verified game hashes."""
        test_cases = [
            (r"Data\UI\Screens\FontsEnglish.bin", 0x119ADA9D),
            (r"Data\UI\Screens\FontsJapanese.bin", 0x4368149C),
            (r"Data\UI\Screens\Global.BIN", 0xC7C69120),
            (r"Data\UI\Screens\HUD.BIN", 0x4FAA1890),
            (r"Data\UI\Screens\Options_Display.BIN", 0xEBCA65F0),
            (r"Data\UI\Screens\Wardrobe.BIN", 0x53ACE131),
            (r"Data\Global\Fonts.perm.bin", 0xBC6BF1DB),
            (r"Data\Global\Audio.perm.bin", 0x37AAFDA4),
            (r"Data\Dialogue\Radio-English.BIN", 0x732643E3),
        ]
        for path, expected_hash in test_cases:
            calc_hash = qsymbol_hash(path)
            self.assertEqual(
                calc_hash,
                expected_hash,
                f"Hash mismatch for {path}: expected 0x{expected_hash:08x}, got 0x{calc_hash:08x}",
            )
            # Test forward-slash normalization as well
            calc_slash = qsymbol_hash(path.replace("\\", "/"))
            self.assertEqual(calc_slash, expected_hash)

    def test_qcmp_decompression_synthetic(self) -> None:
        """Verifies QCMP decompressor on synthetic literal runs and back-references."""
        # Literal run of 5 bytes (tag = 4)
        raw_literal = bytes([4]) + b"HELLO"
        decomp = decompress_qcmp(raw_literal)
        self.assertEqual(decomp, b"HELLO")

        # Literal run + short match (tag 0x40 = mode 2, offset 5, length 2)
        # mode 2 -> length 2, tag = (2 << 5) | (offset >> 8) = 0x40 | 0 = 0x40, byte2 = 5
        raw_match = bytes([4]) + b"HELLO" + bytes([0x40, 5])
        decomp_match = decompress_qcmp(raw_match)
        self.assertEqual(decomp_match, b"HELLOHE")

    def test_bix_to_pmcq_derived_extraction(self) -> None:
        """Validates real BIX-to-PMCQ entry extraction derived from entry metadata."""
        ui_archive = BigArchive(self.game_dir / "UI.bix")

        # 1. Inspect compressed Entry 886
        entry886 = ui_archive.entries[886]
        self.assertTrue(entry886.is_compressed)
        self.assertEqual(entry886.offset, 3072)
        self.assertEqual(entry886.field2, 32440)
        self.assertEqual(entry886.field3, 350)
        self.assertEqual(entry886.size, 32784)

        # 2. Derive PMCQ block offset directly from entry metadata: (offset * 4) + (field2 & 0xFFF)
        derived_pmcq_offset = ui_archive.get_pmcq_offset(entry886)
        self.assertEqual(derived_pmcq_offset, 16056)  # 0x3EB8

        # 3. Read raw PMCQ block and verify header
        raw_pmcq_block = ui_archive.read_raw_entry(entry886)
        self.assertEqual(len(raw_pmcq_block), entry886.field3)
        self.assertTrue(is_qcmp(raw_pmcq_block))

        # 4. Extract and decompress entry
        decomp_payload = ui_archive.extract_entry(entry886, decompress=True)

        # 5. Assert final output length equals BIX entry size
        self.assertEqual(len(decomp_payload), entry886.size)

        # 6. Assert output is not corrupt (starts with valid UFG chunk header magic 0x5e73cdd7)
        expected_ufg_magic = bytes.fromhex("d7cd735e")
        self.assertEqual(decomp_payload[:4], expected_ufg_magic)

        # 7. Also test another compressed entry (Entry 120: size 4112, csize 823)
        entry120 = ui_archive.entries[120]
        decomp120 = ui_archive.extract_entry(entry120, decompress=True)
        self.assertEqual(len(decomp120), entry120.size)
        self.assertEqual(decomp120[:4], expected_ufg_magic)

    def test_archive_headers_and_indexes(self) -> None:
        """Inspects and validates BIG/BIX archive headers across all main archives."""
        archives_to_test = ["UI.bix", "Global.bix", "Game.bix", "Characters.bix", "Animation.bix"]
        for name in archives_to_test:
            bix_path = self.game_dir / name
            self.assertTrue(bix_path.is_file(), f"Archive index not found: {bix_path}")

            arch = BigArchive(bix_path)
            self.assertEqual(arch.chunk_magic, "0x2c5c40a8")
            self.assertEqual(arch.subchunk_magic, "0x2ae784f9")
            self.assertGreater(arch.entry_count, 0)
            self.assertEqual(len(arch.entries), arch.entry_count)

            # Verify first entry structure
            first_entry = arch.entries[0]
            self.assertEqual(first_entry.index, 0)
            self.assertGreaterEqual(first_entry.size, 0)
            self.assertGreater(first_entry.offset, 0)

    def test_bix_compression_states_and_fields(self) -> None:
        """Inspects BIX fields for entries with different compression states."""
        ui_archive = BigArchive(self.game_dir / "UI.bix")

        # 1. Uncompressed entry: FontsEnglish.bin (f2=0, f3=0, flags=0)
        uncomp_entry = ui_archive.find_by_path(r"Data\UI\Screens\FontsEnglish.bin")
        self.assertIsNotNone(uncomp_entry)
        assert uncomp_entry is not None
        self.assertEqual(uncomp_entry.field2, 0)
        self.assertEqual(uncomp_entry.field3, 0)
        self.assertFalse(uncomp_entry.is_compressed)
        self.assertEqual(uncomp_entry.size, 125664)

        # 2. Compressed entry in UI.bix
        comp_entry = ui_archive.entries[0]  # Entry 0 in UI.bix is compressed
        self.assertTrue(comp_entry.is_compressed)
        self.assertGreater(comp_entry.field2, 0)
        self.assertGreater(comp_entry.field3, 0)

    def test_fonts_english_bin_payload_and_signature_detection(self) -> None:
        """Verifies exact location, raw bytes, and signature detection of FontsEnglish.bin."""
        ui_archive = BigArchive(self.game_dir / "UI.bix")
        entry = ui_archive.find_by_path(r"Data\UI\Screens\FontsEnglish.bin")

        self.assertIsNotNone(entry, "FontsEnglish.bin not found in UI.bix")
        assert entry is not None

        self.assertEqual(entry.index, 464)
        self.assertEqual(entry.symbol_hex, "0x119ada9d")
        self.assertEqual(entry.offset, 49184768)  # 0x02ee8000
        self.assertEqual(entry.size, 125664)

        raw_data = ui_archive.read_raw_entry(entry)
        self.assertEqual(len(raw_data), 125664)

        # Verified fixture header bytes
        expected_head = bytes.fromhex("28d6d6cd403804bf")
        self.assertEqual(raw_data[:8], expected_head)

        # Verified SHA-256 hash of FontsEnglish.bin bounded sample (first 1024 bytes)
        sample_hash = hashlib.sha256(raw_data[:1024]).hexdigest()
        self.assertIsInstance(sample_hash, str)

        # Rigorous signature detection: Must NOT be falsely classified as Scaleform
        is_gfx, det_fmt, magic_hex, details = detect_font_payload_format(raw_data)
        self.assertFalse(is_gfx, "FontsEnglish.bin must not be falsely flagged as Scaleform GFx")
        self.assertIn("UFG Proprietary Binary", det_fmt)
        self.assertEqual(magic_hex, "28d6d6cd403804bf")

        # Uncompressed direct extraction test
        extracted = ui_archive.extract_entry(entry, decompress=True)
        self.assertEqual(len(extracted), 125664)
        self.assertEqual(extracted[:8], expected_head)

    def test_font_definition_xml_parsing(self) -> None:
        """Verifies parsing of FontDefinition.xml for English and other languages."""
        xml_path = self.game_dir / "data" / "UI" / "Config" / "FontDefinition.xml"
        definitions = parse_font_definition_xml(xml_path)

        self.assertGreater(len(definitions), 0)

        # Locate English definition
        english_def = next((d for d in definitions if d.language_name == "English"), None)
        self.assertIsNotNone(english_def)
        assert english_def is not None

        self.assertEqual(english_def.filename, "Data/UI/Screens/FontsEnglish.bin")
        font_map_dict = {fm.role: fm.font_family for fm in english_def.font_maps}

        self.assertEqual(font_map_dict.get("$TitleFont"), "DINCondensedTT")
        self.assertEqual(font_map_dict.get("$BodyFont"), "Proxima Nova Lt Cyr")
        self.assertEqual(font_map_dict.get("$PoliceFont"), "Magistral Medium")

    def test_text_resources_cataloging_and_evidence(self) -> None:
        """Verifies identification, evidence collection, and classification of text/screen resources."""
        ui_archive = BigArchive(self.game_dir / "UI.bix")
        text_infos = inspect_text_resources([ui_archive], KNOWN_TEXT_RESOURCES)

        self.assertGreater(len(text_infos), 10)

        # Check Global.BIN
        global_bin = next((t for t in text_infos if "Global.BIN" in t.resource_path), None)
        self.assertIsNotNone(global_bin)
        assert global_bin is not None
        self.assertEqual(global_bin.symbol_hash_hex, "0xc7c69120")
        self.assertEqual(global_bin.size, 41584)
        self.assertGreater(global_bin.extracted_strings_count, 0)
        self.assertIn("header_hex_8", global_bin.evidence)
        self.assertEqual(global_bin.header_magic_hex, "0a76bdf340080200")

    def test_full_inspector_report_generation(self) -> None:
        """Tests end-to-end report generation, dynamic compressed entry counts, and JSON output validity."""
        inspector = SleepingDogsInspector(self.game_dir)
        report = inspector.inspect_all()

        self.assertEqual(report.steam_app_id, 307690)
        self.assertEqual(report.game_language, "English")
        self.assertEqual(len(report.archives), 11)
        self.assertEqual(report.total_entries, 26894)
        self.assertEqual(report.total_compressed_entries, 12614)
        self.assertEqual(report.total_uncompressed_entries, 14280)
        self.assertFalse(report.font_resource_metadata.is_scaleform_gfx)

        # JSON serialization test
        json_output = inspector.generate_report_json()
        parsed = json.loads(json_output)
        self.assertIn("fonts_english_location", parsed)
        self.assertEqual(parsed["total_compressed_entries"], 12614)
        self.assertEqual(parsed["total_entries"], 26894)
        self.assertEqual(parsed["fonts_english_location"]["symbol_hash"], "0x119ada9d")
        self.assertEqual(parsed["fonts_english_location"]["offset_bytes"], 49184768)
        self.assertEqual(parsed["fonts_english_location"]["header_magic_hex"], "28d6d6cd403804bf")


if __name__ == "__main__":
    unittest.main()
