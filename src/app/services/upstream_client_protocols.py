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
