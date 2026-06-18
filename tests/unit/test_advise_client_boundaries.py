import ast
from pathlib import Path

_CLIENT_ROOT = Path(__file__).parents[2] / "src" / "app" / "clients"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def test_bank_demo_proof_routes_live_in_dedicated_client_mixin() -> None:
    advise_client_methods = _async_function_names(_CLIENT_ROOT / "advise_client.py")
    bank_demo_methods = _async_function_names(_CLIENT_ROOT / "advise_bank_demo_proof_client.py")

    extracted_methods = {
        "build_bank_demo_proof_pack",
        "get_bank_demo_proof_scenario_contract",
        "get_bank_demo_supported_claim_register",
    }

    assert extracted_methods <= bank_demo_methods
    assert not extracted_methods & advise_client_methods


def test_advisory_workspace_routes_live_in_dedicated_client_mixin() -> None:
    advise_client_methods = _async_function_names(_CLIENT_ROOT / "advise_client.py")
    workspace_methods = _async_function_names(_CLIENT_ROOT / "advise_workspace_client.py")

    extracted_methods = {
        "apply_advisory_workspace_draft_action",
        "compare_advisory_workspace",
        "create_advisory_workspace",
        "evaluate_advisory_workspace",
        "get_advisory_workspace",
        "get_advisory_workspace_saved_version_replay_evidence",
        "handoff_advisory_workspace",
        "list_advisory_workspace_saved_versions",
        "request_advisory_workspace_rationale",
        "resume_advisory_workspace",
        "review_advisory_workspace_rationale",
        "save_advisory_workspace",
    }

    assert extracted_methods <= workspace_methods
    assert not extracted_methods & advise_client_methods


def test_advisory_policy_routes_live_in_dedicated_client_mixin() -> None:
    advise_client_methods = _async_function_names(_CLIENT_ROOT / "advise_client.py")
    policy_methods = _async_function_names(_CLIENT_ROOT / "advise_policy_client.py")

    extracted_methods = {
        "activate_policy_pack_version",
        "create_policy_evaluation",
        "get_policy_evaluation",
        "get_policy_evaluation_lineage",
        "get_policy_evaluation_workflow",
        "get_policy_pack_version",
        "get_policy_review_queue",
        "get_policy_sign_off_package",
        "list_policy_packs",
        "record_policy_evaluation_event",
        "record_policy_sign_off_decision",
        "replay_policy_evaluation",
        "request_policy_ai_evidence",
        "request_policy_report_package",
        "validate_policy_pack_version",
    }

    assert extracted_methods <= policy_methods
    assert not extracted_methods & advise_client_methods


def test_advisory_proposal_routes_live_in_dedicated_client_mixin() -> None:
    advise_client_methods = _async_function_names(_CLIENT_ROOT / "advise_client.py")
    proposal_methods = _async_function_names(_CLIENT_ROOT / "advise_proposal_client.py")

    extracted_methods = {
        "create_execution_handoff",
        "create_proposal",
        "create_proposal_artifact",
        "create_proposal_async",
        "create_proposal_memo",
        "create_proposal_version",
        "create_proposal_version_async",
        "create_report_request",
        "get_approvals",
        "get_delivery_events",
        "get_delivery_summary",
        "get_execution_status",
        "get_proposal",
        "get_proposal_idempotency_record",
        "get_proposal_lineage",
        "get_proposal_memo",
        "get_proposal_memo_lineage",
        "get_proposal_memo_projection",
        "get_proposal_memo_replay_evidence",
        "get_proposal_narrative",
        "get_proposal_operation",
        "get_proposal_operation_by_correlation",
        "get_proposal_operation_replay_evidence",
        "get_proposal_version",
        "get_proposal_version_replay_evidence",
        "get_workflow_events",
        "list_proposals",
        "record_approval",
        "record_execution_update",
        "record_proposal_memo_report_package_event",
        "regenerate_proposal_narrative",
        "request_proposal_memo_ai_commentary",
        "request_proposal_memo_report_package",
        "review_proposal_memo",
        "review_proposal_narrative",
        "simulate_proposal",
        "transition_proposal",
    }

    assert extracted_methods <= proposal_methods
    assert not extracted_methods & advise_client_methods
