from pathlib import Path

from scripts.check_agent_quality_evidence import (
    FunctionEvidence,
    SourceFileEvidence,
    collect_agent_quality_evidence,
    validate_agent_quality_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_collect_agent_quality_evidence_reports_largest_file_and_function(tmp_path: Path) -> None:
    source_root = tmp_path / "src" / "app"
    source_root.mkdir(parents=True)
    (source_root / "small.py").write_text("def small():\n    return 1\n", encoding="utf-8")
    (source_root / "large.py").write_text(
        "\n".join(
            [
                "def largest():",
                "    value = 1",
                "    value += 1",
                "    return value",
                "CONSTANT = 1",
            ]
        ),
        encoding="utf-8",
    )

    evidence = collect_agent_quality_evidence(source_root)

    assert evidence.tracked_source_files == 2
    assert evidence.largest_source_file == SourceFileEvidence(
        path=source_root / "large.py",
        line_count=5,
    )
    assert evidence.largest_function == FunctionEvidence(
        path=source_root / "large.py",
        name="largest",
        line_number=1,
        line_count=4,
    )


def test_validate_agent_quality_evidence_accepts_current_repository_truth() -> None:
    assert validate_agent_quality_evidence(REPO_ROOT) == []


def test_validate_agent_quality_evidence_reports_missing_documentation_truth(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_root = tmp_path / "src" / "app"
    source_root.mkdir(parents=True)
    source_file = source_root / "service.py"
    source_file.write_text("def largest():\n    return 1\n", encoding="utf-8")

    workflow_path = tmp_path / ".github" / "workflows" / "quality-baseline.yml"
    workflow_path.parent.mkdir(parents=True)
    workflow_path.write_text(
        "--max-source-file-lines 2\n"
        "--max-function-lines 2\n"
        "Enforce Agent Quality Evidence\n"
        "python scripts/check_agent_quality_evidence.py\n"
        "output/quality-baseline/agent-quality-evidence.txt\n",
        encoding="utf-8",
    )
    makefile_path = tmp_path / "Makefile"
    makefile_path.write_text(
        "lint:\n\t$(MAKE) agent-quality-evidence\n\n"
        "agent-quality-evidence:\n\tpython scripts/check_agent_quality_evidence.py\n",
        encoding="utf-8",
    )

    from scripts import check_agent_quality_evidence as module

    monkeypatch.setattr(module, "DEFAULT_MAX_SOURCE_FILE_LINES", 2)
    monkeypatch.setattr(module, "DEFAULT_MAX_FUNCTION_LINES", 2)
    monkeypatch.setattr(module, "REQUIRED_DOCUMENTS", (Path("quality/ci_quality_gates.md"),))
    document_path = tmp_path / "quality" / "ci_quality_gates.md"
    document_path.parent.mkdir()
    document_path.write_text("stale evidence\n", encoding="utf-8")

    findings = validate_agent_quality_evidence(tmp_path)

    missing_fragment_prefix = (
        f"{document_path} is missing current agent quality evidence fragment: "
    )
    assert findings == [
        f"{missing_fragment_prefix}agent quality evidence",
        f"{missing_fragment_prefix}scripts/check_agent_quality_evidence.py",
        f"{missing_fragment_prefix}2/2",
        f"{missing_fragment_prefix}src/app/service.py",
    ]
