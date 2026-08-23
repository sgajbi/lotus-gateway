"""Fail CI when measured quality-baseline metrics regress beyond their ratchet."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from numbers import Number
from pathlib import Path
from typing import Any

DEFAULT_BASELINE = Path("quality/quality_ratchet.json")
DEFAULT_ARTIFACT_DIR = Path("output/quality-baseline")


@dataclass(frozen=True)
class MetricResult:
    name: str
    current: Decimal
    baseline: Decimal
    threshold: Decimal
    comparison: str
    remediation: str

    @property
    def delta(self) -> Decimal:
        return self.current - self.baseline

    @property
    def passed(self) -> bool:
        if self.comparison == "not_below":
            return self.current >= self.threshold
        if self.comparison == "not_above":
            return self.current <= self.threshold
        raise ValueError(f"Unsupported comparison: {self.comparison}")


def _as_number(value: Any, *, field: str, metric_name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Number):
        raise ValueError(f"Metric {metric_name} has non-numeric {field}: {value!r}")
    return Decimal(str(value))


def _read_metric(log_path: Path, metric: dict[str, Any]) -> Decimal:
    if not log_path.is_file():
        raise ValueError(f"Missing quality-baseline log for {metric['name']}: {log_path}")
    text = log_path.read_text(encoding="utf-8")
    matches = re.findall(metric["pattern"], text, re.MULTILINE)
    kind = metric["kind"]
    if kind == "count":
        return Decimal(len(matches))
    if kind == "number":
        if len(matches) != 1:
            raise ValueError(
                "Expected one numeric result for "
                f"{metric['name']} in {log_path}, found {len(matches)}"
            )
        match = matches[0]
        value = match[0] if isinstance(match, tuple) else match
        return Decimal(value)
    if kind == "group_sum":
        if not matches:
            raise ValueError(f"Expected numeric results for {metric['name']} in {log_path}")
        if len(matches) != 1 or not isinstance(matches[0], tuple):
            raise ValueError(
                f"Expected one grouped numeric result for {metric['name']} in {log_path}"
            )
        return sum((Decimal(value) for value in matches[0]), Decimal(0))
    raise ValueError(f"Unsupported metric kind for {metric['name']}: {kind}")


def evaluate_metrics(
    baseline: dict[str, Any],
    artifact_dir: Path,
) -> list[MetricResult]:
    results: list[MetricResult] = []
    for metric in baseline.get("metrics", []):
        name = metric["name"]
        results.append(
            MetricResult(
                name=name,
                current=_read_metric(artifact_dir / metric["log"], metric),
                baseline=_as_number(metric["baseline"], field="baseline", metric_name=name),
                threshold=_as_number(metric["threshold"], field="threshold", metric_name=name),
                comparison=metric["comparison"],
                remediation=metric["remediation"],
            )
        )
    return results


def _format_value(value: Decimal) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _report(results: list[MetricResult]) -> None:
    print("Quality baseline ratchet evidence:")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"{status} {result.name}: current={_format_value(result.current)} "
            f"baseline={_format_value(result.baseline)} delta={_format_value(result.delta)} "
            f"threshold={_format_value(result.threshold)}"
        )
        if not result.passed:
            print(f"  remediation: {result.remediation}")


def _update_baseline(path: Path, baseline: dict[str, Any], results: list[MetricResult]) -> None:
    current_by_name = {result.name: result.current for result in results}
    for metric in baseline["metrics"]:
        value = current_by_name[metric["name"]]
        marker = f"__QUALITY_NUMBER__{value:f}"
        metric["baseline"] = marker
        metric["threshold"] = marker
    payload = json.dumps(baseline, indent=2)
    payload = re.sub(r'"__QUALITY_NUMBER__(-?[0-9]+(?:\.[0-9]+)?)"', r"\1", payload)
    path.write_text(payload + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Explicitly update the checked-in baseline to current measured values.",
    )
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    results = evaluate_metrics(baseline, args.artifact_dir)
    _report(results)
    if args.update_baseline:
        _update_baseline(args.baseline, baseline, results)
        print(f"Updated quality baseline: {args.baseline}")
        return 0
    failures = [result for result in results if not result.passed]
    if failures:
        print(
            "Quality baseline ratchet failed: resolve each regression or update the baseline "
            "in a reviewed change."
        )
        return 1
    print(
        "Quality baseline ratchet passed: no measured metric regressed beyond its "
        "checked-in threshold."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
