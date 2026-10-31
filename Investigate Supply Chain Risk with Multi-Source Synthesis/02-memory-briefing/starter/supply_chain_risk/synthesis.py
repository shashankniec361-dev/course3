
"""Synthesis — turn provenance-carrying claims into an executive briefing.

The synthesis is deterministic Python (not an LLM call), so provenance
preservation and conflict annotation are guaranteed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .memory import SharedMemory, _claim_id
from .models import Claim

WELL_ESTABLISHED = "Well-Established"
CONTESTED = "Contested"
INCOMPLETE = "Incomplete"
SECTIONS = (WELL_ESTABLISHED, CONTESTED, INCOMPLETE)

REL_TOL = 0.10

TRACKED_METRICS = (
    "on_time_delivery_rate",
    "defect_rate_ppm",
    "average_lead_time_days",
    "production_capacity_utilization",
)

HIGH_IMPACT = frozenset(
    {
        "on_time_delivery_rate",
        "defect_rate_ppm",
        "production_capacity_utilization",
    }
)

LOGISTICS = "logistics"
NEWS = "industry_news"


def _tokens(metric_id: str) -> set[str]:
    return set(metric_id.split("_"))


@dataclass
class MetricGroup:
    metric_id: str
    claims: list[Claim]


def group_by_metric(
    claims: list[Claim],
    memory: SharedMemory | None = None,
) -> list[MetricGroup]:
    """Cluster claims describing the same metric."""
    if not claims:
        return []

    parent = list(range(len(claims)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        root_first = find(first)
        root_second = find(second)

        if root_first != root_second:
            parent[root_second] = root_first

    # Group claims with identical metric identifiers.
    first_by_metric: dict[str, int] = {}

    for index, claim in enumerate(claims):
        if claim.metric_id in first_by_metric:
            union(index, first_by_metric[claim.metric_id])
        else:
            first_by_metric[claim.metric_id] = index

    # Merge near-duplicate metrics using shared-memory retrieval.
    if memory is not None:
        index_by_claim_id = {
            _claim_id(claim): index
            for index, claim in enumerate(claims)
        }

        for index, claim in enumerate(claims):
            for neighbour in memory.related_to(claim):
                neighbour_index = index_by_claim_id.get(
                    _claim_id(neighbour)
                )

                if neighbour_index is None or neighbour_index == index:
                    continue

                shared_tokens = (
                    _tokens(claim.metric_id)
                    & _tokens(neighbour.metric_id)
                )

                if len(shared_tokens) >= 2:
                    union(index, neighbour_index)

    # Build the final clusters.
    clusters: dict[int, list[Claim]] = {}

    for index, claim in enumerate(claims):
        root = find(index)
        clusters.setdefault(root, []).append(claim)

    groups: list[MetricGroup] = []

    for members in clusters.values():
        counts: dict[str, int] = {}

        for claim in members:
            counts[claim.metric_id] = (
                counts.get(claim.metric_id, 0) + 1
            )

        # Most common metric ID is canonical; alphabetical tie-break.
        canonical_id = sorted(
            counts,
            key=lambda metric: (-counts[metric], metric),
        )[0]

        groups.append(
            MetricGroup(
                metric_id=canonical_id,
                claims=members,
            )
        )

    return sorted(groups, key=lambda group: group.metric_id)


@dataclass
class Finding:
    metric_id: str
    classification: str
    claims: list[Claim]
    coverage: str
    escalate: bool
    escalation_reason: str = ""

    @property
    def sources(self) -> list[str]:
        seen: list[str] = []

        for claim in self.claims:
            if claim.source not in seen:
                seen.append(claim.source)

        return seen


def _source_values(claims: list[Claim]) -> dict[str, float]:
    """Get the first numeric value reported by each source."""
    values: dict[str, float] = {}

    for claim in claims:
        if claim.value is not None and claim.source not in values:
            values[claim.source] = claim.value

    return values


def _disagree(values: list[float]) -> bool:
    """Return True when the relative difference exceeds REL_TOL."""
    if len(values) < 2:
        return False

    maximum = max(values)
    minimum = min(values)

    denominator = max(
        abs(minimum),
        abs(maximum),
        1e-12,
    )

    relative_difference = (maximum - minimum) / denominator

    return relative_difference > REL_TOL


def _classify(group: MetricGroup) -> tuple[str, str]:
    """Return classification and coverage badge for a present metric."""
    values_by_source = _source_values(group.claims)
    source_count = len(values_by_source)

    if source_count >= 2:
        values = list(values_by_source.values())

        if _disagree(values):
            return CONTESTED, f"{source_count} sources, conflicting"

        return (
            WELL_ESTABLISHED,
            f"corroborated across {source_count} sources",
        )

    # Qualitative claims can still be corroborated across multiple sources.
    sources = {claim.source for claim in group.claims}

    if len(sources) >= 2:
        return (
            WELL_ESTABLISHED,
            f"corroborated across {len(sources)} sources",
        )

    return WELL_ESTABLISHED, "single source only"


def _escalation(
    metric_id: str,
    classification: str,
    claims: list[Claim],
) -> tuple[bool, str]:
    """Apply explicit escalation criteria without using confidence."""
    if any(claim.needs_identifier for claim in claims):
        return True, "Supplier identity requires clarification"

    if metric_id in HIGH_IMPACT and classification == CONTESTED:
        return True, "Conflicting reports for a high-impact metric"

    if metric_id in HIGH_IMPACT and classification == INCOMPLETE:
        return True, "High-impact metric has an evidence coverage gap"

    return False, ""


@dataclass
class Briefing:
    supplier: str
    findings: list[Finding] = field(default_factory=list)
    unavailable_sources: list[str] = field(default_factory=list)

    def section(self, name: str) -> list[Finding]:
        return [
            finding
            for finding in self.findings
            if finding.classification == name
        ]

    @property
    def escalations(self) -> list[Finding]:
        return [
            finding
            for finding in self.findings
            if finding.escalate
        ]

    def render(self) -> str:
        lines = [
            f"# Supply Chain Risk Briefing — {self.supplier}",
            "",
        ]

        if self.unavailable_sources:
            lines.append(
                f"> Sources unavailable: {', '.join(self.unavailable_sources)}"
            )
            lines.append("")

        for name in SECTIONS:
            lines.append(f"## {name}")
            findings = self.section(name)

            if not findings:
                lines.append("_none_")
                lines.append("")
                continue

            for finding in findings:
                lines.extend(_render_finding(finding))

            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


def _render_finding(f: Finding) -> list[str]:
    """Render a finding with source attribution and coverage information."""
    escalation_marker = (
        " — ESCALATION REQUIRED" if f.escalate else ""
    )

    lines = [
        f"### {f.metric_id}{escalation_marker}",
        f"Coverage: {f.coverage}",
    ]

    if f.escalation_reason:
        lines.append(f"Escalation reason: {f.escalation_reason}")

    if f.classification == INCOMPLETE:
        lines.append("")
        return lines

    # Logistics findings use the required Markdown table format.
    if any(claim.source == LOGISTICS for claim in f.claims):
        lines.extend(
            [
                "",
                "| Metric | Value | As of | Source |",
                "|---|---:|---|---|",
            ]
        )

        for claim in f.claims:
            value = (
                "Not reported"
                if claim.value is None
                else f"{claim.value:.1f}"
            )

            if claim.unit:
                value = f"{value} {claim.unit}"

            lines.append(
                f"| {f.metric_id} | {value} | "
                f"{claim.source_date.isoformat()} | {claim.source} |"
            )

        lines.append("")
        return lines

    numeric_claims = [
        claim for claim in f.claims
        if claim.value is not None
    ]

    if numeric_claims:
        lines.extend(["", "- Reported values by source:"])

        for claim in numeric_claims:
            value = f"{claim.value:.1f}"

            if claim.unit:
                value = f"{value} {claim.unit}"

            lines.append(
                f"  - {claim.source} ({claim.source_date.isoformat()}): "
                f"{value} — {claim.evidence}"
            )

        for claim in f.claims:
            if claim.value is None:
                lines.append(
                    f"  - {claim.source} ({claim.source_date.isoformat()}): "
                    f"{claim.evidence}"
                )

        lines.append("")
        return lines

    # Qualitative findings, particularly news, are rendered as prose.
    for claim in f.claims:
        lines.extend(
            [
                "",
                f"> {claim.evidence}",
                f"> — {claim.source}, {claim.source_date.isoformat()}",
            ]
        )

    lines.append("")
    return lines


def build_briefing(
    supplier: str,
    claims: list[Claim],
    memory: SharedMemory | None = None,
    *,
    tracked_metrics: tuple[str, ...] = TRACKED_METRICS,
    unavailable: dict[str, str] | None = None,
    unavailable_sources: list[str] | None = None,
) -> Briefing:
    """Assemble the coverage-tagged briefing."""
    unavailable = unavailable or {}

    findings: list[Finding] = []
    groups = group_by_metric(claims, memory)

    present_metrics: set[str] = set()

    for group in groups:
        present_metrics.add(group.metric_id)

        classification, coverage = _classify(group)

        escalate, reason = _escalation(
            group.metric_id,
            classification,
            group.claims,
        )

        findings.append(
            Finding(
                metric_id=group.metric_id,
                classification=classification,
                claims=group.claims,
                coverage=coverage,
                escalate=escalate,
                escalation_reason=reason,
            )
        )

    # Include tracked metrics without usable evidence.
    missing_metrics = set(tracked_metrics) - present_metrics

    # Also include metrics associated with unavailable sources.
    missing_metrics.update(set(unavailable) - present_metrics)

    for metric_id in sorted(missing_metrics):
        reason = unavailable.get(
            metric_id,
            metric_id,
        )

        coverage = f"missing source: {reason}"

        escalate, escalation_reason = _escalation(
            metric_id,
            INCOMPLETE,
            [],
        )

        findings.append(
            Finding(
                metric_id=metric_id,
                classification=INCOMPLETE,
                claims=[],
                coverage=coverage,
                escalate=escalate,
                escalation_reason=escalation_reason,
            )
        )

    section_order = {
        section: index
        for index, section in enumerate(SECTIONS)
    }

    findings.sort(
        key=lambda finding: (
            section_order[finding.classification],
            finding.metric_id,
        )
    )

    return Briefing(
        supplier=supplier,
        findings=findings,
        unavailable_sources=list(unavailable_sources or []),
    )
