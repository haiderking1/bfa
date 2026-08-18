"""Data models for Sleeping Dogs: Definitive Edition inspector."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BigEntry:
    """Represents an index entry in a .bix archive."""

    index: int
    symbol_hash: int
    symbol_hex: str
    offset: int
    field2: int
    field3: int
    flags: int
    size: int
    resolved_path: Optional[str] = None
    is_compressed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ArchiveInfo:
    """Metadata and contents of a BIG/BIX archive pair."""

    archive_name: str
    bix_path: str
    big_path: str
    bix_size: int
    big_size: int
    entry_count: int
    compressed_entry_count: int
    uncompressed_entry_count: int
    chunk_magic: str
    subchunk_magic: str
    subchunk_name: str
    entries: List[BigEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class FontMapping:
    """Mapping between a UI role and a typeface."""

    role: str
    font_family: str
    style: int


@dataclass
class LanguageFontDefinition:
    """Font definition per language in FontDefinition.xml."""

    language_name: str
    filename: str
    font_maps: List[FontMapping] = field(default_factory=list)


@dataclass
class FontResourceInfo:
    """Inspection data for font resources (e.g. FontsEnglish.bin)."""

    resource_path: str
    archive_name: str
    symbol_hash_hex: str
    offset: int
    size: int
    uncompressed_size: int
    configured_fonts: List[str]
    is_scaleform_gfx: bool
    detected_format: str
    header_magic_hex: str
    scaleform_tags_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocalizationEntry:
    """One hashed localization string from a UILocalizationChunk."""

    key_hash: int
    text: str
    key_string: Optional[str] = None

    @property
    def key_hash_hex(self) -> str:
        return f"0x{self.key_hash:08x}"


@dataclass
class LocalizationTable:
    """Decoded Sleeping Dogs UILocalizationChunk string table."""

    debug_name: str
    name_uid: int
    type_uid: int
    qchunk_id: int
    qchunk_size: int
    qchunk_data_size: int
    qchunk_data_offset: int
    m_chunk_size: int
    m_padding: int
    qoffset: int
    encoding: str
    entries: List[LocalizationEntry] = field(default_factory=list)
    string_pool_padding: bytes = b""
    chunk_payload_padding: bytes = b""
    tail_padding: bytes = b""
    prefix: bytes = b""
    source_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "debug_name": self.debug_name,
            "name_uid_hex": f"0x{self.name_uid:08x}",
            "type_uid_hex": f"0x{self.type_uid:08x}",
            "encoding": self.encoding,
            "entry_count": len(self.entries),
            "entries": [
                {
                    "key_hash_hex": e.key_hash_hex,
                    "text": e.text,
                    "key_string": e.key_string,
                }
                for e in self.entries
            ],
        }


@dataclass
class TextResourceInfo:
    """Inspection data for text/screen BIN files."""

    resource_path: str
    archive_name: str
    symbol_hash_hex: str
    offset: int
    size: int
    uncompressed_size: int
    resource_type: str
    detected_format: str
    header_magic_hex: str
    encoding: str
    extracted_strings_count: int
    sample_strings: List[str] = field(default_factory=list)
    control_tags_detected: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    decoded_localization_strings: List[str] = field(default_factory=list)
    unknown_printable_data: List[str] = field(default_factory=list)
    is_verified_localization: bool = False


@dataclass
class ProtonCompatibilityInfo:
    """Information regarding Proton/Wine compatibility status."""

    proton_path: Optional[str]
    compat_data_path: Optional[str]
    app_id: int
    proton_available: bool
    wine_executable_test_passed: bool
    notes: str


@dataclass
class SleepingDogsInspectionReport:
    """Comprehensive machine-readable report of Sleeping Dogs formats."""

    game_install_dir: str
    steam_app_id: int
    game_language: str
    archives: List[ArchiveInfo]
    total_entries: int
    total_compressed_entries: int
    total_uncompressed_entries: int
    fonts_english_location: Dict[str, Any]
    font_definitions: List[LanguageFontDefinition]
    font_resource_metadata: FontResourceInfo
    text_resources: List[TextResourceInfo]
    proton_compatibility: ProtonCompatibilityInfo
    format_specifications: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DiscoveredLocalizationResource:
    """A UILocalizationChunk located in a BIG/BIX pair via its qSymbol path."""

    archive_name: str
    resource_path: str
    source_language: str
    debug_name: str
    symbol_hash: int
    is_compressed: bool
    extra_sz: int
    uncompressed: bytes
    raw: bytes
    table: LocalizationTable


@dataclass
class StagedLocalizationEntry:
    """Normalized localization entry stored in the Sleeping Dogs SQLite staging DB."""

    id: int
    resource_path: str
    archive_name: str
    source_language: str
    entry_index: int
    key_hash: int
    key_string: Optional[str]
    original_text: str
    translated_text: Optional[str]
    status: str
    control_tags: List[str]
    error_text: Optional[str]
    attempts: int


@dataclass
class ImportSummary:
    """Result of importing discovered Sleeping Dogs localization resources."""

    resources: int
    entries: int
    compressed_resources: int
    direct_resources: int
    source_language: str


@dataclass
class PackSummary:
    """Result of writing translated localization BINs to an isolated workspace."""

    output_dir: str
    resources_written: int
    resources_skipped: int
    entries_written: int
    compressed_resources: int
    direct_resources: int
    failed_resources: int
    overlay_resources: int = 0
