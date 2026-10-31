# Exercise 4 — Starter: Deterministic HITL Routing With Stratified Sampling and Calibration

This starter is byte-identical to `exercises/03-independent-review/solution/`. You now have
extraction with retry, batch processing, and the independent reviewer + integration pass
working. The final exercise wires those signals into a deterministic routing decision and
adds the drift-detection plumbing.

## What you'll build in this exercise

1. `route_extraction(...)` — classifies each extraction as `auto_approve` or `human_review`
   based on three independent signals: extractor field-confidence threshold, reviewer
   agreement, and integration findings. **Any one** of those three triggers `human_review`.
2. `apply_stratified_spot_check(...)` — promotes a fraction of `auto_approve` decisions to
   `spot_check`, grouped by `policy_type` so small strata (e.g., umbrella policies) never
   silently disappear from the drift-detection sample.
3. `calibration_report(...)` — a sliced `policy_type × field` reliability table with
   mean predicted confidence, observed accuracy, and Brier score per cell, plus an overall
   Brier score.

## Where the TODOs are

| File | TODO sites | What you write |
|---|---|---|
| `policy_extractor/routing.py` | `route_extraction` | Compute `fields_below` + `disagreements` + `integration_failures`; route to `human_review` if any is non-empty, else `auto_approve` |
| `policy_extractor/routing.py` | `apply_stratified_spot_check` | Bucket auto-approves by `policy_type`, promote `max(1, ceil(sample_pct * n))` per stratum |
| `policy_extractor/routing.py` | `calibration_report` | Bucket labels by `(policy_type, field)`, compute Brier per cell + overall |

Pre-written for you (read but don't change):
- `policy_extractor/routing.py` — `RoutingDecision`, `CalibrationLabel`, `CalibrationCell`, `CalibrationReport`, `DEFAULT_CONFIDENCE_THRESHOLD`, `Decision`, and `write_routing_decisions`.
- All Exercise 1 + 2 + 3 modules (extractor, validator, retry, batch, reviewer, etc.).
- `tests/test_us04_routing.py` — 9 tests covering the three-input determinism, stratified sampling, and the calibration report.

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/ -v
```

Target: 45 passed, 3 skipped (the three skipped are `@pytest.mark.live`).

## Smoke test (optional — needs `ANTHROPIC_API_KEY` set)

```bash
.venv/bin/policy-extractor pipeline data/policies/ --routing-out /tmp/routing.json --spot-check-pct 0.2 --seed 42
```

This runs extract → review → integration → route end-to-end over all 10 bundled policies,
prints the summary (auto-approve / human-review / spot-check counts + pattern summary),
and writes the routing decisions to `/tmp/routing.json`.

## You're done

When all 45 tests pass, you have the full Insurance Policy Extraction Pipeline. The
`solution/` directory in this folder is the reference implementation — compare your work
against it.
