import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.contracts import performance_workspace
from app.contracts.performance_evidence import (
    PerformanceCalculationEvidenceView,
    PerformanceEvidenceUpstreamSnapshotView,
    PerformanceSourceSupportabilityView,
)
from app.services import performance_calculation_evidence, performance_workspace_evidence
from app.services.performance_workspace_evidence import (
    EvidenceViewFetchState,
    EvidenceViewRequestContext,
    await_recent_evidence_completion,
    build_calculation_evidence_view,
    build_performance_evidence_view,
    build_source_supportability,
    evidence_status_reason,
    execution_is_complete,
    execution_lineage_stage_complete,
    extract_calculation_id_from_result,
    fetch_calculation_evidence,
    fetch_performance_evidence_artifact,
    gateway_evidence_artifact_url,
    lineage_is_complete,
    lineage_is_transient,
    performance_evidence_artifact_failure_detail,
    refresh_execution_after_lineage_completion,
    resolve_evidence_reason,
    resolve_evidence_state,
    resolve_evidence_view_response,
)
from app.services.performance_workspace_evidence_supportability import (
    UNVERIFIED_CALCULATION_REASON,
)


@pytest.mark.parametrize(
    "block",
    [
        None,
        [],
        "ready",
        1,
        {},
        {"state": ""},
        {"state": "unknown"},
        {"state": 1},
        {"state": "   "},
        {"state": None},
    ],
)
@pytest.mark.parametrize("nested", [False, True])
def test_required_calculation_supportability_fails_closed(block, nested):
    qualification = {"calculation_supportability": block}
    payload = {"metadata": qualification} if nested else qualification
    items = build_source_supportability([(200, payload)])
    assert len(items) == 1
    assert items[0].state == "partial"
    assert items[0].reason == UNVERIFIED_CALCULATION_REASON
    assert items[0].freshness_bucket == "unknown"
    assert (
        resolve_evidence_state(evidence_state="supported", source_supportability=items) == "partial"
    )


def test_ready_peer_does_not_hide_missing_calculation_qualification():
    items = build_source_supportability(
        [
            (200, {"calculation_supportability": {"state": "ready"}}),
            (200, {"calculation_id": "legacy"}),
        ]
    )
    assert [item.state for item in items] == ["supported", "partial"]
    assert (
        resolve_evidence_state(evidence_state="supported", source_supportability=items) == "partial"
    )
    assert (
        resolve_evidence_reason(
            evidence_state="partial", supported_reason="ready", source_supportability=items
        )
        == UNVERIFIED_CALCULATION_REASON
    )


@pytest.mark.parametrize(
    "state, expected",
    [
        ("ready", "supported"),
        ("blocked", "partial"),
        ("stale", "partial"),
        ("unavailable", "unavailable"),
    ],
)
@pytest.mark.parametrize("nested", [False, True])
def test_valid_calculation_posture_and_reason_are_preserved(state, expected, nested):
    qualification = {
        "calculation_supportability": {
            "state": state,
            "reason": "source_quality_issue",
            "freshness_bucket": "fresh",
        }
    }
    items = build_source_supportability(
        [(200, {"metadata": qualification} if nested else qualification)]
    )
    assert items[0].state == expected
    assert items[0].reason == "source_quality_issue"
    assert items[0].freshness_bucket == "fresh"


def test_unrequested_or_failed_calculations_do_not_fabricate_qualification():
    assert build_source_supportability([None, ValueError("transport"), (204, {}), (503, {})]) == []


def test_blocked_calculation_without_reason_is_not_confirmed_ready():
    items = build_source_supportability(
        [(200, {"calculation_supportability": {"state": "blocked"}})]
    )
    assert items[0].reason == "Source calculation supportability is blocked upstream."


def test_workspace_contract_reexports_performance_evidence_views() -> None:
    assert (
        performance_workspace.PerformanceCalculationEvidenceView
        is PerformanceCalculationEvidenceView
    )
    assert (
        performance_workspace.PerformanceEvidenceUpstreamSnapshotView
        is PerformanceEvidenceUpstreamSnapshotView
    )
    assert (
        performance_workspace.PerformanceSourceSupportabilityView
        is PerformanceSourceSupportabilityView
    )


def test_workspace_evidence_facade_reexports_calculation_evidence_boundary() -> None:
    assert (
        performance_workspace_evidence.fetch_calculation_evidence
        is performance_calculation_evidence.fetch_calculation_evidence
    )
    assert (
        performance_workspace_evidence.fetch_performance_evidence_artifact
        is performance_calculation_evidence.fetch_performance_evidence_artifact
    )
    assert (
        performance_workspace_evidence.build_calculation_evidence_view
        is performance_calculation_evidence.build_calculation_evidence_view
    )


class _EvidenceAnalyticsClient:
    def __init__(
        self,
        *,
        execution_results: list[tuple[int, dict]],
        lineage_results: list[tuple[int, dict]],
    ) -> None:
        self.execution_results = execution_results
        self.lineage_results = lineage_results
        self.execution_calls: list[str] = []
        self.lineage_calls: list[str] = []

    async def get_execution(self, *, calculation_id: str, correlation_id: str):
        _ = correlation_id
        self.execution_calls.append(calculation_id)
        return self.execution_results.pop(0)

    async def get_lineage(self, *, calculation_id: str, correlation_id: str):
        _ = correlation_id
        self.lineage_calls.append(calculation_id)
        return self.lineage_results.pop(0)


class _ArtifactAnalyticsClient:
    def __init__(self, result: tuple[int, bytes, str | None]) -> None:
        self.result = result
        self.artifact_calls: list[dict[str, str]] = []

    async def get_lineage_artifact(
        self, *, calculation_id: str, artifact_name: str, correlation_id: str
    ) -> tuple[int, bytes, str | None]:
        self.artifact_calls.append(
            {
                "calculation_id": calculation_id,
                "artifact_name": artifact_name,
                "correlation_id": correlation_id,
            }
        )
        return self.result


def test_extract_calculation_id_from_result_returns_stable_string_id():
    assert extract_calculation_id_from_result((200, {"calculation_id": 42})) == "42"
    assert extract_calculation_id_from_result((200, {})) is None
    assert extract_calculation_id_from_result(ValueError("boom")) is None
    assert extract_calculation_id_from_result(None) is None


@pytest.mark.asyncio
async def test_fetch_performance_evidence_artifact_returns_bytes_and_content_type() -> None:
    client = _ArtifactAnalyticsClient((200, b"{}", "application/json"))

    content, content_type = await fetch_performance_evidence_artifact(
        analytics_client=client,
        calculation_id="calc-1",
        artifact_name="request.json",
        correlation_id="corr-1",
    )

    assert content == b"{}"
    assert content_type == "application/json"
    assert client.artifact_calls == [
        {
            "calculation_id": "calc-1",
            "artifact_name": "request.json",
            "correlation_id": "corr-1",
        }
    ]


@pytest.mark.asyncio
async def test_fetch_performance_evidence_artifact_raises_upstream_text_detail() -> None:
    client = _ArtifactAnalyticsClient((404, b"artifact not found", "text/plain"))

    with pytest.raises(HTTPException) as exc_info:
        await fetch_performance_evidence_artifact(
            analytics_client=client,
            calculation_id="calc-1",
            artifact_name="request.json",
            correlation_id="corr-1",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "artifact not found"


def test_performance_evidence_artifact_failure_detail_uses_safe_fallbacks() -> None:
    assert (
        performance_evidence_artifact_failure_detail(b"")
        == "Performance evidence artifact is unavailable."
    )
    assert (
        performance_evidence_artifact_failure_detail(b"\xff\xfe\xfd")
        == "Performance evidence artifact retrieval failed."
    )


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
            "calculation_role": None,
            "calculation_id": None,
            "period_keys": [],
            "metric_basis": None,
            "history_coverage": None,
        }
    ]


@pytest.mark.parametrize("case", ["complete", "partial", "unknown"])
def test_source_history_projection_retains_full_supported_response(case, history_responses):
    source = history_responses[case]
    items = build_source_supportability(
        [(200, source)],
        calculations=[("workspace_summary", source["calculation_id"])],
        metric_basis="NET",
    )
    assert len(items) == 1
    item = items[0]
    assert (
        item.history_coverage.model_dump(mode="json")
        == source["calculation_supportability"]["history_coverage"]
    )
    assert item.calculation_role == "workspace_summary"
    assert item.calculation_id == source["calculation_id"]
    assert item.period_keys == list(source["results_by_period"])
    assert item.metric_basis == "NET"
    assert item.state == ("supported" if case == "complete" else "partial")


