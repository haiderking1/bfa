"""Shared translation prompt and Sleeping Dogs game brief."""

from __future__ import annotations

import json
import unittest

from bfa.config import Settings
from bfa.games.sleeping_dogs.prompt import (
    SLEEPING_DOGS_TRANSLATION_BRIEF,
    apply_sleeping_dogs_brief,
)
from bfa.models import PendingString
from bfa.translation_prompt import (
    build_translation_messages,
    build_translation_system_prompt,
)


def _settings(**overrides: object) -> Settings:
    values = {
        "api_key": "test-key",
        "base_url": "http://127.0.0.1",
        "model": "test-model",
        "thinking": "disabled",
        "target_language": "Arabic",
        "workers": 8,
        "batch_size": 10,
        "request_retries": 0,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


class TranslationPromptTests(unittest.TestCase):
    def test_generic_prompt_does_not_name_sleeping_dogs(self) -> None:
        prompt = build_translation_system_prompt("Arabic")
        self.assertIn("Arabic", prompt)
        self.assertIn("تباً!", prompt)
        self.assertNotIn("Sleeping Dogs", prompt)
        self.assertNotIn("خزنة", prompt)

    def test_brief_is_appended_and_locks_game_terms(self) -> None:
        prompt = build_translation_system_prompt("Arabic", SLEEPING_DOGS_TRANSLATION_BRIEF)
        self.assertIn("Sleeping Dogs: Definitive Edition", prompt)
        self.assertIn("وي شين", prompt)
        self.assertIn("وينستون", prompt)
        self.assertIn("دوج آيز", prompt)
        self.assertIn("القفز فوق الحاجز", prompt)
        self.assertIn("خزنة", prompt)
        self.assertIn("حشرة", prompt)
        self.assertIn("masculine", prompt)
        self.assertIn("as shit", prompt)

    def test_messages_include_brief_and_batch_ids(self) -> None:
        messages = build_translation_messages(
            [PendingString(9, "Vault Attack")],
            "Arabic",
            SLEEPING_DOGS_TRANSLATION_BRIEF,
        )
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Sleeping Dogs: Definitive Edition", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(
            json.loads(messages[1]["content"]),
            [{"id": 9, "text": "Vault Attack"}],
        )

    def test_sleeping_dogs_brief_is_applied_once(self) -> None:
        attached = apply_sleeping_dogs_brief(_settings())
        self.assertIn("Sleeping Dogs: Definitive Edition", attached.translation_brief)
        custom = apply_sleeping_dogs_brief(_settings(translation_brief="custom brief"))
        self.assertEqual(custom.translation_brief, "custom brief")


if __name__ == "__main__":
    unittest.main()
