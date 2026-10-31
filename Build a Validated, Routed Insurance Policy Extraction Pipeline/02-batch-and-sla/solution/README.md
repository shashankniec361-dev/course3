# Exercise 2 — Solution: Batch Processing With SLA-Driven Submission Frequency

`submission_frequency` and `process_with_resubmission` are now implemented. The
monthly renewal cycle can be submitted as one batch with `custom_id` correlation,
per-item failures are isolated and retried in a single follow-up batch, and an
explicit guard raises `SLATooTightError` when batching cannot meet the SLA.

This directory ALSO contains the scaffold for Exercise 3 (`reviewer.py` +
`tests/test_us03_review.py`) — so this is byte-identical to
`exercises/03-independent-review/starter/`.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_us01_retry.py tests/test_us02_batch.py -v
```

Target: 24 passed, 2 skipped.

## What changed since `02-batch-and-sla/starter/`

- `policy_extractor/batch.py` — `submission_frequency` and `process_with_resubmission` bodies implemented.

## What's pre-positioned for the next exercise

- `policy_extractor/reviewer.py` (TODO stubs for `build_review_messages`, `independent_review`,
  `integration_pass`, `_check_coverage_limit_vs_endorsements`, `_check_endorsements_vs_exclusions`;
  `REVIEW_TOOL`, `REVIEWER_SYSTEM_PROMPT`, dataclasses, `_parse_field_reviews`, `has_disagreement`,
  `_check_premium_vs_components`, `_bigrams`, `_STOPWORDS` are fully implemented).
- `tests/test_us03_review.py` — 13 tests covering reviewer independence and the integration pass.
