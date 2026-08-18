"""SQLite persistence for Sleeping Dogs localization resources and entries."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Mapping, Sequence

from bfa.games.sleeping_dogs.localization import localization_control_tags
from bfa.games.sleeping_dogs.models import (
    DiscoveredLocalizationResource,
    ImportSummary,
    LocalizationEntry,
    LocalizationTable,
    StagedLocalizationEntry,
)
from bfa.models import PendingString

SCHEMA = """
CREATE TABLE IF NOT EXISTS sd_resources (
    id INTEGER PRIMARY KEY,
    archive_name TEXT NOT NULL,
    resource_path TEXT NOT NULL UNIQUE,
    source_language TEXT NOT NULL,
    debug_name TEXT NOT NULL,
    symbol_hash INTEGER NOT NULL,
    is_compressed INTEGER NOT NULL,
    extra_sz INTEGER NOT NULL DEFAULT 0,
    uncompressed_size INTEGER NOT NULL,
    original_uncompressed BLOB NOT NULL,
    original_raw BLOB NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sd_entries (
    id INTEGER PRIMARY KEY,
    resource_id INTEGER NOT NULL REFERENCES sd_resources(id) ON DELETE CASCADE,
    entry_index INTEGER NOT NULL,
    key_hash INTEGER NOT NULL,
    key_string TEXT,
    original_text TEXT NOT NULL,
    translated_text TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_text TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    control_tags TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource_id, entry_index)
);

CREATE INDEX IF NOT EXISTS idx_sd_entries_status
    ON sd_entries(status);
CREATE INDEX IF NOT EXISTS idx_sd_entries_resource
    ON sd_entries(resource_id);
