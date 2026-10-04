import json
from decimal import Decimal
from pathlib import Path

import pytest

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


def _duplicate_documents(tmp_path: Path, observed: float = 1.32) -> dict:
    baseline_path = tmp_path / "quality" / "duplicate_code_baseline.json"
    baseline_path.parent.mkdir()
    baseline = {
        "metrics": {
            "clone_count": {"baseline": 64, "threshold": 64},
            "duplicated_lines": {"baseline": 1281, "threshold": 1281},
            "duplicated_percentage": {"baseline": observed, "threshold": 1.35},
        }
    }
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    ci_document = tmp_path / DUPLICATE_CODE_DOCUMENTS[0]
    scorecard_document = tmp_path / DUPLICATE_CODE_DOCUMENTS[1]
    ci_document.write_text(
        "duplicate-code clone count must not exceed 64, duplicated lines must not exceed 1,281,\n"
        "and duplicated percentage must not exceed 1.35%",
        encoding="utf-8",
    )
    scorecard_document.write_text(
        "now measures 64 production clone findings, 1,281 duplicated lines, and "
        f"{observed:.2f}% duplicated lines against the unchanged 1.35% ceiling",
        encoding="utf-8",
    )

    return baseline


@pytest.mark.parametrize("observed", [1.32, 1.35])
def test_duplicate_documents_separate_observation_from_policy(
    tmp_path: Path, observed: float
) -> None:
    _duplicate_documents(tmp_path, observed)
    assert _validate_duplicate_code_documentation_alignment(tmp_path) == []


def test_duplicate_code_documentation_tracks_enforced_thresholds(tmp_path: Path) -> None:
    _duplicate_documents(tmp_path)
    ci_document = tmp_path / DUPLICATE_CODE_DOCUMENTS[0]
    scorecard_document = tmp_path / DUPLICATE_CODE_DOCUMENTS[1]

    ci_document.write_text("stale duplicate-code threshold", encoding="utf-8")

    findings = _validate_duplicate_code_documentation_alignment(tmp_path)

    assert findings == [
        f"{ci_document} is missing current duplicate-code threshold fragment: "
        "duplicate-code clone count must not exceed 64, duplicated lines must not exceed 1,281, "
        "and duplicated percentage must not exceed 1.35%"
    ]

    ci_document.write_text(
        "duplicate-code clone count must not exceed 64, duplicated lines must not exceed 1,281, "
        "and duplicated percentage must not exceed 1.35%",
        encoding="utf-8",
    )
    scorecard_document.write_text("stale duplicate-code threshold", encoding="utf-8")

    findings = _validate_duplicate_code_documentation_alignment(tmp_path)

    assert findings == [
        f"{scorecard_document} is missing current duplicate-code observation fragment: "
        "now measures 64 production clone findings, 1,281 duplicated lines, and "
        "1.32% duplicated lines",
        f"{scorecard_document} is missing current duplicate-code policy fragment: "
        "against the unchanged 1.35% ceiling",
    ]


@pytest.mark.parametrize("document", DUPLICATE_CODE_DOCUMENTS)
def test_duplicate_documents_reject_missing_document(tmp_path: Path, document: Path) -> None:
    _duplicate_documents(tmp_path)
    (tmp_path / document).unlink()
    assert f"Missing duplicate-code quality document: {tmp_path / document}" in (
        _validate_duplicate_code_documentation_alignment(tmp_path)
    )


@pytest.mark.parametrize("replacement", ["1.35%", "1.31%", "nan%", "unknown%"])
def test_duplicate_scorecard_rejects_false_or_malformed_observation(
    tmp_path: Path, replacement: str
) -> None:
    _duplicate_documents(tmp_path)
    path = tmp_path / DUPLICATE_CODE_DOCUMENTS[1]
    path.write_text(
        path.read_text(encoding="utf-8").replace("1.32%", replacement), encoding="utf-8"
    )
    assert any(
        "observation fragment" in item
        for item in (_validate_duplicate_code_documentation_alignment(tmp_path))
    )


