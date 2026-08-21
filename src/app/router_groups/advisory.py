from fastapi import APIRouter

from app.routers.advisor_book import router as advisor_book_router
from app.routers.advisor_cockpit import router as advisor_cockpit_router
from app.routers.advisor_cockpit_acknowledgements import (
    router as advisor_cockpit_acknowledgements_router,
)
from app.routers.advisor_cockpit_action_lookup import (
    router as advisor_cockpit_action_lookup_router,
)
from app.routers.advisor_cockpit_house_view import (
    router as advisor_cockpit_house_view_router,
)
from app.routers.advisor_cockpit_preparation_packets import (
    router as advisor_cockpit_preparation_packets_router,
)
from app.routers.advisor_cockpit_snapshot import router as advisor_cockpit_snapshot_router
from app.routers.advisor_cockpit_supportability import (
    router as advisor_cockpit_supportability_router,
)
from app.routers.advisory_copilot import router as advisory_copilot_router
from app.routers.advisory_policy import router as advisory_policy_router
from app.routers.advisory_policy_actions import router as advisory_policy_actions_router
from app.routers.advisory_policy_ai_evidence import (
    router as advisory_policy_ai_evidence_router,
)
from app.routers.advisory_policy_evaluation_actions import (
    router as advisory_policy_evaluation_actions_router,
)
from app.routers.advisory_policy_evaluation_detail import (
    router as advisory_policy_evaluation_detail_router,
)
from app.routers.advisory_policy_evaluation_events import (
    router as advisory_policy_evaluation_events_router,
)
from app.routers.advisory_policy_evaluation_evidence import (
    router as advisory_policy_evaluation_evidence_router,
)
from app.routers.advisory_policy_evaluation_support_actions import (
    router as advisory_policy_evaluation_support_actions_router,
)
from app.routers.advisory_policy_evaluation_workflow import (
    router as advisory_policy_evaluation_workflow_router,
)
from app.routers.advisory_policy_evaluations import (
    router as advisory_policy_evaluations_router,
)
from app.routers.advisory_policy_pack_detail import (
    router as advisory_policy_pack_detail_router,
)
from app.routers.advisory_policy_review_queue import (
    router as advisory_policy_review_queue_router,
)
from app.routers.advisory_policy_sign_off_decisions import (
    router as advisory_policy_sign_off_decisions_router,
)
from app.routers.advisory_policy_sign_off_package import (
    router as advisory_policy_sign_off_package_router,
)
from app.routers.advisory_policy_validation import (
    router as advisory_policy_validation_router,
)
from app.routers.advisory_workspace_actions import (
    router as advisory_workspace_actions_router,
)
from app.routers.advisory_workspace_assistant import (
    router as advisory_workspace_assistant_router,
)
from app.routers.advisory_workspace_compare import (
    router as advisory_workspace_compare_router,
)
from app.routers.advisory_workspace_draft_actions import (
    router as advisory_workspace_draft_actions_router,
)
from app.routers.advisory_workspace_evaluate import (
    router as advisory_workspace_evaluate_router,
)
from app.routers.advisory_workspace_handoff import (
    router as advisory_workspace_handoff_router,
)
from app.routers.advisory_workspace_rationale_reviews import (
    router as advisory_workspace_rationale_reviews_router,
)
from app.routers.advisory_workspace_replay_evidence import (
    router as advisory_workspace_replay_evidence_router,
)
from app.routers.advisory_workspace_resume import (
    router as advisory_workspace_resume_router,
)
from app.routers.advisory_workspace_version_lookups import (
    router as advisory_workspace_version_lookups_router,
)
from app.routers.advisory_workspace_versions import (
    router as advisory_workspace_versions_router,
)
from app.routers.advisory_workspaces import router as advisory_workspaces_router
from app.routers.bank_demo_proof import router as bank_demo_proof_router
from app.routers.bank_demo_proof_packs import router as bank_demo_proof_packs_router
from app.routers.bank_demo_supported_claims import (
    router as bank_demo_supported_claims_router,
)
from app.routers.proposal_approvals import router as proposal_approvals_router
from app.routers.proposal_artifact import router as proposal_artifact_router
from app.routers.proposal_client_consent import router as proposal_client_consent_router
from app.routers.proposal_create import router as proposal_create_router
from app.routers.proposal_delivery import router as proposal_delivery_router
from app.routers.proposal_delivery_events import router as proposal_delivery_events_router
from app.routers.proposal_detail import router as proposal_detail_router
from app.routers.proposal_discussion_pack import router as proposal_discussion_pack_router
from app.routers.proposal_execution import router as proposal_execution_router
from app.routers.proposal_execution_status import router as proposal_execution_status_router
from app.routers.proposal_execution_updates import router as proposal_execution_updates_router
from app.routers.proposal_generation import router as proposal_generation_router
from app.routers.proposal_idempotency_records import (
    router as proposal_idempotency_records_router,
)
from app.routers.proposal_lineage import router as proposal_lineage_router
from app.routers.proposal_memo_actions import router as proposal_memo_actions_router
from app.routers.proposal_memo_ai_commentary import (
    router as proposal_memo_ai_commentary_router,
)
from app.routers.proposal_memo_detail import router as proposal_memo_detail_router
from app.routers.proposal_memo_evidence import router as proposal_memo_evidence_router
from app.routers.proposal_memo_lineage import router as proposal_memo_lineage_router
from app.routers.proposal_memo_replay_evidence import (
    router as proposal_memo_replay_evidence_router,
)
from app.routers.proposal_memo_report_packages import (
    router as proposal_memo_report_packages_router,
)
from app.routers.proposal_memo_reporting import router as proposal_memo_reporting_router
from app.routers.proposal_memos import router as proposal_memos_router
from app.routers.proposal_narrative_actions import router as proposal_narrative_actions_router
from app.routers.proposal_narrative_reviews import (
    router as proposal_narrative_reviews_router,
)
from app.routers.proposal_narratives import router as proposal_narratives_router
from app.routers.proposal_operation_correlation import (
    router as proposal_operation_correlation_router,
)
from app.routers.proposal_operation_lookups import router as proposal_operation_lookups_router
from app.routers.proposal_operation_support_lookups import (
    router as proposal_operation_support_lookups_router,
)
from app.routers.proposal_operations import router as proposal_operations_router
from app.routers.proposal_report_requests import router as proposal_report_requests_router
from app.routers.proposal_risk_approval import router as proposal_risk_approval_router
from app.routers.proposal_risk_impact import router as proposal_risk_impact_router
from app.routers.proposal_version_async import router as proposal_version_async_router
from app.routers.proposal_version_commands import router as proposal_version_commands_router
from app.routers.proposal_version_replay_evidence import (
    router as proposal_version_replay_evidence_router,
)
from app.routers.proposal_versions import router as proposal_versions_router
from app.routers.proposal_workflow import router as proposal_workflow_router
from app.routers.proposal_workflow_decisions import router as proposal_workflow_decisions_router
from app.routers.proposal_workflow_evidence import (
    router as proposal_workflow_evidence_router,
)
from app.routers.proposals import router as proposals_router

