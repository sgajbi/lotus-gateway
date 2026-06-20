import ast
from datetime import date
from pathlib import Path

from app.services.performance_workspace_attribution import (
    build_detail_attribution_summary,
    build_workspace_attribution_summary,
    parse_attribution_reasons,
    parse_attribution_residual_materiality,
    parse_attribution_result,
    parse_attribution_supportability_evidence,
    parse_attribution_trend_results,
)

_SERVICE_ROOT = Path(__file__).parents[2] / "src" / "app" / "services"


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def test_build_workspace_attribution_summary_maps_embedded_payload():
    summary = build_workspace_attribution_summary(
        {
            "attribution": {
                "metric_basis": "GROSS",
                "model": "BF",
                "linking": "carino",
                "benchmark_context": {
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "return_source": "calculated",
                },
                "result": {
                    "status": "partial",
                    "reason_codes": ["OFF_BENCHMARK_EXPOSURE"],
                    "reasons": [
                        {
                            "code": "OFF_BENCHMARK_EXPOSURE",
                            "severity": "warning",
                            "message": "Portfolio has off-benchmark exposure.",
                            "affected_group_count": 1,
                        }
                    ],
                    "reconciliation": {
                        "total_active_return": 0.42,
                        "sum_of_effects": 0.4,
                        "residual": 0.02,
                        "residual_materiality": {
                            "classification": "immaterial",
                            "treatment": "no_action",
                            "absolute_residual": 0.02,
                            "warning_threshold": 0.1,
                            "material_threshold": 0.5,
                        },
                    },
                    "supportability_evidence": {
                        "portfolio_only_group_count": 1,
                        "currency_attribution_status": "not_requested",
                        "linking_status": "linked",
                    },
                    "levels": [
                        {
                            "dimension": "asset_class",
                            "totals": {
                                "allocation": 0.1,
                                "selection": 0.2,
                                "interaction": 0.1,
                                "total_effect": 0.4,
                            },
                            "rows": [
                                {
                                    "key": {"asset_class": "Equity"},
                                    "portfolio_weight_avg": 0.6,
                                    "benchmark_weight_avg": 0.55,
                                    "portfolio_return": 5.0,
                                    "benchmark_return": 4.5,
                                    "allocation": 0.1,
                                    "selection": 0.2,
                                    "interaction": 0.1,
                                    "total_effect": 0.4,
                                }
                            ],
                        }
                    ],
                },
            }
        }
    )

    assert summary is not None
    assert summary.metric_basis == "GROSS"
    assert summary.status == "partial"
    assert summary.reasons[0].code == "OFF_BENCHMARK_EXPOSURE"
    assert summary.benchmark_id == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert summary.active_return_pct == 0.42
    assert summary.residual_materiality is not None
    assert summary.residual_materiality.material_threshold_pct == 0.5
    assert summary.supportability_evidence is not None
    assert summary.supportability_evidence.portfolio_only_group_count == 1
    assert summary.levels[0].dimension == "asset_class"
    assert summary.levels[0].rows[0].key_label == "Equity"
    assert summary.levels[0].rows[0].portfolio_weight_avg_pct == 60.0


def test_build_detail_attribution_summary_maps_group_payload():
    summary = build_detail_attribution_summary(
        metric_basis="NET",
        benchmark_context={
            "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
            "return_source": "assigned",
        },
        model="BF",
        linking="none",
        period_payload={
            "status": "valid",
            "reconciliation": {"total_active_return": 0.12345},
            "supportability_evidence": {
                "benchmark_only_group_count": 2,
                "currency_attribution_status": "not_requested",
                "linking_status": "not_requested",
            },
            "levels": [
                {
                    "dimension": "sector",
                    "groups": [
                        {
                            "key": {"sector": "Technology"},
                            "allocation": 0.11111,
                            "selection": 0.22222,
                            "interaction": 0.0,
                            "total_effect": 0.33333,
                        }
                    ],
                }
            ],
        },
    )

    assert summary.metric_basis == "NET"
    assert summary.benchmark_return_source == "assigned"
    assert summary.levels[0].rows[0].key_label == "Technology"
    assert summary.levels[0].rows[0].allocation_pct == 0.11111
    assert summary.levels[0].rows[0].total_effect_pct == 0.33333
    assert summary.supportability_evidence is not None
    assert summary.supportability_evidence.benchmark_only_group_count == 2


