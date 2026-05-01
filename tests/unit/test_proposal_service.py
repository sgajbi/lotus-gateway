import pytest
from fastapi import HTTPException

from app.services.proposal_service import ProposalService


class _FakeAdviseClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def simulate_proposal(self, body: dict, idempotency_key: str, correlation_id: str):
        self.calls.append(
            (
                "simulate_proposal",
                {
                    "body": body,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {
            "proposal_run_id": "pr_1",
            "correlation_id": "corr_engine_1",
            "status": "READY",
            "before": {"portfolio_value": {"amount": "100000.00", "currency": "USD"}},
            "intents": [
                {
                    "intent_type": "CASH_FLOW",
                    "intent_id": "oi_cf_1",
                    "currency": "USD",
                    "amount": "2000.00",
                }
            ],
            "after_simulated": {"portfolio_value": {"amount": "102000.00", "currency": "USD"}},
            "reconciliation": {"cash_balance_delta": {"amount": "2000.00", "currency": "USD"}},
            "rule_results": [{"rule_id": "CASH_BAND", "severity": "SOFT", "status": "PASS"}],
            "explanation": {"summary": "Within mandate concentration limits."},
            "diagnostics": {
                "warnings": [],
                "data_quality": {"price_missing": [], "fx_missing": []},
            },
            "drift_analysis": {"tracking_error_pct": 1.2},
            "suitability": {"status": "PASS", "issues": []},
            "gate_decision": {
                "gate": "CLIENT_CONSENT_REQUIRED",
                "recommended_next_step": "REQUEST_CLIENT_CONSENT",
            },
            "lineage": {"request_hash": "sha256:req-1", "idempotency_key": "idem-simulate-1"},
        }

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
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "RISK_REVIEW",
            "latest_workflow_event": {
                "event_id": "pwe_2",
                "proposal_id": proposal_id,
                "event_type": "SUBMITTED_FOR_RISK_REVIEW",
                "from_state": "DRAFT",
                "to_state": "RISK_REVIEW",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:07:00+00:00",
                "reason": {"comment": "submit"},
            },
            "approval": None,
        }

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
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "AWAITING_CLIENT_CONSENT",
            "latest_workflow_event": {
                "event_id": "pwe_3",
                "proposal_id": proposal_id,
                "event_type": "COMPLIANCE_APPROVED",
                "from_state": "COMPLIANCE_REVIEW",
                "to_state": "AWAITING_CLIENT_CONSENT",
                "actor_id": body["actor_id"],
                "occurred_at": "2026-02-19T12:08:00+00:00",
                "reason": {},
                "related_version_no": body.get("related_version_no"),
            },
            "approval": {
                "approval_id": "pap_1",
                "proposal_id": proposal_id,
                "approval_type": body["approval_type"],
                "approved": True,
                "actor_id": body["actor_id"],
                "occurred_at": "2026-02-19T12:08:00+00:00",
                "details": body["details"],
                "related_version_no": body.get("related_version_no"),
            },
        }

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


class _FakeAdviseErrorClient(_FakeAdviseClient):
    async def record_approval(
        self, proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        _ = proposal_id, body, idempotency_key, correlation_id
        return 409, {"detail": "STATE_CONFLICT"}


@pytest.mark.asyncio
async def test_simulate_proposal_wraps_typed_simulation_payload() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    result = await service.simulate_proposal(
        body={"portfolio_snapshot": {"portfolio_id": "PF_1001"}},
        idempotency_key="idem-simulate-1",
        correlation_id="corr_0",
    )

    assert result.data.proposal_run_id == "pr_1"
    assert result.data.status == "READY"
    assert result.data.gate_decision["gate"] == "CLIENT_CONSENT_REQUIRED"
    assert result.data.lineage["idempotency_key"] == "idem-simulate-1"
    _, payload = client.calls[0]
    assert payload["idempotency_key"] == "idem-simulate-1"


@pytest.mark.asyncio
async def test_submit_proposal_maps_risk_transition() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

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

    assert result.data.current_state == "RISK_REVIEW"
    assert result.data.latest_workflow_event.event_type == "SUBMITTED_FOR_RISK_REVIEW"
    assert result.data.approval is None
    _, payload = client.calls[0]
    assert payload["body"]["event_type"] == "SUBMITTED_FOR_RISK_REVIEW"
    assert payload["idempotency_key"] == "idem-submit-1"


@pytest.mark.asyncio
async def test_approve_compliance_maps_approval_payload() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    result = await service.approve_compliance(
        proposal_id="pp_1",
        actor_id="compliance_1",
        expected_state="COMPLIANCE_REVIEW",
        details={"comment": "ok"},
        related_version_no=2,
        idempotency_key="idem-approval-1",
        correlation_id="corr_2",
    )

    assert result.data.current_state == "AWAITING_CLIENT_CONSENT"
    assert result.data.approval.approval_type == "COMPLIANCE"
    assert result.data.latest_workflow_event.event_type == "COMPLIANCE_APPROVED"
    _, payload = client.calls[0]
    assert payload["body"]["approval_type"] == "COMPLIANCE"
    assert payload["body"]["approved"] is True
    assert payload["idempotency_key"] == "idem-approval-1"


@pytest.mark.asyncio
async def test_list_proposals_wraps_typed_envelope() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    result = await service.list_proposals(
        filters={"portfolio_id": "PF_1001", "limit": 10},
        correlation_id="corr_list",
    )

    assert result.data.items[0].proposal_id == "pp_1"
    assert result.data.items[0].current_version_no == 1
    assert result.data.next_cursor == "pp_00042"


@pytest.mark.asyncio
async def test_create_proposal_and_version_wrap_typed_envelopes() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    async def _fake_create_proposal(body: dict, idempotency_key: str, correlation_id: str):
        _ = body, idempotency_key, correlation_id
        return 200, {
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 1,
            },
            "version": {
                "proposal_version_id": "ppv_1",
                "proposal_id": "pp_1",
                "version_no": 1,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_1", "status": "READY"},
                "artifact": {"artifact_id": "artifact_1"},
                "evidence_bundle": {},
            },
            "latest_workflow_event": {
                "event_id": "pwe_1",
                "proposal_id": "pp_1",
                "event_type": "CREATED",
                "from_state": None,
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:00:00+00:00",
                "reason": {},
            },
        }

    async def _fake_create_proposal_version(
        proposal_id: str, body: dict, idempotency_key: str, correlation_id: str
    ):
        _ = proposal_id, body, idempotency_key, correlation_id
        return 200, {
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 2,
            },
            "version": {
                "proposal_version_id": "ppv_2",
                "proposal_id": "pp_1",
                "version_no": 2,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
                "artifact": {"artifact_id": "artifact_2"},
                "evidence_bundle": {},
            },
            "latest_workflow_event": {
                "event_id": "pwe_2",
                "proposal_id": "pp_1",
                "event_type": "NEW_VERSION_CREATED",
                "from_state": "DRAFT",
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:06:00+00:00",
                "reason": {},
                "related_version_no": 2,
            },
        }

    client.create_proposal = _fake_create_proposal  # type: ignore[method-assign]
    client.create_proposal_version = _fake_create_proposal_version  # type: ignore[method-assign]

    create_result = await service.create_proposal(
        body={"created_by": "advisor_1"},
        idempotency_key="idem-create-1",
        correlation_id="corr-create",
    )
    version_result = await service.create_proposal_version(
        proposal_id="pp_1",
        body={"created_by": "advisor_1"},
        idempotency_key="idem-version-1",
        correlation_id="corr-version",
    )

    assert create_result.data.proposal.proposal_id == "pp_1"
    assert create_result.data.version.version_no == 1
    assert create_result.data.latest_workflow_event.event_type == "CREATED"
    assert version_result.data.proposal.current_version_no == 2
    assert version_result.data.version.version_no == 2
    assert version_result.data.latest_workflow_event.event_type == "NEW_VERSION_CREATED"


@pytest.mark.asyncio
async def test_get_proposal_and_version_wrap_typed_envelopes() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

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
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    events = await service.get_workflow_events(proposal_id="pp_1", correlation_id="corr_3")
    approvals = await service.get_approvals(proposal_id="pp_1", correlation_id="corr_3")

    assert events.data.current_state == "DRAFT"
    assert events.data.events[0].event_type == "CREATED"
    assert approvals.data.current_state == "AWAITING_CLIENT_CONSENT"
    assert approvals.data.approvals[0].approval_type == "RISK"


@pytest.mark.asyncio
async def test_get_proposal_lineage_wraps_envelope() -> None:
    client = _FakeAdviseClient()
    service = ProposalService(advise_client=client)

    lineage = await service.get_proposal_lineage(proposal_id="pp_1", correlation_id="corr_3")

    assert lineage.data.proposal.proposal_id == "pp_1"
    assert lineage.data.proposal_id == "pp_1"
    assert lineage.data.versions[0].version_no == 1


@pytest.mark.asyncio
async def test_approval_upstream_error_passthrough() -> None:
    service = ProposalService(advise_client=_FakeAdviseErrorClient())

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
