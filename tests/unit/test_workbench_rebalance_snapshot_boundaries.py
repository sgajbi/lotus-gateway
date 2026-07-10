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


def test_workbench_rebalance_snapshot_delegates_supportability_mapping() -> None:
    snapshot_functions = _function_names(_SERVICE_ROOT / "workbench_rebalance_snapshot.py")
    supportability_functions = _function_names(
        _SERVICE_ROOT / "workbench_rebalance_supportability.py"
    )

    extracted_functions = {
        "parse_rebalance_supportability",
        "_extract_rebalance_supportability_payload",
        "_unpack_rebalance_supportability_summary",
        "_supportability_payload_from_summary",
        "_merge_supportability_summary_counts",
        "_record_rebalance_supportability_unavailable",
    }

    assert extracted_functions <= supportability_functions
    assert not extracted_functions & snapshot_functions
