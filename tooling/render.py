"""Visual test rendering for BFA font inspection."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import uharfbuzz as hb
from fontTools.ttLib import TTFont


def render_arabic_text_line(
    image: Image.Image,
    font_path: str,
    font_size: int,
    text: str,
    x: int,
    y: int,
    fill: tuple[int, int, int] = (0, 0, 0),
) -> int:
    """Render Arabic text right-to-left using HarfBuzz shaping and PIL drawing."""
    draw = ImageDraw.Draw(image)
    pil_font = ImageFont.truetype(font_path, size=font_size)

    # Use PIL's built-in complex text layout / Raqm / HarfBuzz if available
    try:
        draw.text((x, y), text, font=pil_font, fill=fill, direction="rtl", language="ar")
        bbox = draw.textbbox((x, y), text, font=pil_font, direction="rtl", language="ar")
        return bbox[2] - bbox[0]
    except Exception:
        # Fallback to direct draw
        draw.text((x, y), text, font=pil_font, fill=fill)
        bbox = draw.textbbox((x, y), text, font=pil_font)
        return bbox[2] - bbox[0]


def render_test_sheet(font_path: Path, output_image_path: Path) -> Path:
    """Render a comprehensive visual inspection sheet for the BFA font."""
    img_width = 1400
    img_height = 1600
    image = Image.new("RGB", (img_width, img_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Fonts
    title_font = ImageFont.truetype(str(font_path), size=36)
    section_font = ImageFont.truetype(str(font_path), size=24)
    glyph_font_large = ImageFont.truetype(str(font_path), size=44)
    glyph_font_medium = ImageFont.truetype(str(font_path), size=28)
    label_font = ImageFont.load_default()

    # Draw header banner
    draw.rectangle([(0, 0), (img_width, 90)], fill=(30, 41, 59))
    draw.text((40, 26), "BFA Font - UI Symbol Set & Localization Verification", fill=(255, 255, 255), font=title_font)

    current_y = 120

    # Sections to display
    sections = [
        (
            "1. Directional Arrows",
            [
                ("←", "U+2190", "arrowleft"),
                ("→", "U+2192", "arrowright"),
                ("↑", "U+2191", "arrowup"),
                ("↓", "U+2193", "arrowdown"),
                ("↖", "U+2196", "arrownorthwest"),
                ("↗", "U+2197", "arrownortheast"),
                ("↘", "U+2198", "arrowsoutheast"),
                ("↙", "U+2199", "arrowsouthwest"),
                ("↔", "U+2194", "arrowboth"),
                ("↕", "U+2195", "arrowupdown"),
            ],
        ),
        (
            "2. Navigation Symbols",
            [
                ("⌂", "U+2302", "house"),
                ("⌫", "U+232B", "eraseleft"),
                ("⏎", "U+23CE", "return"),
                ("↵", "U+21B5", "carriagereturn"),
                ("⇧", "U+21E7", "arrowupoutline"),
                ("⇥", "U+21E5", "arrowrightbar"),
            ],
        ),
        (
            "3. Basic Controls & Math",
            [
                ("+", "U+002B", "plus"),
                ("−", "U+2212", "minus"),
                ("×", "U+00D7", "multiply"),
                ("÷", "U+00F7", "divide"),
                ("=", "U+003D", "equal"),
                ("<", "U+003C", "less"),
                (">", "U+003E", "greater"),
                ("≤", "U+2264", "lessequal"),
                ("≥", "U+2265", "greaterequal"),
            ],
        ),
        (
            "4. UI Decoration",
            [
                ("…", "U+2026", "ellipsis"),
                ("•", "U+2022", "bullet"),
                ("·", "U+00B7", "periodcentered"),
                ("★", "U+2605", "blackstar"),
                ("☆", "U+2606", "whitestar"),
                ("♥", "U+2665", "blackheart"),
                ("♡", "U+2661", "whiteheart"),
            ],
        ),
        (
            "5. Brackets & Quotes",
            [
                ("[", "U+005B", "bracketleft"),
                ("]", "U+005D", "bracketright"),
                ("{", "U+007B", "braceleft"),
                ("}", "U+007D", "braceright"),
                ("(", "U+0028", "parenleft"),
                (")", "U+0029", "parenright"),
                ("«", "U+00AB", "guillemotleft"),
                ("»", "U+00BB", "guillemotright"),
                ("“", "U+201C", "quotedblleft"),
                ("”", "U+201D", "quotedblright"),
                ("‘", "U+2018", "quoteleft"),
                ("’", "U+2019", "quoteright"),
            ],
        ),
        (
            "6. Legal & Currency",
            [
                ("©", "U+00A9", "copyright"),
                ("®", "U+00AE", "registered"),
                ("™", "U+2122", "trademark"),
                ("$", "U+0024", "dollar"),
                ("€", "U+20AC", "Euro"),
                ("£", "U+00A3", "sterling"),
                ("¥", "U+00A5", "yen"),
            ],
        ),
    ]

    for section_title, glyphs in sections:
        # Section Header
        draw.text((40, current_y), section_title, fill=(51, 65, 85), font=section_font)
        draw.line([(40, current_y + 32), (img_width - 40, current_y + 32)], fill=(226, 232, 240), width=1)
        current_y += 45

        # Render glyph tiles in rows
        tile_width = 115
        tile_height = 80
        per_row = (img_width - 80) // tile_width

        for idx, (char, codepoint, glyph_name) in enumerate(glyphs):
            row = idx // per_row
            col = idx % per_row
            x = 40 + col * tile_width
            y = current_y + row * (tile_height + 10)

            # Tile background
            draw.rectangle([(x, y), (x + tile_width - 8, y + tile_height)], fill=(248, 250, 252), outline=(203, 213, 225), width=1)

            # Glyph
            draw.text((x + 12, y + 8), char, fill=(15, 23, 42), font=glyph_font_large)

            # Metadata label
            draw.text((x + 60, y + 14), codepoint, fill=(100, 116, 139), font=label_font)
            draw.text((x + 60, y + 36), glyph_name[:8], fill=(71, 85, 105), font=label_font)

        rows_count = (len(glyphs) + per_row - 1) // per_row
        current_y += rows_count * (tile_height + 10) + 20

    # Section 7: Comprehensive Game UI & Arabic Localization Strings
    draw.text((40, current_y), "7. Localization & Game UI Test Strings", fill=(51, 65, 85), font=section_font)
    draw.line([(40, current_y + 32), (img_width - 40, current_y + 32)], fill=(226, 232, 240), width=1)
    current_y += 45

    test_lines = [
        "Arabic Text: مرحباً بك في مغامرة البطل العربي - اضغط ⏎ للبدء",
        "Controls: [⇧] قفز   [⇥] الحقيبة   [⌫] تراجع   [⌂] القائمة الرئيسية",
        "Game HUD: الصحة: 100% ♥ ♥ ♡   التقييم: ★ ★ ★ ☆ ☆   المستوى: 42 ≥ 10",
        "Inventory: 50 × ذهب $1200   درع: +15   سيف: €450 / £380 / ¥5000",
        "Dialogues: «انتبه يا بطل! الطريق مغلق ↵» … قال: “سنواصل التقدم ← ↑ →”",
        "Legal: BFA™ Engine © 2026 BFA Studios®. All Rights Reserved.",
    ]

    for line in test_lines:
        draw.text((40, current_y), line, fill=(15, 23, 42), font=glyph_font_medium)
        current_y += 42

    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(output_image_path))
    return output_image_path
