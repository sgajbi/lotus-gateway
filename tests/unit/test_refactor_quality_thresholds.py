from pathlib import Path

from scripts.check_refactor_quality_thresholds import (
    DEFAULT_MAX_SOURCE_FILE_LINES,
    check_refactor_quality_thresholds,
    find_function_size_violations,
)


def test_refactor_quality_thresholds_pass_for_small_source_file(tmp_path: Path) -> None:
    source_file = tmp_path / "small.py"
    source_file.write_text("def ok():\n    return 1\n", encoding="utf-8")

    result = check_refactor_quality_thresholds(
        source_roots=[tmp_path],
        max_source_file_lines=10,
        max_function_lines=3,
    )

    assert result.passed
    assert result.file_size_violations == ()
    assert result.function_size_violations == ()


def test_default_source_file_threshold_tracks_remediated_gateway_baseline() -> None:
    assert DEFAULT_MAX_SOURCE_FILE_LINES == 404


def test_refactor_quality_thresholds_reports_oversized_files(tmp_path: Path) -> None:
    source_file = tmp_path / "large.py"
    source_file.write_text("\n".join(["VALUE = 1"] * 4), encoding="utf-8")

    result = check_refactor_quality_thresholds(
        source_roots=[tmp_path],
        max_source_file_lines=3,
        max_function_lines=10,
    )

    assert not result.passed
    assert len(result.file_size_violations) == 1
    assert result.file_size_violations[0].path == source_file
    assert result.file_size_violations[0].line_count == 4


def test_refactor_quality_thresholds_reports_oversized_functions() -> None:
    violations = find_function_size_violations(
        path=Path("example.py"),
        source="\n".join(
            [
                "async def too_large():",
                "    value = 1",
                "    value += 1",
                "    return value",
            ]
        ),
        max_function_lines=3,
    )

    assert len(violations) == 1
    assert violations[0].function_name == "too_large"
    assert violations[0].line_number == 1
    assert violations[0].line_count == 4
