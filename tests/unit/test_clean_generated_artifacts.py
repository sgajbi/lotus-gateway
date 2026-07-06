from pathlib import Path

import pytest

from scripts.clean_generated_artifacts import (
    clean_generated_artifacts,
    generated_artifact_paths,
    remove_disposable_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_clean_generated_artifacts_removes_repo_generated_byproducts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    source_file = repo / "src" / "app" / "main.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("print('keep source')\n", encoding="utf-8")
    for directory in (
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "htmlcov",
        "output",
        ".codex-logs",
        "src/app/__pycache__",
        "tests/unit/__pycache__",
        "src/lotus_gateway.egg-info",
    ):
        artifact_dir = repo / directory
        artifact_dir.mkdir(parents=True)
        (artifact_dir / "artifact.txt").write_text("generated\n", encoding="utf-8")
    for file_name in (
        ".coverage",
        "gateway-local.log",
        "src/app/__pycache__/main.cpython-312.pyc",
        "tests/unit/test_example.cpython-312.pyc",
    ):
        artifact_file = repo / file_name
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("generated\n", encoding="utf-8")

    removed = clean_generated_artifacts(repo)

    assert removed
    for path in removed:
        assert not path.exists()
    assert source_file.exists()
    assert not (repo / "output").exists()
    assert not (repo / "gateway-local.log").exists()


def test_clean_generated_artifacts_preserves_protected_repository_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    protected_cache = repo / ".git" / "__pycache__"
    protected_cache.mkdir(parents=True)
    protected_file = protected_cache / "git.cpython-312.pyc"
    protected_file.write_text("keep\n", encoding="utf-8")
    venv_cache = repo / ".venv" / "__pycache__"
    venv_cache.mkdir(parents=True)
    venv_file = venv_cache / "dep.cpython-312.pyc"
    venv_file.write_text("keep\n", encoding="utf-8")

    removed = clean_generated_artifacts(repo)

    assert removed == []
    assert protected_file.exists()
    assert venv_file.exists()


def test_clean_generated_artifacts_refuses_outside_repo_deletion(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.log"
    outside.write_text("do not delete\n", encoding="utf-8")

    with pytest.raises(ValueError, match="outside repository root"):
        remove_disposable_path(outside, repo_root=repo)

    assert outside.exists()


def test_generated_artifact_dry_run_lists_without_deleting(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    coverage = repo / ".coverage"
    coverage.write_text("coverage\n", encoding="utf-8")

    listed = clean_generated_artifacts(repo, dry_run=True)

    assert listed == [coverage]
    assert generated_artifact_paths(repo) == [coverage]
    assert coverage.exists()


def test_make_clean_uses_cleanup_script() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "python scripts/clean_generated_artifacts.py" in makefile
    assert "python -c" not in makefile
