
"""Readers for the audit, logistics, quality, and news sources."""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Protocol

from supply_chain_risk.models import Claim, FailureContext, ReaderResult


AUDIT = "supplier_audit"
LOGISTICS = "logistics"
QUALITY = "internal_quality"
NEWS = "industry_news"

LOGISTICS_EXCLUSIVE_METRICS = frozenset({
    "late_shipment_count",
})


class NewsExtractor(Protocol):
    def extract(self, article_text: str) -> list[dict[str, object]]:
        """Extract structured claims from a news article."""


def read_audit(path: Path) -> ReaderResult:
    """Read supplier audit JSON and convert its metrics into claims."""
    if not path.exists():
        return ReaderResult(
            source=AUDIT,
            ok=False,
            error=FailureContext(
                failure_type="file_not_found",
                attempted=f"Read audit file: {path}",
                alternatives=["Check the file path", "Use another audit source"],
            ),
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        report_date = date.fromisoformat(payload["report_date"])
        supplier = payload.get("supplier", "Supplier")

        claims = [
            Claim(
                claim=f"{supplier}: {metric['label']}",
                evidence=metric["statement"],
                source=AUDIT,
                source_date=report_date,
                confidence=0.95,
                metric_id=metric["metric_id"],
                value=float(metric["value"]) if metric.get("value") is not None else None,
                unit=metric.get("unit"),
            )
            for metric in payload.get("metrics", [])
        ]

        return ReaderResult(source=AUDIT, ok=True, claims=claims)

    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return ReaderResult(
            source=AUDIT,
            ok=False,
            error=FailureContext(
                failure_type="invalid_source",
                attempted=f"Parse audit file: {path}",
                alternatives=[f"Check audit JSON structure: {exc}"],
            ),
        )


def _logistics_claims(rows: list[dict[str, str]]) -> list[Claim]:
    """Derive delivery metrics from shipment-level CSV records."""
    if not rows:
        return []

    collection_dates = [
        date.fromisoformat(row["collection_date"])
        for row in rows
        if row.get("collection_date")
    ]
    if not collection_dates:
        return []

    source_date = max(collection_dates)
    total = len(rows)

    on_time_count = sum(
        1 for row in rows if row.get("on_time", "").strip().lower() == "true"
    )
    on_time_rate = round(on_time_count / total * 100, 2)

    lead_times = [
        float(row["lead_time_days"])
        for row in rows
        if row.get("lead_time_days", "").strip()
    ]
    average_lead_time = (
        round(sum(lead_times) / len(lead_times), 2) if lead_times else None
    )

    late_count = total - on_time_count

    claims = [
        Claim(
            claim="Shipment on-time delivery rate",
            evidence=f"{on_time_count} of {total} shipments were delivered on time.",
            source=LOGISTICS,
            source_date=source_date,
            confidence=0.90,
            metric_id="on_time_delivery_rate",
            value=on_time_rate,
            unit="percent",
        ),
        Claim(
            claim="Average shipment lead time",
            evidence=f"Average lead time calculated from {len(lead_times)} shipments.",
            source=LOGISTICS,
            source_date=source_date,
            confidence=0.90,
            metric_id="average_lead_time_days",
            value=average_lead_time,
            unit="days",
        ),
        Claim(
            claim="Late shipment count",
            evidence=f"{late_count} of {total} shipments were late.",
            source=LOGISTICS,
            source_date=source_date,
            confidence=0.90,
            metric_id="late_shipment_count",
            value=float(late_count),
            unit="shipments",
        ),
    ]

    return claims


def read_logistics(
    path: Path,
    *,
    fail_after: int | None = None,
) -> ReaderResult:
    """Read logistics CSV and derive shipment performance metrics."""
    if not path.exists():
        return ReaderResult(
            source=LOGISTICS,
            ok=False,
            error=FailureContext(
                failure_type="file_not_found",
                attempted=f"Read logistics file: {path}",
                alternatives=["Check the CSV path", "Use another logistics source"],
            ),
        )

    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))

        if fail_after is not None:
            partial_rows = rows[:fail_after]
            partial_claims = _logistics_claims(partial_rows)

            return ReaderResult(
                source=LOGISTICS,
                ok=False,
                claims=partial_claims,
                error=FailureContext(
                    failure_type="timeout",
                    attempted=f"Read logistics CSV; simulated failure after {fail_after} rows",
                    partial_results=partial_claims,
                    alternatives=[
                        "Retry the logistics source",
                        "Continue using partial shipment data",
                        "Use audit data as an alternative source",
                    ],
                ),
            )

        return ReaderResult(
            source=LOGISTICS,
            ok=True,
            claims=_logistics_claims(rows),
        )

    except (OSError, csv.Error, ValueError, KeyError) as exc:
        return ReaderResult(
            source=LOGISTICS,
            ok=False,
            error=FailureContext(
                failure_type="invalid_source",
                attempted=f"Parse logistics CSV: {path}",
                alternatives=[f"Check CSV structure: {exc}"],
            ),
        )


