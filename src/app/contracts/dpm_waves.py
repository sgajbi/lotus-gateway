from pydantic import BaseModel, Field, model_validator

_CORE_DPM_PORTFOLIO_UNIVERSE = "CORE_DPM_PORTFOLIO_UNIVERSE"
_CORE_DISCOVERY_CALLER_SUPPLIED_FIELDS = ("portfolios", "portfolio_ids", "source_candidates")


def _has_supplied_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


class DpmWaveForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to the lotus-manage RFC-0041 rebalance-wave "
            "authority. Gateway does not discover PM books, infer affected portfolios, classify "
            "source readiness, simulate construction alternatives, approve items, stage items, "
            "create handoff evidence, or cancel wave state locally. For BULK_REVIEW_CAMPAIGN, "
            "`campaign_candidate_source=CORE_DPM_PORTFOLIO_UNIVERSE` asks lotus-manage to resolve "
            "bounded source-owned candidates from lotus-core `DpmPortfolioUniverseCandidate:v1`; "
            "Gateway preserves the request shape and rejects caller-supplied candidate portfolios "
            "in that mode so Workbench cannot mix source discovery with explicit-list input."
        ),
        examples=[
            {
                "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
                "trigger_id": "manual-wave-20260503-001",
                "rationale": "CIO model update for the Singapore balanced DPM book.",
                "as_of_date": "2026-05-03",
                "actor_id": "pm_sg_1",
                "portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            },
            {
                "trigger_type": "BULK_REVIEW_CAMPAIGN",
                "trigger_id": "campaign-core-universe-20260524",
                "rationale": "Review bounded Core-owned DPM mandate candidates.",
                "as_of_date": "2026-05-24",
                "actor_id": "pm_sg_1",
                "campaign_candidate_source": "CORE_DPM_PORTFOLIO_UNIVERSE",
                "model_portfolio_ids": ["MODEL_PB_SG_GLOBAL_BAL_DPM"],
                "include_inactive_mandates": False,
                "campaign_candidate_page_size": 500,
            },
        ],
    )

    @model_validator(mode="after")
    def reject_caller_portfolios_for_core_candidate_source(self) -> "DpmWaveForwardRequest":
        if self.body.get("campaign_candidate_source") != _CORE_DPM_PORTFOLIO_UNIVERSE:
            return self
        supplied_fields = [
            field
            for field in _CORE_DISCOVERY_CALLER_SUPPLIED_FIELDS
            if _has_supplied_value(self.body.get(field))
        ]
        if supplied_fields:
            supplied = ", ".join(supplied_fields)
            raise ValueError(
                "CORE_DPM_PORTFOLIO_UNIVERSE candidate discovery supplies the portfolio set from "
                "lotus-core DpmPortfolioUniverseCandidate:v1; omit caller-supplied candidate "
                f"fields: {supplied}."
            )
        return self


class DpmWaveCreateRequest(DpmWaveForwardRequest):
    idempotency_key: str = Field(
        description=(
            "Required manage idempotency token for durable wave creation. Gateway forwards it as "
            "the `Idempotency-Key` header and does not derive replay keys."
        ),
        examples=["wave-idem-001"],
    )


class DpmCampaignDefinitionForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "BulkReviewCampaignDefinition:v1 payload forwarded unchanged to lotus-manage. "
            "Gateway does not discover global portfolios, infer source facts, run maker-checker "
            "workflow, calculate campaign membership, or claim OMS execution."
        ),
        examples=[
            {
                "display_name": "May 2026 concentrated holdings review",
                "status": "ACTIVE",
                "as_of_date": "2026-05-14",
                "rationale": "Review source-backed DPM candidates with concentrated holdings.",
                "eligible_portfolio_types": ["DPM_DISCRETIONARY"],
                "candidates": [
                    {
                        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                        "portfolio_type": "DPM_DISCRETIONARY",
                        "source_refs": [
                            {
                                "source_system": "lotus-risk",
                                "source_type": "RiskEventAffectedCohort",
                                "source_id": "risk-event:concentration:2026-05-14",
                                "content_hash": "sha256:campaign-candidate",
                            }
                        ],
                    }
                ],
                "created_by": "pm_sg_1",
                "correlation_id": "corr-campaign-definition-001",
            }
        ],
    )


class DpmCampaignDefinitionLaunchRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Bulk-review campaign launch payload forwarded unchanged to lotus-manage. "
            "Manage owns launch-package readiness, deterministic replay posture, wave creation, "
            "reason codes, and launch history. Gateway does not recompute campaign membership or "
            "readiness, run maker-checker workflow, approve trades, stage orders, or claim OMS "
            "execution."
        ),
        examples=[
            {
                "requested_as_of_date": "2026-05-10",
                "actor_id": "pm_sg_1",
                "correlation_id": "corr-campaign-definition-launch-001",
            }
        ],
    )


