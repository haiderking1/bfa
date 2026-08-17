from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sqlite.repository import TranslationDatabase


class PipelineDatabaseTests(unittest.TestCase):
    def test_json_sqlite_json_round_trip_with_wal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.json"
            database_path = root / "translations.sqlite"
            output = root / "translated.json"
            source.write_text(
                json.dumps(
                    {
                        "title": "New Game",
                        "menu": {"start": "Start", "again": "Start"},
                        "items": ["Sword", 42, True],
                    }
                ),
                encoding="utf-8",
            )

            with TranslationDatabase(database_path) as database:
                self.assertEqual(database.journal_mode, "wal")
                imported = database.import_document(source)
                self.assertEqual(imported.string_count, 3)
                self.assertEqual(imported.occurrence_count, 4)

                pending = database.pending_strings("Arabic")
                database.save_translations(
                    {item.id: f"AR:{item.source_text}" for item in pending},
                    "Arabic",
                )
                database.export_document(output, "Arabic", source)

            translated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(translated["title"], "AR:New Game")
            self.assertEqual(translated["menu"]["start"], "AR:Start")
            self.assertEqual(translated["menu"]["again"], "AR:Start")
            self.assertEqual(translated["items"], ["AR:Sword", 42, True])


if __name__ == "__main__":
    unittest.main()
