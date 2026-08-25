import pytest
from fastapi import HTTPException

from app.services.advisor_cockpit_service import AdvisorCockpitService
from tests.support.advisor_cockpit_fixtures import (
    advisor_action_item_payload,
    advisor_action_page_payload,
)

CALLER_HEADERS = {
    "X-Actor-Id": "advisor_sg_001",
    "X-Tenant-Id": "tenant-sg",
}


class _FakeAdviseClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.status = 200
        self.payload: dict[str, object] = advisor_action_page_payload()

    async def list_advisor_cockpit_actions(
        self,
        *,
        params: dict[str, object],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "list_advisor_cockpit_actions",
                {
                    "params": params,
                    "caller_headers": caller_headers,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def list_advisor_cockpit_preparation_packets(
        self,
        *,
        params: dict[str, object],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "list_advisor_cockpit_preparation_packets",
                {
                    "params": params,
                    "caller_headers": caller_headers,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def get_advisor_cockpit_action(
        self,
        *,
        action_item_id: str,
        params: dict[str, object],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "get_advisor_cockpit_action",
                {
                    "action_item_id": action_item_id,
                    "params": params,
                    "caller_headers": caller_headers,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def get_advisor_cockpit_snapshot(
        self,
        *,
        params: dict[str, object],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "get_advisor_cockpit_snapshot",
                {
                    "params": params,
                    "caller_headers": caller_headers,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def get_advisor_cockpit_supportability(
        self,
        *,
        params: dict[str, object],
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "get_advisor_cockpit_supportability",
                {
                    "params": params,
                    "caller_headers": caller_headers,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def acknowledge_advisor_cockpit_action(
        self,
        *,
        action_item_id: str,
        body: dict[str, object],
        params: dict[str, object],
        caller_headers: dict[str, str],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "acknowledge_advisor_cockpit_action",
                {
                    "action_item_id": action_item_id,
                    "body": body,
                    "params": params,
                    "caller_headers": caller_headers,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload

    async def evaluate_advisor_cockpit_house_view_cohort(
        self,
        *,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            (
                "evaluate_advisor_cockpit_house_view_cohort",
                {
                    "body": body,
                    "correlation_id": correlation_id,
                },
            )
        )
        return self.status, self.payload


@pytest.mark.asyncio
async def test_advisor_cockpit_service_preserves_advise_owned_action_posture() -> None:
    advise_client = _FakeAdviseClient()
    service = AdvisorCockpitService(advise_client=advise_client)

    response = await service.list_actions(
        params={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "advisor_id": "advisor_sg_001",
            "role": "ADVISOR",
        },
        caller_headers=CALLER_HEADERS,
        correlation_id="corr-cockpit-list",
    )

    assert response.correlation_id == "corr-cockpit-list"
    assert response.data.items[0].action_item_id == "cockpit_action_001"
    assert response.data.items[0].owner_role == "COMPLIANCE_REVIEWER"
    assert response.data.items[0].unsupported_capabilities == ["CLIENT_READY_PUBLICATION"]
    assert response.data.page_size == 25
    assert advise_client.calls == [
        (
            "list_advisor_cockpit_actions",
            {
                "params": {
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "advisor_id": "advisor_sg_001",
                    "role": "ADVISOR",
                },
                "caller_headers": CALLER_HEADERS,
                "correlation_id": "corr-cockpit-list",
            },
        )
    ]


@pytest.mark.asyncio
async def test_advisor_cockpit_service_projects_action_detail_without_recomputing_posture() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.payload = advisor_action_item_payload()
    service = AdvisorCockpitService(advise_client=advise_client)

    response = await service.get_action(
        action_item_id="cockpit_action_001",
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
        caller_headers=CALLER_HEADERS,
        correlation_id="corr-cockpit-detail",
    )

    assert response.correlation_id == "corr-cockpit-detail"
    assert response.data.action_item_id == "cockpit_action_001"
    assert response.data.status == "PENDING_REVIEW"
    assert response.data.next_required_action.startswith("Review policy evaluation")
    assert advise_client.calls[0][0] == "get_advisor_cockpit_action"


@pytest.mark.asyncio
async def test_advisor_cockpit_service_fails_closed_on_malformed_success_payload() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.payload = {"items": [{"action_item_id": "unsafe-source-detail"}]}
    service = AdvisorCockpitService(advise_client=advise_client)

    with pytest.raises(HTTPException) as exc:
        await service.list_actions(
            params={},
            caller_headers=CALLER_HEADERS,
            correlation_id="corr-cockpit-invalid",
        )

    assert exc.value.status_code == 502
    assert exc.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 200,
        "error_code": "ADVISE_COCKPIT_ACTION_CONTRACT_INVALID",
        "detail": "lotus-advise advisor cockpit action data did not match the governed contract.",
    }
    assert "unsafe-source-detail" not in str(exc.value.detail)


@pytest.mark.asyncio
async def test_advisor_cockpit_service_preserves_advise_owned_preparation_packets() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.payload = {
        "items": [
            {
                "packet_id": "prep_packet_PB_SG_GLOBAL_BAL_001",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "meeting_posture": "READY_WITH_REVIEW_ITEMS",
                "memo_evidence_refs": ["memo:proposal_001:v1"],
                "policy_posture": "PENDING_REVIEW",
                "client_ready_publication": "BLOCKED",
            }
        ],
        "supportability": {
            "gateway_posture": "SUPPORTED_BY_LOTUS_GATEWAY_RFC0026",
            "client_ready_publication": "BLOCKED",
        },
    }
    service = AdvisorCockpitService(advise_client=advise_client)

    response = await service.list_preparation_packets(
        params={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "advisor_id": "advisor_sg_001",
            "role": "ADVISOR",
            "limit": 10,
        },
        caller_headers=CALLER_HEADERS,
        correlation_id="corr-cockpit-prep",
    )

    assert response.correlation_id == "corr-cockpit-prep"
    assert response.data == advise_client.payload
    assert response.data["items"][0]["client_ready_publication"] == "BLOCKED"
    assert advise_client.calls == [
        (
            "list_advisor_cockpit_preparation_packets",
            {
                "params": {
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "advisor_id": "advisor_sg_001",
                    "role": "ADVISOR",
                    "limit": 10,
                },
                "caller_headers": CALLER_HEADERS,
                "correlation_id": "corr-cockpit-prep",
            },
        )
    ]


@pytest.mark.asyncio
async def test_advisor_cockpit_service_preserves_house_view_cohort_product() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.payload = {
        "product_name": "TacticalHouseViewAffectedCohort",
        "affected_portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
        "supportability": {"state": "READY"},
    }
    service = AdvisorCockpitService(advise_client=advise_client)
    body = {
        "tactical_view": {"tactical_view_id": "thv_2026_05_asia_duration"},
        "candidate_portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
    }

    response = await service.evaluate_house_view_cohort(
        body=body,
        correlation_id="corr-house-view",
    )

    assert response.data == advise_client.payload
    assert advise_client.calls == [
        (
            "evaluate_advisor_cockpit_house_view_cohort",
            {
                "body": body,
                "correlation_id": "corr-house-view",
            },
        )
    ]


@pytest.mark.asyncio
async def test_advisor_cockpit_service_maps_acknowledgement_conflict_to_safe_detail() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.status = 409
    advise_client.payload = {
        "detail": "ADVISOR_COCKPIT_ACKNOWLEDGEMENT_IDEMPOTENCY_CONFLICT",
        "portfolio_id": "PB_SENSITIVE",
        "advisor_id": "advisor_sensitive",
    }
    service = AdvisorCockpitService(advise_client=advise_client)

    with pytest.raises(HTTPException) as exc:
        await service.acknowledge_action(
            action_item_id="cockpit_action_001",
            body={"action_item_version": 1, "acknowledged_by": "advisor_sg_001"},
            params={"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
            caller_headers=CALLER_HEADERS,
            idempotency_key="idem-cockpit-ack",
            correlation_id="corr-cockpit-ack",
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 409,
        "error_code": "ADVISE_COCKPIT_UPSTREAM_ERROR",
        "detail": "ADVISOR_COCKPIT_ACKNOWLEDGEMENT_IDEMPOTENCY_CONFLICT",
    }
    assert advise_client.calls == [
        (
            "acknowledge_advisor_cockpit_action",
            {
                "action_item_id": "cockpit_action_001",
                "body": {"action_item_version": 1, "acknowledged_by": "advisor_sg_001"},
                "params": {"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
                "caller_headers": CALLER_HEADERS,
                "idempotency_key": "idem-cockpit-ack",
                "correlation_id": "corr-cockpit-ack",
            },
        )
    ]
