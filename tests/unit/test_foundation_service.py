import pytest
from fastapi import HTTPException

from app.services.foundation_service import FoundationService


class _StubLotusCoreQueryClient:
    def __init__(
        self, list_payload: dict, snapshot_payload: dict, portfolio_payload: dict | None = None
    ):
        self.list_payload = list_payload
        self.snapshot_payload = snapshot_payload
        self.portfolio_payload = portfolio_payload or {}
        self.snapshot_calls: list[dict[str, object]] = []
        self.portfolio_calls: list[dict[str, object]] = []

    async def get_portfolio_lookups(self, correlation_id: str):
        return 200, self.list_payload

    async def get_portfolio(self, portfolio_id: str, correlation_id: str):
        self.portfolio_calls.append(
            {
                "portfolio_id": portfolio_id,
                "correlation_id": correlation_id,
            }
        )
        return 200, self.portfolio_payload

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        self.snapshot_calls.append(
            {
                "portfolio_id": portfolio_id,
                "as_of_date": as_of_date,
                "sections": sections,
                "consumer_system": consumer_system,
                "correlation_id": correlation_id,
            }
        )
        return 200, self.snapshot_payload


class _StubAnalyticsClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def get_stateful_twr(
        self,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        correlation_id: str,
    ):
        return self.status_code, self.payload


class _StubDpmClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def list_runs(self, params: dict, correlation_id: str):
        return self.status_code, self.payload


class _StubReportingClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def get_portfolio_snapshot(self, portfolio_id: str, as_of_date: str, correlation_id: str):
        return self.status_code, self.payload


@pytest.mark.asyncio
async def test_foundation_portfolio_catalog_success():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={
                "items": [
                    {
                        "portfolio_id": "PF_2002",
                        "portfolio_name": "Income",
                        "base_currency": "EUR",
                    },
                    {
                        "portfolio_id": "PF_1001",
                        "portfolio_name": "Alpha Growth",
                        "base_currency": "USD",
                    },
                ]
            },
            snapshot_payload={},
        ),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    response = await service.get_portfolio_catalog(correlation_id="corr-1")

    assert [item.portfolio_id for item in response.items] == ["PF_1001", "PF_2002"]
    assert response.items[0].display_name == "Alpha Growth"


@pytest.mark.asyncio
async def test_foundation_portfolio_catalog_preserves_identity_aliases():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={
                "items": [
                    {
                        "portfolio_id": "PF_2002",
                        "portfolio_name": "Income Reserve",
                        "base_currency": "EUR",
                        "cif_id": "CIF_2002",
                        "booking_center": "CHPB",
                    },
                    {
                        "id": "PF_1001",
                        "label": "Alpha Growth",
                        "base_currency": "USD",
                        "client_id": "CIF_1001",
                        "booking_center_code": "SGPB",
                    },
                ]
            },
            snapshot_payload={},
        ),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    response = await service.get_portfolio_catalog(correlation_id="corr-1b")

    assert [item.portfolio_id for item in response.items] == ["PF_1001", "PF_2002"]
    assert response.items[0].display_name == "Alpha Growth"
    assert response.items[0].client_id == "CIF_1001"
    assert response.items[0].booking_center_code == "SGPB"
    assert response.items[1].display_name == "Income Reserve"
    assert response.items[1].client_id == "CIF_2002"
    assert response.items[1].booking_center_code == "CHPB"


@pytest.mark.asyncio
async def test_foundation_workspace_success():
    lotus_core_client = _StubLotusCoreQueryClient(
        list_payload={"items": []},
        portfolio_payload={
            "portfolio_id": "PF_1001",
            "portfolio_name": "Alpha Growth",
            "base_currency": "USD",
            "booking_center": "SG",
            "cif_id": "CIF_1001",
        },
        snapshot_payload={
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-03-25",
            "valuation_context": {
                "portfolio_currency": "USD",
                "reporting_currency": "USD",
                "position_basis": "market_value_base",
                "weight_basis": "total_market_value_base",
            },
            "sections": {
                "positions_baseline": [
                    {"security_id": "EQ_1", "market_value_base": 700.0},
                    {"security_id": "CASH_1", "market_value_base": 100.0},
                ],
                "portfolio_totals": {
                    "baseline_total_market_value_base": 1000.0,
                    "baseline_total_cash_base": 100.0,
                },
                "instrument_enrichment": [
                    {"security_id": "EQ_1", "asset_class": "Equity"},
                    {"security_id": "CASH_1", "asset_class": "Cash"},
                ],
            },
        },
    )
    service = FoundationService(
        lotus_core_query_client=lotus_core_client,
        analytics_client=_StubAnalyticsClient(
            200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 4.3}}}
        ),
        dpm_client=_StubDpmClient(
            200,
            {
                "items": [
                    {
                        "rebalance_run_id": "rr_1",
                        "status": "READY",
                        "created_at": "2026-03-25T08:00:00Z",
                    }
                ]
            },
        ),
        reporting_client=_StubReportingClient(
            200,
            {
                "generatedAt": "2026-03-25T09:00:00Z",
                "rows": [{"metric": "market_value_base"}],
            },
        ),
    )

    response = await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-2",
    )

    assert response.portfolio.display_name == "Alpha Growth"
    assert response.portfolio.client_id == "CIF_1001"
    assert response.portfolio.base_currency == "USD"
    assert response.portfolio.booking_center_code == "SG"
    assert response.summary.market_value_base == 1000.0
    assert response.summary.total_cash_base == 100.0
    assert response.summary.cash_weight_pct == 10.0
    assert response.summary.position_count == 2
    assert response.allocations[0].asset_class == "Cash"
    assert response.allocations[0].market_value_base == 100.0
    assert response.allocations[0].weight_pct == 10.0
    assert response.top_positions[0].display_name == "EQ_1"
    assert response.top_positions[0].market_value_base == 700.0
    assert response.top_positions[0].weight_pct == 70.0
    assert lotus_core_client.portfolio_calls[0]["portfolio_id"] == "PF_1001"
    assert lotus_core_client.snapshot_calls[0]["portfolio_id"] == "PF_1001"
    assert lotus_core_client.snapshot_calls[0]["sections"] == [
        "positions_baseline",
        "portfolio_totals",
        "instrument_enrichment",
    ]
    assert lotus_core_client.snapshot_calls[0]["consumer_system"] == "lotus-gateway"
    assert response.performance is not None
    assert response.performance.return_pct == 4.3
    assert response.rebalance is not None
    assert response.rebalance.status == "READY"
    assert response.rebalance.last_run_at_utc == "2026-03-25T08:00:00Z"
    assert response.rebalance.last_rebalance_run_id == "rr_1"
    assert response.readiness.has_positions is True
    assert response.readiness.reporting.status == "READY"
    assert response.readiness.reporting.generated_at_utc == "2026-03-25T09:00:00Z"
    assert response.readiness.reporting.row_count == 1
    assert response.workflow_cues[0].key == "performance"
    assert response.workflow_cues[0].href == "/app/performance?portfolioId=PF_1001"
    assert response.workflow_cues[1].key == "risk"
    assert response.workflow_cues[2].key == "proposal"
    assert response.evidence.status == "ready"
    assert response.evidence.warning_count == 0
    assert response.evidence.partial_failure_count == 0
    assert response.partial_failures == []


