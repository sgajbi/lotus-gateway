import json
from pathlib import Path

import pytest

from scripts.check_duplicate_code_ratchet import (
    build_baseline,
    evaluate,
    load_report,
    load_status,
)


def _entry(
    first_file: str,
    second_file: str,
    *,
    fragment: str = "def shared():\n    return 1\n",
    lines: int = 15,
) -> dict[str, object]:
    return {
        "format": "python",
        "lines": lines,
        "fragment": fragment,
        "firstFile": {"name": first_file, "start": 10},
        "secondFile": {"name": second_file, "start": 20},
    }


def _write_report(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    report = {
        "statistics": {
            "total": {
                "clones": len(entries),
                "duplicatedLines": sum(int(entry["lines"]) for entry in entries),
                "percentage": 1.25,
            }
        },
        "duplicates": entries,
    }
    path = tmp_path / "jscpd-report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def _baseline_and_report(
    tmp_path: Path, entries: list[dict[str, object]]
) -> tuple[dict[str, object], object]:
    report = load_report(_write_report(tmp_path, entries))
    return build_baseline(report), report


def test_duplicate_ratchet_accepts_exact_reviewed_baseline(tmp_path: Path) -> None:
    entries = [_entry("src/app/a.py", "src/app/b.py")]
    baseline, report = _baseline_and_report(tmp_path, entries)

    result = evaluate(report, baseline, status=0)

    assert result.passed
    assert result.clone_count == 1
    assert result.unexpected_fingerprints == ()


def test_duplicate_ratchet_rejects_new_identity_at_same_count(tmp_path: Path) -> None:
    baseline, _ = _baseline_and_report(
        tmp_path / "baseline",
        [_entry("src/app/a.py", "src/app/b.py"), _entry("src/app/c.py", "src/app/d.py")],
    )
    current = load_report(
        _write_report(
            tmp_path / "current",
            [_entry("src/app/a.py", "src/app/b.py"), _entry("src/app/e.py", "src/app/f.py")],
        )
    )

    result = evaluate(current, baseline, status=0)

    assert not result.passed
    assert len(result.unexpected_fingerprints) == 1
    assert result.clone_count == result.baseline_clone_count


def test_duplicate_ratchet_rejects_count_and_line_regression(tmp_path: Path) -> None:
    baseline, _ = _baseline_and_report(
        tmp_path / "baseline", [_entry("src/app/a.py", "src/app/b.py", lines=15)]
    )
    current = load_report(
        _write_report(
            tmp_path / "current",
            [
                _entry("src/app/a.py", "src/app/b.py", lines=15),
                _entry("src/app/c.py", "src/app/d.py", lines=20),
            ],
        )
    )

    result = evaluate(current, baseline, status=0)

    assert not result.passed
    assert result.clone_count == 2
    assert result.report.duplicated_lines == 35


def test_duplicate_ratchet_rejects_detector_failure_even_with_old_report(tmp_path: Path) -> None:
    entries = [_entry("src/app/a.py", "src/app/b.py")]
    baseline, report = _baseline_and_report(tmp_path, entries)

    result = evaluate(report, baseline, status=1)

    assert not result.passed
    assert result.status == 1


def test_duplicate_report_rejects_out_of_scope_source(tmp_path: Path) -> None:
    report_path = _write_report(tmp_path, [_entry("src/app/a.py", "tests/b.py")])

    with pytest.raises(ValueError, match="out-of-scope source"):
        load_report(report_path)


def test_duplicate_report_rejects_inconsistent_clone_statistics(tmp_path: Path) -> None:
    report_path = _write_report(tmp_path, [_entry("src/app/a.py", "src/app/b.py")])
    document = json.loads(report_path.read_text(encoding="utf-8"))
    document["statistics"]["total"]["clones"] = 2
    report_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="clone count does not match"):
        load_report(report_path)


def test_duplicate_ratchet_rejects_detector_policy_drift(tmp_path: Path) -> None:
    entries = [_entry("src/app/a.py", "src/app/b.py")]
    baseline, report = _baseline_and_report(tmp_path, entries)
    baseline["detector"]["version"] = "unreviewed"

    with pytest.raises(ValueError, match="detector policy"):
        evaluate(report, baseline, status=0)


def test_duplicate_status_requires_one_numeric_marker(tmp_path: Path) -> None:
    status_path = tmp_path / "detector.txt"
    status_path.write_text("QUALITY_COMMAND_STATUS=0\nQUALITY_COMMAND_STATUS=1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="exactly one"):
        load_status(status_path)


def test_duplicate_baseline_rejects_ambiguous_fingerprints(tmp_path: Path) -> None:
    entries = [_entry("src/app/a.py", "src/app/b.py")]
    baseline, report = _baseline_and_report(tmp_path, entries)
    baseline["allowed_fingerprints"] = ["same", "same"]

    with pytest.raises(ValueError, match="must be unique"):
        evaluate(report, baseline, status=0)


def test_duplicate_fingerprint_normalizes_path_separators_and_source_order(
    tmp_path: Path,
) -> None:
    first = load_report(_write_report(tmp_path / "first", [_entry("src/app/a.py", "src/app/b.py")]))
    second = load_report(
        _write_report(
            tmp_path / "second",
            [
                _entry(
                    "src\\app\\b.py",
                    "src\\app\\a.py",
                    fragment="def differently_named():\n    return 2\n",
                )
            ],
        )
    )

    assert (
        build_baseline(first)["allowed_fingerprints"]
        == build_baseline(second)["allowed_fingerprints"]
    )
