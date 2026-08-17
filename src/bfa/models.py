from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PendingString:
    id: int
    source_text: str


@dataclass(frozen=True, slots=True)
class ImportResult:
    document_id: int
    source_path: Path
    string_count: int
    occurrence_count: int


@dataclass(frozen=True, slots=True)
class TranslationSummary:
    total: int
    completed: int
    failed: int
    batches: int
