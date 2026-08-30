import json
from pathlib import Path
from typing import Any

from app.main import app
from app.services.idea_source_error_policy import (
    PRESENTATION_RECEIPT_SOURCE_ERROR_MESSAGES,
)

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "upstream"
    / "lotus-idea-presentation-receipt.v1.json"
)


def _contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_openapi_publishes_exact_presentation_receipt_transport() -> None:
    contract = _contract()
    spec = app.openapi()
    operation = spec["paths"][contract["bffPath"]]["post"]
    request_schema = spec["components"]["schemas"]["IdeaCandidatePresentationReceiptRequest"]
    response_schema = spec["components"]["schemas"]["IdeaCandidatePresentationReceiptResponse"]
    evidence_schema = spec["components"]["schemas"]["IdeaPresentationReceiptEvidenceResponse"]

    assert request_schema["required"] == contract["requiredRequestFields"]
    assert request_schema["additionalProperties"] is False
    assert response_schema["properties"]["durableStorageBacked"]["const"] is True
    assert evidence_schema["properties"]["queueSnapshotDigest"]["pattern"].startswith("^sha256:")
    assert {int(status_code) for status_code in operation["responses"]} >= set(
        contract["successStatuses"]
    )
    assert (
        operation["responses"]["200"]["content"]["application/json"]["example"][
            "persistenceDecision"
        ]
        == "replayed"
    )
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/IdeaCandidatePresentationReceiptResponse"
    }
    assert (
        operation["responses"]["201"]["content"]["application/json"]["example"][
            "persistenceDecision"
        ]
        == "accepted"
    )


def test_presentation_receipt_contract_keeps_candidate_identity_in_the_path() -> None:
    contract = _contract()

    assert "candidateId" not in contract["requiredRequestFields"]
    assert "rankPolicy" not in contract["requiredRequestFields"]
    assert "scorePolicyVersion" not in contract["requiredRequestFields"]


def test_presentation_receipt_safe_problem_allowlist_matches_versioned_contract() -> None:
    safe_codes = {
        str(status_code): sorted(messages)
        for status_code, messages in PRESENTATION_RECEIPT_SOURCE_ERROR_MESSAGES.items()
    }

    assert safe_codes == {
        status_code: sorted(codes)
        for status_code, codes in _contract()["safeProblemCodesByStatus"].items()
    }
