import json
from typing import Any

import httpx
from fastapi.testclient import TestClient

from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.main import app
from app.services.portfolio_service import PortfolioService


def _contributor(
    security_id: str,
    value: str | None,
    bucket_weight: str | None,
) -> dict[str, Any]:
    return {
        "contributor_type": "direct_position",
        "portfolio_id": "PF_CORE_QUALIFIED",
        "security_id": security_id,
        "booked_security_id": security_id,
        "source_snapshot_id": 101,
        "component_record_id": None,
        "component_weight": None,
        "component_effective_from": None,
        "component_effective_to": None,
        "component_source_system": None,
        "component_source_record_id": None,
        "market_value_reporting_currency": value,
        "bucket_weight": bucket_weight,
    }


def _allocation_payload(scenario: str) -> dict[str, Any]:
    if scenario in {"unknown", "contradictory"}:
        total, bond_value, equity_weight, bond_weight = None, None, None, None
        state, reason, valued, unvalued = "PARTIAL", "market_value_missing", 1, 1
    elif scenario == "signed":
        total, bond_value, equity_weight, bond_weight = "80", "-20", "1.25", "-0.25"
        state, reason, valued, unvalued = "COMPLETE", "all_source_positions_covered", 2, 0
    else:
        total, bond_value, equity_weight, bond_weight = "100", "0", "1", "0"
        if scenario == "carry-forward":
            state = "CARRY_FORWARD"
        elif scenario == "invalid-measured-zero":
            state = "MEASURED_ZERO"
        else:
            state = "COMPLETE"
        reason = (
            "latest_source_snapshot_precedes_as_of_date"
            if scenario == "carry-forward"
            else "all_source_positions_covered"
        )
        valued, unvalued = 2, 0

    bond_residual = None if bond_value is None else "0"
    payload = {
        "scope_type": "portfolio",
        "scope": {"portfolio_id": "PF_CORE_QUALIFIED"},
        "resolved_as_of_date": "2026-04-09",
        "reporting_currency": "USD",
        "total_market_value_reporting_currency": total,
        "valuation_coverage": {
            "coverage_state": state,
            "coverage_reason": reason,
            "snapshot_row_count": 2,
            "expected_open_position_count": 2,
            "valued_position_count": valued,
            "unvalued_position_count": unvalued,
        },
        "look_through": {
            "requested_mode": "direct_only",
            "applied_mode": "direct_only",
            "supported": False,
            "decomposed_position_count": 0,
            "limitation_reason": None,
        },
        "calculation_lineage": {
            "algorithm_id": "PORTFOLIO_ALLOCATION",
            "algorithm_version": 1,
            "intermediate_precision": 28,
            "input_content_hash": ("1" if scenario == "unknown" else "2") * 64,
            "calculation_content_hash": "b" * 64,
            "output_content_hash": "c" * 64,
            "numeric_output_policy": None,
        },
        "views": [
            {
                "dimension": dimension,
                "total_market_value_reporting_currency": (
                    "100" if scenario == "contradictory" else total
                ),
                "buckets": [
                    {
                        "dimension_value": "EQUITY",
                        "market_value_reporting_currency": "100",
                        "weight": equity_weight,
                        "position_count": 1,
                        "contributor_count": 1,
                        "contributors": [_contributor("EQ_1", "100", "1")],
                        "contributors_truncated": False,
                        "omitted_market_value_reporting_currency": "0",
                    },
                    {
                        "dimension_value": "BOND",
                        "market_value_reporting_currency": bond_value,
                        "weight": bond_weight,
                        "position_count": 1,
                        "contributor_count": 1,
                        "contributors": [
                            _contributor(
                                "BOND_1",
                                bond_value,
                                None if bond_value in {None, "0"} else "1",
                            )
                        ],
                        "contributors_truncated": False,
                        "omitted_market_value_reporting_currency": bond_residual,
                    },
                ],
            }
            for dimension in ["asset_class", "currency", "sector", "region"]
        ],
    }
    if scenario == "measured-zero":
        payload["total_market_value_reporting_currency"] = "0"
        payload["valuation_coverage"]["coverage_state"] = "MEASURED_ZERO"
        for view in payload["views"]:
            view["total_market_value_reporting_currency"] = "0"
            for bucket in view["buckets"]:
                bucket["market_value_reporting_currency"] = "0"
                bucket["weight"] = None
                bucket["omitted_market_value_reporting_currency"] = "0"
                bucket["contributors"][0]["market_value_reporting_currency"] = "0"
                bucket["contributors"][0]["bucket_weight"] = None
    elif scenario == "wrong-scope":
        payload["scope"] = {"portfolio_id": "PF_OTHER"}
    elif scenario == "invalid-degraded-weight":
        payload = _allocation_payload("unknown")
        payload["views"][0]["buckets"][0]["weight"] = "1"
    elif scenario == "invalid-coverage-counts":
        payload["valuation_coverage"]["unvalued_position_count"] = 1
    elif scenario == "invalid-residual-qualification":
        payload["views"][0]["buckets"][0]["omitted_market_value_reporting_currency"] = None
    elif scenario == "invalid-contributor-portfolio":
        payload["views"][0]["buckets"][0]["contributors"][0]["portfolio_id"] = "PF_OTHER"
    elif scenario == "invalid-look-through-mode":
        payload["look_through"]["requested_mode"] = "prefer_look_through"
    elif scenario == "invalid-applied-look-through-mode":
        payload["look_through"]["applied_mode"] = "prefer_look_through"
    elif scenario == "invalid-direct-only-component":
        payload["views"][0]["buckets"][0]["contributors"][0]["contributor_type"] = (
            "look_through_component"
        )
    elif scenario == "invalid-direct-only-decomposition":
        payload["look_through"]["decomposed_position_count"] = 1
    elif scenario == "invalid-trusted-bucket-value":
        payload["views"][0]["buckets"][0]["market_value_reporting_currency"] = None
        payload["views"][0]["buckets"][0]["omitted_market_value_reporting_currency"] = None
    elif scenario == "invalid-trusted-bucket-weight":
        payload["views"][0]["buckets"][0]["weight"] = None
    elif scenario == "invalid-contributor-weight-without-bucket":
        payload = _allocation_payload("unknown")
        payload["views"][0]["buckets"][1]["contributors"][0]["bucket_weight"] = "1"
    elif scenario == "invalid-bucket-weight-arithmetic":
        payload["views"][0]["buckets"][0]["weight"] = "0.5"
        payload["views"][0]["buckets"][1]["weight"] = "0.5"
    elif scenario == "invalid-contributor-weight-arithmetic":
        payload["views"][0]["buckets"][0]["contributors"][0]["bucket_weight"] = "0.01"
    elif scenario == "invalid-loaded-empty-bucket":
        payload["total_market_value_reporting_currency"] = "0"
        payload["valuation_coverage"] = {
            "coverage_state": "LOADED_EMPTY",
            "coverage_reason": "source_snapshot_has_no_open_positions",
            "snapshot_row_count": 0,
            "expected_open_position_count": 0,
            "valued_position_count": 0,
            "unvalued_position_count": 0,
        }
        for view in payload["views"]:
            view["total_market_value_reporting_currency"] = "0"
    elif scenario == "invalid-unavailable-bucket":
        payload = _allocation_payload("unknown")
        payload["valuation_coverage"] = {
            "coverage_state": "UNAVAILABLE",
            "coverage_reason": "source_snapshot_unavailable",
            "snapshot_row_count": 0,
            "expected_open_position_count": 2,
            "valued_position_count": 0,
            "unvalued_position_count": 0,
        }
    elif scenario == "invalid-view-bucket-total":
        bond_bucket = payload["views"][0]["buckets"][1]
        bond_bucket["market_value_reporting_currency"] = "10"
        bond_bucket["weight"] = "0.1"
        bond_bucket["contributors"][0]["market_value_reporting_currency"] = "10"
        bond_bucket["contributors"][0]["bucket_weight"] = "1"
        bond_bucket["omitted_market_value_reporting_currency"] = "0"
    elif scenario == "invalid-numeric-policy-arithmetic":
        payload = _allocation_payload("signed")
        payload["total_market_value_reporting_currency"] = "1"
        payload["calculation_lineage"]["numeric_output_policy"] = {
            "name": "allocation-output",
            "version": "1.0.0",
            "precision": 1,
            "scale": 1,
            "working_precision": 1,
            "rounding": "ROUND_HALF_EVEN",
        }
        for view in payload["views"]:
            view["total_market_value_reporting_currency"] = "1"
        bond_bucket = payload["views"][0]["buckets"][1]
        bond_bucket["market_value_reporting_currency"] = "-99"
        bond_bucket["weight"] = "-99"
        bond_bucket["contributors"][0]["market_value_reporting_currency"] = "-99"
        bond_bucket["omitted_market_value_reporting_currency"] = "0"
    elif scenario == "invalid-zero-rounding-policy":
        payload = _allocation_payload("measured-zero")
        payload["calculation_lineage"]["numeric_output_policy"] = {
            "name": "allocation-output",
            "version": "1.0.0",
            "precision": 18,
            "scale": 8,
            "working_precision": 28,
            "rounding": "NOT_A_ROUNDING_MODE",
        }
    elif scenario == "numeric-policy":
        payload["calculation_lineage"]["numeric_output_policy"] = {
            "name": "allocation-output",
            "version": "1.0.0",
            "precision": 18,
            "scale": 8,
            "working_precision": 28,
            "rounding": "ROUND_HALF_EVEN",
        }
    elif scenario == "invalid-numeric-output-magnitude":
        payload["calculation_lineage"]["numeric_output_policy"] = {
            "name": "allocation-output",
            "version": "1.0.0",
            "precision": 3,
            "scale": 2,
            "working_precision": 6,
            "rounding": "ROUND_HALF_EVEN",
        }
    elif scenario == "invalid-numeric-output-scale":
        payload["calculation_lineage"]["numeric_output_policy"] = {
            "name": "allocation-output",
            "version": "1.0.0",
            "precision": 6,
            "scale": 2,
            "working_precision": 12,
            "rounding": "ROUND_HALF_EVEN",
        }
        equity_bucket = payload["views"][0]["buckets"][0]
        equity_bucket["contributors"][0]["market_value_reporting_currency"] = "99.999"
        equity_bucket["contributors"][0]["bucket_weight"] = "1.00"
        equity_bucket["omitted_market_value_reporting_currency"] = "0.001"
    return payload


