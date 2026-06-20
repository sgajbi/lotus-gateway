"""Run deterministic Gateway demo-readiness certification and write evidence."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
sys.path = [str(SRC_ROOT), *[entry for entry in sys.path if entry != str(SRC_ROOT)]]

from fastapi.testclient import TestClient  # noqa: E402

from app.clients.advise_client import AdviseClient  # noqa: E402
from app.clients.dpm_client import DpmClient  # noqa: E402
from app.clients.lotus_analytics_client import LotusAnalyticsClient  # noqa: E402
from app.clients.lotus_core_query_client import LotusCoreQueryClient  # noqa: E402
from app.main import app  # noqa: E402
from app.services import workbench_service_provider  # noqa: E402

CANONICAL_PORTFOLIO_ID = "PB_SG_GLOBAL_BAL_001"
CANONICAL_BENCHMARK = "BMK_PB_GLOBAL_BALANCED_60_40"
CORRELATION_ID = "demo-cert-gateway-001"


@dataclass(frozen=True)
class CertificationAssertion:
    name: str
    actual: Any
    expected: Any
    passed: bool


@dataclass
class CertificationEvidence:
    assertions: list[CertificationAssertion] = field(default_factory=list)
    endpoints: list[dict[str, Any]] = field(default_factory=list)

    def expect(self, name: str, actual: Any, expected: Any) -> None:
        passed = actual == expected
        self.assertions.append(
            CertificationAssertion(
                name=name,
                actual=actual,
                expected=expected,
                passed=passed,
            )
        )
        if not passed:
            raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")

    def record_endpoint(self, *, method: str, path: str, status_code: int) -> None:
        self.endpoints.append({"method": method, "path": path, "status_code": status_code})


def _core_portfolio_payload() -> dict[str, Any]:
    return {
        "portfolio_id": CANONICAL_PORTFOLIO_ID,
        "base_currency": "USD",
        "booking_center_code": "SG",
        "client_id": "CIF_DEMO_001",
    }


def _core_snapshot_payload() -> dict[str, Any]:
    return {
        "as_of_date": "2026-04-10",
        "sections": {
            "positions_baseline": [
                {
                    "security_id": "EQ_GLOBAL",
                    "quantity": 900.0,
                    "market_value_base": 900_000.0,
                    "weight": 0.72,
                },
                {
                    "security_id": "BOND_GLOBAL",
                    "quantity": 250.0,
                    "market_value_base": 250_000.0,
                    "weight": 0.20,
                },
                {
                    "security_id": "CASH_USD",
                    "quantity": 100_000.0,
                    "market_value_base": 100_000.0,
                    "weight": 0.08,
                },
            ],
            "portfolio_totals": {"baseline_total_market_value_base": 1_250_000.0},
            "instrument_enrichment": [
                {
                    "security_id": "EQ_GLOBAL",
                    "instrument_name": "Global Equity Fund",
                    "asset_class": "Equity",
                },
                {
                    "security_id": "BOND_GLOBAL",
                    "instrument_name": "Global Aggregate Bond Fund",
                    "asset_class": "Fixed Income",
                },
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "US Dollar Cash",
                    "asset_class": "Cash",
                },
            ],
        },
    }


def _performance_payload() -> dict[str, Any]:
    return {
        "results_by_period": {
            "YTD": {
                "portfolio": {"summary": {"period_return": {"base": 4.2}}},
                "benchmark": {"summary": {"period_return": {"base": 3.6}}},
            }
        }
    }


def _dpm_runs_payload() -> dict[str, Any]:
    return {
        "items": [
            {
                "rebalance_run_id": "rr_demo_001",
                "status": "PENDING_REVIEW",
                "created_at": "2026-04-10T08:00:00Z",
                "workflow_state": "PM_REVIEW_REQUIRED",
            }
        ],
        "supportability": _dpm_supportability_payload()["supportability"],
    }


def _dpm_supportability_payload() -> dict[str, Any]:
    return {
        "supportability": {
            "feature_key": "manage.observability.action_register_supportability",
            "state": "healthy",
            "reason": "action_register_current",
            "freshness_bucket": "fresh",
            "run_count": 1,
            "operation_count": 4,
            "workflow_decision_count": 1,
        }
    }


def _projected_positions_payload() -> dict[str, Any]:
    return {
        "positions": [
            {
                "security_id": "EQ_GLOBAL",
                "instrument_name": "Global Equity Fund",
                "asset_class": "Equity",
                "baseline_quantity": 900.0,
                "proposed_quantity": 950.0,
                "delta_quantity": 50.0,
            }
        ]
    }


def _projected_summary_payload() -> dict[str, Any]:
    return {
        "total_baseline_positions": 3,
        "total_proposed_positions": 3,
        "net_delta_quantity": 50.0,
    }


@contextmanager
def _deterministic_upstream_clients() -> Iterator[None]:
    patches: list[tuple[type[Any], str, Callable[..., Any]]] = []

    async def get_portfolio(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, _core_portfolio_payload()

    async def get_core_snapshot(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, _core_snapshot_payload()

    async def get_portfolio_analytics_reference(
        *args: Any, **kwargs: Any
    ) -> tuple[int, dict[str, Any]]:
        return 200, {"performance_end_date": "2026-04-10"}

    async def create_simulation_session(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 201, {"session": {"session_id": "sess_demo_001", "version": 1}}

    async def add_simulation_changes(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, {"session_id": "sess_demo_001", "version": 2}

    async def get_projected_positions(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, _projected_positions_payload()

    async def get_projected_summary(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, _projected_summary_payload()

    async def get_workspace_summary(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, _performance_payload()

    async def list_runs(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, _dpm_runs_payload()

    async def get_supportability_summary(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, _dpm_supportability_payload()

    async def simulate_proposal(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        return 200, {"status": "COMPLETED", "gate_decision": {"status": "PASS"}}

    patches.extend(
        [
            (LotusCoreQueryClient, "get_portfolio", get_portfolio),
            (LotusCoreQueryClient, "get_core_snapshot", get_core_snapshot),
            (
                LotusCoreQueryClient,
                "get_portfolio_analytics_reference",
                get_portfolio_analytics_reference,
            ),
            (LotusCoreQueryClient, "create_simulation_session", create_simulation_session),
            (LotusCoreQueryClient, "add_simulation_changes", add_simulation_changes),
            (LotusCoreQueryClient, "get_projected_positions", get_projected_positions),
            (LotusCoreQueryClient, "get_projected_summary", get_projected_summary),
            (LotusAnalyticsClient, "get_workspace_summary", get_workspace_summary),
            (DpmClient, "list_runs", list_runs),
            (DpmClient, "get_supportability_summary", get_supportability_summary),
            (AdviseClient, "simulate_proposal", simulate_proposal),
        ]
    )
    originals = [(owner, name, getattr(owner, name)) for owner, name, _ in patches]
    try:
        _reset_workbench_service_cache()
        for owner, name, replacement in patches:
            setattr(owner, name, replacement)
        yield
    finally:
        for owner, name, original in originals:
            setattr(owner, name, original)
        _reset_workbench_service_cache()


def _reset_workbench_service_cache() -> None:
    workbench_service_provider._WORKBENCH_SERVICE = None
    workbench_service_provider._WORKBENCH_SERVICE_SIGNATURE = None
    workbench_service_provider._PERFORMANCE_WORKSPACE_SERVICE = None
    workbench_service_provider._PERFORMANCE_WORKSPACE_SERVICE_SIGNATURE = None
    workbench_service_provider._ADVISOR_BRIEF_SERVICE = None
    workbench_service_provider._ADVISOR_BRIEF_SERVICE_SIGNATURE = None
    workbench_service_provider._RISK_WORKSPACE_SERVICE = None
    workbench_service_provider._RISK_WORKSPACE_SERVICE_SIGNATURE = None


def run_demo_certification(output_path: Path) -> dict[str, Any]:
    evidence = CertificationEvidence()
    started_at = datetime.now(UTC).isoformat()
    try:
        with _deterministic_upstream_clients():
            client = TestClient(app)
            _certify_health(client, evidence)
            _certify_workbench_overview(client, evidence)
            _certify_portfolio_360(client, evidence)
            _certify_sandbox_policy(client, evidence)
        status = "passed"
        error = None
    except Exception as exc:  # noqa: BLE001
        status = "failed"
        error = str(exc)

    payload = {
        "schema_version": "1.0",
        "app": "lotus-gateway",
        "certification_scope": "gateway-demo-readiness-report-only",
        "status": status,
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "canonical_portfolio_id": CANONICAL_PORTFOLIO_ID,
        "canonical_benchmark": CANONICAL_BENCHMARK,
        "data_posture": "deterministic synthetic upstream fixtures through real Gateway APIs",
        "gate_posture": "report-only",
        "endpoints": evidence.endpoints,
        "assertions": [
            {
                "name": assertion.name,
                "actual": assertion.actual,
                "expected": assertion.expected,
                "passed": assertion.passed,
            }
            for assertion in evidence.assertions
        ],
        "error": error,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def _certify_health(client: TestClient, evidence: CertificationEvidence) -> None:
    response = client.get("/health/ready", headers={"X-Correlation-Id": CORRELATION_ID})
    evidence.record_endpoint(method="GET", path="/health/ready", status_code=response.status_code)
    evidence.expect("health.ready.status_code", response.status_code, 200)
    evidence.expect("health.ready.status", response.json()["status"], "ready")


def _certify_workbench_overview(client: TestClient, evidence: CertificationEvidence) -> None:
    path = f"/api/v1/workbench/{CANONICAL_PORTFOLIO_ID}/overview"
    response = client.get(path, headers={"X-Correlation-Id": CORRELATION_ID})
    evidence.record_endpoint(method="GET", path=path, status_code=response.status_code)
    body = response.json()
    evidence.expect("overview.status_code", response.status_code, 200)
    evidence.expect(
        "overview.portfolio_id", body["portfolio"]["portfolio_id"], CANONICAL_PORTFOLIO_ID
    )
    evidence.expect(
        "overview.market_value_base", body["overview"]["market_value_base"], 1_250_000.0
    )
    evidence.expect("overview.cash_weight_pct", body["overview"]["cash_weight_pct"], 8.0)
    evidence.expect("overview.position_count", body["overview"]["position_count"], 3)
    evidence.expect(
        "overview.performance_return_pct", body["performance_snapshot"]["return_pct"], 4.2
    )
    evidence.expect(
        "overview.benchmark_return_pct",
        body["performance_snapshot"]["benchmark_return_pct"],
        3.6,
    )
    evidence.expect(
        "overview.rebalance_status", body["rebalance_snapshot"]["status"], "PENDING_REVIEW"
    )
    evidence.expect(
        "overview.supportability_state",
        body["rebalance_snapshot"]["supportability"]["state"],
        "healthy",
    )
    evidence.expect("overview.partial_failures", body["partial_failures"], [])


def _certify_portfolio_360(client: TestClient, evidence: CertificationEvidence) -> None:
    path = f"/api/v1/workbench/{CANONICAL_PORTFOLIO_ID}/portfolio-360?session_id=sess_demo_001"
    response = client.get(path, headers={"X-Correlation-Id": CORRELATION_ID})
    evidence.record_endpoint(method="GET", path=path, status_code=response.status_code)
    body = response.json()
    evidence.expect("portfolio_360.status_code", response.status_code, 200)
    evidence.expect("portfolio_360.current_position_count", len(body["current_positions"]), 3)
    evidence.expect("portfolio_360.projected_position_count", len(body["projected_positions"]), 1)
    evidence.expect(
        "portfolio_360.projected_delta_quantity",
        body["projected_summary"]["net_delta_quantity"],
        50.0,
    )
    evidence.expect("portfolio_360.partial_failures", body["partial_failures"], [])


def _certify_sandbox_policy(client: TestClient, evidence: CertificationEvidence) -> None:
    create_path = f"/api/v1/workbench/{CANONICAL_PORTFOLIO_ID}/sandbox/sessions"
    created = client.post(
        create_path,
        headers={"X-Correlation-Id": CORRELATION_ID},
        json={"created_by": "advisor_demo", "ttl_hours": 48},
    )
    evidence.record_endpoint(method="POST", path=create_path, status_code=created.status_code)
    created_body = created.json()
    evidence.expect("sandbox_create.status_code", created.status_code, 200)
    evidence.expect("sandbox_create.session_id", created_body["session_id"], "sess_demo_001")
    evidence.expect("sandbox_create.session_version", created_body["session_version"], 1)

    apply_path = (
        f"/api/v1/workbench/{CANONICAL_PORTFOLIO_ID}/sandbox/sessions/sess_demo_001/changes"
    )
    updated = client.post(
        apply_path,
        headers={"X-Correlation-Id": CORRELATION_ID},
        json={
            "changes": [{"security_id": "EQ_GLOBAL", "transaction_type": "BUY", "quantity": 50.0}],
            "evaluate_policy": True,
        },
    )
    evidence.record_endpoint(method="POST", path=apply_path, status_code=updated.status_code)
    updated_body = updated.json()
    evidence.expect("sandbox_apply.status_code", updated.status_code, 200)
    evidence.expect("sandbox_apply.session_version", updated_body["session_version"], 2)
    evidence.expect(
        "sandbox_apply.policy_feedback_status",
        updated_body["policy_feedback"]["status"],
        "PASS",
    )
    evidence.expect("sandbox_apply.partial_failures", updated_body["partial_failures"], [])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic Gateway demo-readiness certification.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/demo-certification/gateway-demo-certification.json"),
        help="Machine-readable demo certification evidence path.",
    )
    args = parser.parse_args()

    result = run_demo_certification(args.output)
    print(
        "Gateway demo certification "
        f"{result['status']}: assertions={len(result['assertions'])}, output={args.output}"
    )
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
