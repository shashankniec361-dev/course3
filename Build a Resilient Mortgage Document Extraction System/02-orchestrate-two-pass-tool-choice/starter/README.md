# Exercise 2. Orchestrate Two-Pass Tool Choice (Starter)

You finished Exercise 1 with a resilient schema and a set of typed tool definitions. Picking up from there: the pipeline still needs the orchestration that actually *uses* those tools, one forced call to route the document, one `tool_choice="any"` call to extract.

## What you'll write

Open `mortgage_extractor/pipeline.py`. Implement the three `Pipeline` methods and the `_single_tool_use_block` helper. Nothing else needs to be touched in this exercise.

| File | Methods you implement |
|---|---|
| `mortgage_extractor/pipeline.py` | `Pipeline.run`, `Pipeline.classify_document`, `Pipeline.extract`, `_single_tool_use_block` |

## What's already in the package

All of Exercise 1's solution, plus:

- `mortgage_extractor/__main__.py`, the CLI entry point. Provided so you can run `mortgage-extract path/to/doc.txt` and watch your pipeline work end-to-end.
- `mortgage_extractor/prompts.py`, the production extractor prompt (final version). Exercise 3 will have you rebuild this, you are reading the finished version here only because the cached fixtures in `fixtures/recorded_responses/` were recorded against these prompts, and Exercise 2's tests need offline-deterministic API calls. Treat it as a black box for now.
- `scripts/regenerate_fixtures.py`, driver to refresh the cache against the live API.
- `tests/test_us02_pipeline.py`, the acceptance tests for this exercise.

## Setup

If you haven't already from Exercise 1:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

You won't need a live API key for the verify command, the cached responses cover every payload your finished pipeline will send.

## Verify

```bash
.venv/bin/pytest tests/test_us02_pipeline.py -v
```

Also keep Exercise 1's tests green:

```bash
.venv/bin/pytest tests/test_us01_schema.py tests/test_us02_pipeline.py -v
```

Once both files pass, try the CLI:

```bash
mortgage-extract fixtures/documents/appraisal_informal_sqft.txt
```

You should see a JSON payload with `extraction` and `validation` blocks. (Validation will always say `consistent: true` until Exercise 4, the validator is still a stub today.)

## Watch for

- **Forced vs. any.** Pass 1 sets `tool_choice={"type":"tool","name":"classify_document"}`, the model has no choice but to route. Pass 2 sets `tool_choice={"type":"any"}`, the model must pick a tool, but it gets to choose which. `"any"` is only meaningful with at least two tools registered, which is why pass 2 registers the doc-type extractor *and* `flag_for_review`. Without the escape hatch, `"any"` collapses to forced.
- **Two short-circuits for `DocumentType.OTHER`.** `run()` short-circuits after classify, so `extract()` is never called on `OTHER`. The defensive guard at the top of `extract()` does it again for callers who skip `run()` and call `extract()` directly, without that second guard they get a confusing "unexpected tool call" error instead of the proper `UnsupportedDocumentTypeError`.
- **Read the `tool_use` block, not the text.** The structured output you want is in the `ToolUseBlock` content block. Walking the response with `[b for b in response.content if isinstance(b, ToolUseBlock)]` and reading `.input` is the cookbook pattern. Do not parse `response.content[0].text`.
