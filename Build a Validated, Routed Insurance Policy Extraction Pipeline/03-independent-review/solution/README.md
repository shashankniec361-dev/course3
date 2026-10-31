# Exercise 3 — Solution: Independent Reviewer and Within-Policy Integration Pass

The reviewer call (built from only the source + extraction, no extractor messages)
and the three-check integration pass are now implemented. The pipeline can detect
contradictions like `coverage_limit < sum(endorsements.limit)` and endorsement/exclusion
clauses that overlap.

This directory ALSO contains the scaffold for Exercise 4 (`routing.py` + `tests/test_us04_routing.py`)
— so this is byte-identical to `exercises/04-hitl-routing/starter/`.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/test_us01_retry.py tests/test_us02_batch.py tests/test_us03_review.py -v
```

Target: 36 passed, 3 skipped.

## What changed since `03-independent-review/starter/`

- `policy_extractor/reviewer.py` — five functions now implemented.

## What's pre-positioned for the next exercise

- `policy_extractor/routing.py` (TODO stubs for `route_extraction`, `apply_stratified_spot_check`,
  `calibration_report`; `RoutingDecision`, `CalibrationLabel`, `CalibrationCell`, `CalibrationReport`,
  `DEFAULT_CONFIDENCE_THRESHOLD`, and `write_routing_decisions` are fully implemented).
- `tests/test_us04_routing.py` — 9 tests covering routing determinism, stratified sampling, and calibration.
- `policy_extractor/__main__.py` — now wires up the `pipeline` subcommand that chains extract → review → integration → route end-to-end.
