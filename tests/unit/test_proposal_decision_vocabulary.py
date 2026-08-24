import copy
import json
from importlib import resources
from pathlib import Path

import pytest

from app.contracts.proposal_decision_vocabulary import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    SOURCE_SERVICE,
    load_proposal_decision_vocabulary,
    parse_proposal_decision_vocabulary,
)


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


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("schema_version", "future", f"schema must be {SCHEMA_VERSION}"),
        ("contract_version", "future", f"contract must be {CONTRACT_VERSION}"),
        ("source_owner", {"service": "other"}, f"source must be {SOURCE_SERVICE}"),
    ),
)
def test_parser_rejects_unrecognized_contract_identity(
    field: str,
    value: object,
    message: str,
) -> None:
    payload = _source_payload()
    payload[field] = value

    with pytest.raises(ValueError, match=message):
        parse_proposal_decision_vocabulary(payload)


@pytest.mark.parametrize("value", (None, [], ["not-an-object"]))
def test_parser_rejects_invalid_decision_rule_collection(value: object) -> None:
    payload = _source_payload()
    payload["decision_statuses"] = value

    with pytest.raises(ValueError, match="decision_statuses must be a non-empty object list"):
        parse_proposal_decision_vocabulary(payload)


def test_parser_rejects_duplicate_workflow_gate() -> None:
    payload = _source_payload()
    gates = payload["workflow_gates"]
    assert isinstance(gates, list)
    gates.append(copy.deepcopy(gates[0]))

    with pytest.raises(ValueError, match="duplicate proposal workflow gate"):
        parse_proposal_decision_vocabulary(payload)


def test_parser_rejects_empty_source_authority() -> None:
    payload = _source_payload()
    source_owner = payload["source_owner"]
    assert isinstance(source_owner, dict)
    source_owner["authority"] = " "

    with pytest.raises(ValueError, match="authority must be a non-empty string"):
        parse_proposal_decision_vocabulary(payload)


@pytest.mark.parametrize("rule_modules", ([], ["module", "module"], [1]))
def test_parser_rejects_invalid_source_rule_modules(rule_modules: object) -> None:
    payload = _source_payload()
    source_owner = payload["source_owner"]
    assert isinstance(source_owner, dict)
    source_owner["rule_modules"] = rule_modules

    with pytest.raises(ValueError, match="rule_modules must"):
        parse_proposal_decision_vocabulary(payload)


def test_parser_rejects_decision_status_absent_from_gateway_types() -> None:
    payload = _source_payload()
    decisions = payload["decision_statuses"]
    assert isinstance(decisions, list)
    decisions[0]["status"] = "FUTURE_STATUS"

    with pytest.raises(ValueError, match="decision statuses differ from Gateway types"):
        parse_proposal_decision_vocabulary(payload)


def test_path_loader_reads_a_valid_caller_selected_artifact(
    tmp_path: Path,
) -> None:
    contract_path = tmp_path / "proposal-decision-vocabulary.json"
    contract_path.write_text(json.dumps(_source_payload()), encoding="utf-8")

    assert load_proposal_decision_vocabulary(contract_path) == load_proposal_decision_vocabulary()


def test_path_loader_rejects_non_object_json(tmp_path: Path) -> None:
    contract_path = tmp_path / "proposal-decision-vocabulary.json"
    contract_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a JSON object"):
        load_proposal_decision_vocabulary(contract_path)
