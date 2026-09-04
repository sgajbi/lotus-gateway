"""Typed projection of lotus-ai's deterministic output-validation verdict.

lotus-ai stamps every task and workflow-pack execution with an ``output_validation``
verdict (contract source: lotus-ai ``contracts/output_validation.py``, runbook section
"AI Output Validation"). Gateway preserves that verdict without reinterpretation and
never presents AI output as product content unless the source proved it VALIDATED.
Gateway does not duplicate lotus-ai validation logic.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AiOutputValidationState = Literal[
    "VALIDATED",
    "REJECTED",
    "UNVALIDATED_LOCAL_ONLY",
    "VALIDATION_UNAVAILABLE",
]

# States in which lotus-ai withholds the output whole and forces a non-COMPLETED
# execution status; a COMPLETED execution carrying one is a source contradiction.
WITHHOLDING_VALIDATION_STATES: frozenset[str] = frozenset({"REJECTED", "VALIDATION_UNAVAILABLE"})


class AiOutputValidation(BaseModel):
    """lotus-ai's output-validation verdict preserved as source truth."""

    model_config = ConfigDict(extra="ignore")

    validation_state: AiOutputValidationState = Field(
        description="Deterministic validation verdict recorded by lotus-ai for this output."
    )
    authority: Literal["non_authoritative_ai_output"] = Field(
        description=(
            "Source-owned authority marking: AI output is never authoritative financial "
            "truth. Any other value fails the contract closed."
        ),
    )
    ruleset_version: str = Field(
        min_length=1,
        description="Version of the lotus-ai validation rule set that produced the verdict.",
    )
    failed_rule_ids: tuple[str, ...] = Field(
        default=(),
        description="Rule identifiers that rejected the output; empty unless REJECTED.",
    )
    findings: tuple[str, ...] = Field(
        default=(),
        description="Bounded source statements for each failed or waived rule.",
    )


def ai_output_displayable(validation: AiOutputValidation | None) -> bool:
    """Only a proven VALIDATED verdict makes AI output displayable product content.

    Absence of a verdict is not evidence of validity: it fails closed.
    """

    return validation is not None and validation.validation_state == "VALIDATED"
