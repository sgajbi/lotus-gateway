from pydantic import BaseModel, Field


class DpmWaveSupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns rebalance-wave state and supportability.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0041",
        description="Business authority and RFC provenance for DPM rebalance waves.",
        examples=["lotus-manage:RFC-0041"],
    )
    state: str = Field(
        description=(
            "Manage-published supportability state. Gateway preserves this value and defaults to "
            "UNKNOWN only when the upstream payload omits explicit supportability."
        ),
        examples=["ready", "degraded", "blocked", "UNKNOWN"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Manage-published bounded reason codes for blocked or degraded wave posture.",
        examples=[["wave_supportability_ready"]],
    )
    blocked_actions: list[str] = Field(
        default_factory=list,
        description="Manage-published action identifiers that Workbench should disable.",
        examples=[["simulate", "approve"]],
    )
    wave_id: str | None = Field(
        default=None,
        description="Manage-owned rebalance-wave identifier when available.",
        examples=["dwv_001"],
    )
    wave_state: str | None = Field(
        default=None,
        description="Manage-owned wave lifecycle state when available.",
        examples=["HANDOFF_READY"],
    )
    item_count: int | None = Field(
        default=None,
        description="Manage-published item count when available.",
        examples=[12],
    )
    issue_count: int = Field(
        default=0,
        description="Count of manage-published supportability issues, if supplied.",
        examples=[0],
    )
    remediation_owner: str | None = Field(
        default=None,
        description="Manage-published owner for source repair or operational remediation.",
        examples=["Portfolio Operations"],
    )
