import ast
from pathlib import Path

_CLIENT_ROOT = Path(__file__).parents[2] / "src" / "app" / "clients"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def test_bank_demo_proof_routes_live_in_dedicated_client_mixin() -> None:
    advise_client_methods = _async_function_names(_CLIENT_ROOT / "advise_client.py")
    bank_demo_methods = _async_function_names(_CLIENT_ROOT / "advise_bank_demo_proof_client.py")

    extracted_methods = {
        "build_bank_demo_proof_pack",
        "get_bank_demo_proof_scenario_contract",
        "get_bank_demo_supported_claim_register",
    }

    assert extracted_methods <= bank_demo_methods
    assert not extracted_methods & advise_client_methods
