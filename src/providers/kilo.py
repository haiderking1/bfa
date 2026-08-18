"""Kilo Gateway OpenAI-compatible translation provider."""

from __future__ import annotations

from typing import Sequence

from openai import APIStatusError, AsyncOpenAI, RateLimitError

from bfa.config import Settings
from bfa.models import PendingString
from providers.opencode import (
    ProviderError,
    RateLimitProviderError,
    _messages,
    _parse_translations,
    _retry_after,
)


class KiloProvider:
    """Translate through Kilo Gateway's OpenAI-compatible endpoint."""

    def __init__(self, settings: Settings):
        if not settings.kilo_api_key:
            raise ValueError("KILO_API_KEY is empty")
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.kilo_api_key,
            base_url=settings.kilo_base_url,
            max_retries=0,
            timeout=settings.kilo_timeout_seconds,
        )

    async def translate_batch(
        self,
        batch: Sequence[PendingString],
        target_language: str,
    ) -> dict[int, str]:
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.kilo_model,
                messages=_messages(batch, target_language, self.settings.translation_brief),
                extra_body={"reasoning_effort": "none"},
            )
        except RateLimitError as exc:
            raise RateLimitProviderError(
                str(exc),
                _retry_after(exc.response),
            ) from exc
        except APIStatusError as exc:
            if exc.status_code == 429:
                raise RateLimitProviderError(
                    str(exc),
                    _retry_after(exc.response),
                ) from exc
            raise

        content = response.choices[0].message.content
        if not content:
            raise ProviderError("Kilo returned an empty response")
        return _parse_translations(content, batch)

    async def close(self) -> None:
        await self.client.close()
