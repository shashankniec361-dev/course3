# Exercise 3 (Starter): When a Source Goes Dark

The readers, the store, and the briefing are complete. Now make the
investigation survive a failing source and wire the whole pipeline together.

## Where to write code

- `supply_chain_risk/readers.py` — add the timeout path to `read_logistics`
  that returns partial results inside a `FailureContext` instead of raising.
- `supply_chain_risk/coordinator.py` — write `investigate`: run every reader,
  recover locally from failures, annotate gaps, and vectorize only successful
  claims.

Every spot is marked with a `# TODO:` comment.

## Setup and verify

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -q
```

This exercise completes the project, so the full suite should pass. Then watch
recovery end to end:

```bash
.venv/bin/supply-chain-investigate meridian --offline --simulate-timeout
```
