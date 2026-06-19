import ast
from pathlib import Path

_CLIENT_ROOT = Path(__file__).parents[2] / "src" / "app" / "clients"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def test_lotus_core_lookup_routes_live_in_dedicated_client_mixin() -> None:
    query_methods = _async_function_names(_CLIENT_ROOT / "lotus_core_query_client.py")
    lookup_methods = _async_function_names(_CLIENT_ROOT / "lotus_core_lookup_client.py")

    extracted_methods = {
        "_get_lookup",
        "get_portfolio_lookups",
        "get_instrument_lookups",
        "get_currency_lookups",
    }

    assert extracted_methods <= lookup_methods
    assert not extracted_methods & query_methods