@pytest.mark.asyncio
async def test_foundation_workspace_degrades_when_optional_upstreams_fail():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"items": []},
            portfolio_payload={
                "portfolio_id": "PF_1001",
                "portfolio_name": "Alpha Growth",
                "base_currency": "USD",
            },
            snapshot_payload={
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-03-25",
                "sections": {
                    "positions_baseline": [{"security_id": "EQ_1", "market_value_base": 450.0}],
                    "portfolio_totals": {
                        "baseline_total_market_value_base": 500.0,
                        "baseline_total_cash_base": 50.0,
                    },
                    "instrument_enrichment": [{"security_id": "EQ_1", "asset_class": "Equity"}],
                },
            },
        ),
        analytics_client=_StubAnalyticsClient(503, {"detail": "lotus-performance unavailable"}),
        dpm_client=_StubDpmClient(500, {"detail": "dpm unavailable"}),
        reporting_client=_StubReportingClient(503, {"detail": "reporting unavailable"}),
    )

    response = await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-3",
    )

    assert response.performance is None
    assert response.rebalance is None
    assert response.readiness.reporting.status == "UNAVAILABLE"
    assert response.warnings == [
        "FOUNDATION_PERFORMANCE_UNAVAILABLE",
        "FOUNDATION_REBALANCE_UNAVAILABLE",
        "FOUNDATION_REPORTING_UNAVAILABLE",
    ]
    assert len(response.partial_failures) == 3


@pytest.mark.asyncio
async def test_foundation_catalog_rejects_invalid_items_payload():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"items": {"portfolio_id": "PF_1001"}},
            snapshot_payload={},
        ),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_portfolio_catalog(correlation_id="corr-invalid-items")

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Invalid lotus-core portfolio catalog payload structure."


@pytest.mark.asyncio
async def test_foundation_catalog_rejects_item_without_portfolio_id():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"items": [{"portfolio_name": "Missing identifier"}]},
            snapshot_payload={},
        ),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_portfolio_catalog(correlation_id="corr-missing-id")

    assert exc_info.value.status_code == 502
    assert (
        exc_info.value.detail == "Invalid lotus-core portfolio catalog item without portfolio_id."
    )


@pytest.mark.asyncio
async def test_foundation_workspace_rejects_invalid_snapshot_payload():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"items": []},
            portfolio_payload={"portfolio_id": "PF_1001", "base_currency": "USD"},
            snapshot_payload={"portfolio": [], "sections": "invalid"},
        ),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_portfolio_workspace(
            portfolio_id="PF_INVALID",
            correlation_id="corr-invalid-snapshot",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Invalid lotus-core foundation snapshot payload structure."


@pytest.mark.asyncio
async def test_foundation_workspace_handles_invalid_optional_upstream_payloads():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"items": []},
            portfolio_payload={"portfolio_id": "PF_1001", "portfolio_name": "Alpha Growth"},
            snapshot_payload={
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-03-25",
                "sections": {
                    "positions_baseline": [{"security_id": "EQ_1", "market_value_base": 450.0}],
                    "portfolio_totals": {
                        "baseline_total_market_value_base": 500.0,
                        "baseline_total_cash_base": 50.0,
                    },
                    "instrument_enrichment": [{"security_id": "EQ_1", "asset_class": "Equity"}],
                },
            },
        ),
        analytics_client=_StubAnalyticsClient(200, {"resultsByPeriod": []}),
        dpm_client=_StubDpmClient(200, "unexpected"),
        reporting_client=_StubReportingClient(
            200, {"generatedAt": "2026-03-25T09:00:00Z", "rows": "invalid"}
        ),
    )

    response = await service.get_portfolio_workspace(
        portfolio_id="PF_1001",
        correlation_id="corr-invalid-optional",
    )

    assert response.performance is None
    assert response.rebalance is None
    assert response.readiness.reporting.status == "EMPTY"
    assert response.readiness.reporting.row_count == 0
    assert response.warnings == [
        "FOUNDATION_PERFORMANCE_INVALID",
        "FOUNDATION_REBALANCE_UNAVAILABLE",
    ]
    assert len(response.partial_failures) == 1
    assert response.partial_failures[0].source_service == "lotus-manage"
    assert response.partial_failures[0].error_code == "INVALID_UPSTREAM_PAYLOAD"


