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
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


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
