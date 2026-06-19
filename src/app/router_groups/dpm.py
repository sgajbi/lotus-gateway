from fastapi import APIRouter

from app.routers.dpm_command_center import router as dpm_command_center_router
from app.routers.dpm_command_center_exception_ai import (
    router as dpm_command_center_exception_ai_router,
)
from app.routers.dpm_command_center_exception_resolution import (
    router as dpm_command_center_exception_resolution_router,
)
from app.routers.dpm_command_center_exceptions import (
    router as dpm_command_center_exceptions_router,
)
from app.routers.dpm_command_center_mandate_analysis import (
    router as dpm_command_center_mandate_analysis_router,
)
from app.routers.dpm_command_center_mandate_detail import (
    router as dpm_command_center_mandate_detail_router,
)
from app.routers.dpm_command_center_mandate_diff import (
    router as dpm_command_center_mandate_diff_router,
)
from app.routers.dpm_command_center_mandates import (
    router as dpm_command_center_mandates_router,
)
from app.routers.dpm_command_center_monitoring import (
    router as dpm_command_center_monitoring_router,
)
from app.routers.dpm_command_center_monitoring_commands import (
    router as dpm_command_center_monitoring_commands_router,
)
from app.routers.dpm_command_center_monitoring_detail import (
    router as dpm_command_center_monitoring_detail_router,
)
from app.routers.dpm_command_center_outcome_review_ai_evidence_input import (
    router as dpm_command_center_outcome_review_ai_evidence_input_router,
)
from app.routers.dpm_command_center_outcome_review_detail import (
    router as dpm_command_center_outcome_review_detail_router,
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
from app.routers.dpm_command_center_outcome_review_preview import (
    router as dpm_command_center_outcome_review_preview_router,
)
from app.routers.dpm_command_center_outcome_review_supportability import (
    router as dpm_command_center_outcome_review_supportability_router,
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
from app.routers.dpm_command_center_pm_quality_fairness_detail import (
    router as dpm_command_center_pm_quality_fairness_detail_router,
)
from app.routers.dpm_command_center_pm_quality_fairness_lookup import (
    router as dpm_command_center_pm_quality_fairness_lookup_router,
)
from app.routers.dpm_command_center_pm_quality_fairness_preview import (
    router as dpm_command_center_pm_quality_fairness_preview_router,
)
from app.routers.dpm_command_center_pm_quality_policies import (
    router as dpm_command_center_pm_quality_policies_router,
)
from app.routers.dpm_command_center_pm_quality_policy_actions import (
    router as dpm_command_center_pm_quality_policy_actions_router,
)
from app.routers.dpm_command_center_pm_quality_policy_detail import (
    router as dpm_command_center_pm_quality_policy_detail_router,
)
from app.routers.dpm_command_center_pm_quality_review_action_detail import (
    router as dpm_command_center_pm_quality_review_action_detail_router,
)
from app.routers.dpm_command_center_pm_quality_review_action_lookup import (
    router as dpm_command_center_pm_quality_review_action_lookup_router,
)
from app.routers.dpm_command_center_pm_quality_review_action_preview import (
    router as dpm_command_center_pm_quality_review_action_preview_router,
)
from app.routers.dpm_command_center_pm_quality_review_actions import (
    router as dpm_command_center_pm_quality_review_actions_router,
)
from app.routers.dpm_command_center_pm_quality_score_run_detail import (
    router as dpm_command_center_pm_quality_score_run_detail_router,
)
from app.routers.dpm_command_center_pm_quality_score_run_lookup import (
    router as dpm_command_center_pm_quality_score_run_lookup_router,
)
from app.routers.dpm_command_center_pm_quality_score_run_preview import (
    router as dpm_command_center_pm_quality_score_run_preview_router,
)
from app.routers.dpm_command_center_pm_quality_summary_detail import (
    router as dpm_command_center_pm_quality_summary_detail_router,
)
from app.routers.dpm_command_center_pm_quality_summary_invocation_preview import (
    router as dpm_command_center_pm_quality_summary_invocation_preview_router,
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
from app.routers.dpm_command_center_portfolio_memory_search import (
    router as dpm_command_center_portfolio_memory_search_router,
)
from app.routers.dpm_command_center_wave_outcome_reviews import (
    router as dpm_command_center_wave_outcome_reviews_router,
)
from app.routers.dpm_construction import router as dpm_construction_router
from app.routers.dpm_construction_actions import router as dpm_construction_actions_router
from app.routers.dpm_construction_selection import router as dpm_construction_selection_router
from app.routers.dpm_proof_pack_ai import router as dpm_proof_pack_ai_router
from app.routers.dpm_proof_pack_ai_evidence_input import (
    router as dpm_proof_pack_ai_evidence_input_router,
)
from app.routers.dpm_proof_pack_detail import router as dpm_proof_pack_detail_router
from app.routers.dpm_proof_pack_evidence import router as dpm_proof_pack_evidence_router
from app.routers.dpm_proof_pack_report_input import (
    router as dpm_proof_pack_report_input_router,
)
from app.routers.dpm_proof_packs import router as dpm_proof_packs_router
from app.routers.dpm_wave_actions import router as dpm_wave_actions_router
from app.routers.dpm_wave_ai import router as dpm_wave_ai_router
from app.routers.dpm_wave_campaign_approval_commands import (
    router as dpm_wave_campaign_approval_commands_router,
)
from app.routers.dpm_wave_campaign_approval_inbox import (
    router as dpm_wave_campaign_approval_inbox_router,
)
from app.routers.dpm_wave_campaign_approvals import (
    router as dpm_wave_campaign_approvals_router,
)
from app.routers.dpm_wave_campaign_assignment_action_commands import (
    router as dpm_wave_campaign_assignment_action_commands_router,
)
from app.routers.dpm_wave_campaign_assignment_task_actions import (
    router as dpm_wave_campaign_assignment_task_actions_router,
)
from app.routers.dpm_wave_campaign_assignment_task_transitions import (
    router as dpm_wave_campaign_assignment_task_transitions_router,
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
from app.routers.dpm_wave_campaign_definition_detail import (
    router as dpm_wave_campaign_definition_detail_router,
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
from app.routers.dpm_wave_campaign_launch_package import (
    router as dpm_wave_campaign_launch_package_router,
)
from app.routers.dpm_wave_campaign_lifecycle import (
    router as dpm_wave_campaign_lifecycle_router,
)
from app.routers.dpm_wave_campaign_maker_checker_commands import (
    router as dpm_wave_campaign_maker_checker_commands_router,
)
from app.routers.dpm_wave_campaign_operating_queue import (
    router as dpm_wave_campaign_operating_queue_router,
)
from app.routers.dpm_wave_campaign_preview_readiness import (
    router as dpm_wave_campaign_preview_readiness_router,
)
from app.routers.dpm_wave_campaign_readiness import (
    router as dpm_wave_campaign_readiness_router,
)
from app.routers.dpm_wave_campaign_supersede import (
    router as dpm_wave_campaign_supersede_router,
)
from app.routers.dpm_wave_campaign_workflow import (
    router as dpm_wave_campaign_workflow_router,
)
from app.routers.dpm_wave_campaign_workflow_automation import (
    router as dpm_wave_campaign_workflow_automation_router,
)
from app.routers.dpm_wave_campaign_workflow_boards import (
    router as dpm_wave_campaign_workflow_boards_router,
)
from app.routers.dpm_wave_cancellation import router as dpm_wave_cancellation_router
from app.routers.dpm_wave_detail import router as dpm_wave_detail_router
from app.routers.dpm_wave_evidence import router as dpm_wave_evidence_router
from app.routers.dpm_wave_handoff import router as dpm_wave_handoff_router
from app.routers.dpm_wave_item_selection import router as dpm_wave_item_selection_router
from app.routers.dpm_wave_items import router as dpm_wave_items_router
from app.routers.dpm_wave_lifecycle_actions import router as dpm_wave_lifecycle_actions_router
from app.routers.dpm_wave_lookup import router as dpm_wave_lookup_router
from app.routers.dpm_wave_operations_handoff_ai import (
    router as dpm_wave_operations_handoff_ai_router,
)
from app.routers.dpm_wave_preview import router as dpm_wave_preview_router
from app.routers.dpm_wave_report_input import router as dpm_wave_report_input_router
from app.routers.dpm_wave_simulation import router as dpm_wave_simulation_router
from app.routers.dpm_wave_supportability import router as dpm_wave_supportability_router
from app.routers.dpm_wave_workflow_actions import router as dpm_wave_workflow_actions_router
from app.routers.dpm_waves import router as dpm_waves_router

RouterGroup = tuple[APIRouter, ...]

DPM_COMMAND_CENTER_ROUTERS: RouterGroup = (
    dpm_command_center_router,
    dpm_command_center_mandates_router,
    dpm_command_center_mandate_detail_router,
    dpm_command_center_mandate_analysis_router,
    dpm_command_center_mandate_diff_router,
    dpm_command_center_monitoring_router,
    dpm_command_center_monitoring_commands_router,
    dpm_command_center_monitoring_detail_router,
    dpm_command_center_exceptions_router,
    dpm_command_center_exception_resolution_router,
    dpm_command_center_exception_ai_router,
    dpm_command_center_outcome_reviews_router,
    dpm_command_center_outcome_review_preview_router,
    dpm_command_center_outcome_review_detail_router,
    dpm_command_center_outcome_review_lookup_router,
    dpm_command_center_outcome_review_evidence_router,
    dpm_command_center_outcome_review_ai_evidence_input_router,
    dpm_command_center_outcome_review_handoff_router,
    dpm_command_center_outcome_review_narratives_router,
    dpm_command_center_outcome_review_lookups_router,
    dpm_command_center_outcome_review_supportability_router,
    dpm_command_center_wave_outcome_reviews_router,
    dpm_command_center_pm_quality_router,
    dpm_command_center_pm_quality_ai_router,
    dpm_command_center_pm_quality_score_run_preview_router,
    dpm_command_center_pm_quality_fairness_preview_router,
    dpm_command_center_pm_quality_fairness_router,
    dpm_command_center_pm_quality_fairness_detail_router,
    dpm_command_center_pm_quality_fairness_lookup_router,
    dpm_command_center_pm_quality_policy_detail_router,
    dpm_command_center_pm_quality_policies_router,
    dpm_command_center_pm_quality_policy_actions_router,
    dpm_command_center_pm_quality_review_action_preview_router,
    dpm_command_center_pm_quality_review_actions_router,
    dpm_command_center_pm_quality_review_action_detail_router,
    dpm_command_center_pm_quality_review_action_lookup_router,
    dpm_command_center_pm_quality_score_run_detail_router,
    dpm_command_center_pm_quality_score_run_lookup_router,
    dpm_command_center_pm_quality_summary_invocation_preview_router,
    dpm_command_center_pm_quality_summary_invocations_router,
    dpm_command_center_pm_quality_summary_detail_router,
    dpm_command_center_pm_quality_summary_lookup_router,
    dpm_command_center_portfolio_memory_router,
    dpm_command_center_portfolio_memory_search_router,
)

DPM_CAMPAIGN_ROUTERS: RouterGroup = (
    dpm_wave_campaign_definitions_router,
    dpm_wave_campaign_definition_lookup_router,
    dpm_wave_campaign_definition_detail_router,
    dpm_wave_campaign_discovery_router,
    dpm_wave_campaign_workflow_boards_router,
    dpm_wave_campaign_operating_queue_router,
    dpm_wave_campaign_assignment_views_router,
    dpm_wave_campaign_workflow_automation_router,
    dpm_wave_campaign_approval_inbox_router,
    dpm_wave_campaign_approvals_router,
    dpm_wave_campaign_assignment_action_commands_router,
    dpm_wave_campaign_approval_commands_router,
    dpm_wave_campaign_assignments_router,
    dpm_wave_campaign_assignment_tasks_router,
    dpm_wave_campaign_assignment_task_actions_router,
    dpm_wave_campaign_assignment_task_transitions_router,
    dpm_wave_campaign_workflow_router,
    dpm_wave_campaign_maker_checker_commands_router,
)

DPM_PROOF_AND_CONSTRUCTION_ROUTERS: RouterGroup = (
    dpm_construction_router,
    dpm_construction_actions_router,
    dpm_construction_selection_router,
    dpm_proof_packs_router,
    dpm_proof_pack_detail_router,
    dpm_proof_pack_evidence_router,
    dpm_proof_pack_report_input_router,
    dpm_proof_pack_ai_evidence_input_router,
    dpm_proof_pack_ai_router,
)

DPM_WAVE_ROUTERS: RouterGroup = (
    dpm_wave_preview_router,
    dpm_waves_router,
    dpm_wave_lookup_router,
    dpm_wave_detail_router,
    dpm_wave_items_router,
    dpm_wave_item_selection_router,
    dpm_wave_actions_router,
    dpm_wave_simulation_router,
    dpm_wave_lifecycle_actions_router,
    dpm_wave_cancellation_router,
    dpm_wave_workflow_actions_router,
    dpm_wave_handoff_router,
    dpm_wave_evidence_router,
    dpm_wave_report_input_router,
    dpm_wave_supportability_router,
    dpm_wave_ai_router,
    dpm_wave_operations_handoff_ai_router,
    dpm_wave_campaign_launch_router,
    dpm_wave_campaign_launch_package_router,
    dpm_wave_campaign_launch_actions_router,
    dpm_wave_campaign_lifecycle_router,
    dpm_wave_campaign_supersede_router,
    dpm_wave_campaign_preview_readiness_router,
    dpm_wave_campaign_readiness_router,
)
