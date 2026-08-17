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
        )

    def require_api_key(self) -> None:
        if not self.api_key:
            raise ConfigurationError(
                "OPENCODE_API_KEY is empty; add your key to the ignored .env file"
            )
