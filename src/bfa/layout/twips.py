"""SWF/Scaleform coordinate conversion.

Flash stores rectangle edges in twips. One pixel is 20 twips.
"""

from __future__ import annotations

TWIPS_PER_PIXEL = 20


def twips_to_pixels(twips: int) -> float:
    """Converts a SWF twip length to CSS/Scaleform pixels."""
    return twips / TWIPS_PER_PIXEL
