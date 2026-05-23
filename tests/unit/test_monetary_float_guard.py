from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_guard_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_monetary_float_usage.py"
    spec = importlib.util.spec_from_file_location("check_monetary_float_usage", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_scan_repo_ignores_local_virtualenv_directories(tmp_path: Path) -> None:
    guard = _load_guard_module()
    product_file = tmp_path / "src" / "app" / "services" / "portfolio_service.py"
    product_file.parent.mkdir(parents=True)
    product_file.write_text("market_value: float = 1.0\n", encoding="utf-8")

    virtualenv_file = tmp_path / ".venv-codex" / "Lib" / "site-packages" / "vendor.py"
    virtualenv_file.parent.mkdir(parents=True)
    virtualenv_file.write_text("market_value: float = 1.0\n", encoding="utf-8")

    findings = guard.scan_repo(tmp_path)

    assert findings == ["src/app/services/portfolio_service.py:1:market_value: float = 1.0"]