def read_quality(path: Path) -> ReaderResult:
    """Read internal quality metrics from SQLite."""
    if not path.exists():
        return ReaderResult(
            source=QUALITY,
            ok=False,
            error=FailureContext(
                failure_type="file_not_found",
                attempted=f"Read quality database: {path}",
                alternatives=["Check the database path", "Use another quality source"],
            ),
        )

    try:
        with sqlite3.connect(path) as connection:
            records = connection.execute(
                """
                SELECT metric_id, label, value, unit, recorded_date, statement
                FROM quality_metrics
                """
            ).fetchall()

        claims = [
            Claim(
                claim=record[1],
                evidence=record[5],
                source=QUALITY,
                source_date=date.fromisoformat(record[4]),
                confidence=0.95,
                metric_id=record[0],
                value=float(record[2]) if record[2] is not None else None,
                unit=record[3],
            )
            for record in records
        ]

        return ReaderResult(source=QUALITY, ok=True, claims=claims)

    except (sqlite3.Error, OSError, ValueError, TypeError) as exc:
        return ReaderResult(
            source=QUALITY,
            ok=False,
            error=FailureContext(
                failure_type="invalid_source",
                attempted=f"Read quality database: {path}",
                alternatives=[f"Check SQLite database and table structure: {exc}"],
            ),
        )


def read_news(path: Path, extractor: NewsExtractor) -> ReaderResult:
    """Extract dated claims from a news article."""
    if not path.exists():
        return ReaderResult(
            source=NEWS,
            ok=False,
            error=FailureContext(
                failure_type="file_not_found",
                attempted=f"Read news article: {path}",
                alternatives=["Check the article path", "Use another news article"],
            ),
        )

    try:
        article_text = path.read_text(encoding="utf-8")
        extracted = extractor.extract(article_text)

        claims = [
            Claim(
                claim=str(item["claim"]),
                evidence=str(item["evidence"]),
                source=NEWS,
                source_date=date.fromisoformat(str(item["source_date"])),
                confidence=float(item["confidence"]),
                metric_id=str(item["metric_id"]),
                value=float(item["value"]) if item.get("value") is not None else None,
                unit=str(item["unit"]) if item.get("unit") is not None else None,
                needs_identifier=bool(item.get("needs_identifier", False)),
                candidates=tuple(str(candidate) for candidate in item.get("candidates", [])),
            )
            for item in extracted
        ]

        return ReaderResult(source=NEWS, ok=True, claims=claims)

    except (OSError, KeyError, TypeError, ValueError) as exc:
        return ReaderResult(
            source=NEWS,
            ok=False,
            error=FailureContext(
                failure_type="invalid_source",
                attempted=f"Extract claims from news article: {path}",
                alternatives=[f"Check article or extractor output: {exc}"],
            ),
        )
    except Exception as exc:
        return ReaderResult(
            source=NEWS,
            ok=False,
            error=FailureContext(
                failure_type="extraction_error",
                attempted=f"Extract claims from news article: {path}",
                alternatives=[f"Retry extraction: {exc}"],
            ),
        )
