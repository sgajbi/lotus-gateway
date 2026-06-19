import ast
from pathlib import Path

_CLIENT_ROOT = Path(__file__).parents[2] / "src" / "app" / "clients"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def test_risk_analytics_routes_live_in_dedicated_client_mixin() -> None:
    analytics_methods = _async_function_names(_CLIENT_ROOT / "lotus_analytics_client.py")
    risk_methods = _async_function_names(_CLIENT_ROOT / "lotus_analytics_risk_client.py")

    extracted_methods = {
        "post_risk_calculate",
        "post_risk_concentration",
        "post_risk_drawdown",
        "post_risk_rolling_metrics",
        "post_risk_historical_attribution",
    }

    assert extracted_methods <= risk_methods
    assert not extracted_methods & analytics_methods
