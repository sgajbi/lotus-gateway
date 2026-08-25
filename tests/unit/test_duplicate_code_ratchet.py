import json
import sys
from pathlib import Path

import pytest

from scripts.check_duplicate_code_ratchet import (
    build_baseline,
    evaluate,
    load_report,
    load_status,
    main,
)


def _entry(
    first_file: str,
    second_file: str,
    *,
    fragment: str = "def shared():\n    return 1\n",
    lines: int = 15,
    first_start: int = 10,
    second_start: int = 20,
) -> dict[str, object]:
    return {
        "format": "python",
        "lines": lines,
        "fragment": fragment,
        "firstFile": {"name": first_file, "start": first_start},
        "secondFile": {"name": second_file, "start": second_start},
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
    assert result.stale_fingerprints == ()


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


def test_duplicate_ratchet_rejects_stale_baseline_fingerprint(tmp_path: Path) -> None:
    baseline, report = _baseline_and_report(tmp_path, [_entry("src/app/a.py", "src/app/b.py")])
    baseline["allowed_fingerprints"].append("removed-clone")

    result = evaluate(report, baseline, status=0)

    assert not result.passed
    assert result.can_update_baseline
    assert result.stale_fingerprints == ("removed-clone",)


def test_duplicate_baseline_update_banks_removed_fingerprint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline_report = _write_report(
        tmp_path / "baseline-report",
        [_entry("src/app/a.py", "src/app/b.py"), _entry("src/app/c.py", "src/app/d.py")],
    )
    current_report = _write_report(
        tmp_path / "current-report", [_entry("src/app/a.py", "src/app/b.py")]
    )
    status_path = tmp_path / "detector.txt"
    status_path.write_text("QUALITY_COMMAND_STATUS=0\n", encoding="utf-8")
    baseline_path = tmp_path / "baseline.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_duplicate_code_ratchet.py",
            "--report",
            str(baseline_report),
            "--artifact-log",
            str(status_path),
            "--baseline",
            str(baseline_path),
            "--initialize-baseline",
        ],
    )
    assert main() == 0

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_duplicate_code_ratchet.py",
            "--report",
            str(current_report),
            "--artifact-log",
            str(status_path),
            "--baseline",
            str(baseline_path),
            "--update-baseline",
        ],
    )
    assert main() == 0
    updated = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert len(updated["allowed_fingerprints"]) == 1


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


def test_duplicate_report_rejects_path_traversal_source(tmp_path: Path) -> None:
    report_path = _write_report(tmp_path, [_entry("src/app/../tests.py", "src/app/b.py")])

    with pytest.raises(ValueError, match="out-of-scope source"):
        load_report(report_path)


def test_duplicate_report_rejects_non_object_json(tmp_path: Path) -> None:
    path = tmp_path / "jscpd-report.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load_report(path)


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
                    fragment="def shared():\r\n        return 1\r\n",
                    first_start=20,
                    second_start=10,
                )
            ],
        )
    )

    assert (
        build_baseline(first)["allowed_fingerprints"]
        == build_baseline(second)["allowed_fingerprints"]
    )


def test_duplicate_fingerprint_distinguishes_multiple_clones_between_same_files(
    tmp_path: Path,
) -> None:
    report = load_report(
        _write_report(
            tmp_path,
            [
                _entry("src/app/a.py", "src/app/b.py", fragment="def first():\n    return 1\n"),
                _entry(
                    "src/app/a.py",
                    "src/app/b.py",
                    fragment="def second():\n    return 2\n",
                ),
            ],
        )
    )

    assert len({finding.fingerprint for finding in report.findings}) == 2
    assert len(build_baseline(report)["allowed_fingerprints"]) == 2


def test_duplicate_fingerprint_distinguishes_identical_fragments_at_different_locations(
    tmp_path: Path,
) -> None:
    report = load_report(
        _write_report(
            tmp_path,
            [
                _entry("src/app/a.py", "src/app/b.py"),
                _entry(
                    "src/app/a.py",
                    "src/app/b.py",
                    first_start=30,
                    second_start=40,
                ),
            ],
        )
    )

    assert len({finding.fingerprint for finding in report.findings}) == 2
    assert len(build_baseline(report)["allowed_fingerprints"]) == 2


def test_duplicate_fingerprint_uses_stable_occurrence_order_not_absolute_lines(
    tmp_path: Path,
) -> None:
    first = load_report(
        _write_report(
            tmp_path / "first",
            [
                _entry("src/app/a.py", "src/app/b.py"),
                _entry("src/app/a.py", "src/app/b.py", first_start=30, second_start=40),
            ],
        )
    )
    moved = load_report(
        _write_report(
            tmp_path / "moved",
            [
                _entry("src/app/a.py", "src/app/b.py", first_start=100, second_start=200),
                _entry("src/app/a.py", "src/app/b.py", first_start=300, second_start=400),
            ],
        )
    )

    assert (
        build_baseline(first)["allowed_fingerprints"]
        == build_baseline(moved)["allowed_fingerprints"]
    )


def test_duplicate_report_rejects_empty_fragment(tmp_path: Path) -> None:
    report_path = _write_report(tmp_path, [_entry("src/app/a.py", "src/app/b.py", fragment="\n")])

    with pytest.raises(ValueError, match="empty fragment"):
        load_report(report_path)


def test_duplicate_report_rejects_invalid_source_start(tmp_path: Path) -> None:
    report_path = _write_report(tmp_path, [_entry("src/app/a.py", "src/app/b.py")])
    document = json.loads(report_path.read_text(encoding="utf-8"))
    document["duplicates"][0]["firstFile"]["start"] = 0
    report_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid start line"):
        load_report(report_path)
