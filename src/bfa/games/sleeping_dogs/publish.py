"""Pack translations, inject BFA, and install by patching the stock UI archives."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from bfa.fonts.asset import BFA_FONT_PATH
from bfa.games.sleeping_dogs.font_inject import FontInjectSummary, inject_sleeping_dogs_font
from bfa.games.sleeping_dogs.models import PackSummary
from bfa.games.sleeping_dogs.pack import build_translated_resources
from bfa.games.sleeping_dogs.redirector import OverlayInstallSummary, install_game_overlay
from bfa.games.sleeping_dogs.repository import SleepingDogsDatabase


@dataclass(frozen=True, slots=True)
class PublishSummary:
    pack: PackSummary
    font: FontInjectSummary | None
    install: OverlayInstallSummary | None


def publish_sleeping_dogs(
    database: SleepingDogsDatabase,
    output_dir: Path,
    *,
    game_path: Union[str, Path] | None = None,
    font_path: Path | None = None,
    wrap_compressed: bool = False,
    inject_font: bool = True,
    install: bool = True,
) -> PublishSummary:
    """Writes loc + BFA, then patches UI.big/UI.bix from a one-time backup.

    The game executable is never written. No ASI loader or Proton override is used.
    """
    packed = build_translated_resources(
        database,
        output_dir,
        wrap_compressed=wrap_compressed,
    )
    font_summary = None
    if inject_font:
        if game_path is None:
            raise ValueError("game_path is required to inject the BFA font")
        font_summary = inject_sleeping_dogs_font(
            game_path,
            output_dir,
            font_path=font_path or BFA_FONT_PATH,
        )
    install_summary = None
    if install:
        if game_path is None:
            raise ValueError("game_path is required to install the overlay")
        install_summary = install_game_overlay(output_dir, Path(game_path))
    return PublishSummary(pack=packed, font=font_summary, install=install_summary)
