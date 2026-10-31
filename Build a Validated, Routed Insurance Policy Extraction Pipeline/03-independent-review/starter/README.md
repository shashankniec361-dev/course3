# Exercise 3 — Starter: Independent Reviewer and Within-Policy Integration Pass

This starter is byte-identical to `exercises/02-batch-and-sla/solution/`. You now have
extraction with retry + batch processing working. This exercise adds the second-pass QA
layer: an independent Claude reviewer (a stronger model, with NO access to the
extractor's prompts or reasoning) plus a pure within-policy integration pass that catches
cross-field contradictions the per-field reviewer can't see.

## What you'll build in this exercise

1. `build_review_messages(...)` — constructs the reviewer's `(messages, system)` from
   ONLY the source document + the proposed extraction. No extractor messages, no
   `<thinking>`, no tool-call ids.
2. `independent_review(...)` — calls the reviewer with `REVIEW_TOOL` forced, parses the
   per-field judgement, returns a `ReviewResult`.
3. `integration_pass(extraction)` — runs three cross-field consistency checks and
   returns a list of `IntegrationFinding`s.
4. `_check_coverage_limit_vs_endorsements(extraction)` — emits a `fail` finding when
   `coverage_limit < sum(endorsements.limit)`.
5. `_check_endorsements_vs_exclusions(extraction)` — fuzzy bigram-overlap match (with
   the pre-built `_STOPWORDS` and `_bigrams` helpers) that flags when an endorsement
   and an exclusion describe the same coverage.

## Where the TODOs are

| File | TODO sites | What you write |
|---|---|---|
| `policy_extractor/reviewer.py` | `build_review_messages` | The reviewer prompt — built from `(source_document, extracted_record)` and nothing else |
| `policy_extractor/reviewer.py` | `independent_review` | The reviewer call + parse loop |
| `policy_extractor/reviewer.py` | `integration_pass` | Orchestrate the three checks; skip `_check_premium_vs_components` when it returns `None` |
| `policy_extractor/reviewer.py` | `_check_coverage_limit_vs_endorsements` | Sum endorsement limits and compare against `coverage_limit` |
| `policy_extractor/reviewer.py` | `_check_endorsements_vs_exclusions` | Use `_bigrams()` to detect content-word overlap between each endorsement name and each exclusion |

Pre-written for you (read but don't change):
- `policy_extractor/reviewer.py` — `REVIEW_TOOL`, `REVIEWER_SYSTEM_PROMPT`, dataclasses (`FieldAgreement`, `ReviewResult`, `IntegrationFinding`), `has_disagreement`, `_parse_field_reviews`, `_check_premium_vs_components`, `_bigrams`, `_STOPWORDS`. (`_check_premium_vs_components` parallels the consistency check you wrote for the validator in Exercise 1 — handed over so you don't write the same logic twice.)
- All Exercise 1 + 2 modules (extractor, validator, retry, batch, etc.).
- `tests/test_us03_review.py` — 13 tests covering reviewer independence and the integration checks.

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_us01_retry.py tests/test_us02_batch.py tests/test_us03_review.py -v
```

Target: 36 passed, 3 skipped.

## Onward

When tests pass, move to `exercises/04-hitl-routing/starter/`.
