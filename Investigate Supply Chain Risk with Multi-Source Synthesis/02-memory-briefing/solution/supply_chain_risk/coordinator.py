"""Coordinator — deterministic control-flow over the source readers.

Runs each scoped reader, collects successful claims into shared memory, and hands
them to synthesis. Error propagation is local-recovery: a reader that fails
returns a `ReaderResult` with structured `FailureContext`; the coordinator
proceeds on the remaining sources and annotates the gap in the briefing rather
than aborting. Only successful claims are written to shared memory — failures are
recorded as coverage gaps, not vectorized.

This is intentionally a plain control-flow function, not an LLM-driven
orchestrator (multi-agent orchestration is a separate module).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .memory import SharedMemory
from .models import ReaderResult
from .readers import (
    LOGISTICS_EXCLUSIVE_METRICS,
    NewsExtractor,
    read_audit,
    read_logistics,
    read_news,
    read_quality,
)
from .synthesis import Briefing, build_briefing

# Metrics each source is the sole expected provider of (for gap attribution).
EXCLUSIVE_METRICS = {"logistics": LOGISTICS_EXCLUSIVE_METRICS}


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
    # TODO: Run every reader (audit, logistics, quality, and read_news for each
    #   article in data_dir/news). Pass fail_after to read_logistics only when
    #   simulate_logistics_timeout is set.
    # TODO: Keep only claims from successful reads (r.ok). For each FAILED read,
    #   record an "unavailable" note and map the source's EXCLUSIVE_METRICS to a
    #   gap reason — but only for metrics no surviving source reported.
    # TODO: Add ONLY the successful claims to shared memory (never partial results),
    #   then call build_briefing with the unavailable annotations. Return an
    #   InvestigationResult carrying the briefing and all reader_results.
    raise NotImplementedError
