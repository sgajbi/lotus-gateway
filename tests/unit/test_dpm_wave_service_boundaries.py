import ast
from pathlib import Path

_SERVICE_ROOT = Path(__file__).parents[2] / "src" / "app" / "services"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


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


def test_dpm_wave_ai_payload_mapping_lives_in_dedicated_module() -> None:
    ai_handoff_helpers = _function_names(_SERVICE_ROOT / "dpm_wave_ai_handoff.py")
    payload_helpers = _function_names(_SERVICE_ROOT / "dpm_wave_ai_payloads.py")

    extracted_helpers = {
        "operations_handoff_summary_request_payload",
        "operations_handoff_summary_response",
        "operations_handoff_summary_task_payload",
        "operations_handoff_supportability_payload",
        "supportability_from",
        "wave_pm_memo_request_payload",
        "wave_pm_memo_response",
        "wave_pm_memo_supportability_payload",
        "wave_pm_memo_task_payload",
        "wave_report_source_refs",
    }

    assert extracted_helpers <= payload_helpers
    assert not extracted_helpers & ai_handoff_helpers


def test_dpm_wave_campaign_workflow_lives_in_dedicated_service_mixin() -> None:
    wave_service_methods = _async_function_names(_SERVICE_ROOT / "dpm_wave_service.py")
    campaign_workflow_methods = _async_function_names(
        _SERVICE_ROOT / "dpm_wave_campaign_workflow.py"
    )

    extracted_methods = {
        "create_campaign_approval_decision",
        "create_campaign_assignment_action",
        "create_campaign_assignment_task",
        "create_campaign_maker_checker_control",
        "get_campaign_approval_inbox",
        "get_campaign_assignment_plan",
        "get_campaign_operating_queue",
        "get_campaign_workflow_automation",
        "get_campaign_workflow_board",
        "list_campaign_approval_decisions",
        "list_campaign_assignment_actions",
        "list_campaign_assignment_tasks",
        "list_campaign_maker_checker_controls",
        "transition_campaign_assignment_task",
    }

    assert extracted_methods <= campaign_workflow_methods
    assert not extracted_methods & wave_service_methods
