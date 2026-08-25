import ast
from pathlib import Path

_SERVICE_ROOT = Path(__file__).parents[2] / "src" / "app" / "services"
_TEST_ROOT = Path(__file__).parents[2] / "tests" / "unit"
_CLIENT_FACTORY_FILES = {
    "advise_client_factory.py",
    "analytics_client_factory.py",
    "archive_client_factory.py",
    "dpm_service_factory.py",
    "idea_client_factory.py",
    "lotus_core_client_factory.py",
    "reporting_client_factory.py",
}
_UPSTREAM_ROUTING_SETTING_SUFFIXES = (
    "_base_url",
    "_timeout_seconds",
    "_max_retries",
    "_retry_backoff_seconds",
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _class_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def test_only_service_factories_import_concrete_clients() -> None:
    offenders = {
        path.relative_to(_SERVICE_ROOT).as_posix(): sorted(
            module
            for module in _imported_modules(path)
            if module == "app.clients" or module.startswith("app.clients.")
        )
        for path in _SERVICE_ROOT.rglob("*.py")
        if path.name not in _CLIENT_FACTORY_FILES
    }
    offenders = {name: imports for name, imports in offenders.items() if imports}

    assert offenders == {}


def test_service_layer_does_not_depend_on_router_modules() -> None:
    offenders = {
        path.relative_to(_SERVICE_ROOT).as_posix(): sorted(
            module
            for module in _imported_modules(path)
            if module == "app.routers" or module.startswith("app.routers.")
        )
        for path in _SERVICE_ROOT.rglob("*.py")
    }
    offenders = {name: imports for name, imports in offenders.items() if imports}

    assert offenders == {}


def test_service_providers_do_not_return_direct_builder_calls() -> None:
    offenders: dict[str, list[str]] = {}
    for path in _SERVICE_ROOT.glob("*_service_provider.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        direct_builder_returns: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Return):
                continue
            if not isinstance(node.value, ast.Call):
                continue
            if not isinstance(node.value.func, ast.Name):
                continue
            if node.value.func.id.startswith("build_"):
                direct_builder_returns.append(node.value.func.id)
        if direct_builder_returns:
            offenders[path.relative_to(_SERVICE_ROOT).as_posix()] = sorted(direct_builder_returns)

    assert offenders == {}


def test_service_providers_use_shared_cache_helper() -> None:
    offenders: list[str] = []
    for path in _SERVICE_ROOT.glob("*_service_provider.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        helper_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "resolve_cached_service"
        ]
        if not helper_calls:
            offenders.append(path.relative_to(_SERVICE_ROOT).as_posix())

    assert offenders == []


def test_services_delegate_workflow_task_request_shape_to_shared_helper() -> None:
    offenders: dict[str, list[int]] = {}
    for path in _SERVICE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        inline_task_request_lines: list[int] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.keyword):
                continue
            if node.arg != "task_request":
                continue
            if isinstance(node.value, ast.Dict):
                inline_task_request_lines.append(node.lineno)
        if inline_task_request_lines:
            offenders[path.relative_to(_SERVICE_ROOT).as_posix()] = inline_task_request_lines

    assert offenders == {}


def test_dpm_command_center_service_delegates_exception_summary_handoff() -> None:
    path = _SERVICE_ROOT / "dpm_command_center_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name
        in {
            "request_exception_summary",
            "_load_exception_summary_context",
            "_execute_exception_summary_workflow",
            "_compose_exception_summary_response",
        }
    )
    command_center_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "DpmCommandCenterService"
    ]
    base_names = {
        base.id
        for service_class in command_center_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert delegated_methods == []
    assert "DpmCommandCenterExceptionSummaryMixin" in base_names


def test_dpm_command_center_service_delegates_outcome_narrative_handoff() -> None:
    path = _SERVICE_ROOT / "dpm_command_center_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name
        in {
            "request_outcome_review_ai_narrative",
            "_build_outcome_review_narrative_context",
            "_execute_outcome_review_narrative_pack",
        }
    )
    command_center_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "DpmCommandCenterService"
    ]
    base_names = {
        base.id
        for service_class in command_center_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert delegated_methods == []
    assert "DpmCommandCenterOutcomeNarrativeMixin" in base_names


def test_dpm_command_center_service_delegates_response_assembly() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "dpm_command_center_service.py")
    response_methods = _function_names(_SERVICE_ROOT / "dpm_command_center_response.py")
    expected_response_methods = {
        "compose_outcome_review_response",
        "compose_command_center_response",
        "compose_portfolio_memory_response",
    }

    assert expected_response_methods <= response_methods
    assert service_methods.isdisjoint(expected_response_methods)


def test_dpm_command_center_service_delegates_core_route_family() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "dpm_command_center_service.py")
    core_methods = _function_names(_SERVICE_ROOT / "dpm_command_center_core_service.py")
    expected_core_methods = {
        "get_command_center",
        "run_monitoring_once",
        "list_monitoring_runs",
        "get_monitoring_run",
        "list_monitoring_exceptions",
        "resolve_monitoring_exception",
        "get_mandate_by_portfolio",
        "get_mandate",
        "get_mandate_health",
        "get_mandate_diff",
    }

    assert expected_core_methods <= core_methods
    assert service_methods.isdisjoint(expected_core_methods)


def test_advisory_protocols_delegate_advisor_brief_client_protocols() -> None:
    advisory_protocols_path = _SERVICE_ROOT / "advisory_client_protocols.py"
    advisor_brief_protocols_path = _SERVICE_ROOT / "advisor_brief_client_protocols.py"
    advisory_tree = ast.parse(
        advisory_protocols_path.read_text(encoding="utf-8"),
        filename=str(advisory_protocols_path),
    )
    advisor_brief_tree = ast.parse(
        advisor_brief_protocols_path.read_text(encoding="utf-8"),
        filename=str(advisor_brief_protocols_path),
    )

    advisory_protocol_names = {
        node.name for node in ast.walk(advisory_tree) if isinstance(node, ast.ClassDef)
    }
    advisor_brief_protocol_names = {
        node.name for node in ast.walk(advisor_brief_tree) if isinstance(node, ast.ClassDef)
    }

    assert "AdvisorBriefAiClient" not in advisory_protocol_names
    assert "AdvisorBriefAdviseClient" not in advisory_protocol_names
    assert advisor_brief_protocol_names == {
        "AdvisorBriefAdviseClient",
        "AdvisorBriefAiClient",
    }


