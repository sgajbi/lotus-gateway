import json
from pathlib import Path

from scripts.certify_demo_readiness import (
    CANONICAL_PORTFOLIO_ID,
    run_demo_certification,
)


def test_demo_certification_writes_passing_machine_readable_evidence(tmp_path: Path) -> None:
    output_path = tmp_path / "gateway-demo-certification.json"

    result = run_demo_certification(output_path)

    assert result["status"] == "passed"
    assert result["gate_posture"] == "report-only"
    assert result["canonical_portfolio_id"] == CANONICAL_PORTFOLIO_ID
    assert result["error"] is None
    assert len(result["endpoints"]) == 5
    assert {endpoint["status_code"] for endpoint in result["endpoints"]} == {200}
    assert all(assertion["passed"] for assertion in result["assertions"])

    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert persisted == result
    assert _assertion_value(result, "overview.market_value_base") == 1_250_000.0
    assert _assertion_value(result, "overview.cash_weight_pct") == 8.0
    assert _assertion_value(result, "overview.performance_return_pct") == 4.2
    assert _assertion_value(result, "sandbox_apply.policy_feedback_status") == "PASS"


def _assertion_value(result: dict, name: str):
    for assertion in result["assertions"]:
        if assertion["name"] == name:
            return assertion["actual"]
    raise AssertionError(f"Missing assertion {name}")
