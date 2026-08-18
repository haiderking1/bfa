"""Official DeepSeek OpenAI-compatible translation provider."""

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


class DeepSeekProvider:
    """Translate through DeepSeek's official chat-completions API.

    Thinking is always disabled. DeepSeek enables it by default, and that
    bills reasoning tokens as output — fatal for a small prepaid balance.
    """

    def __init__(self, settings: Settings, client: AsyncOpenAI | None = None):
        if not settings.deepseek_api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY is empty; top up and create a key at "
                "https://platform.deepseek.com"
            )
        self.settings = settings
        self._owns_client = client is None
        self.client = client or AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            max_retries=0,
            timeout=settings.deepseek_timeout_seconds,
        )

    async def translate_batch(
        self,
        batch: Sequence[PendingString],
        target_language: str,
    ) -> dict[int, str]:
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.deepseek_model,
                messages=_messages(batch, target_language, self.settings.translation_brief),
                response_format={"type": "json_object"},
                extra_body={"thinking": {"type": "disabled"}},
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
            if exc.status_code == 402:
                raise ProviderError(
                    "DeepSeek balance is empty; top up at https://platform.deepseek.com"
                ) from exc
            raise

        content = response.choices[0].message.content
        if not content:
            raise ProviderError("DeepSeek returned an empty response")
        return _parse_translations(content, batch)

    async def close(self) -> None:
        if self._owns_client:
            await self.client.close()
