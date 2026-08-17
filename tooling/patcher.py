"""Font patcher to extend BFA font with new vector glyphs."""

from __future__ import annotations

from pathlib import Path
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord

from tooling.models import GlyphSpec


def ensure_name_record(
    font: TTFont,
    name_id: int,
    string_val: str,
    platform_id: int = 3,
    plat_enc_id: int = 1,
    lang_id: int = 1033,
) -> None:
    """Ensure a specific name record exists in the name table."""
    name_table = font["name"]
    for record in name_table.names:
        if (
            record.nameID == name_id
            and record.platformID == platform_id
            and record.platEncID == plat_enc_id
            and record.langID == lang_id
        ):
            record.string = string_val.encode("utf-16-be" if platform_id == 3 else "mac-roman")
            return

    new_record = NameRecord()
    new_record.nameID = name_id
    new_record.platformID = platform_id
    new_record.platEncID = plat_enc_id
    new_record.langID = lang_id
    new_record.string = string_val.encode("utf-16-be" if platform_id == 3 else "mac-roman")
    name_table.names.append(new_record)


def update_font_metadata(font: TTFont) -> None:
    """Enforce required BFA font metadata."""
    # Windows platform records (3, 1, 1033)
    ensure_name_record(font, 1, "BFA", 3, 1, 1033)
    ensure_name_record(font, 2, "Regular", 3, 1, 1033)
    ensure_name_record(font, 3, "BFA;BFA-Regular", 3, 1, 1033)
    ensure_name_record(font, 4, "BFA", 3, 1, 1033)
    ensure_name_record(font, 6, "BFA-Regular", 3, 1, 1033)

    # Mac platform records (1, 0, 0)
    ensure_name_record(font, 1, "BFA", 1, 0, 0)
    ensure_name_record(font, 2, "Regular", 1, 0, 0)
    ensure_name_record(font, 3, "BFA;BFA-Regular", 1, 0, 0)
    ensure_name_record(font, 4, "BFA", 1, 0, 0)
    ensure_name_record(font, 6, "BFA-Regular", 1, 0, 0)


def patch_font(input_path: Path, output_path: Path, specs: list[GlyphSpec]) -> None:
    """Patch the font with given glyph specifications."""
    font = TTFont(str(input_path))
    top_dict = font["CFF "].cff.topDictIndex[0]
    charstrings = top_dict.CharStrings

    glyph_order = font.getGlyphOrder()
    existing_glyph_set = set(glyph_order)

    for spec in specs:
        if spec.draw_fn is None:
            continue

        # Draw glyph using T2CharStringPen
        pen = T2CharStringPen(width=spec.advance_width, glyphSet=charstrings)
        spec.draw_fn(pen)
        char_string = pen.getCharString(
            private=top_dict.Private,
            globalSubrs=top_dict.GlobalSubrs,
        )

        # Calculate bounding box to determine left side bearing (LSB)
        bounds_pen = BoundsPen(charstrings)
        char_string.draw(bounds_pen)
        lsb = int(bounds_pen.bounds[0]) if bounds_pen.bounds else 0

        # Store in CFF CharStrings
        if spec.name in charstrings.charStrings:
            index = charstrings.charStrings[spec.name]
            charstrings.charStringsIndex[index] = char_string
        else:
            charstrings.charStringsIndex.append(char_string)
            charstrings.charStrings[spec.name] = len(charstrings.charStringsIndex) - 1

        # Add to glyph order if new
        if spec.name not in existing_glyph_set:
            glyph_order.append(spec.name)
            existing_glyph_set.add(spec.name)

        # Set metrics in hmtx
        font["hmtx"][spec.name] = (spec.advance_width, lsb)

        # Map unicode in cmap tables
        for subtable in font["cmap"].tables:
            if subtable.isUnicode():
                subtable.cmap[spec.unicode_cp] = spec.name

        # Update GDEF GlyphClassDef if present
        if "GDEF" in font and hasattr(font["GDEF"].table, "GlyphClassDef"):
            class_defs = font["GDEF"].table.GlyphClassDef
            if class_defs and hasattr(class_defs, "classDefs"):
                class_defs.classDefs[spec.name] = 1  # Base glyph

    # Update font glyph order and maxp
    font.setGlyphOrder(glyph_order)
    font["maxp"].numGlyphs = len(glyph_order)

    # Maintain metadata
    update_font_metadata(font)

    # Save to output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(output_path))
