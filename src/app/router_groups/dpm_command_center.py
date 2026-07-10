from app.router_groups.dpm_types import RouterGroup
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
