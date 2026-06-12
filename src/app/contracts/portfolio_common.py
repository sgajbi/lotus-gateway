from pydantic import BaseModel, Field


class PortfolioPartialFailure(BaseModel):
    source_service: str = Field(
        description="Source service that produced the degraded optional response section.",
        examples=["lotus-core"],
    )
    error_code: str = Field(
        description="Gateway warning or failure code associated with the degraded section.",
        examples=["PORTFOLIO_CASHFLOW_UNAVAILABLE"],
    )
    detail: str = Field(
        description="Human-readable detail describing the degraded upstream section.",
        examples=["cashflow temporarily unavailable"],
    )
