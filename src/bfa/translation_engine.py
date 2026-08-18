"""Bounded, character-aware translation batching with retries and throttling.

The engine follows Raven's proven translation behavior: batches are limited by
both item count and request characters, workers pull from a bounded queue, and
rate-limit cooldowns are shared by every worker.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Callable, Protocol, Sequence

from bfa.config import Settings
from bfa.models import PendingString

MAX_CHUNK_CHARACTERS = 4000
SMALL_JOB_PENDING_THRESHOLD = 256
SMALL_JOB_MAX_WORKERS = 8


def scale_translation_workers(
    configured_workers: int,
    pending_count: int,
    chunk_count: int,
) -> int:
    """Cap concurrency to actual leftover work so a tiny queue cannot stampede."""
    if configured_workers < 1:
        raise ValueError("workers must be at least 1")
    if pending_count < 1 or chunk_count < 1:
        return 1
    workers = min(configured_workers, chunk_count, pending_count)
    if pending_count <= SMALL_JOB_PENDING_THRESHOLD:
        workers = min(workers, SMALL_JOB_MAX_WORKERS)
    return max(1, workers)


class BatchTranslationProvider(Protocol):
    async def translate_batch(
        self,
        batch: Sequence[PendingString],
        target_language: str,
    ) -> dict[int, str]:
        ...


@dataclass(frozen=True, slots=True)
class BatchOutcome:
    batch: list[PendingString]
    translations: dict[int, str] | None
    error: str | None
    attempts: int


@dataclass(frozen=True, slots=True)
class TranslationRun:
    total: int
    completed: int
    failed: int
    batches: int


class DispatchThrottle:
    """Shared cooldown used to prevent every worker retrying at once."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._pause_until = 0.0

    async def wait(self) -> None:
        while True:
            async with self._lock:
                remaining = self._pause_until - asyncio.get_running_loop().time()
            if remaining <= 0:
                return
            await asyncio.sleep(remaining)

    async def pause(self, duration: float) -> None:
        if duration <= 0:
            return
        async with self._lock:
            until = asyncio.get_running_loop().time() + duration
            self._pause_until = max(self._pause_until, until)


def build_chunks(
    strings: Sequence[PendingString],
    batch_size: int,
    max_characters: int = MAX_CHUNK_CHARACTERS,
) -> list[list[PendingString]]:
    """Split pending strings by item count and UTF-8 request character budget."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if max_characters < 1:
        raise ValueError("max_characters must be at least 1")

    chunks: list[list[PendingString]] = []
    current: list[PendingString] = []
    current_characters = 0

    def flush() -> None:
        nonlocal current, current_characters
        if current:
            chunks.append(current)
            current = []
            current_characters = 0

    for item in strings:
        item_characters = len(item.source_text)
        if current and (
            len(current) >= batch_size
            or current_characters + item_characters > max_characters
        ):
            flush()

        current.append(item)
        current_characters += item_characters

        # A single long line remains intact, but prevents the next line joining it.
        if len(current) >= batch_size or current_characters >= max_characters:
            flush()

    flush()
    return chunks


def _is_rate_limited(error: Exception) -> bool:
    return bool(getattr(error, "rate_limited", False))


def _error_retry_after(error: Exception) -> float | None:
    value = getattr(error, "retry_after", None)
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def _backoff(attempt: int, base: float = 1.0, maximum: float = 30.0) -> float:
    base_seconds = min(maximum, base * (2 ** min(attempt - 1, 30)))
    return min(maximum, base_seconds + base_seconds * 0.25 * random.random())


async def _translate_with_retry(
    provider: BatchTranslationProvider,
    batch: list[PendingString],
    target_language: str,
    settings: Settings,
    throttle: DispatchThrottle,
    max_attempts: int | None = None,
) -> BatchOutcome:
    if max_attempts is None:
        max_attempts = settings.max_attempts or settings.request_retries + 1
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        await throttle.wait()
        try:
            translations = await provider.translate_batch(batch, target_language)
            expected_ids = {item.id for item in batch}
            if set(translations) != expected_ids:
                missing = sorted(expected_ids - set(translations))
                extra = sorted(set(translations) - expected_ids)
                raise ValueError(
                    f"translation IDs do not match; missing={missing}, extra={extra}"
                )
            return BatchOutcome(batch, translations, None, attempt)
        except Exception as exc:
            last_error = exc
            retry_after = _error_retry_after(exc)
            if _is_rate_limited(exc):
                await throttle.pause(
                    min(retry_after, settings.burst_pause_seconds)
                    if retry_after is not None and retry_after > 0
                    else settings.burst_pause_seconds
                )
            if attempt == max_attempts:
                break
            delay = retry_after if retry_after is not None else _backoff(attempt)
            await asyncio.sleep(delay)

    message = str(last_error) if last_error is not None else "translation failed"
    return BatchOutcome(batch, None, message, max_attempts)


def _split_failed_batch(
    batch: list[PendingString],
) -> tuple[list[PendingString], list[PendingString]]:
    mid = max(1, len(batch) // 2)
    return batch[:mid], batch[mid:]


async def run_translation(
    pending: Sequence[PendingString],
    settings: Settings,
    provider: BatchTranslationProvider,
    on_result: Callable[[BatchOutcome], tuple[int, int]],
    on_progress: Callable[[int, int], None] | None = None,
) -> TranslationRun:
    """Translate all pending items and persist each completed batch via callback.

    A failed multi-item batch is split and retried so one bad JSON response
    cannot park an entire chunk of 20 strings.
    """
    if not pending:
        return TranslationRun(total=0, completed=0, failed=0, batches=0)

    chunks = build_chunks(
        pending,
        settings.batch_size,
        settings.max_chunk_characters,
    )
    worker_count = scale_translation_workers(
        settings.workers,
        pending_count=len(pending),
        chunk_count=len(chunks),
    )
    queue: asyncio.Queue[list[PendingString] | None] = asyncio.Queue()
    for chunk in chunks:
        await queue.put(chunk)

    throttle = DispatchThrottle()
    completed_items = 0
    completed_translations = 0
    failed_translations = 0
    batches_run = 0
    progress_lock = asyncio.Lock()

    async def worker() -> None:
        nonlocal completed_items, completed_translations, failed_translations, batches_run
        while True:
            batch = await queue.get()
            try:
                if batch is None:
                    return
                outcome = await _translate_with_retry(
                    provider,
                    batch,
                    settings.target_language,
                    settings,
                    throttle,
                    max_attempts=1 if len(batch) > 1 else None,
                )
                async with progress_lock:
                    batches_run += 1
                if outcome.error is not None and len(batch) > 1:
                    left, right = _split_failed_batch(batch)
                    await queue.put(left)
                    await queue.put(right)
                    continue
                batch_completed, batch_failed = on_result(outcome)
                async with progress_lock:
                    completed_items += len(batch)
                    completed_translations += batch_completed
                    failed_translations += batch_failed
                    if on_progress is not None:
                        on_progress(completed_items, len(pending))
            finally:
                queue.task_done()

    workers = [asyncio.create_task(worker()) for _ in range(worker_count)]
    try:
        await queue.join()
        for _ in range(worker_count):
            await queue.put(None)
        await asyncio.gather(*workers)
    except BaseException:
        for task in workers:
            task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        raise

    return TranslationRun(
        total=len(pending),
        completed=completed_translations,
        failed=failed_translations,
        batches=batches_run,
    )
