from __future__ import annotations

import asyncio
import json
import unittest

import httpx

from bfa.config import Settings
from bfa.models import PendingString
from providers.ollama import OllamaProvider


class OllamaProviderTests(unittest.TestCase):
    def test_native_chat_request_and_batch_response(self) -> None:
        seen: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["path"] = request.url.path
            payload = json.loads(request.content)
            seen["payload"] = payload
            return httpx.Response(
                200,
                json={
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "translations": [
                                    {"id": 7, "text": "اللعنة!"},
                                    {"id": 8, "text": "ابدأ اللعبة"},
                                ],
                            },
                            ensure_ascii=False,
                        ),
                    }
                },
            )

        client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="http://ollama.test",
        )
        settings = Settings(
            api_key="",
            base_url="",
            model="",
            thinking="disabled",
            target_language="Arabic",
            workers=1,
            batch_size=10,
            request_retries=0,
            provider="ollama",
            ollama_model="gemma4:e2b",
        )
        provider = OllamaProvider(settings, client=client)
        try:
            result = asyncio.run(
                provider.translate_batch(
                    [
                        PendingString(7, "Dammit!"),
                        PendingString(8, "Start Game"),
                    ],
                    "Arabic",
                )
            )
        finally:
            asyncio.run(client.aclose())

        self.assertEqual(result, {7: "اللعنة!", 8: "ابدأ اللعبة"})
        self.assertEqual(seen["path"], "/api/chat")
        payload = seen["payload"]
        assert isinstance(payload, dict)
        self.assertEqual(payload["model"], "gemma4:e2b")
        self.assertFalse(payload["think"])
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["format"], "json")

    def test_malformed_batch_response_is_rejected(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"message": {"content": '{"translations": []}'}},
            )

        client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="http://ollama.test",
        )
        settings = Settings(
            api_key="",
            base_url="",
            model="",
            thinking="disabled",
            target_language="Arabic",
            workers=1,
            batch_size=10,
            request_retries=0,
            provider="ollama",
        )
        provider = OllamaProvider(settings, client=client)
        try:
            with self.assertRaisesRegex(Exception, "IDs do not match"):
                asyncio.run(
                    provider.translate_batch(
                        [PendingString(1, "Hello")],
                        "Arabic",
                    )
                )
        finally:
            asyncio.run(client.aclose())


if __name__ == "__main__":
    unittest.main()
