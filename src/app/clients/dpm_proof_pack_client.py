from typing import Any

from app.clients.manage_write_authority import build_manage_write_headers


class DpmProofPackClientMixin:
    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _get_binary_text(
        self,
        path: str,
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, str, dict[str, Any]]:
        raise NotImplementedError

    async def generate_proof_pack(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/api/v1/rebalance/proof-packs",
            body=body,
            headers=build_manage_write_headers(
                correlation_id,
                extras={"Idempotency-Key": idempotency_key},
            ),
            operation="manage.rebalance.proof_packs.generate",
        )

    async def get_proof_pack(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proof-packs/{proof_pack_id}",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proof_packs.get",
        )

    async def get_proof_pack_markdown(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, str, dict[str, Any]]:
        return await self._get_binary_text(
            f"/api/v1/rebalance/proof-packs/{proof_pack_id}/summary.md",
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proof_packs.markdown",
        )

    async def get_proof_pack_report_input(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proof-packs/{proof_pack_id}/report-input",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proof_packs.report_input",
        )

    async def get_proof_pack_ai_evidence_input(
        self,
        proof_pack_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/api/v1/rebalance/proof-packs/{proof_pack_id}/ai-evidence-input",
            params={},
            headers=self._headers(correlation_id),
            operation="manage.rebalance.proof_packs.ai_evidence_input",
        )
