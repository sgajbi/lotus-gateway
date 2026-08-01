import pytest

from app.services.advisory_copilot_service import AdvisoryCopilotService


class _FakeAdvisoryCopilotClient:
    def __init__(self) -> None:
        self.review_calls: list[dict[str, object]] = []

    async def create_advisory_copilot_evidence_packet(self, **kwargs):  # noqa: ANN003
        raise AssertionError(kwargs)

    async def create_advisory_copilot_evidence_packet_from_proposal_version(
        self,
        **kwargs,  # noqa: ANN003
    ):
        raise AssertionError(kwargs)

    async def get_advisory_copilot_evidence_packet(self, **kwargs):  # noqa: ANN003
        raise AssertionError(kwargs)

    async def run_advisory_copilot_action(self, **kwargs):  # noqa: ANN003
        raise AssertionError(kwargs)

    async def get_advisory_copilot_run(self, **kwargs):  # noqa: ANN003
        assert kwargs == {
            "run_id": "copilot-run-001",
            "correlation_id": "corr-copilot-review",
        }
        return 200, {
            "run": {
                "run_id": "copilot-run-001",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "proposal_id": "proposal-001",
            }
        }

    async def review_advisory_copilot_run(self, **kwargs):  # noqa: ANN003
        self.review_calls.append(kwargs)
        return 200, {
            "run": {
                "run_id": "copilot-run-001",
                "review_posture": "APPROVED_FOR_INTERNAL_USE",
            }
        }

    async def get_advisory_copilot_supportability(self, **kwargs):  # noqa: ANN003
        raise AssertionError(kwargs)

    async def list_advisory_copilot_proposal_version_runs(self, **kwargs):  # noqa: ANN003
        raise AssertionError(kwargs)


@pytest.mark.asyncio
async def test_review_run_enriches_missing_resource_scope_from_advise_run() -> None:
    client = _FakeAdvisoryCopilotClient()
    service = AdvisoryCopilotService(advise_client=client)

    response = await service.review_run(
        run_id="copilot-run-001",
        body={"body": {"action": "APPROVE_FOR_INTERNAL_USE"}},
        idempotency_key="idem-copilot-review",
        caller_headers={
            "X-Actor-Id": "desk_head_sg_001",
            "X-Role": "ADVISORY_SUPERVISOR",
            "X-Tenant-Id": "tenant-sg-001",
            "X-Legal-Entity-Code": "PB_SG",
            "X-Service-Identity": "lotus-gateway",
            "X-Capabilities": "advisory.copilot.review",
            "X-Principal-Status": "ACTIVE",
        },
        correlation_id="corr-copilot-review",
    )

    assert response.data["run"]["review_posture"] == "APPROVED_FOR_INTERNAL_USE"
    assert client.review_calls == [
        {
            "run_id": "copilot-run-001",
            "body": {"action": "APPROVE_FOR_INTERNAL_USE"},
            "idempotency_key": "idem-copilot-review",
            "caller_headers": {
                "X-Actor-Id": "desk_head_sg_001",
                "X-Role": "ADVISORY_SUPERVISOR",
                "X-Tenant-Id": "tenant-sg-001",
                "X-Legal-Entity-Code": "PB_SG",
                "X-Service-Identity": "lotus-gateway",
                "X-Capabilities": "advisory.copilot.review",
                "X-Principal-Status": "ACTIVE",
                "X-Authorized-Portfolio-Id": "PB_SG_GLOBAL_BAL_001",
                "X-Authorized-Proposal-Id": "proposal-001",
            },
            "correlation_id": "corr-copilot-review",
        }
    ]
