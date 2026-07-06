"""Remove local generated artifacts and cache byproducts from a Gateway checkout."""

from __future__ import annotations

import argparse
import shutil
from collections.abc import Iterable
from pathlib import Path

ROOT_DIRECTORIES = (
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "htmlcov",
    "output",
    ".codex-logs",
)
ROOT_FILES = (".coverage",)
ROOT_GLOBS = ("gateway-*.log",)
RECURSIVE_DIRECTORIES = ("__pycache__", "*.egg-info")
RECURSIVE_FILES = ("*.pyc",)
PROTECTED_PARTS = {".git", ".venv", "venv", "node_modules"}


def generated_artifact_paths(repo_root: Path) -> list[Path]:
    """Return disposable generated artifacts for the repository root."""

    root = repo_root.resolve()
    candidates: list[Path] = []

    candidates.extend(root / directory for directory in ROOT_DIRECTORIES)
    candidates.extend(root / file_name for file_name in ROOT_FILES)
    for pattern in ROOT_GLOBS:
        candidates.extend(root.glob(pattern))
    for directory_name in RECURSIVE_DIRECTORIES:
        candidates.extend(path for path in root.rglob(directory_name) if path.is_dir())
    for pattern in RECURSIVE_FILES:
        candidates.extend(path for path in root.rglob(pattern) if path.is_file())

    return _dedupe_existing_paths(
        path for path in candidates if path.exists() and _is_disposable_path(path, root)
    )


def clean_generated_artifacts(repo_root: Path, *, dry_run: bool = False) -> list[Path]:
    """Remove disposable generated artifacts and return the paths that were targeted."""

    root = repo_root.resolve()
    removed = generated_artifact_paths(root)
    if dry_run:
        return removed

    for path in sorted(removed, key=lambda item: len(item.parts), reverse=True):
        remove_disposable_path(path, repo_root=root)
    return removed


def remove_disposable_path(path: Path, *, repo_root: Path) -> None:
    """Remove one generated artifact after verifying it is safely inside the repo."""

    root = repo_root.resolve()
    target = path.resolve()
    if target == root or root not in target.parents:
        raise ValueError(f"Refusing to delete outside repository root: {target}")
    relative_parts = set(target.relative_to(root).parts)
    if relative_parts & PROTECTED_PARTS:
        raise ValueError(f"Refusing to delete protected repository path: {target}")

    if target.is_dir():
        shutil.rmtree(target)
        return
    target.unlink(missing_ok=True)


def _dedupe_existing_paths(paths: Iterable[Path]) -> list[Path]:
    resolved_paths: dict[Path, Path] = {}
    for path in paths:
        resolved_paths[path.resolve()] = path
    collapsed: dict[Path, Path] = {}
    for resolved, original in sorted(resolved_paths.items(), key=lambda item: len(item[0].parts)):
        if any(parent in collapsed for parent in resolved.parents):
            continue
        collapsed[resolved] = original
    return list(collapsed.values())


def _is_disposable_path(path: Path, repo_root: Path) -> bool:
    try:
        relative_parts = set(path.resolve().relative_to(repo_root).parts)
    except ValueError:
        return False
    return not (relative_parts & PROTECTED_PARTS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove Gateway local generated artifacts and cache byproducts.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to clean. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List disposable paths without deleting them.",
    )
    args = parser.parse_args()

    removed = clean_generated_artifacts(args.repo_root, dry_run=args.dry_run)
    action = "Would remove" if args.dry_run else "Removed"
    for path in removed:
        print(path)
    print(f"{action} {len(removed)} generated artifact path(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
