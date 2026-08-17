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
from bfa.games.sleeping_dogs.models import (
    ArchiveInfo,
    BigEntry,
    FontMapping,
    FontResourceInfo,
    LanguageFontDefinition,
    ProtonCompatibilityInfo,
    SleepingDogsInspectionReport,
    TextResourceInfo,
)
from bfa.games.sleeping_dogs.text_resources import (
    KNOWN_TEXT_RESOURCES,
    classify_payload_evidence,
    extract_strings_and_tags,
    inspect_text_resources,
)

__all__ = [
    "ArchiveInfo",
    "BigArchive",
    "BigEntry",
    "FontMapping",
    "FontResourceInfo",
    "KNOWN_TEXT_RESOURCES",
    "LanguageFontDefinition",
    "ProtonCompatibilityInfo",
    "SleepingDogsInspectionReport",
    "SleepingDogsInspector",
    "TextResourceInfo",
    "classify_payload_evidence",
    "decompress_qcmp",
    "detect_font_payload_format",
    "extract_strings_and_tags",
    "inspect_font_resource",
    "inspect_text_resources",
    "is_qcmp",
    "normalize_path",
    "parse_font_definition_xml",
    "qsymbol_hash",
    "qsymbol_hex",
]
