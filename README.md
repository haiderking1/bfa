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

Choose a translation provider in the ignored `.env` file. For local Ollama
translation with the installed Gemma model:

```env
BFA_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma4:e2b
BFA_WORKERS=1
BFA_BATCH_SIZE=10
BFA_MAX_CHUNK_CHARACTERS=4000
```

For OpenCode instead:

```env
BFA_PROVIDER=opencode
OPENCODE_API_KEY=your_key_here
OPENCODE_BASE_URL=https://opencode.ai/zen/go/v1
OPENCODE_MODEL=deepseek-v4-flash
OPENCODE_THINKING=disabled
BFA_WORKERS=100
BFA_BATCH_SIZE=50
```

BFA supports both the remote OpenCode provider and a local Ollama provider.
The local profile is recommended for large jobs when API usage is limited:

```env
BFA_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma4:e2b
BFA_WORKERS=1
BFA_BATCH_SIZE=10
BFA_MAX_CHUNK_CHARACTERS=4000
```

The Ollama provider uses the native `/api/chat` endpoint with thinking disabled.
The OpenCode provider uses the OpenAI-compatible SDK and explicitly sends
DeepSeek's non-thinking setting. Both providers pass through the same SQLite,
validation, and output packing pipeline.

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

## Sleeping Dogs: Definitive Edition

The first full game adapter reads localization BINs from the Steam install,
stages them in SQLite, translates, then patches `UI.big`/`UI.bix` from a
one-time backup so the stock executable loads Arabic. The executable is
never replaced and no Proton launch options are required. Use `--no-install`
to write only the isolated workspace.

```bash
uv run bfa sleeping-dogs inspect \
  --game-path /path/to/SleepingDogsDefinitiveEdition

uv run bfa sleeping-dogs import \
  --game-path /path/to/SleepingDogsDefinitiveEdition \
  --database translations.sqlite

uv run bfa sleeping-dogs translate \
  --database translations.sqlite

uv run bfa sleeping-dogs build \
  --database translations.sqlite \
  --output build/sleeping_dogs_ar
```

`inspect` and `import` discover `Data\UI\Localization\{LANG}_{SECTION}.bin`
resources from BIG/BIX qSymbol paths. `translate` uses the configured provider
(`BFA_PROVIDER=opencode` or `BFA_PROVIDER=ollama`) and the corresponding
settings. `build` writes validated UILocalizationChunk BINs under the output
directory, preserving internal resource paths.
