# Exercise 1 (Starter): One Claim Shape for Every Source

Build the `Claim` model and the four readers so every source converges on one
dated, provenance-carrying shape.

## Where to write code

- `supply_chain_risk/models.py` — declare the `Claim` fields (required
  `source_date`, validated `confidence`, the `candidates` tuple).
- `supply_chain_risk/readers.py` — `read_audit`, `read_logistics`,
  `_logistics_claims`, `read_quality`, `read_news`.
- `supply_chain_risk/news_extraction.py` — the system prompt and the
  `AnthropicNewsExtractor.extract` structured-output call.

Every spot is marked with a `# TODO:` comment.

## Setup and verify

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_readers.py -q
```

All reader tests should pass when you are done. The data corpus and recorded
fixtures are already provided under `data/` and `fixtures/`.
