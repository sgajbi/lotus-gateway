from fastapi import FastAPI

from app.routers.advisor_cockpit import router as advisor_cockpit_router
from app.routers.advisory_policy import router as advisory_policy_router
from app.routers.advisory_workspaces import router as advisory_workspaces_router
from app.routers.analytics_diagnostics import router as analytics_diagnostics_router
from app.routers.archive_documents import router as archive_documents_router
from app.routers.bank_demo_proof import router as bank_demo_proof_router
from app.routers.composite_performance import router as composite_performance_router
from app.routers.domain_products import router as domain_products_router
from app.routers.dpm_command_center import router as dpm_command_center_router
from app.routers.dpm_command_center_outcome_reviews import (
    router as dpm_command_center_outcome_reviews_router,
)
from app.routers.dpm_command_center_pm_quality import (
    router as dpm_command_center_pm_quality_router,
)
from app.routers.dpm_command_center_pm_quality_fairness import (
    router as dpm_command_center_pm_quality_fairness_router,
)
from app.routers.dpm_command_center_pm_quality_policies import (
    router as dpm_command_center_pm_quality_policies_router,
)
from app.routers.dpm_command_center_pm_quality_review_actions import (
    router as dpm_command_center_pm_quality_review_actions_router,
)
from app.routers.dpm_command_center_pm_quality_summary_invocations import (
    router as dpm_command_center_pm_quality_summary_invocations_router,
)
from app.routers.dpm_construction import router as dpm_construction_router
from app.routers.dpm_proof_packs import router as dpm_proof_packs_router
from app.routers.dpm_wave_campaign_definitions import (
    router as dpm_wave_campaign_definitions_router,
)
from app.routers.dpm_wave_campaign_workflow import (
    router as dpm_wave_campaign_workflow_router,
)
from app.routers.dpm_waves import router as dpm_waves_router
from app.routers.foundation import router as foundation_router
from app.routers.intake import router as intake_router
from app.routers.platform import router as platform_router
from app.routers.portfolio import router as portfolio_router
from app.routers.portfolio_activity import router as portfolio_activity_router
from app.routers.portfolio_book import router as portfolio_book_router
from app.routers.portfolio_performance import router as portfolio_performance_router
from app.routers.proposal_delivery import router as proposal_delivery_router
from app.routers.proposal_memos import router as proposal_memos_router
from app.routers.proposal_narratives import router as proposal_narratives_router
from app.routers.proposal_operations import router as proposal_operations_router
from app.routers.proposal_versions import router as proposal_versions_router
from app.routers.proposal_workflow import router as proposal_workflow_router
from app.routers.proposals import router as proposals_router
from app.routers.reporting import router as reporting_router
from app.routers.reporting_batches import batches_router as reporting_batches_router
from app.routers.reporting_jobs import jobs_router as reporting_jobs_router
from app.routers.reporting_schedules import schedules_router as reporting_schedules_router
from app.routers.reporting_snapshots import router as reporting_snapshots_router
from app.routers.source_products import router as source_products_router
from app.routers.workbench import router as workbench_router
from app.routers.workbench_performance import router as workbench_performance_router
from app.routers.workbench_risk import router as workbench_risk_router
from app.routers.workbench_sandbox import router as workbench_sandbox_router


def register_routers(app: FastAPI) -> None:
    app.include_router(advisor_cockpit_router)
    app.include_router(bank_demo_proof_router)
    app.include_router(advisory_workspaces_router)
    app.include_router(advisory_policy_router)
    app.include_router(proposals_router)
    app.include_router(proposal_operations_router)
    app.include_router(proposal_versions_router)
    app.include_router(proposal_workflow_router)
    app.include_router(proposal_narratives_router)
    app.include_router(proposal_delivery_router)
    app.include_router(proposal_memos_router)
    app.include_router(platform_router)
    app.include_router(domain_products_router)
    app.include_router(source_products_router)
    app.include_router(intake_router)
    app.include_router(foundation_router)
    app.include_router(portfolio_router)
    app.include_router(portfolio_activity_router)
    app.include_router(portfolio_book_router)
    app.include_router(portfolio_performance_router)
    app.include_router(composite_performance_router)
    app.include_router(dpm_command_center_router)
    app.include_router(dpm_command_center_outcome_reviews_router)
    app.include_router(dpm_command_center_pm_quality_router)
    app.include_router(dpm_command_center_pm_quality_fairness_router)
    app.include_router(dpm_command_center_pm_quality_policies_router)
    app.include_router(dpm_command_center_pm_quality_review_actions_router)
    app.include_router(dpm_command_center_pm_quality_summary_invocations_router)
    app.include_router(dpm_wave_campaign_definitions_router)
    app.include_router(dpm_wave_campaign_workflow_router)
    app.include_router(dpm_construction_router)
    app.include_router(dpm_proof_packs_router)
    app.include_router(dpm_waves_router)
    app.include_router(workbench_router)
    app.include_router(workbench_performance_router)
    app.include_router(workbench_risk_router)
    app.include_router(workbench_sandbox_router)
    app.include_router(reporting_router)
    app.include_router(reporting_snapshots_router)
    app.include_router(reporting_jobs_router)
    app.include_router(reporting_batches_router)
    app.include_router(reporting_schedules_router)
    app.include_router(archive_documents_router)
    app.include_router(analytics_diagnostics_router)