def test_parse_attribution_result_selects_requested_period_and_benchmark_context():
    warnings: list[str] = []
    partial_failures = []

    summary = parse_attribution_result(
        result=(
            200,
            {
                "model": "BF",
                "linking": "carino",
                "benchmark_context": {
                    "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
                    "return_source": "assigned",
                },
                "results_by_period": {
                    "YTD": {
                        "status": "valid",
                        "reconciliation": {
                            "total_active_return": 0.31,
                            "sum_of_effects": 0.3,
                            "residual": 0.01,
                        },
                        "levels": [
                            {
                                "dimension": "asset_class",
                                "groups": [
                                    {
                                        "key": {"asset_class": "Equity"},
                                        "allocation": 0.1,
                                        "selection": 0.2,
                                        "interaction": 0.0,
                                        "total_effect": 0.3,
                                    }
                                ],
                            }
                        ],
                    }
                },
            },
        ),
        metric_basis="NET",
        requested_period="YTD",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert summary is not None
    assert summary.metric_basis == "NET"
    assert summary.model == "BF"
    assert summary.linking == "carino"
    assert summary.benchmark_id == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert summary.benchmark_return_source == "assigned"
    assert summary.active_return_pct == 0.31
    assert summary.levels[0].rows[0].key_label == "Equity"
    assert warnings == []
    assert partial_failures == []


def test_parse_attribution_result_records_upstream_failure():
    warnings: list[str] = []
    partial_failures = []

    summary = parse_attribution_result(
        result=RuntimeError("timeout"),
        metric_basis="NET",
        requested_period="YTD",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert summary is None
    assert warnings == ["ATTRIBUTION_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-performance"
    assert partial_failures[0].error_code == "UPSTREAM_EXCEPTION"


def test_parse_attribution_result_bounds_http_failure_detail():
    warnings: list[str] = []
    partial_failures = []

    summary = parse_attribution_result(
        result=(
            503,
            {
                "detail": {
                    "code": "ATTRIBUTION_UNAVAILABLE",
                    "message": "attribution unavailable",
                    "debug_payload": {
                        "client_name": "Private Client",
                        "token": "secret-token",
                    },
                }
            },
        ),
        metric_basis="NET",
        requested_period="YTD",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert summary is None
    assert warnings == ["ATTRIBUTION_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-performance"
    assert partial_failures[0].error_code == "HTTP_503"
    assert partial_failures[0].detail == "ATTRIBUTION_UNAVAILABLE: attribution unavailable"
    assert "Private Client" not in str(partial_failures[0])
    assert "secret-token" not in str(partial_failures[0])


def test_parse_attribution_result_records_invalid_payload_warning():
    warnings: list[str] = []
    partial_failures = []

    summary = parse_attribution_result(
        result=(200, []),  # type: ignore[arg-type]
        metric_basis="NET",
        requested_period="YTD",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert summary is None
    assert warnings == ["ATTRIBUTION_INVALID"]
    assert partial_failures == []


def test_parse_attribution_trend_results_builds_cumulative_rows():
    warnings: list[str] = []
    partial_failures = []

    rows = parse_attribution_trend_results(
        results=[
            (
                200,
                {
                    "results_by_period": {
                        "EXPLICIT": {
                            "status": "valid",
                            "reason_codes": ["LINKED"],
                            "reconciliation": {
                                "total_active_return": 0.11,
                                "residual": 0.01,
                            },
                            "levels": [
                                {
                                    "totals": {
                                        "allocation": 0.1,
                                        "selection": 0.2,
                                        "interaction": 0.0,
                                        "total_effect": 0.3,
                                    }
                                }
                            ],
                        }
                    }
                },
            ),
            (
                200,
                {
                    "results_by_period": {
                        "EXPLICIT": {
                            "status": "partial",
                            "reconciliation": {
                                "total_active_return": 0.21,
                                "residual": 0.02,
                            },
                            "levels": [
                                {
                                    "totals": {
                                        "allocation": 0.05,
                                        "selection": 0.15,
                                        "interaction": 0.0,
                                        "total_effect": 0.2,
                                    }
                                }
                            ],
                        }
                    }
                },
            ),
        ],
        window_pairs=[
            (date(2026, 1, 1), date(2026, 1, 31)),
            (date(2026, 2, 1), date(2026, 2, 28)),
        ],
        chart_frequency="monthly",
        requested_period="EXPLICIT",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert len(rows) == 2
    assert rows[0].period_label == "2026-01"
    assert rows[0].total_effect_pct == 0.3
    assert rows[0].cumulative_total_effect_pct == 0.3
    assert rows[0].reason_codes == ["LINKED"]
    assert rows[1].period_label == "2026-02"
    assert rows[1].status == "partial"
    assert rows[1].cumulative_total_effect_pct == 0.5
    assert warnings == []
    assert partial_failures == []


def test_parse_attribution_trend_results_skips_failed_periods():
    warnings: list[str] = []
    partial_failures = []

    rows = parse_attribution_trend_results(
        results=[RuntimeError("timeout")],
        window_pairs=[(date(2026, 1, 1), date(2026, 1, 31))],
        chart_frequency="monthly",
        requested_period="EXPLICIT",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert rows == []
    assert warnings == ["ATTRIBUTION_TREND_PERIOD_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-performance"
    assert partial_failures[0].error_code == "UPSTREAM_EXCEPTION"


def test_attribution_parsers_fail_closed_for_invalid_payloads():
    assert build_workspace_attribution_summary({"attribution": []}) is None
    assert parse_attribution_reasons([]) == []
    assert parse_attribution_residual_materiality([]) is None
    assert parse_attribution_residual_materiality({"absolute_residual": 0.1}) is None
    assert parse_attribution_supportability_evidence([]) is None


def test_attribution_supportability_parsers_live_in_dedicated_module() -> None:
    attribution_methods = _function_names(_SERVICE_ROOT / "performance_workspace_attribution.py")
    supportability_methods = _function_names(
        _SERVICE_ROOT / "performance_workspace_attribution_supportability.py"
    )

    extracted_methods = {
        "parse_attribution_reasons",
        "parse_attribution_residual_materiality",
        "parse_attribution_supportability_evidence",
    }

    assert extracted_methods <= supportability_methods
    assert not extracted_methods & attribution_methods


def test_attribution_trend_parsers_live_in_dedicated_module() -> None:
    attribution_methods = _function_names(_SERVICE_ROOT / "performance_workspace_attribution.py")
    trend_methods = _function_names(_SERVICE_ROOT / "performance_workspace_attribution_trend.py")

    extracted_methods = {
        "build_attribution_trend_period_payload",
        "build_attribution_trend_row",
        "parse_attribution_trend_results",
        "parse_single_attribution_trend_row",
        "select_attribution_trend_period_payload",
        "unpack_attribution_trend_payload",
    }

    assert extracted_methods <= trend_methods
    assert not extracted_methods & attribution_methods
