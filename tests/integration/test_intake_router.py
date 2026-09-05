from fastapi.testclient import TestClient

from app.contracts.intake import EnvelopeResponse, LookupResponse
from app.main import app

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"
LOTUS_CORE_INGESTION_CLIENT = "app.clients.lotus_core_ingestion_client.LotusCoreIngestionClient"

_TRUSTED_HEADERS = {
    "X-Actor-Id": "OPS_SG_001",
    "X-Tenant-Id": "tenant-sg",
    "X-Region": "APAC",
}


def test_ingest_portfolio_bundle_success(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_ingest(*args, **kwargs):
        captured.update(kwargs)
        return 202, {"message": "queued"}

    monkeypatch.setattr(
        f"{LOTUS_CORE_INGESTION_CLIENT}.ingest_portfolio_bundle",
        _fake_ingest,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/portfolio-bundle",
        json={"body": {"sourceSystem": "UI", "portfolios": []}},
        headers={"X-Idempotency-Key": "bundle-idem-1001", **_TRUSTED_HEADERS},
    )

    assert response.status_code == 200
    assert response.json()["data"]["message"] == "queued"
    assert captured["body"] == {"sourceSystem": "UI", "portfolios": []}
    assert isinstance(captured["correlation_id"], str)
    assert captured["idempotency_key"] == "bundle-idem-1001"


def test_ingest_portfolio_bundle_allows_missing_idempotency_header(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_ingest(*args, **kwargs):
        captured.update(kwargs)
        return 202, {"message": "queued"}

    monkeypatch.setattr(
        f"{LOTUS_CORE_INGESTION_CLIENT}.ingest_portfolio_bundle",
        _fake_ingest,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/portfolio-bundle",
        json={"body": {"sourceSystem": "UI", "portfolios": []}},
        headers=_TRUSTED_HEADERS,
    )

    assert response.status_code == 200
    assert captured["body"] == {"sourceSystem": "UI", "portfolios": []}
    assert isinstance(captured["correlation_id"], str)
    assert captured["idempotency_key"] is None
    assert captured["caller_headers"]["X-Tenant-Id"] == "tenant-sg"


def test_preview_upload_success(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_preview(*args, **kwargs):
        captured.update(kwargs)
        return 200, {"entity_type": "portfolios", "valid_rows": 1}

    monkeypatch.setattr(
        f"{LOTUS_CORE_INGESTION_CLIENT}.preview_upload",
        _fake_preview,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/uploads/preview",
        data={"entityType": "portfolios", "sampleSize": "20"},
        files={"file": ("sample.csv", b"portfolio_id\nPF1\n", "text/csv")},
        headers=_TRUSTED_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["data"]["entity_type"] == "portfolios"
    assert captured["entity_type"] == "portfolios"
    assert captured["filename"] == "sample.csv"
    assert captured["content"] == b"portfolio_id\nPF1\n"
    assert captured["sample_size"] == 20
    assert isinstance(captured["correlation_id"], str)


def test_commit_upload_success(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_commit(*args, **kwargs):
        captured.update(kwargs)
        return 202, {"entity_type": "portfolios", "published_rows": 1}

    monkeypatch.setattr(
        f"{LOTUS_CORE_INGESTION_CLIENT}.commit_upload",
        _fake_commit,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/uploads/commit",
        data={"entityType": "portfolios", "allowPartial": "true"},
        files={"file": ("sample.csv", b"portfolio_id\nPF1\n", "text/csv")},
        headers=_TRUSTED_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["data"]["published_rows"] == 1
    assert captured["entity_type"] == "portfolios"
    assert captured["filename"] == "sample.csv"
    assert captured["content"] == b"portfolio_id\nPF1\n"
    assert captured["allow_partial"] is True
    assert isinstance(captured["correlation_id"], str)


def test_upload_routes_apply_default_form_options(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_preview(
        self, entity_type, filename, content, sample_size, correlation_id, caller_headers=None
    ):
        captured["preview"] = {
            "entity_type": entity_type,
            "filename": filename,
            "content": content,
            "sample_size": sample_size,
            "correlation_id": correlation_id,
        }
        return 200, {"entity_type": entity_type, "valid_rows": 1}

    async def _fake_commit(
        self, entity_type, filename, content, allow_partial, correlation_id, caller_headers=None
    ):
        captured["commit"] = {
            "entity_type": entity_type,
            "filename": filename,
            "content": content,
            "allow_partial": allow_partial,
            "correlation_id": correlation_id,
        }
        return 202, {"entity_type": entity_type, "published_rows": 1}

    monkeypatch.setattr(f"{LOTUS_CORE_INGESTION_CLIENT}.preview_upload", _fake_preview)
    monkeypatch.setattr(f"{LOTUS_CORE_INGESTION_CLIENT}.commit_upload", _fake_commit)

    client = TestClient(app)

    preview_response = client.post(
        "/api/v1/intake/uploads/preview",
        data={"entityType": "transactions"},
        files={"file": ("transactions.csv", b"id,qty\n1,10\n", "text/csv")},
        headers=_TRUSTED_HEADERS,
    )
    commit_response = client.post(
        "/api/v1/intake/uploads/commit",
        data={"entityType": "transactions"},
        files={"file": ("transactions.csv", b"id,qty\n1,10\n", "text/csv")},
        headers=_TRUSTED_HEADERS,
    )

    assert preview_response.status_code == 200
    assert commit_response.status_code == 200
    preview_capture = captured["preview"]
    commit_capture = captured["commit"]
    assert isinstance(preview_capture, dict)
    assert isinstance(commit_capture, dict)
    assert preview_capture["entity_type"] == "transactions"
    assert preview_capture["filename"] == "transactions.csv"
    assert preview_capture["content"] == b"id,qty\n1,10\n"
    assert preview_capture["sample_size"] == 20
    assert isinstance(preview_capture["correlation_id"], str)
    assert commit_capture["entity_type"] == "transactions"
    assert commit_capture["filename"] == "transactions.csv"
    assert commit_capture["content"] == b"id,qty\n1,10\n"
    assert commit_capture["allow_partial"] is False
    assert isinstance(commit_capture["correlation_id"], str)


def test_lookups_success(monkeypatch):
    async def _fake_portfolios(*args, **kwargs):
        return 200, {"items": [{"id": "PF_1", "label": "PF_1"}]}

    async def _fake_instruments(*args, **kwargs):
        return 200, {"items": [{"id": "SEC_1", "label": "SEC_1 | Apple Inc."}]}

    async def _fake_currencies(*args, **kwargs):
        return 200, {"items": [{"id": "USD", "label": "USD"}]}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_lookups", _fake_portfolios)
    monkeypatch.setattr(
        f"{LOTUS_CORE_QUERY_CLIENT}.get_instrument_lookups",
        _fake_instruments,
    )
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_currency_lookups", _fake_currencies)

    client = TestClient(app)

    portfolio_response = client.get("/api/v1/lookups/portfolios")
    instrument_response = client.get("/api/v1/lookups/instruments?limit=50")
    currency_response = client.get("/api/v1/lookups/currencies")

    assert portfolio_response.status_code == 200
    assert portfolio_response.json()["items"][0]["id"] == "PF_1"

    assert instrument_response.status_code == 200
    assert instrument_response.json()["items"][0]["id"] == "SEC_1"
    instrument_body = LookupResponse.model_validate(instrument_response.json())
    assert instrument_body.items[0].label == "SEC_1 | Apple Inc."

    assert currency_response.status_code == 200
    assert currency_response.json()["items"][0]["id"] == "USD"
    currency_body = LookupResponse.model_validate(currency_response.json())
    assert currency_body.items[0].label == "USD"


def test_lookup_routes_preserve_query_filters_and_correlation_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_portfolios(self, correlation_id, **kwargs):
        captured["portfolio"] = {
            "correlation_id": correlation_id,
            **kwargs,
        }
        return 200, {"items": [{"id": "PF_1", "label": "PF_1"}]}

    async def _fake_instruments(self, limit, correlation_id, **kwargs):
        captured["instrument"] = {
            "limit": limit,
            "correlation_id": correlation_id,
            **kwargs,
        }
        return 200, {"items": [{"id": "SEC_1", "label": "SEC_1 | Apple Inc."}]}

    async def _fake_currencies(self, correlation_id, **kwargs):
        captured["currency"] = {
            "correlation_id": correlation_id,
            **kwargs,
        }
        return 200, {"items": [{"id": "USD", "label": "USD"}]}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_portfolio_lookups", _fake_portfolios)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_instrument_lookups", _fake_instruments)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_currency_lookups", _fake_currencies)

    client = TestClient(app)

    portfolio_response = client.get(
        "/api/v1/lookups/portfolios?cif_id=CIF_1001&booking_center=SG&q=Alpha&limit=25"
    )
    instrument_response = client.get(
        "/api/v1/lookups/instruments?limit=50&product_type=EQUITY&q=Apple"
    )
    currency_response = client.get(
        "/api/v1/lookups/currencies?instrument_page_limit=500&source=ALL&q=USD&limit=10"
    )

    assert portfolio_response.status_code == 200
    assert instrument_response.status_code == 200
    assert currency_response.status_code == 200

    portfolio_body = LookupResponse.model_validate(portfolio_response.json())
    instrument_body = LookupResponse.model_validate(instrument_response.json())
    currency_body = LookupResponse.model_validate(currency_response.json())

    assert captured["portfolio"] == {
        "correlation_id": portfolio_body.correlation_id,
        "cif_id": "CIF_1001",
        "booking_center": "SG",
        "q": "Alpha",
        "limit": 25,
    }
    assert captured["instrument"] == {
        "limit": 50,
        "correlation_id": instrument_body.correlation_id,
        "product_type": "EQUITY",
        "q": "Apple",
    }
    assert captured["currency"] == {
        "correlation_id": currency_body.correlation_id,
        "instrument_page_limit": 500,
        "source": "ALL",
        "q": "USD",
        "limit": 10,
    }


def test_lookup_routes_apply_default_query_options(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_instruments(self, limit, correlation_id, **kwargs):
        captured["instrument"] = {
            "limit": limit,
            "correlation_id": correlation_id,
            **kwargs,
        }
        return 200, {"items": [{"id": "SEC_1", "label": "SEC_1 | Apple Inc."}]}

    async def _fake_currencies(self, correlation_id, **kwargs):
        captured["currency"] = {
            "correlation_id": correlation_id,
            **kwargs,
        }
        return 200, {"items": [{"id": "USD", "label": "USD"}]}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_instrument_lookups", _fake_instruments)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_currency_lookups", _fake_currencies)

    client = TestClient(app)

    instrument_response = client.get("/api/v1/lookups/instruments")
    currency_response = client.get("/api/v1/lookups/currencies")

    assert instrument_response.status_code == 200
    assert currency_response.status_code == 200
    instrument_capture = captured["instrument"]
    currency_capture = captured["currency"]
    assert isinstance(instrument_capture, dict)
    assert isinstance(currency_capture, dict)
    assert instrument_capture["limit"] == 200
    assert instrument_capture["product_type"] is None
    assert instrument_capture["q"] is None
    assert isinstance(instrument_capture["correlation_id"], str)
    assert currency_capture["instrument_page_limit"] is None
    assert currency_capture["source"] is None
    assert currency_capture["q"] is None
    assert currency_capture["limit"] is None
    assert isinstance(currency_capture["correlation_id"], str)


def test_upload_routes_preserve_form_payload_and_correlation_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_preview(
        self, entity_type, filename, content, sample_size, correlation_id, caller_headers=None
    ):
        captured["preview"] = {
            "entity_type": entity_type,
            "filename": filename,
            "content": content,
            "sample_size": sample_size,
            "correlation_id": correlation_id,
        }
        return 200, {"entity_type": entity_type, "valid_rows": 1}

    async def _fake_commit(
        self, entity_type, filename, content, allow_partial, correlation_id, caller_headers=None
    ):
        captured["commit"] = {
            "entity_type": entity_type,
            "filename": filename,
            "content": content,
            "allow_partial": allow_partial,
            "correlation_id": correlation_id,
        }
        return 202, {"entity_type": entity_type, "published_rows": 1}

    monkeypatch.setattr(f"{LOTUS_CORE_INGESTION_CLIENT}.preview_upload", _fake_preview)
    monkeypatch.setattr(f"{LOTUS_CORE_INGESTION_CLIENT}.commit_upload", _fake_commit)

    client = TestClient(app)

    preview_response = client.post(
        "/api/v1/intake/uploads/preview",
        data={"entityType": "portfolios", "sampleSize": "15"},
        files={"file": ("sample.csv", b"portfolio_id\nPF1\n", "text/csv")},
        headers=_TRUSTED_HEADERS,
    )
    commit_response = client.post(
        "/api/v1/intake/uploads/commit",
        data={"entityType": "portfolios", "allowPartial": "true"},
        files={"file": ("sample.csv", b"portfolio_id\nPF1\n", "text/csv")},
        headers=_TRUSTED_HEADERS,
    )

    assert preview_response.status_code == 200
    assert commit_response.status_code == 200

    preview_body = EnvelopeResponse.model_validate(preview_response.json())
    commit_body = EnvelopeResponse.model_validate(commit_response.json())

    assert captured["preview"] == {
        "entity_type": "portfolios",
        "filename": "sample.csv",
        "content": b"portfolio_id\nPF1\n",
        "sample_size": 15,
        "correlation_id": preview_body.correlation_id,
    }
    assert captured["commit"] == {
        "entity_type": "portfolios",
        "filename": "sample.csv",
        "content": b"portfolio_id\nPF1\n",
        "allow_partial": True,
        "correlation_id": commit_body.correlation_id,
    }


def test_intake_writes_fail_closed_without_trusted_caller_context(monkeypatch):
    called: list[str] = []

    async def _fake_ingest(*args, **kwargs):
        called.append("ingest")
        return 202, {"message": "queued"}

    monkeypatch.setattr(f"{LOTUS_CORE_INGESTION_CLIENT}.ingest_portfolio_bundle", _fake_ingest)

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/portfolio-bundle",
        json={"body": {"sourceSystem": "UI", "portfolios": []}},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "missing_caller_context"
    assert called == []


def test_intake_upload_writes_forward_the_admitted_tenant(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_commit(*args, **kwargs):
        captured.update(kwargs)
        return 200, {"message": "committed"}

    monkeypatch.setattr(f"{LOTUS_CORE_INGESTION_CLIENT}.commit_upload", _fake_commit)

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/uploads/commit",
        data={"entityType": "portfolios", "allowPartial": "false"},
        files={"file": ("sample.csv", b"portfolio_id\nPF1\n", "text/csv")},
        headers=_TRUSTED_HEADERS,
    )

    assert response.status_code == 200
    assert captured["caller_headers"]["X-Tenant-Id"] == "tenant-sg"
    assert captured["caller_headers"]["X-Actor-Id"] == "OPS_SG_001"
