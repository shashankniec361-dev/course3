# Exercise 1. Design the Resilient Extraction Schema (Solution)

This folder is the project state after Exercise 1: a working `mortgage_extractor/schema.py` and `mortgage_extractor/tools.py` with the resilient design described in the exercise. Use it to compare against your own work.

## What's complete in this folder

- `mortgage_extractor/schema.py`, `mortgage_data_schema()`, `list_nullable_fields()`, and the three categorical enum constants.
- `mortgage_extractor/tools.py`, the four tool definitions and `_required_sections_for()` helper.
- `mortgage_extractor/{config,errors,models,client}.py`, provided as scaffolding.
- `fixtures/`, `tests/test_us01_schema.py`, provided.

## What's not here yet

The pipeline orchestration, prompts, validator, CLI, and recorded-response refresh script all arrive in Exercises 2 through 4. Running `mortgage-extract` from this stage doesn't work yet, the entry point doesn't exist.

## Verify

```bash
.venv/bin/pytest tests/test_us01_schema.py -v
```

All five `test_ac_01_*` tests should pass.

## Key design moves

- **Top-level `required` lists only what every document type carries.** `borrower` and `property` and `loan` are all in the schema's top-level `required`, but `income` is not, only income-verification documents carry it. `tools.doc_type_extractor()` further narrows the required list per document type, so an appraisal extractor doesn't force borrower/loan and an income-verification extractor doesn't force loan/property.
- **Three problems → three idioms.** Plain optional (not in `required`), nullable union (`type: ["<base>", "null"]`), and `enum + "other" + *_detail`. Each handles a different failure mode: schema absence, value absence, and categorical drift.
- **`flag_for_review` is a second tool, not a fallback path.** Exercise 2 will register it alongside the doc-type extractor so `tool_choice="any"` has a meaningful choice. With one tool registered, `"any"` collapses to forced.
