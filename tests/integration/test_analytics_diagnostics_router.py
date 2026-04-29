import logging

from fastapi.testclient import TestClient

from app.main import app


def _operator_headers(**overrides: str) -> dict[str, str]:
    headers = {
        "X-Actor-Id": "support-operator-1",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Role": "support-operator",
        "X-Correlation-Id": "corr-protected-diagnostics",
    }
    headers.update(overrides)
    return headers


def test_protected_analytics_diagnostics_lookup_returns_product_safe_posture(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = TestClient(app)

    response = client.get(
        "/api/v1/analytics-ui/diagnostics/gdiag-risk-summary-permission-blocked",
        headers=_operator_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "analytics-ui-diagnostics.v1"
    assert body["panel"] == "risk-summary"
    assert body["supportabilityState"] == "permission_blocked"
    assert body["safeDimensions"] == {
        "operation": "analytics.risk.calculate",
        "service": "lotus-risk",
        "state": "permission_blocked",
        "reason": "upstream_authorization_denied",
    }
    assert body["auditEvent"] == "gateway.analytics.audit.protected_diagnostics_lookup"
    assert "portfolio_id" in body["forbiddenFields"]
    assert "correlation_id" in body["forbiddenFields"]
    assert "PB_SG_GLOBAL_BAL_001" not in str(body)
    assert "trace-" not in str(body)

    audit_record = _protected_diagnostics_record(caplog.records)
    assert audit_record.extra_fields["event"] == (
        "gateway.analytics.audit.protected_diagnostics_lookup"
    )
    assert audit_record.extra_fields["reason"] == "lookup_succeeded"
    assert "support_reference" not in audit_record.extra_fields


def test_protected_analytics_diagnostics_lookup_requires_operator_role(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = TestClient(app)

    response = client.get(
        "/api/v1/analytics-ui/diagnostics/gdiag-risk-summary-permission-blocked",
        headers=_operator_headers(**{"X-Role": "advisor"}),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "operator_role_required"
    audit_record = _protected_diagnostics_record(caplog.records)
    assert audit_record.extra_fields["state"] == "permission_blocked"
    assert audit_record.extra_fields["reason"] == "operator_role_required"


def test_protected_analytics_diagnostics_lookup_requires_caller_context(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = TestClient(app)

    response = client.get(
        "/api/v1/analytics-ui/diagnostics/gdiag-risk-summary-permission-blocked",
        headers={"X-Role": "support-operator"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "missing_caller_context"
    audit_record = _protected_diagnostics_record(caplog.records)
    assert audit_record.extra_fields["reason"] == "missing_caller_context"
    assert "actor_id" not in audit_record.extra_fields


def test_protected_analytics_diagnostics_lookup_rejects_unsafe_reference(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = TestClient(app)

    response = client.get(
        "/api/v1/analytics-ui/diagnostics/bad%20reference",
        headers=_operator_headers(),
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_support_reference"
    audit_record = _protected_diagnostics_record(caplog.records)
    assert audit_record.extra_fields["reason"] == "invalid_support_reference"


def test_protected_analytics_diagnostics_lookup_rejects_raw_identifier_reference(caplog):
    caplog.set_level(logging.INFO, logger="analytics_ui.gateway")
    client = TestClient(app)

    response = client.get(
        "/api/v1/analytics-ui/diagnostics/PB_SG_GLOBAL_BAL_001",
        headers=_operator_headers(),
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_support_reference"
    audit_record = _protected_diagnostics_record(caplog.records)
    assert audit_record.extra_fields["reason"] == "invalid_support_reference"


def test_protected_analytics_diagnostics_lookup_is_documented_in_openapi():
    schema = app.openapi()
    route = schema["paths"]["/api/v1/analytics-ui/diagnostics/{support_reference}"]["get"]

    assert route["tags"] == ["Analytics Diagnostics"]
    assert route["summary"] == "Resolve protected analytics diagnostics posture"
    assert route["responses"]["200"]["content"]["application/json"]["example"]["auditEvent"] == (
        "gateway.analytics.audit.protected_diagnostics_lookup"
    )


def _protected_diagnostics_record(records):
    return next(
        record
        for record in records
        if record.name == "analytics_ui.gateway"
        and record.message == "gateway.analytics.audit.protected_diagnostics_lookup"
    )
