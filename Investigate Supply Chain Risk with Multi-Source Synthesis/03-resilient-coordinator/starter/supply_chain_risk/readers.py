
"""Source readers — adapters over differently-shaped evidence sources that all
converge on the same Claim representation.

- read_audit     : structured supplier-audit JSON
- read_logistics : semi-structured shipment CSV (metrics derived from rows)
- read_quality   : internal quality records in SQLite
- read_news      : unstructured prose, extracted via a NewsExtractor

Readers return ReaderResult — errors are values, not exceptions — so a single
unreadable source never aborts the investigation.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Protocol

from .models import Claim, FailureContext, ReaderResult

AUDIT = "supplier_audit"
LOGISTICS = "logistics"
QUALITY = "internal_quality"
NEWS = "industry_news"


def read_audit(path: str | Path) -> ReaderResult:
    """Parse the structured supplier audit JSON into Claims."""
    path = Path(path)

    if not path.exists():
        return ReaderResult(
            source=AUDIT,
            ok=False,
            error=FailureContext(
                failure_type="file_not_found",
                attempted=f"open {path}",
                alternatives=[
                    "request the audit report from the supplier"
                ],
            ),
        )

    doc = json.loads(path.read_text())
    report_date = date.fromisoformat(doc["report_date"])

    claims = [
        Claim(
            claim=metric["statement"],
            evidence=(
                f"{metric['label']}: {metric['value']} "
                f"{metric['unit']} ({doc['period']})"
            ),
            source=AUDIT,
            source_date=report_date,
            confidence=0.9,
            metric_id=metric["metric_id"],
            value=float(metric["value"]),
            unit=metric["unit"],
        )
        for metric in doc["metrics"]
    ]

    return ReaderResult(
        source=AUDIT,
        ok=True,
        claims=claims,
    )


def _logistics_claims(rows: list[dict[str, str]]) -> list[Claim]:
    """Calculate logistics metrics from shipment rows."""
    collection = max(
        date.fromisoformat(row["collection_date"])
        for row in rows
    )

    on_time = sum(
        1
        for row in rows
        if row["on_time"].strip().lower() == "true"
    )

    on_time_rate = round(100.0 * on_time / len(rows), 1)

    avg_lead = round(
        sum(int(row["lead_time_days"]) for row in rows) / len(rows),
        1,
    )

    late = len(rows) - on_time

    return [
        Claim(
            claim=(
                f"On-time delivery measured {on_time_rate}% "
                f"across {len(rows)} shipments."
            ),
            evidence=(
                f"{on_time}/{len(rows)} shipments delivered "
                "on or before the promised date."
            ),
            source=LOGISTICS,
            source_date=collection,
            confidence=0.85,
            metric_id="on_time_delivery_rate",
            value=on_time_rate,
            unit="percent",
        ),
        Claim(
            claim=(
                f"Average lead time was {avg_lead} days "
                f"across {len(rows)} shipments."
            ),
            evidence=(
                f"Mean of lead_time_days over {len(rows)} "
                "Q1 shipment records."
            ),
            source=LOGISTICS,
            source_date=collection,
            confidence=0.85,
            metric_id="average_lead_time_days",
            value=avg_lead,
            unit="days",
        ),
        Claim(
            claim=(
                f"{late} of {len(rows)} shipments were late this quarter."
            ),
            evidence=(
                f"Count of rows with on_time=false over "
                f"{len(rows)} shipment records."
            ),
            source=LOGISTICS,
            source_date=collection,
            confidence=0.85,
            metric_id="late_shipment_count",
            value=float(late),
            unit="shipments",
        ),
    ]


# Metrics only this source provides — used to report a coverage gap when it fails.
LOGISTICS_EXCLUSIVE_METRICS = ("late_shipment_count",)


def read_logistics(
    path: str | Path,
    *,
    fail_after: int | None = None,
) -> ReaderResult:
    """Derive delivery metrics from the semi-structured shipment CSV.

    fail_after simulates a source timeout after reading that many rows.
    The reader returns partial claims in FailureContext instead of raising.
    """
    path = Path(path)

    if not path.exists():
        return ReaderResult(
            source=LOGISTICS,
            ok=False,
            error=FailureContext(
                failure_type="file_not_found",
                attempted=f"open {path}",
                alternatives=[
                    "pull the shipment extract from the 3PL portal"
                ],
            ),
        )

    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        return ReaderResult(
            source=LOGISTICS,
            ok=True,
            claims=[],
        )

    # Simulate a timeout after the requested number of rows.
    if fail_after is not None and len(rows) > fail_after:
        partial_rows = rows[:fail_after]

        partial_claims = (
            _logistics_claims(partial_rows)
            if partial_rows
            else []
        )

        return ReaderResult(
            source=LOGISTICS,
            ok=False,
            error=FailureContext(
                failure_type="timeout",
                attempted=(
                    f"read {path}: timeout after {fail_after} "
                    f"of {len(rows)} shipment rows"
                ),
                partial_results=partial_claims,
                alternatives=[
                    "retry the shipment extract",
                    "request a fresh export from the 3PL portal",
                ],
            ),
        )

    return ReaderResult(
        source=LOGISTICS,
        ok=True,
        claims=_logistics_claims(rows),
    )


def read_quality(path: str | Path) -> ReaderResult:
    """Read internal quality records from SQLite."""
    path = Path(path)

    if not path.exists():
        return ReaderResult(
            source=QUALITY,
            ok=False,
            error=FailureContext(
                failure_type="file_not_found",
                attempted=f"open {path}",
                alternatives=[
                    "query the incoming-inspection database directly"
                ],
            ),
        )

    conn = sqlite3.connect(path)

    try:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT metric_id, label, value, unit, recorded_date, statement "
            "FROM quality_metrics"
        ).fetchall()
    finally:
        conn.close()

    claims = [
        Claim(
            claim=row["statement"],
            evidence=(
                f"{row['label']}: {row['value']} {row['unit']}"
            ),
            source=QUALITY,
            source_date=date.fromisoformat(row["recorded_date"]),
            confidence=0.88,
            metric_id=row["metric_id"],
            value=float(row["value"]),
            unit=row["unit"],
        )
        for row in rows
    ]

    return ReaderResult(
        source=QUALITY,
        ok=True,
        claims=claims,
    )


class NewsExtractor(Protocol):
    """Extract structured claim dictionaries from article prose.

    Implemented by AnthropicNewsExtractor at runtime and by a recorded
    fixture extractor in tests.
    """

    def extract(
        self,
        article_text: str,
    ) -> list[dict[str, object]]:
        ...


def read_news(
    path: str | Path,
    extractor: NewsExtractor,
) -> ReaderResult:
    """Extract Claims from an unstructured news article.

    A readable article that yields no supplier-relevant claims returns
    ok=True with an empty claims list. A missing file returns ok=False.

    Ambiguous entity matches are preserved using needs_identifier and
    candidates rather than being resolved heuristically.
    """
    path = Path(path)

    if not path.exists():
        return ReaderResult(
            source=NEWS,
            ok=False,
            error=FailureContext(
                failure_type="file_not_found",
                attempted=f"open {path}",
                alternatives=[
                    "re-fetch the article from the news source"
                ],
            ),
        )

    raw = extractor.extract(path.read_text())

    claims = [
        Claim(
            claim=str(item["claim"]),
            evidence=str(item["evidence"]),
            source=NEWS,
            source_date=date.fromisoformat(
                str(item["source_date"])
            ),
            confidence=float(item["confidence"]),  # type: ignore[arg-type]
            metric_id=str(item["metric_id"]),
            needs_identifier=bool(
                item.get("needs_identifier", False)
            ),
            candidates=tuple(
                item.get("candidates", []) or ()
            ),  # type: ignore[arg-type]
        )
        for item in raw
    ]

    return ReaderResult(
        source=NEWS,
        ok=True,
        claims=claims,
    )
