import asyncio
from datetime import datetime, timezone
from typing import Any, cast

from app.clients.advise_client import AdviseClient
from app.clients.dpm_client import DpmClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.clients.reporting_client import ReportingClient
from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformBootstrapCaching,
    PlatformBootstrapEvidence,
    PlatformBootstrapFreshness,
    PlatformBootstrapSupportability,
    PlatformBootstrapVersioning,
    PlatformCapabilitiesData,
    PlatformCapabilitiesNormalized,
    PlatformCapabilitiesResponse,
    PlatformShellBootstrap,
    PlatformShellWorkspaceDescriptor,
)


class PlatformCapabilitiesService:
    _SHELL_BOOTSTRAP_CONTRACT_VERSION = "shell-bootstrap.v1"
    _PRIMARY_CAPABILITY_SOURCES = (
        "lotus_core",
        "lotus_performance",
        "lotus_advise",
        "lotus_manage",
        "lotus_report",
    )
    _OPTIONAL_CAPABILITY_SOURCES = ("lotus_risk",)
    _RISK_ANALYTICS_FEATURE_KEYS = (
        "risk.analytics.risk_analytics",
        "risk.analytics.drawdown",
        "risk.analytics.concentration",
        "risk.analytics.rolling_metrics",
        "risk.analytics.historical_attribution",
        "risk.analytics.metrics",
    )

    def __init__(
        self,
        lotus_core_query_client: LotusCoreQueryClient,
        analytics_client: LotusAnalyticsClient,
        reporting_client: ReportingClient,
        contract_version: str,
        source_timeout_seconds: float = 1.0,
        risk_client: LotusAnalyticsClient | None = None,
        advise_client: AdviseClient | None = None,
        manage_client: DpmClient | None = None,
        dpm_client: Any | None = None,
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

        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources: dict[str, dict[str, Any]] = {}
        errors: list[CapabilitySourceError] = []
        for service_name, result in zip(self._PRIMARY_CAPABILITY_SOURCES, results[:5], strict=True):
            if isinstance(result, BaseException):
                errors.append(
                    CapabilitySourceError(
                        service=service_name,
                        status_code=500,
                        detail=self._exception_detail(result),
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
        lotus_core_policy_result = results[5]
        if isinstance(lotus_core_policy_result, BaseException):
            errors.append(
                CapabilitySourceError(
                    service="lotus_core_policy",
                    status_code=500,
                    detail=self._exception_detail(lotus_core_policy_result),
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
        for index, source in enumerate(optional_sources, start=6):
            optional_result_map[source] = results[index]

        self._merge_optional_source(
            optional_result_map=optional_result_map,
            source_name="risk",
            gateway_source_name="lotus_risk",
            sources=sources,
            errors=errors,
        )

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
        input_modes_by_source: dict[str, list[str]] = {}
        input_modes_union: list[str] = []
        policy_versions_by_source: dict[str, str] = {}
        for source_name, source_payload in sources.items():
            source_modes = self._payload_value(
                source_payload,
                "supportedInputModes",
                "supported_input_modes",
                default=[],
            )
            normalized_modes = [str(mode) for mode in source_modes]
            input_modes_by_source[source_name] = normalized_modes
            policy_versions_by_source[source_name] = str(
                self._payload_value(
                    source_payload,
                    "policyVersion",
                    "policy_version",
                    default="unknown",
                )
            )
            for mode in normalized_modes:
                if mode not in input_modes_union:
                    input_modes_union.append(mode)
        for source_name in (*self._PRIMARY_CAPABILITY_SOURCES, *self._OPTIONAL_CAPABILITY_SOURCES):
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
                    "performance.analytics.twr",
                    "lotus_performance.analytics.mwr",
                    "performance.analytics.mwr",
                    "lotus_performance.analytics.contribution",
                    "performance.analytics.contribution",
                    "lotus_performance.analytics.attribution",
                    "performance.analytics.attribution",
                )
            ),
            "lotus_advise_lifecycle": self._feature_enabled(
                sources=sources,
                source_name="lotus_advise",
                feature_keys=(
                    "advisory.proposals.lifecycle",
                    "lotus_advise.proposals.lifecycle",
                    "advise.proposals.lifecycle",
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
            "lotus_risk_analytics": any(
                self._feature_enabled(
                    sources=sources,
                    source_name="lotus_risk",
                    feature_keys=(key,),
                )
                for key in self._RISK_ANALYTICS_FEATURE_KEYS
            ),
        }

        module_health = self._module_health(sources=sources, errors=errors)
        navigation = {
            "command_center": True,
            "portfolio_intake": (
                feature_enabled["lotus_core_intake"] or feature_enabled["lotus_core_snapshot"]
            ),
            "analytics_studio": feature_enabled["lotus_performance_analytics"],
            "advisory_pipeline": feature_enabled["lotus_advise_lifecycle"],
            "scenario_builder": feature_enabled["lotus_advise_lifecycle"],
            "decision_console": (
                feature_enabled["lotus_core_snapshot"]
                and (
                    feature_enabled["lotus_advise_lifecycle"]
                    or feature_enabled["lotus_manage_support"]
                )
            ),
            "reporting_hub": feature_enabled["lotus_report_reporting"],
            "portfolio_workspace": (
                feature_enabled["lotus_core_intake"] or feature_enabled["lotus_core_snapshot"]
            ),
            "performance_workspace": feature_enabled["lotus_performance_analytics"],
            "risk_workspace": feature_enabled["lotus_risk_analytics"],
            "proposal_workspace": False,
            "advisory_workspace": False,
        }
        workflow_flags = {
            "proposal_lifecycle": self._any_workflow_enabled(
                sources=sources,
                source_name="lotus_advise",
                workflow_keys=(
                    "advisory_proposal_lifecycle",
                    "proposal_lifecycle",
                ),
            ),
            "proposal_approval_flow": self._any_workflow_enabled(
                sources=sources,
                source_name="lotus_advise",
                workflow_keys=(
                    "advisory_proposal_approval_flow",
                    "proposal_approval_flow",
                ),
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
        shell_bootstrap = self._build_shell_bootstrap(
            sources=sources,
            navigation=navigation,
            module_health=module_health,
            policy_versions_by_source=policy_versions_by_source,
            errors=errors,
            evaluated_at=evaluated_at,
        )
        return PlatformCapabilitiesNormalized(
            navigation=navigation,
            workflowFlags=workflow_flags,
            inputModesBySource=input_modes_by_source,
            inputModesUnion=input_modes_union,
            moduleHealth=module_health,
            policyVersionsBySource=policy_versions_by_source,
            lotusCorePolicyDiagnostics=lotus_core_policy_diagnostics,
            shellBootstrap=shell_bootstrap,
        )

    def _build_shell_bootstrap(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        navigation: dict[str, bool],
        module_health: dict[str, str],
        policy_versions_by_source: dict[str, str],
        errors: list[CapabilitySourceError],
        evaluated_at: str,
    ) -> PlatformShellBootstrap:
        error_services = [error.service for error in errors]
        shell_state = "partial" if errors else "ready"
        shell_reasons = [f"{error.service}:{error.status_code}" for error in errors]

        return PlatformShellBootstrap(
            contractVersion=self._SHELL_BOOTSTRAP_CONTRACT_VERSION,
            supportability=PlatformBootstrapSupportability(
                state=shell_state,
                reasons=shell_reasons,
            ),
            freshness=PlatformBootstrapFreshness(
                state="current" if not errors else "partial",
                freshnessClass="shell_navigation",
                evaluatedAt=evaluated_at,
                maxAgeSeconds=60,
            ),
            evidence=PlatformBootstrapEvidence(
                state="partial" if errors else "source_backed",
                lineageSources=list(policy_versions_by_source.keys()),
                partialFailure=bool(errors),
                sourceErrorServices=error_services,
            ),
            versioning=PlatformBootstrapVersioning(
                shellContractVersion=self._SHELL_BOOTSTRAP_CONTRACT_VERSION,
                capabilityContractVersion=self._contract_version,
                sourcePolicyVersions=policy_versions_by_source,
            ),
            caching=PlatformBootstrapCaching(
                cacheMode="request_scoped_composition",
                invalidationOwner="upstream_service",
                staleReadTolerance="bounded_navigation_refresh",
                revalidateOnNavigation=True,
                ttlSeconds=60,
                correctnessCritical=False,
            ),
            workspaces=[
                self._build_workspace_descriptor(
                    workspace_id="portfolio",
                    label="Portfolio",
                    href="/portfolio",
                    enabled=navigation["portfolio_workspace"],
                    dependency_source="lotus_core",
                    source_supportability=None,
                    module_health=module_health,
                    policy_versions_by_source=policy_versions_by_source,
                    error_services=error_services,
                    evaluated_at=evaluated_at,
                    freshness_class="shell_navigation",
                    max_age_seconds=60,
                    cache_mode="request_scoped_composition",
                    stale_read_tolerance="bounded_navigation_refresh",
                ),
                self._build_workspace_descriptor(
                    workspace_id="performance",
                    label="Performance",
                    href="/performance",
                    enabled=navigation["performance_workspace"],
                    dependency_source="lotus_performance",
                    source_supportability=None,
                    module_health=module_health,
                    policy_versions_by_source=policy_versions_by_source,
                    error_services=error_services,
                    evaluated_at=evaluated_at,
                    freshness_class="analytical_summary",
                    max_age_seconds=120,
                    cache_mode="short_lived_revalidation",
                    stale_read_tolerance="bounded_analytical_read",
                ),
                self._build_workspace_descriptor(
                    workspace_id="risk",
                    label="Risk",
                    href="/performance?mode=risk",
                    enabled=navigation["risk_workspace"],
                    dependency_source="lotus_risk",
                    source_supportability=None,
                    module_health=module_health,
                    policy_versions_by_source=policy_versions_by_source,
                    error_services=error_services,
                    evaluated_at=evaluated_at,
                    freshness_class="analytical_summary",
                    max_age_seconds=120,
                    cache_mode="short_lived_revalidation",
                    stale_read_tolerance="bounded_analytical_read",
                ),
                self._build_workspace_descriptor(
                    workspace_id="proposal",
                    label="Proposal",
                    href="/proposals",
                    enabled=navigation["proposal_workspace"],
                    dependency_source="lotus_advise",
                    source_supportability=self._source_supportability(
                        sources=sources,
                        source_name="lotus_advise",
                    ),
                    module_health=module_health,
                    policy_versions_by_source=policy_versions_by_source,
                    error_services=error_services,
                    evaluated_at=evaluated_at,
                    freshness_class="workflow_truth",
                    max_age_seconds=0,
                    cache_mode="authoritative_read",
                    stale_read_tolerance="none",
                ),
                self._build_workspace_descriptor(
                    workspace_id="advisory",
                    label="Advisory",
                    href="/recommendations",
                    enabled=navigation["advisory_workspace"],
                    dependency_source="lotus_advise",
                    source_supportability=self._source_supportability(
                        sources=sources,
                        source_name="lotus_advise",
                    ),
                    module_health=module_health,
                    policy_versions_by_source=policy_versions_by_source,
                    error_services=error_services,
                    evaluated_at=evaluated_at,
                    freshness_class="workflow_truth",
                    max_age_seconds=0,
                    cache_mode="authoritative_read",
                    stale_read_tolerance="none",
                ),
            ],
        )

    def _build_workspace_descriptor(
        self,
        *,
        workspace_id: str,
        label: str,
        href: str,
        enabled: bool,
        dependency_source: str,
        source_supportability: dict[str, Any] | None,
        module_health: dict[str, str],
        policy_versions_by_source: dict[str, str],
        error_services: list[str],
        evaluated_at: str,
        freshness_class: str,
        max_age_seconds: int,
        cache_mode: str,
        stale_read_tolerance: str,
    ) -> PlatformShellWorkspaceDescriptor:
        source_health = module_health.get(dependency_source, "unknown")
        if enabled and source_health == "available":
            supportability_state = "ready"
            evidence_state = "source_backed"
            freshness_state = "current"
            reasons: list[str] = []
        elif source_health == "unavailable":
            supportability_state = "partial"
            evidence_state = "partial"
            freshness_state = "partial"
            reasons = [f"{dependency_source}_unavailable"]
        else:
            supportability_state = "unavailable"
            evidence_state = "unavailable"
            freshness_state = "unavailable"
            reasons = (
                [f"{workspace_id}_disabled"] if not enabled else [f"{dependency_source}_unknown"]
            )
        if source_supportability is not None and source_health == "available":
            supportability_state = str(source_supportability.get("state") or supportability_state)
            source_reason = source_supportability.get("reason")
            reasons = [str(source_reason)] if source_reason else reasons

        return PlatformShellWorkspaceDescriptor(
            id=workspace_id,
            label=label,
            href=href,
            enabled=enabled,
            supportability=PlatformBootstrapSupportability(
                state=supportability_state,
                reasons=reasons,
            ),
            freshness=PlatformBootstrapFreshness(
                state=freshness_state,
                freshnessClass=freshness_class,
                evaluatedAt=evaluated_at,
                maxAgeSeconds=max_age_seconds,
            ),
            evidence=PlatformBootstrapEvidence(
                state=evidence_state,
                lineageSources=[dependency_source],
                partialFailure=dependency_source in error_services,
                sourceErrorServices=(
                    [dependency_source] if dependency_source in error_services else []
                ),
            ),
            versioning=PlatformBootstrapVersioning(
                shellContractVersion=self._SHELL_BOOTSTRAP_CONTRACT_VERSION,
                capabilityContractVersion=self._contract_version,
                sourcePolicyVersion=policy_versions_by_source.get(dependency_source),
            ),
            caching=PlatformBootstrapCaching(
                cacheMode=cache_mode,
                invalidationOwner=dependency_source,
                staleReadTolerance=stale_read_tolerance,
                revalidateOnNavigation=True,
                ttlSeconds=max_age_seconds,
                correctnessCritical=freshness_class == "workflow_truth",
            ),
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

    def _payload_value(
        self,
        payload: dict[str, Any],
        camel_key: str,
        snake_key: str,
        *,
        default: Any,
    ) -> Any:
        value = payload.get(camel_key, payload.get(snake_key, default))
        if isinstance(default, list) and not isinstance(value, list):
            return []
        return value

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

    def _any_workflow_enabled(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
        workflow_keys: tuple[str, ...],
    ) -> bool:
        return any(
            self._workflow_enabled(
                sources=sources,
                source_name=source_name,
                workflow_key=workflow_key,
            )
            for workflow_key in workflow_keys
        )

    def _source_supportability(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        source_name: str,
    ) -> dict[str, Any] | None:
        supportability = sources.get(source_name, {}).get("supportability")
        if not isinstance(supportability, dict):
            return None
        return supportability

    def _module_health(
        self,
        *,
        sources: dict[str, dict[str, Any]],
        errors: list[CapabilitySourceError],
    ) -> dict[str, str]:
        errored_sources = {error.service for error in errors}
        health: dict[str, str] = {}
        for source_name in (*self._PRIMARY_CAPABILITY_SOURCES, *self._OPTIONAL_CAPABILITY_SOURCES):
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
        if isinstance(result, BaseException):
            errors.append(
                CapabilitySourceError(
                    service=gateway_source_name,
                    status_code=500,
                    detail=self._exception_detail(result),
                )
            )
            return
        status_code, payload = cast(tuple[int, dict[str, Any]], result)
        if status_code >= 400:
            errors.append(
                CapabilitySourceError(
                    service=gateway_source_name,
                    status_code=status_code,
                    detail=str(payload.get("detail", payload)),
                )
            )
            return
        sources[gateway_source_name] = payload

    def _exception_detail(self, exc: BaseException) -> str:
        message = str(exc)
        exception_type = type(exc).__name__
        if message:
            return f"upstream_exception:{exception_type}: {message}"
        return f"upstream_exception:{exception_type}"
