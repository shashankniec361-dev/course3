# Supply Chain Risk Investigation — Project Module Exercises

You build one project across three cumulative exercises. Each exercise's
`starter/` is the previous exercise's `solution/`, so nothing resets. By the end
of Exercise 3 you have the complete working system.

| Exercise | You build | Verify |
|---|---|---|
| `01-claim-readers` | The `Claim` model and the four source readers | `pytest tests/test_readers.py` |
| `02-memory-briefing` | The shared vector store and the synthesis briefing | `pytest tests/test_memory.py tests/test_synthesis.py` |
| `03-resilient-coordinator` | The timeout path and the resilient coordinator | `pytest tests/` |

## Setup (per exercise)

Each exercise folder is a self-contained Python package. From a `starter/` or
`solution/` directory:

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

The Meridian source corpus (`data/`) and recorded news fixtures (`fixtures/`)
ship with every stage, so the tests and the CLI run offline with no API key. The
first run downloads the local embedding model (about 90 MB), then caches it.

## Run the finished tool

From `03-resilient-coordinator/solution/`:

```bash
.venv/bin/supply-chain-investigate meridian --offline
.venv/bin/supply-chain-investigate meridian --offline --simulate-timeout
```

The `starter/` of each exercise contains `# TODO:` markers at every place you
write code. The matching `solution/` is the finished state to compare against.
