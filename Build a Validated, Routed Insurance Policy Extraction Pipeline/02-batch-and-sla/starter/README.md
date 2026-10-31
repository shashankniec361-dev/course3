# Exercise 2 — Starter: Batch Processing With SLA-Driven Submission Frequency

This starter is byte-identical to `exercises/01-retry-with-error-feedback/solution/`. You
already have the retry loop from Exercise 1 working; now you're plugging the same per-item
extraction into the Message Batches API for a 50% cost discount on the monthly cycle,
and writing the helper that derives submission frequency from an SLA.

## What you'll build in this exercise

1. `submission_frequency(sla_hours, batch_eta_hours)` — pure helper returning the minimum
   batches-per-day needed to meet an SLA. Raises `SLATooTightError` when the SLA is
   shorter than the batch's own completion time.
2. `process_with_resubmission(...)` — the two-round batch flow:
   - **Round 1:** submit all policies. For each result, validate the model's output.
     Successful + clean → final. Successful + `missing_source` → escalate.
     Successful + `format`/`consistency` → queue with prior_attempts feedback for Round 2.
     Errored/expired/canceled → queue without feedback.
   - **Round 2:** resubmit the queue with the Round-1 errors threaded in via
     `prior_attempts`. Treat any second-round failure as terminal escalation.

## Where the TODOs are

| File | TODO sites | What you write |
|---|---|---|
| `policy_extractor/batch.py` | `submission_frequency` (the `head_room` math) | Compute `max(1, ceil(24 / (head_room + batch_eta_hours)))`, with an explicit `SLATooTightError` guard when SLA < batch ETA |
| `policy_extractor/batch.py` | `process_with_resubmission` | The two-round flow described above |

Pre-written for you (read but don't change):
- `policy_extractor/batch.py` — `AnthropicBatchClient` (the SDK adapter), `BatchClient` Protocol, `BatchItemResult`, `BatchStatus`, `SLATooTightError`, `_build_request`, `_extract_tool_input`, and `dry_run_sample`.
- All Exercise 1 modules (extractor, validator, retry, etc.) — the per-item retry semantics
  ride on top of Exercise 1.
- `tests/test_us02_batch.py` — 12 tests covering correlation by `custom_id`, isolated-failure resubmission, and the SLA math.

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_us01_retry.py tests/test_us02_batch.py -v
```

Target: 24 passed, 2 skipped (the two skipped are `@pytest.mark.live`).

## Smoke test (optional — needs `ANTHROPIC_API_KEY` set)

```bash
.venv/bin/policy-extractor batch data/policies/ --dry-run-sample 3
```

The dry-run gate runs 3 policies real-time, prints a `pattern_summary`, and only
authorises the full batch if the first-pass success rate clears the threshold.

## Onward

When tests pass, move to `exercises/03-independent-review/starter/`.