"""


class SleepingDogsDatabase:
    """SQLite repository for Sleeping Dogs localization staging."""

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

    def __enter__(self) -> SleepingDogsDatabase:
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        self.close()

    def import_resources(
        self,
        resources: Sequence[DiscoveredLocalizationResource],
        *,
        source_language: str,
    ) -> ImportSummary:
        entries_imported = 0
        compressed = 0
        with self.connection:
            for resource in resources:
                existing = self.connection.execute(
                    "SELECT id FROM sd_resources WHERE resource_path = ?",
                    (resource.resource_path,),
                ).fetchone()
                if existing:
                    resource_id = int(existing["id"])
                    self.connection.execute(
                        "DELETE FROM sd_entries WHERE resource_id = ?",
                        (resource_id,),
                    )
                    self.connection.execute(
                        """
                        UPDATE sd_resources SET
                            archive_name = ?, source_language = ?, debug_name = ?,
                            symbol_hash = ?, is_compressed = ?, extra_sz = ?,
                            uncompressed_size = ?, original_uncompressed = ?, original_raw = ?
                        WHERE id = ?
                        """,
                        (
                            resource.archive_name,
                            resource.source_language,
                            resource.debug_name,
                            resource.symbol_hash,
                            int(resource.is_compressed),
                            resource.extra_sz,
                            len(resource.uncompressed),
                            resource.uncompressed,
                            resource.raw,
                            resource_id,
                        ),
                    )
                else:
                    cursor = self.connection.execute(
                        """
                        INSERT INTO sd_resources(
                            archive_name, resource_path, source_language, debug_name,
                            symbol_hash, is_compressed, extra_sz, uncompressed_size,
                            original_uncompressed, original_raw
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            resource.archive_name,
                            resource.resource_path,
                            resource.source_language,
                            resource.debug_name,
                            resource.symbol_hash,
                            int(resource.is_compressed),
                            resource.extra_sz,
                            len(resource.uncompressed),
                            resource.uncompressed,
                            resource.raw,
                        ),
                    )
                    resource_id = int(cursor.lastrowid)

                if resource.is_compressed:
                    compressed += 1

                rows = []
                for index, entry in enumerate(resource.table.entries):
                    status = "completed" if entry.text == "" else "pending"
                    translated = "" if entry.text == "" else None
                    rows.append(
                        (
                            resource_id,
                            index,
                            entry.key_hash,
                            entry.key_string,
                            entry.text,
                            translated,
                            status,
                            json.dumps(
                                localization_control_tags(entry.text),
                                ensure_ascii=False,
                            ),
                        )
                    )
                self.connection.executemany(
                    """
                    INSERT INTO sd_entries(
                        resource_id, entry_index, key_hash, key_string,
                        original_text, translated_text, status, control_tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                entries_imported += len(rows)

        return ImportSummary(
            resources=len(resources),
            entries=entries_imported,
            compressed_resources=compressed,
            direct_resources=len(resources) - compressed,
            source_language=source_language,
        )

    def pending_strings(self, _target_language: str | None = None) -> list[PendingString]:
        rows = self.connection.execute(
            """
            SELECT id, original_text
            FROM sd_entries
            WHERE status != 'completed'
            ORDER BY id
            """
        ).fetchall()
        return [
            PendingString(id=int(row["id"]), source_text=str(row["original_text"]))
            for row in rows
        ]

    def save_translations(
        self,
        translations: Mapping[int, str],
        _target_language: str | None = None,
    ) -> None:
        with self.connection:
            self.connection.executemany(
                """
                UPDATE sd_entries SET
                    translated_text = ?,
                    status = 'completed',
                    error_text = NULL,
                    attempts = attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                [
                    (translated_text, string_id)
                    for string_id, translated_text in translations.items()
                ],
            )

    def save_failure(
        self,
        string_ids: list[int],
        _target_language: str | None,
        error: str,
    ) -> None:
        with self.connection:
            self.connection.executemany(
                """
                UPDATE sd_entries SET
                    status = 'failed',
                    error_text = ?,
                    attempts = attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                [(error[:2000], string_id) for string_id in string_ids],
            )

    def counts(self) -> dict[str, int | str]:
        total = int(self.connection.execute("SELECT COUNT(*) FROM sd_entries").fetchone()[0])
        completed = int(
            self.connection.execute(
                "SELECT COUNT(*) FROM sd_entries WHERE status = 'completed'"
            ).fetchone()[0]
        )
        failed = int(
            self.connection.execute(
                "SELECT COUNT(*) FROM sd_entries WHERE status = 'failed'"
            ).fetchone()[0]
        )
        resources = int(self.connection.execute("SELECT COUNT(*) FROM sd_resources").fetchone()[0])
        compressed = int(
            self.connection.execute(
                "SELECT COUNT(*) FROM sd_resources WHERE is_compressed = 1"
            ).fetchone()[0]
        )
        return {
            "journal_mode": self.journal_mode,
            "resources": resources,
            "compressed_resources": compressed,
            "direct_resources": resources - compressed,
            "entries": total,
            "completed": completed,
            "failed": failed,
            "pending": max(total - completed, 0),
        }

    def resource_rows(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM sd_resources ORDER BY resource_path"
        ).fetchall()

    def entries_for_resource(self, resource_id: int) -> list[StagedLocalizationEntry]:
        resource = self.connection.execute(
            "SELECT * FROM sd_resources WHERE id = ?",
            (resource_id,),
        ).fetchone()
        if resource is None:
            raise ValueError(f"unknown Sleeping Dogs resource id {resource_id}")
        rows = self.connection.execute(
            """
            SELECT * FROM sd_entries
            WHERE resource_id = ?
            ORDER BY entry_index
            """,
            (resource_id,),
        ).fetchall()
        return [
            StagedLocalizationEntry(
                id=int(row["id"]),
                resource_path=str(resource["resource_path"]),
                archive_name=str(resource["archive_name"]),
                source_language=str(resource["source_language"]),
                entry_index=int(row["entry_index"]),
                key_hash=int(row["key_hash"]),
                key_string=row["key_string"],
                original_text=str(row["original_text"]),
                translated_text=row["translated_text"],
                status=str(row["status"]),
                control_tags=json.loads(str(row["control_tags"])),
                error_text=row["error_text"],
                attempts=int(row["attempts"]),
            )
            for row in rows
        ]

    def reconstructed_table(self, resource_row: sqlite3.Row) -> LocalizationTable:
        from bfa.games.sleeping_dogs.localization import parse_uilocalization_chunk

        table = parse_uilocalization_chunk(bytes(resource_row["original_uncompressed"]))
        staged = self.entries_for_resource(int(resource_row["id"]))
        if len(staged) != len(table.entries):
            raise ValueError(
                f"{resource_row['resource_path']} entry count changed since import"
            )
        updated: list[LocalizationEntry] = []
        for original, staged_entry in zip(table.entries, staged):
            if original.key_hash != staged_entry.key_hash:
                raise ValueError(
                    f"{resource_row['resource_path']} key hash changed at index "
                    f"{staged_entry.entry_index}"
                )
            text = (
                staged_entry.translated_text
                if staged_entry.translated_text is not None
                else original.text
            )
            updated.append(
                LocalizationEntry(
                    key_hash=original.key_hash,
                    text=text,
                    key_string=staged_entry.key_string or original.key_string,
                )
            )
        table.entries = updated
        return table
