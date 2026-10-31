# Exercise 1 — Solution: Retry With Error Feedback and Futile-Retry Escalation

The retry loop, validator, and feedback-block assembly are now implemented.
The single-document extractor distinguishes recoverable failures (`format` /
`consistency`) from irrecoverable ones (`missing_source`) and retries the
former with the prior offending value fed verbatim back to the model.

This directory ALSO contains the scaffold for Exercise 2 (`batch.py` + `tests/test_us02_batch.py`)
— so this is byte-identical to `exercises/02-batch-and-sla/starter/`.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_us01_retry.py -v
```

Target: 13 passed, 1 skipped.

## What changed since `01-retry-with-error-feedback/starter/`

- `policy_extractor/extractor.py` — `build_extraction_messages` `if prior_attempts:` block now assembles the `<prior_attempt>` feedback blocks.
- `policy_extractor/validator.py` — all four functions implemented with the three-stage ordering (missing → format → consistency).
- `policy_extractor/retry.py` — `extract_with_retry` loop fully implemented.

## What's pre-positioned for the next exercise

- `policy_extractor/batch.py` (TODO stubs for `submission_frequency` and `process_with_resubmission`; the SDK adapter and `dry_run_sample` are fully implemented).
- `tests/test_us02_batch.py` — 12 tests covering batch correlation, resubmission, and SLA math. They will fail until you complete Exercise 2.
- `policy_extractor/__main__.py` — now wires up the `batch` subcommand alongside `extract`.
