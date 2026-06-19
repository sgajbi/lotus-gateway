from pydantic import BaseModel, Field


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
