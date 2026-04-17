import pytest
from fastapi import HTTPException

from app.services.proposal_service import ProposalService


class _FakeDpmClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def list_proposals(self, params: dict, correlation_id: str):
        self.calls.append(("list_proposals", {"params": params, "correlation_id": correlation_id}))
        return 200, {
            "items": [
                {
                    "proposal_id": "pp_1",
                    "portfolio_id": "PF_1001",
                    "current_state": "DRAFT",
                    "current_version_no": 1,
                    "created_by": "advisor_1",
                }
            ],
            "next_cursor": "pp_00042",
        }

    async def get_proposal(self, proposal_id: str, include_evidence: bool, correlation_id: str):
        self.calls.append(
            (
                "get_proposal",
                {
                    "proposal_id": proposal_id,
                    "include_evidence": include_evidence,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {
                "proposal_id": proposal_id,
                "portfolio_id": "PF_1001",
                "current_state": "RISK_REVIEW",
                "current_version_no": 2,
                "created_by": "advisor_1",
            },
            "current_version": {
                "proposal_version_id": "ppv_2",
                "proposal_id": proposal_id,
                "version_no": 2,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
                "artifact": {"artifact_id": "artifact_2"},
                "evidence_bundle": {"hashes": {"request_hash": "sha256:req-2"}},
            },
            "last_gate_decision": {
                "gate": "CLIENT_CONSENT_REQUIRED",
                "recommended_next_step": "REQUEST_CLIENT_CONSENT",
            },
        }

    async def get_proposal_version(
        self, proposal_id: str, version_no: int, include_evidence: bool, correlation_id: str
    ):
        self.calls.append(
            (
                "get_proposal_version",
                {
                    "proposal_id": proposal_id,
                    "version_no": version_no,
                    "include_evidence": include_evidence,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_version_id": "ppv_2",
            "proposal_id": proposal_id,
            "version_no": version_no,
            "created_at": "2026-02-19T12:06:00+00:00",
            "request_hash": "sha256:req-2",
            "artifact_hash": "sha256:artifact-2",
            "simulation_hash": "sha256:sim-2",
            "status_at_creation": "READY",
            "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
            "artifact": {"artifact_id": "artifact_2"},
            "evidence_bundle": {"hashes": {"request_hash": "sha256:req-2"}},
            "gate_decision": {"gate": "EXECUTION_READY", "recommended_next_step": "EXECUTE"},
        }

    async def transition_proposal(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        self.calls.append(
            (
                "transition_proposal",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"current_state": "RISK_REVIEW"}

    async def record_approval(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        self.calls.append(
            (
                "record_approval",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"current_state": "AWAITING_CLIENT_CONSENT"}

    async def get_workflow_events(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_workflow_events",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "DRAFT",
            "events": [
                {
                    "event_id": "pwe_1",
                    "proposal_id": proposal_id,
                    "event_type": "CREATED",
                    "from_state": None,
                    "to_state": "DRAFT",
                    "actor_id": "advisor_1",
                    "occurred_at": "2026-02-19T12:00:00+00:00",
                    "reason": {},
                }
            ],
        }

    async def get_approvals(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_approvals",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "AWAITING_CLIENT_CONSENT",
            "approvals": [
                {
                    "approval_id": "pap_1",
                    "proposal_id": proposal_id,
                    "approval_type": "RISK",
                    "approved": True,
                    "actor_id": "risk_1",
                    "occurred_at": "2026-02-19T12:07:00+00:00",
                    "details": {"comment": "Within mandate"},
                }
            ],
        }

    async def get_proposal_lineage(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_proposal_lineage",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal": {
                "proposal_id": proposal_id,
                "portfolio_id": "PF_1001",
                "current_state": "AWAITING_CLIENT_CONSENT",
                "current_version_no": 2,
            },
            "proposal_id": proposal_id,
            "versions": [
                {
                    "proposal_version_id": "ppv_1",
                    "version_no": 1,
                    "request_hash": "sha256:req-1",
                    "simulation_hash": "sha256:sim-1",
                    "artifact_hash": "sha256:artifact-1",
                }
            ],
        }


class _FakeDpmErrorClient(_FakeDpmClient):
    async def record_approval(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        _ = proposal_id, body, idempotency_key, correlation_id
        return 409, {"detail": "STATE_CONFLICT"}


@pytest.mark.asyncio
async def test_submit_proposal_maps_risk_transition() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    result = await service.submit_proposal(
        proposal_id="pp_1",
        actor_id="advisor_1",
        expected_state="DRAFT",
        review_type="RISK",
        reason={"comment": "submit"},
        related_version_no=1,
        idempotency_key="idem-submit-1",
        correlation_id="corr_1",
    )

    assert result.data["current_state"] == "RISK_REVIEW"
    _, payload = client.calls[0]
    assert payload["body"]["event_type"] == "SUBMITTED_FOR_RISK_REVIEW"
    assert payload["idempotency_key"] == "idem-submit-1"


@pytest.mark.asyncio
async def test_approve_compliance_maps_approval_payload() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    await service.approve_compliance(
        proposal_id="pp_1",
        actor_id="compliance_1",
        expected_state="COMPLIANCE_REVIEW",
        details={"comment": "ok"},
        related_version_no=2,
        idempotency_key="idem-approval-1",
        correlation_id="corr_2",
    )

    _, payload = client.calls[0]
    assert payload["body"]["approval_type"] == "COMPLIANCE"
    assert payload["body"]["approved"] is True
    assert payload["idempotency_key"] == "idem-approval-1"


@pytest.mark.asyncio
async def test_list_proposals_wraps_typed_envelope() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    result = await service.list_proposals(
        filters={"portfolio_id": "PF_1001", "limit": 10},
        correlation_id="corr_list",
    )

    assert result.data.items[0].proposal_id == "pp_1"
    assert result.data.items[0].current_version_no == 1
    assert result.data.next_cursor == "pp_00042"


@pytest.mark.asyncio
async def test_get_proposal_and_version_wrap_typed_envelopes() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    detail = await service.get_proposal(
        proposal_id="pp_1",
        include_evidence=True,
        correlation_id="corr_detail",
    )
    version = await service.get_proposal_version(
        proposal_id="pp_1",
        version_no=2,
        include_evidence=True,
        correlation_id="corr_version",
    )

    assert detail.data.proposal.proposal_id == "pp_1"
    assert detail.data.current_version.version_no == 2
    assert detail.data.last_gate_decision["gate"] == "CLIENT_CONSENT_REQUIRED"
    assert version.data.proposal_id == "pp_1"
    assert version.data.gate_decision["gate"] == "EXECUTION_READY"


@pytest.mark.asyncio
async def test_get_workflow_events_and_approvals_wrap_typed_envelopes() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    events = await service.get_workflow_events(proposal_id="pp_1", correlation_id="corr_3")
    approvals = await service.get_approvals(proposal_id="pp_1", correlation_id="corr_3")

    assert events.data.current_state == "DRAFT"
    assert events.data.events[0].event_type == "CREATED"
    assert approvals.data.current_state == "AWAITING_CLIENT_CONSENT"
    assert approvals.data.approvals[0].approval_type == "RISK"


@pytest.mark.asyncio
async def test_get_proposal_lineage_wraps_envelope() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    lineage = await service.get_proposal_lineage(proposal_id="pp_1", correlation_id="corr_3")

    assert lineage.data.proposal.proposal_id == "pp_1"
    assert lineage.data.proposal_id == "pp_1"
    assert lineage.data.versions[0].version_no == 1


@pytest.mark.asyncio
async def test_approval_upstream_error_passthrough() -> None:
    service = ProposalService(dpm_client=_FakeDpmErrorClient())

    try:
        await service.approve_risk(
            proposal_id="pp_1",
            actor_id="risk_1",
            expected_state="RISK_REVIEW",
            details={},
            related_version_no=None,
            idempotency_key="idem-risk-1",
            correlation_id="corr_4",
        )
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "STATE_CONFLICT" in str(exc.detail)
        return

    raise AssertionError("Expected HTTPException")
