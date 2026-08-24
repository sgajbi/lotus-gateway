import copy
import json
from importlib import resources

import pytest

from app.contracts.proposal_decision_vocabulary import parse_proposal_decision_vocabulary


def _source_payload() -> dict[str, object]:
    text = (
        resources.files("app.contracts.upstream")
        .joinpath("lotus_advise_proposal_decision_vocabulary.v1.json")
        .read_text(encoding="utf-8")
    )
    return copy.deepcopy(json.loads(text))


def test_parser_rejects_duplicate_decision_status() -> None:
    payload = _source_payload()
    decisions = payload["decision_statuses"]
    assert isinstance(decisions, list)
    decisions.append(copy.deepcopy(decisions[0]))

    with pytest.raises(ValueError, match="duplicate proposal decision status"):
        parse_proposal_decision_vocabulary(payload)


def test_parser_rejects_source_value_absent_from_gateway_types() -> None:
    payload = _source_payload()
    decisions = payload["decision_statuses"]
    assert isinstance(decisions, list)
    decisions[0]["allowed_workflow_gates"].append("UNREVIEWED_GATE")

    with pytest.raises(ValueError, match="absent from Gateway types.*UNREVIEWED_GATE"):
        parse_proposal_decision_vocabulary(payload)
