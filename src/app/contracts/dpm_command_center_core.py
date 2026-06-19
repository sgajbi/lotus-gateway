from pydantic import BaseModel, Field


class DpmCommandCenterForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to the lotus-manage RFC-0038 mandate "
            "monitoring authority. Gateway does not discover books, calculate health, infer "
            "exceptions, or change source-readiness posture."
        ),
        examples=[
            {
                "mandate_ids": ["MANDATE_PB_SG_GLOBAL_BAL_001"],
                "as_of_date": "2026-05-03",
                "tenant_id": "default",
                "portfolio_manager_id": "PM_SG_DPM_001",
                "requested_by": "workbench.pm.sg.001",
            }
        ],
    )


class DpmCommandCenterResolveExceptionRequest(BaseModel):
    resolution_reason: str = Field(
        description=(
            "Bounded resolution reason forwarded to lotus-manage for the selected monitoring "
            "exception. Gateway preserves the reason and does not close exceptions locally."
        ),
        examples=["SOURCE_DATA_REPAIRED_AND_RECALCULATED"],
    )


class DpmCommandCenterSupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns the DPM command-center supportability state.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0038",
        description="Business authority and RFC provenance for mandate health and monitoring.",
        examples=["lotus-manage:RFC-0038"],
    )
    state: str = Field(
        description=(
            "Manage-published command-center supportability state. Gateway preserves this value "
            "and derives mandate drill-down readiness only from manage-published field gaps and "
            "source lineage."
        ),
        examples=["READY", "PARTIAL", "EMPTY", "UNKNOWN"],
    )
    data_completeness_state: str | None = Field(
        default=None,
        description=(
            "Manage-published data completeness state, preserved for Workbench readiness displays."
        ),
        examples=["PARTIAL"],
    )
    partial_readiness_reasons: list[str] = Field(
        default_factory=list,
        description="Manage-published reason codes explaining partial or degraded readiness.",
        examples=[["PM_BOOK_DISCOVERY_NOT_AVAILABLE"]],
    )
    source_run_id: str | None = Field(
        default=None,
        description="Manage-published source or monitoring run id backing the command-center view.",
        examples=["dmr_20260503_083000"],
    )
    remediation_owner: str | None = Field(
        default=None,
        description="Manage-published owner for source repair or supportability remediation.",
        examples=["Portfolio Operations"],
    )


class DpmCommandCenterGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc38-command-center-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM command-center authority responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmCommandCenterSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published fields."
        ),
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage command-center payload preserved for Workbench composition. "
            "Gateway does not alter health scores, dimensions, exceptions, reason codes, "
            "lineage, recommended actions, or monitoring-run state."
        ),
        examples=[
            {
                "health_distribution": {"READY": 3, "PENDING_REVIEW": 1, "BLOCKED": 1},
                "evaluated_mandates": 5,
                "active_exception_count": 2,
                "supportability": {
                    "data_completeness_state": "PARTIAL",
                    "partial_readiness_reasons": ["PM_BOOK_DISCOVERY_NOT_AVAILABLE"],
                },
            }
        ],
    )
