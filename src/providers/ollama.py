"""Local Ollama translation provider."""

from __future__ import annotations

import json
from typing import Any, Sequence

import httpx

from bfa.config import Settings
from bfa.models import PendingString
from bfa.translation_prompt import build_translation_messages
from providers.opencode import ProviderError


class OllamaProvider:
    """Translate batches through Ollama's native ``/api/chat`` endpoint."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=settings.ollama_base_url,
            timeout=httpx.Timeout(settings.ollama_timeout_seconds),
        )

    async def translate_batch(
        self,
        batch: Sequence[PendingString],
        target_language: str,
    ) -> dict[int, str]:
        response = await self.client.post(
            "/api/chat",
            json={
                "model": self.settings.ollama_model,
                "messages": build_translation_messages(
                    batch,
                    target_language,
                    self.settings.translation_brief,
                ),
                "stream": False,
                "think": False,
                "format": "json",
                "options": {"temperature": 0.2},
            },
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Ollama request failed with HTTP {response.status_code}: "
                f"{response.text[:500]}"
            ) from exc

        try:
            payload = response.json()
            content = payload["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError("Ollama response did not contain message.content") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Ollama returned an empty response")
        return self._parse_translations(content, batch)

    @staticmethod
    def _parse_translations(
        content: str,
        batch: Sequence[PendingString],
    ) -> dict[int, str]:
        try:
            payload: Any = json.loads(content.strip())
        except json.JSONDecodeError as exc:
            raise ProviderError("Ollama response was not valid JSON") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("translations"), list):
            raise ProviderError("Ollama response must contain a translations array")

        expected_ids = {item.id for item in batch}
        result: dict[int, str] = {}
        for item in payload["translations"]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), int):
                raise ProviderError("each Ollama translation must contain an integer id")
            if not isinstance(item.get("text"), str):
                raise ProviderError("each Ollama translation must contain string text")
            item_id = int(item["id"])
            if item_id in result:
                raise ProviderError(f"duplicate Ollama translation id returned: {item_id}")
            result[item_id] = item["text"]

        if set(result) != expected_ids:
            missing = sorted(expected_ids - set(result))
            extra = sorted(set(result) - expected_ids)
            raise ProviderError(
                f"Ollama translation IDs do not match; missing={missing}, extra={extra}"
            )
        return result

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
