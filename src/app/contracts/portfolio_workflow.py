from pydantic import BaseModel, Field


class PortfolioWorkflowLaunchCue(BaseModel):
    key: str = Field(
        description="Stable workflow cue key exposed to product surfaces.",
        examples=["performance"],
    )
    label: str = Field(
        description="Advisor-facing workflow cue label.",
        examples=["Performance"],
    )
    href: str = Field(
        description="Route or in-page target used to launch the workflow from the workspace shell.",
        examples=["/performance?portfolioId=PF_1001"],
    )


class PortfolioReadinessIndicator(BaseModel):
    key: str = Field(
        description="Stable readiness indicator key used by product modules and UI affordances.",
        examples=["holdings"],
    )
    label: str = Field(
        description="Front-office label for the readiness dimension.",
        examples=["Holdings"],
    )
    status: str = Field(
        description="Gateway-normalized readiness posture for the dimension.",
        examples=["Ready"],
    )
    href: str = Field(
        description="In-page anchor or route target that helps the operator resolve the finding.",
        examples=["#portfolio-insights"],
    )


class PortfolioReadinessReason(BaseModel):
    code: str = Field(
        description="Source-authored readiness reason code returned by lotus-core.",
        examples=["pricing_not_published"],
    )
    detail: str | None = Field(
        default=None,
        description="Optional source-authored explanation for the readiness reason.",
        examples=["Pricing has not yet been published for the requested business date."],
    )


class PortfolioReadinessBucket(BaseModel):
    status: str = Field(
        description="Readiness posture for the specific source-backed dimension.",
        examples=["Pending"],
    )
    reasons: list[PortfolioReadinessReason] = Field(
        default_factory=list,
        description="Source-authored reasons explaining why the dimension is not fully ready.",
    )


class PortfolioSupportabilitySummary(BaseModel):
    feature_key: str = Field(
        default="core.observability.portfolio_supportability",
        description="RFC-0108 feature key for the source-owned portfolio supportability signal.",
        examples=["core.observability.portfolio_supportability"],
    )
    state: str = Field(
        description="Gateway-normalized supportability state for portfolio readiness composition.",
        examples=["ready", "degraded"],
    )
    reason: str = Field(
        description="Bounded source-authored reason code for the supportability state.",
        examples=["portfolio_supportability_ready"],
    )
    freshness_bucket: str = Field(
        description=(
            "Gateway-normalized freshness bucket for analytics UI observability. "
            "`current` from lotus-core is exposed as `fresh` for Workbench metric vocabulary."
        ),
        examples=["fresh", "stale", "unknown"],
    )
    ready_domains: int = Field(
        description="Count of source readiness domains currently ready.",
        examples=[4],
    )
    pending_domains: int = Field(
        description="Count of source readiness domains currently pending.",
        examples=[0],
    )
    blocked_domains: int = Field(
        description="Count of source readiness domains currently blocked.",
        examples=[0],
    )
    no_activity_domains: int = Field(
        description="Count of source readiness domains with no activity.",
        examples=[0],
    )


class PortfolioReadinessResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the readiness response envelope.",
        examples=["corr-portfolio-readiness"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway readiness response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose operational readiness is being reported.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description="Resolved readiness as-of date used for the source-backed evaluation.",
        examples=["2026-03-27"],
    )
    holdings: PortfolioReadinessBucket | None = Field(
        default=None,
        description="Detailed holdings-book readiness bucket from lotus-core.",
    )
    pricing: PortfolioReadinessBucket | None = Field(
        default=None,
        description="Detailed pricing readiness bucket from lotus-core.",
    )
    transactions: PortfolioReadinessBucket | None = Field(
        default=None,
        description="Detailed transaction-book readiness bucket from lotus-core.",
    )
    reporting: PortfolioReadinessBucket | None = Field(
        default=None,
        description="Detailed reporting readiness bucket from lotus-core.",
    )
    blocking_reasons: list[PortfolioReadinessReason] = Field(
        default_factory=list,
        description="Portfolio-level blocking reasons that prevent the workspace from being ready.",
        examples=[
            [
                {
                    "code": "awaiting_pricing",
                    "detail": "Reporting remains blocked until pricing is published.",
                }
            ]
        ],
    )
    supportability: PortfolioSupportabilitySummary | None = Field(
        default=None,
        description=(
            "Source-owned RFC-0108 portfolio supportability posture preserved from lotus-core "
            "for Workbench freshness, degraded-state, and operational evidence."
        ),
    )
    indicators: list[PortfolioReadinessIndicator] = Field(
        default_factory=list,
        description="Compact readiness indicators derived for the front-office workspace rails.",
        examples=[
            [
                {
                    "key": "holdings",
                    "label": "Holdings",
                    "status": "Ready",
                    "href": "#portfolio-insights",
                }
            ]
        ],
    )


class PortfolioWorkflowAction(BaseModel):
    sequence: int = Field(
        description="Display order for the workflow action within the prioritized action list.",
        examples=[1],
    )
    title: str = Field(
        description="Advisor-facing workflow action title.",
        examples=["Review performance"],
    )
    impact: str = Field(
        description="Short explanation of why the workflow action matters now for the portfolio.",
        examples=[
            "Review portfolio return, benchmark context, and contribution once the book is valued."
        ],
    )
    target: str = Field(
        description="Explicit workflow target or operating outcome that the action opens.",
        examples=[
            "Target: Performance workflow for this portfolio",
            "Target: cash funding and opening balance setup",
        ],
    )
    href: str = Field(
        description="Route or in-page target used to launch the workflow action.",
        examples=[
            "/performance?portfolioId=PF_1001",
            "/portfolio?portfolioId=PF_1001#portfolio-drilldown",
        ],
    )
    cta_label: str = Field(
        description="Short call-to-action label shown on the action button.",
        examples=["Performance"],
    )
    recommended: bool = Field(
        default=False,
        description="Whether this action is the highest-priority recommended next step.",
        examples=[True],
    )


class PortfolioWorkflowResponse(BaseModel):
    correlation_id: str = Field(
        description="Opaque correlation identifier for the workflow response envelope.",
        examples=["corr-portfolio-workflow"],
    )
    contract_version: str = Field(
        default="v1",
        description="Version of the gateway workflow response contract.",
        examples=["v1"],
    )
    portfolio_id: str = Field(
        description="Portfolio identifier whose prioritized workflow actions are being returned.",
        examples=["PF_1001"],
    )
    as_of_date: str = Field(
        description=(
            "Resolved as-of date used to derive workflow actions from "
            "source-backed portfolio state."
        ),
        examples=["2026-03-27"],
    )
    actions: list[PortfolioWorkflowAction] = Field(
        default_factory=list,
        description=(
            "Prioritized advisor workflow actions derived from the current "
            "portfolio workspace state."
        ),
        examples=[
            [
                {
                    "sequence": 1,
                    "title": "Review performance",
                    "impact": (
                        "Review portfolio return, benchmark context, and contribution once "
                        "the book is valued."
                    ),
                    "target": "Target: Performance workflow for this portfolio",
                    "href": "/performance?portfolioId=PF_1001",
                    "cta_label": "Performance",
                    "recommended": True,
                },
                {
                    "sequence": 2,
                    "title": "Review holdings",
                    "impact": (
                        "Confirm funded positions, valuations, and portfolio weights before "
                        "client review."
                    ),
                    "target": "Target: Holdings workflow for this portfolio",
                    "href": "/portfolio?portfolioId=PF_1001#portfolio-drilldown",
                    "cta_label": "Holdings",
                    "recommended": False,
                },
            ]
        ],
    )