class DpmCampaignDefinitionLifecycleCommandRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Campaign-definition lifecycle command payload forwarded unchanged to lotus-manage. "
            "Manage owns retire/supersede validation, lifecycle lineage, supportability, content "
            "hashes, reason codes, and operating boundaries. Gateway does not calculate campaign "
            "lifecycle, membership, readiness, approval state, maker-checker state, order state, "
            "OMS state, or external workflow orchestration."
        ),
        examples=[
            {
                "actor_id": "pm_sg_1",
                "reason_code": "CAMPAIGN_DEFINITION_RETIRED_BY_OWNER",
                "correlation_id": "corr-campaign-definition-retire-001",
            }
        ],
    )


class DpmCampaignWorkflowForwardRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Campaign workflow/audit payload forwarded unchanged to lotus-manage. Manage owns "
            "approval-decision state, assignment-action state, assignment-task state, task "
            "transition state, maker-checker posture, idempotency, source refs, hashes, reason "
            "codes, and operating boundaries. Gateway does not calculate campaign readiness, "
            "cohort membership, SLA posture, approval state, maker-checker state, task state, "
            "workflow orchestration, order state, OMS execution, client contact, fills, or "
            "settlement."
        ),
        examples=[
            {
                "actor_id": "pm_sg_1",
                "reason_code": "CAMPAIGN_WORKFLOW_EVIDENCE_RECORDED",
                "correlation_id": "corr-campaign-workflow-001",
            }
        ],
    )


class DpmWaveMemoRequest(BaseModel):
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "wave_pm_memo",
            "wave_rationale_summary",
            "approval_checklist",
            "risk_caveats",
            "operations_handoff",
            "evidence_gaps",
        ],
        min_length=1,
        description=(
            "Bounded support-only outputs requested from lotus-ai dpm_wave_pm_memo.pack@v1. "
            "Gateway forwards these labels as caller intent and does not allow outputs that "
            "approve trades, place orders, contact clients, score PMs, or invent missing evidence."
        ),
        examples=[["wave_pm_memo", "approval_checklist", "evidence_gaps"]],
    )
    audience: list[str] = Field(
        default_factory=lambda: ["portfolio_manager", "investment_control", "operations"],
        min_length=1,
        description=(
            "Intended human review audiences for the generated support memo. The lotus-ai pack "
            "still returns review-required evidence text; Gateway does not route the output to "
            "clients or operational execution systems."
        ),
        examples=[["portfolio_manager", "investment_control", "operations"]],
    )


class DpmOperationsHandoffSummaryRequest(BaseModel):
    requested_outputs: list[str] = Field(
        default_factory=lambda: [
            "operations_summary",
            "execution_prerequisites",
            "blocking_conditions",
            "support_references",
            "evidence_gaps",
        ],
        min_length=1,
        description=(
            "Bounded support-only outputs requested from lotus-ai "
            "dpm_operations_handoff_summary.pack@v1. Gateway forwards these labels as caller "
            "intent and does not allow outputs that approve trades, place orders, contact "
            "clients, score PMs, route execution, or invent missing evidence."
        ),
        examples=[["operations_summary", "execution_prerequisites", "blocking_conditions"]],
    )
    audience: list[str] = Field(
        default_factory=lambda: ["operations", "portfolio_manager", "investment_control"],
        min_length=1,
        description=(
            "Intended internal review audiences for the generated operations handoff summary. "
            "The lotus-ai pack returns review-required support text; Gateway does not route the "
            "output to clients or external execution systems."
        ),
        examples=[["operations", "portfolio_manager", "investment_control"]],
    )


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


class DpmWaveGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc41-wave-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM command-center wave responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative rebalance-wave payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmWaveSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published fields."
        )
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage wave payload preserved for Workbench composition. Gateway does "
            "not alter wave_id, lifecycle state, item states, reason codes, aggregate metrics, "
            "proof-pack refs, handoff refs, source refs, or supportability."
        ),
        examples=[
            {
                "wave": {
                    "wave_id": "dwv_001",
                    "state": "HANDOFF_READY",
                    "aggregate_metrics": {"item_count": 1, "ready_item_count": 1},
                },
                "durable": True,
            }
        ],
    )


class DpmCampaignDefinitionGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-campaign-definition-001"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM campaign-definition responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative campaign-definition payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage BulkReviewCampaignDefinition:v1 payload, "
            "BulkReviewCampaignDiscovery:v1 page, lifecycle event list, "
            "BulkReviewCampaignDefinitionPreviewReadiness:v1 posture, launch package, or launch "
            "history preserved for Workbench composition. Gateway does not alter candidates, "
            "source refs, governance, content hashes, lifecycle events, status, expiry, "
            "candidate counts, readiness, reason codes, blocked actions, or as-of posture."
        ),
        examples=[
            {
                "campaign_id": "campaign-holdings-apple-tesla-20260510",
                "campaign_version": "2026.05",
                "product_name": "BulkReviewCampaignDefinition",
                "status": "ACTIVE",
            }
        ],
    )


class DpmCampaignWorkflowGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-campaign-workflow-001"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM campaign workflow/audit responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description=(
            "Upstream service that supplied the authoritative campaign workflow/audit payload."
        ),
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage campaign workflow/audit payload preserved for Workbench "
            "composition. Gateway preserves count/page metadata, supportability, source refs, "
            "reason codes, operating boundaries, content hashes, no-order/no-OMS/no-external-"
            "workflow posture, approval-decision evidence, assignment-action evidence, "
            "assignment-task evidence, task-transition evidence, and maker-checker evidence "
            "without local workflow or state calculation."
        ),
        examples=[
            {
                "product_name": "BulkReviewCampaignOperatingQueue",
                "product_version": "v1",
                "items": [],
                "count": 0,
                "limit": 50,
                "offset": 0,
                "operating_boundaries": [
                    "NO_ORDER_GENERATION",
                    "NO_OMS_EXECUTION_CLAIM",
                    "NO_EXTERNAL_WORKFLOW_ORCHESTRATION",
                ],
            }
        ],
    )


class DpmWaveMemoGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-rfc41-wave-ai-pm-memo"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM wave AI memo handoff responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed workflow-pack run.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the authoritative wave report-input evidence.",
        examples=["lotus-manage"],
    )
    manage_upstream_status: int = Field(
        description="HTTP status returned by lotus-manage for the wave report-input request.",
        examples=[200],
    )
    ai_upstream_status: int = Field(
        description="HTTP status returned by lotus-ai for workflow-pack execution.",
        examples=[200],
    )
    supportability: DpmWaveSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published wave "
            "report-input fields and carried into the lotus-ai guardrail request."
        )
    )
    wave_report_input: dict[str, object] = Field(
        description=(
            "Authoritative manage DpmWaveReportInput payload preserved for traceability. Gateway "
            "does not rewrite item evidence, source refs, hashes, approval posture, or proof-pack "
            "posture before calling lotus-ai."
        ),
        examples=[
            {
                "wave_id": "dwv_001",
                "report_input_ref": "report-input:dwv_001",
                "source_refs": ["lotus-manage:wave:dwv_001"],
            }
        ],
    )
    memo_request: dict[str, object] = Field(
        description=(
            "Bounded caller intent sent to lotus-ai. This object is support-only and excludes "
            "trade approval, order placement, client contact, PM scoring, and evidence invention."
        ),
        examples=[
            {
                "requested_outputs": ["wave_pm_memo", "approval_checklist"],
                "audience": ["portfolio_manager", "investment_control"],
            }
        ],
    )
    data: dict[str, object] = Field(
        description=(
            "lotus-ai workflow-pack execution response. Gateway preserves the AI authority "
            "payload and does not post-process generated memo content into execution actions."
        )
    )


class DpmOperationsHandoffSummaryGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway, lotus-manage, and lotus-ai.",
        examples=["corr-rfc41-operations-handoff-summary"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for DPM operations handoff summary responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-ai",
        description="Service that executed the governed operations handoff summary workflow pack.",
        examples=["lotus-ai"],
    )
    evidence_source_service: str = Field(
        default="lotus-manage",
        description="Service that supplied the authoritative wave handoff evidence.",
        examples=["lotus-manage"],
    )
    manage_upstream_status: int = Field(
        description="HTTP status returned by lotus-manage for the wave report-input request.",
        examples=[200],
    )
    ai_upstream_status: int = Field(
        description="HTTP status returned by lotus-ai for workflow-pack execution.",
        examples=[200],
    )
    supportability: DpmWaveSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived only from manage-published wave "
            "report-input fields and carried into the lotus-ai guardrail request."
        )
    )
    wave_report_input: dict[str, object] = Field(
        description=(
            "Authoritative manage DpmWaveReportInput payload preserved for traceability. Gateway "
            "does not rewrite handoff refs, item evidence, source refs, hashes, approval posture, "
            "or proof-pack posture before calling lotus-ai."
        ),
    )
    handoff_summary_request: dict[str, object] = Field(
        description=(
            "Bounded caller intent sent to lotus-ai for operations handoff support. This object "
            "excludes trade approval, order placement, client contact, PM scoring, routing "
            "instructions, and evidence invention."
        ),
        examples=[
            {
                "requested_outputs": ["operations_summary", "blocking_conditions"],
                "audience": ["operations", "portfolio_manager"],
            }
        ],
    )
    data: dict[str, object] = Field(
        description=(
            "lotus-ai workflow-pack execution response. Gateway preserves the AI authority "
            "payload and does not post-process generated handoff text into execution actions."
        )
    )


class DpmWaveErrorDetail(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that rejected or failed the rebalance-wave request.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage.",
        examples=[422],
    )
    error_code: str = Field(
        description="Gateway error classification for the failed manage wave request.",
        examples=["MANAGE_WAVE_UPSTREAM_ERROR"],
    )
    detail: str = Field(
        description="Product-safe summary of the manage error payload.",
        examples=["Wave dwv_001 cannot be simulated from state DRAFT."],
    )
