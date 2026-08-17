"""CLI entry point for building and validating the extended BFA font."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from tooling.glyph_generators import get_all_glyph_specs
from tooling.patcher import patch_font
from tooling.render import render_test_sheet
from tooling.validator import validate_font


def build_and_validate_font(
    input_path: Path,
    output_path: Path,
    backup_path: Path | None = None,
    render_preview_path: Path | None = None,
) -> bool:
    """Build extended BFA font, optionally backup, and run full verification."""
    print(f"=== Extending BFA Font ===")
    print(f"Input font:  {input_path}")
    print(f"Output font: {output_path}")

    # Step 1: Backup if requested
    if backup_path:
        print(f"Creating backup at: {backup_path}")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, backup_path)

    # Step 2: Retrieve glyph specifications
    specs = get_all_glyph_specs()
    print(f"Loaded {len(specs)} glyph specifications to add/extend.")

    # Step 3: Patch font
    patch_font(input_path, output_path, specs)
    print(f"Font patched and saved to: {output_path}")

    # Step 4: Validate font
    print("\n=== Validating Patched Font ===")
    report = validate_font(output_path)
    for check in report.passed_checks:
        print(f"  [PASS] {check}")
    for warn in report.warnings:
        print(f"  [WARN] {warn}")
    for fail in report.failed_checks:
        print(f"  [FAIL] {fail}")

    # Step 5: Render preview sheet if requested
    if render_preview_path:
        print(f"\n=== Rendering Visual Inspection Sheet ===")
        render_test_sheet(output_path, render_preview_path)
        print(f"Preview sheet saved to: {render_preview_path}")

    if not report.is_valid:
        print("\n[ERROR] Font validation failed!")
        return False

    print("\n[SUCCESS] Font extended and all verification checks passed successfully.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Extend BFA font with game UI symbols.")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("fonts/bfa.ttf"),
        help="Path to input BFA font",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("fonts/bfa.ttf"),
        help="Path to output extended font",
    )
    parser.add_argument(
        "--backup",
        "-b",
        type=Path,
        default=Path("/tmp/bfa_backup/bfa.ttf"),
        help="Backup destination outside repository",
    )
    parser.add_argument(
        "--preview",
        "-p",
        type=Path,
        default=Path("fonts/bfa_preview.png"),
        help="Path to output visual test preview image",
    )

    args = parser.parse_args()
    success = build_and_validate_font(
        input_path=args.input,
        output_path=args.output,
        backup_path=args.backup,
        render_preview_path=args.preview,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
