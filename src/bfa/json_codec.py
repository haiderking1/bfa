from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator, Mapping, TypeAlias


JsonPathPart: TypeAlias = str | int
JsonPath: TypeAlias = tuple[JsonPathPart, ...]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_strings(value: Any, path: JsonPath = ()) -> Iterator[tuple[JsonPath, str]]:
    """Yield non-empty string values; object keys are structural and are not translated."""
    if isinstance(value, str):
        if value:
            yield path, value
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from extract_strings(item, path + (index,))
        return

    if isinstance(value, dict):
        for key, item in value.items():
            yield from extract_strings(item, path + (key,))


def encode_path(path: JsonPath) -> str:
    return json.dumps(path, ensure_ascii=False, separators=(",", ":"))


def decode_path(value: str) -> JsonPath:
    decoded = json.loads(value)
    if not isinstance(decoded, list):
        raise ValueError("stored JSON path must be a list")
    return tuple(decoded)


def apply_translations(
    value: Any,
    translations: Mapping[JsonPath, str],
    path: JsonPath = (),
) -> Any:
    """Return a translated copy while preserving all non-string JSON values."""
    if isinstance(value, str):
        return translations.get(path, value)
    if isinstance(value, list):
        return [
            apply_translations(item, translations, path + (index,))
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        return {
            key: apply_translations(item, translations, path + (key,))
            for key, item in value.items()
        }
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)
