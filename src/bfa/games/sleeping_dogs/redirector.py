"""Isolated overlay paths and stock-exe install via UI archive patching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bfa.games.sleeping_dogs.archive_patch import (
    apply_ui_replacements,
    remove_incompatible_plugins,
)

REDIRECTOR_DIR = "RedirectorData"


@dataclass(frozen=True, slots=True)
class OverlayInstallSummary:
    game_path: str
    files_installed: int
    removed_plugin_files: list[str]


def resource_output_path(output_root: Path, resource_path: str) -> Path:
    """Maps an internal game path onto an isolated output directory."""
    parts = [part for part in resource_path.replace("/", "\\").split("\\") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise ValueError(f"refusing to write unsafe resource path: {resource_path}")
    return Path(output_root).joinpath(*parts)


def redirector_relative_parts(resource_path: str) -> list[str]:
    """Strips the leading Data\\ prefix used by FileRedirector layouts."""
    parts = [part for part in resource_path.replace("/", "\\").split("\\") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise ValueError(f"refusing unsafe resource path: {resource_path}")
    if parts[0].lower() == "data":
        parts = parts[1:]
    if not parts:
        raise ValueError(f"resource path has no overlay tail: {resource_path}")
    return parts


def redirector_output_path(output_root: Path, resource_path: str) -> Path:
    """Maps an internal game path onto an isolated RedirectorData tree."""
    return Path(output_root).joinpath(REDIRECTOR_DIR, *redirector_relative_parts(resource_path))


def write_packaged_resource(output_root: Path, resource_path: str, data: bytes) -> tuple[Path, Path]:
    """Writes a resource under both Data\\ and RedirectorData\\."""
    data_path = resource_output_path(Path(output_root), resource_path)
    redirector_path = redirector_output_path(output_root, resource_path)
    for destination in (data_path, redirector_path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return data_path, redirector_path


def packaged_replacements(output_root: Path) -> dict[str, bytes]:
    """Reads isolated Data\\ resources as qSymbol paths."""
    data_root = Path(output_root) / "Data"
    replacements: dict[str, bytes] = {}
    if not data_root.is_dir():
        return replacements
    for path in sorted(item for item in data_root.rglob("*") if item.is_file()):
        relative = path.relative_to(output_root)
        if any(part in {".", ".."} for part in relative.parts):
            raise ValueError(f"refusing unsafe packaged path: {path}")
        resource_path = "\\".join(relative.parts)
        replacements[resource_path] = path.read_bytes()
    return replacements


def install_game_overlay(output_root: Path, game_path: Path) -> OverlayInstallSummary:
    """Installs loc + font by patching UI.big/UI.bix from a backup.

    Removes the incompatible FileRedirector loader if it is still present.
    Never writes dinput8.dll or launch-option overrides.
    """
    game_root = Path(game_path)
    if not game_root.is_dir():
        raise FileNotFoundError(f"Game installation directory not found: {game_root}")
    removed = remove_incompatible_plugins(game_root)
    replacements = packaged_replacements(output_root)
    installed = apply_ui_replacements(game_root, replacements)
    return OverlayInstallSummary(
        game_path=str(game_root),
        files_installed=installed,
        removed_plugin_files=removed,
    )


def iter_redirector_files(output_root: Path) -> Iterable[Path]:
    """Yields files under the isolated RedirectorData tree."""
    root = Path(output_root) / REDIRECTOR_DIR
    if not root.is_dir():
        return ()
    return (path for path in root.rglob("*") if path.is_file())
