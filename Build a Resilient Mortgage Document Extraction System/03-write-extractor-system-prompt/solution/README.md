# Exercise 3. Write the Extractor System Prompt (Solution)

This folder is the project state after Exercise 3: the production extractor prompt is now driving the pipeline. Use it to compare against your own work.

## What's complete in this folder

Everything from Exercise 2, plus:

- `mortgage_extractor/prompts.py`, `NORMALIZATION_RULES`, `_CATEGORICAL_CRITERIA` (verbatim first rule), four contrastive `<example>` blocks with `<reasoning>`, and the prompt-assembly functions.
- `tests/test_us03_prompts.py`, acceptance tests for this exercise.

## What's not here yet

`mortgage_extractor/validator.py` arrives in Exercise 4. Until then, the CLI's `validation` block reports `consistent: true` vacuously.

## Verify

```bash
.venv/bin/pytest tests/ -v
```

All three test files should pass.

Live-fire check:

```bash
mortgage-extract fixtures/documents/income_missing_bonus.txt | tee /tmp/out.json
python3 -c "import json,sys; r=json.load(open('/tmp/out.json')); print('bonus_monthly:', r['extraction']['income']['bonus_monthly'])"
```

You should see `bonus_monthly: None`, the model returned `null` because the document doesn't state a bonus, and your `_CATEGORICAL_CRITERIA` first rule prevented fabrication.

## Key design moves

- **First rule, verbatim.** `"Return null for any field not explicitly stated in the document. Do not infer, default, or fabricate."` is item 1, character-for-character. It does the bulk of the work against fabrication. The remaining rules disambiguate categorical edge cases.
- **Reasoning in every example.** `<reasoning>` makes the *why* visible to the model and to test reviewers. Input/output pairs alone teach the format; `<reasoning>` teaches the rule the format encodes.
- **One `NORMALIZATION_RULES` constant.** The same string is referenced from both the income and appraisal extractor prompts. Changing a normalization rule means editing one place. The module docstring in `schema.py` and `models.py` both point back to it.
