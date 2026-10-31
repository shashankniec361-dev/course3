"""HITL routing with stratified sampling and confidence calibration.

The routing layer is deliberately deterministic: the decision for each extraction is
a pure function of (extractor confidence, reviewer agreement, integration findings).
The model's self-rated confidence is one of three inputs, not the sole gate.
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from policy_extractor.records import PolicyExtraction
from policy_extractor.reviewer import IntegrationFinding, ReviewResult

DEFAULT_CONFIDENCE_THRESHOLD = 0.90

Decision = Literal["auto_approve", "human_review", "spot_check"]


@dataclass
class RoutingDecision:
    policy_id: str
    policy_type: str
    decision: Decision
    reason: str
    fields_below_threshold: list[str]
    reviewer_disagreements: list[str]
    integration_failures: list[str]
    confidence_summary: dict[str, float]


def route_extraction(
    *,
    extraction: PolicyExtraction,
    review: ReviewResult,
    integration_findings: Sequence[IntegrationFinding],
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> RoutingDecision:
    """Classify a single extraction as auto_approve or human_review.

    spot_check is assigned later by apply_stratified_spot_check over a batch.
    """
    # TODO: Compute the routing decision deterministically on three inputs.
    #
    # 1. fields_below = sorted list of field names whose extractor confidence is
    #    below `threshold`. (Read from extraction.confidence.)
    # 2. disagreements = sorted list of field names where review.agreements[f].agreement
    #    == "disagree".
    # 3. integration_failures = sorted list of check_names from integration_findings
    #    where status == "fail".
    #
    # Decision rule: if ANY of those three lists is non-empty → "human_review".
    # Otherwise → "auto_approve".
    #
    # ⚠ The routing decision must be deterministic on the *conjunction* of all three
    # signals (confidence ∧ reviewer ∧ integration). The natural-looking shortcut
    # — "auto_approve when all extractor confidences are high" — silently ignores
    # reviewer disagreement and integration failures. A hallucinated all-0.99
    # extraction with a reviewer disagreement would then sail through. The
    # The regression test here (extractor self-rates 0.99, reviewer disagrees on one field,
    # expect human_review) is what catches the shortcut.
    #
    # Build a human-readable `reason` string that lists which of the three triggered:
    #   "fields_below_threshold=...; reviewer_disagreement=...; integration_failure=..."
    # Auto-approve reason can be:
    #   "all confidence at/above threshold, reviewer agrees, integration clean".
    #
    # Return a RoutingDecision with all five lists/maps populated, including a
    # dict copy of extraction.confidence as confidence_summary.
    raise NotImplementedError("LO-D — implement route_extraction.")


def apply_stratified_spot_check(
    decisions: Sequence[RoutingDecision],
    *,
    sample_pct: float,
    seed: int | None = None,
) -> list[RoutingDecision]:
    """Promote a stratified sample of auto_approve decisions to spot_check.

    Groups by policy_type; from each stratum, promotes ceil(sample_pct * stratum_size)
    decisions to spot_check. A stratum with at least one eligible record never gets
    zero spot-checks — this is the drift-detection net.
    """
    rng = random.Random(seed)
    # TODO: Implement stratified spot-check promotion.
    #
    # 1. Bucket decisions by policy_type, keeping the INDEX of each auto_approve
    #    decision. (We need the index so we can rebuild the output list in order.)
    #    Skip non-auto_approve decisions — they are not eligible for spot_check.
    # 2. For each stratum with at least one eligible index:
    #       n = len(indices)
    #       k = max(1, math.ceil(sample_pct * n))
    #       k = min(k, n)
    #       promoted_indices |= set(rng.sample(indices, k))
    #
    #    ⚠ Use `max(1, math.ceil(...))` — NOT `round()` or `int()`. With `int()`,
    #    a small stratum like "2 umbrella policies × 20%" becomes int(0.4) = 0
    #    and the stratum disappears from the drift-detection sample. Umbrella drift
    #    then goes undetected, defeating the purpose of stratification.
    #
    # 3. Rebuild the output list in original order: each promoted index becomes a
    #    new RoutingDecision with decision="spot_check" and reason="stratified
    #    drift-detection sample" (preserve the other fields). Non-promoted entries
    #    pass through unchanged.
    raise NotImplementedError("LO-D — implement apply_stratified_spot_check.")


def write_routing_decisions(
    decisions: Iterable[RoutingDecision],
    path: Path,
) -> None:
    """Write routing decisions to a single JSON file."""
    payload = [asdict(d) for d in decisions]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


# ---------- Calibration ----------


@dataclass(frozen=True)
class CalibrationLabel:
    policy_id: str
    policy_type: str
    field: str
    predicted_confidence: float
    correct: bool


@dataclass
class CalibrationCell:
    policy_type: str
    field: str
    samples: int
    mean_predicted_confidence: float
    observed_accuracy: float
    brier_score: float


@dataclass
class CalibrationReport:
    cells: dict[tuple[str, str], CalibrationCell] = field(default_factory=dict)
    overall_brier: float = 0.0


def calibration_report(labels: Sequence[CalibrationLabel]) -> CalibrationReport:
    """Produce a (policy_type x field) sliced reliability report.

    For each cell, compute mean predicted confidence, observed accuracy, and Brier
    score (mean squared error between predicted_confidence and the binary outcome).
    Also reports the overall Brier across all samples.
    """
    if not labels:
        return CalibrationReport()
    # TODO: Build the sliced reliability report.
    #
    # 1. Bucket the labels by (policy_type, field) into a dict-of-list.
    # 2. For each bucket compute:
    #       n = len(bucket)
    #       mean_predicted_confidence = sum(b.predicted_confidence) / n
    #       observed_accuracy = sum(1 for b in bucket if b.correct) / n
    #       brier_score = sum((b.predicted_confidence - (1.0 if b.correct else 0.0)) ** 2) / n
    #    Store as a CalibrationCell keyed on (policy_type, field).
    # 3. overall_brier = sum((b.predicted_confidence - (1.0 if b.correct else 0.0)) ** 2
    #                        for b in labels) / len(labels).
    # 4. Return CalibrationReport(cells=..., overall_brier=...).
    #
    # Why Brier (squared error vs the 0/1 outcome) and not log-loss or a CI:
    # Brier reads directly — a Brier of 0.04 is 0.04 mean squared error in
    # confidence space, comparable across cells. Log-loss and confidence
    # intervals require log/CI tooling to interpret and won't surface "this cell
    # is much worse than the overall number" at a glance.
    raise NotImplementedError("LO-D — implement calibration_report.")
