from fastapi import APIRouter, Depends, FastAPI

from app.router_groups.advisory import (
    ADVISOR_BOOK_ROUTERS,
    ADVISOR_COCKPIT_ROUTERS,
    ADVISORY_COPILOT_ROUTERS,
    ADVISORY_POLICY_ROUTERS,
    ADVISORY_WORKSPACE_ROUTERS,
    BANK_DEMO_PROOF_ROUTERS,
    PROPOSAL_ROUTERS,
)
from app.router_groups.dpm import (
    DPM_CAMPAIGN_ROUTERS,
    DPM_COMMAND_CENTER_ROUTERS,
    DPM_PROOF_AND_CONSTRUCTION_ROUTERS,
    DPM_WAVE_ROUTERS,
)
from app.router_registration import include_routers
from app.routers.analytics_diagnostics import router as analytics_diagnostics_router
from app.routers.archive_document_downloads import (
    router as archive_document_downloads_router,
)
from app.routers.archive_documents import router as archive_documents_router
from app.routers.composite_performance import router as composite_performance_router
from app.routers.composite_performance_inspection import (
    router as composite_performance_inspection_router,
)
from app.routers.domain_product_catalog import router as domain_product_catalog_router
from app.routers.domain_product_detail import router as domain_product_detail_router
from app.routers.domain_product_graph import router as domain_product_graph_router
from app.routers.domain_product_trust import router as domain_product_trust_router
from app.routers.ideas import router as ideas_router
from app.routers.ideas_actions import router as ideas_actions_router
from app.routers.intake import router as intake_router
from app.routers.intake_upload_commits import router as intake_upload_commits_router
from app.routers.intake_uploads import router as intake_uploads_router
from app.routers.lookup_currency_catalog import router as lookup_currency_catalog_router
from app.routers.lookup_instrument_catalog import router as lookup_instrument_catalog_router
from app.routers.lookup_portfolio_catalog import router as lookup_portfolio_catalog_router
from app.routers.platform import router as platform_router
from app.routers.portfolio import router as portfolio_router
from app.routers.portfolio_activity import router as portfolio_activity_router
from app.routers.portfolio_allocations import router as portfolio_allocations_router
from app.routers.portfolio_book import router as portfolio_book_router
from app.routers.portfolio_income_summary import router as portfolio_income_summary_router
from app.routers.portfolio_insights import router as portfolio_insights_router
from app.routers.portfolio_liquidity import router as portfolio_liquidity_router
from app.routers.portfolio_performance import router as portfolio_performance_router
from app.routers.portfolio_positions import router as portfolio_positions_router
from app.routers.portfolio_projected_cashflow import (
    router as portfolio_projected_cashflow_router,
)
from app.routers.portfolio_readiness import router as portfolio_readiness_router
from app.routers.portfolio_transactions import router as portfolio_transactions_router
from app.routers.portfolio_workflow import router as portfolio_workflow_router
from app.routers.portfolio_workspace import router as portfolio_workspace_router
from app.routers.reporting_batch_cancel import cancel_router as reporting_batch_cancel_router
from app.routers.reporting_batch_lease_recovery import (
    recovery_router as reporting_batch_lease_recovery_router,
)
from app.routers.reporting_batch_pause import pause_router as reporting_batch_pause_router
from app.routers.reporting_batch_resume import controls_router as reporting_batch_resume_router
from app.routers.reporting_batch_retry import retry_router as reporting_batch_retry_router
from app.routers.reporting_batch_run_once import (
    worker_router as reporting_batch_run_once_router,
)
from app.routers.reporting_batch_status import status_router as reporting_batch_status_router
from app.routers.reporting_batches import batches_router as reporting_batches_router
from app.routers.reporting_job_controls import controls_router as reporting_job_controls_router
from app.routers.reporting_job_events import events_router as reporting_job_events_router
from app.routers.reporting_job_lineage import lineage_router as reporting_job_lineage_router
from app.routers.reporting_job_search import search_router as reporting_job_search_router
from app.routers.reporting_job_submissions import router as reporting_job_submissions_router
from app.routers.reporting_jobs import jobs_router as reporting_jobs_router
from app.routers.reporting_ordering import router as reporting_ordering_router
from app.routers.reporting_outcome_review_submissions import (
    router as reporting_outcome_review_submissions_router,
)
from app.routers.reporting_portfolio_reviews import router as reporting_portfolio_reviews_router
from app.routers.reporting_portfolio_snapshots import (
    router as reporting_portfolio_snapshots_router,
)
from app.routers.reporting_portfolio_summary import (
    router as reporting_portfolio_summary_router,
)
from app.routers.reporting_schedule_runs import (
    schedule_runs_router as reporting_schedule_runs_router,
)
from app.routers.reporting_schedules import schedules_router as reporting_schedules_router
from app.routers.reporting_snapshot_lineage import router as reporting_snapshot_lineage_router
from app.routers.reporting_snapshot_records import router as reporting_snapshot_records_router
from app.routers.source_products import router as source_products_router
from app.routers.workbench import router as workbench_router
from app.routers.workbench_analytics import router as workbench_analytics_router
from app.routers.workbench_performance import router as workbench_performance_router
from app.routers.workbench_performance_advisor_brief import (
    router as workbench_performance_advisor_brief_router,
)
from app.routers.workbench_performance_advisor_brief_review_actions import (
    router as workbench_performance_advisor_brief_review_actions_router,
)
from app.routers.workbench_performance_attribution_trend import (
    router as workbench_performance_attribution_trend_router,
)
from app.routers.workbench_performance_details import (
    router as workbench_performance_details_router,
)
from app.routers.workbench_performance_evidence import (
    router as workbench_performance_evidence_router,
)
from app.routers.workbench_performance_modules import (
    router as workbench_performance_modules_router,
)
from app.routers.workbench_portfolio_360 import router as workbench_portfolio_360_router
from app.routers.workbench_risk import router as workbench_risk_router
from app.routers.workbench_risk_attribution import (
    router as workbench_risk_attribution_router,
)
from app.routers.workbench_risk_concentration import (
    router as workbench_risk_concentration_router,
)
from app.routers.workbench_risk_drawdown import router as workbench_risk_drawdown_router
from app.routers.workbench_risk_rolling import router as workbench_risk_rolling_router
from app.routers.workbench_sandbox import router as workbench_sandbox_router
from app.routers.workbench_sandbox_changes import router as workbench_sandbox_changes_router
from app.services.dpm_manage_request_authority import bind_dpm_manage_request_authority

