"""Domain models for font extension tooling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class GlyphSpec:
    """Specification for adding or verifying a glyph in the BFA font."""

    unicode_cp: int
    char: str
    name: str
    advance_width: int
    category: str
    draw_fn: Callable[[Any], None] | None = None
    description: str = ""


@dataclass
class ValidationReport:
    """Structured report of font validation checks."""

    is_valid: bool = True
    passed_checks: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def add_pass(self, check_name: str, message: str = "") -> None:
        self.passed_checks.append(f"{check_name}: {message}" if message else check_name)

    def add_fail(self, check_name: str, message: str) -> None:
        self.is_valid = False
        self.failed_checks.append(f"{check_name}: {message}")

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)
