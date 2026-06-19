from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_SOURCE_ROOT = Path("src/app")
DEFAULT_MAX_SOURCE_FILE_LINES = 432
DEFAULT_MAX_FUNCTION_LINES = 49


@dataclass(frozen=True)
class FileSizeViolation:
    path: Path
    line_count: int
    max_lines: int

    def format(self) -> str:
        return f"{self.path}: {self.line_count} lines exceeds max {self.max_lines}"


@dataclass(frozen=True)
class FunctionSizeViolation:
    path: Path
    line_number: int
    function_name: str
    line_count: int
    max_lines: int

    def format(self) -> str:
        return (
            f"{self.path}:{self.line_number} {self.function_name}: "
            f"{self.line_count} lines exceeds max {self.max_lines}"
        )


@dataclass(frozen=True)
class ThresholdResult:
    file_size_violations: tuple[FileSizeViolation, ...]
    function_size_violations: tuple[FunctionSizeViolation, ...]

    @property
    def passed(self) -> bool:
        return not self.file_size_violations and not self.function_size_violations


def iter_python_files(source_roots: Sequence[Path]) -> Iterable[Path]:
    for source_root in source_roots:
        if source_root.is_file() and source_root.suffix == ".py":
            yield source_root
            continue
        if source_root.is_dir():
            yield from source_root.rglob("*.py")


def check_refactor_quality_thresholds(
    *,
    source_roots: Sequence[Path],
    max_source_file_lines: int,
    max_function_lines: int,
) -> ThresholdResult:
    file_violations: list[FileSizeViolation] = []
    function_violations: list[FunctionSizeViolation] = []

    for path in sorted(iter_python_files(source_roots)):
        source = path.read_text(encoding="utf-8")
        line_count = len(source.splitlines())
        if line_count > max_source_file_lines:
            file_violations.append(
                FileSizeViolation(
                    path=path,
                    line_count=line_count,
                    max_lines=max_source_file_lines,
                )
            )
        function_violations.extend(
            find_function_size_violations(
                path=path,
                source=source,
                max_function_lines=max_function_lines,
            )
        )

    return ThresholdResult(
        file_size_violations=tuple(file_violations),
        function_size_violations=tuple(function_violations),
    )


def find_function_size_violations(
    *,
    path: Path,
    source: str,
    max_function_lines: int,
) -> list[FunctionSizeViolation]:
    tree = ast.parse(source, filename=str(path))
    violations: list[FunctionSizeViolation] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.end_lineno is None:
            continue
        line_count = node.end_lineno - node.lineno + 1
        if line_count > max_function_lines:
            violations.append(
                FunctionSizeViolation(
                    path=path,
                    line_number=node.lineno,
                    function_name=node.name,
                    line_count=line_count,
                    max_lines=max_function_lines,
                )
            )
    return violations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail when refactor quality thresholds regress above the governed baseline."
    )
    parser.add_argument(
        "source_roots",
        nargs="*",
        type=Path,
        default=[DEFAULT_SOURCE_ROOT],
        help="Python source roots or files to scan.",
    )
    parser.add_argument(
        "--max-source-file-lines",
        type=int,
        default=DEFAULT_MAX_SOURCE_FILE_LINES,
        help="Maximum allowed script-counted lines in any Python source file.",
    )
    parser.add_argument(
        "--max-function-lines",
        type=int,
        default=DEFAULT_MAX_FUNCTION_LINES,
        help="Maximum allowed AST span for any function or async function.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = check_refactor_quality_thresholds(
        source_roots=args.source_roots,
        max_source_file_lines=args.max_source_file_lines,
        max_function_lines=args.max_function_lines,
    )
    if result.passed:
        print(
            "Refactor quality thresholds passed: "
            f"max_source_file_lines={args.max_source_file_lines}, "
            f"max_function_lines={args.max_function_lines}"
        )
        return 0

    print("Refactor quality threshold violations:")
    for violation in result.file_size_violations:
        print(f"- {violation.format()}")
    for violation in result.function_size_violations:
        print(f"- {violation.format()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