def test_advisory_protocols_are_split_by_route_family() -> None:
    advisory_protocols_path = _SERVICE_ROOT / "advisory_client_protocols.py"
    tree = ast.parse(
        advisory_protocols_path.read_text(encoding="utf-8"),
        filename=str(advisory_protocols_path),
    )
    protocol_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    imported_modules = _imported_modules(advisory_protocols_path)

    assert protocol_names == set()
    assert {
        "app.services.advisor_cockpit_client_protocols",
        "app.services.advisory_copilot_client_protocols",
        "app.services.advisory_policy_client_protocols",
        "app.services.advisory_workspace_client_protocols",
        "app.services.bank_demo_proof_client_protocols",
        "app.services.proposal_client_protocols",
    }.issubset(imported_modules)


def test_advisory_services_import_focused_protocol_families() -> None:
    expected_protocol_imports = {
        "advisor_cockpit_service.py": "app.services.advisor_cockpit_client_protocols",
        "advisory_copilot_service.py": "app.services.advisory_copilot_client_protocols",
        "advisory_policy_service.py": "app.services.advisory_policy_client_protocols",
        "advisory_workspace_service.py": "app.services.advisory_workspace_client_protocols",
        "bank_demo_proof_service.py": "app.services.bank_demo_proof_client_protocols",
        "proposal_lifecycle_query_service.py": "app.services.proposal_client_protocols",
        "proposal_memo_service.py": "app.services.proposal_client_protocols",
        "proposal_service.py": "app.services.proposal_client_protocols",
        "proposal_transition_service.py": "app.services.proposal_client_protocols",
    }

    for service_file, expected_import in expected_protocol_imports.items():
        imports = _imported_modules(_SERVICE_ROOT / service_file)
        assert expected_import in imports
        assert "app.services.advisory_client_protocols" not in imports


def test_dpm_wave_protocol_is_split_from_shared_protocol_aggregator() -> None:
    dpm_protocols_path = _SERVICE_ROOT / "dpm_client_protocols.py"
    dpm_wave_protocols_path = _SERVICE_ROOT / "dpm_wave_client_protocols.py"
    dpm_tree = ast.parse(
        dpm_protocols_path.read_text(encoding="utf-8"),
        filename=str(dpm_protocols_path),
    )
    dpm_wave_tree = ast.parse(
        dpm_wave_protocols_path.read_text(encoding="utf-8"),
        filename=str(dpm_wave_protocols_path),
    )

    dpm_protocol_names = {
        node.name for node in ast.walk(dpm_tree) if isinstance(node, ast.ClassDef)
    }
    dpm_wave_protocol_names = {
        node.name for node in ast.walk(dpm_wave_tree) if isinstance(node, ast.ClassDef)
    }
    assert "DpmWaveClient" not in dpm_protocol_names
    assert dpm_wave_protocol_names == {"DpmWaveClient"}


def test_dpm_wave_services_import_focused_protocol_family() -> None:
    for service_file in {
        "dpm_wave_ai_handoff.py",
        "dpm_wave_campaign_definitions.py",
        "dpm_wave_service.py",
    }:
        imports = _imported_modules(_SERVICE_ROOT / service_file)
        assert "app.services.dpm_wave_client_protocols" in imports
        assert "app.services.dpm_client_protocols" not in imports


def test_dpm_pm_operating_quality_protocol_is_split_from_command_center_protocol() -> None:
    dpm_protocols_path = _SERVICE_ROOT / "dpm_client_protocols.py"
    pm_quality_protocols_path = _SERVICE_ROOT / "dpm_pm_operating_quality_client_protocols.py"
    dpm_tree = ast.parse(
        dpm_protocols_path.read_text(encoding="utf-8"),
        filename=str(dpm_protocols_path),
    )
    pm_quality_tree = ast.parse(
        pm_quality_protocols_path.read_text(encoding="utf-8"),
        filename=str(pm_quality_protocols_path),
    )

    command_center_protocol = next(
        node
        for node in ast.walk(dpm_tree)
        if isinstance(node, ast.ClassDef) and node.name == "DpmCommandCenterClient"
    )
    command_center_method_names = {
        node.name for node in command_center_protocol.body if isinstance(node, ast.AsyncFunctionDef)
    }
    pm_quality_protocol_names = {
        node.name for node in ast.walk(pm_quality_tree) if isinstance(node, ast.ClassDef)
    }
    pm_quality_method_names = {
        node.name for node in ast.walk(pm_quality_tree) if isinstance(node, ast.AsyncFunctionDef)
    }

    assert pm_quality_protocol_names == {
        "DpmPmOperatingQualityClient",
        "DpmPmOperatingQualityClientAccessMixin",
    }
    assert pm_quality_method_names
    assert {
        method for method in command_center_method_names if "pm_operating_quality" in method
    } == set()


def test_dpm_pm_operating_quality_services_import_focused_protocol_family() -> None:
    for service_file in {
        "dpm_pm_operating_quality_service.py",
        "dpm_pm_operating_quality_summary_invocation_service.py",
        "dpm_pm_operating_quality_summary_service.py",
    }:
        imports = _imported_modules(_SERVICE_ROOT / service_file)
        assert "app.services.dpm_pm_operating_quality_client_protocols" in imports
        assert "app.services.dpm_client_protocols" not in imports


