import json
from pathlib import Path

from scripts.check_agent_quality_evidence import (
    DUPLICATE_CODE_DOCUMENTS,
    FunctionEvidence,
    SourceFileEvidence,
    _validate_duplicate_code_documentation_alignment,
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
    monkeypatch.setattr(module, "DUPLICATE_CODE_DOCUMENTS", ())
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


def test_duplicate_code_documentation_tracks_enforced_thresholds(tmp_path: Path) -> None:
    baseline_path = tmp_path / "quality" / "duplicate_code_baseline.json"
    baseline_path.parent.mkdir()
    baseline_path.write_text(
        json.dumps(
            {
                "metrics": {
                    "clone_count": {"threshold": 86},
                    "duplicated_lines": {"threshold": 1720},
                    "duplicated_percentage": {"threshold": 1.98},
                }
            }
        ),
        encoding="utf-8",
    )
    ci_document = tmp_path / DUPLICATE_CODE_DOCUMENTS[0]
    scorecard_document = tmp_path / DUPLICATE_CODE_DOCUMENTS[1]
    ci_document.write_text(
        "duplicate-code clone count must not exceed 86, duplicated lines must not exceed 1,720, "
        "and duplicated percentage must not exceed 1.98%",
        encoding="utf-8",
    )
    scorecard_document.write_text(
        "now measures 86 production clone findings, 1,720 duplicated lines, and "
        "1.98% duplicated lines",
        encoding="utf-8",
    )

    assert _validate_duplicate_code_documentation_alignment(tmp_path) == []

    ci_document.write_text("stale duplicate-code threshold", encoding="utf-8")

    findings = _validate_duplicate_code_documentation_alignment(tmp_path)

    assert findings == [
        f"{ci_document} is missing current duplicate-code threshold fragment: "
        "duplicate-code clone count must not exceed 86, duplicated lines must not exceed 1,720, "
        "and duplicated percentage must not exceed 1.98%"
    ]

    ci_document.write_text(
        "duplicate-code clone count must not exceed 86, duplicated lines must not exceed 1,720, "
        "and duplicated percentage must not exceed 1.98%",
        encoding="utf-8",
    )
    scorecard_document.write_text("stale duplicate-code threshold", encoding="utf-8")

    findings = _validate_duplicate_code_documentation_alignment(tmp_path)

    assert findings == [
        f"{scorecard_document} is missing current duplicate-code threshold fragment: "
        "now measures 86 production clone findings, 1,720 duplicated lines, and "
        "1.98% duplicated lines"
    ]
