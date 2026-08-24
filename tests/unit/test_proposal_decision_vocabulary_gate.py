import base64
import copy
import json
from importlib import resources
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.contracts.proposal_decision_vocabulary import (
    load_proposal_decision_vocabulary,
    parse_proposal_decision_vocabulary,
)
from scripts.check_proposal_decision_vocabulary import (
    _decode_github_contents_envelope,
    _source_vocabulary,
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


def test_gate_rejects_an_implicit_packaged_self_comparison(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(SOURCE_URL_ENV, raising=False)
    args = SimpleNamespace(
        source_contract=None,
        source_url=None,
        allow_packaged_snapshot=False,
    )

    with pytest.raises(ValueError, match="current Advise proposal decision vocabulary is required"):
        _source_vocabulary(args)


def test_offline_snapshot_check_requires_an_explicit_opt_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(SOURCE_URL_ENV, raising=False)
    args = SimpleNamespace(
        source_contract=None,
        source_url=None,
        allow_packaged_snapshot=True,
    )

    vocabulary, revision = _source_vocabulary(args)

    assert vocabulary == load_proposal_decision_vocabulary()
    assert revision == "packaged-snapshot-explicit"


def test_protected_and_scheduled_lanes_reconcile_the_current_advise_artifact() -> None:
    workflow_root = REPO_ROOT / ".github" / "workflows"
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    make_gate = (
        "proposal-decision-vocabulary-gate:\n"
        "\tpython scripts/check_proposal_decision_vocabulary.py\n"
    )
    assert make_gate in makefile
    assert (make_gate.removesuffix("\n") + " --allow-packaged-snapshot") not in makefile
    assert "proposal-decision-vocabulary-snapshot-check:" in makefile
    protected_workflows = (
        "feature-lane.yml",
        "pr-merge-gate.yml",
        "main-releasability.yml",
    )
    for name in protected_workflows:
        source = (workflow_root / name).read_text(encoding="utf-8")
        assert SOURCE_URL_ENV in source
        assert "make lint" in source
        assert "--allow-packaged-snapshot" not in source

    drift_source = (workflow_root / "upstream-contract-drift.yml").read_text(encoding="utf-8")
    assert SOURCE_URL_ENV in drift_source
    assert "schedule:" in drift_source
    assert "lotus-advise-proposal-decision-vocabulary" in drift_source
    assert "make proposal-decision-vocabulary-gate" in drift_source
    assert "--allow-packaged-snapshot" not in drift_source
