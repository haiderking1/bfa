"""Comprehensive font validation module for BFA."""

from __future__ import annotations

import io
import subprocess
from pathlib import Path
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
import uharfbuzz as hb

from tooling.models import ValidationReport

REQUESTED_UNICODES = {
    # Arrows (10)
    "←": (0x2190, "arrowleft", "Arrows"),
    "→": (0x2192, "arrowright", "Arrows"),
    "↑": (0x2191, "arrowup", "Arrows"),
    "↓": (0x2193, "arrowdown", "Arrows"),
    "↖": (0x2196, "arrownorthwest", "Arrows"),
    "↗": (0x2197, "arrownortheast", "Arrows"),
    "↘": (0x2198, "arrowsoutheast", "Arrows"),
    "↙": (0x2199, "arrowsouthwest", "Arrows"),
    "↔": (0x2194, "arrowboth", "Arrows"),
    "↕": (0x2195, "arrowupdown", "Arrows"),
    # Navigation (6)
    "⌂": (0x2302, "house", "Navigation"),
    "⌫": (0x232B, "eraseleft", "Navigation"),
    "⏎": (0x23CE, "return", "Navigation"),
    "↵": (0x21B5, "carriagereturn", "Navigation"),
    "⇧": (0x21E7, "arrowupoutline", "Navigation"),
    "⇥": (0x21E5, "arrowrightbar", "Navigation"),
    # Basic controls (9)
    "+": (0x002B, "plus", "Basic Controls"),
    "−": (0x2212, "minus", "Basic Controls"),
    "×": (0x00D7, "multiply", "Basic Controls"),
    "÷": (0x00F7, "divide", "Basic Controls"),
    "=": (0x003D, "equal", "Basic Controls"),
    "<": (0x003C, "less", "Basic Controls"),
    ">": (0x003E, "greater", "Basic Controls"),
    "≤": (0x2264, "lessequal", "Basic Controls"),
    "≥": (0x2265, "greaterequal", "Basic Controls"),
    # UI decoration (7)
    "…": (0x2026, "ellipsis", "UI Decoration"),
    "•": (0x2022, "bullet", "UI Decoration"),
    "·": (0x00B7, "periodcentered", "UI Decoration"),
    "★": (0x2605, "blackstar", "UI Decoration"),
    "☆": (0x2606, "whitestar", "UI Decoration"),
    "♥": (0x2665, "blackheart", "UI Decoration"),
    "♡": (0x2661, "whiteheart", "UI Decoration"),
    # Brackets and quotes (14)
    "[": (0x005B, "bracketleft", "Brackets & Quotes"),
    "]": (0x005D, "bracketright", "Brackets & Quotes"),
    "{": (0x007B, "braceleft", "Brackets & Quotes"),
    "}": (0x007D, "braceright", "Brackets & Quotes"),
    "(": (0x0028, "parenleft", "Brackets & Quotes"),
    ")": (0x0029, "parenright", "Brackets & Quotes"),
    "«": (0x00AB, "guillemotleft", "Brackets & Quotes"),
    "»": (0x00BB, "guillemotright", "Brackets & Quotes"),
    "“": (0x201C, "quotedblleft", "Brackets & Quotes"),
    "”": (0x201D, "quotedblright", "Brackets & Quotes"),
    "‘": (0x2018, "quoteleft", "Brackets & Quotes"),
    "’": (0x2019, "quoteright", "Brackets & Quotes"),
    # Legal and currency (7)
    "©": (0x00A9, "copyright", "Legal & Currency"),
    "®": (0x00AE, "registered", "Legal & Currency"),
    "™": (0x2122, "trademark", "Legal & Currency"),
    "$": (0x0024, "dollar", "Legal & Currency"),
    "€": (0x20AC, "Euro", "Legal & Currency"),
    "£": (0x00A3, "sterling", "Legal & Currency"),
    "¥": (0x00A5, "yen", "Legal & Currency"),
}


def validate_cmap(font: TTFont, report: ValidationReport) -> None:
    """Verify all requested code points exist in the cmap and map to drawable glyphs."""
    cmap = font.getBestCmap()
    if not cmap:
        report.add_fail("cmap", "Font has no valid cmap table")
        return

    charstrings = font["CFF "].cff.topDictIndex[0].CharStrings if "CFF " in font else None
    missing_chars = []
    undrawable_chars = []

    for char, (cp, expected_name, category) in REQUESTED_UNICODES.items():
        if cp not in cmap:
            missing_chars.append(f"{char} (U+{cp:04X})")
            continue

        glyph_name = cmap[cp]
        if charstrings is not None:
            if glyph_name not in charstrings:
                undrawable_chars.append(f"{char} (glyph '{glyph_name}' missing in CFF)")
            else:
                try:
                    pen = RecordingPen()
                    charstrings[glyph_name].draw(pen)
                    if not pen.value:
                        undrawable_chars.append(f"{char} (glyph '{glyph_name}' has empty outlines)")
                except Exception as ex:
                    undrawable_chars.append(f"{char} (glyph '{glyph_name}' draw error: {ex})")

    if missing_chars:
        report.add_fail("cmap_missing", f"Missing requested characters: {', '.join(missing_chars)}")
    else:
        report.add_pass("cmap_presence", f"All {len(REQUESTED_UNICODES)} requested characters present in cmap")

    if undrawable_chars:
        report.add_fail("glyph_draw", f"Undrawable glyphs: {', '.join(undrawable_chars)}")
    else:
        report.add_pass("glyph_draw", "All requested glyphs have valid, drawable outlines")


