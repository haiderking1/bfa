"""Locate and load the shared BFA typeface."""

from __future__ import annotations

from pathlib import Path

from fontTools.ttLib import TTFont

BFA_FONT_PATH = Path(__file__).resolve().parents[3] / "fonts" / "bfa.ttf"


def require_bfa_font(path: Path | None = None) -> Path:
    """Returns the BFA font path after verifying the file exists."""
    font_path = Path(path) if path is not None else BFA_FONT_PATH
    if not font_path.is_file():
        raise FileNotFoundError(f"BFA font not found: {font_path}")
    return font_path


def load_bfa_font(path: Path | None = None) -> TTFont:
    """Loads the BFA OpenType font with fontTools."""
    return TTFont(str(require_bfa_font(path)))
