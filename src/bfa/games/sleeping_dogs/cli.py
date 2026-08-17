"""CLI tool for Sleeping Dogs: Definitive Edition format discovery and inspection."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bfa.games.sleeping_dogs.inspector import (
    DEFAULT_GAME_PATH,
    SleepingDogsInspector,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only format inspector for Sleeping Dogs: Definitive Edition",
    )
    parser.add_argument(
        "--game-dir",
        type=Path,
        default=DEFAULT_GAME_PATH,
        help=f"Path to Sleeping Dogs installation (default: {DEFAULT_GAME_PATH})",
    )
    parser.add_argument(
        "--output-json",
        "-o",
        type=Path,
        default=None,
        help="Path to save machine-readable JSON inspection report",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary text to standard output",
    )

    args = parser.parse_args(argv)

    try:
        inspector = SleepingDogsInspector(args.game_dir)
        report = inspector.inspect_all()

        if args.output_json:
            inspector.generate_report_json(args.output_json)
            print(f"Machine-readable report written to: {args.output_json}")

        if args.summary or not args.output_json:
            print("=" * 70)
            print("SLEEPING DOGS: DEFINITIVE EDITION FORMAT DISCOVERY REPORT")
            print("=" * 70)
            print(f"Game Directory: {report.game_install_dir}")
            print(f"Steam App ID:   {report.steam_app_id}")
            print(f"Language:       {report.game_language}")
            print(f"Archives Found: {len(report.archives)}")
            print(f"Total Entries:  {report.total_entries}")
            print(f"Compressed:     {report.total_compressed_entries}")
            print(f"Uncompressed:   {report.total_uncompressed_entries}")
            print("-" * 70)
            print("FONTS ENGLISH LOCATION:")
            for k, v in report.fonts_english_location.items():
                print(f"  {k:22s}: {v}")
            print("-" * 70)
            print("CONFIGURED ENGLISH FONTS (FontDefinition.xml):")
            for f in report.font_resource_metadata.configured_fonts:
                print(f"  - {f}")
            print("-" * 70)
            print(f"DISCOVERED TEXT & SCREEN RESOURCES ({len(report.text_resources)} found):")
            for res in report.text_resources[:15]:
                print(f"  [{res.archive_name:10s}] {res.resource_path:42s} ({res.size} bytes, {res.extracted_strings_count} strings)")
            print("-" * 70)
            print("PROTON COMPATIBILITY:")
            print(f"  Proton Available: {report.proton_compatibility.proton_available}")
            print(f"  Status: {report.proton_compatibility.notes}")
            print("=" * 70)

        return 0
    except Exception as exc:
        print(f"Error during inspection: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