def test_portfolio_protocols_are_split_from_workspace_protocol_aggregator() -> None:
    workspace_protocols_path = _SERVICE_ROOT / "workspace_client_protocols.py"
    portfolio_protocols_path = _SERVICE_ROOT / "portfolio_client_protocols.py"
    workspace_tree = ast.parse(
        workspace_protocols_path.read_text(encoding="utf-8"),
        filename=str(workspace_protocols_path),
    )
    portfolio_tree = ast.parse(
        portfolio_protocols_path.read_text(encoding="utf-8"),
        filename=str(portfolio_protocols_path),
    )

    workspace_protocol_names = {
        node.name for node in ast.walk(workspace_tree) if isinstance(node, ast.ClassDef)
    }
    portfolio_protocol_names = {
        node.name for node in ast.walk(portfolio_tree) if isinstance(node, ast.ClassDef)
    }

    assert {
        "PortfolioCoreClient",
        "PortfolioManageClient",
        "PortfolioPerformanceClient",
    }.isdisjoint(workspace_protocol_names)
    assert portfolio_protocol_names == {
        "PortfolioCoreClient",
        "PortfolioManageClient",
        "PortfolioPerformanceClient",
    }


def test_portfolio_services_import_focused_protocol_family() -> None:
    for service_file in {
        "portfolio_catalog_payloads.py",
        "portfolio_service.py",
        "portfolio_upstream_access.py",
    }:
        imports = _imported_modules(_SERVICE_ROOT / service_file)
        assert "app.services.portfolio_client_protocols" in imports
        assert "app.services.workspace_client_protocols" not in imports


def test_portfolio_workflow_delegates_action_definitions() -> None:
    workflow_methods = _function_names(_SERVICE_ROOT / "portfolio_workflow.py")
    definition_methods = _function_names(_SERVICE_ROOT / "portfolio_workflow_definitions.py")
    delegated_methods = {
        "workflow_action_spec_href",
        "workflow_order_rank",
        "workflow_task_label",
        "workflow_cta_label",
        "workflow_target_label",
        "workflow_impact_label",
    }

    assert delegated_methods <= definition_methods
    assert workflow_methods.isdisjoint(delegated_methods)


def test_dpm_pm_operating_quality_summary_lives_in_focused_service_mixin() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "dpm_pm_operating_quality_service.py")
    summary_service_methods = _function_names(
        _SERVICE_ROOT / "dpm_pm_operating_quality_summary_service.py"
    )
    summary_methods = {
        "request_pm_operating_quality_summary",
        "_compose_pm_operating_quality_summary_response",
        "_execute_pm_operating_quality_summary_workflow",
        "_load_pm_operating_quality_summary_context",
        "_require_pm_operating_quality_score_run",
    }

    assert summary_methods <= summary_service_methods
    assert not summary_methods & service_methods


def test_dpm_pm_operating_quality_summary_invocations_live_in_focused_service_mixin() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "dpm_pm_operating_quality_service.py")
    invocation_service_methods = _function_names(
        _SERVICE_ROOT / "dpm_pm_operating_quality_summary_invocation_service.py"
    )
    invocation_methods = {
        "preview_pm_operating_quality_summary_invocation",
        "create_pm_operating_quality_summary_invocation",
        "list_pm_operating_quality_summary_invocations",
        "get_pm_operating_quality_summary_invocation",
    }

    assert invocation_methods <= invocation_service_methods
    assert not invocation_methods & service_methods


def test_dpm_pm_operating_quality_service_delegates_response_assembly() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "dpm_pm_operating_quality_service.py")
    response_methods = _function_names(_SERVICE_ROOT / "dpm_pm_operating_quality_response.py")

    assert "compose_pm_operating_quality_response" in response_methods
    assert "_compose_pm_operating_quality_response" not in service_methods


def test_risk_workspace_service_uses_shared_request_builders_directly() -> None:
    path = _SERVICE_ROOT / "risk_workspace_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    private_request_builders = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("_build_")
        and node.name.endswith("_request")
    )

    assert private_request_builders == []


def test_risk_workspace_service_delegates_cache_policy() -> None:
    path = _SERVICE_ROOT / "risk_workspace_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    private_cache_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.endswith("_cache_key")
    )

    assert private_cache_helpers == []


def test_risk_workspace_attribution_orchestration_lives_in_focused_mixin() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "risk_workspace_service.py")
    attribution_service_methods = _function_names(
        _SERVICE_ROOT / "risk_workspace_attribution_service.py"
    )
    attribution_orchestration_methods = {
        "get_attribution",
        "_blocked_risk_attribution_response",
        "_cached_attribution_response",
        "_load_attribution_response",
        "_risk_attribution_request_context",
    }

    assert attribution_orchestration_methods <= attribution_service_methods
    assert not attribution_orchestration_methods & service_methods


def test_risk_workspace_mandate_orchestration_lives_in_focused_mixin() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "risk_workspace_service.py")
    mandate_service_methods = _function_names(_SERVICE_ROOT / "risk_workspace_mandate_service.py")
    mandate_orchestration_methods = {
        "_load_summary_with_mandate",
        "_load_concentration_with_mandate",
        "_load_mandate_sources",
    }

    assert mandate_orchestration_methods <= mandate_service_methods
    assert not mandate_orchestration_methods & service_methods


def test_advisor_brief_service_delegates_workflow_pack_runtime_mapping() -> None:
    path = _SERVICE_ROOT / "advisor_brief_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    workflow_pack_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and (
            "workflow_pack_run" in node.name
            or "workflow_pack_task_flow" in node.name
            or node.name == "_assert_advisor_brief_review_action_allowed"
        )
    )

    assert workflow_pack_helpers == []


def test_advisor_brief_workflow_pack_delegates_task_flow_parsing() -> None:
    workflow_pack_methods = _function_names(_SERVICE_ROOT / "advisor_brief_workflow_pack.py")
    task_flow_methods = _function_names(_SERVICE_ROOT / "advisor_brief_task_flow.py")
    expected_task_flow_methods = {
        "parse_advisor_brief_workflow_pack_task_flow",
        "_parse_task_flow_handoff",
        "_parse_task_flow_handoff_refs",
        "_parse_task_flow_lineage",
        "_parse_task_flow_lineage_items",
        "_parse_task_flow_required_fields",
        "_parse_task_flow_review_states",
        "_parse_task_flow_run_refs",
    }

    assert expected_task_flow_methods <= task_flow_methods
    assert workflow_pack_methods.isdisjoint(expected_task_flow_methods)


