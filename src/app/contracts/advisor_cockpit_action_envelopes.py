"""OpenAPI response envelopes for the Advisor Cockpit action read surface."""

from pydantic import BaseModel, ConfigDict, Field

from app.config import settings
from app.contracts.advisor_cockpit_action_models import (
    AdvisorCockpitActionItem,
    AdvisorCockpitActionPage,
)


class _AdvisorCockpitActionEnvelopeBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    correlation_id: str = Field(min_length=1, max_length=160)
    contract_version: str = Field(default=settings.contract_version, min_length=1)


class AdvisorCockpitActionPageEnvelopeResponse(_AdvisorCockpitActionEnvelopeBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "correlation_id": "corr-advisor-cockpit-1",
                    "contract_version": "v1",
                    "data": {
                        "items": [
                            {
                                "action_item_id": "aci_policy_review_001",
                                "action_item_version": 1,
                                "action_family": "POLICY_REVIEW_REQUIRED",
                                "status": "PENDING_REVIEW",
                                "priority": "HIGH",
                                "owner_role": "COMPLIANCE_REVIEWER",
                                "owner_role_label": "Compliance reviewer",
                                "owning_system": "lotus-advise",
                                "title": "Policy review required",
                                "next_required_action": (
                                    "Review policy evaluation before advisor follow-up."
                                ),
                                "reason_codes": ["POLICY_PENDING_REVIEW"],
                                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                                "sla_age_band": "DUE_SOON",
                                "materiality_rank": 20,
                                "evidence_refs": [],
                                "source_readiness_gaps": [],
                                "dependency_readiness": [],
                                "lineage_refs": [],
                                "acknowledgement_state": {"acknowledged": False},
                                "unsupported_capabilities": ["CLIENT_READY_PUBLICATION"],
                            }
                        ],
                        "page_size": 25,
                        "total_count": 1,
                    },
                }
            ]
        },
    )
    data: AdvisorCockpitActionPage


class AdvisorCockpitActionEnvelopeResponse(_AdvisorCockpitActionEnvelopeBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "correlation_id": "corr-advisor-cockpit-1",
                    "contract_version": "v1",
                    "data": {
                        "action_item_id": "aci_policy_review_001",
                        "action_item_version": 1,
                        "action_family": "POLICY_REVIEW_REQUIRED",
                        "status": "PENDING_REVIEW",
                        "priority": "HIGH",
                        "owner_role": "COMPLIANCE_REVIEWER",
                        "owner_role_label": "Compliance reviewer",
                        "owning_system": "lotus-advise",
                        "title": "Policy review required",
                        "next_required_action": (
                            "Review policy evaluation before advisor follow-up."
                        ),
                        "reason_codes": ["POLICY_PENDING_REVIEW"],
                        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                        "sla_age_band": "DUE_SOON",
                        "materiality_rank": 20,
                        "evidence_refs": [],
                        "source_readiness_gaps": [],
                        "dependency_readiness": [],
                        "lineage_refs": [],
                        "acknowledgement_state": {"acknowledged": False},
                        "unsupported_capabilities": ["CLIENT_READY_PUBLICATION"],
                    },
                }
            ]
        },
    )
    data: AdvisorCockpitActionItem


__all__ = [
    "AdvisorCockpitActionEnvelopeResponse",
    "AdvisorCockpitActionPageEnvelopeResponse",
]
