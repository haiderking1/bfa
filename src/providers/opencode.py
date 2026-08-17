from __future__ import annotations

import asyncio
import json
from typing import Any, Sequence

from openai import AsyncOpenAI

from bfa.config import Settings
from bfa.models import PendingString


class ProviderError(RuntimeError):
    """Raised when the model response cannot be used for translation."""


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


def _messages(batch: Sequence[PendingString], target_language: str) -> list[dict[str, str]]:
    items = [{"id": item.id, "text": item.source_text} for item in batch]
    system = f"""
You translate video game UI and subtitles into {target_language}.
Return only valid JSON in this exact shape:
{{"translations":[{{"id":123,"text":"translated text"}}]}}

Translate every item exactly once and preserve every id. Preserve placeholders,
variables, markup tags, escape sequences, line breaks, controller buttons,
format specifiers, and capitalization conventions unless the target language
requires a change. Do not translate JSON keys, identifiers, or placeholder names.
Do not add explanations or markdown outside the JSON object.
""".strip()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
    ]


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
        last_error: Exception | None = None
        for attempt in range(self.settings.request_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.settings.model,
                    messages=_messages(batch, target_language),
                    extra_body={"thinking": {"type": self.settings.thinking}},
                )
                content = response.choices[0].message.content
                if not content:
                    raise ProviderError("model returned an empty response")
                return _parse_translations(content, batch)
            except Exception as exc:
                last_error = exc
                if attempt < self.settings.request_retries:
                    await asyncio.sleep(min(2**attempt, 8))

        assert last_error is not None
        raise ProviderError(str(last_error)) from last_error

    async def close(self) -> None:
        await self.client.close()