RouterGroup = tuple[APIRouter, ...]

PLATFORM_DISCOVERY_ROUTERS: RouterGroup = (
    platform_router,
    domain_product_catalog_router,
    domain_product_detail_router,
    domain_product_graph_router,
    domain_product_trust_router,
    source_products_router,
)

INTAKE_ROUTERS: RouterGroup = (
    intake_router,
    intake_uploads_router,
    intake_upload_commits_router,
)

LOOKUP_ROUTERS: RouterGroup = (
    lookup_currency_catalog_router,
    lookup_instrument_catalog_router,
    lookup_portfolio_catalog_router,
)

PORTFOLIO_ROUTERS: RouterGroup = (
    portfolio_router,
    portfolio_workspace_router,
    portfolio_readiness_router,
    portfolio_insights_router,
    portfolio_income_summary_router,
    portfolio_activity_router,
    portfolio_transactions_router,
    portfolio_book_router,
    portfolio_liquidity_router,
    portfolio_projected_cashflow_router,
    portfolio_allocations_router,
    portfolio_positions_router,
    portfolio_performance_router,
    portfolio_workflow_router,
)

PERFORMANCE_ROUTERS: RouterGroup = (
    composite_performance_router,
    composite_performance_inspection_router,
)

WORKBENCH_ROUTERS: RouterGroup = (
    workbench_router,
    workbench_portfolio_360_router,
    workbench_analytics_router,
    workbench_performance_router,
    workbench_performance_details_router,
    workbench_performance_advisor_brief_router,
    workbench_performance_advisor_brief_review_actions_router,
    workbench_performance_attribution_trend_router,
    workbench_performance_evidence_router,
    workbench_performance_modules_router,
    workbench_risk_router,
    workbench_risk_attribution_router,
    workbench_risk_concentration_router,
    workbench_risk_drawdown_router,
    workbench_risk_rolling_router,
    workbench_sandbox_router,
    workbench_sandbox_changes_router,
)

REPORTING_ROUTERS: RouterGroup = (
    reporting_ordering_router,
    reporting_portfolio_summary_router,
    reporting_portfolio_reviews_router,
    reporting_portfolio_snapshots_router,
    reporting_job_submissions_router,
    reporting_outcome_review_submissions_router,
    reporting_snapshot_records_router,
    reporting_snapshot_lineage_router,
    reporting_job_search_router,
    reporting_jobs_router,
    reporting_job_events_router,
    reporting_job_lineage_router,
    reporting_job_controls_router,
    reporting_batches_router,
    reporting_batch_status_router,
    reporting_batch_resume_router,
    reporting_batch_cancel_router,
    reporting_batch_pause_router,
    reporting_batch_retry_router,
    reporting_batch_lease_recovery_router,
    reporting_batch_run_once_router,
    reporting_schedules_router,
    reporting_schedule_runs_router,
)

OPERATIONS_ROUTERS: RouterGroup = (
    archive_documents_router,
    archive_document_downloads_router,
    analytics_diagnostics_router,
)

IDEA_ROUTERS: RouterGroup = (ideas_router, ideas_actions_router)

ROUTER_GROUPS: tuple[RouterGroup, ...] = (
    ADVISOR_BOOK_ROUTERS,
    ADVISOR_COCKPIT_ROUTERS,
    BANK_DEMO_PROOF_ROUTERS,
    ADVISORY_WORKSPACE_ROUTERS,
    ADVISORY_POLICY_ROUTERS,
    ADVISORY_COPILOT_ROUTERS,
    PROPOSAL_ROUTERS,
    PLATFORM_DISCOVERY_ROUTERS,
    INTAKE_ROUTERS,
    LOOKUP_ROUTERS,
    PORTFOLIO_ROUTERS,
    PERFORMANCE_ROUTERS,
    DPM_COMMAND_CENTER_ROUTERS,
    DPM_CAMPAIGN_ROUTERS,
    DPM_PROOF_AND_CONSTRUCTION_ROUTERS,
    DPM_WAVE_ROUTERS,
    WORKBENCH_ROUTERS,
    REPORTING_ROUTERS,
    IDEA_ROUTERS,
    OPERATIONS_ROUTERS,
)

DPM_ROUTER_GROUPS: tuple[RouterGroup, ...] = (
    DPM_COMMAND_CENTER_ROUTERS,
    DPM_CAMPAIGN_ROUTERS,
    DPM_PROOF_AND_CONSTRUCTION_ROUTERS,
    DPM_WAVE_ROUTERS,
)

_DPM_REQUEST_DEPENDENCIES = (Depends(bind_dpm_manage_request_authority),)


def register_routers(app: FastAPI) -> None:
    for router_group in ROUTER_GROUPS:
        dependencies = (
            _DPM_REQUEST_DEPENDENCIES
            if any(router_group is candidate for candidate in DPM_ROUTER_GROUPS)
            else ()
        )
        include_routers(
            app,
            *router_group,
            dependencies=dependencies,
        )
