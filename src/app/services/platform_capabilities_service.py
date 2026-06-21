import asyncio
from datetime import datetime, timezone
from typing import Any

from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformCapabilitiesData,
    PlatformCapabilitiesNormalized,
    PlatformCapabilitiesResponse,
)
from app.services.platform_capabilities_feature_flags import (
    feature_enabled as _normalized_feature_enabled,
)
from app.services.platform_capabilities_feature_flags import (
    workflow_enabled as _normalized_workflow_enabled,
)
from app.services.platform_capabilities_normalization import (
    PRIMARY_CAPABILITY_SOURCES,
    build_normalized_capabilities,
)
from app.services.platform_capabilities_normalization import (
    module_health as _normalized_module_health,
)
from app.services.platform_capabilities_normalization import (
    payload_value as _normalized_payload_value,
)
from app.services.platform_capabilities_sources import (
    lotus_core_policy_from_result,
    merge_optional_capability_sources,
    primary_sources_from_results,
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
        sources, errors = primary_sources_from_results(results)
        lotus_core_policy_payload = lotus_core_policy_from_result(
            result=results[len(PRIMARY_CAPABILITY_SOURCES)],
            errors=errors,
        )
        merge_optional_capability_sources(
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
        tasks = self._required_capability_tasks(
            consumer_system=consumer_system,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )
        tasks.append(
            self._lotus_core_policy_task(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            )
        )
        optional_tasks, optional_sources = self._optional_capability_tasks(
            correlation_id=correlation_id,
        )
        tasks.extend(optional_tasks)
        return tasks, optional_sources

    def _required_capability_tasks(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> list[Any]:
        return [
            self._source_capability_task(
                client=self._lotus_core_query_client,
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._source_capability_task(
                client=self._analytics_client,
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._source_capability_task(
                client=self._advise_client,
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._source_capability_task(
                client=self._manage_client,
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._source_capability_task(
                client=self._reporting_client,
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
        ]

    def _source_capability_task(
        self,
        *,
        client: PlatformCapabilitiesSourceClient,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> Any:
        return self._with_timeout(
            client.get_capabilities(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            )
        )

    def _lotus_core_policy_task(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> Any:
        return self._with_timeout(
            self._lotus_core_query_client.get_effective_policy(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            )
        )

    def _optional_capability_tasks(
        self,
        *,
        correlation_id: str,
    ) -> tuple[list[Any], list[str]]:
        if self._risk_client is not None:
            return (
                [
                    self._with_timeout(
                        self._risk_client.get_capabilities(
                            correlation_id=correlation_id,
                        )
                    )
                ],
                ["risk"],
            )
        return [], []

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
