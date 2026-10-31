# Exercise 1. Design the Resilient Extraction Schema (Starter)

You are the senior AI engineer at Meridian Home Lending. Your task in this exercise is to design the JSON Schema that every downstream extractor in the pipeline will share. The schema decides what counts as "the document said so" and what counts as "the document was silent." That distinction is the entire reason underwriting trusts the output downstream.

## What you'll write

Open `mortgage_extractor/schema.py` and `mortgage_extractor/tools.py`. Every TODO marker shows you where to make a decision. Nothing else in the package needs to be touched in this exercise.

| File | Functions you implement |
|---|---|
| `mortgage_extractor/schema.py` | `mortgage_data_schema()`, `list_nullable_fields()`, plus the `PROPERTY_TYPES` / `OCCUPANCY_TYPES` / `LOAN_PURPOSES` enum constants |
| `mortgage_extractor/tools.py` | `extract_mortgage_data()`, `classify_document()`, `doc_type_extractor()`, `flag_for_review()`, `_required_sections_for()` |

## What's already in the package

These modules are provided as scaffolding so you can start on the schema directly instead of writing boilerplate.

- `mortgage_extractor/config.py`, model defaults and fixture paths.
- `mortgage_extractor/errors.py`, domain exception classes for the pipeline (used in Exercise 2).
- `mortgage_extractor/models.py`. Pydantic typed result objects: `Borrower`, `Property`, `Loan`, `Income`, `MortgageExtraction`, `DocumentType`, `Discrepancy`, `ValidationReport`. The tests construct these to assert acceptance criteria.
- `mortgage_extractor/client.py`, the `RecordingClient` cache-and-replay wrapper around the Anthropic SDK. You don't call it in Exercise 1; Exercise 2 wires it into the pipeline.
- `fixtures/documents/*.txt`, three real-world-shaped mortgage documents.
- `fixtures/recorded_responses/*.json`, cached Anthropic responses keyed by request hash. The cache pre-loads responses for the final pipeline + final prompts so Exercises 2 through 4 can run offline.
- `tests/test_us01_schema.py`, the acceptance tests for this exercise.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

You will not need `ANTHROPIC_API_KEY` for Exercise 1, the schema tests are pure-structural and run entirely offline.

## Verify

```bash
.venv/bin/pytest tests/test_us01_schema.py -v
```

You're done when all five `test_ac_01_*` tests pass.

## Watch for

- **Required is a contract.** Every entry in a `required` list is something you are forcing the model to emit. When the document doesn't carry that field, the model fabricates rather than violate the contract. Mark a field required only when you can defend it across all three document types this schema serves.
- **Nullable union vs. optional vs. enum + "other".** Three different problems, three different tools:
  - "The field may not appear in the JSON at all" → leave it out of `required` and give it a plain `type`.
  - "The field will appear but its value can be unknown" → use `type: ["<base>", "null"]`.
  - "The field's value space will grow over time" → use `enum: [..., "other"]` and a sibling `*_detail` string for spillover.
- **Per-document-type `required` lists are configured in `tools.py`, not in `schema.py`.** Keep the schema's top-level `required` minimal; let `doc_type_extractor` narrow per type.
