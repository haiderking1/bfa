"""Sleeping Dogs: Definitive Edition format discovery and inspection package."""

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.compression import decompress_qcmp, is_qcmp
from bfa.games.sleeping_dogs.font import (
    detect_font_payload_format,
    inspect_font_resource,
    parse_font_definition_xml,
)
from bfa.games.sleeping_dogs.hash import normalize_path, qsymbol_hash, qsymbol_hex
from bfa.games.sleeping_dogs.inspector import SleepingDogsInspector
from bfa.games.sleeping_dogs.localization import (
    encode_uilocalization_chunk,
    is_uilocalization_chunk,
    parse_uilocalization_chunk,
)
from bfa.games.sleeping_dogs.models import (
    ArchiveInfo,
    BigEntry,
    FontMapping,
    FontResourceInfo,
    LanguageFontDefinition,
    LocalizationEntry,
    LocalizationTable,
    ProtonCompatibilityInfo,
    SleepingDogsInspectionReport,
    TextResourceInfo,
)
from bfa.games.sleeping_dogs.text_resources import (
    KNOWN_LOCALIZATION_RESOURCES,
    KNOWN_SCREEN_RESOURCES,
    KNOWN_TEXT_RESOURCES,
    classify_payload_evidence,
    inspect_text_resources,
    scan_unknown_printable_bytes,
)

__all__ = [
    "ArchiveInfo",
    "BigArchive",
    "BigEntry",
    "FontMapping",
    "FontResourceInfo",
    "KNOWN_LOCALIZATION_RESOURCES",
    "KNOWN_SCREEN_RESOURCES",
    "KNOWN_TEXT_RESOURCES",
    "LanguageFontDefinition",
    "LocalizationEntry",
    "LocalizationTable",
    "ProtonCompatibilityInfo",
    "SleepingDogsInspectionReport",
    "SleepingDogsInspector",
    "TextResourceInfo",
    "classify_payload_evidence",
    "decompress_qcmp",
    "detect_font_payload_format",
    "encode_uilocalization_chunk",
    "inspect_font_resource",
    "inspect_text_resources",
    "is_qcmp",
    "is_uilocalization_chunk",
    "normalize_path",
    "parse_font_definition_xml",
    "parse_uilocalization_chunk",
    "qsymbol_hash",
    "qsymbol_hex",
    "scan_unknown_printable_bytes",
]