@pytest.mark.asyncio
async def test_foundation_workspace_records_optional_upstream_exception():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"items": []},
            portfolio_payload={"portfolio_id": "PF_1001", "portfolio_name": "Alpha Growth"},
            snapshot_payload={
                "portfolio_id": "PF_1001",
                "as_of_date": "2026-03-25",
                "sections": {
                    "positions_baseline": [{"security_id": "EQ_1", "market_value_base": 450.0}],
                    "portfolio_totals": {
                        "baseline_total_market_value_base": 500.0,
                        "baseline_total_cash_base": 50.0,
                    },
                    "instrument_enrichment": [{"security_id": "EQ_1", "asset_class": "Equity"}],
                },
            },
        ),
        analytics_client=_StubAnalyticsClient(
            200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 1.2}}}
        ),
        dpm_client=_StubDpmClient(200, {"items": []}),
        reporting_client=_StubReportingClient(200, {"rows": []}),
    )

    warnings: list[str] = []
    partial_failures = []

    response = service._parse_reporting_result(
        result=RuntimeError("report exploded"),
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert response.status == "UNAVAILABLE"
    assert warnings == ["FOUNDATION_REPORTING_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-report"
    assert partial_failures[0].error_code == "UPSTREAM_EXCEPTION"


@pytest.mark.asyncio
async def test_foundation_catalog_rejects_upstream_error():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"detail": "catalog unavailable"},
            snapshot_payload={},
        ),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    async def _raise_catalog_error(correlation_id: str):
        return 503, {"detail": "catalog unavailable"}

    service._lotus_core_query_client.get_portfolio_lookups = _raise_catalog_error  # type: ignore[method-assign]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_portfolio_catalog(correlation_id="corr-catalog-503")

    assert exc_info.value.status_code == 502
    assert "lotus-core portfolio catalog unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_foundation_workspace_rejects_snapshot_upstream_error():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"items": []},
            snapshot_payload={"detail": "snapshot unavailable"},
        ),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    async def _raise_snapshot_error(
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        return 503, {"detail": "snapshot unavailable"}

    service._lotus_core_query_client.get_core_snapshot = _raise_snapshot_error  # type: ignore[method-assign]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_portfolio_workspace(
            portfolio_id="PF_503",
            correlation_id="corr-snapshot-503",
        )

    assert exc_info.value.status_code == 502
    assert "lotus-core foundation snapshot unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_foundation_workspace_rejects_portfolio_identity_upstream_error():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient(
            list_payload={"items": []},
            portfolio_payload={"detail": "portfolio unavailable"},
            snapshot_payload={"portfolio_id": "PF_503", "sections": {}},
        ),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    async def _raise_portfolio_error(portfolio_id: str, correlation_id: str):
        return 503, {"detail": "portfolio unavailable"}

    service._lotus_core_query_client.get_portfolio = _raise_portfolio_error  # type: ignore[method-assign]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_portfolio_workspace(
            portfolio_id="PF_503",
            correlation_id="corr-portfolio-503",
        )

    assert exc_info.value.status_code == 502
    assert "lotus-core portfolio identity unavailable" in exc_info.value.detail


def test_foundation_parses_defensive_snapshot_branches():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient({"items": []}, {}),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    portfolio, summary, allocations, top_positions, as_of_date = service._parse_core_snapshot(
        fallback_portfolio_id="PF_FALLBACK",
        fallback_as_of_date="2026-03-31",
        portfolio_payload={"name": "Fallback Name"},
        payload={
            "portfolio_id": "PF_FALLBACK",
            "as_of_date": "2026-03-30",
            "valuation_context": {"portfolio_currency": "EUR"},
            "sections": {
                "positions_baseline": [
                    "skip-me",
                    {"security_id": None, "asset_class": "Alternatives", "value_base": "125.55"},
                    {"security_id": "EQ_1", "valuation": {"market_value_base": "374.45"}},
                ],
                "portfolio_totals": [],
                "instrument_enrichment": [
                    "skip-me",
                    {"security_id": "EQ_1", "asset_class_name": "Equity"},
                ],
            },
        },
    )

    assert portfolio.portfolio_id == "PF_FALLBACK"
    assert portfolio.display_name == "Fallback Name"
    assert portfolio.base_currency == "EUR"
    assert summary.market_value_base == 0.0
    assert len(top_positions) == 2
    assert summary.position_count == 2
    assert [bucket.asset_class for bucket in allocations] == ["Alternatives", "Equity"]
    assert allocations[0].weight_pct is None
    assert allocations[1].market_value_base == 374.45
    assert as_of_date == "2026-03-30"


