# Exercise 2. Orchestrate Two-Pass Tool Choice (Solution)

This folder is the project state after Exercise 2: a working two-pass `Pipeline`, an end-to-end CLI, and a `prompts.py` that's a placeholder for what you'll build in Exercise 3. Use it to compare against your own work.

## What's complete in this folder

Everything from Exercise 1, plus:

- `mortgage_extractor/pipeline.py`, `Pipeline.run`, `Pipeline.classify_document`, `Pipeline.extract`, and `_single_tool_use_block`.
- `mortgage_extractor/__main__.py`, the CLI entry point.
- `mortgage_extractor/prompts.py`, the production prompts (final version). You will rebuild this in Exercise 3; it ships final here so the cached responses replay deterministically against Exercise 2's tests.
- `scripts/regenerate_fixtures.py`, refreshes `fixtures/recorded_responses/*.json` against the live API.
- `tests/test_us02_pipeline.py`, acceptance tests for this exercise.

## What's not here yet

`mortgage_extractor/validator.py` arrives in Exercise 4. Until then, the CLI's `validation` block always reports `consistent: true` because the validator is a no-op.

## Verify

```bash
.venv/bin/pytest tests/test_us01_schema.py tests/test_us02_pipeline.py -v
```

Then try the CLI on a real document:

```bash
mortgage-extract fixtures/documents/appraisal_informal_sqft.txt
```

The `extraction` block shows the structured record. The `validation` block shows `consistent: true` (vacuously, no validator yet).

## Key design moves

- **Forced classify, `any` extract.** Pass 1's `tool_choice={"type":"tool","name":"classify_document"}` makes the model produce a routing decision and nothing else. Pass 2's `tool_choice={"type":"any"}` lets the model pick the right doc-type extractor or escape to `flag_for_review`, but it cannot fall back to free text.
- **Two `DocumentType.OTHER` guards.** `run()` short-circuits after classify (the common path). The defensive guard at the top of `extract()` catches the rare path where a caller invokes `extract()` directly with `OTHER`, without it they get a confusing "unexpected tool call" error instead of the proper `UnsupportedDocumentTypeError`.
- **The `tool_use` block is where structured output lives.** `_single_tool_use_block` walks `response.content` filtering for `ToolUseBlock` instances. The model's text output is intentionally ignored.
