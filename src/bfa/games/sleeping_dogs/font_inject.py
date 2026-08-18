"""Inject the shared BFA typeface into a Sleeping Dogs font package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

from bfa.fonts.asset import require_bfa_font
from bfa.fonts.define_font3 import build_define_font3, parse_define_font3
from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.font_package import (
    encode_uiscreen_font_package,
    font3_tags,
    parse_uiscreen_font_package,
    replace_define_font3_payloads,
)
from bfa.games.sleeping_dogs.redirector import write_packaged_resource

FONTS_ENGLISH_RESOURCE = r"Data\UI\Screens\FontsEnglish.bin"


@dataclass(frozen=True, slots=True)
class FontInjectSummary:
    output_path: str
    resource_path: str
    font_path: str
    replaced_fonts: List[str]
    glyph_count: int
    arabic_codepoint_count: int
    package_size: int


def extract_font_package(game_path: Union[str, Path], resource_path: str = FONTS_ENGLISH_RESOURCE) -> bytes:
    """Reads a font package from the game archives without writing anything back."""
    root = Path(game_path)
    archive = BigArchive(root / "UI.bix")
    entry = archive.find_by_path(resource_path)
    if entry is None:
        raise ValueError(f"font resource {resource_path} was not found in UI.bix")
    return archive.extract_entry(entry, decompress=True)


def inject_bfa_into_font_package(package_bytes: bytes, font_path: Path) -> bytes:
    """Replaces every DefineFont3 face with outlines from the BFA font.

    Family names and font IDs stay the same so FontDefinition.xml and the
    movie's DefineText2 tags keep resolving.
    """
    source_font = require_bfa_font(font_path)
    package = parse_uiscreen_font_package(package_bytes)
    replacements: List[bytes] = []
    for tag in font3_tags(package.movie):
        original = parse_define_font3(tag.payload)
        replacements.append(
            build_define_font3(
                source_font,
                font_id=original.font_id,
                name=original.name,
                flags=original.flags,
                language=original.language,
            )
        )
    rebuilt = encode_uiscreen_font_package(
        package,
        replace_define_font3_payloads(package.movie, replacements),
    )
    _assert_injected_package(rebuilt, [parse_define_font3(item).name for item in replacements])
    return rebuilt


def write_injected_font_package(output_dir: Path, package_bytes: bytes) -> Path:
    """Writes an injected font package under Data\\ and RedirectorData\\."""
    data_path, _redirector_path = write_packaged_resource(
        Path(output_dir),
        FONTS_ENGLISH_RESOURCE,
        package_bytes,
    )
    return data_path


def inject_sleeping_dogs_font(
    game_path: Union[str, Path],
    output_dir: Path,
    *,
    font_path: Path | None = None,
    resource_path: str = FONTS_ENGLISH_RESOURCE,
) -> FontInjectSummary:
    """Extracts FontsEnglish.bin, injects BFA, and writes an isolated copy."""
    source_font = require_bfa_font(font_path)
    original = extract_font_package(game_path, resource_path)
    injected = inject_bfa_into_font_package(original, source_font)
    destination = write_injected_font_package(output_dir, injected)
    package = parse_uiscreen_font_package(injected)
    fonts = [parse_define_font3(tag.payload) for tag in font3_tags(package.movie)]
    codes = fonts[0].codes if fonts else []
    arabic = sum(1 for code in codes if 0x0600 <= code <= 0x06FF)
    return FontInjectSummary(
        output_path=str(destination),
        resource_path=resource_path,
        font_path=str(source_font),
        replaced_fonts=[item.name for item in fonts],
        glyph_count=len(codes),
        arabic_codepoint_count=arabic,
        package_size=len(injected),
    )


def _assert_injected_package(package_bytes: bytes, expected_names: List[str]) -> None:
    package = parse_uiscreen_font_package(package_bytes)
    fonts = [parse_define_font3(tag.payload) for tag in font3_tags(package.movie)]
    names = [item.name for item in fonts]
    if names != expected_names:
        raise ValueError(f"injected font names changed: {names!r}")
    if not fonts:
        raise ValueError("injected font package contains no DefineFont3 tags")
    codes = fonts[0].codes
    if 32 not in codes:
        raise ValueError("injected font is missing SPACE")
    if not any(0x0600 <= code <= 0x06FF for code in codes):
        raise ValueError("injected font is missing Arabic codepoints")
    if any(item.codes != codes for item in fonts[1:]):
        raise ValueError("injected faces do not share the same BFA cmap")
