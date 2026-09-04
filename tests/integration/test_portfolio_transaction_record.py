"""Exact transaction record lookup for URL rehydration (issue #570).

One bounded source read resolves one source-owned record. Cross-identity substitution
fails closed, and not-found, permission, invalid-request, and source-unavailable states
stay distinct for Workbench.
"""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.portfolio_service_provider import portfolio_service

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"


@pytest.fixture(autouse=True)
def _clear_upstream_cache():
    portfolio_service().clear_upstream_cache()
    yield
    portfolio_service().clear_upstream_cache()


_PORTFOLIO_ID = "PF_1001"
_TRANSACTION_ID = "TXN-2026-0777"
_RECORD_PATH = f"/api/v1/portfolio/portfolios/{_PORTFOLIO_ID}/transactions/{_TRANSACTION_ID}"


def _record_payload() -> dict[str, object]:
    return {
        "product_name": "TransactionLedgerWindow",
        "product_version": "v1",
        "portfolio_id": _PORTFOLIO_ID,
        "reporting_currency": "SGD",
        "transaction": {
            "transaction_id": _TRANSACTION_ID,
            "transaction_date": "2026-03-27T09:30:00Z",
            "settlement_date": "2026-03-31T00:00:00Z",
            "transaction_type": "BUY",
            "security_id": "EQ_1",
            "instrument_id": "INST_EQ_1",
            "quantity": 10.0,
            "price": 70.0,
            "gross_transaction_amount": 700.0,
            "currency": "USD",
            "net_cost": 700.0,
            "realized_gain_loss": 15.0,
        },
        "reason_codes": ["TRANSACTION_LEDGER_READY"],
        "missing_instrument_reference_count": 0,
        "missing_instrument_security_ids": [],
    }


def _stub_record(monkeypatch: pytest.MonkeyPatch, status_code: int, payload: dict[str, object]):
    calls: list[dict[str, object]] = []

    async def _record(self, **kwargs):
        calls.append(kwargs)
        return status_code, deepcopy(payload)

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_transaction_record", _record)
    return calls


def test_transaction_record_returns_exact_source_record_with_one_bounded_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _stub_record(monkeypatch, 200, _record_payload())

    response = TestClient(app).get(
        f"{_RECORD_PATH}?as_of_date=2026-03-27&reporting_currency=SGD",
        headers={"X-Correlation-Id": "corr-transaction-record"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == _PORTFOLIO_ID
    assert body["reporting_currency"] == "SGD"
    assert body["reason_codes"] == ["TRANSACTION_LEDGER_READY"]
    assert body["transaction"]["transaction_id"] == _TRANSACTION_ID
    assert body["transaction"]["transaction_type"] == "BUY"
    assert body["transaction"]["transaction_date"] == "2026-03-27T09:30:00Z"
    assert body["transaction"]["gross_amount"] == 700.0
    assert body["correlation_id"] == "corr-transaction-record"
    assert len(calls) == 1
    assert calls[0]["portfolio_id"] == _PORTFOLIO_ID
    assert calls[0]["transaction_id"] == _TRANSACTION_ID
    assert calls[0]["as_of_date"] == "2026-03-27"
    assert calls[0]["include_projected"] is False
    assert calls[0]["reporting_currency"] == "SGD"


@pytest.mark.parametrize(
    ("field", "changed_value"),
    (
        ("portfolio_id", "PF_OTHER"),
        ("transaction_id", "TXN-2026-9999"),
    ),
)
def test_transaction_record_rejects_source_identity_substitution(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    changed_value: str,
) -> None:
    payload = _record_payload()
    if field == "portfolio_id":
        payload["portfolio_id"] = changed_value
    else:
        payload["transaction"]["transaction_id"] = changed_value
    _stub_record(monkeypatch, 200, payload)

    response = TestClient(app).get(_RECORD_PATH)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "portfolio_transaction_record_identity_mismatch"


def test_transaction_record_rejects_success_without_record_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _record_payload()
    del payload["transaction"]
    _stub_record(monkeypatch, 200, payload)

    response = TestClient(app).get(_RECORD_PATH)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "portfolio_transaction_record_identity_mismatch"


@pytest.mark.parametrize(
    ("source_status", "expected_status", "expected_code"),
    (
        (404, 404, "portfolio_transaction_not_found"),
        (403, 403, "portfolio_transaction_access_denied"),
        (401, 403, "portfolio_transaction_access_denied"),
        (400, 400, "portfolio_transaction_request_invalid"),
        (422, 400, "portfolio_transaction_request_invalid"),
        (500, 502, "portfolio_transaction_source_unavailable"),
        (503, 502, "portfolio_transaction_source_unavailable"),
    ),
)
def test_transaction_record_keeps_source_failure_states_distinct(
    monkeypatch: pytest.MonkeyPatch,
    source_status: int,
    expected_status: int,
    expected_code: str,
) -> None:
    _stub_record(
        monkeypatch,
        source_status,
        {"detail": "postgres internals and tenant-secret evidence"},
    )

    response = TestClient(app).get(_RECORD_PATH)

    assert response.status_code == expected_status
    body = response.json()
    assert body["detail"]["code"] == expected_code
    assert "postgres" not in str(body)
    assert "tenant-secret" not in str(body)


def test_transaction_record_rejects_naive_source_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _record_payload()
    payload["transaction"]["transaction_date"] = "2026-03-27T09:30:00"
    _stub_record(monkeypatch, 200, payload)

    response = TestClient(app).get(_RECORD_PATH)

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "portfolio_transaction_source_contract_invalid"


def test_transaction_record_preserves_raw_record_without_restatement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _record_payload()
    payload["reporting_currency"] = None
    _stub_record(monkeypatch, 200, payload)

    response = TestClient(app).get(_RECORD_PATH)

    assert response.status_code == 200
    assert response.json()["reporting_currency"] is None
