"""CLI for the Sleeping Dogs: Definitive Edition localization adapter."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

from bfa.config import Settings
from bfa.fonts.asset import BFA_FONT_PATH
from bfa.games.sleeping_dogs.discover import discover_localization_resources
from bfa.games.sleeping_dogs.font_inject import inject_sleeping_dogs_font
from bfa.games.sleeping_dogs.inspector import (
    DEFAULT_GAME_PATH,
    SleepingDogsInspector,
)
from bfa.games.sleeping_dogs.publish import publish_sleeping_dogs
from bfa.games.sleeping_dogs.repository import SleepingDogsDatabase
from bfa.games.sleeping_dogs.translation import translate_pending


def add_sleeping_dogs_subcommands(parser: argparse.ArgumentParser) -> None:
    parser.set_defaults(sd_command=None)
    commands = parser.add_subparsers(dest="sd_command")

    inspect_parser = commands.add_parser(
        "inspect",
        help="Inspect archives and discover localization resources (read-only)",
    )
    _game_path_argument(inspect_parser)
    inspect_parser.add_argument(
        "--output-json",
        "-o",
        type=Path,
        default=None,
        help="Write the machine-readable inspection report to this path",
    )
    inspect_parser.add_argument(
        "--language",
        default="EN",
        help="Localization language prefix to discover (default: EN)",
    )

    import_parser = commands.add_parser(
        "import",
        help="Decode localization BINs into a SQLite staging database",
    )
    _game_path_argument(import_parser)
    _database_argument(import_parser)
    import_parser.add_argument(
        "--language",
        default="EN",
        help="Localization language prefix to import (default: EN)",
    )

    translate_parser = commands.add_parser(
        "translate",
        help="Translate pending strings, then pack and patch the game archives",
    )
    _database_argument(translate_parser)
    _game_path_argument(translate_parser)
    _publish_arguments(translate_parser)
    translate_parser.add_argument(
        "--no-publish",
        action="store_true",
        help="Translate only; skip packing and overlay install",
    )
    translate_parser.add_argument("--target-language", help="Target language (default: Arabic)")
    translate_parser.add_argument("--workers", type=int, help="Concurrent translation workers")
    translate_parser.add_argument("--batch-size", type=int, help="Maximum strings per translation request")
    translate_parser.add_argument(
        "--max-chunk-characters",
        type=int,
        help="Maximum source characters per request (default: 4000)",
    )

    build_parser = commands.add_parser(
        "build",
        help="Pack translations, inject BFA, and patch the stock UI archives",
    )
    _database_argument(build_parser)
    _game_path_argument(build_parser)
    _publish_arguments(build_parser)
    build_parser.add_argument(
        "--wrap-compressed",
        action="store_true",
        help="Wrap originally compressed resources in a PMCQ header",
    )

    fonts_parser = commands.add_parser(
        "fonts",
        help="Inject the BFA font into an isolated FontsEnglish.bin",
    )
    _game_path_argument(fonts_parser)
    fonts_parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/sleeping_dogs_ar"),
        help="Isolated output directory (default: build/sleeping_dogs_ar)",
    )
    _font_path_argument(fonts_parser)


def _game_path_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--game-path",
        type=Path,
        default=DEFAULT_GAME_PATH,
        help=f"Path to Sleeping Dogs: Definitive Edition (default: {DEFAULT_GAME_PATH})",
    )


def _font_path_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--font",
        type=Path,
        default=BFA_FONT_PATH,
        help=f"Path to the BFA font (default: {BFA_FONT_PATH})",
    )


def _publish_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/sleeping_dogs_ar"),
        help="Isolated output directory (default: build/sleeping_dogs_ar)",
    )
    _font_path_argument(parser)
    parser.add_argument(
        "--skip-font",
        action="store_true",
        help="Pack localization only; do not inject the BFA font",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Write the isolated overlay but do not patch the game archives",
    )


def _database_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("translations.sqlite"),
        help="SQLite staging database path (default: translations.sqlite)",
    )


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def run(args: argparse.Namespace, settings: Settings | None = None) -> int:
    command = args.sd_command
    if command == "inspect":
        return _run_inspect(args)
    if command == "import":
        return _run_import(args)
    if command == "translate":
        if settings is None:
            settings = Settings.from_environment()
            updates = {}
            if args.target_language:
                updates["target_language"] = args.target_language
            if args.workers is not None:
                if args.workers <= 0:
                    raise ValueError("--workers must be a positive integer")
                updates["workers"] = args.workers
            if args.batch_size is not None:
                if args.batch_size <= 0:
                    raise ValueError("--batch-size must be a positive integer")
                updates["batch_size"] = args.batch_size
            if args.max_chunk_characters is not None:
                if args.max_chunk_characters <= 0:
                    raise ValueError("--max-chunk-characters must be a positive integer")
                updates["max_chunk_characters"] = args.max_chunk_characters
            if updates:
                settings = replace(settings, **updates)
        return _run_translate(args, settings)
    if command == "build":
        return _run_build(args)
    if command == "fonts":
        return _run_fonts(args)
    parser = argparse.ArgumentParser(prog="bfa sleeping-dogs")
    add_sleeping_dogs_subcommands(parser)
    parser.print_help()
    return 0


def _run_inspect(args: argparse.Namespace) -> int:
    inspector = SleepingDogsInspector(args.game_path)
    report = inspector.inspect_all()
    discovered = discover_localization_resources(inspector.archives, language=args.language)
    compressed = sum(1 for item in discovered if item.is_compressed)
    entries = sum(len(item.table.entries) for item in discovered)

    payload = report.to_dict()
    payload["localization_discovery"] = {
        "language": args.language,
        "resources": len(discovered),
        "entries": entries,
        "compressed_resources": compressed,
        "direct_resources": len(discovered) - compressed,
        "resource_paths": [item.resource_path for item in discovered],
    }
    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Machine-readable report written to: {args.output_json}")

    print("=" * 70)
    print("SLEEPING DOGS: DEFINITIVE EDITION")
    print("=" * 70)
    print(f"Game Directory: {report.game_install_dir}")
    print(f"Steam App ID:   {report.steam_app_id}")
    print(f"Archives Found: {len(report.archives)}")
    print(f"Total Entries:  {report.total_entries}")
    print("-" * 70)
    print(f"LOCALIZATION DISCOVERY ({args.language}):")
    print(f"  Resources:     {len(discovered)}")
    print(f"  Entries:       {entries}")
    print(f"  Compressed:    {compressed}")
    print(f"  Direct:        {len(discovered) - compressed}")
    for item in discovered[:12]:
        kind = "compressed" if item.is_compressed else "direct"
        print(
            f"  [{item.archive_name:10s}] {item.resource_path} "
            f"({len(item.table.entries)} strings, {kind})"
        )
    if len(discovered) > 12:
        print(f"  ... {len(discovered) - 12} more")
    print("=" * 70)
    return 0


def _run_import(args: argparse.Namespace) -> int:
    from bfa.games.sleeping_dogs.archive import BigArchive

    game_path = Path(args.game_path)
    archives = []
    for bix_file in sorted(game_path.glob("*.bix")):
        big_file = bix_file.with_suffix(".big")
        if big_file.is_file():
            archives.append(BigArchive(bix_file, big_file))
    discovered = discover_localization_resources(archives, language=args.language)
    with SleepingDogsDatabase(args.database) as database:
        summary = database.import_resources(discovered, source_language=args.language)
        _print_json(
            {
                "database": str(args.database),
                "journal_mode": database.journal_mode,
                "source_language": summary.source_language,
                "resources": summary.resources,
                "entries": summary.entries,
                "compressed_resources": summary.compressed_resources,
                "direct_resources": summary.direct_resources,
            }
        )
    return 0


def _run_translate(args: argparse.Namespace, settings: Settings) -> int:
    def report_progress(done: int, total: int) -> None:
        print(
            f"\rTranslating: {done}/{total} strings "
            f"({done / total:.1%})",
            end="",
            file=sys.stderr,
            flush=True,
        )

    try:
        with SleepingDogsDatabase(args.database) as database:
            summary = asyncio.run(
                translate_pending(
                    database,
                    settings,
                    on_progress=report_progress,
                )
            )
            counts = database.counts()
            payload = {
                "translation": asdict(summary),
                "database": counts,
            }
            if not getattr(args, "no_publish", False):
                published = _publish(args, database)
                payload["publish"] = _publish_payload(published)
            _print_json(payload)
    finally:
        print(file=sys.stderr)
    return 1 if summary.failed else 0


def _run_build(args: argparse.Namespace) -> int:
    with SleepingDogsDatabase(args.database) as database:
        published = _publish(args, database)
        counts = database.counts()
    _print_json(_publish_payload(published))
    if published.pack.failed_resources:
        return 1
    if int(counts["resources"]) > 0 and published.pack.resources_written == 0:
        return 1
    return 0


def _publish(args: argparse.Namespace, database: SleepingDogsDatabase):
    return publish_sleeping_dogs(
        database,
        args.output,
        game_path=args.game_path,
        font_path=args.font,
        wrap_compressed=bool(getattr(args, "wrap_compressed", False)),
        inject_font=not bool(getattr(args, "skip_font", False)),
        install=not bool(getattr(args, "no_install", False)),
    )


def _publish_payload(published) -> dict:
    payload = asdict(published.pack)
    if published.font is not None:
        payload["font"] = asdict(published.font)
    if published.install is not None:
        payload["install"] = asdict(published.install)
    return payload


def _run_fonts(args: argparse.Namespace) -> int:
    summary = inject_sleeping_dogs_font(
        args.game_path,
        args.output,
        font_path=args.font,
    )
    _print_json(asdict(summary))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sleeping Dogs: Definitive Edition localization adapter",
    )
    add_sleeping_dogs_subcommands(parser)
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:
        print(f"bfa sleeping-dogs: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
