from fastapi import FastAPI

from app.routers.advisor_cockpit import router as advisor_cockpit_router
from app.routers.advisor_cockpit_acknowledgements import (
    router as advisor_cockpit_acknowledgements_router,
)
from app.routers.advisor_cockpit_house_view import (
    router as advisor_cockpit_house_view_router,
)
from app.routers.advisor_cockpit_projections import (
    router as advisor_cockpit_projections_router,
)
from app.routers.advisory_policy import router as advisory_policy_router
from app.routers.advisory_policy_actions import router as advisory_policy_actions_router
from app.routers.advisory_policy_evaluation_actions import (
    router as advisory_policy_evaluation_actions_router,
)
from app.routers.advisory_policy_evaluation_evidence import (
    router as advisory_policy_evaluation_evidence_router,
)
from app.routers.advisory_policy_evaluation_support_actions import (
    router as advisory_policy_evaluation_support_actions_router,
)
from app.routers.advisory_policy_evaluations import (
    router as advisory_policy_evaluations_router,
)
from app.routers.advisory_workspace_actions import (
    router as advisory_workspace_actions_router,
)
from app.routers.advisory_workspace_assistant import (
    router as advisory_workspace_assistant_router,
)
from app.routers.advisory_workspace_handoff import (
    router as advisory_workspace_handoff_router,
)
from app.routers.advisory_workspace_version_lookups import (
    router as advisory_workspace_version_lookups_router,
)
from app.routers.advisory_workspace_versions import (
    router as advisory_workspace_versions_router,
)
from app.routers.advisory_workspaces import router as advisory_workspaces_router
from app.routers.analytics_diagnostics import router as analytics_diagnostics_router
from app.routers.archive_document_downloads import (
    router as archive_document_downloads_router,
)
from app.routers.archive_documents import router as archive_documents_router
from app.routers.bank_demo_proof import router as bank_demo_proof_router
from app.routers.composite_performance import router as composite_performance_router
from app.routers.domain_product_trust import router as domain_product_trust_router
from app.routers.domain_products import router as domain_products_router
from app.routers.dpm_command_center import router as dpm_command_center_router
from app.routers.dpm_command_center_exception_ai import (
    router as dpm_command_center_exception_ai_router,
)
from app.routers.dpm_command_center_exceptions import (
    router as dpm_command_center_exceptions_router,
)
from app.routers.dpm_command_center_mandate_analysis import (
    router as dpm_command_center_mandate_analysis_router,
)
from app.routers.dpm_command_center_mandates import (
    router as dpm_command_center_mandates_router,
)
from app.routers.dpm_command_center_monitoring import (
    router as dpm_command_center_monitoring_router,
)
from app.routers.dpm_command_center_outcome_review_evidence import (
    router as dpm_command_center_outcome_review_evidence_router,
)
from app.routers.dpm_command_center_outcome_review_handoff import (
    router as dpm_command_center_outcome_review_handoff_router,
)
from app.routers.dpm_command_center_outcome_review_lookup import (
    router as dpm_command_center_outcome_review_lookup_router,
)
from app.routers.dpm_command_center_outcome_review_lookups import (
    router as dpm_command_center_outcome_review_lookups_router,
)
from app.routers.dpm_command_center_outcome_review_narratives import (
    router as dpm_command_center_outcome_review_narratives_router,
)
from app.routers.dpm_command_center_outcome_reviews import (
    router as dpm_command_center_outcome_reviews_router,
)
from app.routers.dpm_command_center_pm_quality import (
    router as dpm_command_center_pm_quality_router,
)
from app.routers.dpm_command_center_pm_quality_ai import (
    router as dpm_command_center_pm_quality_ai_router,
)
from app.routers.dpm_command_center_pm_quality_fairness import (
    router as dpm_command_center_pm_quality_fairness_router,
)
from app.routers.dpm_command_center_pm_quality_fairness_lookup import (
    router as dpm_command_center_pm_quality_fairness_lookup_router,
)
from app.routers.dpm_command_center_pm_quality_policies import (
    router as dpm_command_center_pm_quality_policies_router,
)
from app.routers.dpm_command_center_pm_quality_policy_actions import (
    router as dpm_command_center_pm_quality_policy_actions_router,
)
from app.routers.dpm_command_center_pm_quality_review_action_lookup import (
    router as dpm_command_center_pm_quality_review_action_lookup_router,
)
from app.routers.dpm_command_center_pm_quality_review_actions import (
    router as dpm_command_center_pm_quality_review_actions_router,
)
from app.routers.dpm_command_center_pm_quality_score_run_lookup import (
    router as dpm_command_center_pm_quality_score_run_lookup_router,
)
from app.routers.dpm_command_center_pm_quality_summary_invocations import (
    router as dpm_command_center_pm_quality_summary_invocations_router,
)
from app.routers.dpm_command_center_pm_quality_summary_lookup import (
    router as dpm_command_center_pm_quality_summary_lookup_router,
)
from app.routers.dpm_command_center_portfolio_memory import (
    router as dpm_command_center_portfolio_memory_router,
)
from app.routers.dpm_construction import router as dpm_construction_router
from app.routers.dpm_construction_actions import router as dpm_construction_actions_router
from app.routers.dpm_proof_pack_ai import router as dpm_proof_pack_ai_router
from app.routers.dpm_proof_pack_evidence import router as dpm_proof_pack_evidence_router
from app.routers.dpm_proof_packs import router as dpm_proof_packs_router
from app.routers.dpm_wave_actions import router as dpm_wave_actions_router
from app.routers.dpm_wave_ai import router as dpm_wave_ai_router
from app.routers.dpm_wave_campaign_approvals import (
    router as dpm_wave_campaign_approvals_router,
)
from app.routers.dpm_wave_campaign_assignment_task_actions import (
    router as dpm_wave_campaign_assignment_task_actions_router,
)
from app.routers.dpm_wave_campaign_assignment_tasks import (
    router as dpm_wave_campaign_assignment_tasks_router,
)
from app.routers.dpm_wave_campaign_assignment_views import (
    router as dpm_wave_campaign_assignment_views_router,
)
from app.routers.dpm_wave_campaign_assignments import (
    router as dpm_wave_campaign_assignments_router,
)
from app.routers.dpm_wave_campaign_definition_lookup import (
    router as dpm_wave_campaign_definition_lookup_router,
)
from app.routers.dpm_wave_campaign_definitions import (
    router as dpm_wave_campaign_definitions_router,
)
from app.routers.dpm_wave_campaign_discovery import (
    router as dpm_wave_campaign_discovery_router,
)
from app.routers.dpm_wave_campaign_launch import (
    router as dpm_wave_campaign_launch_router,
)
from app.routers.dpm_wave_campaign_launch_actions import (
    router as dpm_wave_campaign_launch_actions_router,
)
from app.routers.dpm_wave_campaign_lifecycle import (
    router as dpm_wave_campaign_lifecycle_router,
)
from app.routers.dpm_wave_campaign_readiness import (
    router as dpm_wave_campaign_readiness_router,
)
from app.routers.dpm_wave_campaign_workflow import (
    router as dpm_wave_campaign_workflow_router,
)
from app.routers.dpm_wave_campaign_workflow_boards import (
    router as dpm_wave_campaign_workflow_boards_router,
)
from app.routers.dpm_wave_evidence import router as dpm_wave_evidence_router
from app.routers.dpm_wave_items import router as dpm_wave_items_router
from app.routers.dpm_wave_lifecycle_actions import router as dpm_wave_lifecycle_actions_router
from app.routers.dpm_wave_lookup import router as dpm_wave_lookup_router
from app.routers.dpm_wave_workflow_actions import router as dpm_wave_workflow_actions_router
from app.routers.dpm_waves import router as dpm_waves_router
from app.routers.foundation import router as foundation_router
from app.routers.intake import router as intake_router
from app.routers.intake_uploads import router as intake_uploads_router
from app.routers.lookup_catalogs import router as lookup_catalogs_router
from app.routers.platform import router as platform_router
from app.routers.portfolio import router as portfolio_router
from app.routers.portfolio_activity import router as portfolio_activity_router
from app.routers.portfolio_allocations import router as portfolio_allocations_router
from app.routers.portfolio_book import router as portfolio_book_router
from app.routers.portfolio_liquidity import router as portfolio_liquidity_router
from app.routers.portfolio_performance import router as portfolio_performance_router
from app.routers.portfolio_positions import router as portfolio_positions_router
from app.routers.portfolio_transactions import router as portfolio_transactions_router
from app.routers.portfolio_workflow import router as portfolio_workflow_router
from app.routers.portfolio_workspace import router as portfolio_workspace_router
from app.routers.proposal_create import router as proposal_create_router
from app.routers.proposal_delivery import router as proposal_delivery_router
from app.routers.proposal_execution import router as proposal_execution_router
from app.routers.proposal_execution_status import router as proposal_execution_status_router
from app.routers.proposal_generation import router as proposal_generation_router
from app.routers.proposal_memo_actions import router as proposal_memo_actions_router
from app.routers.proposal_memo_evidence import router as proposal_memo_evidence_router
from app.routers.proposal_memo_reporting import router as proposal_memo_reporting_router
from app.routers.proposal_memos import router as proposal_memos_router
from app.routers.proposal_narrative_actions import router as proposal_narrative_actions_router
from app.routers.proposal_narratives import router as proposal_narratives_router
from app.routers.proposal_operation_lookups import router as proposal_operation_lookups_router
from app.routers.proposal_operation_support_lookups import (
    router as proposal_operation_support_lookups_router,
)
from app.routers.proposal_operations import router as proposal_operations_router
from app.routers.proposal_version_commands import router as proposal_version_commands_router
from app.routers.proposal_versions import router as proposal_versions_router
from app.routers.proposal_workflow import router as proposal_workflow_router
from app.routers.proposal_workflow_decisions import router as proposal_workflow_decisions_router
from app.routers.proposal_workflow_evidence import (
    router as proposal_workflow_evidence_router,
)
from app.routers.proposals import router as proposals_router
from app.routers.reporting import router as reporting_router
from app.routers.reporting_batch_controls import (
    controls_router as reporting_batch_controls_router,
)
from app.routers.reporting_batch_worker import worker_router as reporting_batch_worker_router
from app.routers.reporting_batches import batches_router as reporting_batches_router
from app.routers.reporting_job_controls import controls_router as reporting_job_controls_router
from app.routers.reporting_job_search import search_router as reporting_job_search_router
from app.routers.reporting_job_submissions import router as reporting_job_submissions_router
from app.routers.reporting_jobs import jobs_router as reporting_jobs_router
from app.routers.reporting_outcome_review_submissions import (
    router as reporting_outcome_review_submissions_router,
)
from app.routers.reporting_schedules import schedules_router as reporting_schedules_router
from app.routers.reporting_snapshots import router as reporting_snapshots_router
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


