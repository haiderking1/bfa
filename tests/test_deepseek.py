from __future__ import annotations

import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import httpx
from openai import APIStatusError, RateLimitError

from bfa.config import Settings
from bfa.models import PendingString
from providers.deepseek import DeepSeekProvider
from providers.factory import create_translation_provider
from providers.opencode import ProviderError, RateLimitProviderError


def _settings(**overrides: object) -> Settings:
    values = {
        "api_key": "",
        "base_url": "",
        "model": "",
        "thinking": "disabled",
        "target_language": "Arabic",
        "workers": 8,
        "batch_size": 20,
        "request_retries": 0,
        "provider": "deepseek",
        "deepseek_api_key": "sk-test",
        "deepseek_base_url": "https://api.deepseek.com",
        "deepseek_model": "deepseek-v4-flash",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def _http_error(status: int, message: str, cls=APIStatusError):
    request = httpx.Request("POST", "https://api.deepseek.com/chat/completions")
    response = httpx.Response(status, request=request)
    return cls(message, response=response, body={"error": {"message": message}})


class _FakeCompletions:
    def __init__(self, result=None, error: Exception | None = None):
        self.calls: list[dict[str, object]] = []
        self.result = result
        self.error = error

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.result


class _FakeClient:
    def __init__(self, completions: _FakeCompletions):
        self.chat = SimpleNamespace(completions=completions)
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def _json_response(payload: dict[str, object]) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(payload, ensure_ascii=False),
                )
            )
        ]
    )


class DeepSeekProviderTests(unittest.TestCase):
    def test_empty_key_is_rejected_before_any_request(self) -> None:
        with self.assertRaisesRegex(ValueError, "DEEPSEEK_API_KEY"):
            DeepSeekProvider(_settings(deepseek_api_key=""))

    def test_flash_batch_sends_thinking_disabled_and_json_mode(self) -> None:
        completions = _FakeCompletions(
            result=_json_response(
                {
                    "translations": [
                        {"id": 11, "text": "اللعنة!"},
                        {
                            "id": 12,
                            "text": (
                                "<font color='#e1e1e1'>اضغط "
                                "<img  src='BUTTON_ACCEPT' height='52' "
                                "width='52' vspace='-26'> للقفز</font>"
                            ),
                        },
                    ]
                }
            )
        )
        provider = DeepSeekProvider(_settings(), client=_FakeClient(completions))
        result = asyncio.run(
            provider.translate_batch(
                [
                    PendingString(11, "Dammit!"),
                    PendingString(
                        12,
                        (
                            "<font color='#e1e1e1'>Press "
                            "<img  src='BUTTON_ACCEPT' height='52' "
                            "width='52' vspace='-26'> to Vault</font>"
                        ),
                    ),
                ],
                "Arabic",
            )
        )

        self.assertEqual(result[11], "اللعنة!")
        self.assertIn("BUTTON_ACCEPT", result[12])
        self.assertEqual(len(completions.calls), 1)
        call = completions.calls[0]
        self.assertEqual(call["model"], "deepseek-v4-flash")
        self.assertEqual(call["response_format"], {"type": "json_object"})
        self.assertEqual(call["extra_body"], {"thinking": {"type": "disabled"}})
        messages = call["messages"]
        assert isinstance(messages, list)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Arabic", messages[0]["content"])
        self.assertNotIn("Sleeping Dogs", messages[0]["content"])

    def test_sleeping_dogs_brief_is_sent_in_system_prompt(self) -> None:
        completions = _FakeCompletions(
            result=_json_response({"translations": [{"id": 1, "text": "هجوم القفز"}]})
        )
        provider = DeepSeekProvider(
            _settings(translation_brief="Sleeping Dogs: Definitive Edition. vault != خزنة"),
            client=_FakeClient(completions),
        )
        asyncio.run(provider.translate_batch([PendingString(1, "Vault Attack")], "Arabic"))
        messages = completions.calls[0]["messages"]
        assert isinstance(messages, list)
        self.assertIn("Sleeping Dogs: Definitive Edition", messages[0]["content"])
        self.assertIn("خزنة", messages[0]["content"])

    def test_rate_limit_becomes_shared_throttle_error(self) -> None:
        completions = _FakeCompletions(
            error=_http_error(429, "too many requests", cls=RateLimitError)
        )
        provider = DeepSeekProvider(_settings(), client=_FakeClient(completions))
        with self.assertRaises(RateLimitProviderError) as caught:
            asyncio.run(
                provider.translate_batch([PendingString(1, "Hello")], "Arabic")
            )
        self.assertTrue(caught.exception.rate_limited)

    def test_empty_balance_is_a_hard_provider_error(self) -> None:
        completions = _FakeCompletions(
            error=_http_error(402, "Insufficient Balance")
        )
        provider = DeepSeekProvider(_settings(), client=_FakeClient(completions))
        with self.assertRaisesRegex(ProviderError, "balance is empty"):
            asyncio.run(
                provider.translate_batch([PendingString(1, "Hello")], "Arabic")
            )

    def test_empty_model_content_is_rejected(self) -> None:
        completions = _FakeCompletions(
            result=SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=""))]
            )
        )
        provider = DeepSeekProvider(_settings(), client=_FakeClient(completions))
        with self.assertRaisesRegex(ProviderError, "empty response"):
            asyncio.run(
                provider.translate_batch([PendingString(1, "Hello")], "Arabic")
            )

    def test_factory_builds_deepseek_provider(self) -> None:
        provider = create_translation_provider(_settings())
        try:
            self.assertIsInstance(provider, DeepSeekProvider)
        finally:
            asyncio.run(provider.close())

    def test_environment_loads_deepseek_flash_profile(self) -> None:
        watched = (
            "BFA_PROVIDER",
            "DEEPSEEK_API_KEY",
            "DEEPSEEK_MODEL",
            "DEEPSEEK_BASE_URL",
            "BFA_WORKERS",
            "BFA_BATCH_SIZE",
        )
        previous = {name: os.environ.pop(name, None) for name in watched}
        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                env_path = Path(temporary_directory) / ".env"
                env_path.write_text(
                    "\n".join(
                        [
                            "BFA_PROVIDER=deepseek",
                            "DEEPSEEK_API_KEY=sk-live-test",
                            "DEEPSEEK_MODEL=deepseek-v4-flash",
                            "DEEPSEEK_BASE_URL=https://api.deepseek.com/",
                            "BFA_WORKERS=8",
                            "BFA_BATCH_SIZE=20",
                        ]
                    )
                    + "\n",
                    encoding="utf-8",
                )
                settings = Settings.from_environment(env_path)
                self.assertEqual(settings.provider, "deepseek")
                self.assertEqual(settings.deepseek_api_key, "sk-live-test")
                self.assertEqual(settings.deepseek_model, "deepseek-v4-flash")
                self.assertEqual(settings.deepseek_base_url, "https://api.deepseek.com")
                self.assertEqual(settings.workers, 8)
                self.assertEqual(settings.batch_size, 20)
        finally:
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
