
"""Batch processing via the Message Batches API.

Components:
- BatchClient Protocol — normalised boundary so tests can stub
- AnthropicBatchClient — production adapter around anthropic.Anthropic().messages.batches
- submit / poll / collect — primitives
- process_with_resubmission — top-level flow: Batch 1 → validate → Batch 2
- dry_run_sample — validates a small N before authorising bulk batch
- submission_frequency — pure helper mapping SLA to batches-per-day
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from anthropic import Anthropic
from anthropic.types.messages import (
    MessageBatchErroredResult,
    MessageBatchExpiredResult,
    MessageBatchSucceededResult,
)

from policy_extractor.client import MessageClient
from policy_extractor.extractor import EXTRACT_POLICY_TOOL, build_extraction_messages
from policy_extractor.records import (
    ExtractionOutcome,
    PolicyExtraction,
    RetryFutileEscalation,
    ValidationError,
)
from policy_extractor.retry import build_extraction, extract_with_retry
from policy_extractor.summary import summarize_patterns
from policy_extractor.validator import validate_extraction

DEFAULT_EXTRACTOR_MODEL = "claude-haiku-4-5"
BATCH_POLL_INTERVAL_SECONDS = 5.0
BATCH_POLL_TIMEOUT_SECONDS = 86_400.0

BatchStatus = Literal["succeeded", "errored", "canceled", "expired"]


class SLATooTightError(ValueError):
    """Raised when an SLA is tighter than the batch API's own completion time."""


@dataclass(frozen=True)
class BatchItemResult:
    custom_id: str
    status: BatchStatus
    tool_input: dict[str, Any] | None
    error: str | None


class BatchClient(Protocol):
    """Narrow boundary around the Batches API used by the pipeline."""

    def submit(self, requests: list[dict[str, Any]]) -> str:
        """Submit a batch; return its id."""
        ...

    def collect(self, batch_id: str) -> list[BatchItemResult]:
        """Poll until the batch ends, then return normalised per-item results."""
        ...


class AnthropicBatchClient:
    """Production BatchClient adapter around Anthropic Message Batches."""

    def __init__(self, client: Anthropic) -> None:
        self._client = client

    def submit(self, requests: list[dict[str, Any]]) -> str:
        batch = self._client.messages.batches.create(
            requests=requests
        )  # type: ignore[arg-type]
        return batch.id

    def collect(self, batch_id: str) -> list[BatchItemResult]:
        deadline = time.monotonic() + BATCH_POLL_TIMEOUT_SECONDS

        while True:
            batch = self._client.messages.batches.retrieve(batch_id)

            if batch.processing_status == "ended":
                break

            if time.monotonic() > deadline:
                raise TimeoutError(f"Batch {batch_id} did not end within 24h.")

            time.sleep(BATCH_POLL_INTERVAL_SECONDS)

        out: list[BatchItemResult] = []

        for item in self._client.messages.batches.results(batch_id):
            result = item.result

            if isinstance(result, MessageBatchSucceededResult):
                tool_input = _extract_tool_input(result.message)
                out.append(
                    BatchItemResult(
                        custom_id=item.custom_id,
                        status="succeeded",
                        tool_input=tool_input,
                        error=None,
                    )
                )

            elif isinstance(result, MessageBatchErroredResult):
                out.append(
                    BatchItemResult(
                        custom_id=item.custom_id,
                        status="errored",
                        tool_input=None,
                        error=str(result.error),
                    )
                )

            elif isinstance(result, MessageBatchExpiredResult):
                out.append(
                    BatchItemResult(
                        custom_id=item.custom_id,
                        status="expired",
                        tool_input=None,
                        error="expired",
                    )
                )

            else:
                out.append(
                    BatchItemResult(
                        custom_id=item.custom_id,
                        status="canceled",
                        tool_input=None,
                        error="canceled",
                    )
                )

        return out


def _extract_tool_input(message: Any) -> dict[str, Any] | None:
    for block in message.content:
        if getattr(block, "type", None) == "tool_use":
            return dict(block.input)
    return None


# ---------- Helpers ----------


def submission_frequency(*, sla_hours: float, batch_eta_hours: float) -> int:
    """Return the minimum batches-per-day needed to meet the SLA.

    Raises SLATooTightError when the SLA is shorter than the batch ETA.
    """
    if sla_hours <= 0 or batch_eta_hours <= 0:
        raise ValueError("sla_hours and batch_eta_hours must be positive.")

    if sla_hours < batch_eta_hours:
        raise SLATooTightError(
            f"SLA ({sla_hours}h) is shorter than batch ETA "
            f"({batch_eta_hours}h). Use the real-time Messages API."
        )

    head_room = sla_hours - batch_eta_hours

    return max(
        1,
        math.ceil(24.0 / (head_room + batch_eta_hours)),
    )