def test_advisor_brief_service_delegates_supportability_runtime_mapping() -> None:
    path = _SERVICE_ROOT / "advisor_brief_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    supportability_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and (
            node.name in {"_load_advisory_supportability", "_load_ai_surface_supportability"}
            or node.name.startswith("_parse_ai_surface_supportability")
            or node.name.startswith("_normalize_ai_surface_")
        )
    )

    assert supportability_helpers == []


def test_advisor_brief_runtime_context_owns_runtime_evidence_loading() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "advisor_brief_service.py")
    runtime_context_methods = _function_names(_SERVICE_ROOT / "advisor_brief_runtime_context.py")

    assert "load_advisor_brief_runtime_context" in runtime_context_methods
    assert "_load_advisor_brief_runtime_context" not in service_methods


def test_advisor_brief_service_delegates_review_action_context() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "advisor_brief_service.py")
    review_action_methods = _function_names(_SERVICE_ROOT / "advisor_brief_review_actions.py")

    assert {
        "apply_advisor_brief_review_action",
        "load_advisor_brief_review_action_context",
    } <= review_action_methods
    assert "_apply_advisor_brief_review_action" not in service_methods
    assert "_load_advisor_brief_review_action_context" not in service_methods


def test_advisor_brief_service_delegates_response_assembly() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "advisor_brief_service.py")
    response_methods = _function_names(_SERVICE_ROOT / "advisor_brief_response.py")

    assert {
        "assemble_advisor_brief_response",
        "with_advisor_brief_runtime_context",
    } <= response_methods
    assert "_assemble_advisor_brief_response" not in service_methods
    assert "_with_advisor_brief_runtime_context" not in service_methods


def test_advisor_brief_service_delegates_source_context_mapping() -> None:
    path = _SERVICE_ROOT / "advisor_brief_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    source_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and (
            node.name.startswith("_build_source_metric")
            or node.name.startswith("_build_source_talking")
            or node.name.startswith("_build_source_summary")
            or node.name.startswith("_build_return_source_")
            or node.name == "_build_advisor_brief_source_context"
            or node.name == "_build_supportability"
            or node.name == "_route_query"
        )
    )

    assert source_helpers == []


def test_advisor_brief_source_delegates_source_metric_construction() -> None:
    source_methods = _function_names(_SERVICE_ROOT / "advisor_brief_source.py")
    metric_methods = _function_names(_SERVICE_ROOT / "advisor_brief_source_metrics.py")

    assert "build_return_source_metrics" in metric_methods
    assert "_source_metric" in metric_methods
    assert "_build_return_source_metrics" not in source_methods
    assert "_source_metric" not in source_methods


def test_advisor_brief_source_delegates_narrative_construction() -> None:
    source_methods = _function_names(_SERVICE_ROOT / "advisor_brief_source.py")
    narrative_methods = _function_names(_SERVICE_ROOT / "advisor_brief_source_narrative.py")

    expected_narrative_methods = {
        "build_source_summary",
        "build_source_talking_points",
        "build_recommended_actions",
        "build_risks_and_exceptions",
    }

    assert expected_narrative_methods <= narrative_methods
    assert "_build_return_talking_point" in narrative_methods
    assert "_build_supportability_risk" in narrative_methods
    assert "_build_return_talking_point" not in source_methods
    assert "_build_supportability_risk" not in source_methods


def test_proposal_service_delegates_lifecycle_transitions() -> None:
    path = _SERVICE_ROOT / "proposal_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "approve_compliance",
            "approve_risk",
            "record_client_consent",
            "submit_proposal",
            "_record_approval",
        }
    )
    proposal_service_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "ProposalService"
    ]
    base_names = {
        base.id
        for service_class in proposal_service_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert delegated_methods == []
    assert "ProposalTransitionServiceMixin" in base_names


def test_proposal_service_delegates_lifecycle_queries() -> None:
    path = _SERVICE_ROOT / "proposal_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "get_approvals",
            "get_proposal_lineage",
            "get_workflow_events",
        }
    )
    proposal_service_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "ProposalService"
    ]
    base_names = {
        base.id
        for service_class in proposal_service_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }
    lifecycle_query_methods = _function_names(_SERVICE_ROOT / "proposal_lifecycle_query_service.py")

    assert delegated_methods == []
    assert {
        "get_approvals",
        "get_proposal_lineage",
        "get_workflow_events",
    } <= lifecycle_query_methods
    assert "ProposalLifecycleQueryServiceMixin" in base_names


def test_proposal_service_delegates_delivery_posture_routes() -> None:
    path = _SERVICE_ROOT / "proposal_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "create_execution_handoff",
            "create_report_request",
            "get_delivery_events",
            "get_delivery_summary",
            "get_execution_status",
            "get_proposal_narrative",
            "record_execution_update",
            "regenerate_proposal_narrative",
            "review_proposal_narrative",
        }
    )
    proposal_service_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "ProposalService"
    ]
    base_names = {
        base.id
        for service_class in proposal_service_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert delegated_methods == []
    assert "ProposalDeliveryServiceMixin" in base_names


def test_workbench_service_delegates_sandbox_orchestration() -> None:
    path = _SERVICE_ROOT / "workbench_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "_apply_sandbox_changes_payload",
            "_build_sandbox_policy_state",
            "_evaluate_policy_feedback",
            "_load_projected_state",
            "apply_sandbox_changes",
            "create_sandbox_session",
        }
    )
    workbench_service_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "WorkbenchService"
    ]
    base_names = {
        base.id
        for service_class in workbench_service_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert delegated_methods == []
    assert "WorkbenchSandboxServiceMixin" in base_names


def test_portfolio_service_delegates_readiness_and_insight_source_loading() -> None:
    path = _SERVICE_ROOT / "portfolio_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    local_source_bundles = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and node.name in {"PortfolioReadinessSources", "PortfolioInsightSources"}
    )
    inline_source_gathers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "_load_portfolio_readiness_sources",
            "_load_portfolio_insight_sources",
        }
        and any(
            isinstance(child, ast.Attribute)
            and isinstance(child.value, ast.Name)
            and child.value.id == "asyncio"
            and child.attr == "gather"
            for child in ast.walk(node)
        )
    )

    assert local_source_bundles == []
    assert inline_source_gathers == []


