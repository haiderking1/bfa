"""Sleeping Dogs Scaleform text-box discovery."""

from bfa.games.sleeping_dogs.layout.discover import boxes_for_instance, discover_text_field_boxes
from bfa.games.sleeping_dogs.layout.profile import (
    HUD_INFO_FLASHER_INSTANCE_PATH,
    HUD_INFO_FLASHER_WIDTH_PX,
    PACK_WRAP_FONT_SIZE_PX,
    PACK_WRAP_WIDTH_PX,
    PHONE_MESSAGE_INSTANCE_PATH,
    PHONE_MESSAGE_WIDTH_PX,
    SUBTITLE_FONT_SIZE_PX,
    SUBTITLE_INSTANCE_PATH,
    SUBTITLE_WIDTH_PX,
    SUBTITLE_WIDTH_TWIPS,
    wrap_metrics_for,
)
from bfa.games.sleeping_dogs.layout.typeset import typeset_localization_text

__all__ = [
    "HUD_INFO_FLASHER_INSTANCE_PATH",
    "HUD_INFO_FLASHER_WIDTH_PX",
    "PACK_WRAP_FONT_SIZE_PX",
    "PACK_WRAP_WIDTH_PX",
    "PHONE_MESSAGE_INSTANCE_PATH",
    "PHONE_MESSAGE_WIDTH_PX",
    "SUBTITLE_FONT_SIZE_PX",
    "SUBTITLE_INSTANCE_PATH",
    "SUBTITLE_WIDTH_PX",
    "SUBTITLE_WIDTH_TWIPS",
    "boxes_for_instance",
    "discover_text_field_boxes",
    "typeset_localization_text",
    "wrap_metrics_for",
]
