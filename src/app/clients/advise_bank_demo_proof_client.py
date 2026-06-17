from __future__ import annotations

from typing import Any


class AdviseBankDemoProofClientMixin:
    async def get_bank_demo_proof_scenario_contract(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/bank-demo-proof/scenario-contract",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.bank-demo-proof.scenario-contract",
        )

    async def get_bank_demo_supported_claim_register(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/advisory/bank-demo-proof/supported-claim-register",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.bank-demo-proof.supported-claim-register",
        )

    async def build_bank_demo_proof_pack(
        self,
        *,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/advisory/bank-demo-proof/proof-packs",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.bank-demo-proof.proof-packs",
        )

    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError
