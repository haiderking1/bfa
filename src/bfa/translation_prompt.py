"""Shared translation system prompt for every provider."""

from __future__ import annotations

import json
from typing import Sequence

from bfa.models import PendingString


def build_translation_system_prompt(target_language: str, brief: str = "") -> str:
    """Builds the provider system prompt, optionally with a game-specific brief."""
    parts = [
        f"You translate video game UI and subtitles into {target_language}.",
        "Return only valid JSON in this exact shape:",
        '{"translations":[{"id":123,"text":"translated text"}]}',
        "",
        "Translate every item exactly once and preserve every id. Preserve placeholders,",
        "variables, markup tags, escape sequences, line breaks, controller buttons,",
        "format specifiers, and capitalization conventions unless the target language",
        "requires a change. Do not translate JSON keys, identifiers, or placeholder names.",
        "",
        f"For {target_language} game localization, preserve the original emotional force",
        "and slang intensity. Do not sanitize profanity, insults, anger, or panic into a",
        "polite expression. Translate the meaning and tone naturally for a gamer.",
        'For example, "Dammit!" or "Damn it!" should be rendered as "اللعنة!" or',
        '"تباً!", not "يا إلهي!". Keep short exclamations short and forceful.',
        "Use these exact natural equivalents when the English source exactly matches:",
        '"Shit!" -> "تباً!", "Screw you!" -> "تباً لك!", "What the hell?" ->',
        '"ما هذا بحق الجحيم؟", "Get the hell out of here!" -> "اخرج من هنا فوراً!",',
        '"You son of a bitch!" -> "يا ابن الكلب!", and "No way!" -> "مستحيل!".',
        'Never translate "shit" as a word meaning skill, goodness, or cleverness.',
        "Use Modern Standard Arabic with natural spoken dialogue phrasing, and keep",
        "recurring names and terminology consistent across entries.",
    ]
    stripped_brief = brief.strip()
    if stripped_brief:
        parts.extend(["", stripped_brief])
    parts.extend(["", "Do not add explanations or markdown outside the JSON object."])
    return "\n".join(parts)


def build_translation_messages(
    batch: Sequence[PendingString],
    target_language: str,
    brief: str = "",
) -> list[dict[str, str]]:
    """OpenAI-style chat messages for one translation batch."""
    items = [{"id": item.id, "text": item.source_text} for item in batch]
    return [
        {
            "role": "system",
            "content": build_translation_system_prompt(target_language, brief),
        },
        {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
    ]
