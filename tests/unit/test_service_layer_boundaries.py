import ast
from pathlib import Path

_SERVICE_ROOT = Path(__file__).parents[2] / "src" / "app" / "services"
_TEST_ROOT = Path(__file__).parents[2] / "tests" / "unit"
_CLIENT_FACTORY_FILES = {
    "advise_client_factory.py",
    "analytics_client_factory.py",
    "archive_client_factory.py",
    "dpm_service_factory.py",
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