def test_portfolio_service_delegates_book_source_loading() -> None:
    path = _SERVICE_ROOT / "portfolio_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    local_source_bundles = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "PortfolioBookSourceResults"
    )
    inline_source_gathers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "_load_portfolio_book_source_results"
        and any(
            isinstance(child, ast.Attribute)
            and isinstance(child.value, ast.Name)
            and child.value.id == "asyncio"
            and child.attr == "gather"
            for child in ast.walk(node)
        )
    )

    assert local_source_bundles == []
    assert inline_source_gathers == []


def test_portfolio_service_avoids_stale_workspace_wrapper_methods() -> None:
    path = _SERVICE_ROOT / "portfolio_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    stale_wrappers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name
        in {
            "_build_workspace_control_capabilities",
            "_optional_int",
            "_optional_str",
            "_parse_portfolio_identity",
            "_parse_portfolio_profile",
        }
    )

    assert stale_wrappers == []


def test_portfolio_service_delegates_upstream_payload_helpers() -> None:
    path = _SERVICE_ROOT / "portfolio_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    local_upstream_payload_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name
        in {
            "_build_safe_upstream_error_detail",
            "_format_upstream_error_detail",
            "_optional_payload",
            "_raise_on_upstream_client_error",
            "_require_payload",
        }
    )

    assert local_upstream_payload_helpers == []


def test_portfolio_service_delegates_transaction_workflows() -> None:
    path = _SERVICE_ROOT / "portfolio_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "get_transaction_ledger",
            "get_income_summary",
            "get_activity_summary",
            "_load_transaction_ledger_payload",
            "_load_transaction_summary_context",
            "_load_transaction_rows_page",
        }
    )
    portfolio_service_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "PortfolioService"
    ]
    base_names = {
        base.id
        for service_class in portfolio_service_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert delegated_methods == []
    assert "PortfolioTransactionServiceMixin" in base_names


def test_portfolio_transaction_ledger_delegates_request_mapping() -> None:
    ledger_methods = _function_names(_SERVICE_ROOT / "portfolio_transaction_ledger.py")
    ledger_imports = _imported_modules(_SERVICE_ROOT / "portfolio_transaction_ledger.py")
    request_methods = _function_names(_SERVICE_ROOT / "portfolio_transaction_requests.py")
    request_classes = _class_names(_SERVICE_ROOT / "portfolio_transaction_requests.py")
    request_mapping_methods = {
        "build_portfolio_transactions_request_context",
        "build_transaction_rows_page_request_context",
        "portfolio_transactions_cache_key",
        "portfolio_transactions_client_kwargs",
    }

    assert request_mapping_methods <= request_methods
    assert "PortfolioTransactionsRequestContext" in request_classes
    assert ledger_methods.isdisjoint(request_mapping_methods)
    assert "app.services.portfolio_transaction_requests" in ledger_imports


def test_portfolio_workflow_declares_only_the_ledger_arguments_it_uses() -> None:
    path = _SERVICE_ROOT / "portfolio_workflow_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    workflow_protocol = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "_PortfolioWorkflowDependencies"
    )
    ledger_method = next(
        node
        for node in workflow_protocol.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_transaction_ledger"
    )

    assert [argument.arg for argument in ledger_method.args.args] == [
        "self",
        "portfolio_id",
        "correlation_id",
        "as_of_date",
        "include_projected",
        "skip",
        "limit",
    ]
    assert ledger_method.args.vararg is None
    assert ledger_method.args.kwarg is None


def test_portfolio_service_delegates_workflow_orchestration() -> None:
    path = _SERVICE_ROOT / "portfolio_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "get_portfolio_workflow",
            "_get_latest_transaction_probe",
        }
    )
    portfolio_service_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "PortfolioService"
    ]
    base_names = {
        base.id
        for service_class in portfolio_service_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert delegated_methods == []
    assert "PortfolioWorkflowServiceMixin" in base_names


def test_portfolio_service_delegates_holdings_orchestration() -> None:
    path = _SERVICE_ROOT / "portfolio_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    delegated_methods = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name
        in {
            "get_portfolio_book",
            "_load_portfolio_book_source_results",
            "get_portfolio_liquidity",
            "_load_portfolio_liquidity_payloads",
            "get_portfolio_projected_cashflow",
            "get_portfolio_allocations",
            "_load_portfolio_allocation_payloads",
            "get_portfolio_positions",
            "_load_position_book_payloads",
        }
    )
    portfolio_service_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "PortfolioService"
    ]
    base_names = {
        base.id
        for service_class in portfolio_service_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert delegated_methods == []
    assert "PortfolioHoldingsServiceMixin" in base_names


def test_portfolio_holdings_service_delegates_projected_cashflow_orchestration() -> None:
    holdings_methods = _function_names(_SERVICE_ROOT / "portfolio_holdings_service.py")
    cashflow_methods = _function_names(_SERVICE_ROOT / "portfolio_projected_cashflow_service.py")

    assert "get_portfolio_projected_cashflow" in cashflow_methods
    assert "get_portfolio_projected_cashflow" not in holdings_methods


def test_portfolio_service_delegates_workspace_component_parsing() -> None:
    path = _SERVICE_ROOT / "portfolio_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    local_workspace_component_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name
        in {
            "_parse_cashflow",
            "_parse_operations",
            "_parse_summary",
            "_parse_workspace_performance",
            "_parse_workspace_rebalance",
            "_parse_workspace_rebalance_supportability",
            "_reporting_readiness",
            "_extract_resolved_as_of_date",
        }
    )
    local_workspace_component_state = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "PortfolioWorkspaceAssemblyState"
    )

    assert local_workspace_component_helpers == []
    assert local_workspace_component_state == []


