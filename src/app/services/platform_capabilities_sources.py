from typing import Any, cast

from app.contracts.platform_capabilities import CapabilitySourceError
from app.services.platform_capabilities_normalization import PRIMARY_CAPABILITY_SOURCES
from app.services.upstream_envelope import safe_upstream_detail


def primary_sources_from_results(
    results: list[Any],
) -> tuple[dict[str, dict[str, Any]], list[CapabilitySourceError]]:
    sources: dict[str, dict[str, Any]] = {}
    errors: list[CapabilitySourceError] = []
    for service_name, result in zip(PRIMARY_CAPABILITY_SOURCES, results[:5], strict=True):
        payload = payload_from_source_result(
            result=result,
            service_name=service_name,
            errors=errors,
        )
        if payload is not None:
            sources[service_name] = payload
    return sources, errors


def lotus_core_policy_from_result(
    *,
    result: Any,
    errors: list[CapabilitySourceError],
) -> dict[str, Any] | None:
    return payload_from_source_result(
        result=result,
        service_name="lotus_core_policy",
        errors=errors,
    )


def merge_optional_capability_sources(
    *,
    results: list[Any],
    optional_sources: list[str],
    sources: dict[str, dict[str, Any]],
    errors: list[CapabilitySourceError],
) -> None:
    optional_result_map: dict[str, Any] = {}
    start_index = len(PRIMARY_CAPABILITY_SOURCES) + 1
    for index, source in enumerate(optional_sources, start=start_index):
        optional_result_map[source] = results[index]
    merge_optional_source(
        optional_result_map=optional_result_map,
        source_name="risk",
        gateway_source_name="lotus_risk",
        sources=sources,
        errors=errors,
    )


def payload_from_source_result(
    *,
    result: Any,
    service_name: str,
    errors: list[CapabilitySourceError],
) -> dict[str, Any] | None:
    if isinstance(result, BaseException):
        errors.append(
            CapabilitySourceError(
                service=service_name,
                status_code=500,
                detail=exception_detail(result),
            )
        )
        return None
    status_code, payload = cast(tuple[int, dict[str, Any]], result)
    if status_code >= 400:
        errors.append(
            CapabilitySourceError(
                service=service_name,
                status_code=status_code,
                detail=safe_upstream_detail(
                    payload,
                    default_detail="capability source unavailable",
                ),
            )
        )
        return None
    return payload


def merge_optional_source(
    *,
    optional_result_map: dict[str, Any],
    source_name: str,
    gateway_source_name: str,
    sources: dict[str, dict[str, Any]],
    errors: list[CapabilitySourceError],
) -> None:
    result = optional_result_map.get(source_name)
    if result is None:
        return
    payload = payload_from_source_result(
        result=result,
        service_name=gateway_source_name,
        errors=errors,
    )
    if payload is not None:
        sources[gateway_source_name] = payload


def exception_detail(exc: BaseException) -> str:
    message = str(exc)
    exception_type = type(exc).__name__
    if message:
        return f"upstream_exception:{exception_type}: {message}"
    return f"upstream_exception:{exception_type}"
