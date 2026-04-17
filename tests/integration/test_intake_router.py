from fastapi.testclient import TestClient

from app.contracts.intake import EnvelopeResponse, LookupResponse
from app.main import app

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"
LOTUS_CORE_INGESTION_CLIENT = "app.clients.lotus_core_ingestion_client.LotusCoreIngestionClient"


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
        headers={"X-Idempotency-Key": "bundle-idem-1001"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["message"] == "queued"
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
    )

    assert response.status_code == 200
    assert captured["idempotency_key"] is None


def test_preview_upload_success(monkeypatch):
    async def _fake_preview(*args, **kwargs):
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
    )

    assert response.status_code == 200
    assert response.json()["data"]["entity_type"] == "portfolios"


def test_commit_upload_success(monkeypatch):
    async def _fake_commit(*args, **kwargs):
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
    )

    assert response.status_code == 200
    assert response.json()["data"]["published_rows"] == 1


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

    assert currency_response.status_code == 200
    assert currency_response.json()["items"][0]["id"] == "USD"


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


def test_upload_routes_preserve_form_payload_and_correlation_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_preview(self, entity_type, filename, content, sample_size, correlation_id):
        captured["preview"] = {
            "entity_type": entity_type,
            "filename": filename,
            "content": content,
            "sample_size": sample_size,
            "correlation_id": correlation_id,
        }
        return 200, {"entity_type": entity_type, "valid_rows": 1}

    async def _fake_commit(self, entity_type, filename, content, allow_partial, correlation_id):
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
    )
    commit_response = client.post(
        "/api/v1/intake/uploads/commit",
        data={"entityType": "portfolios", "allowPartial": "true"},
        files={"file": ("sample.csv", b"portfolio_id\nPF1\n", "text/csv")},
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