def _build_request(
    custom_id: str,
    document_text: str,
    *,
    prior_attempts: list[dict[str, Any]] | None = None,
    model: str = DEFAULT_EXTRACTOR_MODEL,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    messages, system = build_extraction_messages(document_text, prior_attempts)

    return {
        "custom_id": custom_id,
        "params": {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "tools": [EXTRACT_POLICY_TOOL],
            "tool_choice": {"type": "tool", "name": "extract_policy"},
        },
    }


# ---------- Top-level: process with at most one resubmission round ----------


def process_with_resubmission(
    *,
    batch_client: BatchClient,
    extractor_client: MessageClient,
    policies: list[tuple[str, str]],
    model: str = DEFAULT_EXTRACTOR_MODEL,
) -> dict[str, ExtractionOutcome]:
    """Submit policies as a batch and resubmit eligible failures once."""

    del extractor_client

    final: dict[str, ExtractionOutcome] = {}

    if not policies:
        return final

    docs_by_id = {pid: doc for pid, doc in policies}

    # Round 1: submit every policy.
    first_requests = [
        _build_request(pid, doc, model=model)
        for pid, doc in policies
    ]

    first_batch_id = batch_client.submit(first_requests)
    first_results = batch_client.collect(first_batch_id)

    # Correlate responses by custom_id, never by response position.
    first_by_id = {
        item.custom_id: item
        for item in first_results
    }

    retry_queue: dict[str, list[dict[str, Any]]] = {}
    histories: dict[str, list[ValidationError]] = {}

    for pid, document_text in policies:
        item = first_by_id.get(pid)

        # Missing or unsuccessful batch result: retry without feedback.
        if item is None or item.status != "succeeded" or item.tool_input is None:
            retry_queue[pid] = []
            histories[pid] = []
            continue

        extraction = item.tool_input
        error = validate_extraction(extraction)

        # Successful and valid extraction.
        if error is None:
            final[pid] = build_extraction(
                policy_id=pid,
                extraction=extraction,
                attempt_index=0,
                history=[],
            )
            continue

        # Missing source information cannot be fixed by retrying.
        if error.category == "missing_source":
            final[pid] = RetryFutileEscalation(
                policy_id=pid,
                field=error.field,
                category="missing_source",
                detected_pattern=error.detected_pattern,
                reason=error.message,
            )
            continue

        # Format/consistency error: retry with the original extraction.
        histories[pid] = [error]

        retry_queue[pid] = [
            {
                "extraction": extraction,
                "error_field": error.field,
                "error_category": error.category,
                "error_pattern": error.detected_pattern,
                "error_message": error.message,
            }
        ]

    # No policies need another attempt.
    if not retry_queue:
        return final

    # Round 2: submit only queued policies.
    second_requests = [
        _build_request(
            pid,
            docs_by_id[pid],
            model=model,
            prior_attempts=retry_queue[pid] or None,
        )
        for pid in retry_queue
    ]

    second_batch_id = batch_client.submit(second_requests)
    second_results = batch_client.collect(second_batch_id)

    second_by_id = {
        item.custom_id: item
        for item in second_results
    }

    for pid in retry_queue:
        item = second_by_id.get(pid)
        history = histories.get(pid, [])

        # Any second-round batch failure is terminal.
        if item is None or item.status != "succeeded" or item.tool_input is None:
            status = item.status if item is not None else "missing_result"
            reason = (
                item.error
                if item is not None and item.error
                else f"Second batch attempt ended with status {status}."
            )

            final[pid] = RetryFutileEscalation(
                policy_id=pid,
                field="batch",
                category="missing_source",
                detected_pattern=f"batch_item_{status}",
                reason=reason,
            )
            continue

        extraction = item.tool_input
        error = validate_extraction(extraction)

        # Second attempt succeeded and passed validation.
        if error is None:
            final[pid] = build_extraction(
                policy_id=pid,
                extraction=extraction,
                attempt_index=1,
                history=history,
            )

        # Missing source: escalate immediately.
        elif error.category == "missing_source":
            final[pid] = RetryFutileEscalation(
                policy_id=pid,
                field=error.field,
                category="missing_source",
                detected_pattern=error.detected_pattern,
                reason=error.message,
            )

        # Format/consistency still invalid after the second round.
        else:
            final[pid] = RetryFutileEscalation(
                policy_id=pid,
                field=error.field,
                category="missing_source",
                detected_pattern=(
                    f"retries_exhausted__{error.detected_pattern}"
                ),
                reason=(
                    f"Second batch attempt failed validation: {error.message}"
                ),
            )

    return final


# ---------- Dry-run sample ----------


@dataclass
class DryRunSampleResult:
    sampled: int
    succeeded: int
    escalated: int
    first_pass_success_rate: float
    pattern_summary: dict[str, dict[str, Any]] = field(default_factory=dict)


def dry_run_sample(
    *,
    extractor_client: MessageClient,
    policies: list[tuple[str, str]],
    sample_size: int,
    model: str = DEFAULT_EXTRACTOR_MODEL,
) -> DryRunSampleResult:
    """Run a sample of policies through the real-time extractor."""

    n = min(sample_size, len(policies))
    outcomes: list[ExtractionOutcome] = []

    for pid, doc in policies[:n]:
        outcomes.append(
            extract_with_retry(
                client=extractor_client,
                policy_id=pid,
                document_text=doc,
                model=model,
                max_retries=0,
            )
        )

    succeeded = sum(
        1 for outcome in outcomes
        if isinstance(outcome, PolicyExtraction)
    )

    escalated = sum(
        1 for outcome in outcomes
        if isinstance(outcome, RetryFutileEscalation)
    )

    rate = succeeded / n if n > 0 else 0.0

    summary: dict[str, dict[str, Any]] = {
        pattern: dict(row)
        for pattern, row in summarize_patterns(outcomes).items()
    }

    return DryRunSampleResult(
        sampled=n,
        succeeded=succeeded,
        escalated=escalated,
        first_pass_success_rate=rate,
        pattern_summary=summary,
    )
