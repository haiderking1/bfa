# BFA

BFA is a native game localization pipeline for Arabic support.

## Pipeline

```text
JSON -> SQLite (WAL) -> AI translation -> JSON
```

The importer recursively extracts non-empty JSON string values while preserving
JSON paths. Object keys, numbers, booleans, arrays, and other structure remain
unchanged. Repeated source strings are deduplicated and translated once.

## Project layout

```text
src/
├── bfa/
│   ├── cli.py                 # Command-line interface
│   ├── config.py              # .env and runtime settings
│   ├── json_codec.py          # JSON traversal and reconstruction
│   ├── models.py              # Shared domain dataclasses
│   └── translation_service.py # Batching and concurrency orchestration
├── providers/
│   └── opencode.py            # OpenCode-compatible API client
└── sqlite/
    ├── repository.py          # SQLite persistence and JSON document mapping
    └── schema.py              # Tables and indexes
```

## Configuration

Copy your OpenCode Go API key into the ignored `.env` file:

```env
OPENCODE_API_KEY=your_key_here
OPENCODE_BASE_URL=https://opencode.ai/zen/go/v1
OPENCODE_MODEL=deepseek-v4-flash
OPENCODE_THINKING=disabled
BFA_WORKERS=100
BFA_BATCH_SIZE=50
```

The translation request uses the OpenAI-compatible SDK and explicitly sends
DeepSeek's non-thinking setting.

## Commands

Import a JSON file:

```bash
uv run bfa import game.json --database translations.sqlite
```

Translate pending strings:

```bash
uv run bfa translate --database translations.sqlite
```

Export the translated JSON:

```bash
uv run bfa export translated.json \
  --database translations.sqlite \
  --source game.json
```

Or run the complete pipeline:

```bash
uv run bfa pipeline game.json translated.json \
  --database translations.sqlite
```

Failed batches remain in SQLite and are retried by a later `translate` run.
