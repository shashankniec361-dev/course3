
"""JSON Schema for mortgage document extraction."""
from __future__ import annotations

from typing import Any

JsonSchema = dict[str, Any]

PROPERTY_TYPES: list[str] = [
    "single_family",
    "condo",
    "townhouse",
    "multi_family",
    "manufactured",
    "cooperative",
    "other",
]

OCCUPANCY_TYPES: list[str] = [
    "primary_residence",
    "second_home",
    "investment",
    "other",
]

LOAN_PURPOSES: list[str] = [
    "purchase",
    "refinance_rate_term",
    "refinance_cash_out",
    "home_equity",
    "other",
]


def mortgage_data_schema() -> JsonSchema:
    """Return the canonical JSON Schema for mortgage extraction."""
    return {
        "type": "object",
        "properties": {
            "borrower": {
                "type": "object",
                "properties": {
                    "full_name": {"type": "string"},
                    "coborrower_name": {"type": ["string", "null"]},
                    "ssn_last4": {"type": ["string", "null"]},
                    "date_of_birth": {"type": ["string", "null"]},
                    "email": {"type": ["string", "null"]},
                    "phone": {"type": ["string", "null"]},
                },
                "required": ["full_name"],
            },
            "property": {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "property_type": {
                        "type": "string",
                        "enum": PROPERTY_TYPES,
                    },
                    "property_type_detail": {"type": ["string", "null"]},
                    "occupancy_type": {
                        "type": ["string", "null"],
                        "enum": [*OCCUPANCY_TYPES, None],
                    },
                    "occupancy_type_detail": {"type": ["string", "null"]},
                    "year_built": {"type": ["integer", "null"]},
                    "gross_living_area_sqft": {"type": ["integer", "null"]},
                    "hoa_dues_monthly": {"type": ["number", "null"]},
                    "appraised_value": {"type": ["number", "null"]},
                },
                "required": ["address", "property_type"],
            },
            "loan": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "term_months": {"type": ["integer", "null"]},
                    "interest_rate": {"type": ["number", "null"]},
                    "loan_purpose": {
                        "type": ["string", "null"],
                        "enum": [*LOAN_PURPOSES, None],
                    },
                    "loan_purpose_detail": {"type": ["string", "null"]},
                    "loan_program": {"type": ["string", "null"]},
                },
                "required": ["amount"],
            },
            "income": {
                "type": "object",
                "properties": {
                    "base_monthly": {"type": ["number", "null"]},
                    "bonus_monthly": {"type": ["number", "null"]},
                    "bonus_ytd": {"type": ["number", "null"]},
                    "commission_monthly": {"type": ["number", "null"]},
                    "overtime_monthly": {"type": ["number", "null"]},
                    "other_monthly": {"type": ["number", "null"]},
                    "stated_monthly_total": {"type": ["number", "null"]},
                },
                "required": [],
            },
        },
        "required": [],
    }


def list_nullable_fields(schema: JsonSchema) -> list[str]:
    """Return dotted paths of every nullable leaf field."""
    nullable_paths: list[str] = []

    def walk(properties: dict[str, Any], prefix: str = "") -> None:
        for name, definition in properties.items():
            path = f"{prefix}.{name}" if prefix else name
            field_type = definition.get("type")

            if isinstance(field_type, list) and "null" in field_type:
                nullable_paths.append(path)
            elif field_type == "object":
                walk(definition.get("properties", {}), path)

    walk(schema.get("properties", {}))
    return nullable_paths
