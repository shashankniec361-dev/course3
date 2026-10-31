# Exercise 2 (Starter): From Claims to an Honest Briefing

Your readers from Exercise 1 are complete. Now build the shared vector store and
the synthesis step that turns claims into a coverage-tagged briefing.

## Where to write code

- `supply_chain_risk/memory.py` — the unique collection name in `__init__`,
  `add_claims` (embed + store provenance as metadata), `search`, `related_to`.
- `supply_chain_risk/synthesis.py` — `group_by_metric`, `_disagree`,
  `_classify`, `_escalation`, `_render_finding`, `build_briefing`.

Every spot is marked with a `# TODO:` comment.

## Setup and verify

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_memory.py tests/test_synthesis.py -q
```

The first run downloads the local embedding model (about 90 MB), then caches it.
The reader tests from Exercise 1 stay green throughout.
