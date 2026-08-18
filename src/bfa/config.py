from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """Raised when the local BFA configuration is invalid."""


def load_env_file(path: Path | None = None) -> None:
    """Load simple KEY=VALUE entries without overriding shell environment values."""
    env_path = path or Path.cwd() / ".env"
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        if not separator or not key.strip():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a positive integer") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    thinking: str
    target_language: str
    workers: int
    batch_size: int
    request_retries: int
    max_attempts: int | None = None
    max_chunk_characters: int = 4000
    burst_pause_seconds: float = 10.0
    provider: str = "opencode"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma4:e2b"
    ollama_timeout_seconds: float = 300.0
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "nvidia/nemotron-3.5-lightning:free"
    openrouter_timeout_seconds: float = 300.0
    kilo_api_key: str = ""
    kilo_base_url: str = "https://api.kilo.ai/api/gateway"
    kilo_model: str = "tencent/hy3:free"
    kilo_timeout_seconds: float = 300.0
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_seconds: float = 300.0
    translation_brief: str = ""

    @classmethod
    def from_environment(cls, dotenv_path: Path | None = None) -> Settings:
        load_env_file(dotenv_path)
        thinking = os.getenv("OPENCODE_THINKING", "disabled").strip().lower()
        if thinking not in {"enabled", "disabled"}:
            raise ConfigurationError("OPENCODE_THINKING must be 'enabled' or 'disabled'")

        return cls(
            api_key=os.getenv("OPENCODE_API_KEY", "").strip(),
            base_url=os.getenv(
                "OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1"
            ).strip(),
            model=os.getenv("OPENCODE_MODEL", "deepseek-v4-flash").strip(),
            thinking=thinking,
            target_language=os.getenv("BFA_TARGET_LANGUAGE", "Arabic").strip(),
            workers=_positive_int("BFA_WORKERS", 100),
            batch_size=_positive_int("BFA_BATCH_SIZE", 50),
            request_retries=_positive_int("BFA_REQUEST_RETRIES", 3),
            max_attempts=_positive_int("BFA_MAX_ATTEMPTS", 3),
            max_chunk_characters=_positive_int("BFA_MAX_CHUNK_CHARACTERS", 4000),
            burst_pause_seconds=float(os.getenv("BFA_BURST_PAUSE_SECONDS", "10")),
            provider=os.getenv("BFA_PROVIDER", "opencode").strip().lower(),
            ollama_base_url=os.getenv(
                "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
            ).strip().rstrip("/"),
            ollama_model=os.getenv("OLLAMA_MODEL", "gemma4:e2b").strip(),
            ollama_timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300")),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ).strip().rstrip("/"),
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free"
            ).strip(),
            openrouter_timeout_seconds=float(
                os.getenv("OPENROUTER_TIMEOUT_SECONDS", "300")
            ),
            kilo_api_key=os.getenv("KILO_API_KEY", "").strip(),
            kilo_base_url=os.getenv(
                "KILO_BASE_URL", "https://api.kilo.ai/api/gateway"
            ).strip().rstrip("/"),
            kilo_model=os.getenv("KILO_MODEL", "tencent/hy3:free").strip(),
            kilo_timeout_seconds=float(os.getenv("KILO_TIMEOUT_SECONDS", "300")),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
            deepseek_base_url=os.getenv(
                "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
            ).strip().rstrip("/"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip(),
            deepseek_timeout_seconds=float(
                os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "300")
            ),
        )

    def require_api_key(self) -> None:
        if not self.api_key:
            raise ConfigurationError(
                "OPENCODE_API_KEY is empty; add your key to the ignored .env file"
            )