RouterGroup = tuple[APIRouter, ...]

ADVISOR_BOOK_ROUTERS: RouterGroup = (advisor_book_router,)

ADVISOR_COCKPIT_ROUTERS: RouterGroup = (
    advisor_cockpit_router,
    advisor_cockpit_action_lookup_router,
    advisor_cockpit_acknowledgements_router,
    advisor_cockpit_preparation_packets_router,
    advisor_cockpit_snapshot_router,
    advisor_cockpit_supportability_router,
    advisor_cockpit_house_view_router,
)

BANK_DEMO_PROOF_ROUTERS: RouterGroup = (
    bank_demo_proof_router,
    bank_demo_supported_claims_router,
    bank_demo_proof_packs_router,
)

ADVISORY_WORKSPACE_ROUTERS: RouterGroup = (
    advisory_workspaces_router,
    advisory_workspace_actions_router,
    advisory_workspace_draft_actions_router,
    advisory_workspace_evaluate_router,
    advisory_workspace_versions_router,
    advisory_workspace_resume_router,
    advisory_workspace_compare_router,
    advisory_workspace_version_lookups_router,
    advisory_workspace_replay_evidence_router,
    advisory_workspace_assistant_router,
    advisory_workspace_rationale_reviews_router,
    advisory_workspace_handoff_router,
)

ADVISORY_POLICY_ROUTERS: RouterGroup = (
    advisory_policy_router,
    advisory_policy_pack_detail_router,
    advisory_policy_actions_router,
    advisory_policy_evaluations_router,
    advisory_policy_review_queue_router,
    advisory_policy_evaluation_detail_router,
    advisory_policy_evaluation_evidence_router,
    advisory_policy_evaluation_workflow_router,
    advisory_policy_evaluation_actions_router,
    advisory_policy_evaluation_events_router,
    advisory_policy_evaluation_support_actions_router,
    advisory_policy_sign_off_decisions_router,
    advisory_policy_sign_off_package_router,
    advisory_policy_ai_evidence_router,
    advisory_policy_validation_router,
)

ADVISORY_COPILOT_ROUTERS: RouterGroup = (advisory_copilot_router,)

PROPOSAL_ROUTERS: RouterGroup = (
    proposal_generation_router,
    proposal_artifact_router,
    proposal_create_router,
    proposals_router,
    proposal_detail_router,
    proposal_discussion_pack_router,
    proposal_operations_router,
    proposal_operation_lookups_router,
    proposal_operation_support_lookups_router,
    proposal_idempotency_records_router,
    proposal_versions_router,
    proposal_version_async_router,
    proposal_version_commands_router,
    proposal_version_replay_evidence_router,
    proposal_workflow_router,
    proposal_workflow_decisions_router,
    proposal_risk_approval_router,
    proposal_risk_impact_router,
    proposal_approvals_router,
    proposal_lineage_router,
    proposal_client_consent_router,
    proposal_workflow_evidence_router,
    proposal_narrative_actions_router,
    proposal_narrative_reviews_router,
    proposal_narratives_router,
    proposal_delivery_router,
    proposal_delivery_events_router,
    proposal_report_requests_router,
    proposal_execution_router,
    proposal_execution_updates_router,
    proposal_execution_status_router,
    proposal_operation_correlation_router,
    proposal_memos_router,
    proposal_memo_detail_router,
    proposal_memo_evidence_router,
    proposal_memo_lineage_router,
    proposal_memo_replay_evidence_router,
    proposal_memo_actions_router,
    proposal_memo_ai_commentary_router,
    proposal_memo_reporting_router,
    proposal_memo_report_packages_router,
)
