
"""Anthropic tool definitions for the mortgage extraction pipeline."""
from __future__ import annotations

from copy import deepcopy
from typing import TypedDict

from mortgage_extractor.models import DocumentType
from mortgage_extractor.schema import JsonSchema, mortgage_data_schema


class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: JsonSchema


def extract_mortgage_data() -> ToolDefinition:
    """Return the canonical mortgage-data extractor tool definition."""
    return {
        "name": "extract_mortgage_data",
        "description": (
            "Extract structured borrower, property, loan, and income "
            "information from the mortgage document. Return null for fields "
            "that the document does not explicitly state; never invent "
            "missing values. If a categorical value does not fit the supplied "
            "enum, use 'other' and provide the explanation in its "
            "corresponding *_detail field."
        ),
        "input_schema": mortgage_data_schema(),
    }


def classify_document() -> ToolDefinition:
    """Return the document-classifier tool definition."""
    return {
        "name": "classify_document",
        "description": (
            "Classify the supplied mortgage document as loan_application, "
            "appraisal, income_verification, or other. Provide a brief "
            "reason supporting the classification."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "enum": [
                        "loan_application",
                        "appraisal",
                        "income_verification",
                        "other",
                    ],
                },
                "reason": {
                    "type": "string",
                    "description": "A one-sentence explanation for the classification.",
                },
            },
            "required": ["document_type", "reason"],
        },
    }


def doc_type_extractor(doc_type: DocumentType) -> ToolDefinition:
    """Return a document-type-specific extractor tool."""
    input_schema = deepcopy(mortgage_data_schema())
    input_schema["required"] = _required_sections_for(doc_type)

    return {
        "name": f"extract_{doc_type.value}",
        "description": (
            f"Extract the information carried by a {doc_type.value} document. "
            "Return null for fields that the document does not explicitly "
            "state; never invent missing values. If a categorical value does "
            "not fit the supplied enum, use 'other' and provide the explanation "
            "in its corresponding *_detail field."
        ),
        "input_schema": input_schema,
    }


def flag_for_review() -> ToolDefinition:
    """Return the extraction escape-hatch tool."""
    return {
        "name": "flag_for_review",
        "description": (
            "Flag this document for human review when its information cannot "
            "be reliably extracted. Provide a clear reason."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why human review is required.",
                },
            },
            "required": ["reason"],
        },
    }


def _required_sections_for(doc_type: DocumentType) -> list[str]:
    """Return the required top-level sections for a document type."""
    if doc_type == DocumentType.LOAN_APPLICATION:
        return ["borrower", "property", "loan"]

    if doc_type == DocumentType.APPRAISAL:
        return ["property"]

    if doc_type == DocumentType.INCOME_VERIFICATION:
        return ["borrower", "income"]

    if doc_type == DocumentType.OTHER:
        raise ValueError("Unsupported document type cannot be extracted")

    raise ValueError(f"Unknown document type: {doc_type}")


__all__ = [
    "ToolDefinition",
    "classify_document",
    "doc_type_extractor",
    "extract_mortgage_data",
    "flag_for_review",
]
