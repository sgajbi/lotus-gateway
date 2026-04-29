from typing import Any, Literal

from pydantic import BaseModel, Field

ANALYTICS_DIAGNOSTICS_RESPONSE_EXAMPLE: dict[str, Any] = {
    "contractVersion": "analytics-ui-diagnostics.v1",
    "supportReference": "gdiag-risk-summary-permission-blocked",
    "route": "workbench-analytics",
    "panel": "risk-summary",
    "lookupStatus": "available",
    "supportabilityState": "permission_blocked",
    "auditEvent": "gateway.analytics.audit.protected_diagnostics_lookup",
    "safeDimensions": {
        "operation": "analytics.risk.calculate",
        "service": "lotus-risk",
        "state": "permission_blocked",
        "reason": "upstream_authorization_denied",
    },
    "operatorGuidance": [
        "Confirm caller entitlement and region posture in the authoritative upstream service.",
        "Use correlation evidence from the protected operational log store, not dashboard labels.",
    ],
    "forbiddenFields": [
        "portfolio_id",
        "client_id",
        "holding_id",
        "trace_id",
        "correlation_id",
        "request_body",
        "response_body",
        "raw_entitlement_failure",
    ],
}


class AnalyticsDiagnosticsResponse(BaseModel):
    contract_version: str = Field(
        default="analytics-ui-diagnostics.v1",
        alias="contractVersion",
        description="Version of the bounded analytics diagnostics lookup contract.",
    )
    support_reference: str = Field(
        ...,
        alias="supportReference",
        description="Opaque safe support reference supplied by the operator.",
        examples=["gdiag-risk-summary-permission-blocked"],
    )
    route: Literal["workbench-analytics"] = Field(
        default="workbench-analytics",
        description="Gateway analytics route family covered by this lookup.",
    )
    panel: str = Field(
        ...,
        description="Product-safe analytics panel classification resolved from the reference.",
        examples=["risk-summary"],
    )
    lookup_status: Literal["available"] = Field(
        default="available",
        alias="lookupStatus",
        description=(
            "Lookup result state. Missing raw evidence is represented by guidance, not PII."
        ),
    )
    supportability_state: str = Field(
        ...,
        alias="supportabilityState",
        description="Governed supportability state for the referenced analytics posture.",
        examples=["permission_blocked"],
    )
    audit_event: Literal["gateway.analytics.audit.protected_diagnostics_lookup"] = Field(
        default="gateway.analytics.audit.protected_diagnostics_lookup",
        alias="auditEvent",
        description="Bounded audit event emitted for this protected lookup.",
    )
    safe_dimensions: dict[str, str] = Field(
        ...,
        alias="safeDimensions",
        description="Metric-safe dimensions that may be used for operator triage.",
    )
    operator_guidance: list[str] = Field(
        ...,
        alias="operatorGuidance",
        description="Bounded operator next steps that do not expose sensitive source payloads.",
    )
    forbidden_fields: list[str] = Field(
        ...,
        alias="forbiddenFields",
        description=(
            "Fields that must remain out of analytics labels, dashboards, and audit fields."
        ),
    )

    model_config = {"populate_by_name": True}
