
"""System prompts, normalization rules, and few-shot examples.

The prompts teach the extractor how to handle missing values, normalize
informal numerics, and preserve arithmetic discrepancies.
"""

from __future__ import annotations

from mortgage_extractor.models import DocumentType

NORMALIZATION_RULES = """
Normalization rules:
- Square footage: convert informal measurements to an integer number of
  square feet. For example, "about 2,400 sq ft" becomes 2400.
- Currency: remove currency symbols and thousands separators, and return a
  numeric value. For example, "$485,000" becomes 485000.0.
- Percentage: convert percentages to decimal numbers. For example, "6.5%"
  becomes 0.065.
- Preserve the meaning and precision of the source document. Do not invent
  missing values or silently change stated amounts.
"""


_CATEGORICAL_CRITERIA = """
1. Return null for any field not explicitly stated in the document. Do not infer, default, or fabricate.
2. Keep base income separate from bonus, commission, and overtime. Never combine these components into base_monthly.
3. When a categorical value does not match a supported enum, return "other" and provide the explanation in its corresponding *_detail field.
4. Return numeric fields as numbers, not strings. Preserve stated totals separately from the individual income components.
"""


_FEW_SHOT_EXAMPLES = """
<example name="clean-paystub">
<input>
Employee: Alice Morgan
Pay period: Monthly
Base salary: $5,000
Monthly bonus: $500
Year-to-date bonus: $1,500
Commission: $200
Overtime: $100
Other monthly income: $50
Total monthly income: $5,850
</input>
<reasoning>
Every income component and the stated total are explicitly present. Keep each component separate and preserve the stated total rather than calculating a replacement.
</reasoning>
<output>
{
  "borrower": {"full_name": "Alice Morgan"},
  "income": {
    "base_monthly": 5000.0,
    "bonus_monthly": 500.0,
    "bonus_ytd": 1500.0,
    "commission_monthly": 200.0,
    "overtime_monthly": 100.0,
    "other_monthly": 50.0,
    "stated_monthly_total": 5850.0
  }
}
</output>
</example>

<example name="missing-bonus-paystub">
<input>
Employee: Daniel Reed
Monthly base salary: $4,200
Commission: $300
Overtime: $100
Total monthly income: $4,600
The paystub does not mention a bonus.
</input>
<reasoning>
bonus_ytd is null because the document says no bonus this year — fabricating a zero would imply zero earned, not zero reported. The monthly bonus is also null because no monthly bonus amount is stated.
</reasoning>
<output>
{
  "borrower": {"full_name": "Daniel Reed"},
  "income": {
    "base_monthly": 4200.0,
    "bonus_monthly": null,
    "bonus_ytd": null,
    "commission_monthly": 300.0,
    "overtime_monthly": 100.0,
    "other_monthly": null,
    "stated_monthly_total": 4600.0
  }
}
</output>
</example>

<example name="informal-appraisal">
<input>
Property address: 125 Oak Street
Property type: single-family home
Gross living area: about 2,400 sq ft
Appraised value: $485,000
</input>
<reasoning>
The phrase "about 2,400 sq ft" explicitly gives an approximate square-footage value. Normalize it to the integer 2400. The currency amount is normalized to a numeric value.
</reasoning>
<output>
{
  "property": {
    "address": "125 Oak Street",
    "property_type": "single_family",
    "gross_living_area_sqft": 2400,
    "appraised_value": 485000.0
  }
}
</output>
</example>

<example name="mismatch-paystub">
<input>
Employee: Morgan Lee
Monthly base salary: $5,000
Monthly bonus: $500
Commission: $200
Overtime: $100
Total monthly income as stated on the paystub: $6,000
</input>
<reasoning>
The individual components sum to $5,800, but the document explicitly states a total of $6,000. Preserve the stated total as written. Do not silently replace it with the calculated sum; the downstream validator must identify the discrepancy.
</reasoning>
<output>
{
  "borrower": {"full_name": "Morgan Lee"},
  "income": {
    "base_monthly": 5000.0,
    "bonus_monthly": 500.0,
    "bonus_ytd": null,
    "commission_monthly": 200.0,
    "overtime_monthly": 100.0,
    "other_monthly": null,
    "stated_monthly_total": 6000.0
  }
}
</output>
</example>
"""


def classifier_system_prompt() -> str:
    """System prompt for the classifier pass."""
    return (
        "You are a document classifier for a mortgage lender. You will receive "
        "the text of a single mortgage-related document and must call the "
        "`classify_document` tool exactly once with the document's type and a "
        "one-sentence reason describing the textual cues that drove the "
        "classification. Use `other` if the document is not one of the listed "
        "types or is too damaged to classify confidently."
    )


def extractor_system_prompt(doc_type: DocumentType) -> str:
    """Return the system prompt for the given document type's extractor."""
    if doc_type == DocumentType.INCOME_VERIFICATION:
        return income_verification_system_prompt()

    intro = (
        f"You are extracting structured mortgage data from a "
        f"{doc_type.value} document. Call the `extract_{doc_type.value}` "
        "tool exactly once with the extracted data. If the document is "
        "unreadable or too damaged to extract reliably, call "
        "`flag_for_review` instead."
    )
    return f"{intro}\n\n{NORMALIZATION_RULES}\n{_FEW_SHOT_EXAMPLES}"


def income_verification_system_prompt() -> str:
    """Return the income-verification extractor system prompt."""
    intro = (
        "You are extracting structured income-verification data from a "
        "mortgage document. Call `extract_income_verification` exactly once "
        "with the extracted data, or call `flag_for_review` if the document "
        "is unreadable or too damaged to extract reliably."
    )
    return (
        f"{intro}\n\n"
        f"{_CATEGORICAL_CRITERIA}\n"
        f"{NORMALIZATION_RULES}\n"
        f"{_FEW_SHOT_EXAMPLES}"
    )
