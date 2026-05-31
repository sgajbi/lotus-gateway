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
