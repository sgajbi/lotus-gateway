"""Validate the deterministic duplicate-code report against a reviewed baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

STATUS_PATTERN = re.compile(r"^QUALITY_COMMAND_STATUS=(\d+)$", re.MULTILINE)
SOURCE_PREFIX = "src/app/"
DETECTOR_POLICY = {
    "name": "jscpd",
    "version": "4.2.2",
    "format": "python",
    "pattern": "src/app/**/*.py",
    "min_lines": 15,
    "min_tokens": 50,
    "max_lines": 10000,
    "max_size": "1mb",
}


@dataclass(frozen=True)
class DuplicateFinding:
    fingerprint: str
    first_file: str
    second_file: str
    lines: int


@dataclass(frozen=True)
class DuplicateReport:
    findings: tuple[DuplicateFinding, ...]
    duplicated_lines: int
    duplicated_percentage: Decimal


@dataclass(frozen=True)
class RatchetResult:
    report: DuplicateReport
    baseline_clone_count: int
    baseline_duplicated_lines: int
    baseline_duplicated_percentage: Decimal
    unexpected_fingerprints: tuple[str, ...]
    status: int

    @property
    def clone_count(self) -> int:
        return len(self.report.findings)

    @property
    def passed(self) -> bool:
        return (
            self.status == 0
            and self.clone_count <= self.baseline_clone_count
            and self.report.duplicated_lines <= self.baseline_duplicated_lines
            and self.report.duplicated_percentage <= self.baseline_duplicated_percentage
            and not self.unexpected_fingerprints
        )


def _normalise_source(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("duplicate report source name must be a string")
    source = value.replace("\\", "/")
    if source.startswith("./"):
        source = source[2:]
    if not source.startswith(SOURCE_PREFIX):
        raise ValueError(f"duplicate report contains an out-of-scope source: {value!r}")
    return source


def _fingerprint(entry: dict[str, Any]) -> DuplicateFinding:
    first = entry.get("firstFile")
    second = entry.get("secondFile")
    fragment = entry.get("fragment")
    if not isinstance(first, dict) or not isinstance(second, dict) or not isinstance(fragment, str):
        raise ValueError("duplicate report entry is missing source or fragment data")
    first_file = _normalise_source(first.get("name"))
    second_file = _normalise_source(second.get("name"))
    lines = entry.get("lines")
    if isinstance(lines, bool) or not isinstance(lines, int) or lines <= 0:
        raise ValueError("duplicate report entry has an invalid line count")
    identity = {"format": entry.get("format"), "sources": sorted((first_file, second_file))}
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return DuplicateFinding(digest, first_file, second_file, lines)


def load_report(path: Path) -> DuplicateReport:
    document = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    duplicates = document.get("duplicates")
    total = document.get("statistics", {}).get("total")
    if not isinstance(duplicates, list) or not isinstance(total, dict):
        raise ValueError("duplicate report is missing duplicates or total statistics")
    findings = tuple(_fingerprint(entry) for entry in duplicates)
    if total.get("clones") != len(findings):
        raise ValueError("duplicate report clone count does not match its entries")
    duplicated_lines = total.get("duplicatedLines")
    percentage = total.get("percentage")
    if isinstance(duplicated_lines, bool) or not isinstance(duplicated_lines, int):
        raise ValueError("duplicate report has an invalid duplicated-line count")
    if isinstance(percentage, bool) or not isinstance(percentage, (int, Decimal)):
        raise ValueError("duplicate report has an invalid duplicated percentage")
    return DuplicateReport(findings, duplicated_lines, Decimal(str(percentage)))


def load_status(path: Path) -> int:
    matches = STATUS_PATTERN.findall(path.read_text(encoding="utf-8"))
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one QUALITY_COMMAND_STATUS marker, found {len(matches)}"
        )
    return int(matches[0])


def _decimal_metric(metrics: dict[str, Any], name: str) -> Decimal:
    value = metrics[name]["threshold"]
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise ValueError(f"invalid duplicate baseline threshold for {name}")
    return Decimal(str(value))


def _integer_metric(metrics: dict[str, Any], name: str) -> int:
    value = _decimal_metric(metrics, name)
    if value != value.to_integral_value():
        raise ValueError(f"invalid integer duplicate baseline threshold for {name}")
    return int(value)


def evaluate(report: DuplicateReport, baseline: dict[str, Any], status: int) -> RatchetResult:
    if baseline.get("schema_version") != 1:
        raise ValueError("duplicate baseline has an unsupported schema version")
    if baseline.get("detector") != DETECTOR_POLICY:
        raise ValueError("duplicate baseline detector policy does not match the pinned policy")
    metrics = baseline.get("metrics")
    allowed = baseline.get("allowed_fingerprints")
    if not isinstance(metrics, dict) or not isinstance(allowed, list):
        raise ValueError("duplicate baseline is missing metrics or allowed_fingerprints")
    if not all(isinstance(value, str) for value in allowed):
        raise ValueError("duplicate baseline fingerprints must be strings")
    if len(set(allowed)) != len(allowed):
        raise ValueError("duplicate baseline fingerprints must be unique")
    allowed_set = set(allowed)
    current_set = {finding.fingerprint for finding in report.findings}
    return RatchetResult(
        report=report,
        baseline_clone_count=_integer_metric(metrics, "clone_count"),
        baseline_duplicated_lines=_integer_metric(metrics, "duplicated_lines"),
        baseline_duplicated_percentage=_decimal_metric(metrics, "duplicated_percentage"),
        unexpected_fingerprints=tuple(sorted(current_set - allowed_set)),
        status=status,
    )


def build_baseline(report: DuplicateReport) -> dict[str, Any]:
    fingerprints = sorted({finding.fingerprint for finding in report.findings})
    return {
        "schema_version": 1,
        "detector": DETECTOR_POLICY.copy(),
        "metrics": {
            "clone_count": {"baseline": len(report.findings), "threshold": len(report.findings)},
            "duplicated_lines": {
                "baseline": report.duplicated_lines,
                "threshold": report.duplicated_lines,
            },
            "duplicated_percentage": {
                "baseline": report.duplicated_percentage,
                "threshold": report.duplicated_percentage,
            },
        },
        "allowed_fingerprints": fingerprints,
    }


def _encode_json(value: Any, *, indent: int = 0) -> str:
    """Serialize the baseline while preserving exact decimal JSON numbers."""

    if isinstance(value, bool) or value is None or isinstance(value, int):
        return json.dumps(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        if not value:
            return "[]"
        items = [_encode_json(item, indent=indent + 2) for item in value]
        prefix = " " * (indent + 2)
        return "[\n" + ",\n".join(prefix + item for item in items) + "\n" + " " * indent + "]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = [
            f"{json.dumps(str(key))}: {_encode_json(item, indent=indent + 2)}"
            for key, item in value.items()
        ]
        prefix = " " * (indent + 2)
        return "{\n" + ",\n".join(prefix + item for item in items) + "\n" + " " * indent + "}"
    raise TypeError(f"Unsupported baseline JSON value: {type(value).__name__}")


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(_encode_json(document) + "\n", encoding="utf-8")


def _print_result(result: RatchetResult) -> None:
    print(
        "Duplicate-code ratchet: "
        f"clones={result.clone_count}/{result.baseline_clone_count}, "
        f"duplicated_lines={result.report.duplicated_lines}/{result.baseline_duplicated_lines}, "
        "duplicated_percentage="
        f"{result.report.duplicated_percentage}/{result.baseline_duplicated_percentage}"
    )
    print(f"Unexpected stable duplicate findings: {len(result.unexpected_fingerprints)}")
    if result.status != 0:
        print(f"Duplicate detector failed with QUALITY_COMMAND_STATUS={result.status}.")
    for finding in sorted(
        (
            finding
            for finding in result.report.findings
            if finding.fingerprint in result.unexpected_fingerprints
        ),
        key=lambda finding: (finding.first_file, finding.second_file, finding.lines),
    ):
        print(
            "  unexpected source pair: "
            f"{finding.first_file} <-> {finding.second_file} ({finding.lines} lines)"
        )
    if not result.passed:
        print(
            "Duplicate-code ratchet failed: remove the new clone, correct the detector input, "
            "or make a reviewed baseline change after inspecting both source locations."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--artifact-log", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--initialize-baseline", action="store_true")
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()
    if args.initialize_baseline and args.update_baseline:
        parser.error("--initialize-baseline and --update-baseline are mutually exclusive")
    try:
        report = load_report(args.report)
        status = load_status(args.artifact_log)
        if args.initialize_baseline:
            _write_json(args.baseline, build_baseline(report))
            print(f"Initialized duplicate-code baseline: {args.baseline}")
            return 0
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"), parse_float=Decimal)
        result = evaluate(report, baseline, status)
        _print_result(result)
        if args.update_baseline:
            if not result.passed:
                print("Refusing to update duplicate-code baseline while the ratchet fails.")
                return 2
            _write_json(args.baseline, build_baseline(report))
            print(f"Updated duplicate-code baseline: {args.baseline}")
            return 0
        return 0 if result.passed else 1
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Duplicate-code ratchet input error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
