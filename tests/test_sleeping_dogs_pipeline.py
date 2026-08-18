"""Pipeline tests for the Sleeping Dogs localization adapter."""

from __future__ import annotations

import asyncio
import hashlib
import tempfile
import unittest
from pathlib import Path

from bfa.config import Settings
from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.compression import decompress_qcmp, is_qcmp, wrap_pmcq
from bfa.games.sleeping_dogs.discover import discover_localization_resources
from bfa.games.sleeping_dogs.hash import qsymbol_hash
from bfa.games.sleeping_dogs.inspector import DEFAULT_GAME_PATH
from bfa.games.sleeping_dogs.localization import (
    encode_uilocalization_chunk,
    is_uilocalization_chunk,
    localization_control_tags,
    parse_uilocalization_chunk,
)
from bfa.games.sleeping_dogs.display_text import shape_localization_text
from bfa.games.sleeping_dogs.pack import build_translated_resources, table_with_texts
from bfa.games.sleeping_dogs.repository import SleepingDogsDatabase
from bfa.games.sleeping_dogs.translation import translate_pending
from bfa.games.sleeping_dogs.validation import (
    LocalizationValidationError,
    encode_and_reparse,
    localization_placeholders,
    validate_translated_text,
)
from bfa.models import PendingString
from providers.opencode import ProviderError


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _test_settings(**overrides: object) -> Settings:
    values = {
        "api_key": "test-key",
        "base_url": "http://127.0.0.1",
        "model": "test-model",
        "thinking": "disabled",
        "target_language": "Arabic",
        "workers": 8,
        "batch_size": 10,
        "request_retries": 0,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


class _FakeProvider:
    def __init__(self, mapping=None, error: Exception | None = None):
        self.mapping = mapping
        self.error = error
        self.calls = 0
        self.closed = False

    async def translate_batch(self, batch, target_language: str) -> dict[int, str]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        if self.mapping is None:
            return {item.id: f"AR:{item.source_text}" for item in batch}
        return {item.id: self.mapping(item) for item in batch}

    async def close(self) -> None:
        self.closed = True


class SleepingDogsPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.game_dir = DEFAULT_GAME_PATH
        if not cls.game_dir.is_dir():
            raise unittest.SkipTest(f"Game directory does not exist: {cls.game_dir}")
        bix = cls.game_dir / "UI.bix.bfa-original"
        big = cls.game_dir / "UI.big.bfa-original"
        if bix.is_file() and big.is_file():
            cls.ui_archive = BigArchive(bix, big)
        else:
            cls.ui_archive = BigArchive(cls.game_dir / "UI.bix")
        cls.discovered_en = discover_localization_resources([cls.ui_archive], language="EN")

    def _load(self, relative_path: str) -> bytes:
        entry = self.ui_archive.find_by_path(relative_path)
        self.assertIsNotNone(entry, relative_path)
        assert entry is not None
        return self.ui_archive.extract_entry(entry, decompress=True)

    def test_fixture_known_english_and_russian_strings(self) -> None:
        store = parse_uilocalization_chunk(self._load(r"Data\UI\Localization\EN_BA_3b_Store.bin"))
        self.assertEqual(store.entries[0].text, "Dammit!")

        chase = parse_uilocalization_chunk(self._load(r"Data\UI\Localization\EN_BA_3_Chase.bin"))
        texts = {entry.key_hash: entry.text for entry in chase.entries}
        self.assertEqual(texts[qsymbol_hash("WEI.M_BA.557.A")], "Where's Jackie?")

        russian = parse_uilocalization_chunk(self._load(r"Data\UI\Localization\RU_BA_3b_Store.bin"))
        self.assertEqual(russian.entries[0].text, "Проклятье!")

        frontend = parse_uilocalization_chunk(self._load(r"Data\UI\Localization\EN_Front-End.bin"))
        social = next(
            entry.text for entry in frontend.entries if entry.text.startswith("Welcome to Social Hub!")
        )
        self.assertEqual(
            localization_control_tags("Find health&nbsp;shrines &AMP; more"),
            ["&nbsp;", "&AMP;"],
        )

    def test_changed_length_arabic_round_trip(self) -> None:
        original = self._load(r"Data\UI\Localization\EN_BA_3b_Store.bin")
        table = parse_uilocalization_chunk(original)
        arabic = table_with_texts(table, ["اللعنة!"])
        encoded = encode_uilocalization_chunk(arabic, recompute_layout=True)
        self.assertNotEqual(encoded, original)
        self.assertEqual(len(encoded) % 8, 0)
        parsed = parse_uilocalization_chunk(encoded)
        self.assertEqual(parsed.entries[0].text, "اللعنة!")
        self.assertEqual(parsed.entries[0].key_hash, table.entries[0].key_hash)
        self.assertEqual(parsed.qchunk_size, len(encoded) - 16)
        self.assertEqual(parsed.qchunk_data_size, len(encoded) - 16)
        self.assertEqual(encode_and_reparse(arabic, recompute_layout=True), encoded)

    def test_control_tag_preservation_on_rebuild(self) -> None:
        original = self._load(r"Data\UI\Localization\EN_Front-End.bin")
        table = parse_uilocalization_chunk(original)
        social = next(
            entry for entry in table.entries if entry.text.startswith("Welcome to Social Hub!")
        )
        translated = social.text.replace(
            "Welcome to Social Hub!",
            "مرحباً بك في المركز الاجتماعي!",
        )
        validate_translated_text(social.text, translated)
        self.assertEqual(
            localization_control_tags(social.text),
            localization_control_tags(translated),
        )
        texts = [
            translated if entry.key_hash == social.key_hash else entry.text
            for entry in table.entries
        ]
        rebuilt = table_with_texts(table, texts)
        encoded = encode_and_reparse(rebuilt, recompute_layout=True)
        parsed = parse_uilocalization_chunk(encoded)
        parsed_social = next(
            entry.text for entry in parsed.entries if "المركز الاجتماعي" in entry.text
        )
        self.assertIn("<br><br>", parsed_social)

    def test_compressed_resource_changed_length_pmcq_wrap(self) -> None:
        path = r"Data\UI\Localization\EN_GameplayDLCNinNP.bin"
        entry = self.ui_archive.find_by_path(path)
        assert entry is not None
        self.assertTrue(entry.is_compressed)
        original = self.ui_archive.extract_entry(entry, decompress=True)
        table = parse_uilocalization_chunk(original)
        tagged = next(item for item in table.entries if "<font" in item.text)
        longer = tagged.text.replace("</font>", "!!!</font>")
        validate_translated_text(tagged.text, longer)
        texts = [longer if item.key_hash == tagged.key_hash else item.text for item in table.entries]
        encoded = encode_and_reparse(table_with_texts(table, texts), recompute_layout=True)
        wrapped = wrap_pmcq(encoded, extra_sz=entry.flags)
        self.assertTrue(is_qcmp(wrapped))
        round_trip = decompress_qcmp(wrapped, uncompressed_size=len(encoded))
        self.assertTrue(is_uilocalization_chunk(round_trip))
        parsed = parse_uilocalization_chunk(round_trip)
        self.assertEqual(len(parsed.entries), len(table.entries))
        self.assertTrue(any("!!!</font>" in item.text for item in parsed.entries))

    def test_direct_and_compressed_noop_identity(self) -> None:
        paths = [
            r"Data\UI\Localization\EN_BA_3b_Store.bin",
            r"Data\UI\Localization\EN_BA_3_Chase.bin",
            r"Data\UI\Localization\RU_BA_3b_Store.bin",
            r"Data\UI\Localization\EN_Front-End.bin",
            r"Data\UI\Localization\EN_GameplayDLCNinNP.bin",
        ]
        for path in paths:
            original = self._load(path)
            table = parse_uilocalization_chunk(original)
            rebuilt = encode_uilocalization_chunk(table)
            self.assertEqual(rebuilt, original, path)

    def test_malformed_translation_is_rejected(self) -> None:
        source = "Welcome to Social Hub!<br><br>Hello %d"
        with self.assertRaises(LocalizationValidationError):
            validate_translated_text(source, "مرحبا")
        with self.assertRaises(LocalizationValidationError):
            validate_translated_text("Score: %d of %d", "Score: %d")
        with self.assertRaises(LocalizationValidationError):
            validate_translated_text("Hi", "Hi\x00there")
        self.assertEqual(localization_placeholders("Collectibles: %d of %d, %d%%"), ["%d", "%d", "%d", "%%"])
        validate_translated_text("I'm 50% sure of it.", "أنا متأكد بنسبة 50%")
        validate_translated_text("10% strike damage increase", "زيادة ضرر الضربة بنسبة 10%")
        validate_translated_text("CLOSE NEWS &AMP; UPDATES", "إغلاق الأخبار &AMP; التحديثات")
        with self.assertRaises(LocalizationValidationError):
            validate_translated_text("CLOSE NEWS &AMP; UPDATES", "إغلاق الأخبار والتحديثات")

    def test_mixed_batch_rejects_only_invalid_translations(self) -> None:
        from bfa.games.sleeping_dogs.translation import _split_valid_translations

        batch = [
            PendingString(id=1, source_text="Welcome!<br><br>Hello"),
            PendingString(id=2, source_text="Dammit!"),
            PendingString(id=3, source_text="Score: %d of %d"),
        ]
        accepted, rejected = _split_valid_translations(
            batch,
            {
                1: "مرحبا",
                2: "اللعنة!",
                3: "",
            },
        )
        self.assertIn(1, accepted)
        self.assertIn("<br>", accepted[1])
        self.assertEqual(accepted[2], "اللعنة!")
        self.assertIn(3, rejected)

    def test_failed_batch_retry_and_malformed_provider_response(self) -> None:
        store = parse_uilocalization_chunk(self._load(r"Data\UI\Localization\EN_BA_3b_Store.bin"))
        chase = parse_uilocalization_chunk(self._load(r"Data\UI\Localization\EN_BA_3_Chase.bin"))
        selected = [
            item
            for item in self.discovered_en
            if item.debug_name in {"EN_BA_3b_Store", "EN_BA_3_Chase"}
        ]
        self.assertEqual(len(selected), 2)

        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "translations.sqlite"
            settings = _test_settings(batch_size=50, workers=2)
            with SleepingDogsDatabase(database_path) as database:
                imported = database.import_resources(selected, source_language="EN")
                self.assertEqual(imported.entries, len(store.entries) + len(chase.entries))
                self.assertEqual(database.journal_mode, "wal")

                fail_provider = _FakeProvider(error=ProviderError("model response was not valid JSON"))
                failed = asyncio.run(translate_pending(database, settings, fail_provider))
                self.assertEqual(failed.failed, imported.entries)
                self.assertEqual(failed.completed, 0)
                counts = database.counts()
                self.assertEqual(counts["failed"], imported.entries)

                retry = asyncio.run(translate_pending(database, settings, _FakeProvider()))
                self.assertEqual(retry.completed, imported.entries)
                self.assertEqual(retry.failed, 0)
                self.assertEqual(database.counts()["completed"], imported.entries)
                self.assertEqual(database.counts()["failed"], 0)

    def test_discover_all_english_resources_via_qsymbol_paths(self) -> None:
        discovered = self.discovered_en
        self.assertEqual(len(discovered), 421)
        self.assertEqual(sum(1 for item in discovered if item.is_compressed), 14)
        self.assertEqual(sum(1 for item in discovered if not item.is_compressed), 407)
        self.assertEqual(sum(len(item.table.entries) for item in discovered), 20508)
        store = next(item for item in discovered if item.debug_name == "EN_BA_3b_Store")
        self.assertEqual(store.table.entries[0].text, "Dammit!")
        self.assertEqual(store.table.entries[0].key_string, "ZIWAI.M_BA.119.A")
        self.assertTrue(
            all(
                item.resource_path == rf"Data\UI\Localization\{item.debug_name}.bin"
                for item in discovered
            )
        )
        self.assertNotIn("RU_BA_3b_Store", {item.debug_name for item in discovered})

    def test_import_translate_build_isolated_output_and_game_untouched(self) -> None:
        before = {
            "UI.bix": _sha256(self.game_dir / "UI.bix"),
            "UI.big": _sha256(self.game_dir / "UI.big"),
        }
        discovered = self.discovered_en
        wanted = {
            "EN_BA_3b_Store",
            "EN_BA_3_Chase",
            "EN_Front-End",
            "EN_GameplayDLCNinNP",
        }
        selected = [item for item in discovered if item.debug_name in wanted]
        self.assertEqual(len(selected), 4)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            database_path = root / "translations.sqlite"
            output_dir = root / "sleeping_dogs_ar"
            settings = _test_settings()

            def map_item(item: PendingString) -> str:
                if item.source_text == "Dammit!":
                    return "اللعنة!"
                return f"AR:{item.source_text}"

            with SleepingDogsDatabase(database_path) as database:
                imported = database.import_resources(selected, source_language="EN")
                self.assertGreater(imported.compressed_resources, 0)
                self.assertGreater(imported.direct_resources, 0)
                summary = asyncio.run(
                    translate_pending(database, settings, _FakeProvider(mapping=map_item))
                )
                self.assertEqual(summary.failed, 0)
                self.assertEqual(summary.completed, imported.entries)
                packed = build_translated_resources(database, output_dir)

            self.assertEqual(packed.resources_written, 4)
            self.assertEqual(packed.failed_resources, 0)
            store_out = output_dir / "Data" / "UI" / "Localization" / "EN_BA_3b_Store.bin"
            store_overlay = output_dir / "RedirectorData" / "UI" / "Localization" / "EN_BA_3b_Store.bin"
            chase_out = output_dir / "Data" / "UI" / "Localization" / "EN_BA_3_Chase.bin"
            frontend_out = output_dir / "Data" / "UI" / "Localization" / "EN_Front-End.bin"
            compressed_out = output_dir / "Data" / "UI" / "Localization" / "EN_GameplayDLCNinNP.bin"
            self.assertTrue(store_out.is_file())
            self.assertTrue(store_overlay.is_file())
            self.assertEqual(store_overlay.read_bytes(), store_out.read_bytes())
            self.assertEqual(
                parse_uilocalization_chunk(store_out.read_bytes()).entries[0].text,
                shape_localization_text("اللعنة!"),
            )
            chase = parse_uilocalization_chunk(chase_out.read_bytes())
            self.assertIn("AR:Where's Jackie?", [entry.text for entry in chase.entries])
            frontend = parse_uilocalization_chunk(frontend_out.read_bytes())
            social = next(entry.text for entry in frontend.entries if "Social Hub" in entry.text or "AR:Welcome" in entry.text)
            self.assertIn("<br><br>", social)
            nin = parse_uilocalization_chunk(compressed_out.read_bytes())
            self.assertTrue(any("<font" in entry.text for entry in nin.entries))
            self.assertTrue(is_uilocalization_chunk(compressed_out.read_bytes()))

            original_store = self._load(r"Data\UI\Localization\EN_BA_3b_Store.bin")
            self.assertNotEqual(store_out.read_bytes(), original_store)

        self.assertEqual(_sha256(self.game_dir / "UI.bix"), before["UI.bix"])
        self.assertEqual(_sha256(self.game_dir / "UI.big"), before["UI.big"])

    def test_noop_translated_resource_keeps_original_bytes(self) -> None:
        selected = [item for item in self.discovered_en if item.debug_name == "EN_BA_3b_Store"]
        original = selected[0].uncompressed
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with SleepingDogsDatabase(root / "db.sqlite") as database:
                database.import_resources(selected, source_language="EN")
                pending = database.pending_strings("Arabic")
                database.save_translations(
                    {item.id: item.source_text for item in pending},
                    "Arabic",
                )
                packed = build_translated_resources(database, root / "out")
            self.assertEqual(packed.resources_written, 1)
            written = (root / "out" / "Data" / "UI" / "Localization" / "EN_BA_3b_Store.bin").read_bytes()
            self.assertEqual(written, original)

    def test_all_english_resources_fake_translate_and_rebuild(self) -> None:
        self.assertEqual(len(self.discovered_en), 421)
        before_bix = _sha256(self.game_dir / "UI.bix")
        before_big = _sha256(self.game_dir / "UI.big")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output_dir = root / "sleeping_dogs_ar"
            settings = _test_settings(workers=20, batch_size=50)
            with SleepingDogsDatabase(root / "translations.sqlite") as database:
                imported = database.import_resources(self.discovered_en, source_language="EN")
                self.assertEqual(imported.resources, 421)
                self.assertEqual(imported.entries, 20508)
                self.assertEqual(imported.compressed_resources, 14)
                self.assertEqual(imported.direct_resources, 407)
                summary = asyncio.run(translate_pending(database, settings, _FakeProvider()))
                self.assertEqual(summary.failed, 0)
                self.assertEqual(summary.completed, 20508)
                packed = build_translated_resources(database, output_dir)
            self.assertEqual(packed.resources_written, 421)
            self.assertEqual(packed.entries_written, 20508)
            self.assertEqual(packed.failed_resources, 0)
            self.assertEqual(packed.compressed_resources, 14)
            self.assertEqual(packed.direct_resources, 407)
            store = parse_uilocalization_chunk(
                (output_dir / "Data" / "UI" / "Localization" / "EN_BA_3b_Store.bin").read_bytes()
            )
            self.assertEqual(store.entries[0].text, "AR:Dammit!")
            frontend = parse_uilocalization_chunk(
                (output_dir / "Data" / "UI" / "Localization" / "EN_Front-End.bin").read_bytes()
            )
            social = next(entry.text for entry in frontend.entries if "Social Hub" in entry.text)
            self.assertIn("<br><br>", social)
            written = list((output_dir / "Data" / "UI" / "Localization").glob("EN_*.bin"))
            self.assertEqual(len(written), 421)
            sample = parse_uilocalization_chunk(written[0].read_bytes())
            self.assertGreater(len(sample.entries), 0)
        self.assertEqual(_sha256(self.game_dir / "UI.bix"), before_bix)
        self.assertEqual(_sha256(self.game_dir / "UI.big"), before_big)


if __name__ == "__main__":
    unittest.main()
