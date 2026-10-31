# Evidence Pack — submission structure

Assemble your submission as a single folder (or `.zip`) with this layout. Fill `reflection-brief.md`
as you go — capture the evidence at the moment you run each system, not from memory afterward.

## Where each system lives

The three reference systems ship in the course repo (`cd15552 Claude AI Engineer Evaluation and
Observability`), one project per top-level folder. Run each from the `solution/` of that project's
**final** exercise (the `starter/` folders hold the fill-in exercises; the capstone runs the finished
`solution/`). Install with `pip install -e ".[dev]"` from inside the solution dir, which puts the
console command on your `PATH`.

| Evidence folder | Course project → final-exercise `solution/` | Console command |
|---|---|---|
| `01-policy-pipeline/` | `Build a Validated, Routed Insurance Policy Extraction Pipeline/04-hitl-routing/solution/` | `policy-extractor` |
| `02-mortgage-extraction/` | `Build a Resilient Mortgage Document Extraction System/04-validate-mathematical-consistency/solution/` | `mortgage-extract` |
| `03-supply-chain/` | `Investigate Supply Chain Risk with Multi-Source Synthesis/03-resilient-coordinator/solution/` | `supply-chain-investigate` |

```
capstone-submission/
├── reflection-brief.md            # the completed brief (provided — fill it in)
├── environment.txt                # `python3 --version` + OS; how you set up the venvs
├── perturbation-log.md            # one experiment per system (provided — fill it in)
│
├── 01-policy-pipeline/
│   ├── tests.txt                  # full `pytest -v` output (passing count visible)
│   ├── static-checks.txt          # `mypy` + `ruff` output
│   ├── pipeline-run.txt           # terminal capture of `policy-extractor pipeline data/policies/`
│   ├── routing_decisions.json     # generated routing output (the pipeline's --routing-out default)
│   ├── calibration-report.txt     # output of `calibration_report.py` (sliced, provided)
│   └── screenshots/               # at least one screenshot of a run
│
├── 02-mortgage-extraction/
│   ├── tests.txt
│   ├── static-checks.txt
│   ├── extract-run.txt            # `mortgage-extract <document>` output
│   ├── discrepancy-run.txt        # a run where the validator reports a discrepancy
│   └── screenshots/
│
└── 03-supply-chain/
    ├── tests.txt
    ├── static-checks.txt
    ├── investigation-run.txt      # `supply-chain-investigate meridian --offline`
    ├── briefing.*                 # generated briefing (3 sections)
    ├── timeout-run.txt            # `... --simulate-timeout` (graceful degradation)
    └── screenshots/
```

Plain text (`.txt`) captures and screenshots are both fine. The only hard rule: a reviewer should be
able to open any artifact you cite in the reflection brief and find the exact value you quoted.

## Perturbation log

A ready-to-fill `perturbation-log.md` is provided with one block per system. For **each** system, make
one deliberate change to an input or configuration, predict what will happen, run it, and record what
actually happened.

Good perturbations to start from (invent your own for stand-out credit):

- **Policy pipeline** — blank out a required field in one document so the information is genuinely
  absent. Confirm it escalates with a single API call and no invented value.
- **Mortgage extraction** — edit a stated total so it no longer matches the line items. Confirm the
  consistency validator flags the discrepancy.
- **Supply chain** — run with `--simulate-timeout`. Confirm the failed source is annotated as
  Incomplete and the run still finishes.
