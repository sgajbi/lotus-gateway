from __future__ import annotations

import tomllib
from pathlib import Path

from scripts.check_testclient_dependency import parse_version


def test_fastapi_resolution_excludes_blocked_security_audit_release() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dependencies = pyproject["project"]["dependencies"]
    audit_requirements = Path("requirements-audit.txt").read_text(encoding="utf-8").splitlines()

    assert "fastapi>=0.129.0,<0.136.3" in dependencies
    assert "fastapi>=0.129.0,<0.136.3" in audit_requirements


def test_pydantic_floor_supports_tolerant_nested_source_parsing() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dependencies = pyproject["project"]["dependencies"]
    audit_requirements = Path("requirements-audit.txt").read_text(encoding="utf-8").splitlines()

    assert "pydantic>=2.12.0" in dependencies
    assert "pydantic>=2.12.0" in audit_requirements


def test_testclient_uses_secure_dev_only_httpx2_dependency() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dev_dependencies = pyproject["project"]["optional-dependencies"]["dev"]
    audit_requirements = Path("requirements-audit.txt").read_text(encoding="utf-8").splitlines()

    assert "httpx2>=2.12.0,<3.0.0" in dev_dependencies
    assert not any(requirement.startswith("httpx2") for requirement in audit_requirements)


def test_testclient_version_gate_rejects_prerelease_and_malformed_versions() -> None:
    assert parse_version("2.12.0") == (2, 12, 0)
    assert parse_version("2.12.0rc1") == (0, 0, 0)
    assert parse_version("not-a-version") == (0, 0, 0)
