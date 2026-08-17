from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Mapping

from bfa.json_codec import (
    JsonPath,
    apply_translations,
    decode_path,
    encode_path,
    extract_strings,
    read_json,
    write_json,
)
from bfa.models import ImportResult, PendingString

from .schema import SCHEMA


class TranslationDatabase:
    """SQLite repository for JSON documents, string occurrences, and translations."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, timeout=30.0)
        self.connection.row_factory = sqlite3.Row
        self._configure()
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def _configure(self) -> None:
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 30000")
        journal_mode = self.connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]
        if str(journal_mode).lower() != "wal":
            raise RuntimeError(f"SQLite WAL could not be enabled; mode is {journal_mode!r}")
        self.connection.execute("PRAGMA synchronous = NORMAL")

    @property
    def journal_mode(self) -> str:
        return str(self.connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> TranslationDatabase:
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        self.close()

    def import_document(self, source_path: Path) -> ImportResult:
        source_path = source_path.expanduser().resolve()
        payload = read_json(source_path)
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        extracted = list(extract_strings(payload))

        with self.connection:
            existing = self.connection.execute(
                "SELECT id FROM documents WHERE source_path = ?", (str(source_path),)
            ).fetchone()
            if existing:
                document_id = int(existing["id"])
                self.connection.execute(
                    "UPDATE documents SET source_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (serialized, document_id),
                )
                self.connection.execute(
                    "DELETE FROM occurrences WHERE document_id = ?", (document_id,)
                )
            else:
                cursor = self.connection.execute(
                    "INSERT INTO documents(source_path, source_json) VALUES (?, ?)",
                    (str(source_path), serialized),
                )
                document_id = int(cursor.lastrowid)

            for json_path, source_text in extracted:
                self.connection.execute(
                    "INSERT OR IGNORE INTO strings(source_text) VALUES (?)", (source_text,)
                )
                string_row = self.connection.execute(
                    "SELECT id FROM strings WHERE source_text = ?", (source_text,)
                ).fetchone()
                assert string_row is not None
                self.connection.execute(
                    "INSERT INTO occurrences(document_id, string_id, json_path) VALUES (?, ?, ?)",
                    (document_id, int(string_row["id"]), encode_path(json_path)),
                )

        return ImportResult(
            document_id=document_id,
            source_path=source_path,
            string_count=len({text for _path, text in extracted}),
            occurrence_count=len(extracted),
        )

    def pending_strings(self, target_language: str) -> list[PendingString]:
        rows = self.connection.execute(
            """
            SELECT s.id, s.source_text
            FROM strings AS s
            LEFT JOIN translations AS t
                ON t.string_id = s.id AND t.target_language = ?
            WHERE t.status IS NULL OR t.status != 'completed'
            ORDER BY s.id
            """,
            (target_language,),
        ).fetchall()
        return [PendingString(id=int(row["id"]), source_text=str(row["source_text"])) for row in rows]

    def save_translations(
        self,
        translations: Mapping[int, str],
        target_language: str,
    ) -> None:
        with self.connection:
            self.connection.executemany(
                """
                INSERT INTO translations(
                    string_id, target_language, translated_text, status, error_text, attempts
                ) VALUES (?, ?, ?, 'completed', NULL, 1)
                ON CONFLICT(string_id, target_language) DO UPDATE SET
                    translated_text = excluded.translated_text,
                    status = 'completed',
                    error_text = NULL,
                    attempts = translations.attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    (string_id, target_language, translated_text)
                    for string_id, translated_text in translations.items()
                ],
            )

    def save_failure(
        self,
        string_ids: list[int],
        target_language: str,
        error: str,
    ) -> None:
        with self.connection:
            self.connection.executemany(
                """
                INSERT INTO translations(
                    string_id, target_language, translated_text, status, error_text, attempts
                ) VALUES (?, ?, NULL, 'failed', ?, 1)
                ON CONFLICT(string_id, target_language) DO UPDATE SET
                    status = 'failed',
                    error_text = excluded.error_text,
                    attempts = translations.attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [(string_id, target_language, error[:2000]) for string_id in string_ids],
            )

    def _document_row(self, source_path: Path | None) -> sqlite3.Row:
        if source_path is None:
            rows = self.connection.execute("SELECT * FROM documents ORDER BY id").fetchall()
            if len(rows) != 1:
                raise ValueError("specify --source when the database contains zero or multiple documents")
            return rows[0]

        normalized = str(source_path.expanduser().resolve())
        row = self.connection.execute(
            "SELECT * FROM documents WHERE source_path = ?", (normalized,)
        ).fetchone()
        if row is None:
            raise ValueError(f"document is not imported: {normalized}")
        return row

    def export_document(
        self,
        output_path: Path,
        target_language: str,
        source_path: Path | None = None,
    ) -> None:
        document = self._document_row(source_path)
        payload = json.loads(str(document["source_json"]))
        rows = self.connection.execute(
            """
            SELECT o.json_path, t.translated_text
            FROM occurrences AS o
            LEFT JOIN translations AS t
                ON t.string_id = o.string_id AND t.target_language = ?
            WHERE o.document_id = ?
            """,
            (target_language, int(document["id"])),
        ).fetchall()
        replacements: dict[JsonPath, str] = {
            decode_path(str(row["json_path"])): str(row["translated_text"])
            for row in rows
            if row["translated_text"] is not None
        }
        write_json(output_path, apply_translations(payload, replacements))

    def counts(self, target_language: str) -> dict[str, int | str]:
        total = int(self.connection.execute("SELECT COUNT(*) FROM strings").fetchone()[0])
        completed = int(
            self.connection.execute(
                "SELECT COUNT(*) FROM translations WHERE target_language = ? AND status = 'completed'",
                (target_language,),
            ).fetchone()[0]
        )
        failed = int(
            self.connection.execute(
                "SELECT COUNT(*) FROM translations WHERE target_language = ? AND status = 'failed'",
                (target_language,),
            ).fetchone()[0]
        )
        return {
            "journal_mode": self.journal_mode,
            "strings": total,
            "completed": completed,
            "failed": failed,
            "pending": max(total - completed, 0),
        }
