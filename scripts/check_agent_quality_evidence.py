"""Validate that agent-facing quality evidence tracks executable CI ratchets."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_refactor_quality_thresholds import (  # noqa: E402
    DEFAULT_MAX_FUNCTION_LINES,
    DEFAULT_MAX_SOURCE_FILE_LINES,
)

DEFAULT_REPO_ROOT = Path(".")
DEFAULT_SOURCE_ROOT = Path("src/app")

REQUIRED_DOCUMENTS = (
    Path("quality/ci_quality_gates.md"),
    Path("quality/quality_scorecard.md"),
    Path("quality/refactor_health_report.md"),
    Path("quality/baseline_report.md"),
    Path("wiki/Validation-and-CI.md"),
    Path("REPOSITORY-ENGINEERING-CONTEXT.md"),
)


@dataclass(frozen=True)
class SourceFileEvidence:
    path: Path
    line_count: int


@dataclass(frozen=True)
class FunctionEvidence:
    path: Path
    name: str
    line_number: int
    line_count: int


@dataclass(frozen=True)
class AgentQualityEvidence:
    tracked_source_files: int
    largest_source_file: SourceFileEvidence
    largest_function: FunctionEvidence | None


def iter_source_files(source_root: Path) -> list[Path]:
    if source_root.is_file() and source_root.suffix == ".py":
        return [source_root]
    return sorted(source_root.rglob("*.py"))


def collect_agent_quality_evidence(source_root: Path = DEFAULT_SOURCE_ROOT) -> AgentQualityEvidence:
    source_files = iter_source_files(source_root)
    if not source_files:
        raise ValueError(f"No Python source files found under {source_root}")

    largest_source_file = SourceFileEvidence(path=source_files[0], line_count=-1)
    largest_function: FunctionEvidence | None = None

    for source_file in source_files:
        source = source_file.read_text(encoding="utf-8")
        line_count = len(source.splitlines())
        if line_count > largest_source_file.line_count:
            largest_source_file = SourceFileEvidence(path=source_file, line_count=line_count)

        tree = ast.parse(source, filename=str(source_file))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.end_lineno is None:
                continue
            function_line_count = node.end_lineno - node.lineno + 1
            if largest_function is None or function_line_count > largest_function.line_count:
                largest_function = FunctionEvidence(
                    path=source_file,
                    name=node.name,
                    line_number=node.lineno,
                    line_count=function_line_count,
                )

    return AgentQualityEvidence(
        tracked_source_files=len(source_files),
        largest_source_file=largest_source_file,
        largest_function=largest_function,
    )


def validate_agent_quality_evidence(repo_root: Path = DEFAULT_REPO_ROOT) -> list[str]:
    findings: list[str] = []
    source_root = repo_root / DEFAULT_SOURCE_ROOT
    evidence = collect_agent_quality_evidence(source_root)

    findings.extend(_validate_ratchets(evidence))
    findings.extend(_validate_workflow_alignment(repo_root))
    findings.extend(_validate_makefile_alignment(repo_root))
    findings.extend(_validate_documentation_alignment(repo_root, evidence))

    return findings


def _validate_ratchets(evidence: AgentQualityEvidence) -> list[str]:
    findings: list[str] = []
    if evidence.largest_source_file.line_count != DEFAULT_MAX_SOURCE_FILE_LINES:
        findings.append(
            "Source-file threshold is not ratcheted to the current baseline: "
            f"largest={evidence.largest_source_file.path} "
            f"lines={evidence.largest_source_file.line_count}, "
            f"default_threshold={DEFAULT_MAX_SOURCE_FILE_LINES}."
        )

    if evidence.largest_function is None:
        findings.append(
            "No Python functions found under src/app; cannot validate function ratchet."
        )
    elif evidence.largest_function.line_count != DEFAULT_MAX_FUNCTION_LINES:
        findings.append(
            "Function threshold is not ratcheted to the current baseline: "
            f"largest={evidence.largest_function.path}:{evidence.largest_function.line_number} "
            f"{evidence.largest_function.name} lines={evidence.largest_function.line_count}, "
            f"default_threshold={DEFAULT_MAX_FUNCTION_LINES}."
        )

    return findings


def _validate_workflow_alignment(repo_root: Path) -> list[str]:
    workflow_path = repo_root / ".github/workflows/quality-baseline.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    required_fragments = (
        f"--max-source-file-lines {DEFAULT_MAX_SOURCE_FILE_LINES}",
        f"--max-function-lines {DEFAULT_MAX_FUNCTION_LINES}",
        "Enforce Agent Quality Evidence",
        "python scripts/check_agent_quality_evidence.py",
        "output/quality-baseline/agent-quality-evidence.txt",
    )
    return [
        f"{workflow_path} is missing required agent quality evidence fragment: {fragment}"
        for fragment in required_fragments
        if fragment not in workflow
    ]


def _validate_makefile_alignment(repo_root: Path) -> list[str]:
    makefile_path = repo_root / "Makefile"
    makefile = makefile_path.read_text(encoding="utf-8")
    required_fragments = (
        "agent-quality-evidence",
        "$(MAKE) agent-quality-evidence",
        "python scripts/check_agent_quality_evidence.py",
    )
    return [
        f"{makefile_path} is missing required agent quality evidence fragment: {fragment}"
        for fragment in required_fragments
        if fragment not in makefile
    ]


def _validate_documentation_alignment(
    repo_root: Path,
    evidence: AgentQualityEvidence,
) -> list[str]:
    findings: list[str] = []
    required_fragments = (
        "agent quality evidence",
        "scripts/check_agent_quality_evidence.py",
        f"{DEFAULT_MAX_SOURCE_FILE_LINES}/{DEFAULT_MAX_FUNCTION_LINES}",
        _document_path_fragment(repo_root, evidence.largest_source_file.path),
    )

    for relative_path in REQUIRED_DOCUMENTS:
        document_path = repo_root / relative_path
        if not document_path.is_file():
            findings.append(f"Missing required agent quality evidence document: {document_path}")
            continue
        document_text = document_path.read_text(encoding="utf-8").lower()
        for fragment in required_fragments:
            if fragment.lower() not in document_text:
                findings.append(
                    f"{document_path} is missing current agent quality evidence fragment: "
                    f"{fragment}"
                )

    return findings


def _document_path_fragment(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def main() -> int:
    findings = validate_agent_quality_evidence()
    if findings:
        print("Agent quality evidence check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    evidence = collect_agent_quality_evidence()
    largest_function = evidence.largest_function
    function_summary = (
        "none"
        if largest_function is None
        else (
            f"{largest_function.path}:{largest_function.line_number} "
            f"{largest_function.name}={largest_function.line_count}"
        )
    )
    print(
        "Agent quality evidence check passed: "
        f"tracked_source_files={evidence.tracked_source_files}, "
        f"thresholds={DEFAULT_MAX_SOURCE_FILE_LINES}/{DEFAULT_MAX_FUNCTION_LINES}, "
        f"largest_source_file={evidence.largest_source_file.path}:"
        f"{evidence.largest_source_file.line_count}, "
        f"largest_function={function_summary}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
