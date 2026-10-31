"""CLI entry point for the policy-extractor pipeline.

At this stage the `extract` and `batch` subcommands are wired up.
Later exercises will add `pipeline` once the reviewer and routing layers exist.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

from anthropic import Anthropic

from policy_extractor.batch import (
    AnthropicBatchClient,
    DryRunSampleResult,
    dry_run_sample,
    process_with_resubmission,
)
from policy_extractor.client import AnthropicMessagesClient
from policy_extractor.records import (
    ExtractionOutcome,
    PolicyExtraction,
)
from policy_extractor.retry import extract_with_retry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="policy-extractor")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Extract a single policy document (US-01).")
    p_extract.add_argument("document", type=Path)
    p_extract.add_argument("--policy-id", required=True)
    p_extract.add_argument("--max-retries", type=int, default=3)

    p_batch = sub.add_parser("batch", help="Submit a batch of policies (US-02).")
    p_batch.add_argument("policies_dir", type=Path)
    p_batch.add_argument(
        "--dry-run-sample", type=int, default=3,
        help="Run N policies real-time first as a sample. Use 0 to skip the sample.",
    )
    p_batch.add_argument(
        "--sample-threshold", type=float, default=0.7,
        help="Minimum sample first-pass success rate to authorise the full batch.",
    )
    p_batch.add_argument("--force", action="store_true", help="Skip the sample-rate gate.")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr,
    )

    if args.command == "extract":
        return _cmd_extract(args)
    if args.command == "batch":
        return _cmd_batch(args)
    return 2


def _cmd_extract(args: argparse.Namespace) -> int:
    text = args.document.read_text()
    client = AnthropicMessagesClient(Anthropic())
    outcome = extract_with_retry(
        client=client,
        policy_id=args.policy_id,
        document_text=text,
        max_retries=args.max_retries,
    )
    print(json.dumps(_serialize_outcome(outcome), indent=2, sort_keys=True))
    return 0 if isinstance(outcome, PolicyExtraction) else 1


def _load_policies(policies_dir: Path) -> list[tuple[str, str]]:
    policies = []
    for path in sorted(policies_dir.glob("POL-*.txt")):
        policies.append((path.stem, path.read_text()))
    if not policies:
        raise FileNotFoundError(f"No POL-*.txt files in {policies_dir}.")
    return policies


def _cmd_batch(args: argparse.Namespace) -> int:
    policies = _load_policies(args.policies_dir)
    extractor_client = AnthropicMessagesClient(Anthropic())

    if args.dry_run_sample > 0:
        sample = dry_run_sample(
            extractor_client=extractor_client,
            policies=policies,
            sample_size=args.dry_run_sample,
        )
        _print_sample(sample)
        if not args.force and sample.first_pass_success_rate < args.sample_threshold:
            print(
                f"Sample first-pass success rate {sample.first_pass_success_rate:.0%} "
                f"below threshold {args.sample_threshold:.0%}; aborting. Use --force to override.",
                file=sys.stderr,
            )
            return 3

    batch_client = AnthropicBatchClient(Anthropic())
    results = process_with_resubmission(
        batch_client=batch_client,
        extractor_client=extractor_client,
        policies=policies,
    )
    print(json.dumps({pid: _serialize_outcome(o) for pid, o in results.items()}, indent=2))
    return 0


def _serialize_outcome(outcome: ExtractionOutcome) -> dict[str, object]:
    if isinstance(outcome, PolicyExtraction):
        return {"kind": "extraction", **asdict(outcome)}
    return {"kind": "escalation", **asdict(outcome)}


def _print_sample(sample: DryRunSampleResult) -> None:
    print(json.dumps(asdict(sample), indent=2), file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
