from app.contracts.performance_workspace import (
    PerformanceCalculationEvidenceView,
    PerformanceEvidenceUpstreamSnapshotView,
    PerformanceSourceSupportabilityView,
)
from app.services.performance_workspace_evidence import (
    build_calculation_evidence_view,
    build_performance_evidence_view,
    build_source_supportability,
    evidence_status_reason,
    execution_is_complete,
    execution_lineage_stage_complete,
    extract_calculation_id_from_result,
    gateway_evidence_artifact_url,
    lineage_is_complete,
    lineage_is_transient,
    resolve_evidence_reason,
    resolve_evidence_state,
)


def test_extract_calculation_id_from_result_returns_stable_string_id():
    assert extract_calculation_id_from_result((200, {"calculation_id": 42})) == "42"
    assert extract_calculation_id_from_result((200, {})) is None
    assert extract_calculation_id_from_result(ValueError("boom")) is None
    assert extract_calculation_id_from_result(None) is None


def test_build_source_supportability_deduplicates_upstream_posture():
    source_results = [
        (
            200,
            {
                "metadata": {
                    "calculation_supportability": {
                        "state": "stale",
                        "reason": "Source data window stale",
                        "freshness_bucket": "stale",
                        "source_service": "lotus-performance",
                    }
                }
            },
        ),
        (
            200,
            {
                "calculation_supportability": {
                    "state": "stale",
                    "reason": "Source data window stale",
                    "freshness_bucket": "stale",
                    "source_service": "lotus-performance",
                }
            },
        ),
        (503, {"detail": "ignored"}),
    ]

    items = build_source_supportability(source_results)

    assert [item.model_dump() for item in items] == [
        {
            "key": "source_calculation",
            "state": "partial",
            "reason": "Source data window stale",
            "freshness_bucket": "stale",
            "source_service": "lotus-performance",
        }
    ]


def test_resolve_evidence_state_and_reason_honor_source_supportability():
    stale_item = PerformanceSourceSupportabilityView(
        key="source_calculation",
        state="partial",
        reason="Source data window stale",
        freshness_bucket="stale",
        source_service="lotus-performance",
    )

    assert (
        resolve_evidence_state(
            evidence_state="supported",
            source_supportability=[stale_item],
        )
        == "partial"
    )
    assert (
        resolve_evidence_reason(
            evidence_state="partial",
            supported_reason="Supported",
            source_supportability=[stale_item],
        )
        == "Source data window stale"
    )


def test_evidence_completion_helpers_fail_closed_for_bad_payloads():
    complete_execution = (
        200,
        {
            "status": "complete",
            "stages": [
                {
                    "stage_name": "lineage_materialization",
                    "status": "complete",
                }
            ],
        },
    )

    assert execution_is_complete(complete_execution)
    assert execution_lineage_stage_complete(complete_execution)
    assert lineage_is_complete((200, {"status": "complete"}))
    assert lineage_is_transient((200, {"status": "pending"}))
    assert not execution_is_complete((500, {"status": "complete"}))
    assert not lineage_is_complete((200, {"status": "pending"}))
    assert not lineage_is_transient((404, {"status": "pending"}))


def test_build_calculation_evidence_view_maps_artifacts_and_reason():
    evidence = build_calculation_evidence_view(
        portfolio_id="PORT-1",
        calculation_role="workspace_summary",
        calculation_id="calc-1",
        execution_result=(
            200,
            {
                "analytics_type": "TWR",
                "execution_mode": "sync",
                "status": "complete",
                "stages": [
                    {
                        "stage_name": "execution",
                        "status": "complete",
                        "completed_at_utc": "2026-03-27T12:00:00Z",
                    }
                ],
                "upstream_snapshots": [
                    {
                        "upstream_endpoint": "portfolio_timeseries",
                        "source_identifier": "PORT-1",
                        "as_of_date": "2026-03-27",
                        "retrieval_status": "200",
                    }
                ],
            },
        ),
        lineage_result=(
            200,
            {
                "status": "pending",
                "artifacts": {
                    "response.json": {},
                    "request.json": {},
                },
            },
        ),
    )

    assert evidence.calculation_role == "workspace_summary"
    assert evidence.analytics_type == "TWR"
    assert evidence.lineage_status == "pending"
    assert evidence.reason == "Lineage is pending in lotus-performance."
    assert [artifact.artifact_name for artifact in evidence.artifacts] == [
        "request.json",
        "response.json",
    ]
    assert evidence.artifacts[0].url == (
        "/api/v1/workbench/PORT-1/performance/evidence/artifacts/calc-1/request.json"
    )


def test_build_performance_evidence_view_marks_stale_source_dates():
    calculation = PerformanceCalculationEvidenceView(
        calculation_role="workspace_summary",
        calculation_id="calc-1",
        analytics_type="TWR",
        execution_status="complete",
        execution_mode="sync",
        lineage_status="complete",
        stage_statuses=[],
        upstream_snapshots=[
            PerformanceEvidenceUpstreamSnapshotView(
                upstream_endpoint="portfolio_timeseries",
                source_identifier="PORT-1",
                as_of_date="2026-03-26",
                retrieval_status="200",
            )
        ],
        artifacts=[],
        reason=None,
    )

    evidence = build_performance_evidence_view(
        state="supported",
        reason="Evidence ready",
        as_of_date="2026-03-27",
        period="YTD",
        basis="NET",
        benchmark_code="BMK-1",
        contract_version="v1",
        limitations=[],
        calculations=[calculation],
        source_supportability=[],
    )

    assert evidence.input_freshness == {
        "performance": "stale",
        "benchmark": "stale",
    }
    assert evidence.source_services == ["lotus-performance"]
    assert evidence.calculation_versions == {
        "gateway_contract": "v1",
        "analytics_types": "TWR",
    }


def test_artifact_url_and_status_reason_are_bounded():
    assert gateway_evidence_artifact_url(
        portfolio_id="PORT-1",
        calculation_id="calc-1",
        artifact_name="request.json",
    ) == "/api/v1/workbench/PORT-1/performance/evidence/artifacts/calc-1/request.json"
    assert evidence_status_reason(503, {"detail": "upstream unavailable"}) == (
        "upstream unavailable"
    )
    assert evidence_status_reason(503, {}) == "HTTP_503"
    assert evidence_status_reason(200, {}) == "missing payload"
