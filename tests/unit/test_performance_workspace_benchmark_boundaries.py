import ast
from pathlib import Path

_SERVICE_ROOT = Path(__file__).parents[2] / "src" / "app" / "services"


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def test_benchmark_catalog_parsing_lives_outside_context_orchestration() -> None:
    orchestration_functions = _function_names(_SERVICE_ROOT / "performance_workspace_benchmarks.py")
    catalog_functions = _function_names(
        _SERVICE_ROOT / "performance_workspace_benchmark_catalog.py"
    )

    catalog_parser_functions = {
        "_benchmark_catalog_records_from_result",
        "_benchmark_option_from_record",
        "_benchmark_options_from_records",
        "_record_benchmark_catalog_failure",
        "_upsert_benchmark_option",
        "parse_benchmark_catalog_result",
    }

    assert catalog_parser_functions <= catalog_functions
    assert orchestration_functions.isdisjoint(catalog_parser_functions)
