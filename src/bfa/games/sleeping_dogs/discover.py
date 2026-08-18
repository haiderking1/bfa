"""Discover Sleeping Dogs UILocalizationChunk resources from BIG/BIX archives.

Resource paths are reconstructed as Data\\UI\\Localization\\{debug_name}.bin and
accepted only when the qSymbol hash matches the BIX entry. This does not depend
on a hardcoded short list of files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.compression import is_qcmp
from bfa.games.sleeping_dogs.hash import qsymbol_hash
from bfa.games.sleeping_dogs.localization import (
    is_uilocalization_chunk,
    parse_uilocalization_chunk,
)
from bfa.games.sleeping_dogs.models import DiscoveredLocalizationResource

LOCALIZATION_DIR = r"Data\UI\Localization"
MAX_COMPRESSED_UNCOMPRESSED_SIZE = 512_000


def localization_resource_path(debug_name: str) -> str:
    """Returns the canonical qSymbol path for a localization debug name."""
    return rf"{LOCALIZATION_DIR}\{debug_name}.bin"


def source_language_from_debug_name(debug_name: str) -> str:
    """Extracts the language/track prefix from a localization debug name."""
    for prefix in ("DBG_LBL_", "DBG_MAX_", "DBG_BLNK_", "DBG_ID_"):
        if debug_name.startswith(prefix):
            return prefix.rstrip("_")
    if "_" not in debug_name:
        return debug_name
    return debug_name.split("_", 1)[0]


def _open_archives(game_path: Union[str, Path, Sequence[BigArchive]]) -> List[BigArchive]:
    if isinstance(game_path, (str, Path)):
        root = Path(game_path)
        archives: List[BigArchive] = []
        for bix_file in sorted(root.glob("*.bix")):
            big_file = bix_file.with_suffix(".big")
            if big_file.is_file():
                archives.append(BigArchive(bix_file, big_file))
        return archives
    return list(game_path)


def _debug_label_map(resources: Iterable[DiscoveredLocalizationResource]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for resource in resources:
        if resource.source_language != "DBG_LBL":
            continue
        for entry in resource.table.entries:
            if entry.key_string:
                mapping[entry.key_hash] = entry.key_string
    return mapping


def apply_debug_key_strings(
    resources: List[DiscoveredLocalizationResource],
) -> List[DiscoveredLocalizationResource]:
    """Fills optional key_string values from matching DBG_LBL resources."""
    keys = _debug_label_map(resources)
    if not keys:
        return resources
    for resource in resources:
        if resource.source_language == "DBG_LBL":
            continue
        for entry in resource.table.entries:
            if entry.key_string is None and entry.key_hash in keys:
                entry.key_string = keys[entry.key_hash]
    return resources


def discover_localization_resources(
    game_path: Union[str, Path, Sequence[BigArchive]],
    *,
    language: Optional[str] = "EN",
    include_debug_labels: bool = True,
) -> List[DiscoveredLocalizationResource]:
    """Finds UILocalizationChunk resources and verifies their qSymbol paths.

    Args:
        game_path: Game install directory or already-opened archives.
        language: If set, keep resources whose debug name starts with
            ``{language}_``. ``None`` keeps every localization chunk.
        include_debug_labels: When filtering to a spoken language, also load
            DBG_LBL resources so key preimages can be attached.
    """
    archives = _open_archives(game_path)
    discovered: List[DiscoveredLocalizationResource] = []
    keep_languages: Optional[set[str]] = None
    if language is not None:
        keep_languages = {language}
        if include_debug_labels:
            keep_languages.add("DBG_LBL")

    for archive in archives:
        for entry in archive.entries:
            head = archive.read_raw_prefix(entry, 4)
            compressed = entry.is_compressed or is_qcmp(head)
            if compressed:
                if entry.size > MAX_COMPRESSED_UNCOMPRESSED_SIZE:
                    continue
                try:
                    raw = archive.read_raw_entry(entry)
                    uncompressed = archive.extract_entry(entry, decompress=True)
                except (OSError, ValueError):
                    continue
            else:
                if not is_uilocalization_chunk(head):
                    continue
                raw = archive.read_raw_entry(entry)
                uncompressed = raw

            if not is_uilocalization_chunk(uncompressed):
                continue
            try:
                table = parse_uilocalization_chunk(uncompressed)
            except ValueError:
                continue

            resource_path = localization_resource_path(table.debug_name)
            if qsymbol_hash(resource_path) != entry.symbol_hash:
                continue

            source_language = source_language_from_debug_name(table.debug_name)
            if keep_languages is not None and source_language not in keep_languages:
                continue

            discovered.append(
                DiscoveredLocalizationResource(
                    archive_name=archive.archive_name,
                    resource_path=resource_path,
                    source_language=source_language,
                    debug_name=table.debug_name,
                    symbol_hash=entry.symbol_hash,
                    is_compressed=compressed,
                    extra_sz=entry.flags,
                    uncompressed=uncompressed,
                    raw=raw,
                    table=table,
                )
            )

    if include_debug_labels:
        apply_debug_key_strings(discovered)
    if language is not None:
        discovered = [item for item in discovered if item.source_language == language]

    discovered.sort(key=lambda item: item.resource_path.lower())
    return discovered
