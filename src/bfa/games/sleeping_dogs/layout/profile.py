"""Measured Scaleform fields used to typeset Arabic loc strings.

Subtitle RECT: ``subtitles_1/m_text/dispTxt`` on GlobalOverlay.
HUD objective RECT: ``mc_infoFlasher/mc_inner/mc_text/tf_text``.
Phone SMS RECT: ``mc_smartphone/tf_smartphoneLeftAlign``.

Loc tables are shared, but widgets are not. Wrap width is chosen from the loc
key and resource: SMS keys use the phone box, gameplay/UI tables use the HUD
flasher, and spoken/NIS tables use the subtitle box.
"""

from __future__ import annotations

from dataclasses import dataclass

from bfa.layout.twips import twips_to_pixels

SUBTITLE_INSTANCE_PATH = "subtitles_1/m_text/dispTxt"
SUBTITLE_WIDTH_TWIPS = 22858
SUBTITLE_HEIGHT_TWIPS = 1900
SUBTITLE_FONT_HEIGHT_TWIPS = 420
SUBTITLE_WIDTH_PX = twips_to_pixels(SUBTITLE_WIDTH_TWIPS)
SUBTITLE_FONT_SIZE_PX = twips_to_pixels(SUBTITLE_FONT_HEIGHT_TWIPS)

HUD_INFO_FLASHER_INSTANCE_PATH = "mc_infoFlasher/mc_inner/mc_text/tf_text"
HUD_INFO_FLASHER_WIDTH_TWIPS = 8920
HUD_INFO_FLASHER_WIDTH_PX = twips_to_pixels(HUD_INFO_FLASHER_WIDTH_TWIPS)
HUD_INFO_FLASHER_FONT_SIZE_PX = 20.0

PHONE_MESSAGE_INSTANCE_PATH = "mc_smartphone/tf_smartphoneLeftAlign"
PHONE_MESSAGE_WIDTH_TWIPS = 4429
PHONE_MESSAGE_WIDTH_PX = twips_to_pixels(PHONE_MESSAGE_WIDTH_TWIPS)
PHONE_MESSAGE_FONT_SIZE_PX = 19.0

PACK_WRAP_WIDTH_PX = HUD_INFO_FLASHER_WIDTH_PX
PACK_WRAP_FONT_SIZE_PX = HUD_INFO_FLASHER_FONT_SIZE_PX

_UI_RESOURCE_PREFIXES = (
    "EN_Gameplay",
    "EN_Global",
    "EN_Front-End",
    "EN_Achievements",
    "EN_Ignored",
)


@dataclass(frozen=True, slots=True)
class WrapMetrics:
    """Pixel wrap box used when packing one loc string."""

    width_px: float
    font_size_px: float


def wrap_metrics_for(
    *,
    resource_debug_name: str = "",
    key_string: str | None = None,
) -> WrapMetrics:
    """Returns the wrap box for one loc string from its table name and key."""
    if _is_phone_message_key(key_string):
        return WrapMetrics(PHONE_MESSAGE_WIDTH_PX, PHONE_MESSAGE_FONT_SIZE_PX)
    if _is_subtitle_resource(resource_debug_name):
        return WrapMetrics(SUBTITLE_WIDTH_PX, SUBTITLE_FONT_SIZE_PX)
    return WrapMetrics(HUD_INFO_FLASHER_WIDTH_PX, HUD_INFO_FLASHER_FONT_SIZE_PX)


def _is_phone_message_key(key_string: str | None) -> bool:
    if not key_string:
        return False
    tokens = key_string.upper().replace("-", "_").split("_")
    return "SMS" in tokens or "TEXTMSG" in tokens


def _is_subtitle_resource(debug_name: str) -> bool:
    if debug_name == "":
        return False
    return not debug_name.startswith(_UI_RESOURCE_PREFIXES)
