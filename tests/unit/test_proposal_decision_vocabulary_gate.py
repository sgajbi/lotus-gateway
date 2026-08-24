import base64
import copy
import json
from importlib import resources
from pathlib import Path

import pytest

from app.contracts.proposal_decision_vocabulary import (
    load_proposal_decision_vocabulary,
    parse_proposal_decision_vocabulary,
)
from scripts.check_proposal_decision_vocabulary import (
    _decode_github_contents_envelope,
    compare_vocabularies,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_URL_ENV = "LOTUS_ADVISE_PROPOSAL_DECISION_VOCABULARY_URL"


def _source_payload() -> dict[str, object]:
    text = (
        resources.files("app.contracts.upstream")
        .joinpath("lotus_advise_proposal_decision_vocabulary.v1.json")
        .read_text(encoding="utf-8")
    )
    return copy.deepcopy(json.loads(text))


def test_comparator_names_the_changed_source_pairing() -> None:
    packaged = load_proposal_decision_vocabulary()
    payload = _source_payload()
    decisions = payload["decision_statuses"]
    assert isinstance(decisions, list)
    decisions[0]["allowed_workflow_gates"] = ["NONE"]
    changed = parse_proposal_decision_vocabulary(payload)

    assert compare_vocabularies(packaged, changed) == [
        "decision workflow gates differ for READY_FOR_CLIENT_REVIEW: "
        "packaged=['EXECUTION_READY', 'NONE'], source=['NONE']"
    ]


def test_github_contents_decoder_preserves_payload_and_blob_revision() -> None:
    payload = _source_payload()
    envelope = {
        "encoding": "base64",
        "sha": "source-blob-sha",
        "content": base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii"),
    }

    decoded, revision = _decode_github_contents_envelope(envelope)

    assert decoded == payload
    assert revision == "source-blob-sha"


@pytest.mark.parametrize(
    "envelope",
    (
        [],
        {"encoding": "none", "sha": "source-blob-sha", "content": "value"},
        {"encoding": "base64", "sha": "", "content": "e30="},
    ),
)
def test_github_contents_decoder_rejects_unverifiable_source(envelope: object) -> None:
    with pytest.raises(ValueError):
        _decode_github_contents_envelope(envelope)


def test_protected_and_scheduled_lanes_reconcile_the_current_advise_artifact() -> None:
    workflow_root = REPO_ROOT / ".github" / "workflows"
    protected_workflows = (
        "feature-lane.yml",
        "pr-merge-gate.yml",
        "main-releasability.yml",
    )
    for name in protected_workflows:
        source = (workflow_root / name).read_text(encoding="utf-8")
        assert SOURCE_URL_ENV in source
        assert "make lint" in source

    drift_source = (workflow_root / "upstream-contract-drift.yml").read_text(encoding="utf-8")
    assert SOURCE_URL_ENV in drift_source
    assert "schedule:" in drift_source
    assert "lotus-advise-proposal-decision-vocabulary" in drift_source
    assert "make proposal-decision-vocabulary-gate" in drift_source
