from pydantic import BaseModel, Field


class DomainProductFailurePostureCondition(BaseModel):
    condition: str = Field(
        description="Situation in which the conditional failure posture applies."
    )
    posture: str = Field(description="Effective failure posture when the condition is true.")
    reason_codes: list[str] = Field(
        alias="reasonCodes",
        description="Stable source-failure reason codes associated with the condition.",
    )
    behavior: str = Field(description="Required consumer behavior when the condition is true.")

    model_config = {"populate_by_name": True}