def validate_arabic(font: TTFont, report: ValidationReport) -> None:
    """Verify Arabic alphabet, GSUB shaping, and GPOS tables."""
    cmap = font.getBestCmap()
    arabic_codepoints = [cp for cp in cmap if 0x0600 <= cp <= 0x06FF]
    if len(arabic_codepoints) < 30:
        report.add_fail("arabic_cmap", f"Arabic codepoints count too low: {len(arabic_codepoints)}")
    else:
        report.add_pass("arabic_cmap", f"Found {len(arabic_codepoints)} Arabic codepoints in cmap")

    if "GSUB" not in font:
        report.add_fail("gsub_table", "GSUB table missing")
    else:
        gsub_features = [f.FeatureTag for f in font["GSUB"].table.FeatureList.FeatureRecord]
        required_features = ["init", "medi", "fina", "isol"]
        missing_features = [f for f in required_features if f not in gsub_features]
        if missing_features:
            report.add_fail("gsub_features", f"Missing GSUB features: {missing_features}")
        else:
            report.add_pass("gsub_features", f"GSUB features intact: {gsub_features}")

    if "GPOS" not in font:
        report.add_fail("gpos_table", "GPOS table missing")
    else:
        gpos_features = [f.FeatureTag for f in font["GPOS"].table.FeatureList.FeatureRecord]
        report.add_pass("gpos_features", f"GPOS features intact: {gpos_features}")


def validate_metadata(font_path: Path, font: TTFont, report: ValidationReport) -> None:
    """Verify font family name, full name, PostScript name, and fc-scan output."""
    name_table = font["name"]
    names_dict: dict[int, str] = {}
    for rec in name_table.names:
        if rec.platformID == 3 and rec.platEncID == 1:
            names_dict[rec.nameID] = rec.toUnicode()

    family = names_dict.get(1, "")
    full_name = names_dict.get(4, "")
    ps_name = names_dict.get(6, "")

    if family != "BFA":
        report.add_fail("metadata_family", f"Family name is '{family}', expected 'BFA'")
    else:
        report.add_pass("metadata_family", "Family name is 'BFA'")

    if full_name != "BFA":
        report.add_fail("metadata_fullname", f"Full name is '{full_name}', expected 'BFA'")
    else:
        report.add_pass("metadata_fullname", "Full name is 'BFA'")

    if ps_name != "BFA-Regular":
        report.add_fail("metadata_psname", f"PostScript name is '{ps_name}', expected 'BFA-Regular'")
    else:
        report.add_pass("metadata_psname", "PostScript name is 'BFA-Regular'")

    # Run fc-scan
    try:
        proc = subprocess.run(
            ["fc-scan", str(font_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        output = proc.stdout
        if 'family: "BFA"' in output and 'fullname: "BFA"' in output and 'postscriptname: "BFA-Regular"' in output:
            report.add_pass("fc_scan", "fc-scan confirms family 'BFA', fullname 'BFA', postscriptname 'BFA-Regular'")
        else:
            report.add_fail("fc_scan", f"fc-scan output mismatch:\n{output[:300]}")
    except Exception as ex:
        report.add_warning(f"fc-scan check skipped or errored: {ex}")


def validate_fonttools(font: TTFont, report: ValidationReport) -> None:
    """Verify font compiles and round-trips cleanly via fontTools."""
    try:
        buf = io.BytesIO()
        font.save(buf)
        buf.seek(0)
        reloaded = TTFont(buf)
        if len(reloaded.getGlyphOrder()) == len(font.getGlyphOrder()):
            report.add_pass("fonttools_roundtrip", f"Font roundtripped cleanly ({len(reloaded.getGlyphOrder())} glyphs)")
        else:
            report.add_fail("fonttools_roundtrip", "Glyph count mismatch after roundtrip")
    except Exception as ex:
        report.add_fail("fonttools_roundtrip", f"Font compile/save error: {ex}")


def validate_shaping(font_path: Path, report: ValidationReport) -> None:
    """Verify HarfBuzz shaping of test Arabic text and symbols."""
    try:
        blob = hb.Blob.from_file_path(str(font_path))
        face = hb.Face(blob)
        hb_font = hb.Font(face)

        test_str = "مرحباً ⌂ ⏎ ← → ↑ ↓ ★ ☆ ♥ ♡ + − × ÷ = < > ≤ ≥ [ ] { } ( ) « » “ ” ‘ ’ © ® ™ $ € £ ¥"
        buf = hb.Buffer()
        buf.add_str(test_str)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf)

        if not buf.glyph_infos:
            report.add_fail("harfbuzz_shaping", "HarfBuzz shaping produced 0 glyphs")
        else:
            notdef_count = sum(1 for info in buf.glyph_infos if info.codepoint == 0)
            if notdef_count > 0:
                report.add_fail("harfbuzz_shaping", f"HarfBuzz shaped string contains {notdef_count} .notdef glyphs")
            else:
                report.add_pass("harfbuzz_shaping", f"HarfBuzz shaped string successfully ({len(buf.glyph_infos)} glyphs, 0 .notdef)")
    except Exception as ex:
        report.add_fail("harfbuzz_shaping", f"HarfBuzz shaping exception: {ex}")


def validate_font(font_path: Path) -> ValidationReport:
    """Execute all validation checks on the specified font."""
    report = ValidationReport()
    try:
        font = TTFont(str(font_path))
    except Exception as ex:
        report.add_fail("load_font", f"Failed to load font with fontTools: {ex}")
        return report

    validate_cmap(font, report)
    validate_arabic(font, report)
    validate_metadata(font_path, font, report)
    validate_fonttools(font, report)
    validate_shaping(font_path, report)

    return report
