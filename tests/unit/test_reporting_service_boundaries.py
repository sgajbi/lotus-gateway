import ast
from pathlib import Path

_SERVICE_ROOT = Path(__file__).parents[2] / "src" / "app" / "services"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_reporting_services_do_not_depend_on_router_modules() -> None:
    offenders = {
        path.name: sorted(
            module
            for module in _imported_modules(path)
            if module == "app.routers" or module.startswith("app.routers.")
        )
        for path in _SERVICE_ROOT.glob("reporting*_service.py")
    }
    offenders = {name: imports for name, imports in offenders.items() if imports}

    assert offenders == {}
