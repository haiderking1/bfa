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