def test_performance_workspace_service_delegates_request_context_policy() -> None:
    path = _SERVICE_ROOT / "performance_workspace_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    local_context_policy_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name
        in {
            "_assemble_attribution_trend_request_context",
            "_assemble_horizon_comparison_request_context",
            "_assemble_workspace_request_context",
            "_build_attribution_trend_dimension_context",
            "_build_horizon_chart_frequency_context",
            "_build_workspace_dimension_context",
        }
    )

    assert local_context_policy_helpers == []


def test_performance_workspace_service_delegates_trend_orchestration() -> None:
    path = _SERVICE_ROOT / "performance_workspace_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    local_trend_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name
        in {
            "get_performance_attribution_trend",
            "get_performance_horizon_comparison",
            "_build_attribution_trend_request_context",
            "_build_attribution_trend_response",
            "_build_attribution_trend_rows",
            "_build_attribution_trend_window_pairs",
            "_build_horizon_comparison_request_context",
            "_build_horizon_comparison_response",
            "_fetch_attribution_trend_results",
            "_fetch_horizon_comparison_dependencies",
            "_parse_horizon_comparison_rows",
        }
    )

    assert local_trend_helpers == []


def test_performance_workspace_trend_service_delegates_attribution_trend_orchestration() -> None:
    trend_service_path = _SERVICE_ROOT / "performance_workspace_trend_service.py"
    attribution_trend_service_path = (
        _SERVICE_ROOT / "performance_workspace_attribution_trend_service.py"
    )
    trend_service_tree = ast.parse(
        trend_service_path.read_text(encoding="utf-8"),
        filename=str(trend_service_path),
    )
    attribution_trend_service_tree = ast.parse(
        attribution_trend_service_path.read_text(encoding="utf-8"),
        filename=str(attribution_trend_service_path),
    )
    attribution_trend_helpers = {
        "get_performance_attribution_trend",
        "_build_attribution_trend_request_context",
        "_build_attribution_trend_response",
        "_build_attribution_trend_rows",
        "_build_attribution_trend_window_pairs",
        "_fetch_attribution_trend_results",
    }

    local_trend_service_helpers = sorted(
        node.name
        for node in ast.walk(trend_service_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in attribution_trend_helpers
    )
    extracted_trend_helpers = {
        node.name
        for node in ast.walk(attribution_trend_service_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert attribution_trend_helpers <= extracted_trend_helpers
    assert local_trend_service_helpers == []


def test_performance_workspace_service_delegates_detail_view_orchestration() -> None:
    path = _SERVICE_ROOT / "performance_workspace_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    local_detail_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name
        in {
            "_build_workspace_detail_views",
            "_should_fetch_independent_detail_views",
            "_build_independent_workspace_detail_views",
            "_fetch_independent_workspace_detail_results",
            "_build_summary_workspace_detail_views",
            "_workspace_summary_has_return_payload",
        }
    )

    assert local_detail_helpers == []


def test_performance_workspace_service_delegates_summary_view_orchestration() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "performance_workspace_service.py")
    summary_view_methods = _function_names(_SERVICE_ROOT / "performance_workspace_summary_views.py")

    assert "build_workspace_summary_views" in summary_view_methods
    assert "fetch_workspace_summary_view_result" in summary_view_methods
    assert "_build_workspace_summary_views" not in service_methods
    assert "_fetch_workspace_summary_view_result" not in service_methods


def test_performance_workspace_service_delegates_response_orchestration() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "performance_workspace_service.py")
    response_service_methods = _function_names(
        _SERVICE_ROOT / "performance_workspace_response_service.py"
    )
    response_orchestration_methods = {
        "_build_workspace_response_parts",
        "_build_workspace_response_components",
        "_build_workspace_response_evidence_view",
    }

    assert response_orchestration_methods <= response_service_methods
    assert not response_orchestration_methods & service_methods


def test_performance_workspace_capabilities_delegate_detail_capability_policy() -> None:
    capability_methods = _function_names(_SERVICE_ROOT / "performance_workspace_capabilities.py")
    detail_methods = _function_names(_SERVICE_ROOT / "performance_workspace_detail_capabilities.py")
    delegated_detail_methods = {
        "build_attribution_capability",
        "build_contribution_capability",
        "build_detail_capabilities",
    }

    assert delegated_detail_methods <= detail_methods
    assert capability_methods.isdisjoint(delegated_detail_methods)


def test_performance_workspace_capabilities_delegate_module_capability_builder() -> None:
    capability_methods = _function_names(_SERVICE_ROOT / "performance_workspace_capabilities.py")
    module_methods = _function_names(_SERVICE_ROOT / "performance_workspace_module_capability.py")

    assert "build_module_capability" in module_methods
    assert "build_module_capability" not in capability_methods


def test_performance_workspace_service_delegates_evidence_orchestration() -> None:
    path = _SERVICE_ROOT / "performance_workspace_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    local_evidence_helpers = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name
        in {
            "get_performance_evidence_artifact",
            "_build_evidence_view",
            "_fetch_evidence_view_state",
        }
    )
    service_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "PerformanceWorkspaceService"
    ]
    base_names = {
        base.id
        for service_class in service_classes
        for base in service_class.bases
        if isinstance(base, ast.Name)
    }

    assert local_evidence_helpers == []
    assert "PerformanceWorkspaceEvidenceServiceMixin" in base_names


def test_performance_workspace_evidence_delegates_response_composition() -> None:
    evidence_facade_methods = _function_names(_SERVICE_ROOT / "performance_workspace_evidence.py")
    response_methods = _function_names(_SERVICE_ROOT / "performance_workspace_evidence_response.py")
    expected_response_methods = {
        "build_performance_evidence_view",
        "resolve_evidence_view_response",
    }

    assert expected_response_methods <= response_methods
    assert evidence_facade_methods.isdisjoint(expected_response_methods)


def test_performance_workspace_evidence_delegates_supportability_policy() -> None:
    response_methods = _function_names(_SERVICE_ROOT / "performance_workspace_evidence_response.py")
    supportability_methods = _function_names(
        _SERVICE_ROOT / "performance_workspace_evidence_supportability.py"
    )
    expected_supportability_methods = {
        "build_source_supportability",
        "resolve_evidence_reason",
        "resolve_evidence_state",
    }

    assert expected_supportability_methods <= supportability_methods
    assert response_methods.isdisjoint(expected_supportability_methods)


