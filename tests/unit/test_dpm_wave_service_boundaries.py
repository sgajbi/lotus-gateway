import ast
from pathlib import Path

_SERVICE_ROOT = Path(__file__).parents[2] / "src" / "app" / "services"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def test_dpm_wave_ai_handoff_lives_in_dedicated_service_mixin() -> None:
    wave_service_methods = _async_function_names(_SERVICE_ROOT / "dpm_wave_service.py")
    ai_handoff_methods = _async_function_names(_SERVICE_ROOT / "dpm_wave_ai_handoff.py")

    extracted_methods = {
        "_execute_operations_handoff_summary_workflow",
        "_execute_wave_pm_memo_workflow",
        "_load_wave_report_input",
        "request_operations_handoff_summary",
        "request_wave_pm_memo",
    }

    assert extracted_methods <= ai_handoff_methods
    assert not extracted_methods & wave_service_methods
