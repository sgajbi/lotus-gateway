from typing import Any, Protocol


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
