import ast
from pathlib import Path

_CLIENT_ROOT = Path(__file__).parents[2] / "src" / "app" / "clients"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def test_pm_operating_quality_routes_live_in_dedicated_client_mixin() -> None:
    dpm_client_methods = _async_function_names(_CLIENT_ROOT / "dpm_client.py")
    pm_quality_methods = _async_function_names(_CLIENT_ROOT / "dpm_pm_operating_quality_client.py")

    extracted_methods = {
        name for name in pm_quality_methods if name.startswith(("preview_pm_", "create_pm_"))
    } | {name for name in pm_quality_methods if name.startswith(("list_pm_", "get_pm_", "put_pm_"))}

    assert extracted_methods
    assert not {
        name for name in dpm_client_methods if name.startswith(("preview_pm_", "create_pm_"))
    }
    assert not {
        name for name in dpm_client_methods if name.startswith(("list_pm_", "get_pm_", "put_pm_"))
    }


def test_construction_routes_live_in_dedicated_client_mixin() -> None:
    dpm_client_methods = _async_function_names(_CLIENT_ROOT / "dpm_client.py")
    construction_methods = _async_function_names(_CLIENT_ROOT / "dpm_construction_client.py")

    extracted_methods = {
        "generate_construction_alternative_set",
        "get_construction_alternative_set",
        "select_construction_alternative",
    }

    assert extracted_methods <= construction_methods
    assert not extracted_methods & dpm_client_methods


def test_proof_pack_routes_live_in_dedicated_client_mixin() -> None:
    dpm_client_methods = _async_function_names(_CLIENT_ROOT / "dpm_client.py")
    proof_pack_methods = _async_function_names(_CLIENT_ROOT / "dpm_proof_pack_client.py")

    extracted_methods = {
        "generate_proof_pack",
        "get_proof_pack",
        "get_proof_pack_markdown",
        "get_proof_pack_report_input",
        "get_proof_pack_ai_evidence_input",
    }

    assert extracted_methods <= proof_pack_methods
    assert not extracted_methods & dpm_client_methods


def test_wave_routes_live_in_dedicated_client_mixin() -> None:
    dpm_client_methods = _async_function_names(_CLIENT_ROOT / "dpm_client.py")
    wave_methods = (
        _async_function_names(_CLIENT_ROOT / "dpm_wave_core_client.py")
        | _async_function_names(_CLIENT_ROOT / "dpm_wave_campaign_definition_client.py")
        | _async_function_names(_CLIENT_ROOT / "dpm_wave_campaign_workflow_client.py")
    )
    wave_facade_methods = _async_function_names(_CLIENT_ROOT / "dpm_wave_client.py")

    core_methods = {
        "preview_wave",
        "create_wave",
        "list_waves",
        "get_wave",
        "discover_campaigns",
        "get_wave_items",
        "source_check_wave",
        "simulate_wave",
        "select_wave_item",
        "approve_wave",
        "stage_wave",
        "handoff_wave",
        "cancel_wave",
        "get_wave_proof_pack_posture",
        "get_wave_supportability",
        "get_wave_report_input",
    }
    campaign_definition_methods = {
        "put_campaign_definition",
        "list_campaign_definitions",
        "get_campaign_definition",
        "get_campaign_definition_lifecycle_events",
        "get_campaign_definition_preview_readiness",
        "get_campaign_definition_launch_history",
        "get_campaign_definition_launch_package",
        "launch_campaign_definition",
        "retire_campaign_definition",
        "supersede_campaign_definition",
    }
    campaign_workflow_methods = {
        "get_campaign_operating_queue",
        "get_campaign_approval_inbox",
        "get_campaign_workflow_board",
        "get_campaign_assignment_plan",
        "get_campaign_workflow_automation",
        "list_campaign_approval_decisions",
        "create_campaign_approval_decision",
        "list_campaign_assignment_actions",
        "create_campaign_assignment_action",
        "list_campaign_assignment_tasks",
        "create_campaign_assignment_task",
        "transition_campaign_assignment_task",
        "list_campaign_maker_checker_controls",
        "create_campaign_maker_checker_control",
    }
    extracted_methods = core_methods | campaign_definition_methods | campaign_workflow_methods

    assert extracted_methods <= wave_methods
    assert core_methods <= _async_function_names(_CLIENT_ROOT / "dpm_wave_core_client.py")
    assert campaign_definition_methods <= _async_function_names(
        _CLIENT_ROOT / "dpm_wave_campaign_definition_client.py"
    )
    assert campaign_workflow_methods <= _async_function_names(
        _CLIENT_ROOT / "dpm_wave_campaign_workflow_client.py"
    )
    assert wave_facade_methods == set()
    assert not extracted_methods & dpm_client_methods
