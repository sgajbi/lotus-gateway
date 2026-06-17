import ast
from pathlib import Path

_CLIENT_ROOT = Path(__file__).parents[2] / "src" / "app" / "clients"


def _async_function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)}


def test_pm_operating_quality_routes_live_in_dedicated_client_mixin() -> None:
    dpm_client_methods = _async_function_names(_CLIENT_ROOT / "dpm_client.py")
    pm_quality_methods = _async_function_names(_CLIENT_ROOT / "dpm_pm_operating_quality_client.py")

    extracted_methods = {
        name for name in pm_quality_methods if name.startswith(("preview_pm_", "create_pm_"))
    } | {name for name in pm_quality_methods if name.startswith(("list_pm_", "get_pm_", "put_pm_"))}

    assert extracted_methods
    assert not {
        name for name in dpm_client_methods if name.startswith(("preview_pm_", "create_pm_"))
    }
    assert not {
        name for name in dpm_client_methods if name.startswith(("list_pm_", "get_pm_", "put_pm_"))
    }


def test_construction_routes_live_in_dedicated_client_mixin() -> None:
    dpm_client_methods = _async_function_names(_CLIENT_ROOT / "dpm_client.py")
    construction_methods = _async_function_names(_CLIENT_ROOT / "dpm_construction_client.py")

    extracted_methods = {
        "generate_construction_alternative_set",
        "get_construction_alternative_set",
        "select_construction_alternative",
    }

    assert extracted_methods <= construction_methods
    assert not extracted_methods & dpm_client_methods


def test_proof_pack_routes_live_in_dedicated_client_mixin() -> None:
    dpm_client_methods = _async_function_names(_CLIENT_ROOT / "dpm_client.py")
    proof_pack_methods = _async_function_names(_CLIENT_ROOT / "dpm_proof_pack_client.py")

    extracted_methods = {
        "generate_proof_pack",
        "get_proof_pack",
        "get_proof_pack_markdown",
        "get_proof_pack_report_input",
        "get_proof_pack_ai_evidence_input",
    }

    assert extracted_methods <= proof_pack_methods
    assert not extracted_methods & dpm_client_methods
