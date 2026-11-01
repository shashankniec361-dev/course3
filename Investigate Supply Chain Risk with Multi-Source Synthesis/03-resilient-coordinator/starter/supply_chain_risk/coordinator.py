
"""Coordinator — deterministic control-flow over the source readers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .memory import SharedMemory
from .models import FailureContext, ReaderResult
from .readers import (
    LOGISTICS_EXCLUSIVE_METRICS,
    NewsExtractor,
    read_audit,
    read_logistics,
    read_news,
    read_quality,
)
from .synthesis import Briefing, build_briefing

EXCLUSIVE_METRICS = {
    "logistics": LOGISTICS_EXCLUSIVE_METRICS,
}


@dataclass
class InvestigationResult:
    briefing: Briefing
    reader_results: list[ReaderResult]


def investigate(
    supplier: str,
    data_dir: str | Path,
    extractor: NewsExtractor,
    *,
    simulate_logistics_timeout: bool = False,
    logistics_fail_after: int = 5,
    memory: SharedMemory | None = None,
) -> InvestigationResult:
    """Run all readers and recover locally from source failures."""

    data_dir = Path(data_dir)
    reader_results: list[ReaderResult] = []

    # Audit reader.
    reader_results.append(read_audit(data_dir / "audit.json"))

    # Logistics reader.
    if simulate_logistics_timeout:
        logistics_result = read_logistics(
            data_dir / "logistics.csv",
            fail_after=logistics_fail_after,
        )
    else:
        logistics_result = read_logistics(data_dir / "logistics.csv")

    reader_results.append(logistics_result)

    # Quality reader.
    reader_results.append(read_quality(data_dir / "quality.sqlite"))

    # Each news article is processed independently.
    news_dir = data_dir / "news"

    if news_dir.exists():
        for article_path in sorted(news_dir.glob("*.txt")):
            try:
                result = read_news(article_path, extractor)
            except Exception as exc:
                result = ReaderResult(
                    source="industry_news",
                    ok=False,
                    error=FailureContext(
                        failure_type="reader_error",
                        attempted=f"read news article {article_path}",
                        alternatives=[f"retry extraction: {exc}"],
                    ),
                )

            reader_results.append(result)

    # Keep claims from successful reads only.
    successful_claims = [
        claim
        for result in reader_results
        if result.ok
        for claim in result.claims
    ]

    # Determine which metrics are already covered by surviving sources.
    surviving_metric_ids = {
        claim.metric_id for claim in successful_claims
    }

    unavailable: dict[str, str] = {}
    unavailable_sources: list[str] = []

    for result in reader_results:
        if result.ok:
            continue

        error = result.error
        failure_type = error.failure_type if error else "unknown"

        unavailable_sources.append(result.source)

        for metric_id in EXCLUSIVE_METRICS.get(result.source, ()):
            if metric_id not in surviving_metric_ids:
                unavailable[metric_id] = (
                    f"{result.source} unavailable: {failure_type}"
                )

    # Only successful claims are vectorized.
    # FailureContext.partial_results are intentionally excluded.
    if memory is not None and successful_claims:
        memory.add_claims(successful_claims)

    briefing = build_briefing(
        supplier,
        successful_claims,
        memory=memory,
        unavailable=unavailable,
        unavailable_sources=sorted(set(unavailable_sources)),
    )

    return InvestigationResult(
        briefing=briefing,
        reader_results=reader_results,
    )
