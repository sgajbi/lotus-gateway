import json
import sys
import tokenize
from pathlib import Path

import pytest

from scripts.check_duplicate_code_ratchet import (
    FSTRING_END_TOKEN,
    FSTRING_START_TOKEN,
    SourceLocation,
    _normalise_fragment,
    _normalise_token_stream,
    _source_fragment,
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


def _write_context_sources(root: Path, *, second_function: str, prefix: str = "") -> None:
    source = f"{prefix}def first():\n    return 1\n\ndef {second_function}():\n    return 1\n"
    for name in ("a.py", "b.py"):
        path = root / "src" / "app" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")


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
    assert not result.all_fingerprints_changed


def test_duplicate_ratchet_identifies_a_complete_identity_change(tmp_path: Path) -> None:
    baseline, _ = _baseline_and_report(
        tmp_path / "baseline",
        [_entry("src/app/a.py", "src/app/b.py"), _entry("src/app/c.py", "src/app/d.py")],
    )
    current = load_report(
        _write_report(
            tmp_path / "current",
            [
                _entry("src/app/e.py", "src/app/f.py"),
                _entry("src/app/g.py", "src/app/h.py"),
            ],
        )
    )

    result = evaluate(current, baseline, status=0)

    assert result.all_fingerprints_changed


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


def test_duplicate_fingerprint_uses_canonical_source_side_when_report_orientation_changes(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    for name, result in (("a.py", 1), ("b.py", 2)):
        path = source_root / "src" / "app" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"def shared():\n    return {result}\n", encoding="utf-8")

    forward = load_report(
        _write_report(
            tmp_path / "forward",
            [
                _entry(
                    "src/app/a.py",
                    "src/app/b.py",
                    fragment="def shared():\n    return 1\n",
                    lines=2,
                    first_start=1,
                    second_start=1,
                )
            ],
        ),
        source_root=source_root,
    )
    reversed_report = load_report(
        _write_report(
            tmp_path / "reversed",
            [
                _entry(
                    "src/app/b.py",
                    "src/app/a.py",
                    fragment="def shared():\n    return 2\n",
                    lines=2,
                    first_start=1,
                    second_start=1,
                )
            ],
        ),
        source_root=source_root,
    )

    assert (
        build_baseline(forward)["allowed_fingerprints"]
        == build_baseline(reversed_report)["allowed_fingerprints"]
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


def test_duplicate_fingerprint_rejects_same_fragment_replacement_with_context(
    tmp_path: Path,
) -> None:
    entries = [
        _entry(
            "src/app/a.py",
            "src/app/b.py",
            fragment="return 1\n",
            lines=1,
            first_start=2,
            second_start=2,
        ),
        _entry(
            "src/app/a.py",
            "src/app/b.py",
            fragment="return 1\n",
            lines=1,
            first_start=5,
            second_start=5,
        ),
    ]
    baseline_root = tmp_path / "baseline-source"
    current_root = tmp_path / "current-source"
    _write_context_sources(baseline_root, second_function="second")
    _write_context_sources(current_root, second_function="replacement")

    baseline = load_report(
        _write_report(tmp_path / "baseline-report", entries), source_root=baseline_root
    )
    current = load_report(
        _write_report(tmp_path / "current-report", entries), source_root=current_root
    )
    result = evaluate(current, build_baseline(baseline), status=0)

    assert not result.passed
    assert len(result.unexpected_fingerprints) == 1
    assert len(result.stale_fingerprints) == 1


def test_duplicate_fingerprint_context_survives_unrelated_line_shift(tmp_path: Path) -> None:
    entries = [
        _entry(
            "src/app/a.py",
            "src/app/b.py",
            fragment="return 1\n",
            lines=1,
            first_start=2,
            second_start=2,
        ),
        _entry(
            "src/app/a.py",
            "src/app/b.py",
            fragment="return 1\n",
            lines=1,
            first_start=5,
            second_start=5,
        ),
    ]
    baseline_root = tmp_path / "baseline-source"
    moved_root = tmp_path / "moved-source"
    _write_context_sources(baseline_root, second_function="second")
    _write_context_sources(
        moved_root,
        second_function="second",
        prefix="from __future__ import annotations\n",
    )
    baseline = load_report(
        _write_report(tmp_path / "baseline-report", entries), source_root=baseline_root
    )
    moved_entries = [
        _entry(
            "src/app/a.py",
            "src/app/b.py",
            fragment="return 1\n",
            lines=1,
            first_start=3,
            second_start=3,
        ),
        _entry(
            "src/app/a.py",
            "src/app/b.py",
            fragment="return 1\n",
            lines=1,
            first_start=6,
            second_start=6,
        ),
    ]
    moved = load_report(
        _write_report(tmp_path / "moved-report", moved_entries), source_root=moved_root
    )

    assert (
        build_baseline(baseline)["allowed_fingerprints"]
        == build_baseline(moved)["allowed_fingerprints"]
    )


def test_duplicate_fingerprint_context_survives_unrelated_scope_body_edit(
    tmp_path: Path,
) -> None:
    baseline_root = tmp_path / "baseline-source"
    moved_root = tmp_path / "moved-source"
    baseline_source = "def shared():\n    before = 0\n    return 1\n    after = 3\n"
    moved_source = "def shared():\n    before = 0\n    return 1\n    after = 3\n    unrelated = 2\n"
    for root, source in ((baseline_root, baseline_source), (moved_root, moved_source)):
        for name in ("a.py", "b.py"):
            path = root / "src" / "app" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

    entry = _entry(
        "src/app/a.py",
        "src/app/b.py",
        fragment="return 1\n",
        lines=1,
        first_start=3,
        second_start=3,
    )
    baseline = load_report(
        _write_report(tmp_path / "baseline-report", [entry]), source_root=baseline_root
    )
    moved = load_report(
        _write_report(
            tmp_path / "moved-report",
            [
                _entry(
                    "src/app/a.py",
                    "src/app/b.py",
                    fragment="return 1\n",
                    lines=1,
                    first_start=3,
                    second_start=3,
                )
            ],
        ),
        source_root=moved_root,
    )

    assert (
        build_baseline(baseline)["allowed_fingerprints"]
        == build_baseline(moved)["allowed_fingerprints"]
    )


def test_duplicate_fingerprint_allows_same_scope_relocation(tmp_path: Path) -> None:
    baseline_root = tmp_path / "baseline-source"
    moved_root = tmp_path / "moved-source"
    baseline_source = "def shared():\n    if enabled:\n        return 1\n    return 1\n"
    moved_source = "def shared():\n    if enabled:\n        return 1\n    return 2\n    return 1\n"
    for root, source in ((baseline_root, baseline_source), (moved_root, moved_source)):
        for name in ("a.py", "b.py"):
            path = root / "src" / "app" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

    baseline_entries = [
        _entry(
            "src/app/a.py",
            "src/app/b.py",
            fragment="return 1\n",
            lines=1,
            first_start=3,
            second_start=4,
        ),
    ]
    moved_entries = [
        _entry(
            "src/app/a.py",
            "src/app/b.py",
            fragment="return 1\n",
            lines=1,
            first_start=3,
            second_start=5,
        ),
    ]
    baseline = load_report(
        _write_report(tmp_path / "baseline-report", baseline_entries), source_root=baseline_root
    )
    moved = load_report(
        _write_report(tmp_path / "moved-report", moved_entries), source_root=moved_root
    )

    result = evaluate(moved, build_baseline(baseline), status=0)

    # Source-pair, fragment, and enclosing scope are stable identity evidence. A
    # same-scope relocation is intentionally not treated as a new clone because
    # adjacent source edits cannot be distinguished from that relocation without
    # making unchanged fingerprints fragile.
    assert result.passed
    assert result.unexpected_fingerprints == ()
    assert result.stale_fingerprints == ()


def test_duplicate_fingerprint_survives_adjacent_source_edit(tmp_path: Path) -> None:
    baseline_root = tmp_path / "baseline-source"
    moved_root = tmp_path / "moved-source"
    baseline_source = "def shared():\n    before = 0\n    return 1\n    after = 3\n"
    moved_source = "def shared():\n    before = 0\n    added = 2\n    return 1\n    after = 3\n"
    for root, source in ((baseline_root, baseline_source), (moved_root, moved_source)):
        for name in ("a.py", "b.py"):
            path = root / "src" / "app" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")

    entry = _entry(
        "src/app/a.py",
        "src/app/b.py",
        fragment="return 1\n",
        lines=1,
        first_start=3,
        second_start=3,
    )
    baseline = load_report(
        _write_report(tmp_path / "baseline-report", [entry]), source_root=baseline_root
    )
    moved = load_report(
        _write_report(
            tmp_path / "moved-report",
            [
                _entry(
                    "src/app/a.py",
                    "src/app/b.py",
                    fragment="return 1\n",
                    lines=1,
                    first_start=4,
                    second_start=4,
                )
            ],
        ),
        source_root=moved_root,
    )

    result = evaluate(moved, build_baseline(baseline), status=0)

    assert result.passed
    assert result.unexpected_fingerprints == ()
    assert result.stale_fingerprints == ()


def test_duplicate_fingerprint_preserves_python_literal_whitespace(tmp_path: Path) -> None:
    baseline, _ = _baseline_and_report(
        tmp_path / "baseline",
        [_entry("src/app/a.py", "src/app/b.py", fragment='message = "client ready"\n')],
    )
    current = load_report(
        _write_report(
            tmp_path / "current",
            [_entry("src/app/a.py", "src/app/b.py", fragment='message = "client  ready"\n')],
        )
    )

    result = evaluate(current, baseline, status=0)

    assert not result.passed
    assert len(result.unexpected_fingerprints) == 1
    assert len(result.stale_fingerprints) == 1


def test_duplicate_fingerprint_normalizes_comment_quotes_and_layout() -> None:
    assert _normalise_fragment("value = foo( a ) # don't duplicate\n") == _normalise_fragment(
        "value  =  foo(  a  ) # don't duplicate\n"
    )


def test_duplicate_fingerprint_normalizes_fstrings_across_tokenizer_shapes() -> None:
    text = 'message = f"client  {name}"\n'
    spaced_expression = 'message = f"client  { name }"\n'
    legacy_tokens = [
        tokenize.TokenInfo(tokenize.NAME, "message", (1, 0), (1, 7), text),
        tokenize.TokenInfo(tokenize.OP, "=", (1, 8), (1, 9), text),
        tokenize.TokenInfo(
            tokenize.STRING,
            'f"client  {name}"',
            (1, 10),
            (1, len(text) - 1),
            text,
        ),
        tokenize.TokenInfo(tokenize.NEWLINE, "\n", (1, len(text) - 1), (2, 0), text),
        tokenize.TokenInfo(tokenize.ENDMARKER, "", (2, 0), (2, 0), ""),
    ]
    modern_tokens = [
        tokenize.TokenInfo(tokenize.NAME, "message", (1, 0), (1, 7), text),
        tokenize.TokenInfo(tokenize.OP, "=", (1, 8), (1, 9), text),
        tokenize.TokenInfo(FSTRING_START_TOKEN, 'f"', (1, 10), (1, 12), text),
        tokenize.TokenInfo(tokenize.NAME, "client  ", (1, 12), (1, 20), text),
        tokenize.TokenInfo(tokenize.OP, "{", (1, 20), (1, 21), text),
        tokenize.TokenInfo(tokenize.NAME, "name", (1, 21), (1, 25), text),
        tokenize.TokenInfo(tokenize.OP, "}", (1, 25), (1, 26), text),
        tokenize.TokenInfo(FSTRING_END_TOKEN, '"', (1, 26), (1, 27), text),
        tokenize.TokenInfo(tokenize.NEWLINE, "\n", (1, 27), (2, 0), text),
        tokenize.TokenInfo(tokenize.ENDMARKER, "", (2, 0), (2, 0), ""),
    ]

    assert _normalise_token_stream(text, legacy_tokens) == _normalise_token_stream(
        text, modern_tokens
    )
    assert _normalise_fragment(text) == _normalise_token_stream(text, legacy_tokens)
    assert _normalise_fragment(text) == _normalise_fragment(spaced_expression)


def test_duplicate_source_fragment_honours_reported_columns(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_path = source_root / "src" / "app" / "a.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("prefix = 1; shared()\ntrailer()\n", encoding="utf-8")
    before_edit = _source_fragment(
        source_root,
        SourceLocation("src/app/a.py", 1, start_column=12, end=1, end_column=20),
        lines=1,
    )

    source_path.write_text("prefix = 999999; shared()\ntrailer()\n", encoding="utf-8")
    after_edit = _source_fragment(
        source_root,
        SourceLocation("src/app/a.py", 1, start_column=17, end=1, end_column=25),
        lines=1,
    )

    assert before_edit == "shared()"
    assert after_edit == before_edit


def test_duplicate_fingerprint_fallback_handles_incomplete_fragment() -> None:
    fragment = 'items = [\n    "a",\n'
    assert _normalise_fragment(fragment) == 'items = [ "a" ,'
    assert _normalise_fragment("value+1,\n]\n") == _normalise_fragment("value + 1,\n]\n")
    assert _normalise_fragment("items = [\nobj.attr,\n") == _normalise_fragment(
        "items = [\nobj . attr,\n"
    )
    assert _normalise_fragment('items = [\nx = f"{foo(a)}",\n') == _normalise_fragment(
        'items = [\nx = f"{ foo( a ) }",\n'
    )
    indented_slice = (
        "\n        )\n\n    def _headers(\n"
        "        self,\n        correlation_id: str,\n"
        "    ) -> dict[str, str]:\n        raise NotImplementedError\n"
    )
    assert _normalise_fragment(indented_slice) == (
        ") def _headers ( self , correlation_id : str , ) -> dict [ str , str ] : "
        "raise NotImplementedError"
    )
    assert _normalise_fragment('x = f"{alpha\ny = 1\n') != _normalise_fragment(
        'x = f"{beta\nz = 9\n'
    )
    unterminated = 'x = "abc\ny = 1\n'
    assert _normalise_fragment(unterminated) == 'x = "abc\ny = 1'


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
