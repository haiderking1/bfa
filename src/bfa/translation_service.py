from __future__ import annotations

from typing import Callable

from bfa.translation_engine import BatchOutcome, run_translation
from providers.factory import create_translation_provider

from .config import Settings
from sqlite.repository import TranslationDatabase
from .models import PendingString, TranslationSummary


async def translate_pending(
    database: TranslationDatabase,
    settings: Settings,
    on_progress: Callable[[int, int], None] | None = None,
) -> TranslationSummary:
    pending = database.pending_strings(settings.target_language)
    if not pending:
        return TranslationSummary(total=0, completed=0, failed=0, batches=0)
    if settings.provider == "opencode":
        settings.require_api_key()
    provider = create_translation_provider(settings)

    def handle_result(outcome: BatchOutcome) -> tuple[int, int]:
        if outcome.error is not None:
            database.save_failure(
                [item.id for item in outcome.batch],
                settings.target_language,
                outcome.error,
            )
            return 0, len(outcome.batch)
        assert outcome.translations is not None
        database.save_translations(
            outcome.translations,
            settings.target_language,
        )
        return len(outcome.translations), 0

    try:
        result = await run_translation(
            pending,
            settings,
            provider,
            handle_result,
            on_progress=on_progress,
        )
    finally:
        await provider.close()

    return TranslationSummary(
        total=result.total,
        completed=result.completed,
        failed=result.failed,
        batches=result.batches,
    )
