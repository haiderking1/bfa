"""Text and Screen BIN resource inspection for Sleeping Dogs: Definitive Edition."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.compression import decompress_qcmp, is_qcmp
from bfa.games.sleeping_dogs.hash import qsymbol_hash, qsymbol_hex
from bfa.games.sleeping_dogs.models import BigEntry, TextResourceInfo

# Known UI screens and text-bearing assets in Sleeping Dogs
KNOWN_TEXT_RESOURCES: List[str] = [
    r"Data\UI\Screens\Global.BIN",
    r"Data\UI\Screens\HUD.BIN",
    r"Data\UI\Screens\PauseMenu.BIN",
    r"Data\UI\Screens\Options_Display.BIN",
    r"Data\UI\Screens\Options_DisplayAdvanced.BIN",
    r"Data\UI\Screens\Options_Audio.BIN",
    r"Data\UI\Screens\Options_Game.BIN",
    r"Data\UI\Screens\Options_Controllers.BIN",
    r"Data\UI\Screens\Options_ButtonMapping.BIN",
    r"Data\UI\Screens\Options_Calibration.BIN",
    r"Data\UI\Screens\Mainmenu.BIN",
    r"Data\UI\Screens\StartFlowScreen.BIN",
    r"Data\UI\Screens\Wardrobe.BIN",
    r"Data\UI\Screens\Upgrades.BIN",
    r"Data\UI\Screens\WorldMap.BIN",
    r"Data\UI\Screens\SocialHub.BIN",
    r"Data\UI\Screens\SaveLoad.BIN",
    r"Data\UI\Screens\Stats.BIN",
    r"Data\UI\Screens\SpyPC.BIN",
    r"Data\UI\Screens\SpyCam.BIN",
    r"Data\UI\Screens\SafeCrackingMinigame.BIN",
    r"Data\UI\Screens\PickLockMinigame.BIN",
    r"Data\UI\Screens\PokerDiceMinigame.BIN",
    r"Data\UI\Screens\PhoneTraceMinigame.BIN",
    r"Data\UI\Screens\PhoneSignalMinigame.BIN",
    r"Data\UI\Screens\HackingMinigame.BIN",
    r"Data\UI\Screens\FaceTracker.BIN",
    r"Data\UI\Screens\Cockfight.BIN",
    r"Data\UI\Screens\CaseComplete.BIN",
    r"Data\UI\Screens\MissionHealth.BIN",
    r"Data\UI\Screens\PCBenchmark.BIN",
    r"Data\UI\Screens\RaceHUD.BIN",
    r"Data\UI\Screens\Credits.BIN",
    r"Data\UI\Screens\OpeningCredits.BIN",
    r"Data\UI\Screens\NISPause.BIN",
    r"Data\UI\Screens\ScriptableList.BIN",
    r"Data\UI\Screens\Splash.BIN",
    r"Data\UI\Screens\gfxfontlib.BIN",
    r"Data\Dialogue\Radio-English.BIN",
]

CONTROL_TAG_PATTERN = re.compile(
    r"(<[^>]+>|\$[A-Za-z0-9_]+|%[0-9]*[sdif]|{[0-9]+}|\\[nrt]|&[a-zA-Z0-9#]+;)",
    re.IGNORECASE,
)

SWF_MAGIC_HEADS = (b"FWS", b"CWS", b"ZWS", b"GFX", b"CFX")


def classify_payload_evidence(path: str, data: bytes, extracted_strings: List[str], control_tags: List[str]) -> Tuple[str, str, Dict[str, Any]]:
    """Determines resource type and format from payload inspection and evidence.

    Returns:
        Tuple of (resource_type, detected_format, evidence_dict).
    """
    header_hex = data[:8].hex() if data else ""
    evidence: Dict[str, Any] = {
        "header_hex_8": header_hex,
        "byte_count": len(data),
        "string_count": len(extracted_strings),
        "tag_count": len(control_tags),
        "swf_signature": None,
    }

    # Check for direct Scaleform / SWF signatures
    for sig in SWF_MAGIC_HEADS:
        if data.startswith(sig):
            sig_name = sig.decode("latin1", "replace")
            evidence["swf_signature"] = sig_name
            return "Scaleform GFx UI Screen", f"Scaleform Movie ({sig_name})", evidence

    # Check for dialogue / audio streams
    if "Radio" in path or "Dialogue" in path or "Speech" in path:
        return "Dialogue / Audio Cue Buffer", "UFG Dialogue Binary Resource (.BIN)", evidence

    # UI Screens
    if "Screens" in path or path.endswith(".BIN"):
        return "UI Screen Resource", "UFG Proprietary Binary Screen Package (.BIN)", evidence

    return "Binary Asset Resource", "UFG Proprietary Binary Container", evidence


def extract_strings_and_tags(data: bytes, min_len: int = 3) -> tuple[List[str], List[str], str]:
    """Extracts printable strings, detected control tags, and encoding from binary data.

    Returns:
        Tuple of (strings_list, detected_control_tags, encoding_name).
    """
    encoding = "UTF-8"

    # Try extracting UTF-8 strings
    extracted: List[str] = []
    tags_found: Set[str] = set()

    # Match printable ASCII / UTF-8 sequences
    matches = re.findall(rb"[\x20-\x7e\xc0-\xff]{" + str(min_len).encode() + rb",}", data)
    for m in matches:
        try:
            s = m.decode("utf-8")
            extracted.append(s)
            for tag in CONTROL_TAG_PATTERN.findall(s):
                tags_found.add(tag)
        except UnicodeDecodeError:
            try:
                s = m.decode("latin1")
                extracted.append(s)
                encoding = "Latin-1 / UTF-8"
                for tag in CONTROL_TAG_PATTERN.findall(s):
                    tags_found.add(tag)
            except Exception:
                pass

    return extracted, sorted(tags_found), encoding


def inspect_text_resources(
    archives: List[BigArchive],
    candidate_paths: Optional[List[str]] = None,
) -> List[TextResourceInfo]:
    """Inspects text and screen BIN resources across the provided archives.

    Args:
        archives: List of opened BigArchive instances.
        candidate_paths: Optional list of relative asset paths to inspect.

    Returns:
        List of TextResourceInfo objects.
    """
    paths_to_check = candidate_paths or KNOWN_TEXT_RESOURCES
    results: List[TextResourceInfo] = []

    for path in paths_to_check:
        h = qsymbol_hash(path)
        found_entry: Optional[BigEntry] = None
        found_archive: Optional[BigArchive] = None

        for arch in archives:
            e = arch.find_by_hash(h)
            if e is not None:
                found_entry = e
                found_archive = arch
                break

        if found_entry and found_archive:
            raw_data = found_archive.read_raw_entry(found_entry)
            decomp_data = found_archive.extract_entry(found_entry, decompress=True)

            strings, control_tags, encoding = extract_strings_and_tags(decomp_data)
            res_type, det_format, evidence = classify_payload_evidence(path, decomp_data, strings, control_tags)
            magic_hex = decomp_data[:8].hex() if decomp_data else ""

            results.append(
                TextResourceInfo(
                    resource_path=path,
                    archive_name=found_archive.archive_name,
                    symbol_hash_hex=found_entry.symbol_hex,
                    offset=found_entry.offset,
                    size=found_entry.size,
                    uncompressed_size=len(decomp_data),
                    resource_type=res_type,
                    detected_format=det_format,
                    header_magic_hex=magic_hex,
                    encoding=encoding,
                    extracted_strings_count=len(strings),
                    sample_strings=strings[:10],
                    control_tags_detected=control_tags,
                    evidence=evidence,
                )
            )

    return results
