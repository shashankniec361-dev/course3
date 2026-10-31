# Exercise 1 — Starter: Retry With Error Feedback and Futile-Retry Escalation

This is the bootstrap scaffold. You are starting an extraction pipeline that will eventually
ingest insurance policy renewal documents, validate them, and route them to
auto-approve or human review. This first exercise gets the single-document extractor
working with a retry loop that distinguishes recoverable failures from irrecoverable ones.

## What you'll build in this exercise

A `extract_with_retry` function that:

1. Calls the Anthropic Messages API with `tool_choice` forcing a structured extraction.
2. Validates the result with a typed `ValidationError` carrying `category` (`format` /
   `missing_source` / `consistency`) and a `detected_pattern` tag.
3. On `format` / `consistency` failure, appends the *prior offending value verbatim* to
   the retry prompt and tries again, up to `max_retries`.
4. On `missing_source` failure (the document genuinely doesn't carry the field), halts
   immediately and emits a `RetryFutileEscalation` — no further API calls.

## Where the TODOs are

| File | TODO sites | What you write |
|---|---|---|
| `policy_extractor/extractor.py` | `build_extraction_messages` — `if prior_attempts:` block | Build a `<prior_attempt>` block per prior attempt with the raw prior extraction + validator error |
| `policy_extractor/validator.py` | `validate_extraction`, `_check_required_present`, `_check_numeric_ranges`, `_check_premium_components_consistency` | Run the three checks in order; return the first `ValidationError` or `None` |
| `policy_extractor/retry.py` | `extract_with_retry` | The retry loop: call → validate → branch on `category` |

Pre-written for you (read but don't change):
- `policy_extractor/extractor.py` — `EXTRACT_POLICY_TOOL` schema, `SYSTEM_PROMPT`, `parse_tool_use`, and the first-attempt branch of `build_extraction_messages`.
- `policy_extractor/client.py`, `records.py`, `summary.py`, `__init__.py`, `__main__.py` — boundary, domain dataclasses, run-level aggregator, CLI.
- `data/policies/POL-2025-*.txt` (×10) and `data/policies/MANIFEST.json` — synthetic test fixtures (clean, missing-schedule, inconsistent-premium).
- `tests/conftest.py` — `RecordedClient`, message helpers, env loader.
- `tests/test_us01_retry.py` — 14 tests covering the LO's acceptance criteria.

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_us01_retry.py -v
```

Target: 13 passed, 1 skipped (the skipped test is `@pytest.mark.live` — it needs a real
`ANTHROPIC_API_KEY` and is intentionally out of scope for the verify gate).

## Smoke test (optional — needs `ANTHROPIC_API_KEY` set)

```bash
.venv/bin/policy-extractor extract data/policies/POL-2025-001.txt --policy-id POL-2025-001
```

## Onward

When tests pass, move to `exercises/02-batch-and-sla/starter/`. That starter is byte-identical
to this exercise's `solution/`, plus the scaffold for batch processing.
