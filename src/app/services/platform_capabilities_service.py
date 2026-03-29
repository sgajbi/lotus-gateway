import asyncio
from typing import Any, cast

from app.clients.dpm_client import DpmClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.clients.reporting_client import ReportingClient
from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformCapabilitiesData,
    PlatformCapabilitiesNormalized,
    PlatformCapabilitiesResponse,
)


class PlatformCapabilitiesService:
    def __init__(
        self,
        dpm_client: DpmClient,
        lotus_core_query_client: LotusCoreQueryClient,
        analytics_client: LotusAnalyticsClient,
        reporting_client: ReportingClient,
        contract_version: str,
        risk_client: LotusAnalyticsClient | None = None,
        manage_client: DpmClient | None = None,
    ):
        self._dpm_client = dpm_client
        self._lotus_core_query_client = lotus_core_query_client
        self._analytics_client = analytics_client
        self._reporting_client = reporting_client
        self._risk_client = risk_client
        self._manage_client = manage_client
        self._contract_version = contract_version

    async def get_platform_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> PlatformCapabilitiesResponse:
        tasks: list[Any] = [
            self._lotus_core_query_client.get_capabilities(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._analytics_client.get_capabilities(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._dpm_client.get_capabilities(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._reporting_client.get_capabilities(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.get_effective_policy(
                consumer_system=consumer_system,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            ),
        ]
        optional_sources: list[str] = []
        if self._risk_client is not None:
            tasks.append(
                self._risk_client.get_capabilities(
                    consumer_system=consumer_system,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
            )
            optional_sources.append("risk")
        if self._manage_client is not None:
            tasks.append(
                self._manage_client.get_capabilities(
                    consumer_system=consumer_system,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
            )
            optional_sources.append("manage")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources: dict[str, dict[str, Any]] = {}
        errors: list[CapabilitySourceError] = []
        service_names = ["lotus_core", "lotus_performance", "lotus_manage", "lotus_report"]

        for service_name, result in zip(service_names, results[:4], strict=True):
            if isinstance(result, BaseException):
                errors.append(
                    CapabilitySourceError(
                        service=service_name,
                        status_code=500,
                        detail=f"upstream_exception: {result}",
                    )
                )
                continue

            status_code, payload = cast(tuple[int, dict[str, Any]], result)
            if status_code >= 400:
                errors.append(
                    CapabilitySourceError(
                        service=service_name,
                        status_code=status_code,
                        detail=str(payload.get("detail", payload)),
                    )
                )
                continue

            sources[service_name] = payload

        lotus_core_policy_payload: dict[str, Any] | None = None
        lotus_core_policy_result = results[4]
        if isinstance(lotus_core_policy_result, BaseException):
            errors.append(
                CapabilitySourceError(
                    service="lotus_core_policy",
                    status_code=500,
                    detail=f"upstream_exception: {lotus_core_policy_result}",
                )
            )
        else:
            policy_status_code, policy_payload = cast(
                tuple[int, dict[str, Any]], lotus_core_policy_result
            )
            if policy_status_code >= 400:
                errors.append(
                    CapabilitySourceError(
                        service="lotus_core_policy",
                        status_code=policy_status_code,
                        detail=str(policy_payload.get("detail", policy_payload)),
                    )
                )
            else:
                lotus_core_policy_payload = policy_payload

        optional_result_map: dict[str, Any] = {}
        for index, source in enumerate(optional_sources, start=5):
            optional_result_map[source] = results[index]

        self._merge_optional_source_into_primary(
            optional_result_map=optional_result_map,
            source_name="risk",
            primary_source_name="lotus_performance",
            sources=sources,
            errors=errors,
        )
        self._merge_optional_source_into_primary(
            optional_result_map=optional_result_map,
            source_name="manage",
            primary_source_name="lotus_manage",
            sources=sources,
            errors=errors,
        )

        normalized = self._build_normalized_capabilities(
            sources=sources,
            errors=errors,
            lotus_core_policy=lotus_core_policy_payload,
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

    def _build_normalized_capabilities(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
        lotus_core_policy: dict[str, Any] | None,
    ) -> PlatformCapabilitiesNormalized:
        input_modes_by_source: dict[str, list[str]] = {}
        input_modes_union: list[str] = []
        policy_versions_by_source: dict[str, str] = {}
        for source_name, source_payload in sources.items():
            source_modes = source_payload.get("supportedInputModes", [])
            if not isinstance(source_modes, list):
                source_modes = []
            normalized_modes = [str(mode) for mode in source_modes]
            input_modes_by_source[source_name] = normalized_modes
            policy_versions_by_source[source_name] = str(
                source_payload.get("policyVersion", "unknown")
            )
            for mode in normalized_modes:
                if mode not in input_modes_union:
                    input_modes_union.append(mode)
        for source_name in (
            "lotus_core",
            "lotus_performance",
            "lotus_manage",
            "lotus_report",
        ):
            policy_versions_by_source.setdefault(source_name, "unknown")

        feature_enabled = {
            "lotus_core_snapshot": self._feature_enabled(
                sources=sources,
                source_name="lotus_core",
                feature_keys=(
                    "lotus_core.integration.core_snapshot",
                    "pas.integration.core_snapshot",
                ),
            ),
            "lotus_core_intake": self._feature_enabled(
                sources=sources,
                source_name="lotus_core",
                feature_keys=(
                    "lotus_core.ingestion.bulk_upload",
                    "pas.ingestion.bulk_upload",
                ),
            ),
            "lotus_performance_analytics": any(
                self._feature_enabled(
                    sources=sources,
                    source_name="lotus_performance",
                    feature_keys=(key,),
                )
                for key in (
                    "lotus_performance.analytics.twr",
                    "pa.analytics.twr",
                    "lotus_performance.analytics.mwr",
                    "pa.analytics.mwr",
                    "lotus_performance.analytics.contribution",
                    "pa.analytics.contribution",
                    "lotus_performance.analytics.attribution",
                    "pa.analytics.attribution",
                )
            ),
            "lotus_manage_lifecycle": self._feature_enabled(
                sources=sources,
                source_name="lotus_manage",
                feature_keys=(
                    "lotus_manage.proposals.lifecycle",
                    "dpm.proposals.lifecycle",
                ),
            ),
            "lotus_manage_support": self._feature_enabled(
                sources=sources,
                source_name="lotus_manage",
                feature_keys=(
                    "lotus_manage.support.run_apis",
                    "dpm.support.run_apis",
                ),
            ),
            "lotus_report_reporting": any(
                self._feature_enabled(
                    sources=sources,
                    source_name="lotus_report",
                    feature_keys=(key,),
                )
                for key in (
                    "lotus_report.reporting.portfolio_summary",
                    "ras.reporting.portfolio_summary",
                    "lotus_report.reporting.portfolio_review",
                    "ras.reporting.portfolio_review",
                    "lotus_report.aggregation.portfolio_snapshot",
                    "ras.aggregation.portfolio_snapshot",
                )
            ),
        }

        module_health = self._module_health(sources=sources, errors=errors)
        navigation = {
            "command_center": True,
            "portfolio_intake": (
                feature_enabled["lotus_core_intake"] or feature_enabled["lotus_core_snapshot"]
            ),
            "analytics_studio": feature_enabled["lotus_performance_analytics"],
            "advisory_pipeline": feature_enabled["lotus_manage_lifecycle"],
            "scenario_builder": feature_enabled["lotus_manage_lifecycle"],
            "decision_console": (
                feature_enabled["lotus_core_snapshot"]
                and (
                    feature_enabled["lotus_manage_lifecycle"]
                    or feature_enabled["lotus_manage_support"]
                )
            ),
            "reporting_hub": feature_enabled["lotus_report_reporting"],
        }
        workflow_flags = {
            "proposal_lifecycle": self._workflow_enabled(
                sources=sources,
                source_name="lotus_manage",
                workflow_key="proposal_lifecycle",
            ),
            "proposal_approval_flow": self._workflow_enabled(
                sources=sources,
                source_name="lotus_manage",
                workflow_key="proposal_approval_flow",
            ),
            "portfolio_bulk_onboarding": self._workflow_enabled(
                sources=sources,
                source_name="lotus_core",
                workflow_key="portfolio_bulk_onboarding",
            ),
            "performance_snapshot": self._workflow_enabled(
                sources=sources,
                source_name="lotus_performance",
                workflow_key="performance_snapshot",
            ),
            "portfolio_reporting": self._workflow_enabled(
                sources=sources,
                source_name="lotus_report",
                workflow_key="portfolio_reporting",
            ),
        }
        lotus_core_policy_diagnostics = self._lotus_core_policy_diagnostics(
            lotus_core_policy=lotus_core_policy,
            errors=errors,
        )
        return PlatformCapabilitiesNormalized(
            navigation=navigation,
            workflowFlags=workflow_flags,
            inputModesBySource=input_modes_by_source,
            inputModesUnion=input_modes_union,
            moduleHealth=module_health,
            policyVersionsBySource=policy_versions_by_source,
            lotusCorePolicyDiagnostics=lotus_core_policy_diagnostics,
        )

    def _feature_enabled(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
        feature_keys: tuple[str, ...],
    ) -> bool:
        source_payload = sources.get(source_name, {})
        features = source_payload.get("features", [])
        if not isinstance(features, list):
            return False
        for feature in features:
            if not isinstance(feature, dict):
                continue
            if str(feature.get("key")) in feature_keys:
                return bool(feature.get("enabled"))
        return False

    def _workflow_enabled(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
        workflow_key: str,
    ) -> bool:
        source_payload = sources.get(source_name, {})
        workflows = source_payload.get("workflows", [])
        if not isinstance(workflows, list):
            return False
        for workflow in workflows:
            if not isinstance(workflow, dict):
                continue
            if str(workflow.get("workflow_key")) == workflow_key:
                return bool(workflow.get("enabled"))
        return False

    def _module_health(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
    ) -> dict[str, str]:
        errored_sources = {error.service for error in errors}
        health: dict[str, str] = {}
        for source_name in (
            "lotus_core",
            "lotus_performance",
            "lotus_manage",
            "lotus_report",
        ):
            if source_name in sources:
                health[source_name] = "available"
            elif source_name in errored_sources:
                health[source_name] = "unavailable"
            else:
                health[source_name] = "unknown"
        return health

    def _lotus_core_policy_diagnostics(
        self,
        *,
        lotus_core_policy: dict[str, Any] | None,
        errors: list[CapabilitySourceError],
    ) -> dict[str, Any]:
        diagnostics: dict[str, Any] = {
            "available": False,
            "allowedSections": [],
            "warnings": [],
            "policyProvenance": {
                "policyVersion": "unknown",
                "policySource": "unknown",
                "matchedRuleId": "unknown",
                "strictMode": False,
            },
        }

        if lotus_core_policy is not None:
            diagnostics["available"] = True
            allowed_sections = lotus_core_policy.get("allowedSections", [])
            warnings = lotus_core_policy.get("warnings", [])
            provenance = lotus_core_policy.get("policyProvenance", {})
            diagnostics["allowedSections"] = (
                [str(section) for section in allowed_sections]
                if isinstance(allowed_sections, list)
                else []
            )
            diagnostics["warnings"] = (
                [str(warning) for warning in warnings] if isinstance(warnings, list) else []
            )
            if isinstance(provenance, dict):
                diagnostics["policyProvenance"] = {
                    "policyVersion": str(provenance.get("policyVersion", "unknown")),
                    "policySource": str(provenance.get("policySource", "unknown")),
                    "matchedRuleId": str(provenance.get("matchedRuleId", "unknown")),
                    "strictMode": bool(provenance.get("strictMode", False)),
                }

        if any(error.service == "lotus_core_policy" for error in errors):
            diagnostics["warnings"] = list(diagnostics["warnings"]) + [
                "LOTUS_CORE_POLICY_ENDPOINT_UNAVAILABLE"
            ]
        return diagnostics

    def _merge_optional_source_into_primary(
        self,
        *,
        optional_result_map: dict[str, Any],
        source_name: str,
        primary_source_name: str,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
    ) -> None:
        result = optional_result_map.get(source_name)
        if result is None or isinstance(result, BaseException):
            return
        status_code, payload = cast(tuple[int, dict[str, Any]], result)
        if status_code >= 400:
            return
        optional_payload = payload
        primary_payload = sources.get(primary_source_name)
        if primary_payload is None:
            sources[primary_source_name] = optional_payload
            errors[:] = [e for e in errors if e.service != primary_source_name]
            return

        primary_features = primary_payload.get("features", [])
        optional_features = optional_payload.get("features", [])
        if isinstance(primary_features, list) and isinstance(optional_features, list):
            seen = {str(item.get("key")) for item in primary_features if isinstance(item, dict)}
            for feature in optional_features:
                if not isinstance(feature, dict):
                    continue
                feature_key = str(feature.get("key"))
                if feature_key not in seen:
                    primary_features.append(feature)
                    seen.add(feature_key)
            primary_payload["features"] = primary_features

        primary_workflows = primary_payload.get("workflows", [])
        optional_workflows = optional_payload.get("workflows", [])
        if isinstance(primary_workflows, list) and isinstance(optional_workflows, list):
            seen_workflows = {
                str(item.get("workflow_key"))
                for item in primary_workflows
                if isinstance(item, dict)
            }
            for workflow in optional_workflows:
                if not isinstance(workflow, dict):
                    continue
                workflow_key = str(workflow.get("workflow_key"))
                if workflow_key not in seen_workflows:
                    primary_workflows.append(workflow)
                    seen_workflows.add(workflow_key)
            primary_payload["workflows"] = primary_workflows

        primary_modes = primary_payload.get("supportedInputModes", [])
        optional_modes = optional_payload.get("supportedInputModes", [])
        if isinstance(primary_modes, list) and isinstance(optional_modes, list):
            merged_modes = list(
                dict.fromkeys(
                    [
                        *map(str, primary_modes),
                        *map(str, optional_modes),
                    ]
                )
            )
            primary_payload["supportedInputModes"] = merged_modes
