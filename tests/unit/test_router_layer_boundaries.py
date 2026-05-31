import ast
from pathlib import Path

_ROUTER_ROOT = Path(__file__).parents[2] / "src" / "app" / "routers"


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
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)
    }


def _is_router_handler(node: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    return any(
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and isinstance(decorator.func.value, ast.Name)
        and decorator.func.value.id == "router"
        for decorator in node.decorator_list
    )


def _direct_service_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if not _is_router_handler(node):
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if not isinstance(child.func, ast.Attribute):
                continue
            if not isinstance(child.func.value, ast.Call):
                continue
            service_factory = child.func.value.func
            if isinstance(service_factory, ast.Name) and service_factory.id.endswith("_service"):
                calls.append(f"{node.name}:{service_factory.id}.{child.func.attr}")
    return calls


def _direct_correlation_access(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    handlers: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if not _is_router_handler(node):
            continue
        if any(
            isinstance(child, ast.Name) and child.id == "correlation_id_var"
            for child in ast.walk(node)
        ):
            handlers.append(node.name)
    return handlers


def _route_handler_dict_literals(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    handlers: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if not _is_router_handler(node):
            continue
        if any(
            isinstance(child, ast.Dict) for statement in node.body for child in ast.walk(statement)
        ):
            handlers.append(node.name)
    return handlers


def test_routers_do_not_import_service_factories_or_clients() -> None:
    offenders = {
        path.name: sorted(
            module
            for module in _imported_modules(path)
            if module.startswith("app.clients.")
            or (module.startswith("app.services.") and module.endswith("_factory"))
        )
        for path in _ROUTER_ROOT.glob("*.py")
    }
    offenders = {name: imports for name, imports in offenders.items() if imports}

    assert offenders == {}


def test_router_handlers_delegate_service_calls_to_private_helpers() -> None:
    offenders = {path.name: _direct_service_calls(path) for path in _ROUTER_ROOT.glob("*.py")}
    offenders = {name: calls for name, calls in offenders.items() if calls}

    assert offenders == {}


def test_router_handlers_delegate_filter_construction_to_private_helpers() -> None:
    offenders = {
        path.name: _route_handler_dict_literals(path) for path in _ROUTER_ROOT.glob("*.py")
    }
    offenders = {name: handlers for name, handlers in offenders.items() if handlers}

    assert offenders == {}


def test_router_handlers_delegate_correlation_to_private_helpers() -> None:
    offenders = {path.name: _direct_correlation_access(path) for path in _ROUTER_ROOT.glob("*.py")}
    offenders = {name: handlers for name, handlers in offenders.items() if handlers}

    assert offenders == {}


def test_routers_do_not_define_private_service_factories() -> None:
    offenders = {
        path.name: sorted(
            name
            for name in _function_names(path)
            if name.startswith("_") and name.endswith("service")
        )
        for path in _ROUTER_ROOT.glob("*.py")
    }
    offenders = {name: functions for name, functions in offenders.items() if functions}

    assert offenders == {}
