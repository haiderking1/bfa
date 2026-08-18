"""Write translated Sleeping Dogs localization BINs to an isolated workspace."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from bfa.fonts.shape import load_shape_context
from bfa.games.sleeping_dogs.compression import wrap_pmcq
from bfa.games.sleeping_dogs.display_text import shape_localization_table
from bfa.games.sleeping_dogs.models import LocalizationEntry, LocalizationTable, PackSummary
from bfa.games.sleeping_dogs.redirector import write_packaged_resource
from bfa.games.sleeping_dogs.repository import SleepingDogsDatabase
from bfa.games.sleeping_dogs.validation import (
    LocalizationValidationError,
    encode_and_reparse,
    validate_resource_translations,
)


def build_translated_resources(
    database: SleepingDogsDatabase,
    output_dir: Path,
    *,
    wrap_compressed: bool = False,
) -> PackSummary:
    """Validates completed resources and writes them under ``output_dir``.

    Incomplete resources are skipped. The original game installation is never
    opened or modified; bytes come from the staging database.
    """
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    failed = 0
    entries_written = 0
    compressed_written = 0
    direct_written = 0
    shape_context = load_shape_context()

    for resource in database.resource_rows():
        staged = database.entries_for_resource(int(resource["id"]))
        source_texts = [item.original_text for item in staged]
        translated_texts = [
            item.translated_text if item.status == "completed" else None
            for item in staged
        ]
        try:
            validate_resource_translations(source_texts, translated_texts)
        except LocalizationValidationError:
            if any(text is None for text in translated_texts):
                skipped += 1
            else:
                failed += 1
                skipped += 1
            continue
        try:
            table = shape_localization_table(
                database.reconstructed_table(resource),
                shape_context,
            )
            changed = any(
                item.translated_text != item.original_text
                or item.translated_text != table.entries[index].text
                for index, item in enumerate(staged)
            )
            encoded = encode_and_reparse(table, recompute_layout=changed)
            if not changed:
                original = bytes(resource["original_uncompressed"])
                if encoded != original:
                    raise LocalizationValidationError(
                        f"{resource['resource_path']} no-op encode is not byte-identical"
                    )
            if wrap_compressed and int(resource["is_compressed"]):
                encoded = wrap_pmcq(encoded, extra_sz=int(resource["extra_sz"]))
        except (LocalizationValidationError, ValueError):
            failed += 1
            skipped += 1
            continue

        write_packaged_resource(output_root, str(resource["resource_path"]), encoded)
        written += 1
        entries_written += len(staged)
        if int(resource["is_compressed"]):
            compressed_written += 1
        else:
            direct_written += 1

    return PackSummary(
        output_dir=str(output_root),
        resources_written=written,
        resources_skipped=skipped,
        entries_written=entries_written,
        compressed_resources=compressed_written,
        direct_resources=direct_written,
        failed_resources=failed,
        overlay_resources=written,
    )


def table_with_texts(table: LocalizationTable, texts: list[str]) -> LocalizationTable:
    """Returns a copy of ``table`` whose entry texts are replaced in order."""
    if len(texts) != len(table.entries):
        raise ValueError("replacement text count does not match localization entries")
    return replace(
        table,
        entries=[
            LocalizationEntry(
                key_hash=entry.key_hash,
                text=text,
                key_string=entry.key_string,
            )
            for entry, text in zip(table.entries, texts)
        ],
    )
