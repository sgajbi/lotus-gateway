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
