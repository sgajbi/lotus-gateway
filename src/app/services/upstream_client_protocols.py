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
