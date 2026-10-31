# Exercise 3. Write the Extractor System Prompt (Starter)

Picking up from Exercise 2: your pipeline works end-to-end against the cached fixtures, but the prompt layer is doing the bare minimum. The model still fabricates fields the document never stated, still echoes "about 2,400 sq ft" as a string instead of normalizing to `2400`, and still silently "corrects" arithmetic discrepancies it should be surfacing. In this exercise you build the prompt that actually constrains the model's behavior to what the underwriting team needs.

## A note on the starter you're seeing

Exercise 2's solution shipped with a working `prompts.py` so the pipeline tests could run offline. For this exercise we have re-stubbed `prompts.py` back to its TODO form, your job is to *write* the production prompt. The chain isn't byte-identical at this one file because the LO for Exercise 3 lives in `prompts.py`, and you need a place to write it.

## What you'll write

Open `mortgage_extractor/prompts.py`. Three TODO regions, then two prompt-assembly functions.

| File | What you implement |
|---|---|
| `mortgage_extractor/prompts.py` | `NORMALIZATION_RULES` constant; `_CATEGORICAL_CRITERIA` numbered list (verbatim first rule); `_FEW_SHOT_EXAMPLES` (four `<example>` blocks each with `<reasoning>`); `extractor_system_prompt()` and `income_verification_system_prompt()` assembly |

## What's already in the package

Everything from Exercise 2's solution, plus:

- `tests/test_us03_prompts.py`, acceptance tests for this exercise. The structural tests (`test_ac_03_01`, `test_ac_03_02`, `test_ac_03_02b`, `test_ac_03_05`) run offline against your prompt strings. The behavioral tests (`test_ac_03_03`, `test_ac_03_04`) run the pipeline against `income_missing_bonus.txt` and `appraisal_informal_sqft.txt` and assert the model returns `None` and `2400` respectively, those pass when the cache is warmed for your prompts' request hashes.

## Setup

If you haven't already:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

For the two behavioral tests (`test_ac_03_03`, `test_ac_03_04`) you will need either (a) the recorded responses that match your prompt's exact text, or (b) `ANTHROPIC_API_KEY` set so the recording client can make a live call on first run. The cache shipped with the reference solution matches one specific prompt string, if you write a different one, your first run will hit the API in `auto` mode and record fresh responses. The structural tests don't make any API calls.

## Verify

```bash
.venv/bin/pytest tests/test_us03_prompts.py -v
```

Keep prior tests green too:

```bash
.venv/bin/pytest tests/ -v
```

## Watch for

- **The first rule is verbatim.** Item 1 of `_CATEGORICAL_CRITERIA` is asserted as the exact substring `"Return null for any field not explicitly stated in the document. Do not infer, default, or fabricate."` Copy it character-for-character. This rule does the heavy lifting against fabrication and is the difference between a pipeline underwriting can trust and one they can't.
- **Reasoning is what makes few-shot examples teach.** Input/output pairs without `<reasoning>` give the model the format but not the rationale. Each example must contain a `<reasoning>` block. Write the *why*, for the missing-bonus example, write something like "bonus_ytd is null because the document says no bonus this year; fabricating zero would imply zero earned, not zero reported."
- **One source of truth for normalization.** `NORMALIZATION_RULES` gets interpolated into every extractor system prompt. Don't write the rules twice. The tests check that the *same* `prompts.NORMALIZATION_RULES` constant appears in both the income and appraisal prompts.
