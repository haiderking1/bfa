"""Glyph generator modules for BFA font extension."""

from __future__ import annotations

from tooling.models import GlyphSpec
from tooling.glyph_generators.arrows import get_arrow_specs
from tooling.glyph_generators.navigation import get_navigation_specs
from tooling.glyph_generators.controls import get_control_specs
from tooling.glyph_generators.decoration import get_decoration_specs
from tooling.glyph_generators.legal_currency import get_legal_currency_specs


def get_all_glyph_specs() -> list[GlyphSpec]:
    """Retrieve all requested glyph specifications."""
    specs: list[GlyphSpec] = []
    specs.extend(get_arrow_specs())
    specs.extend(get_navigation_specs())
    specs.extend(get_control_specs())
    specs.extend(get_decoration_specs())
    specs.extend(get_legal_currency_specs())
    return specs
