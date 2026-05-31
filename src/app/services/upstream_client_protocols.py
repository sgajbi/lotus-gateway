from typing import Any, Protocol


class DpmConstructionClient(Protocol):
    async def generate_construction_alternative_set(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_construction_alternative_set(
        self,
        *,
        alternative_set_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def select_construction_alternative(
        self,
        *,
        alternative_set_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class DpmProofPackClient(Protocol):
    async def generate_proof_pack(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proof_pack(
        self,
        *,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proof_pack_markdown(
        self,
        *,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, str, dict[str, Any]]: ...

    async def get_proof_pack_report_input(
        self,
        *,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proof_pack_ai_evidence_input(
        self,
        *,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class LotusAiWorkflowClient(Protocol):
    async def execute_workflow_pack(
        self,
        *,
        pack_id: str,
        version: str,
        environment: str,
        caller_identity_class: str,
        workflow_surface: str | None,
        task_request: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class BankDemoProofClient(Protocol):
    async def get_bank_demo_proof_scenario_contract(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_bank_demo_supported_claim_register(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def build_bank_demo_proof_pack(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class AdvisoryWorkspaceClient(Protocol):
    async def create_advisory_workspace(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisory_workspace(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def apply_advisory_workspace_draft_action(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def evaluate_advisory_workspace(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def save_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_advisory_workspace_saved_versions(
        self,
        *,
        workspace_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisory_workspace_saved_version_replay_evidence(
        self,
        *,
        workspace_id: str,
        workspace_version_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def resume_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def compare_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def request_advisory_workspace_rationale(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def review_advisory_workspace_rationale(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def handoff_advisory_workspace(
        self,
        *,
        workspace_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class AdvisorCockpitClient(Protocol):
    async def list_advisor_cockpit_actions(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_advisor_cockpit_preparation_packets(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisor_cockpit_action(
        self,
        *,
        action_item_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisor_cockpit_snapshot(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_advisor_cockpit_supportability(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def acknowledge_advisor_cockpit_action(
        self,
        *,
        action_item_id: str,
        body: dict[str, Any],
        params: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def evaluate_advisor_cockpit_house_view_cohort(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class AdvisoryPolicyClient(Protocol):
    async def list_policy_packs(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def validate_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def activate_policy_pack_version(
        self,
        *,
        policy_pack_id: str,
        policy_version: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_policy_evaluation(
        self,
        *,
        proposal_id: str,
        proposal_version_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_review_queue(
        self,
        *,
        evaluation_status: str | None,
        portfolio_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_evaluation(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def replay_policy_evaluation(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_policy_evaluation_event(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_evaluation_lineage(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_sign_off_package(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_policy_evaluation_workflow(
        self,
        *,
        evaluation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_policy_sign_off_decision(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def request_policy_report_package(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def request_policy_ai_evidence(
        self,
        *,
        evaluation_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class ProposalClient(Protocol):
    async def simulate_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_proposal_artifact(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_proposals(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_version(
        self,
        proposal_id: str,
        version_no: int,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_proposal_version(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_proposal_async(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_proposal_version_async(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_operation(
        self,
        operation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_operation_by_correlation(
        self,
        operation_correlation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_operation_replay_evidence(
        self,
        operation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def transition_proposal(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_approval(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_workflow_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_lineage(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_version_replay_evidence(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_idempotency_record(
        self,
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def regenerate_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def review_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_report_request(
        self,
        proposal_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_execution_handoff(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_delivery_summary(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_delivery_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_execution_status(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_execution_update(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_memo_projection(
        self,
        proposal_id: str,
        version_no: int,
        audience: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def review_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def record_proposal_memo_report_package_event(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def request_proposal_memo_report_package(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def request_proposal_memo_ai_commentary(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_memo_lineage(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_proposal_memo_replay_evidence(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class ReportingJobSubmissionClient(Protocol):
    async def submit_portfolio_review_job(
        self,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def submit_outcome_review_report_job(
        self,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class ReportingJobQueryClient(Protocol):
    async def list_report_jobs(
        self,
        *,
        filters: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_report_job(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_report_job_events(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_report_job_lineage(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def cancel_report_job(
        self,
        *,
        job_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_report_snapshot(
        self,
        *,
        snapshot_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_report_snapshot_lineage(
        self,
        *,
        snapshot_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class ReportingBatchSchedulerClient(Protocol):
    async def list_report_batch_schedules(
        self,
        *,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def run_due_report_batch_schedules(
        self,
        *,
        payload: dict[str, Any],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class ReportingBatchLifecycleClient(Protocol):
    async def create_report_batch(
        self,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_report_batch(
        self,
        *,
        batch_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_capabilities(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class ReportingBatchControlClient(Protocol):
    async def control_report_batch(
        self,
        *,
        batch_id: str,
        action: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_capabilities(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class ReportingPortfolioClient(Protocol):
    async def get_portfolio_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_portfolio_summary(
        self,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_portfolio_review(
        self,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class ArchiveDocumentClient(Protocol):
    async def get_document_metadata(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
        current: bool = False,
    ) -> tuple[int, dict[str, Any]]: ...

    async def download_document(
        self,
        *,
        document_id: str,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, bytes, dict[str, str], dict[str, Any]]: ...


class CompositePerformanceClient(Protocol):
    async def post_composite_twr(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_composite_inspection(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class SourceProductExecutionClient(Protocol):
    async def get_external_order_execution_acknowledgement(
        self,
        *,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class IntakeIngestionClient(Protocol):
    async def ingest_portfolio_bundle(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def preview_upload(
        self,
        *,
        entity_type: str,
        filename: str,
        content: bytes,
        sample_size: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def commit_upload(
        self,
        *,
        entity_type: str,
        filename: str,
        content: bytes,
        allow_partial: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class IntakeLookupClient(Protocol):
    async def get_portfolio_lookups(
        self,
        *,
        correlation_id: str,
        cif_id: str | None = None,
        booking_center: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_instrument_lookups(
        self,
        *,
        limit: int,
        correlation_id: str,
        product_type: str | None = None,
        q: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_currency_lookups(
        self,
        *,
        correlation_id: str,
        instrument_page_limit: int | None = None,
        source: str | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> tuple[int, dict[str, Any]]: ...


class RiskWorkspaceClient(Protocol):
    async def post_risk_calculate(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_risk_concentration(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_risk_drawdown(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_risk_rolling_metrics(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def post_risk_historical_attribution(
        self,
        *,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PlatformCapabilitiesSourceClient(Protocol):
    async def get_capabilities(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PlatformCapabilitiesCoreClient(PlatformCapabilitiesSourceClient, Protocol):
    async def get_effective_policy(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PlatformCapabilitiesRiskClient(Protocol):
    async def get_capabilities(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class FoundationCoreClient(Protocol):
    async def get_portfolio_lookups(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class FoundationPerformanceClient(Protocol):
    async def get_stateful_twr(
        self,
        portfolio_id: str,
        report_end_date: str,
        period: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class FoundationManageClient(Protocol):
    async def list_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class FoundationReportingClient(Protocol):
    async def get_portfolio_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PortfolioCoreClient(Protocol):
    async def list_portfolios(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_support_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def query_assets_under_management(
        self,
        *,
        correlation_id: str,
        portfolio_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_cash_balances(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_cashflow_projection(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        horizon_days: int,
    ) -> tuple[int, dict[str, Any]]: ...

    async def query_asset_allocation(
        self,
        *,
        correlation_id: str,
        portfolio_id: str,
        as_of_date: str | None,
        dimensions: list[str],
        reporting_currency: str | None = None,
        look_through_mode: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_positions(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_transactions(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: str,
        transaction_type: str | None,
        security_id: str | None,
        instrument_id: str | None,
        component_type: str | None,
        linked_transaction_group_id: str | None,
        fx_contract_id: str | None,
        swap_event_id: str | None,
        near_leg_group_id: str | None,
        far_leg_group_id: str | None,
        start_date: str | None,
        end_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_readiness(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_analytics_reference(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PortfolioPerformanceClient(Protocol):
    async def get_twr_analytics(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PortfolioManageClient(Protocol):
    async def list_runs(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_supportability_summary(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class WorkbenchCoreClient(Protocol):
    async def get_portfolio_analytics_reference(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_simulation_session(
        self,
        *,
        portfolio_id: str,
        created_by: str | None,
        ttl_hours: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def add_simulation_changes(
        self,
        *,
        session_id: str,
        changes: list[dict[str, Any]],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_core_snapshot(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_projected_positions(
        self,
        *,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_projected_summary(
        self,
        *,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class WorkbenchPerformanceClient(Protocol):
    async def get_twr_analytics(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class WorkbenchManageClient(Protocol):
    async def list_runs(
        self,
        *,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_supportability_summary(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class WorkbenchAdviseClient(Protocol):
    async def simulate_proposal(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class PerformanceWorkspaceAnalyticsClient(Protocol):
    async def get_workspace_summary(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        chart_frequency: str,
        detail_basis: str,
        benchmark_id: str | None,
        reporting_currency: str | None,
        segment: str,
        correlation_id: str,
        periods: list[dict[str, Any]] | None = None,
        include_detail_blocks: bool = False,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_twr_analytics(
        self,
        *,
        portfolio_id: str,
        report_end_date: str,
        report_start_date: str | None,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        correlation_id: str,
        analyses: list[dict[str, Any]] | None = None,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_mwr_analytics(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        window_start_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_contribution_analytics(
        self,
        *,
        portfolio_id: str,
        report_start_date: str,
        report_end_date: str,
        period: str,
        metric_basis: str,
        dimension: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_attribution_analytics(
        self,
        *,
        portfolio_id: str,
        report_start_date: str,
        report_end_date: str,
        period: str,
        metric_basis: str,
        benchmark_id: str | None,
        dimension: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_execution(
        self,
        *,
        calculation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_lineage(
        self,
        *,
        calculation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_lineage_artifact(
        self,
        *,
        calculation_id: str,
        artifact_name: str,
        correlation_id: str,
    ) -> tuple[int, bytes, str | None]: ...


class PerformanceWorkspaceCoreClient(Protocol):
    async def get_portfolio_analytics_reference(
        self,
        portfolio_id: str,
        as_of_date: str,
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_benchmark_assignment(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        reporting_currency: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_benchmark_catalog(
        self,
        *,
        as_of_date: str,
        correlation_id: str,
        benchmark_currency: str | None = None,
        benchmark_status: str | None = "active",
        benchmark_type: str | None = "composite",
    ) -> tuple[int, dict[str, Any]]: ...


class AdvisorBriefAiClient(Protocol):
    async def execute_workflow_pack(
        self,
        *,
        pack_id: str,
        version: str,
        environment: str,
        caller_identity_class: str,
        workflow_surface: str | None,
        task_request: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_observability_runtime_status(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_workflow_pack_run_consumer_view(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_workflow_pack_run_operator_profile(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_workflow_pack_task_flows(
        self,
        *,
        correlation_id: str,
        workflow_pack_id: str | None = None,
        caller: str | None = None,
        workflow_surface: str | None = None,
        limit: int = 25,
    ) -> tuple[int, dict[str, Any]]: ...

    async def apply_workflow_pack_run_review_action(
        self,
        *,
        run_id: str,
        correlation_id: str,
        request_payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]: ...


class AdvisorBriefAdviseClient(Protocol):
    async def get_platform_capabilities(
        self,
        *,
        consumer_system: str = "lotus-gateway",
        tenant_id: str = "default",
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class DpmCommandCenterClient(Protocol):
    async def get_command_center(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def run_monitoring_once(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_monitoring_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_monitoring_run(
        self,
        monitoring_run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_monitoring_exceptions(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def resolve_monitoring_exception(
        self,
        exception_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_mandate_by_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_mandate(
        self,
        mandate_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_mandate_health(
        self,
        mandate_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_mandate_diff(
        self,
        mandate_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def preview_outcome_review(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_outcome_review(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_outcome_reviews(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_outcome_review(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def refresh_outcome_review_sources(
        self,
        outcome_review_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_outcome_review_supportability(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_outcome_review_report_input(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_outcome_review_ai_evidence_input(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_run_outcome_review(
        self,
        rebalance_run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_wave_outcome_reviews(
        self,
        wave_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_portfolio_memory(
        self,
        portfolio_id: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def search_portfolio_memory(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def preview_pm_operating_quality_score_run(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_pm_operating_quality_score_run(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_pm_operating_quality_score_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_pm_operating_quality_score_run(
        self,
        score_run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def preview_pm_operating_quality_summary_invocation(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_pm_operating_quality_summary_invocation(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_pm_operating_quality_summary_invocations(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_pm_operating_quality_summary_invocation(
        self,
        summary_invocation_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def preview_pm_operating_quality_review_action(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_pm_operating_quality_review_action(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_pm_operating_quality_review_actions(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_pm_operating_quality_review_action(
        self,
        review_action_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def preview_pm_operating_quality_fairness_analysis(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_pm_operating_quality_fairness_analysis(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_pm_operating_quality_fairness_analyses(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_pm_operating_quality_fairness_analysis(
        self,
        fairness_analysis_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def put_pm_operating_quality_policy(
        self,
        policy_id: str,
        policy_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_pm_operating_quality_policies(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_pm_operating_quality_policy(
        self,
        policy_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...


class DpmWaveClient(Protocol):
    async def preview_wave(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_wave(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_waves(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def put_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_definitions(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition_lifecycle_events(
        self,
        campaign_id: str,
        campaign_version: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition_preview_readiness(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition_launch_history(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_definition_launch_package(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def launch_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def retire_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def supersede_campaign_definition(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def discover_campaigns(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_operating_queue(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_approval_inbox(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_workflow_board(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_assignment_plan(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_campaign_workflow_automation(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_approval_decisions(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_campaign_approval_decision(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_assignment_actions(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_campaign_assignment_action(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_assignment_tasks(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_campaign_assignment_task(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def transition_campaign_assignment_task(
        self,
        campaign_id: str,
        campaign_version: str,
        task_ref: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def list_campaign_maker_checker_controls(
        self,
        campaign_id: str,
        campaign_version: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def create_campaign_maker_checker_control(
        self,
        campaign_id: str,
        campaign_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave_items(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def source_check_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def simulate_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def select_wave_item(
        self,
        wave_id: str,
        wave_item_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def approve_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def stage_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def handoff_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def cancel_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave_proof_pack_posture(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave_supportability(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...

    async def get_wave_report_input(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]: ...
