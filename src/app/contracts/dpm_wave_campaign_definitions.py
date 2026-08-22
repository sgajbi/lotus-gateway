from pydantic import BaseModel, ConfigDict, Field


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


class DpmCampaignDefinitionLaunchBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requested_as_of_date: str = Field(
        description="ISO business date used for the durable campaign wave.",
        examples=["2026-05-10"],
    )
    actor_id: str = Field(
        min_length=1,
        description="Human or service actor requesting the campaign launch.",
        examples=["pm_sg_1"],
    )
    correlation_id: str | None = Field(
        default=None,
        description=(
            "Optional source correlation id. Manage derives its deterministic launch correlation "
            "when this value is omitted."
        ),
        examples=["corr-campaign-definition-launch-001"],
    )


class DpmCampaignDefinitionLaunchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: DpmCampaignDefinitionLaunchBody = Field(
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


class DpmCampaignDefinitionRetirementBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retired_by: str = Field(
        min_length=1,
        description="Actor retiring the campaign definition for future launch use.",
        examples=["pm_sg_1"],
    )
    retirement_reason: str = Field(
        min_length=1,
        description="Business reason for retiring the campaign definition.",
        examples=["Campaign review completed and is no longer available for new waves."],
    )
    correlation_id: str = Field(
        min_length=1,
        description="Source correlation id for the retirement command.",
        examples=["corr-campaign-definition-retire-001"],
    )


class DpmCampaignDefinitionRetirementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: DpmCampaignDefinitionRetirementBody = Field(
        description=(
            "Typed campaign-definition retirement payload forwarded to lotus-manage. Manage owns "
            "retirement eligibility, lifecycle lineage, supportability, content hashes, reason "
            "codes, and operating boundaries."
        ),
        examples=[
            {
                "retired_by": "pm_sg_1",
                "retirement_reason": "Campaign review completed.",
                "correlation_id": "corr-campaign-definition-retire-001",
            }
        ],
    )


class DpmCampaignDefinitionSupersessionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    superseded_by_campaign_version: str = Field(
        min_length=1,
        description="Existing active replacement version for the same campaign identifier.",
        examples=["2026.06"],
    )
    superseded_by: str = Field(
        min_length=1,
        description="Actor superseding the campaign definition.",
        examples=["pm_sg_1"],
    )
    supersession_reason: str = Field(
        min_length=1,
        description="Business reason for replacing the campaign definition.",
        examples=["Candidate evidence was refreshed for the new review cycle."],
    )
    correlation_id: str = Field(
        min_length=1,
        description="Source correlation id for the supersession command.",
        examples=["corr-campaign-definition-supersede-001"],
    )


class DpmCampaignDefinitionSupersessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: DpmCampaignDefinitionSupersessionBody = Field(
        description=(
            "Typed campaign-definition supersession payload forwarded to lotus-manage. Manage "
            "owns replacement validation, lifecycle lineage, supportability, hashes, reason "
            "codes, and operating boundaries."
        ),
        examples=[
            {
                "superseded_by_campaign_version": "2026.06",
                "superseded_by": "pm_sg_1",
                "supersession_reason": "Candidate evidence was refreshed.",
                "correlation_id": "corr-campaign-definition-supersede-001",
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
