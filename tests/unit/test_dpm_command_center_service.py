import pytest
from fastapi import HTTPException

from app.services.dpm_command_center_service import DpmCommandCenterService


class _FakeDpmClient:
    def __init__(self, result: tuple[int, dict]):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def create_outcome_review(self, body, correlation_id):  # noqa: ANN001
        self.calls.append({"method": "create", "body": body, "correlation_id": correlation_id})
        return self.result

    async def get_outcome_review_supportability(self, outcome_review_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "supportability",
                "outcome_review_id": outcome_review_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result


@pytest.mark.asyncio
async def test_dpm_command_center_preserves_manage_payload_and_supportability() -> None:
    manage_payload = {
        "outcome_review_id": "or_1",
        "state": "READY",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "expected_snapshot_hash": "sha256:expected",
        "supportability": {
            "state": "SUPPORTED",
            "reason_codes": ["READY_FOR_REPORT_INPUT"],
            "blocked_actions": [],
            "remediation_owner": "Portfolio Operations",
        },
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.create_outcome_review(
        body={"rebalance_run_id": "rr_1"},
        correlation_id="corr-1",
    )

    assert response.correlation_id == "corr-1"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.supportability.state == "SUPPORTED"
    assert response.supportability.reason_codes == ["READY_FOR_REPORT_INPUT"]
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "create",
            "body": {"rebalance_run_id": "rr_1"},
            "correlation_id": "corr-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_command_center_supportability_endpoint_handles_flat_payload() -> None:
    client = _FakeDpmClient(
        (
            200,
            {
                "state": "DEGRADED",
                "reasonCodes": ["SOURCE_STALE"],
                "blockedActions": ["CREATE_REPORT_INPUT"],
            },
        )
    )
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_outcome_review_supportability(
        outcome_review_id="or_1",
        correlation_id="corr-2",
    )

    assert response.supportability.state == "DEGRADED"
    assert response.supportability.reason_codes == ["SOURCE_STALE"]
    assert response.supportability.blocked_actions == ["CREATE_REPORT_INPUT"]


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["DEGRADED", "BLOCKED", "UNSUPPORTED", "UNAVAILABLE"])
async def test_dpm_command_center_preserves_manage_supportability_states(state: str) -> None:
    client = _FakeDpmClient(
        (
            200,
            {
                "outcome_review_id": "or_1",
                "supportability": {
                    "state": state,
                    "reason_codes": [f"{state}_REASON"],
                    "blocked_actions": ["CREATE_REPORT_INPUT"] if state == "BLOCKED" else [],
                },
            },
        )
    )
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.create_outcome_review(
        body={"rebalance_run_id": "rr_1"},
        correlation_id=f"corr-{state.lower()}",
    )

    assert response.supportability.state == state
    assert response.supportability.reason_codes == [f"{state}_REASON"]
    if state == "BLOCKED":
        assert response.supportability.blocked_actions == ["CREATE_REPORT_INPUT"]


@pytest.mark.asyncio
async def test_dpm_command_center_forwards_manage_errors_as_product_safe_detail() -> None:
    client = _FakeDpmClient((409, {"detail": "execution evidence incomplete"}))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.create_outcome_review(
            body={"rebalance_run_id": "rr_1"}, correlation_id="corr-3"
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 409,
        "error_code": "MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR",
        "detail": "execution evidence incomplete",
    }