def test_divergent_peer_histories_survive_equal_supportability_posture(history_responses):
    partial, unknown = history_responses["partial"], history_responses["unknown"]
    for source in (partial, unknown):
        source["calculation_supportability"]["reason"] = "calculation_quality_issue"
    items = build_source_supportability(
        [(200, partial), (200, unknown)],
        calculations=[
            ("workspace_summary", partial["calculation_id"]),
            ("attribution", unknown["calculation_id"]),
        ],
        metric_basis="NET",
    )
    assert len(items) == 2
    assert [item.history_coverage.status for item in items] == ["partial", "unknown"]
    assert [item.calculation_role for item in items] == ["workspace_summary", "attribution"]
    assert [item.history_coverage.missing_required_observation_count for item in items] == [360, 1]


@pytest.fixture
def history_responses():
    return json.loads(
        (
            Path(__file__).parents[1] / "fixtures" / "performance-history-source-responses.json"
        ).read_text(encoding="utf-8")
    )


def test_source_history_keeps_multiple_period_scope_without_inventing_period_windows(
    history_responses,
):
    source = history_responses["partial"]
    source["results_by_period"]["YTD"] = source["results_by_period"]["1Y"]
    item = build_source_supportability([(200, source)])[0]
    assert item.period_keys == ["1Y", "YTD"]
    assert (
        item.history_coverage.model_dump(mode="json")
        == source["calculation_supportability"]["history_coverage"]
    )


@pytest.mark.parametrize("case", ["partial", "unknown"])
def test_ready_source_does_not_override_explicit_incomplete_history(case, history_responses):
    source = history_responses[case]
    source["calculation_supportability"]["state"] = "ready"
    items = build_source_supportability([(200, history_responses["complete"]), (200, source)])
    assert [item.state for item in items] == ["supported", "partial"]
    assert (
        resolve_evidence_state(evidence_state="supported", source_supportability=items) == "partial"
    )


def _evidence_request_context() -> EvidenceViewRequestContext:
    return EvidenceViewRequestContext(
        portfolio_id="PORT-1",
        as_of_date="2026-03-27",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-03-27",
        basis="NET",
        benchmark_code="BMK-1",
        contract_version="v1",
        correlation_id="corr-1",
        calculations=[],
        source_results=[],
    )


