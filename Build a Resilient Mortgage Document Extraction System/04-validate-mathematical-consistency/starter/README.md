# Exercise 4. Validate Mathematical Consistency (Starter)

Picking up from Exercise 3: your pipeline now extracts structured records, returns `null` when documents are silent, and normalizes informal numerics. The last thing missing is the validator that catches the silent failure case, a paystub whose stated total doesn't equal the sum of its components. Today, those documents quietly land in the underwriter's queue with bad arithmetic. By the end of this exercise the pipeline will flag them before they get there.

## A note on the starter you're seeing

This starter carries forward Exercise 3's full solution byte-for-byte, with one exception: `Income.calculated_monthly_total` in `mortgage_extractor/models.py` has been re-stubbed back to TODO form. That property is the embodying construct for Arc LO 4, the absent-vs-zero distinction lives there, so you write it here even though `models.py` itself was provided in Exercise 1's scaffold.

## What you'll write

| File | What you implement |
|---|---|
| `mortgage_extractor/models.py` | The body of `Income.calculated_monthly_total` (the absent-vs-zero invariant) |
| `mortgage_extractor/validator.py` | The body of `validate(extraction, *, tolerance)` |

## What's already in the package

Everything from Exercise 3's solution, plus:

- `tests/test_us04_validator.py`, acceptance tests plus a JSON round-trip test. All offline-deterministic except `test_ac_04_04_real_paystub_with_sum_mismatch_is_flagged`, which runs the pipeline against `income_sum_mismatch.txt` (cached response shipped).

## Setup

If you haven't already:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Verify

```bash
.venv/bin/pytest tests/test_us04_validator.py -v
```

Then the whole arc:

```bash
.venv/bin/pytest tests/ -v
.venv/bin/mypy mortgage_extractor/
.venv/bin/ruff check mortgage_extractor/ tests/
```

Finally try the CLI on the sum-mismatch fixture to see the validator do its real job:

```bash
mortgage-extract fixtures/documents/income_sum_mismatch.txt
echo "exit code: $?"
```

The exit code is `1` because the document is inconsistent. The JSON `validation` block names the discrepancy. That's the artifact the underwriting team needs.

## Watch for

- **None vs. 0.0 is load-bearing.** `Income.calculated_monthly_total` returns `None` when every component is `None`, not `0.0`. The validator only diffs when *both* sides are not None, so an income-less appraisal correctly says "no comparison to make" rather than "$0 vs stated $0 = consistent." If you return `0.0` from the empty case, every income-less document gets a free pass and real bugs hide.
- **Mixing monthly and YTD breaks the comparison.** The `Income` model has both `bonus_monthly` and `bonus_ytd`; only the `*_monthly` components belong in the sum. Cross-summing monthly and YTD gives you a number that has no meaningful relationship to `stated_monthly_total` and would surface discrepancies that aren't there. Stick to the five `*_monthly` fields.
- **Tolerance has a default for a reason.** `DEFAULT_TOLERANCE_USD` is `$1.00`. That absorbs cent-level OCR rounding (the same $4,500.00 document showing up as `$4,499.99` after OCR shouldn't trip a discrepancy). Setting tolerance to `0.0` produces false positives on every rounding artifact. Configure per-call when a domain actually demands zero tolerance.
