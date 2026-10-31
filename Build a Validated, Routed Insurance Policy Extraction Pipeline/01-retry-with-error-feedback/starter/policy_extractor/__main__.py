"""CLI entry point for the policy-extractor pipeline.

At this stage only the `extract` subcommand is wired up. Later exercises
will add `batch` and `pipeline`.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path

from anthropic import Anthropic

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

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr,
    )

    if args.command == "extract":
        return _cmd_extract(args)
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


def _serialize_outcome(outcome: ExtractionOutcome) -> dict[str, object]:
    if isinstance(outcome, PolicyExtraction):
        return {"kind": "extraction", **asdict(outcome)}
    return {"kind": "escalation", **asdict(outcome)}


if __name__ == "__main__":
    sys.exit(main())
