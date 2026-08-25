from app.contracts.risk_mandate_comparison import (
    WorkbenchMandateComparison,
    WorkbenchMandateComparisonSupportability,
    WorkbenchMandateConstraintComparison,
    WorkbenchMandateConstraintLimit,
    WorkbenchMandateConstraintMeasure,
    WorkbenchMandateReviewPolicy,
)


def test_mandate_comparison_contract_preserves_source_dates_limits_and_lineage() -> None:
    comparison = WorkbenchMandateComparison(
        mandate_id="MANDATE_PB_SG_GLOBAL_BAL_001",
        mandate_version="3",
        mandate_as_of_date="2026-05-03",
        risk_profile="BALANCED",
        comparison_as_of_date="2026-05-03",
        mandate_health_as_of_date="2026-05-03",
        date_alignment_state="aligned",
        constraints=[
            WorkbenchMandateConstraintComparison(
                key="cash_band",
                label="Cash allocation",
                limit=WorkbenchMandateConstraintLimit(minimum=0.02, maximum=0.10),
                measure=WorkbenchMandateConstraintMeasure(
                    value=0.0859,
                    as_of_date="2026-05-03",
                    source_service="lotus-manage",
                    source_metric="CASH_LIQUIDITY",
                ),
                headroom=0.0141,
                state="within",
                reason="Cash allocation is within the approved mandate band.",
                source_state="READY",
                source_reason_code="CASH_WITHIN_BAND",
            )
        ],
        review_policy=WorkbenchMandateReviewPolicy(
            review_frequency="QUARTERLY",
            last_review_date="2026-03-31",
            next_review_due_date="2026-06-30",
            state="scheduled",
        ),
        source_lineage=[
            {
                "product_name": "DiscretionaryMandateBinding",
                "product_version": "v1",
                "source_system": "lotus-core",
                "source_record_id": "DiscretionaryMandateBinding:v1",
                "data_quality_status": "COMPLETE",
            }
        ],
        supportability=WorkbenchMandateComparisonSupportability(state="ready"),
    )

    payload = comparison.model_dump(mode="json")

    assert payload["comparison_as_of_date"] == "2026-05-03"
    assert payload["date_alignment_state"] == "aligned"
    assert payload["constraints"][0]["headroom"] == 0.0141
    assert payload["constraints"][0]["source_state"] == "READY"
    assert payload["source_lineage"][0]["data_quality_status"] == "COMPLETE"


def test_mandate_constraint_contract_can_refuse_classification_without_a_limit() -> None:
    constraint = WorkbenchMandateConstraintComparison(
        key="issuer_max_weight",
        label="Largest issuer exposure",
        limit=None,
        measure=WorkbenchMandateConstraintMeasure(
            value=0.2107,
            basis="total_market_value_base",
            as_of_date="2026-05-03",
            source_service="lotus-risk",
            source_metric="top_issuer_weight_current",
        ),
        headroom=None,
        state="not_defined",
        reason="The mandate does not define a largest issuer limit.",
    )

    assert constraint.state == "not_defined"
    assert constraint.limit is None
    assert constraint.headroom is None