def test_foundation_snapshot_parser_ignores_legacy_nested_portfolio_and_metadata():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient({"items": []}, {}),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    portfolio, _summary, _allocations, _top_positions, as_of_date = service._parse_core_snapshot(
        fallback_portfolio_id="PF_IGNORED",
        fallback_as_of_date="2026-03-31",
        portfolio_payload={
            "portfolio_id": "PF_IDENTITY",
            "portfolio_name": "Identity Name",
            "base_currency": "USD",
        },
        payload={
            "portfolio_id": "PF_SNAPSHOT",
            "as_of_date": "2026-03-30",
            "portfolio": {"portfolio_id": "PF_LEGACY", "portfolio_name": "Legacy Name"},
            "metadata": {"business_date": "1999-01-01"},
            "sections": {
                "positions_baseline": [],
                "portfolio_totals": {},
                "instrument_enrichment": [],
            },
        },
    )

    assert portfolio.portfolio_id == "PF_SNAPSHOT"
    assert portfolio.display_name == "Identity Name"
    assert as_of_date == "2026-03-30"


def test_foundation_parses_optional_result_edge_cases():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient({"items": []}, {}),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    warnings: list[str] = []
    partial_failures = []
    assert (
        service._parse_performance_result(
            (200, {"resultsByPeriod": {}}), warnings, partial_failures
        )
        is None
    )
    assert warnings == []

    warnings = []
    partial_failures = []
    assert (
        service._parse_performance_result(
            (200, {"resultsByPeriod": {"QTD": []}}),
            warnings,
            partial_failures,
        )
        is None
    )
    assert warnings == []

    warnings = []
    partial_failures = []
    rebalance = service._parse_rebalance_result(
        (200, {"items": ["bad-row"]}),
        warnings,
        partial_failures,
    )
    assert rebalance is not None
    assert rebalance.status == "NOT_AVAILABLE"

    warnings = []
    partial_failures = []
    status_code, payload = service._unpack_optional_upstream(
        result="invalid-response",
        source_service="lotus-manage",
        unavailable_warning="FOUNDATION_REBALANCE_UNAVAILABLE",
        warnings=warnings,
        partial_failures=partial_failures,
    )
    assert status_code is None
    assert payload is None
    assert warnings == ["FOUNDATION_REBALANCE_UNAVAILABLE"]
    assert partial_failures[0].error_code == "INVALID_UPSTREAM_RESPONSE"

    warnings = []
    partial_failures = []
    status_code, payload = service._unpack_optional_upstream(
        result=(503, {"detail": "service down"}),
        source_service="lotus-report",
        unavailable_warning="FOUNDATION_REPORTING_UNAVAILABLE",
        warnings=warnings,
        partial_failures=partial_failures,
    )
    assert status_code == 503
    assert payload is None
    assert warnings == ["FOUNDATION_REPORTING_UNAVAILABLE"]
    assert partial_failures[0].error_code == "HTTP_503"


def test_foundation_extracts_market_value_and_workflow_cues():
    service = FoundationService(
        lotus_core_query_client=_StubLotusCoreQueryClient({"items": []}, {}),
        analytics_client=_StubAnalyticsClient(200, {}),
        dpm_client=_StubDpmClient(200, {}),
        reporting_client=_StubReportingClient(200, {}),
    )

    assert service._extract_market_value({"valuation": {"market_value": "88.10"}}) == 88.1
    assert (
        service._extract_market_value(
            {"valuation": {"market_value_base": "bad"}, "current_value": "45.25"}
        )
        == 45.25
    )
    assert (
        service._extract_market_value({"market_value_base": "bad", "value_base": "17.75"}) == 17.75
    )
    assert service._extract_market_value({"valuation": {"market_value_base": "bad"}}) is None

    cues = service._build_workflow_cues("PF_1001")
    assert [cue.key for cue in cues] == ["performance", "risk", "proposal"]
    assert cues[0].href == "/app/performance?portfolioId=PF_1001"
