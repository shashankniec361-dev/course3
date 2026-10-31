"""Validates extracted policy records and categorises failures.

The validator only handles semantic and consistency errors. JSON-syntax errors
are eliminated upstream by tool_choice-forced structured tool calls — the SDK
enforces the schema before this validator runs.
"""
from __future__ import annotations

from typing import Any

from policy_extractor.records import ValidationError


_REQUIRED_FIELDS = (
    "premium_amount",
    "deductible",
    "coverage_limit",
    "endorsements",
    "exclusions",
)


def validate_extraction(extraction: dict[str, Any]) -> ValidationError | None:
    """Return the first ValidationError found, or None if extraction is clean."""

    checks = (
        _check_required_present,
        _check_numeric_ranges,
        _check_premium_components_consistency,
    )

    for check in checks:
        error = check(extraction)
        if error is not None:
            return error

    return None


def _check_required_present(extraction: dict[str, Any]) -> ValidationError | None:
    """Return missing_source ValidationError for the first null required field, else None."""

    for field in _REQUIRED_FIELDS:
        value = extraction.get(field)

        if value is None:
            return ValidationError(
                field=field,
                observed_value=str(value),
                category="missing_source",
                detected_pattern=f"{field}_absent",
                message=(
                    f"Required field '{field}' is absent from the extraction. "
                    "The source document does not contain this information, "
                    "so retrying cannot resolve it."
                ),
            )

    return None


def _check_numeric_ranges(extraction: dict[str, Any]) -> ValidationError | None:
    """Return format ValidationError for any negative numeric field, else None."""

    numeric_fields = (
        ("premium_amount", "negative_premium"),
        ("deductible", "negative_deductible"),
        ("coverage_limit", "negative_coverage_limit"),
    )

    for field, pattern in numeric_fields:
        value = extraction.get(field)

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if value < 0:
                return ValidationError(
                    field=field,
                    observed_value=str(value),
                    category="format",
                    detected_pattern=pattern,
                    message=(
                        f"Field '{field}' cannot be negative; "
                        f"received {value}."
                    ),
                )

    return None


def _check_premium_components_consistency(
    extraction: dict[str, Any],
) -> ValidationError | None:
    """Return consistency ValidationError when stated premium differs from component sum."""

    components = extraction.get("premium_components")
    premium_amount = extraction.get("premium_amount")

    if not components or not isinstance(premium_amount, (int, float)):
        return None

    component_total = sum(
        component.get("amount", 0)
        for component in components
    )

    difference = abs(premium_amount - component_total)

    if difference > 0.01:
        return ValidationError(
            field="premium_amount",
            observed_value=str(premium_amount),
            category="consistency",
            detected_pattern="premium_does_not_match_components",
            message=(
                f"Premium amount ({premium_amount}) does not match "
                f"the sum of premium components ({component_total})."
            ),
        )

    return None