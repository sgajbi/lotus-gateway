from pydantic import BaseModel, Field


class DpmConstructionGenerateRequest(BaseModel):
    idempotency_key: str = Field(
        description=(
            "Required manage idempotency token for construction alternative-set generation. "
            "Gateway forwards it as the `Idempotency-Key` header and does not derive replay keys."
        ),
        examples=["construction-idem-001"],
    )
    body: dict[str, object] = Field(
        description=(
            "Request payload forwarded unchanged to lotus-manage RFC-0039 construction authority. "
            "Gateway does not optimize, recompute alternatives, infer source readiness, or choose "
            "methods."
        ),
        examples=[
            {
                "input_mode": "stateless",
                "methods": ["DO_NOTHING_BASELINE", "HEURISTIC_EXPLAINABLE", "MIN_TURNOVER"],
                "stateless_input": {
                    "portfolio_snapshot": {"portfolio_id": "PB_SG_GLOBAL_BAL_001"},
                },
            }
        ],
    )


class DpmConstructionSelectionRequest(BaseModel):
    body: dict[str, object] = Field(
        description=(
            "Selection payload forwarded unchanged to lotus-manage. Gateway records no independent "
            "selection truth and does not execute orders."
        ),
        examples=[
            {
                "alternative_id": "alt_heuristic_explainable",
                "actor_id": "pm_sg_1",
                "reason_code": "PM_SELECTED_EXPLAINABLE_BASELINE",
                "comment": "Selected for lower operational complexity.",
            }
        ],
    )


class DpmConstructionSupportability(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Authoritative service that owns construction alternative supportability.",
        examples=["lotus-manage"],
    )
    authority: str = Field(
        default="lotus-manage:RFC-0039",
        description="Business authority and RFC provenance for construction alternatives.",
        examples=["lotus-manage:RFC-0039"],
    )
    state: str = Field(
        description="Manage-published aggregate construction state preserved by Gateway.",
        examples=["READY", "PENDING_REVIEW", "DEGRADED", "BLOCKED", "UNKNOWN"],
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Manage-published bounded reason codes collected for product supportability.",
        examples=[["REGIME_SCENARIO_PACK_READY", "CASHFLOW_PROJECTION_READY"]],
    )
    selected_alternative_id: str | None = Field(
        default=None,
        description="Manage-owned selected alternative id when returned by a selection route.",
        examples=["alt_heuristic_explainable"],
    )


class DpmConstructionGatewayResponse(BaseModel):
    correlation_id: str = Field(
        description="Correlation identifier propagated across Gateway and lotus-manage.",
        examples=["corr-rfc39-construction-1"],
    )
    contract_version: str = Field(
        default="v1",
        description="Gateway BFF contract version for construction alternative responses.",
        examples=["v1"],
    )
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that supplied the authoritative construction payload.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage before Gateway envelope composition.",
        examples=[200],
    )
    supportability: DpmConstructionSupportability = Field(
        description=(
            "Gateway-normalized supportability summary derived from manage-published fields."
        )
    )
    data: dict[str, object] = Field(
        description=(
            "Authoritative manage construction payload preserved for Workbench composition. "
            "Gateway does not alter alternative ids, method statuses, objective traces, "
            "constraint traces, comparison metrics, diagnostics, selected state, or lineage."
        ),
        examples=[
            {
                "alternative_set_id": "cas_001",
                "status": "READY",
                "alternatives": [
                    {
                        "alternative_id": "alt_heuristic_explainable",
                        "method": "HEURISTIC_EXPLAINABLE",
                        "method_status": "READY",
                        "diagnostics": {
                            "authority_context": {
                                "currency_overlay_context": {
                                    "external_hedge_policy_source_product_name": (
                                        "ExternalHedgePolicy"
                                    ),
                                    "external_hedge_policy_source_product_version": "v1",
                                    "external_hedge_policy_source_id": (
                                        "sha256:external-hedge-policy"
                                    ),
                                    "external_hedge_policy_content_hash": (
                                        "sha256:external-hedge-policy-content"
                                    ),
                                    "external_hedge_policy_rule_count": 0,
                                    "external_hedge_policy_rules": [],
                                    "external_eligible_hedge_instrument_source_product_name": (
                                        "ExternalEligibleHedgeInstrument"
                                    ),
                                    "external_eligible_hedge_instrument_source_product_version": (
                                        "v1"
                                    ),
                                    "external_eligible_hedge_instrument_source_id": (
                                        "sha256:external-eligible-hedge-instrument"
                                    ),
                                    "external_eligible_hedge_instrument_content_hash": (
                                        "sha256:external-eligible-hedge-instrument-content"
                                    ),
                                    "external_eligible_hedge_instrument_count": 0,
                                    "external_eligible_hedge_instruments": [],
                                    "missing_data_families": [
                                        "external_hedge_policy",
                                        "external_eligible_hedge_instrument",
                                    ],
                                    "blocked_capabilities": [
                                        "hedge_policy_approval",
                                        "eligible_instrument_selection",
                                        "suitability_approval",
                                        "product_recommendation",
                                        "treasury_instruction",
                                        "counterparty_selection",
                                        "best_execution",
                                        "oms_acknowledgement",
                                        "fills",
                                        "settlement",
                                        "autonomous_treasury_action",
                                    ],
                                    "reason_codes": [
                                        "EXTERNAL_HEDGE_POLICY_FAIL_CLOSED",
                                        "EXTERNAL_ELIGIBLE_HEDGE_INSTRUMENTS_FAIL_CLOSED",
                                    ],
                                },
                                "execution_acknowledgement_context": {
                                    "supportability_status": "BLOCKED",
                                    "source_system": "lotus-core",
                                    "source_product_name": (
                                        "ExternalOrderExecutionAcknowledgement"
                                    ),
                                    "source_product_version": "v1",
                                    "source_id": (
                                        "sha256:external-order-execution-acknowledgement"
                                    ),
                                    "content_hash": (
                                        "sha256:external-order-execution-acknowledgement-content"
                                    ),
                                    "acknowledgement_count": 0,
                                    "missing_data_families": [
                                        "external_oms_order_execution_acknowledgement"
                                    ],
                                    "blocked_capabilities": [
                                        "order_generation",
                                        "venue_routing",
                                        "best_execution",
                                        "oms_acknowledgement",
                                        "fills",
                                        "settlement",
                                        "execution_status_certification",
                                        "autonomous_execution",
                                    ],
                                    "acknowledgements": [],
                                    "reason_codes": [
                                        "EXTERNAL_OMS_SOURCE_NOT_INGESTED",
                                        ("EXTERNAL_ORDER_EXECUTION_ACKNOWLEDGEMENT_FAIL_CLOSED"),
                                    ],
                                },
                            }
                        },
                    }
                ],
            }
        ],
    )


class DpmConstructionErrorDetail(BaseModel):
    source_service: str = Field(
        default="lotus-manage",
        description="Upstream service that rejected or failed the construction request.",
        examples=["lotus-manage"],
    )
    upstream_status: int = Field(
        description="HTTP status returned by lotus-manage.", examples=[409]
    )
    error_code: str = Field(
        description="Gateway error classification for the failed construction request.",
        examples=["MANAGE_CONSTRUCTION_UPSTREAM_ERROR"],
    )
    detail: str = Field(
        description="Product-safe summary of the manage error payload.",
        examples=["CONSTRUCTION_IDEMPOTENCY_KEY_CONFLICT"],
    )
