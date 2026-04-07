from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "src" / "app"


def _source_files() -> list[Path]:
    return [path for path in APP_ROOT.rglob("*.py") if "__pycache__" not in path.parts]


def test_removed_workbench_risk_proxy_is_not_reintroduced_in_gateway_runtime_code() -> None:
    forbidden_patterns = {
        "/analytics/workbench/risk-proxy": "removed lotus-risk compatibility endpoint",
        "get_workbench_risk_proxy": "legacy client method for the removed endpoint",
        "WorkbenchRiskProxy": "legacy analytics contract type should stay deleted",
    }

    violations: list[tuple[str, str, str]] = []
    for source_file in _source_files():
        contents = source_file.read_text(encoding="utf-8")
        for pattern, reason in forbidden_patterns.items():
            if pattern in contents:
                violations.append((str(source_file.relative_to(REPO_ROOT)), pattern, reason))

    assert violations == []
