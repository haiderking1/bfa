"""Discover measured Scaleform text boxes from Sleeping Dogs UI screens."""

from __future__ import annotations

from typing import List, Sequence

from bfa.games.sleeping_dogs.archive import BigArchive
from bfa.games.sleeping_dogs.font_package import is_uiscreen_chunk, parse_uiscreen_font_package
from bfa.games.sleeping_dogs.hash import qsymbol_hash
from bfa.games.sleeping_dogs.text_resources import KNOWN_SCREEN_RESOURCES
from bfa.layout.gfx_text import movie_stage_pixels, text_field_boxes
from bfa.layout.models import TextFieldBox

MAX_SCREEN_UNCOMPRESSED_SIZE = 400_000


def discover_text_field_boxes(archive: BigArchive) -> List[TextFieldBox]:
    """Reads UIScreenChunk CFX movies and returns every DefineEditText rectangle.

    Widths and heights come from the SWF RECT on the field, converted from twips.
    Instance paths come from PlaceObject2 and PlaceObject3 names, not guessed constants.
    """
    path_by_hash = {qsymbol_hash(path): path for path in KNOWN_SCREEN_RESOURCES}
    boxes: list[TextFieldBox] = []
    for entry in archive.entries:
        if entry.size <= 0 or entry.size > MAX_SCREEN_UNCOMPRESSED_SIZE:
            continue
        try:
            data = archive.extract_entry(entry, decompress=True)
        except (OSError, ValueError):
            continue
        if not is_uiscreen_chunk(data):
            continue
        try:
            package = parse_uiscreen_font_package(data)
        except ValueError:
            continue
        stage_width, stage_height = movie_stage_pixels(package.movie.header)
        screen_path = path_by_hash.get(
            entry.symbol_hash,
            rf"Data\UI\Screens\{package.debug_name}.BIN",
        )
        boxes.extend(
            text_field_boxes(
                package.movie.tags,
                screen_path=screen_path,
                screen_name=package.debug_name,
                stage_width_px=stage_width,
                stage_height_px=stage_height,
            )
        )
    boxes.sort(key=lambda item: (item.screen_path, item.instance_path, item.character_id))
    return boxes


def boxes_for_instance(boxes: Sequence[TextFieldBox], instance_path: str) -> List[TextFieldBox]:
    """Returns fields whose PlaceObject path equals or ends with ``instance_path``."""
    suffix = instance_path.lower()
    return [
        box
        for box in boxes
        if box.instance_path.lower() == suffix or box.instance_path.lower().endswith("/" + suffix)
    ]
