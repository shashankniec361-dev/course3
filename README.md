# Claude AI Engineer — Evaluation and Observability

Source-of-truth repository for the project modules in the **Claude AI Engineer: Evaluation and Observability** course (`cd15552`). The course is about building Claude-powered extraction and investigation pipelines you can *trust* — schemas that distinguish "the document said so" from "the document was silent," retry loops that tell recoverable failures from futile ones, independent review passes, deterministic human-in-the-loop routing, and resilient multi-source synthesis.

Each top-level folder is a self-contained project module built across a sequence of cumulative, test-driven exercises. Every exercise ships a `starter/` you fill in (marked with `# TODO:`) and a `solution/` reference, with acceptance criteria pinned down by a pytest suite. Each exercise's `starter/` is the previous exercise's `solution/`, so nothing resets — by the final exercise you have the complete working system.

## Projects

### [Build a Resilient Mortgage Document Extraction System](Build%20a%20Resilient%20Mortgage%20Document%20Extraction%20System/)

You are the senior AI engineer at Meridian Home Lending. Build a mortgage-document extractor whose JSON Schema encodes what underwriting can trust: nullable unions, enum-plus-`other` spillover, and per-document-type `required` lists. Then orchestrate a two-pass classify-then-extract flow with forced `tool_choice`, write the extractor system prompt, and validate mathematical consistency across the extracted fields.

- `01-design-resilient-extraction-schema/` — Design the resilient extraction JSON Schema and tools (`pytest tests/test_us01_schema.py`).
- `02-orchestrate-two-pass-tool-choice/` — Classify-then-extract pipeline with forced `tool_choice` (`pytest tests/test_us02_pipeline.py`).
- `03-write-extractor-system-prompt/` — Author the extractor system prompt (`pytest tests/test_us03_prompts.py`).
- `04-validate-mathematical-consistency/` — Cross-field mathematical consistency validation (`pytest tests/test_us04_validator.py`).

### [Build a Validated, Routed Insurance Policy Extraction Pipeline](Build%20a%20Validated,%20Routed%20Insurance%20Policy%20Extraction%20Pipeline/)

Ingest insurance policy renewal documents, validate them, and route each to auto-approve or human review. Build a retry loop that distinguishes recoverable (`format` / `consistency`) failures from irrecoverable (`missing_source`) ones, add SLA-driven batch submission, an independent reviewer with a within-policy integration pass, and deterministic HITL routing with stratified sampling and calibration.

- `01-retry-with-error-feedback/` — Retry with error feedback and futile-retry escalation (`pytest tests/test_us01_retry.py`).
- `02-batch-and-sla/` — Batch processing with SLA-driven submission frequency (`pytest tests/test_us02_batch.py`).
- `03-independent-review/` — Independent reviewer and within-policy integration pass (`pytest tests/test_us03_review.py`).
- `04-hitl-routing/` — Deterministic HITL routing with stratified sampling and calibration (`pytest tests/`).

### [Investigate Supply Chain Risk with Multi-Source Synthesis](Investigate%20Supply%20Chain%20Risk%20with%20Multi-Source%20Synthesis/)

Build a supply-chain risk investigator over the Meridian source corpus: one `Claim` shape for every source, four source readers, a shared vector store, and a synthesis briefing that stays honest about what the sources do and don't support. Then make the coordinator resilient to a source going dark mid-run via a timeout path.

- `01-claim-readers/` — The `Claim` model and the four source readers (`pytest tests/test_readers.py`).
- `02-memory-briefing/` — Shared vector store and synthesis briefing (`pytest tests/test_memory.py tests/test_synthesis.py`).
- `03-resilient-coordinator/` — Timeout path and resilient coordinator (`pytest tests/`).

## Folder layout

Every exercise pairs starter code with a solution, and each side carries its own `README.md`:

```bash
<project>/
└── <NN-exercise-name>/        # numbered, cumulative exercise step
    ├── starter/               # self-contained Python package with TODO blocks to fill in
    │   ├── README.md          # exercise instructions, requirements, verify command
    │   ├── pyproject.toml
    │   ├── <package>/         # the source you complete
    │   ├── fixtures/ or data/ # offline document corpus + recorded API responses
    │   └── tests/             # acceptance tests for this exercise
    └── solution/              # byte-identical to the next exercise's starter, fully implemented
```

## Running an exercise

Each exercise's `README.md` is authoritative, but every project follows the same shape. From a `starter/` (or `solution/`) directory, create a virtual environment, install in editable mode with dev extras, then run the scoped verify command from that exercise's README:

```bash
cd "<project>/<exercise>/starter"
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -v   # or the scoped test path named in the exercise README
```

The starter suite fails until the `# TODO:` blocks are resolved; the exercise is complete when its verify command passes cleanly.

**Offline by default.** The document corpora (`fixtures/` / `data/`) and recorded Anthropic responses ship with every stage, so tests and the CLIs run offline with no API key. Tests marked `@pytest.mark.live` need a real `ANTHROPIC_API_KEY` and are intentionally outside the verify gate. The Supply Chain project downloads a local embedding model (~90 MB) on first run, then caches it.

## License

See [LICENSE.md](LICENSE.md). Educational content © Udacity, Inc., licensed CC BY-NC-ND 4.0 except where noted.
