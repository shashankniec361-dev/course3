
"""Structured news extraction using the Anthropic API."""
from __future__ import annotations

import json
from typing import Any


MODEL = "claude-opus-4-8"

_CLAIM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "evidence": {"type": "string"},
                    "source_date": {"type": "string"},
                    "confidence": {"type": "number"},
                    "metric_id": {"type": "string"},
                    "value": {"type": ["number", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "needs_identifier": {"type": "boolean"},
                    "candidates": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "claim",
                    "evidence",
                    "source_date",
                    "confidence",
                    "metric_id",
                    "needs_identifier",
                    "candidates",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["claims"],
    "additionalProperties": False,
}


def _system_prompt(supplier: str) -> str:
    """Build the structured extraction prompt for a named supplier."""
    return f"""
You are a supply-chain risk analyst.

Your task is to extract factual supply-chain risk findings about:
{supplier}

Extract only claims supported by the article.

Return the result using the required structured JSON schema with a top-level
"claims" array.

Each claim must include:
- claim: concise factual finding
- evidence: supporting text or a faithful summary from the article
- source_date: date of the event or publication in YYYY-MM-DD format
- confidence: a number between 0.0 and 1.0
- metric_id: a stable identifier for the type of finding
- needs_identifier: true when the supplier identity is ambiguous
- candidates: possible matching supplier names when identity is ambiguous

Include value and unit when the article provides a quantitative metric.
Use null when a numeric value or unit is unavailable.

If the article is unrelated to {supplier}, return an empty claims array.

If the article refers ambiguously to multiple companies with the same or
similar name, do not guess. Set needs_identifier to true and list the
possible company names in candidates.

Do not invent facts, dates, values, or supplier identities.
""".strip()


class AnthropicNewsExtractor:
    """Extract structured supply-chain claims using Anthropic."""

    def __init__(self, supplier: str, client: Any | None = None) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()

        self.supplier = supplier
        self._client = client

    def _system_prompt_for(self) -> str:
        return _system_prompt(self.supplier)

    def extract(self, article_text: str) -> list[dict[str, object]]:
        """Call Anthropic with a structured JSON output contract."""
        response = self._client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=self._system_prompt_for(),
            messages=[
                {
                    "role": "user",
                    "content": article_text,
                }
            ],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": _CLAIM_SCHEMA,
                }
            },
        )

        for block in response.content:
            if getattr(block, "type", None) == "text":
                payload = json.loads(block.text)
                claims = payload.get("claims", [])

                if not isinstance(claims, list):
                    raise ValueError("Structured response 'claims' must be a list")

                return claims

        raise ValueError("Anthropic response did not contain a text block")


class RecordedNewsExtractor:
    """Use recorded fixtures for deterministic offline extraction."""

    def __init__(self, fixtures: dict[str, list[dict[str, object]]]) -> None:
        self.fixtures = fixtures

    def extract(self, article_text: str) -> list[dict[str, object]]:
        return self.fixtures.get(article_text, [])
