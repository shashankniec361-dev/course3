# Reflection Brief — Evaluation and Observability Capstone

**Name:**
**Date:**

> Ground every answer in your own run. When a question asks for a number, file name, or line, paste
> it from your artifacts — a reviewer should be able to find it. Answers that are correct in the
> abstract but cite nothing do not meet the bar. Keep it short and specific.

---

## 0. Environment

| Field | Value |
|---|---|
| OS & version | |
| Python version | |
| Date run | |
| Ran any system live? (which) | |

---

## 1. Validated, routed pipeline

| Evidence | Value |
|---|---|
| Passing test count | |
| Routing output file | |
| auto_approve / human_review / spot_check counts | / / |

**1a. Retry boundary.** From your perturbation run (a required field removed), paste the escalation
record. How many API calls did the system make, and why is retrying a futile case worse than
escalating it?

> 

**1b. Reading the router.** Pick one `human_review` record from your routing output. Which of the
three signals (confidence, reviewer, integration) sent it to a human? If you had trusted the model's
confidence alone, what would have happened?

> 

**1c. Where the aggregate lies.** Run the calibration snippet. Quote the one cell whose accuracy lags
its confidence, plus the overall figure. What does slicing by `policy_type × field` catch that a
single number hides?

> 

---

## 2. Schema-enforced two-pass extraction

| Evidence | Value |
|---|---|
| Passing test count | |
| Document run | |
| Classified type | |

**2a. Two guarantees.** Paste your discrepancy-run output. Tool use already forces valid JSON, yet the
validator still catches a bad sum. Why are these two different guarantees? Name one error each cannot
catch.

> 

**2b. Refusing to fabricate.** Run on a document missing a field. Paste that field's output. Why null
instead of an invented value? Point to the schema choice that allows it.

> 

**2c. Normalization.** Quote one field where the source text and extracted value differ in format
("about 2,400 sq ft" → `2400`). Why normalize at extraction time rather than downstream?

> 

---

## 3. Multi-source synthesis

| Evidence | Value |
|---|---|
| Passing test count | |
| Briefing file | |
| Section the conflict landed in | |

**3a. Annotate, don't arbitrate.** Quote one conflicting-metric pair from your briefing — both values,
sources, dates. Give one way a reader is better served by the preserved conflict than by a single
reconciled number.

> 

**3b. Source goes dark.** Run with `--simulate-timeout`. Paste the part of the briefing showing the
failed source. How is "unreachable" handled differently from "nothing to report," and why does the run
still finish?

> 

**3c. Dates as a guardrail.** Quote two claims about the same supplier with different dates. How does
requiring a date stop a time difference from reading as a contradiction?

> 

---

## 4. Synthesis

**4a. One principle.** Name the single moment in your runs (system + artifact) where *evaluate the
output, don't trust the model's word* most clearly caught something a trusting design would have
shipped.

> 

**4b. Confidence ≠ correctness.** Pick the system where this mattered most, and explain why using
something you observed.

> 

**4c. Apply it.** Describe a real workflow where an LLM pulls structured results from messy input.
Which pattern — validated retry with escalation, independent review with deterministic routing, or
provenance-preserving conflict annotation — would you reach for first, and what would you instrument
to know when it broke?

> 