def test_performance_calculation_evidence_delegates_completion_polling() -> None:
    calculation_methods = _function_names(_SERVICE_ROOT / "performance_calculation_evidence.py")
    completion_methods = _function_names(
        _SERVICE_ROOT / "performance_calculation_evidence_completion.py"
    )
    expected_completion_methods = {
        "await_recent_evidence_completion",
        "execution_is_complete",
        "execution_lineage_stage_complete",
        "lineage_is_complete",
        "lineage_is_transient",
        "refresh_execution_after_lineage_completion",
    }

    assert expected_completion_methods <= completion_methods
    assert calculation_methods.isdisjoint(expected_completion_methods)


def test_performance_contribution_delegates_payload_mapping() -> None:
    contribution_methods = _function_names(_SERVICE_ROOT / "performance_workspace_contribution.py")
    payload_methods = _function_names(
        _SERVICE_ROOT / "performance_workspace_contribution_payloads.py"
    )
    expected_payload_methods = {
        "build_contribution_rows",
        "build_detail_contribution_levels",
        "build_position_rows",
        "build_workspace_contribution_levels",
        "parse_contribution_smoothing_evidence",
        "parse_contribution_source_economics_evidence",
    }

    assert expected_payload_methods <= payload_methods
    assert contribution_methods.isdisjoint(expected_payload_methods)


def test_risk_workspace_mappers_delegate_source_supportability() -> None:
    source_supportability_methods = _function_names(
        _SERVICE_ROOT / "risk_workspace_source_supportability.py"
    )
    rolling_methods = _function_names(_SERVICE_ROOT / "risk_workspace_rolling.py")
    attribution_methods = _function_names(_SERVICE_ROOT / "risk_workspace_attribution.py")

    assert "append_source_calculation_supportability" in source_supportability_methods
    assert "_append_source_calculation_supportability" not in rolling_methods
    assert "_append_source_calculation_supportability" not in attribution_methods


def test_risk_workspace_rolling_delegates_period_mapping() -> None:
    rolling_methods = _function_names(_SERVICE_ROOT / "risk_workspace_rolling.py")
    period_methods = _function_names(_SERVICE_ROOT / "risk_workspace_rolling_periods.py")
    expected_period_methods = {
        "map_rolling_period_result",
        "map_rolling_period_results",
    }

    assert expected_period_methods <= period_methods
    assert rolling_methods.isdisjoint(expected_period_methods)


def test_risk_workspace_attribution_controls_delegate_supportability_items() -> None:
    controls_methods = _function_names(_SERVICE_ROOT / "risk_workspace_attribution_controls.py")
    supportability_methods = _function_names(
        _SERVICE_ROOT / "risk_workspace_attribution_supportability.py"
    )
    expected_supportability_methods = {
        "build_attribution_supportability",
        "build_base_attribution_supportability_items",
        "build_active_risk_supportability_items",
        "active_risk_benchmark_exposure_state",
        "build_total_risk_benchmark_exposure_supportability_item",
        "total_risk_gated_grouping_reason",
    }

    assert expected_supportability_methods <= supportability_methods
    assert controls_methods.isdisjoint(expected_supportability_methods)


def test_risk_workspace_attribution_delegates_period_mapping() -> None:
    attribution_methods = _function_names(_SERVICE_ROOT / "risk_workspace_attribution.py")
    mapping_methods = _function_names(_SERVICE_ROOT / "risk_workspace_attribution_mapping.py")
    expected_mapping_methods = {
        "map_attribution_period_results",
        "_map_attribution_period_result",
        "_map_attribution_sets",
        "_map_attribution_set",
        "_map_attribution_contributors",
        "_safe_float",
    }

    assert expected_mapping_methods <= mapping_methods
    assert attribution_methods.isdisjoint(expected_mapping_methods)


def test_risk_workspace_service_delegates_response_loading() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "risk_workspace_service.py")
    response_loading_methods = _function_names(_SERVICE_ROOT / "risk_workspace_response_loading.py")
    expected_response_loading_methods = {
        "load_concentration_response",
        "load_drawdown_response",
        "load_rolling_response",
        "load_summary_response",
        "post_rolling_metrics",
    }

    assert expected_response_loading_methods <= response_loading_methods
    assert service_methods.isdisjoint(expected_response_loading_methods)


def test_risk_workspace_concentration_delegates_supportability_mapping() -> None:
    mapper_methods = _function_names(_SERVICE_ROOT / "risk_workspace_concentration.py")
    supportability_methods = _function_names(
        _SERVICE_ROOT / "risk_workspace_concentration_supportability.py"
    )
    expected_supportability_methods = {
        "extract_concentration_blocks",
        "build_concentration_supportability",
        "append_source_calculation_supportability",
        "_issuer_supportability_state",
        "_issuer_supportability_reason",
        "_issuer_grouping_reason",
        "_valuation_context_reason",
    }

    assert expected_supportability_methods <= supportability_methods
    assert mapper_methods.isdisjoint(expected_supportability_methods)


def test_dpm_proof_pack_service_delegates_supportability_mapping() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "dpm_proof_pack_service.py")
    supportability_methods = _function_names(_SERVICE_ROOT / "dpm_proof_pack_supportability.py")
    expected_supportability_methods = {
        "build_dpm_proof_pack_supportability",
        "_proof_pack_payload",
        "_proof_pack_state",
        "_reason_codes_from_payload",
        "_section_state_counts",
        "_sections",
    }

    assert expected_supportability_methods <= supportability_methods
    assert service_methods.isdisjoint(expected_supportability_methods)


def test_platform_capabilities_shell_delegates_workspace_descriptors() -> None:
    shell_methods = _function_names(_SERVICE_ROOT / "platform_capabilities_shell.py")
    descriptor_methods = _function_names(
        _SERVICE_ROOT / "platform_capabilities_workspace_descriptors.py"
    )
    expected_descriptor_methods = {
        "build_workspace_descriptor",
        "build_workspace_descriptor_from_spec",
        "workspace_caching",
        "workspace_descriptors",
        "workspace_evidence",
        "workspace_freshness",
        "workspace_supportability",
        "workspace_versioning",
    }

    assert expected_descriptor_methods <= descriptor_methods
    assert shell_methods.isdisjoint(expected_descriptor_methods)


