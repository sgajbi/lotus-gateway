import ast
from pathlib import Path

_CLIENT_ROOT = Path(__file__).parents[2] / "src" / "app" / "clients"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def test_reporting_batch_routes_live_in_dedicated_client_mixin() -> None:
    reporting_client_methods = _async_function_names(_CLIENT_ROOT / "reporting_client.py")
    batch_client_methods = _async_function_names(_CLIENT_ROOT / "reporting_batch_client.py")

    extracted_methods = {
        "control_report_batch",
        "create_report_batch",
        "get_report_batch",
        "list_report_batch_schedules",
        "run_due_report_batch_schedules",
    }

    assert extracted_methods <= batch_client_methods
    assert not extracted_methods & reporting_client_methods
