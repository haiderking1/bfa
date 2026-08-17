from __future__ import annotations

import asyncio

from providers.opencode import OpenCodeProvider

from .config import Settings
from sqlite.repository import TranslationDatabase
from .models import PendingString, TranslationSummary


def _chunks(items: list[PendingString], size: int) -> list[list[PendingString]]:
    return [items[start : start + size] for start in range(0, len(items), size)]


async def translate_pending(
    database: TranslationDatabase,
    settings: Settings,
) -> TranslationSummary:
    pending = database.pending_strings(settings.target_language)
    if not pending:
        return TranslationSummary(total=0, completed=0, failed=0, batches=0)
    settings.require_api_key()

    batches = _chunks(pending, settings.batch_size)
    semaphore = asyncio.Semaphore(settings.workers)
    provider = OpenCodeProvider(settings)

    async def process(batch: list[PendingString]) -> tuple[int, int]:
        async with semaphore:
            try:
                translations = await provider.translate_batch(
                    batch,
                    settings.target_language,
                )
                database.save_translations(translations, settings.target_language)
                return len(batch), 0
            except Exception as exc:
                database.save_failure(
                    [item.id for item in batch],
                    settings.target_language,
                    str(exc),
                )
                return 0, len(batch)

    try:
        results = await asyncio.gather(*(process(batch) for batch in batches))
    finally:
        await provider.close()

    completed = sum(result[0] for result in results)
    failed = sum(result[1] for result in results)
    return TranslationSummary(
        total=len(pending),
        completed=completed,
        failed=failed,
        batches=len(batches),
    )
