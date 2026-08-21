from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from tests.shared.proposal_discussion_pack_payload import (
    build_discussion_pack_source_payloads,
)


def test_discussion_pack_route_binds_selected_identity_and_returns_closed_evidence(
    monkeypatch,
) -> None:
    payloads = build_discussion_pack_source_payloads()

    async def _get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        _ = self, proposal_id, include_evidence, correlation_id
        return 200, payloads["detail"]

    async def _get_narrative(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        _ = self, proposal_id, version_no, correlation_id
        return 200, payloads["narrative"]

    async def _get_memo(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        _ = self, proposal_id, version_no, correlation_id
        return 200, payloads["memo"]

    async def _get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        _ = self, proposal_id, correlation_id
        return 200, payloads["approvals"]

    async def _get_delivery(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        _ = self, proposal_id, correlation_id
        return 200, payloads["delivery"]

    monkeypatch.setattr("app.clients.advise_client.AdviseClient.get_proposal", _get_proposal)
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal_narrative",
        _get_narrative,
    )
    monkeypatch.setattr("app.clients.advise_client.AdviseClient.get_proposal_memo", _get_memo)
    monkeypatch.setattr("app.clients.advise_client.AdviseClient.get_approvals", _get_approvals)
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_delivery_summary",
        _get_delivery,
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/proposals/pp_discussion_001/discussion-pack-review",
            params={
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "version_no": 2,
            },
            headers={"X-Correlation-Id": "corr-discussion-router"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "proposal-discussion-pack-review.v1"
    assert body["correlation_id"] == "corr-discussion-router"
    assert body["data"]["narrative"]["review_state"] == "APPROVED_FOR_ADVISOR_USE"
    assert body["data"]["client_release"] == {
        "state": "blocked",
        "reason_code": "client_release_not_supported",
        "publication_supported": False,
        "delivery_supported": False,
        "explanation": (
            "Advisor-use narrative, memo, and report evidence is not client-release, publication, "
            "communication, or delivery authority."
        ),
    }


def test_discussion_pack_route_requires_portfolio_and_version_identity() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/proposals/pp_discussion_001/discussion-pack-review",
        )

    assert response.status_code == 422
    missing = {tuple(item["loc"]) for item in response.json()["detail"]}
    assert ("query", "portfolio_id") in missing
    assert ("query", "version_no") in missing