def test_registered_route_preserves_core_qualified_allocation_shapes(monkeypatch) -> None:
    allocation_requests: list[dict[str, Any]] = []
    active_scenario = ["unknown"]

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/reporting/assets-under-management/query":
            return httpx.Response(
                200,
                json={
                    "resolved_as_of_date": (
                        "2026-04-08" if active_scenario[0] == "invalid-aum-date" else "2026-04-09"
                    ),
                    "portfolios": [
                        {
                            "portfolio_id": "PF_CORE_QUALIFIED",
                            "aum_reporting_currency": "1000",
                            "position_count": 2,
                        }
                    ],
                },
            )
        if request.url.path == "/portfolios/PF_CORE_QUALIFIED/positions":
            return httpx.Response(
                200,
                json={
                    "positions": [
                        {
                            "security_id": "CASH_USD",
                            "asset_class": "Cash",
                            "valuation": {"market_value_base": "100"},
                        }
                    ]
                },
            )
        assert request.url.path == "/reporting/asset-allocation/query"
        source_request = json.loads(request.content)
        allocation_requests.append(source_request)
        return httpx.Response(200, json=_allocation_payload(active_scenario[0]))

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            **kwargs,
            transport=httpx.MockTransport(respond),
        ),
    )
    core_client = LotusCoreQueryClient(
        base_url="https://core.test",
        timeout_seconds=2,
        max_retries=0,
        retry_backoff_seconds=0,
    )
    service = PortfolioService(core_client, upstream_cache_ttl_seconds=-1)

    async def query_asset_allocation(**kwargs):
        return await LotusCoreQueryClient.query_asset_allocation(
            core_client,
            **kwargs,
        )

    monkeypatch.setattr(core_client, "query_asset_allocation", query_asset_allocation)
    monkeypatch.setattr("app.routers.portfolio_allocations.portfolio_service", lambda: service)

    client = TestClient(app)

    def get_scenario(scenario: str) -> httpx.Response:
        active_scenario[0] = scenario
        return client.get(
            "/api/v1/portfolio/portfolios/PF_CORE_QUALIFIED/allocations",
            params={"as_of_date": "2026-04-09", "reporting_currency": "USD"},
        )

    unknown = get_scenario("unknown").json()
    zero = get_scenario("zero").json()
    measured_zero = get_scenario("measured-zero").json()
    signed = get_scenario("signed").json()
    carry_forward = get_scenario("carry-forward").json()
    valid_numeric_policy_response = get_scenario("numeric-policy")
    valid_numeric_policy = valid_numeric_policy_response.json()
    contradictory = get_scenario("contradictory")
    wrong_scope = get_scenario("wrong-scope")
    invalid_measured_zero = get_scenario("invalid-measured-zero")
    invalid_degraded_weight = get_scenario("invalid-degraded-weight")
    invalid_coverage_counts = get_scenario("invalid-coverage-counts")
    invalid_residual_qualification = get_scenario("invalid-residual-qualification")
    invalid_contributor_portfolio = get_scenario("invalid-contributor-portfolio")
    invalid_look_through_mode = get_scenario("invalid-look-through-mode")
    invalid_applied_look_through_mode = get_scenario("invalid-applied-look-through-mode")
    invalid_direct_only_component = get_scenario("invalid-direct-only-component")
    invalid_direct_only_decomposition = get_scenario("invalid-direct-only-decomposition")
    invalid_trusted_bucket_value = get_scenario("invalid-trusted-bucket-value")
    invalid_trusted_bucket_weight = get_scenario("invalid-trusted-bucket-weight")
    invalid_contributor_weight_without_bucket = get_scenario(
        "invalid-contributor-weight-without-bucket"
    )
    invalid_bucket_weight_arithmetic = get_scenario("invalid-bucket-weight-arithmetic")
    invalid_contributor_weight_arithmetic = get_scenario("invalid-contributor-weight-arithmetic")
    invalid_loaded_empty_bucket = get_scenario("invalid-loaded-empty-bucket")
    invalid_unavailable_bucket = get_scenario("invalid-unavailable-bucket")
    invalid_view_bucket_total = get_scenario("invalid-view-bucket-total")
    invalid_aum_date = get_scenario("invalid-aum-date")
    invalid_numeric_policy_arithmetic = get_scenario("invalid-numeric-policy-arithmetic")
    invalid_zero_rounding_policy = get_scenario("invalid-zero-rounding-policy")
    invalid_numeric_output_magnitude = get_scenario("invalid-numeric-output-magnitude")
    invalid_numeric_output_scale = get_scenario("invalid-numeric-output-scale")

    unknown_buckets = {item["bucket"]: item for item in unknown["views"][0]["buckets"]}
    assert unknown["valuation_coverage"]["coverage_state"] == "PARTIAL"
    assert unknown["total_market_value_reporting_currency"] is None
    assert unknown_buckets["EQUITY"]["market_value_reporting_currency"] == "100"
    assert unknown_buckets["EQUITY"]["weight_pct"] is None
    assert unknown_buckets["BOND"]["market_value_reporting_currency"] is None
    assert unknown_buckets["BOND"]["market_value_base"] is None
    assert unknown_buckets["BOND"]["contributors"][0]["market_value_reporting_currency"] is None
    assert unknown_buckets["BOND"]["omitted_market_value_reporting_currency"] is None
    assert unknown["calculation_lineage"]["input_content_hash"] == "1" * 64

    zero_buckets = {item["bucket"]: item for item in zero["views"][0]["buckets"]}
    assert zero["total_market_value_reporting_currency"] == "100"
    assert zero_buckets["BOND"]["market_value_reporting_currency"] == "0"
    assert zero_buckets["BOND"]["weight_pct"] == 0.0
    assert measured_zero["valuation_coverage"]["coverage_state"] == "MEASURED_ZERO"
    assert measured_zero["total_market_value_reporting_currency"] == "0"
    assert all(
        bucket["weight_pct"] is None
        for view in measured_zero["views"]
        for bucket in view["buckets"]
    )

    signed_buckets = {item["bucket"]: item for item in signed["views"][0]["buckets"]}
    assert signed["total_market_value_reporting_currency"] == "80"
    assert signed_buckets["EQUITY"]["weight_pct"] == 125.0
    assert signed_buckets["BOND"]["weight_pct"] == -25.0
    assert carry_forward["valuation_coverage"]["coverage_state"] == "CARRY_FORWARD"
    assert valid_numeric_policy_response.status_code == 200
    assert valid_numeric_policy["calculation_lineage"]["numeric_output_policy"]["scale"] == 8
    assert contradictory.status_code == 502
    assert contradictory.json()["detail"]["error_code"] == "PORTFOLIO_ALLOCATION_CONTRACT_INVALID"
    assert wrong_scope.status_code == 502
    assert wrong_scope.json()["detail"]["error_code"] == "PORTFOLIO_ALLOCATION_CONTRACT_INVALID"
    assert invalid_measured_zero.status_code == 502
    assert (
        invalid_measured_zero.json()["detail"]["error_code"]
        == "PORTFOLIO_ALLOCATION_CONTRACT_INVALID"
    )
    for invalid_response in (
        invalid_degraded_weight,
        invalid_coverage_counts,
        invalid_residual_qualification,
        invalid_contributor_portfolio,
        invalid_look_through_mode,
        invalid_applied_look_through_mode,
        invalid_direct_only_component,
        invalid_direct_only_decomposition,
        invalid_trusted_bucket_value,
        invalid_trusted_bucket_weight,
        invalid_contributor_weight_without_bucket,
        invalid_bucket_weight_arithmetic,
        invalid_contributor_weight_arithmetic,
        invalid_loaded_empty_bucket,
        invalid_unavailable_bucket,
        invalid_view_bucket_total,
        invalid_aum_date,
        invalid_numeric_policy_arithmetic,
        invalid_zero_rounding_policy,
        invalid_numeric_output_magnitude,
        invalid_numeric_output_scale,
    ):
        assert invalid_response.status_code == 502
        assert (
            invalid_response.json()["detail"]["error_code"]
            == "PORTFOLIO_ALLOCATION_CONTRACT_INVALID"
        )
    assert len(allocation_requests) == 30
    assert all(
        request["dimensions"] == ["asset_class", "currency", "sector", "region"]
        for request in allocation_requests
    )
