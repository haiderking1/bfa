"""Measured text-field geometry extracted from Scaleform movies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextFieldBox:
    """One DefineEditText rectangle and the instance path that places it."""

    screen_path: str
    screen_name: str
    instance_path: str
    character_id: int
    width_twips: int
    height_twips: int
    width_px: float
    height_px: float
    word_wrap: bool
    multiline: bool
    html: bool
    align: str
    font_size_px: float | None
    stage_width_px: float
    stage_height_px: float
