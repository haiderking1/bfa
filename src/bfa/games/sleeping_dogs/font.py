"""Font configuration and font resource parser for Sleeping Dogs: Definitive Edition."""

from __future__ import annotations

import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.compression import decompress_qcmp, is_qcmp
from bfa.games.sleeping_dogs.hash import qsymbol_hash, qsymbol_hex
from bfa.games.sleeping_dogs.models import (
    FontMapping,
    FontResourceInfo,
    LanguageFontDefinition,
)

# Recognizable font and container signatures
SCALEFORM_SWF_SIGNATURES = (b"FWS", b"CWS", b"ZWS", b"GFX", b"CFX")
TRUETYPE_SIGNATURES = (b"OTTO", b"\x00\x01\x00\x00", b"true", b"typ1", b"ttcf")


def detect_font_payload_format(data: bytes) -> Tuple[bool, str, str, Dict[str, Any]]:
    """Detects whether binary data has a valid Scaleform GFx, TrueType, or UFG container signature.

    Returns:
        Tuple of (is_scaleform_gfx, detected_format_name, header_magic_hex, details_dict).
    """
    if not data:
        return False, "Empty Data", "", {}

    magic_hex = data[:8].hex()
    head4 = data[:4]
    head3 = data[:3]

    details: Dict[str, Any] = {
        "raw_length": len(data),
        "header_hex_8": magic_hex,
        "swf_signature_found": False,
        "truetype_signature_found": False,
    }

    if head3 in SCALEFORM_SWF_SIGNATURES or head4 in SCALEFORM_SWF_SIGNATURES:
        sig = head3.decode("latin1", "replace")
        details["swf_signature_found"] = True
        details["swf_signature"] = sig
        return True, f"Scaleform GFx / SWF ({sig})", magic_hex, details

    if head4 in TRUETYPE_SIGNATURES:
        details["truetype_signature_found"] = True
        return False, "Raw TrueType / OpenType Font", magic_hex, details

    if is_qcmp(data):
        return False, "QCMP Compressed Stream (PMCQ)", magic_hex, details

    # United Front Games binary screen/font container (e.g. 28 d6 d6 cd ...)
    return False, "UFG Proprietary Binary Screen/Font Container (.BIN)", magic_hex, details


def parse_font_definition_xml(xml_path: Union[str, Path]) -> List[LanguageFontDefinition]:
    """Parses FontDefinition.xml to extract language font mappings.

    Args:
        xml_path: Path to FontDefinition.xml.

    Returns:
        List of LanguageFontDefinition objects.
    """
    path = Path(xml_path)
    if not path.is_file():
        raise FileNotFoundError(f"FontDefinition.xml not found at {path}")

    tree = ET.parse(path)
    root = tree.getroot()

    definitions: List[LanguageFontDefinition] = []
    for lang_node in root.findall("Language"):
        lang_name = lang_node.get("name", "")
        filename = lang_node.get("filename", "")

        font_maps: List[FontMapping] = []
        for map_node in lang_node.findall("FontMap"):
            role = map_node.get("name", "")
            font_family = map_node.get("font", "")
            style_str = map_node.get("style", "0")
            try:
                style = int(style_str)
            except ValueError:
                style = 0
            font_maps.append(FontMapping(role=role, font_family=font_family, style=style))

        definitions.append(
            LanguageFontDefinition(
                language_name=lang_name,
                filename=filename,
                font_maps=font_maps,
            )
        )

    return definitions


def inspect_font_resource(
    ui_archive: BigArchive,
    font_resource_path: str = r"Data\UI\Screens\FontsEnglish.bin",
    font_definitions: Optional[List[LanguageFontDefinition]] = None,
) -> FontResourceInfo:
    """Inspects a font resource (e.g. FontsEnglish.bin) inside UI.big/UI.bix.

    Args:
        ui_archive: Opened BigArchive for UI.bix.
        font_resource_path: Path of the font resource.
        font_definitions: Optional parsed FontDefinition.xml list.

    Returns:
        FontResourceInfo with location, size, compression, and font metadata.
    """
    entry = ui_archive.find_by_path(font_resource_path)
    if entry is None:
        raise ValueError(f"Font resource {font_resource_path} not found in {ui_archive.archive_name}")

    raw_data = ui_archive.read_raw_entry(entry)
    decomp_data = ui_archive.extract_entry(entry, decompress=True)

    # Detect actual signature and format
    is_gfx, detected_format, magic_hex, details = detect_font_payload_format(decomp_data)

    # Collect configured fonts for English from FontDefinition.xml
    configured_fonts: List[str] = []
    if font_definitions:
        for defn in font_definitions:
            if defn.language_name.lower() in ("english", "english-uk"):
                for fm in defn.font_maps:
                    if fm.font_family not in configured_fonts:
                        configured_fonts.append(fm.font_family)

    if not configured_fonts:
        configured_fonts = ["DINCondensedTT", "Proxima Nova Lt Cyr", "Magistral Medium"]

    details["configured_fonts"] = configured_fonts
    details["bix_entry_index"] = entry.index
    details["is_bix_compressed"] = entry.is_compressed

    return FontResourceInfo(
        resource_path=font_resource_path,
        archive_name=ui_archive.archive_name,
        symbol_hash_hex=entry.symbol_hex,
        offset=entry.offset,
        size=entry.size,
        uncompressed_size=len(decomp_data),
        configured_fonts=configured_fonts,
        is_scaleform_gfx=is_gfx,
        detected_format=detected_format,
        header_magic_hex=magic_hex,
        scaleform_tags_summary=details,
    )
