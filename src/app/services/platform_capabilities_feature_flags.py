from typing import Any

CORE_SNAPSHOT_FEATURE_KEYS = (
    "lotus_core.integration.core_snapshot",
    "lotus_core.support.overview_api",
    "lotus_core.ingestion.portfolio_bundle_adapter",
    "pas.integration.core_snapshot",
)
CORE_INTAKE_FEATURE_KEYS = (
    "lotus_core.ingestion.bulk_upload",
    "lotus_core.ingestion.bulk_upload_adapter",
    "lotus_core.ingestion.portfolio_bundle_adapter",
    "pas.ingestion.bulk_upload",
)
PERFORMANCE_ANALYTICS_FEATURE_KEYS = (
    "lotus_performance.analytics.twr",
    "performance.analytics.twr",
    "lotus_performance.analytics.mwr",
    "performance.analytics.mwr",
    "lotus_performance.analytics.contribution",
    "performance.analytics.contribution",
    "lotus_performance.analytics.attribution",
    "performance.analytics.attribution",
)
ADVISE_LIFECYCLE_FEATURE_KEYS = (
    "advisory.proposals.lifecycle",
    "lotus_advise.proposals.lifecycle",
    "advise.proposals.lifecycle",
    "dpm.proposals.lifecycle",
)
MANAGE_SUPPORT_FEATURE_KEYS = (
    "lotus_manage.support.run_apis",
    "dpm.support.run_apis",
)
REPORTING_FEATURE_KEYS = (
    "lotus_report.reporting.portfolio_summary",
    "ras.reporting.portfolio_summary",
    "lotus_report.reporting.portfolio_review",
    "ras.reporting.portfolio_review",
    "lotus_report.aggregation.portfolio_snapshot",
    "ras.aggregation.portfolio_snapshot",
)
RISK_ANALYTICS_FEATURE_KEYS = (
    "risk.analytics.risk_analytics",
    "risk.analytics.drawdown",
    "risk.analytics.concentration",
    "risk.analytics.rolling_metrics",
    "risk.analytics.historical_attribution",
    "risk.analytics.metrics",
)


def feature_enablement(sources: dict[str, dict[str, Any]]) -> dict[str, bool]:
    return {
        "lotus_core_snapshot": core_snapshot_enabled(sources),
        "lotus_core_intake": core_intake_enabled(sources),
        "lotus_performance_analytics": performance_analytics_enabled(sources),
        "lotus_advise_lifecycle": advise_lifecycle_enabled(sources),
        "lotus_manage_support": manage_support_enabled(sources),
        "lotus_report_reporting": reporting_enabled(sources),
        "lotus_risk_analytics": risk_analytics_enabled(sources),
    }


def core_snapshot_enabled(sources: dict[str, dict[str, Any]]) -> bool:
    return feature_enabled(
        sources=sources,
        source_name="lotus_core",
        feature_keys=CORE_SNAPSHOT_FEATURE_KEYS,
    )


def core_intake_enabled(sources: dict[str, dict[str, Any]]) -> bool:
    return feature_enabled(
        sources=sources,
        source_name="lotus_core",
        feature_keys=CORE_INTAKE_FEATURE_KEYS,
    )


def performance_analytics_enabled(sources: dict[str, dict[str, Any]]) -> bool:
    return any_feature_enabled(
        sources=sources,
        source_name="lotus_performance",
        feature_keys=PERFORMANCE_ANALYTICS_FEATURE_KEYS,
    )


def advise_lifecycle_enabled(sources: dict[str, dict[str, Any]]) -> bool:
    return feature_enabled(
        sources=sources,
        source_name="lotus_advise",
        feature_keys=ADVISE_LIFECYCLE_FEATURE_KEYS,
    )


def manage_support_enabled(sources: dict[str, dict[str, Any]]) -> bool:
    return feature_enabled(
        sources=sources,
        source_name="lotus_manage",
        feature_keys=MANAGE_SUPPORT_FEATURE_KEYS,
    )


def reporting_enabled(sources: dict[str, dict[str, Any]]) -> bool:
    return any_feature_enabled(
        sources=sources,
        source_name="lotus_report",
        feature_keys=REPORTING_FEATURE_KEYS,
    )


def risk_analytics_enabled(sources: dict[str, dict[str, Any]]) -> bool:
    return any_feature_enabled(
        sources=sources,
        source_name="lotus_risk",
        feature_keys=RISK_ANALYTICS_FEATURE_KEYS,
    )


def feature_enabled(
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


def any_feature_enabled(
    *,
    sources: dict[str, dict[str, Any]],
    source_name: str,
    feature_keys: tuple[str, ...],
) -> bool:
    return any(
        feature_enabled(sources=sources, source_name=source_name, feature_keys=(feature_key,))
        for feature_key in feature_keys
    )


def workflow_flags(sources: dict[str, dict[str, Any]]) -> dict[str, bool]:
    return {
        "proposal_lifecycle": any_workflow_enabled(
            sources=sources,
            source_name="lotus_advise",
            workflow_keys=(
                "advisory_proposal_lifecycle",
                "proposal_lifecycle",
            ),
        ),
        "proposal_approval_flow": any_workflow_enabled(
            sources=sources,
            source_name="lotus_advise",
            workflow_keys=(
                "advisory_proposal_approval_flow",
                "proposal_approval_flow",
            ),
        ),
        "portfolio_bulk_onboarding": workflow_enabled(
            sources=sources,
            source_name="lotus_core",
            workflow_key="portfolio_bulk_onboarding",
        ),
        "performance_snapshot": workflow_enabled(
            sources=sources,
            source_name="lotus_performance",
            workflow_key="performance_snapshot",
        ),
        "portfolio_reporting": workflow_enabled(
            sources=sources,
            source_name="lotus_report",
            workflow_key="portfolio_reporting",
        ),
    }


def workflow_enabled(
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


def any_workflow_enabled(
    *,
    sources: dict[str, dict[str, Any]],
    source_name: str,
    workflow_keys: tuple[str, ...],
) -> bool:
    return any(
        workflow_enabled(
            sources=sources,
            source_name=source_name,
            workflow_key=workflow_key,
        )
        for workflow_key in workflow_keys
    )
