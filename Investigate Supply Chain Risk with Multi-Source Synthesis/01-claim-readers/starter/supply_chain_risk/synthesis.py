"""Synthesis — turn provenance-carrying claims into an executive briefing.

The synthesis is deterministic Python (not an LLM call), so provenance
preservation and conflict annotation are *guaranteed*, not merely prompted:

- claims are grouped by the metric they describe (with shared-memory retrieval
  catching near-duplicate metric ids);
- each group is classified Well-Established / Contested / Incomplete;
- conflicts are **annotated, not arbitrated** — every conflicting value is kept
  with its source and date, and no single/averaged value is emitted;
- each finding carries a coverage annotation and an escalation flag driven by
  explicit criteria (never by model confidence or sentiment).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .memory import SharedMemory, _claim_id
from .models import Claim

WELL_ESTABLISHED = "Well-Established"
CONTESTED = "Contested"
INCOMPLETE = "Incomplete"
SECTIONS = (WELL_ESTABLISHED, CONTESTED, INCOMPLETE)

REL_TOL = 0.10  # values within 10% are treated as agreeing

# Metrics the investigation always tries to assess; a tracked metric with no
# usable source is reported as Incomplete (a coverage gap, not a fabricated one).
TRACKED_METRICS = (
    "on_time_delivery_rate",
    "defect_rate_ppm",
    "average_lead_time_days",
    "production_capacity_utilization",
)
# Metrics whose contested/incomplete state warrants human escalation.
HIGH_IMPACT = frozenset(
    {"on_time_delivery_rate", "defect_rate_ppm", "production_capacity_utilization"}
)
LOGISTICS = "logistics"
NEWS = "industry_news"


def _tokens(metric_id: str) -> set[str]:
    return set(metric_id.split("_"))


@dataclass
class MetricGroup:
    metric_id: str
    claims: list[Claim]


def group_by_metric(claims: list[Claim], memory: SharedMemory | None = None) -> list[MetricGroup]:
    """Cluster claims describing the same metric.

    Claims with an identical metric_id always group together. When `memory` is
    given, near-duplicate metric ids (different strings, same concept) are merged
    too: two claims unify if shared-memory retrieval ranks them as neighbours and
    their metric ids share at least two tokens (e.g. defect_rate / defect_rate_ppm).
    """
    # TODO: Cluster claims that share a metric_id. A union-find over claim indices
    #   works well: first union all claims with the same metric_id, then — when
    #   `memory` is provided — for each claim pull memory.related_to(claim) and
    #   union it with any neighbour whose metric_id shares >= 2 tokens (see
    #   _tokens) with it. Emit one MetricGroup per cluster, choosing the most
    #   common metric_id in the cluster as the canonical id. Sort groups by id.
    raise NotImplementedError


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
        for c in self.claims:
            if c.source not in seen:
                seen.append(c.source)
        return seen


def _source_values(claims: list[Claim]) -> dict[str, float]:
    values: dict[str, float] = {}
    for c in claims:
        if c.value is not None and c.source not in values:
            values[c.source] = c.value
    return values


def _disagree(values: list[float]) -> bool:
    # TODO: Return True when the values disagree beyond REL_TOL. Use a relative
    #   difference: (max - min) / max(abs(min), abs(max), tiny) > REL_TOL.
    raise NotImplementedError


def _classify(group: MetricGroup) -> tuple[str, str]:
    """Return (classification, coverage_badge) for a present metric group."""
    # TODO: 2+ sources whose values disagree -> (CONTESTED, "N sources, conflicting").
    #   2+ sources that agree -> (WELL_ESTABLISHED, "corroborated across N sources").
    #   A single source -> (WELL_ESTABLISHED, "single source only").
    raise NotImplementedError


def _escalation(metric_id: str, classification: str, claims: list[Claim]) -> tuple[bool, str]:
    """Explicit escalation criteria — never confidence/sentiment.

    Few-shot intent:
      on_time_delivery_rate Contested (high-impact) -> escalate
      defect_rate_ppm Well-Established               -> do not escalate
      production_capacity_utilization Incomplete     -> escalate (high-impact gap)
      supplier_financial_distress needs_identifier   -> escalate for clarification
    """
    # TODO: Escalate when any claim has needs_identifier, OR the metric is
    #   high-impact (HIGH_IMPACT) and Contested, OR high-impact and Incomplete.
    #   Otherwise do not escalate. Never read the confidence field.
    raise NotImplementedError


@dataclass
class Briefing:
    supplier: str
    findings: list[Finding] = field(default_factory=list)
    unavailable_sources: list[str] = field(default_factory=list)

    def section(self, name: str) -> list[Finding]:
        return [f for f in self.findings if f.classification == name]

    @property
    def escalations(self) -> list[Finding]:
        return [f for f in self.findings if f.escalate]

    def render(self) -> str:
        lines = [f"# Supply Chain Risk Briefing — {self.supplier}", ""]
        if self.unavailable_sources:
            lines.append(f"> Sources unavailable: {', '.join(self.unavailable_sources)}")
            lines.append("")
        for name in SECTIONS:
            lines.append(f"## {name}")
            findings = self.section(name)
            if not findings:
                lines.append("_none_")
                lines.append("")
                continue
            for f in findings:
                lines.extend(_render_finding(f))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"


def _render_finding(f: Finding) -> list[str]:
    # TODO: Render one finding as Markdown lines. Lead with a heading carrying the
    #   metric_id, its coverage badge, and an escalation flag when f.escalate.
    #   Render content appropriately: numeric metric comparisons as a structured
    #   list ("Reported values by source:"), logistics data as a Markdown table,
    #   and news findings as prose ("> ..."). For an INCOMPLETE finding, just show
    #   the coverage line. Keep EVERY conflicting value with its source and date —
    #   never average or drop one.
    raise NotImplementedError


def build_briefing(
    supplier: str,
    claims: list[Claim],
    memory: SharedMemory | None = None,
    *,
    tracked_metrics: tuple[str, ...] = TRACKED_METRICS,
    unavailable: dict[str, str] | None = None,
    unavailable_sources: list[str] | None = None,
) -> Briefing:
    """Assemble the coverage-tagged briefing.

    `unavailable` maps a metric_id to a failure reason (from a source that could
    not be read) so its metric is reported under Incomplete with that context.
    """
    # TODO: Group the claims, classify each group into a Finding (with coverage and
    #   escalation), then add Incomplete findings for tracked metrics with no usable
    #   source and for any metric in `unavailable` not otherwise present. Sort
    #   findings by (section order, metric_id) and return a Briefing.
    raise NotImplementedError
