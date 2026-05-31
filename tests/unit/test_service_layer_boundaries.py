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


def test_non_dpm_service_tests_do_not_need_arg_type_suppressions() -> None:
    allowed = {
        "test_dpm_command_center_service.py",
        "test_dpm_wave_service.py",
    }
    offenders: dict[str, int] = {}
    for path in _TEST_ROOT.glob("test_*_service.py"):
        if path.name in allowed:
            continue
        suppression_count = path.read_text(encoding="utf-8").count("# type: ignore[arg-type]")
        if suppression_count:
            offenders[path.name] = suppression_count

    assert offenders == {}


def test_narrowed_advisory_services_do_not_import_concrete_advise_client() -> None:
    narrowed_services = {
        "advisor_cockpit_service.py",
        "advisory_policy_service.py",
        "advisory_workspace_service.py",
        "bank_demo_proof_service.py",
        "proposal_service.py",
    }
    offenders = sorted(
        path.name
        for path in (_SERVICE_ROOT / service_name for service_name in narrowed_services)
        if "app.clients.advise_client" in _imported_modules(path)
    )

    assert offenders == []


def test_narrowed_reporting_services_do_not_import_concrete_reporting_clients() -> None:
    narrowed_services = {
        "reporting_batch_control_service.py",
        "reporting_batch_lifecycle_service.py",
        "reporting_batch_scheduler_service.py",
        "reporting_job_query_service.py",
        "reporting_job_submission_service.py",
        "reporting_portfolio_service.py",
    }
    concrete_client_modules = {
        "app.clients.render_client",
        "app.clients.reporting_client",
    }
    offenders = {
        path.name: sorted(_imported_modules(path) & concrete_client_modules)
        for path in (_SERVICE_ROOT / service_name for service_name in narrowed_services)
    }
    offenders = {name: imports for name, imports in offenders.items() if imports}

    assert offenders == {}


def test_narrowed_archive_services_do_not_import_concrete_archive_client() -> None:
    path = _SERVICE_ROOT / "archive_document_service.py"

    assert "app.clients.archive_client" not in _imported_modules(path)


def test_narrowed_performance_and_core_services_do_not_import_concrete_clients() -> None:
    narrowed_service_imports = {
        "composite_performance_service.py": {"app.clients.lotus_analytics_client"},
        "intake_service.py": {
            "app.clients.lotus_core_ingestion_client",
            "app.clients.lotus_core_query_client",
        },
        "risk_workspace_service.py": {"app.clients.lotus_analytics_client"},
        "source_product_execution_service.py": {"app.clients.lotus_core_query_client"},
    }
    offenders = {
        service_name: sorted(concrete_imports & _imported_modules(_SERVICE_ROOT / service_name))
        for service_name, concrete_imports in narrowed_service_imports.items()
        if concrete_imports & _imported_modules(_SERVICE_ROOT / service_name)
    }

    assert offenders == {}


def test_platform_capabilities_service_does_not_import_concrete_clients() -> None:
    concrete_imports = {
        "app.clients.advise_client",
        "app.clients.dpm_client",
        "app.clients.lotus_analytics_client",
        "app.clients.lotus_core_query_client",
        "app.clients.reporting_client",
    }
    imports = _imported_modules(_SERVICE_ROOT / "platform_capabilities_service.py")

    assert imports & concrete_imports == set()


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
