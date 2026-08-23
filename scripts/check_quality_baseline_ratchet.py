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
REPORT_RE_FLAGS = re.MULTILINE | re.DOTALL


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
    kind = metric["kind"]
    flags = REPORT_RE_FLAGS if kind in {"number", "group_sum"} else re.MULTILINE
    matches = re.findall(metric["pattern"], text, flags)
    if kind == "count":
        if (
            not matches
            and metric.get("zero_pattern")
            and not re.search(
                metric["zero_pattern"],
                text,
                flags,
            )
        ):
            raise ValueError(f"Missing zero-success marker for {metric['name']} in {log_path}")
        return Decimal(len(matches))
    if kind == "number":
        if (
            not matches
            and metric.get("zero_pattern")
            and re.search(
                metric["zero_pattern"],
                text,
                flags,
            )
        ):
            return Decimal(0)
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


def _encode_json(value: Any, *, indent: int = 0) -> str:
    """Serialize the small policy document while preserving Decimal JSON numbers."""

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
    raise TypeError(f"Unsupported policy JSON value: {type(value).__name__}")


def _parse_allowed_regressions(values: list[str]) -> dict[str, Decimal]:
    allowed: dict[str, Decimal] = {}
    for value in values:
        name, separator, raw_value = value.partition("=")
        if not separator or not name or not raw_value:
            raise ValueError(f"Expected --allow-regression METRIC=VALUE, received: {value!r}")
        try:
            allowed[name] = Decimal(raw_value)
        except ArithmeticError as exc:
            raise ValueError(f"Invalid regression value for {name}: {raw_value!r}") from exc
    return allowed


def _update_baseline(
    path: Path,
    baseline: dict[str, Any],
    results: list[MetricResult],
    allowed_regressions: dict[str, Decimal],
    reason: str | None,
) -> None:
    result_by_name = {result.name: result for result in results}
    unknown_metrics = sorted(set(allowed_regressions) - set(result_by_name))
    if unknown_metrics:
        raise ValueError(f"Unknown metrics in --allow-regression: {', '.join(unknown_metrics)}")
    failures = [result for result in results if not result.passed]
    for result in failures:
        allowed_value = allowed_regressions.get(result.name)
        if allowed_value != result.current:
            raise ValueError(
                f"Refusing to loosen {result.name}; use "
                f"--allow-regression {result.name}={_format_value(result.current)} "
                "with a specific --reason. This command only auto-tightens."
            )
    for name in allowed_regressions:
        if result_by_name[name].passed:
            raise ValueError(f"--allow-regression is not needed for non-regressing metric: {name}")
    if failures and not reason:
        raise ValueError("A --reason is required for every explicit baseline regression allowance")

    current_by_name = {result.name: result.current for result in results}
    for metric in baseline["metrics"]:
        value = current_by_name[metric["name"]]
        metric["baseline"] = value
        metric["threshold"] = value
    path.write_text(_encode_json(baseline) + "\n", encoding="utf-8")
    if failures:
        print(f"Applied explicit baseline regression allowance: {reason}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Explicitly update the checked-in baseline; improvements auto-tighten only.",
    )
    parser.add_argument(
        "--allow-regression",
        action="append",
        default=[],
        metavar="METRIC=VALUE",
        help="Explicitly allow one named metric regression during a reviewed baseline update.",
    )
    parser.add_argument(
        "--reason",
        help="Required justification for every explicit baseline regression allowance.",
    )
    args = parser.parse_args()

    try:
        allowed_regressions = _parse_allowed_regressions(args.allow_regression)
    except ValueError as exc:
        print(f"Quality baseline ratchet argument error: {exc}")
        return 2
    if args.reason and not args.allow_regression:
        print("Quality baseline ratchet argument error: --reason requires --allow-regression")
        return 2
    if args.allow_regression and not args.update_baseline:
        print(
            "Quality baseline ratchet argument error: --allow-regression requires --update-baseline"
        )
        return 2

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"), parse_float=Decimal)
    results = evaluate_metrics(baseline, args.artifact_dir)
    _report(results)
    if args.update_baseline:
        try:
            _update_baseline(
                args.baseline,
                baseline,
                results,
                allowed_regressions,
                args.reason,
            )
        except ValueError as exc:
            print(f"Quality baseline ratchet baseline-update error: {exc}")
            return 2
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
