from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

from .config import ConfigurationError, Settings
from sqlite.repository import TranslationDatabase

from .translation_service import translate_pending


def _database_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("bfa.sqlite"),
        help="SQLite staging database path (default: bfa.sqlite)",
    )


def _translation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-language", help="Target language (default: Arabic)")
    parser.add_argument("--workers", type=int, help="Concurrent translation workers")
    parser.add_argument("--batch-size", type=int, help="Strings per translation request")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bfa",
        description="Native game localization pipeline: JSON -> SQLite -> translated JSON",
    )
    commands = parser.add_subparsers(dest="command")

    import_parser = commands.add_parser("import", help="Import a JSON document into SQLite")
    import_parser.add_argument("input", type=Path)
    _database_argument(import_parser)

    translate_parser = commands.add_parser("translate", help="Translate pending SQLite strings")
    _database_argument(translate_parser)
    _translation_arguments(translate_parser)

    export_parser = commands.add_parser("export", help="Pack translated strings back into JSON")
    export_parser.add_argument("output", type=Path)
    export_parser.add_argument("--source", type=Path, help="Source JSON when DB has multiple documents")
    export_parser.add_argument("--target-language", default="Arabic")
    _database_argument(export_parser)

    pipeline_parser = commands.add_parser("pipeline", help="Import, translate, and export in one command")
    pipeline_parser.add_argument("input", type=Path)
    pipeline_parser.add_argument("output", type=Path)
    _database_argument(pipeline_parser)
    _translation_arguments(pipeline_parser)

    return parser


def _settings(args: argparse.Namespace) -> Settings:
    settings = Settings.from_environment()
    updates = {}
    if args.target_language:
        updates["target_language"] = args.target_language
    if args.workers is not None:
        if args.workers <= 0:
            raise ConfigurationError("--workers must be a positive integer")
        updates["workers"] = args.workers
    if args.batch_size is not None:
        if args.batch_size <= 0:
            raise ConfigurationError("--batch-size must be a positive integer")
        updates["batch_size"] = args.batch_size
    return replace(settings, **updates)


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _run(args: argparse.Namespace) -> int:
    if args.command == "import":
        with TranslationDatabase(args.database) as database:
            result = database.import_document(args.input)
            _print_json(
                {
                    "document_id": result.document_id,
                    "source_path": str(result.source_path),
                    "unique_strings": result.string_count,
                    "occurrences": result.occurrence_count,
                    "journal_mode": database.journal_mode,
                }
            )
        return 0

    if args.command == "translate":
        settings = _settings(args)
        with TranslationDatabase(args.database) as database:
            summary = asyncio.run(translate_pending(database, settings))
            _print_json(asdict(summary))
        return 1 if summary.failed else 0

    if args.command == "export":
        with TranslationDatabase(args.database) as database:
            database.export_document(args.output, args.target_language, args.source)
            _print_json({"output": str(args.output), "target_language": args.target_language})
        return 0

    if args.command == "pipeline":
        settings = _settings(args)
        with TranslationDatabase(args.database) as database:
            imported = database.import_document(args.input)
            summary = asyncio.run(translate_pending(database, settings))
            database.export_document(args.output, settings.target_language, args.input)
            _print_json(
                {
                    "input": str(imported.source_path),
                    "output": str(args.output),
                    "unique_strings": imported.string_count,
                    "occurrences": imported.occurrence_count,
                    "translation": asdict(summary),
                    "journal_mode": database.journal_mode,
                }
            )
        return 1 if summary.failed else 0

    build_parser().print_help()
    return 0


def main() -> int:
    try:
        return _run(build_parser().parse_args())
    except (ConfigurationError, OSError, ValueError) as exc:
        print(f"bfa: {exc}", file=sys.stderr)
        return 1
