import ast
from pathlib import Path

_SERVICE_ROOT = Path(__file__).parents[2] / "src" / "app" / "services"


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_risk_drawdown_supportability_lives_in_dedicated_module() -> None:
    drawdown_functions = _function_names(_SERVICE_ROOT / "risk_workspace_drawdown.py")
    supportability_functions = _function_names(
        _SERVICE_ROOT / "risk_workspace_drawdown_supportability.py"
    )

    extracted_functions = {
        "append_source_calculation_supportability",
        "build_drawdown_supportability",
        "initial_drawdown_period_supportability",
        "resolve_drawdown_benchmark_supportability",
        "resolve_drawdown_period_supportability",
        "resolve_underwater_supportability",
    }

    assert extracted_functions <= supportability_functions
    assert not extracted_functions & drawdown_functions


def test_risk_drawdown_payload_mapping_lives_in_dedicated_module() -> None:
    drawdown_functions = _function_names(_SERVICE_ROOT / "risk_workspace_drawdown.py")
    payload_functions = _function_names(_SERVICE_ROOT / "risk_workspace_drawdown_payloads.py")

    extracted_functions = {
        "iter_drawdown_result_items",
        "map_drawdown_episodes",
        "map_drawdown_period_result",
        "map_drawdown_summary",
        "map_underwater_series",
    }

    assert extracted_functions <= payload_functions
    assert not extracted_functions & drawdown_functions
