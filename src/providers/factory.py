"""Construction of configured translation providers."""

from __future__ import annotations

from typing import Protocol, Sequence

from bfa.config import Settings
from bfa.models import PendingString

from .deepseek import DeepSeekProvider
from .kilo import KiloProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider
from .opencode import OpenCodeProvider


class TranslationProvider(Protocol):
    async def translate_batch(
        self,
        batch: Sequence[PendingString],
        target_language: str,
    ) -> dict[int, str]:
        ...

    async def close(self) -> None:
        ...


def create_translation_provider(settings: Settings) -> TranslationProvider:
    if settings.provider == "ollama":
        return OllamaProvider(settings)
    if settings.provider == "opencode":
        return OpenCodeProvider(settings)
    if settings.provider == "openrouter":
        return OpenRouterProvider(settings)
    if settings.provider == "kilo":
        return KiloProvider(settings)
    if settings.provider == "deepseek":
        return DeepSeekProvider(settings)
    raise ValueError(
        f"unsupported BFA_PROVIDER={settings.provider!r}; "
        "use 'ollama', 'opencode', 'openrouter', 'kilo', or 'deepseek'"
    )
