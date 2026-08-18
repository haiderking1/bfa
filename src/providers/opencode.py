from __future__ import annotations

import json
from typing import Any, Sequence

from openai import APIStatusError, AsyncOpenAI, RateLimitError

from bfa.config import Settings
from bfa.models import PendingString
from bfa.translation_prompt import build_translation_messages


class ProviderError(RuntimeError):
    """Raised when the model response cannot be used for translation."""


class RateLimitProviderError(ProviderError):
    """A provider rejection that should trigger shared worker throttling."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.rate_limited = True


def _retry_after(response: object) -> float | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    raw = headers.get("retry-after")
    if raw is None:
        return None
    try:
        seconds = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return seconds if seconds >= 0 else None


def _parse_json_response(content: str) -> Any:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


def _parse_translations(content: str, batch: Sequence[PendingString]) -> dict[int, str]:
    try:
        payload = _parse_json_response(content)
    except json.JSONDecodeError as exc:
        raise ProviderError("model response was not valid JSON") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("translations"), list):
        raise ProviderError("model response must contain a translations array")

    expected_ids = {item.id for item in batch}
    result: dict[int, str] = {}
    for item in payload["translations"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            raise ProviderError("each translation must contain an integer id")
        if not isinstance(item.get("text"), str):
            raise ProviderError("each translation must contain string text")
        item_id = int(item["id"])
        if item_id in result:
            raise ProviderError(f"duplicate translation id returned: {item_id}")
        result[item_id] = item["text"]

    if set(result) != expected_ids:
        missing = sorted(expected_ids - set(result))
        extra = sorted(set(result) - expected_ids)
        raise ProviderError(f"translation IDs do not match; missing={missing}, extra={extra}")
    return result


def _messages(
    batch: Sequence[PendingString],
    target_language: str,
    brief: str = "",
) -> list[dict[str, str]]:
    return build_translation_messages(batch, target_language, brief)


class OpenCodeProvider:
    """OpenAI-compatible OpenCode Go translation provider."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            max_retries=0,
        )

    async def translate_batch(
        self,
        batch: Sequence[PendingString],
        target_language: str,
    ) -> dict[int, str]:
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.model,
                messages=_messages(batch, target_language, self.settings.translation_brief),
                extra_body={"thinking": {"type": self.settings.thinking}},
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
            raise ProviderError("model returned an empty response")
        return _parse_translations(content, batch)

    async def close(self) -> None:
        await self.client.close()
