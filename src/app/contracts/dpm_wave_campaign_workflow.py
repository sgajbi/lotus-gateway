from pydantic import BaseModel, Field


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
