"""Worker scaling and leftover-queue behavior for the translation engine."""

from __future__ import annotations

import asyncio
import unittest

from bfa.config import Settings
from bfa.models import PendingString
from bfa.translation_engine import (
    SMALL_JOB_MAX_WORKERS,
    SMALL_JOB_PENDING_THRESHOLD,
    BatchOutcome,
    build_chunks,
    run_translation,
    scale_translation_workers,
)


def _settings(**overrides: object) -> Settings:
    values = {
        "api_key": "test-key",
        "base_url": "http://127.0.0.1",
        "model": "test-model",
        "thinking": "disabled",
        "target_language": "Arabic",
        "workers": 100,
        "batch_size": 20,
        "request_retries": 0,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


class _ConcurrencyProbe:
    def __init__(self) -> None:
        self.current = 0
        self.peak = 0
        self.calls = 0
        self._lock = asyncio.Lock()

    async def translate_batch(self, batch, target_language: str) -> dict[int, str]:
        async with self._lock:
            self.calls += 1
            self.current += 1
            self.peak = max(self.peak, self.current)
        await asyncio.sleep(0.05)
        async with self._lock:
            self.current -= 1
        return {item.id: f"AR:{item.source_text}" for item in batch}


class TranslationEngineTests(unittest.TestCase):
    def test_scale_workers_caps_tiny_leftover_queue(self) -> None:
        chunks = build_chunks(
            [PendingString(id=index, source_text=f"line {index}") for index in range(209)],
            batch_size=20,
        )
        self.assertEqual(len(chunks), 11)
        self.assertEqual(
            scale_translation_workers(100, pending_count=209, chunk_count=len(chunks)),
            SMALL_JOB_MAX_WORKERS,
        )

    def test_scale_workers_keeps_full_concurrency_on_large_queue(self) -> None:
        self.assertGreater(17388, SMALL_JOB_PENDING_THRESHOLD)
        self.assertEqual(
            scale_translation_workers(100, pending_count=17388, chunk_count=870),
            100,
        )

    def test_scale_workers_never_exceeds_chunks_or_pending(self) -> None:
        self.assertEqual(scale_translation_workers(100, pending_count=5, chunk_count=5), 5)
        self.assertEqual(scale_translation_workers(100, pending_count=3, chunk_count=1), 1)
        self.assertEqual(scale_translation_workers(8, pending_count=209, chunk_count=11), 8)

    def test_leftover_run_does_not_stampede_configured_workers(self) -> None:
        pending = [PendingString(id=index, source_text=f"line {index}") for index in range(209)]
        provider = _ConcurrencyProbe()

        def handle_result(outcome: BatchOutcome) -> tuple[int, int]:
            assert outcome.translations is not None
            return len(outcome.translations), 0

        result = asyncio.run(
            run_translation(pending, _settings(workers=100, batch_size=20), provider, handle_result)
        )
        self.assertEqual(result.total, 209)
        self.assertEqual(result.completed, 209)
        self.assertEqual(result.failed, 0)
        self.assertLessEqual(provider.peak, SMALL_JOB_MAX_WORKERS)
        self.assertGreater(provider.peak, 1)

    def test_failed_batch_of_twenty_is_split_and_retried(self) -> None:
        pending = [PendingString(id=index, source_text=f"line {index}") for index in range(20)]
        provider = _FailWhenBatchLargerThan(1)
        completed: dict[int, str] = {}
        failed_ids: list[int] = []

        def handle_result(outcome: BatchOutcome) -> tuple[int, int]:
            if outcome.error is not None:
                failed_ids.extend(item.id for item in outcome.batch)
                return 0, len(outcome.batch)
            assert outcome.translations is not None
            completed.update(outcome.translations)
            return len(outcome.translations), 0

        result = asyncio.run(
            run_translation(
                pending,
                _settings(workers=4, batch_size=20, request_retries=0),
                provider,
                handle_result,
            )
        )
        self.assertEqual(result.total, 20)
        self.assertEqual(result.completed, 20)
        self.assertEqual(result.failed, 0)
        self.assertEqual(failed_ids, [])
        self.assertEqual(set(completed), set(range(20)))
        self.assertIn(20, provider.sizes)
        self.assertTrue(all(size >= 1 for size in provider.sizes))
        self.assertGreater(provider.sizes.count(1), 0)

    def test_single_item_failure_is_not_split(self) -> None:
        pending = [PendingString(id=1, source_text="broken")]
        provider = _FailWhenBatchLargerThan(0)

        def handle_result(outcome: BatchOutcome) -> tuple[int, int]:
            self.assertIsNotNone(outcome.error)
            return 0, 1

        result = asyncio.run(
            run_translation(pending, _settings(workers=2, batch_size=20), provider, handle_result)
        )
        self.assertEqual(result.completed, 0)
        self.assertEqual(result.failed, 1)
        self.assertEqual(provider.sizes, [1])


class _FailWhenBatchLargerThan:
    def __init__(self, max_ok: int) -> None:
        self.max_ok = max_ok
        self.sizes: list[int] = []

    async def translate_batch(self, batch, target_language: str) -> dict[int, str]:
        self.sizes.append(len(batch))
        if len(batch) > self.max_ok:
            raise ValueError("model response was not valid JSON")
        return {item.id: f"AR:{item.source_text}" for item in batch}


if __name__ == "__main__":
    unittest.main()