def test_resolve_evidence_view_response_returns_empty_unavailable_view() -> None:
    warnings: list[str] = []
    partial_failures = []

    evidence = resolve_evidence_view_response(
        context=_evidence_request_context(),
        fetch_state=EvidenceViewFetchState(
            source_supportability=[],
            requested_items=[],
            evidence_items=[],
        ),
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert evidence.state == "unavailable"
    assert evidence.report_start_date == "2026-01-01"
    assert evidence.report_end_date == "2026-03-27"
    assert (
        evidence.reason == "No durable calculation evidence is available for the current selection."
    )
    assert evidence.limitations == ["No durable calculation evidence is available."]
    assert warnings == []
    assert partial_failures == []


def test_resolve_evidence_view_response_records_unavailable_warning() -> None:
    warnings: list[str] = []
    partial_failures = []

    evidence = resolve_evidence_view_response(
        context=_evidence_request_context(),
        fetch_state=EvidenceViewFetchState(
            source_supportability=[],
            requested_items=[("workspace_summary", "calc-1")],
            evidence_items=[
                PerformanceCalculationEvidenceView(
                    calculation_role="workspace_summary",
                    calculation_id="calc-1",
                )
            ],
        ),
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert evidence.state == "unavailable"
    assert evidence.reason == (
        "Gateway could not resolve execution or lineage evidence from lotus-performance."
    )
    assert evidence.report_start_date == "2026-01-01"
    assert evidence.report_end_date == "2026-03-27"
    assert warnings == ["PERFORMANCE_EVIDENCE_UNAVAILABLE"]
    assert partial_failures == []


def test_resolve_evidence_view_response_downgrades_supported_source_posture() -> None:
    stale_item = PerformanceSourceSupportabilityView(
        key="source_calculation",
        state="partial",
        reason="Source data window stale",
        freshness_bucket="stale",
        source_service="lotus-performance",
    )

    evidence = resolve_evidence_view_response(
        context=_evidence_request_context(),
        fetch_state=EvidenceViewFetchState(
            source_supportability=[stale_item],
            requested_items=[("workspace_summary", "calc-1")],
            evidence_items=[
                PerformanceCalculationEvidenceView(
                    calculation_role="workspace_summary",
                    calculation_id="calc-1",
                    execution_status="complete",
                    lineage_status="complete",
                )
            ],
        ),
        warnings=[],
        partial_failures=[],
    )

    assert evidence.state == "partial"
    assert evidence.reason == "Source data window stale"
    assert evidence.report_start_date == "2026-01-01"
    assert evidence.report_end_date == "2026-03-27"
    assert evidence.limitations == ["Source data window stale"]
    assert evidence.source_supportability == [stale_item]


def test_resolve_evidence_view_response_records_partial_failure() -> None:
    warnings: list[str] = []
    partial_failures = []

    evidence = resolve_evidence_view_response(
        context=_evidence_request_context(),
        fetch_state=EvidenceViewFetchState(
            source_supportability=[],
            requested_items=[("workspace_summary", "calc-1")],
            evidence_items=[
                PerformanceCalculationEvidenceView(
                    calculation_role="workspace_summary",
                    calculation_id="calc-1",
                    execution_status="complete",
                    lineage_status="pending",
                )
            ],
        ),
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert evidence.state == "partial"
    assert evidence.reason == (
        "One or more performance calculations still have pending, failed, "
        "or unavailable lineage evidence."
    )
    assert evidence.report_start_date == "2026-01-01"
    assert evidence.report_end_date == "2026-03-27"
    assert warnings == ["PERFORMANCE_EVIDENCE_PARTIAL"]
    assert [failure.error_code for failure in partial_failures] == ["PERFORMANCE_EVIDENCE_PARTIAL"]


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


@pytest.mark.asyncio
async def test_refresh_execution_after_lineage_completion_keeps_complete_stage_result():
    execution_result = (
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
    client = _EvidenceAnalyticsClient(
        execution_results=[(200, {"status": "complete"})],
        lineage_results=[],
    )

    refreshed = await refresh_execution_after_lineage_completion(
        analytics_client=client,
        calculation_id="calc-1",
        correlation_id="corr-1",
        execution_result=execution_result,
    )

    assert refreshed == execution_result
    assert client.execution_calls == []


@pytest.mark.asyncio
async def test_await_recent_evidence_completion_polls_and_refreshes_execution_stage():
    execution_result = (
        200,
        {
            "status": "complete",
            "stages": [
                {
                    "stage_name": "lineage_materialization",
                    "status": "in_progress",
                }
            ],
        },
    )
    refreshed_execution = (
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
    client = _EvidenceAnalyticsClient(
        execution_results=[refreshed_execution],
        lineage_results=[
            (
                200,
                {
                    "calculation_id": "calc-1",
                    "status": "complete",
                    "artifacts": {"response.json": {}},
                },
            )
        ],
    )

    refreshed_execution_result, refreshed_lineage_result = await await_recent_evidence_completion(
        analytics_client=client,
        calculation_id="calc-1",
        correlation_id="corr-1",
        execution_result=execution_result,
        lineage_result=(200, {"calculation_id": "calc-1", "status": "pending"}),
        poll_attempts=2,
        poll_interval_seconds=0,
    )

    assert refreshed_execution_result == refreshed_execution
    assert refreshed_lineage_result[1]["status"] == "complete"
    assert client.execution_calls == ["calc-1"]
    assert client.lineage_calls == ["calc-1"]


@pytest.mark.asyncio
async def test_await_recent_evidence_completion_covers_canonical_worker_latency_window():
    execution_result = (
        200,
        {
            "status": "running",
            "stages": [
                {
                    "stage_name": "lineage_materialization",
                    "status": "in_progress",
                }
            ],
        },
    )
    refreshed_execution = (
        200,
        {
            "status": "complete",
            "stages": [
                {
                    "stage_name": "lineage_materialization",
                    "status": "complete",
                    "completed_at_utc": "2026-08-01T14:03:04.701268Z",
                }
            ],
        },
    )
    client = _EvidenceAnalyticsClient(
        execution_results=[
            execution_result,
            execution_result,
            execution_result,
            refreshed_execution,
        ],
        lineage_results=[
            (200, {"calculation_id": "calc-1", "status": "pending", "artifacts": {}}),
            (200, {"calculation_id": "calc-1", "status": "in_progress", "artifacts": {}}),
            (200, {"calculation_id": "calc-1", "status": "pending", "artifacts": {}}),
            (
                200,
                {
                    "calculation_id": "calc-1",
                    "status": "complete",
                    "artifacts": {
                        "request.json": {},
                        "response.json": {},
                    },
                },
            ),
        ],
    )

    refreshed_execution_result, refreshed_lineage_result = await await_recent_evidence_completion(
        analytics_client=client,
        calculation_id="calc-1",
        correlation_id="corr-1",
        execution_result=execution_result,
        lineage_result=(200, {"calculation_id": "calc-1", "status": "pending"}),
        poll_interval_seconds=0,
    )

    assert refreshed_execution_result == refreshed_execution
    assert refreshed_lineage_result[1]["status"] == "complete"
    assert client.execution_calls == ["calc-1", "calc-1", "calc-1", "calc-1"]
    assert client.lineage_calls == ["calc-1", "calc-1", "calc-1", "calc-1"]


@pytest.mark.asyncio
async def test_fetch_calculation_evidence_returns_partial_lineage_evidence_after_poll_limit():
    client = _EvidenceAnalyticsClient(
        execution_results=[
            (
                200,
                {
                    "analytics_type": "WORKSPACE_SUMMARY",
                    "execution_mode": "sync",
                    "status": "complete",
                    "stages": [
                        {
                            "stage_name": "lineage_materialization",
                            "status": "in_progress",
                        }
                    ],
                    "upstream_snapshots": [],
                },
            ),
            (
                200,
                {
                    "analytics_type": "WORKSPACE_SUMMARY",
                    "execution_mode": "sync",
                    "status": "complete",
                    "stages": [
                        {
                            "stage_name": "lineage_materialization",
                            "status": "in_progress",
                        }
                    ],
                    "upstream_snapshots": [],
                },
            ),
        ],
        lineage_results=[
            (200, {"calculation_id": "calc-1", "status": "pending", "artifacts": {}}),
            (200, {"calculation_id": "calc-1", "status": "pending", "artifacts": {}}),
        ],
    )

    evidence = await fetch_calculation_evidence(
        analytics_client=client,
        portfolio_id="PORT-1",
        calculation_role="workspace_summary",
        calculation_id="calc-1",
        correlation_id="corr-1",
        poll_attempts=1,
        poll_interval_seconds=0,
    )

    assert evidence.calculation_role == "workspace_summary"
    assert evidence.execution_status == "complete"
    assert evidence.lineage_status == "pending"
    assert evidence.reason == "Lineage is pending in lotus-performance."
    assert client.execution_calls == ["calc-1", "calc-1"]
    assert client.lineage_calls == ["calc-1", "calc-1"]


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
        report_start_date="2026-01-01",
        report_end_date="2026-03-27",
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
    assert evidence.report_start_date == "2026-01-01"
    assert evidence.report_end_date == "2026-03-27"
    assert evidence.source_services == ["lotus-performance"]
    assert evidence.calculation_versions == {
        "gateway_contract": "v1",
        "analytics_types": "TWR",
    }


def test_artifact_url_and_status_reason_are_bounded():
    assert (
        gateway_evidence_artifact_url(
            portfolio_id="PORT-1",
            calculation_id="calc-1",
            artifact_name="request.json",
        )
        == "/api/v1/workbench/PORT-1/performance/evidence/artifacts/calc-1/request.json"
    )
    assert evidence_status_reason(503, {"detail": "upstream unavailable"}) == (
        "upstream unavailable"
    )
    assert evidence_status_reason(503, {}) == "HTTP_503"
    assert evidence_status_reason(200, {}) == "missing payload"