def register_routers(app: FastAPI) -> None:
    app.include_router(advisor_cockpit_router)
    app.include_router(advisor_cockpit_acknowledgements_router)
    app.include_router(advisor_cockpit_projections_router)
    app.include_router(advisor_cockpit_house_view_router)
    app.include_router(bank_demo_proof_router)
    app.include_router(advisory_workspaces_router)
    app.include_router(advisory_workspace_actions_router)
    app.include_router(advisory_workspace_versions_router)
    app.include_router(advisory_workspace_version_lookups_router)
    app.include_router(advisory_workspace_assistant_router)
    app.include_router(advisory_workspace_handoff_router)
    app.include_router(advisory_policy_router)
    app.include_router(advisory_policy_actions_router)
    app.include_router(advisory_policy_evaluations_router)
    app.include_router(advisory_policy_evaluation_evidence_router)
    app.include_router(advisory_policy_evaluation_actions_router)
    app.include_router(advisory_policy_evaluation_support_actions_router)
    app.include_router(proposal_generation_router)
    app.include_router(proposal_create_router)
    app.include_router(proposals_router)
    app.include_router(proposal_operations_router)
    app.include_router(proposal_operation_lookups_router)
    app.include_router(proposal_operation_support_lookups_router)
    app.include_router(proposal_versions_router)
    app.include_router(proposal_version_commands_router)
    app.include_router(proposal_workflow_router)
    app.include_router(proposal_workflow_decisions_router)
    app.include_router(proposal_workflow_evidence_router)
    app.include_router(proposal_narrative_actions_router)
    app.include_router(proposal_narratives_router)
    app.include_router(proposal_delivery_router)
    app.include_router(proposal_execution_router)
    app.include_router(proposal_execution_status_router)
    app.include_router(proposal_memos_router)
    app.include_router(proposal_memo_evidence_router)
    app.include_router(proposal_memo_actions_router)
    app.include_router(proposal_memo_reporting_router)
    app.include_router(platform_router)
    app.include_router(domain_products_router)
    app.include_router(domain_product_trust_router)
    app.include_router(source_products_router)
    app.include_router(intake_router)
    app.include_router(intake_uploads_router)
    app.include_router(lookup_catalogs_router)
    app.include_router(foundation_router)
    app.include_router(portfolio_router)
    app.include_router(portfolio_workspace_router)
    app.include_router(portfolio_activity_router)
    app.include_router(portfolio_transactions_router)
    app.include_router(portfolio_book_router)
    app.include_router(portfolio_liquidity_router)
    app.include_router(portfolio_allocations_router)
    app.include_router(portfolio_positions_router)
    app.include_router(portfolio_performance_router)
    app.include_router(portfolio_workflow_router)
    app.include_router(composite_performance_router)
    app.include_router(dpm_command_center_router)
    app.include_router(dpm_command_center_mandates_router)
    app.include_router(dpm_command_center_mandate_analysis_router)
    app.include_router(dpm_command_center_monitoring_router)
    app.include_router(dpm_command_center_exceptions_router)
    app.include_router(dpm_command_center_exception_ai_router)
    app.include_router(dpm_command_center_outcome_reviews_router)
    app.include_router(dpm_command_center_outcome_review_lookup_router)
    app.include_router(dpm_command_center_outcome_review_evidence_router)
    app.include_router(dpm_command_center_outcome_review_handoff_router)
    app.include_router(dpm_command_center_outcome_review_narratives_router)
    app.include_router(dpm_command_center_outcome_review_lookups_router)
    app.include_router(dpm_command_center_pm_quality_router)
    app.include_router(dpm_command_center_pm_quality_ai_router)
    app.include_router(dpm_command_center_pm_quality_fairness_router)
    app.include_router(dpm_command_center_pm_quality_fairness_lookup_router)
    app.include_router(dpm_command_center_pm_quality_policies_router)
    app.include_router(dpm_command_center_pm_quality_policy_actions_router)
    app.include_router(dpm_command_center_pm_quality_review_actions_router)
    app.include_router(dpm_command_center_pm_quality_review_action_lookup_router)
    app.include_router(dpm_command_center_pm_quality_score_run_lookup_router)
    app.include_router(dpm_command_center_pm_quality_summary_invocations_router)
    app.include_router(dpm_command_center_pm_quality_summary_lookup_router)
    app.include_router(dpm_command_center_portfolio_memory_router)
    app.include_router(dpm_wave_campaign_definitions_router)
    app.include_router(dpm_wave_campaign_definition_lookup_router)
    app.include_router(dpm_wave_campaign_discovery_router)
    app.include_router(dpm_wave_campaign_workflow_boards_router)
    app.include_router(dpm_wave_campaign_assignment_views_router)
    app.include_router(dpm_wave_campaign_approvals_router)
    app.include_router(dpm_wave_campaign_assignments_router)
    app.include_router(dpm_wave_campaign_assignment_tasks_router)
    app.include_router(dpm_wave_campaign_assignment_task_actions_router)
    app.include_router(dpm_wave_campaign_workflow_router)
    app.include_router(dpm_construction_router)
    app.include_router(dpm_construction_actions_router)
    app.include_router(dpm_proof_packs_router)
    app.include_router(dpm_proof_pack_evidence_router)
    app.include_router(dpm_proof_pack_ai_router)
    app.include_router(dpm_waves_router)
    app.include_router(dpm_wave_lookup_router)
    app.include_router(dpm_wave_items_router)
    app.include_router(dpm_wave_actions_router)
    app.include_router(dpm_wave_lifecycle_actions_router)
    app.include_router(dpm_wave_workflow_actions_router)
    app.include_router(dpm_wave_evidence_router)
    app.include_router(dpm_wave_ai_router)
    app.include_router(dpm_wave_campaign_launch_router)
    app.include_router(dpm_wave_campaign_launch_actions_router)
    app.include_router(dpm_wave_campaign_lifecycle_router)
    app.include_router(dpm_wave_campaign_readiness_router)
    app.include_router(workbench_router)
    app.include_router(workbench_analytics_router)
    app.include_router(workbench_performance_router)
    app.include_router(workbench_performance_details_router)
    app.include_router(workbench_performance_advisor_brief_router)
    app.include_router(workbench_performance_advisor_brief_review_actions_router)
    app.include_router(workbench_performance_attribution_trend_router)
    app.include_router(workbench_performance_evidence_router)
    app.include_router(workbench_performance_modules_router)
    app.include_router(workbench_risk_router)
    app.include_router(workbench_risk_attribution_router)
    app.include_router(workbench_risk_concentration_router)
    app.include_router(workbench_risk_drawdown_router)
    app.include_router(workbench_risk_rolling_router)
    app.include_router(workbench_sandbox_router)
    app.include_router(reporting_router)
    app.include_router(reporting_job_submissions_router)
    app.include_router(reporting_outcome_review_submissions_router)
    app.include_router(reporting_snapshots_router)
    app.include_router(reporting_job_search_router)
    app.include_router(reporting_jobs_router)
    app.include_router(reporting_job_controls_router)
    app.include_router(reporting_batches_router)
    app.include_router(reporting_batch_controls_router)
    app.include_router(reporting_batch_worker_router)
    app.include_router(reporting_schedules_router)
    app.include_router(archive_documents_router)
    app.include_router(archive_document_downloads_router)
    app.include_router(analytics_diagnostics_router)