@pytest.mark.parametrize("document", DUPLICATE_CODE_DOCUMENTS)
def test_duplicate_documents_reject_wrong_policy(tmp_path: Path, document: Path) -> None:
    _duplicate_documents(tmp_path)
    path = tmp_path / document
    path.write_text(path.read_text(encoding="utf-8").replace("1.35%", "1.32%"), encoding="utf-8")
    assert _validate_duplicate_code_documentation_alignment(tmp_path)


@pytest.mark.parametrize("name", ["clone_count", "duplicated_lines", "duplicated_percentage"])
@pytest.mark.parametrize("field", ["baseline", "threshold"])
@pytest.mark.parametrize("value", [None, "1.32", True, -1, float("nan"), float("inf")])
def test_duplicate_authority_rejects_invalid_required_metric(
    tmp_path: Path, name: str, field: str, value: object
) -> None:
    baseline = _duplicate_documents(tmp_path)
    baseline["metrics"][name][field] = value
    path = tmp_path / "quality/duplicate_code_baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")
    assert any(
        "Invalid duplicate-code measurement authority" in item
        for item in (_validate_duplicate_code_documentation_alignment(tmp_path))
    )


@pytest.mark.parametrize("field", ["baseline", "threshold"])
def test_duplicate_authority_rejects_absent_observation_or_policy(
    tmp_path: Path, field: str
) -> None:
    baseline = _duplicate_documents(tmp_path)
    del baseline["metrics"]["duplicated_percentage"][field]
    (tmp_path / "quality/duplicate_code_baseline.json").write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    assert _validate_duplicate_code_documentation_alignment(tmp_path)


@pytest.mark.parametrize("raw", ["{", "[]", '{"metrics": []}', '{"metrics": {}}'])
def test_duplicate_authority_rejects_malformed_structure(tmp_path: Path, raw: str) -> None:
    _duplicate_documents(tmp_path)
    (tmp_path / "quality/duplicate_code_baseline.json").write_text(raw, encoding="utf-8")
    assert _validate_duplicate_code_documentation_alignment(tmp_path)


def test_duplicate_authority_rejects_missing_file(tmp_path: Path) -> None:
    _duplicate_documents(tmp_path)
    path = tmp_path / "quality/duplicate_code_baseline.json"
    path.unlink()
    assert _validate_duplicate_code_documentation_alignment(tmp_path) == [
        f"Missing duplicate-code baseline: {path}"
    ]


@pytest.mark.parametrize("name", ["clone_count", "duplicated_lines"])
@pytest.mark.parametrize("field", ["baseline", "threshold"])
def test_duplicate_authority_rejects_fractional_counts(
    tmp_path: Path, name: str, field: str
) -> None:
    baseline = _duplicate_documents(tmp_path)
    baseline["metrics"][name][field] = 1.5
    (tmp_path / "quality/duplicate_code_baseline.json").write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    assert _validate_duplicate_code_documentation_alignment(tmp_path)


def test_duplicate_authority_rejects_observed_above_ceiling(tmp_path: Path) -> None:
    _duplicate_documents(tmp_path, observed=1.36)
    assert any(
        "observation exceeds policy" in item
        for item in (_validate_duplicate_code_documentation_alignment(tmp_path))
    )


def test_existing_native_ratchet_rejects_actual_report_above_ceiling() -> None:
    from scripts.check_duplicate_code_ratchet import DETECTOR_POLICY, DuplicateReport, evaluate

    baseline = {
        "schema_version": 1,
        "detector": DETECTOR_POLICY,
        "allowed_fingerprints": [],
        "metrics": {
            "clone_count": {"baseline": 0, "threshold": 0},
            "duplicated_lines": {"baseline": 0, "threshold": 0},
            "duplicated_percentage": {"baseline": Decimal("1.32"), "threshold": Decimal("1.35")},
        },
    }
    report = DuplicateReport((), 0, Decimal("1.36"))
    assert not evaluate(report, baseline, 0).passed
