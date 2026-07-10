from typing import Any, TypeAlias

from app.contracts.performance_workspace import PerformanceBenchmarkOptionView
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_parsing import safe_str
from app.services.upstream_envelope import safe_upstream_detail

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


def parse_benchmark_catalog_result(
    *,
    result: GatheredResult,
    assigned_benchmark_code: str | None,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> list[PerformanceBenchmarkOptionView]:
    records = _benchmark_catalog_records_from_result(
        result=result,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    return _benchmark_options_from_records(
        records=records,
        assigned_benchmark_code=assigned_benchmark_code,
    )


def _benchmark_catalog_records_from_result(
    *,
    result: GatheredResult,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> list[object]:
    if isinstance(result, BaseException):
        _record_benchmark_catalog_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code="UPSTREAM_EXCEPTION",
            detail=str(result),
        )
        return []
    status_code, payload = result
    if status_code >= 400 or not isinstance(payload, dict):
        _record_benchmark_catalog_failure(
            warnings=warnings,
            partial_failures=partial_failures,
            error_code=(
                f"HTTP_{status_code}"
                if isinstance(status_code, int)
                else "INVALID_UPSTREAM_PAYLOAD"
            ),
            detail=(
                safe_upstream_detail(payload, default_detail="benchmark catalog unavailable")
                if isinstance(payload, dict)
                else str(payload)
            ),
        )
        return []
    records = payload.get("records", [])
    if not isinstance(records, list):
        return []
    return records


def _benchmark_options_from_records(
    *,
    records: list[object],
    assigned_benchmark_code: str | None,
) -> list[PerformanceBenchmarkOptionView]:
    options_by_code: dict[str, PerformanceBenchmarkOptionView] = {}
    for record in records:
        option = _benchmark_option_from_record(
            record=record,
            assigned_benchmark_code=assigned_benchmark_code,
        )
        if option is not None:
            _upsert_benchmark_option(options_by_code, option)
    return sorted(
        options_by_code.values(),
        key=lambda option: (not option.is_assigned, option.benchmark_name),
    )


def _record_benchmark_catalog_failure(
    *,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
    error_code: str,
    detail: str,
) -> None:
    warnings.append("BENCHMARK_CATALOG_UNAVAILABLE")
    partial_failures.append(build_performance_failure("lotus-core", error_code, detail))


def _benchmark_option_from_record(
    *,
    record: object,
    assigned_benchmark_code: str | None,
) -> PerformanceBenchmarkOptionView | None:
    if not isinstance(record, dict):
        return None
    benchmark_code = safe_str(record.get("benchmark_id"))
    benchmark_name = safe_str(record.get("benchmark_name"))
    if not benchmark_code or not benchmark_name:
        return None
    return PerformanceBenchmarkOptionView(
        benchmark_code=benchmark_code,
        benchmark_name=benchmark_name,
        benchmark_currency=safe_str(record.get("benchmark_currency")),
        benchmark_type=safe_str(record.get("benchmark_type")),
        benchmark_family=safe_str(record.get("benchmark_family")),
        benchmark_provider=safe_str(record.get("benchmark_provider")),
        is_assigned=benchmark_code == assigned_benchmark_code,
    )


def _upsert_benchmark_option(
    options_by_code: dict[str, PerformanceBenchmarkOptionView],
    option: PerformanceBenchmarkOptionView,
) -> None:
    existing = options_by_code.get(option.benchmark_code)
    if existing is None or (option.is_assigned and not existing.is_assigned):
        options_by_code[option.benchmark_code] = option
