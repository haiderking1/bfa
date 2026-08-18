"""OpenCode translation orchestration for Sleeping Dogs localization entries."""

from __future__ import annotations

from typing import Callable, Optional, Protocol, Sequence

from bfa.config import Settings
from bfa.games.sleeping_dogs.prompt import apply_sleeping_dogs_brief
from bfa.games.sleeping_dogs.repair import is_markup_only, repair_translated_text
from bfa.games.sleeping_dogs.repository import SleepingDogsDatabase
from bfa.games.sleeping_dogs.validation import (
    LocalizationValidationError,
    validate_translated_text,
)
from bfa.models import PendingString, TranslationSummary
from bfa.translation_engine import BatchOutcome, run_translation
from providers.factory import create_translation_provider


class TranslationProvider(Protocol):
    async def translate_batch(
        self,
        batch: Sequence[PendingString],
        target_language: str,
    ) -> dict[int, str]:
        ...

    async def close(self) -> None:
        ...


def _split_valid_translations(
    batch: Sequence[PendingString],
    translations: dict[int, str],
) -> tuple[dict[int, str], dict[int, str]]:
    accepted: dict[int, str] = {}
    rejected: dict[int, str] = {}
    by_id = {item.id: item for item in batch}
    for item_id, translated in translations.items():
        source = by_id[item_id].source_text
        candidate = translated
        try:
            validate_translated_text(source, candidate)
        except LocalizationValidationError:
            candidate = repair_translated_text(source, translated)
            try:
                validate_translated_text(source, candidate)
            except LocalizationValidationError as exc:
                rejected[item_id] = str(exc)
                continue
        accepted[item_id] = candidate
    return accepted, rejected


async def translate_pending(
    database: SleepingDogsDatabase,
    settings: Settings,
    provider: Optional[TranslationProvider] = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> TranslationSummary:
    pending = database.pending_strings(settings.target_language)
    if not pending:
        return TranslationSummary(total=0, completed=0, failed=0, batches=0)
    settings = apply_sleeping_dogs_brief(settings)
    if provider is None and settings.provider == "opencode":
        settings.require_api_key()

    markup_only = {
        item.id: item.source_text for item in pending if is_markup_only(item.source_text)
    }
    model_items = [item for item in pending if item.id not in markup_only]
    if markup_only:
        database.save_translations(markup_only, settings.target_language)
        if on_progress is not None:
            on_progress(len(markup_only), len(pending))
    if not model_items:
        return TranslationSummary(
            total=len(pending),
            completed=len(markup_only),
            failed=0,
            batches=0,
        )

    own_provider = provider is None
    active_provider: TranslationProvider = provider or create_translation_provider(settings)

    def handle_result(outcome: BatchOutcome) -> tuple[int, int]:
        if outcome.error is not None:
            database.save_failure(
                [item.id for item in outcome.batch],
                settings.target_language,
                outcome.error,
            )
            return 0, len(outcome.batch)

        assert outcome.translations is not None
        accepted, rejected = _split_valid_translations(
            outcome.batch,
            outcome.translations,
        )
        if accepted:
            database.save_translations(accepted, settings.target_language)
        if rejected:
            for item_id, error in rejected.items():
                database.save_failure(
                    [item_id],
                    settings.target_language,
                    error,
                )
        return len(accepted), len(rejected)

    try:
        def report_progress(done: int, _total: int) -> None:
            if on_progress is not None:
                on_progress(done + len(markup_only), len(pending))

        result = await run_translation(
            model_items,
            settings,
            active_provider,
            handle_result,
            on_progress=report_progress,
        )
    finally:
        if own_provider:
            await active_provider.close()

    return TranslationSummary(
        total=result.total + len(markup_only),
        completed=result.completed + len(markup_only),
        failed=result.failed,
        batches=result.batches,
    )
