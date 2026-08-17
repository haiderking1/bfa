"""Inspection of Sleeping Dogs UI screens versus real localization BIN resources.

UI Screen BIN files (Data\\UI\\Screens\\*.BIN) are Scaleform/UFG UI packages.
They are not string tables. Printable-byte runs inside them are unknown binary
data, not localization text.

Localization lives in Data\\UI\\Localization\\{LANG}_{SECTION}.bin as
UILocalizationChunk resources (qChunk UID 0x90CE6B7A).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.hash import qsymbol_hash
from bfa.games.sleeping_dogs.localization import (
    encode_uilocalization_chunk,
    is_uilocalization_chunk,
    localization_control_tags,
    parse_uilocalization_chunk,
    table_binary_evidence,
)
from bfa.games.sleeping_dogs.models import BigEntry, LocalizationTable, TextResourceInfo

# UI screens and other non-localization BIN packages. These are catalogued for
# binary evidence only; they are not localization string tables.
KNOWN_SCREEN_RESOURCES: List[str] = [
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

# Authoritative localization resources used to prove the decoder. Additional
# UILocalizationChunk files can be inspected by passing explicit paths.
KNOWN_LOCALIZATION_RESOURCES: List[str] = [
    r"Data\UI\Localization\EN_BA_3b_Store.bin",
    r"Data\UI\Localization\DBG_LBL_BA_3b_Store.bin",
    r"Data\UI\Localization\RU_BA_3b_Store.bin",
    r"Data\UI\Localization\EN_BA_3_Chase.bin",
    r"Data\UI\Localization\EN_BA_5_BoatFight.bin",
    r"Data\UI\Localization\EN_GameplayDLCNinNP.bin",
    r"Data\UI\Localization\EN_Front-End.bin",
    r"Data\UI\Localization\EN_M_HGF_CM.bin",
    r"Data\UI\Localization\DBG_LBL_M_HGF_CM.bin",
]

# Retained name so existing imports keep referring to the screen catalog, which
# is binary evidence, not localization.
KNOWN_TEXT_RESOURCES: List[str] = KNOWN_SCREEN_RESOURCES

SWF_MAGIC_HEADS = (b"FWS", b"CWS", b"ZWS", b"GFX", b"CFX")
UI_SCREEN_CHUNK_UID = 0x442A39D9


def scan_unknown_printable_bytes(data: bytes, min_len: int = 4) -> List[str]:
    """Collects leftover printable byte runs from non-localization binaries.

    This is not localization extraction. The runs are unlabeled binary evidence
    and must not be treated as game text.
    """
    found: List[str] = []
    current = bytearray()
    for byte in data:
        if 0x20 <= byte <= 0x7E:
            current.append(byte)
        else:
            if len(current) >= min_len:
                found.append(bytes(current).decode("ascii"))
            current.clear()
    if len(current) >= min_len:
        found.append(bytes(current).decode("ascii"))
    return found


def classify_payload_evidence(
    path: str,
    data: bytes,
    extracted_strings: List[str],
    control_tags: List[str],
) -> Tuple[str, str, Dict[str, Any]]:
    """Classifies a BIN payload from header bytes and path. String counts are not proof of localization."""
    header_hex = data[:8].hex() if data else ""
    evidence: Dict[str, Any] = {
        "header_hex_8": header_hex,
        "byte_count": len(data),
        "decoded_localization_string_count": 0,
        "unknown_printable_count": len(extracted_strings),
        "tag_count": len(control_tags),
        "swf_signature": None,
        "is_uilocalization_chunk": is_uilocalization_chunk(data),
    }

    if is_uilocalization_chunk(data):
        evidence["decoded_localization_string_count"] = len(extracted_strings)
        evidence["unknown_printable_count"] = 0
        return (
            "UI Localization Chunk",
            "UFG UILocalizationChunk (qChunk 0x90CE6B7A)",
            evidence,
        )

    for sig in SWF_MAGIC_HEADS:
        if data.startswith(sig):
            sig_name = sig.decode("latin1", "replace")
            evidence["swf_signature"] = sig_name
            return "Scaleform GFx UI Screen", f"Scaleform Movie ({sig_name})", evidence

    if len(data) >= 4:
        chunk_id = int.from_bytes(data[:4], "little")
        if chunk_id == UI_SCREEN_CHUNK_UID:
            return (
                "UI Screen Resource",
                "UFG UIScreenChunk (qChunk 0x442A39D9)",
                evidence,
            )

    if "Radio" in path or "Dialogue" in path or "Speech" in path:
        return "Dialogue / Audio Cue Buffer", "UFG Dialogue Binary Resource (.BIN)", evidence

    if "Screens" in path or path.endswith(".BIN"):
        return "UI Screen Resource", "UFG Proprietary Binary Screen Package (.BIN)", evidence

    return "Binary Asset Resource", "UFG Proprietary Binary Container", evidence


def decode_localization_resource(data: bytes) -> LocalizationTable:
    """Parses a decompressed localization BIN. Raises ValueError if it is not verified text."""
    return parse_uilocalization_chunk(data)


def round_trip_localization_bytes(data: bytes) -> bytes:
    """Decode then re-encode a localization BIN with no string edits."""
    return encode_uilocalization_chunk(parse_uilocalization_chunk(data))


def inspect_text_resources(
    archives: List[BigArchive],
    candidate_paths: Optional[List[str]] = None,
) -> List[TextResourceInfo]:
    """Inspects screen packages and/or localization BINs.

    Screen packages contribute binary evidence only. Localization BINs contribute
    decoded UTF-8 strings only after the UILocalizationChunk parser verifies them.
    """
    paths_to_check = candidate_paths or (KNOWN_SCREEN_RESOURCES + KNOWN_LOCALIZATION_RESOURCES)
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

        if found_entry is None or found_archive is None:
            continue

        decomp_data = found_archive.extract_entry(found_entry, decompress=True)
        magic_hex = decomp_data[:8].hex() if decomp_data else ""

        decoded_strings: List[str] = []
        unknown_printable: List[str] = []
        control_tags: List[str] = []
        encoding = ""
        verified = False
        evidence: Dict[str, Any]
        loc_table: Optional[LocalizationTable] = None

        if is_uilocalization_chunk(decomp_data):
            loc_table = parse_uilocalization_chunk(decomp_data)
            decoded_strings = [entry.text for entry in loc_table.entries]
            tag_set: Set[str] = set()
            for text in decoded_strings:
                tag_set.update(localization_control_tags(text))
            control_tags = sorted(tag_set)
            encoding = loc_table.encoding
            verified = True
            res_type, det_format, evidence = classify_payload_evidence(
                path, decomp_data, decoded_strings, control_tags
            )
            evidence.update(table_binary_evidence(loc_table))
            if loc_table.string_pool_padding:
                evidence["string_pool_padding_hex"] = loc_table.string_pool_padding.hex()
        else:
            unknown_printable = scan_unknown_printable_bytes(decomp_data)
            res_type, det_format, evidence = classify_payload_evidence(
                path, decomp_data, unknown_printable, []
            )
            encoding = "n/a"

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
                extracted_strings_count=len(decoded_strings) if verified else 0,
                sample_strings=decoded_strings[:10],
                control_tags_detected=control_tags,
                evidence=evidence,
                decoded_localization_strings=decoded_strings,
                unknown_printable_data=unknown_printable,
                is_verified_localization=verified,
            )
        )

    return results
