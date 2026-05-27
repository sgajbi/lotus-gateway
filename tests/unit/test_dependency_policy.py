from __future__ import annotations

import tomllib
from pathlib import Path


def test_fastapi_resolution_excludes_blocked_security_audit_release() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dependencies = pyproject["project"]["dependencies"]
    audit_requirements = Path("requirements-audit.txt").read_text(encoding="utf-8").splitlines()

    assert "fastapi>=0.129.0,<0.136.3" in dependencies
    assert "fastapi>=0.129.0,<0.136.3" in audit_requirements
