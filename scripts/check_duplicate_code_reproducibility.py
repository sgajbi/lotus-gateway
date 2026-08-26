"""Fail when repeated duplicate-code detector runs select different candidates."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.check_duplicate_code_ratchet import (
    DuplicateIdentity,
    DuplicateReport,
    load_report,
    load_status,
)


def _candidate_identities(report: DuplicateReport) -> set[DuplicateIdentity]:
    return {finding.candidate_identity for finding in report.findings}


def compare_reports(
    first: DuplicateReport, second: DuplicateReport
) -> tuple[set[DuplicateIdentity], set[DuplicateIdentity]]:
    """Return normalized candidates unique to each repeated detector report."""

    first_candidates = _candidate_identities(first)
    second_candidates = _candidate_identities(second)
    return first_candidates - second_candidates, second_candidates - first_candidates


def _metrics(report: DuplicateReport) -> tuple[int, int, str]:
    return (
        len(report.findings),
        report.duplicated_lines,
        str(report.duplicated_percentage),
    )


def _candidate_label(candidate: DuplicateIdentity) -> str:
    first_source, first_line, *_ = candidate.locations[0]
    second_source, second_line, *_ = candidate.locations[1]
    return f"{first_source}:{first_line} <-> {second_source}:{second_line}"


def _print_candidates(label: str, candidates: set[DuplicateIdentity]) -> None:
    for candidate in sorted(candidates, key=lambda item: item.locations)[:5]:
        print(f"  {label}: {_candidate_label(candidate)}")
    if len(candidates) > 5:
        print(f"  {label}: ... {len(candidates) - 5} more")


def _print_metric_drift(first: DuplicateReport, second: DuplicateReport) -> None:
    first_metrics = _metrics(first)
    second_metrics = _metrics(second)
    if first_metrics != second_metrics:
        print(
            "Duplicate detector metrics drifted between repeated runs: "
            f"first={first_metrics}, second={second_metrics}"
        )


def check_reproducibility(
    *,
    first_report: Path,
    second_report: Path,
    first_artifact_log: Path,
    second_artifact_log: Path,
    source_root: Path | None = None,
) -> int:
    first_status = load_status(first_artifact_log)
    second_status = load_status(second_artifact_log)
    if first_status != 0 or second_status != 0:
        print(
            "Duplicate detector reproducibility failed because a detector invocation failed: "
            f"first_status={first_status}, second_status={second_status}"
        )
        return 1

    first = load_report(first_report, source_root=source_root)
    second = load_report(second_report, source_root=source_root)
    first_only, second_only = compare_reports(first, second)
    _print_metric_drift(first, second)
    if first_only or second_only or _metrics(first) != _metrics(second):
        print(
            "Duplicate detector reproducibility failed: repeated runs selected different "
            "candidate sets."
        )
        print(f"  first-only candidates: {len(first_only)}")
        print(f"  second-only candidates: {len(second_only)}")
        _print_candidates("first-only", first_only)
        _print_candidates("second-only", second_only)
        return 1

    print(
        "Duplicate detector reproducibility passed: "
        f"candidates={len(first.findings)}, metrics={_metrics(first)}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-report", type=Path, required=True)
    parser.add_argument("--second-report", type=Path, required=True)
    parser.add_argument("--first-artifact-log", type=Path, required=True)
    parser.add_argument("--second-artifact-log", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Repository root used to calculate stable source-context fingerprints.",
    )
    args = parser.parse_args()
    try:
        return check_reproducibility(
            first_report=args.first_report,
            second_report=args.second_report,
            first_artifact_log=args.first_artifact_log,
            second_artifact_log=args.second_artifact_log,
            source_root=args.source_root,
        )
    except (OSError, TypeError, ValueError):
        print("Duplicate detector reproducibility input error.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