def test_workspace_descriptors_delegate_state_derivation() -> None:
    descriptor_methods = _function_names(
        _SERVICE_ROOT / "platform_capabilities_workspace_descriptors.py"
    )
    descriptor_imports = _imported_modules(
        _SERVICE_ROOT / "platform_capabilities_workspace_descriptors.py"
    )
    state_methods = _function_names(
        _SERVICE_ROOT / "platform_capabilities_workspace_descriptor_state.py"
    )
    state_classes = _class_names(
        _SERVICE_ROOT / "platform_capabilities_workspace_descriptor_state.py"
    )
    expected_state_methods = {
        "apply_source_supportability",
        "source_supportability",
        "workspace_descriptor_state",
    }

    assert expected_state_methods <= state_methods
    assert "WorkspaceDescriptorState" in state_classes
    assert descriptor_methods.isdisjoint(expected_state_methods)
    assert "app.services.platform_capabilities_workspace_descriptor_state" in descriptor_imports


def test_platform_capabilities_workspace_descriptors_delegate_static_specs() -> None:
    descriptors_imports = _imported_modules(
        _SERVICE_ROOT / "platform_capabilities_workspace_descriptors.py"
    )
    descriptor_classes = _class_names(
        _SERVICE_ROOT / "platform_capabilities_workspace_descriptors.py"
    )
    spec_classes = _class_names(
        _SERVICE_ROOT / "platform_capabilities_workspace_descriptor_specs.py"
    )

    assert "app.services.platform_capabilities_workspace_descriptor_specs" in descriptors_imports
    assert "WorkspaceDescriptorSpec" in spec_classes
    assert "WorkspaceDescriptorSpec" not in descriptor_classes


def test_platform_capabilities_service_delegates_source_result_parsing() -> None:
    service_methods = _function_names(_SERVICE_ROOT / "platform_capabilities_service.py")
    source_methods = _function_names(_SERVICE_ROOT / "platform_capabilities_sources.py")
    expected_source_methods = {
        "exception_detail",
        "lotus_core_policy_from_result",
        "merge_optional_capability_sources",
        "merge_optional_source",
        "payload_from_source_result",
        "primary_sources_from_results",
    }

    assert expected_source_methods <= source_methods
    assert service_methods.isdisjoint(expected_source_methods)


def test_platform_capabilities_normalization_delegates_feature_and_workflow_flags() -> None:
    normalization_methods = _function_names(
        _SERVICE_ROOT / "platform_capabilities_normalization.py"
    )
    flag_methods = _function_names(_SERVICE_ROOT / "platform_capabilities_feature_flags.py")
    expected_flag_methods = {
        "advise_lifecycle_enabled",
        "any_feature_enabled",
        "any_workflow_enabled",
        "core_intake_enabled",
        "core_snapshot_enabled",
        "feature_enabled",
        "feature_enablement",
        "manage_support_enabled",
        "performance_analytics_enabled",
        "reporting_enabled",
        "risk_analytics_enabled",
        "workflow_enabled",
        "workflow_flags",
    }

    assert expected_flag_methods <= flag_methods
    assert normalization_methods.isdisjoint(expected_flag_methods)


def test_service_tests_do_not_need_arg_type_suppressions() -> None:
    offenders: dict[str, int] = {}
    for path in _TEST_ROOT.glob("test_*_service.py"):
        suppression_count = path.read_text(encoding="utf-8").count("# type: ignore[arg-type]")
        if suppression_count:
            offenders[path.name] = suppression_count

    assert offenders == {}


def test_service_tests_do_not_need_stub_method_suppressions() -> None:
    forbidden_suppressions = ("# type: ignore[method-assign]", "# type: ignore[override]")
    offenders: dict[str, dict[str, int]] = {}
    for path in _TEST_ROOT.glob("test_*_service.py"):
        text = path.read_text(encoding="utf-8")
        suppression_counts = {
            suppression: text.count(suppression)
            for suppression in forbidden_suppressions
            if suppression in text
        }
        if suppression_counts:
            offenders[path.name] = suppression_counts

    assert offenders == {}


def test_services_do_not_emit_raw_upstream_payload_details() -> None:
    forbidden_patterns = (
        "stringify_payload=True",
        'payload.get("detail", payload)',
        'upstream_payload.get("detail", upstream_payload)',
        "detail=upstream_payload",
        '"error": upstream_payload',
    )
    offenders: dict[str, list[str]] = {}
    for path in _SERVICE_ROOT.rglob("*.py"):
        if path.name == "upstream_envelope.py":
            continue
        text = path.read_text(encoding="utf-8")
        matches = [pattern for pattern in forbidden_patterns if pattern in text]
        if matches:
            offenders[path.relative_to(_SERVICE_ROOT).as_posix()] = matches

    assert offenders == {}


def test_upstream_envelope_delegates_error_policy() -> None:
    envelope_methods = _function_names(_SERVICE_ROOT / "upstream_envelope.py")
    policy_methods = _function_names(_SERVICE_ROOT / "upstream_error_policy.py")
    delegated_methods = {
        "safe_upstream_detail",
        "gateway_status_for_service_error",
    }

    assert delegated_methods <= policy_methods
    assert envelope_methods.isdisjoint(delegated_methods)


def test_non_client_service_factories_do_not_repeat_upstream_routing_settings() -> None:
    offenders: dict[str, list[str]] = {}
    for path in _SERVICE_ROOT.glob("*_service_factory.py"):
        if path.name in _CLIENT_FACTORY_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        repeated_settings = sorted(
            {
                node.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "settings"
                and node.attr != "platform_capabilities_source_timeout_seconds"
                and node.attr.endswith(_UPSTREAM_ROUTING_SETTING_SUFFIXES)
            }
        )
        if repeated_settings:
            offenders[path.relative_to(_SERVICE_ROOT).as_posix()] = repeated_settings

    assert offenders == {}
