import asyncio
from datetime import datetime, timezone
from typing import Any, cast

from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformCapabilitiesData,
    PlatformCapabilitiesNormalized,
    PlatformCapabilitiesResponse,
)
from app.services.platform_capabilities_normalization import (
    PRIMARY_CAPABILITY_SOURCES,
    build_normalized_capabilities,
)
from app.services.platform_capabilities_normalization import (
    feature_enabled as _normalized_feature_enabled,
)
from app.services.platform_capabilities_normalization import (
    module_health as _normalized_module_health,
)
from app.services.platform_capabilities_normalization import (
    payload_value as _normalized_payload_value,
)
from app.services.platform_capabilities_normalization import (
    workflow_enabled as _normalized_workflow_enabled,
)
from app.services.workspace_client_protocols import (
    PlatformCapabilitiesCoreClient,
    PlatformCapabilitiesRiskClient,
    PlatformCapabilitiesSourceClient,
)


class PlatformCapabilitiesService:
    def __init__(
        self,
        lotus_core_query_client: PlatformCapabilitiesCoreClient,
        analytics_client: PlatformCapabilitiesSourceClient,
        reporting_client: PlatformCapabilitiesSourceClient,
        contract_version: str,
        source_timeout_seconds: float = 1.0,
        risk_client: PlatformCapabilitiesRiskClient | None = None,
        advise_client: PlatformCapabilitiesSourceClient | None = None,
        manage_client: PlatformCapabilitiesSourceClient | None = None,
        dpm_client: PlatformCapabilitiesSourceClient | None = None,
    ):
        if advise_client is None:
            if dpm_client is None:
                raise ValueError("PlatformCapabilitiesService requires an advise_client")
            advise_client = dpm_client
        if manage_client is None:
            if dpm_client is None:
                raise ValueError("PlatformCapabilitiesService requires a manage_client")
            manage_client = dpm_client
        self._advise_client = advise_client
        self._manage_client = manage_client
        self._lotus_core_query_client = lotus_core_query_client
        self._analytics_client = analytics_client
        self._reporting_client = reporting_client
        self._risk_client = risk_client
        self._contract_version = contract_version
        self._source_timeout_seconds = source_timeout_seconds

    async def get_platform_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> PlatformCapabilitiesResponse:
        evaluated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        tasks, optional_sources = self._build_capability_tasks(
            consumer_system=consumer_system,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sources, errors = self._primary_sources_from_results(results)
        lotus_core_policy_payload = self._lotus_core_policy_from_result(
            result=results[len(PRIMARY_CAPABILITY_SOURCES)],
            errors=errors,
        )
        self._merge_optional_capability_sources(
            results=results,
            optional_sources=optional_sources,
            sources=sources,
            errors=errors,
        )
        return self._build_platform_capabilities_response(
            consumer_system=consumer_system,
            tenant_id=tenant_id,
            sources=sources,
            errors=errors,
            lotus_core_policy_payload=lotus_core_policy_payload,
            evaluated_at=evaluated_at,
        )

    def _build_capability_tasks(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[list[Any], list[str]]:
        tasks: list[Any] = [
            self._with_timeout(
                self._lotus_core_query_client.get_capabilities(
                    consumer_system=consumer_system,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
            ),
            self._with_timeout(
                self._analytics_client.get_capabilities(
                    correlation_id=correlation_id,
                    consumer_system=consumer_system,
                    tenant_id=tenant_id,
                )
            ),
            self._with_timeout(
                self._advise_client.get_capabilities(
                    consumer_system=consumer_system,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
            ),
            self._with_timeout(
                self._manage_client.get_capabilities(
                    consumer_system=consumer_system,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
            ),
            self._with_timeout(
                self._reporting_client.get_capabilities(
                    consumer_system=consumer_system,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
            ),
            self._with_timeout(
                self._lotus_core_query_client.get_effective_policy(
                    consumer_system=consumer_system,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
            ),
        ]
        optional_sources: list[str] = []
        if self._risk_client is not None:
            tasks.append(
                self._with_timeout(
                    self._risk_client.get_capabilities(
                        correlation_id=correlation_id,
                    )
                )
            )
            optional_sources.append("risk")
        return tasks, optional_sources

    def _primary_sources_from_results(
        self,
        results: list[Any],
    ) -> tuple[dict[str, dict[str, Any]], list[CapabilitySourceError]]:
        sources: dict[str, dict[str, Any]] = {}
        errors: list[CapabilitySourceError] = []
        for service_name, result in zip(PRIMARY_CAPABILITY_SOURCES, results[:5], strict=True):
            payload = self._payload_from_source_result(
                result=result,
                service_name=service_name,
                errors=errors,
            )
            if payload is not None:
                sources[service_name] = payload
        return sources, errors

    def _lotus_core_policy_from_result(
        self,
        *,
        result: Any,
        errors: list[CapabilitySourceError],
    ) -> dict[str, Any] | None:
        return self._payload_from_source_result(
            result=result,
            service_name="lotus_core_policy",
            errors=errors,
        )

    def _merge_optional_capability_sources(
        self,
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
        self._merge_optional_source(
            optional_result_map=optional_result_map,
            source_name="risk",
            gateway_source_name="lotus_risk",
            sources=sources,
            errors=errors,
        )

    def _build_platform_capabilities_response(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
        lotus_core_policy_payload: dict[str, Any] | None,
        evaluated_at: str,
    ) -> PlatformCapabilitiesResponse:
        normalized = self._build_normalized_capabilities(
            sources=sources,
            errors=errors,
            lotus_core_policy=lotus_core_policy_payload,
            evaluated_at=evaluated_at,
        )
        data = PlatformCapabilitiesData(
            consumerSystem=consumer_system,
            tenantId=tenant_id,
            contractVersion=self._contract_version,
            sources=sources,
            partialFailure=len(errors) > 0,
            errors=errors,
            normalized=normalized,
        )
        return PlatformCapabilitiesResponse(data=data)

    def _payload_from_source_result(
        self,
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
                    detail=self._exception_detail(result),
                )
            )
            return None
        status_code, payload = cast(tuple[int, dict[str, Any]], result)
        if status_code >= 400:
            errors.append(
                CapabilitySourceError(
                    service=service_name,
                    status_code=status_code,
                    detail=str(payload.get("detail", payload)),
                )
            )
            return None
        return payload

    async def _with_timeout(self, coroutine: Any) -> Any:
        return await asyncio.wait_for(coroutine, timeout=self._source_timeout_seconds)

    def _build_normalized_capabilities(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
        lotus_core_policy: dict[str, Any] | None,
        evaluated_at: str,
    ) -> PlatformCapabilitiesNormalized:
        return build_normalized_capabilities(
            sources=sources,
            errors=errors,
            lotus_core_policy=lotus_core_policy,
            evaluated_at=evaluated_at,
            contract_version=self._contract_version,
        )

    def _feature_enabled(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
        feature_keys: tuple[str, ...],
    ) -> bool:
        return _normalized_feature_enabled(
            sources=sources,
            source_name=source_name,
            feature_keys=feature_keys,
        )

    def _payload_value(
        self,
        payload: dict[str, Any],
        camel_key: str,
        snake_key: str,
        *,
        default: Any,
    ) -> Any:
        return _normalized_payload_value(
            payload,
            camel_key,
            snake_key,
            default=default,
        )

    def _workflow_enabled(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
        workflow_key: str,
    ) -> bool:
        return _normalized_workflow_enabled(
            sources=sources,
            source_name=source_name,
            workflow_key=workflow_key,
        )

    def _any_workflow_enabled(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
        workflow_keys: tuple[str, ...],
    ) -> bool:
        return any(
            _normalized_workflow_enabled(
                sources=sources,
                source_name=source_name,
                workflow_key=workflow_key,
            )
            for workflow_key in workflow_keys
        )

    def _module_health(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
    ) -> dict[str, str]:
        return _normalized_module_health(sources=sources, errors=errors)

    def _merge_optional_source(
        self,
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
        payload = self._payload_from_source_result(
            result=result,
            service_name=gateway_source_name,
            errors=errors,
        )
        if payload is not None:
            sources[gateway_source_name] = payload

    def _exception_detail(self, exc: BaseException) -> str:
        message = str(exc)
        exception_type = type(exc).__name__
        if message:
            return f"upstream_exception:{exception_type}: {message}"
        return f"upstream_exception:{exception_type}"
