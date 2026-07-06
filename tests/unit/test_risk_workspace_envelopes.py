from app.services.risk_workspace_envelopes import (
    risk_metadata,
    risk_upstream_failure,
    unavailable_risk_service_supportability,
)


def test_risk_upstream_failure_preserves_dict_detail() -> None:
    failure = risk_upstream_failure(
        upstream_status=503,
        upstream_payload={"detail": "risk service unavailable", "debug": "not exposed"},
    )

    assert failure.source_service == "lotus-risk"
    assert failure.error_code == "HTTP_503"
    assert failure.detail == "risk request failed"


def test_risk_upstream_failure_bounds_structured_detail() -> None:
    failure = risk_upstream_failure(
        upstream_status=503,
        upstream_payload={
            "detail": {
                "code": "RISK_DOWN",
                "message": "risk service unavailable",
                "debug_payload": {
                    "client_name": "Private Client",
                    "token": "secret-token",
                },
            }
        },
    )

    assert failure.source_service == "lotus-risk"
    assert failure.error_code == "HTTP_503"
    assert failure.detail == "RISK_DOWN"
    assert "Private Client" not in str(failure)
    assert "secret-token" not in str(failure)


def test_risk_upstream_failure_handles_non_dict_payload() -> None:
    failure = risk_upstream_failure(
        upstream_status=502,
        upstream_payload="bad gateway",
    )

    assert failure.source_service == "lotus-risk"
    assert failure.error_code == "HTTP_502"
    assert failure.detail == "risk request failed"


def test_unavailable_risk_service_supportability_is_product_safe() -> None:
    supportability = unavailable_risk_service_supportability(
        reason="lotus-risk rolling endpoint is unavailable."
    )

    assert len(supportability) == 1
    assert supportability[0].key == "risk_service"
    assert supportability[0].label == "Risk service"
    assert supportability[0].state == "unavailable"
    assert supportability[0].source_service == "lotus-risk"
    assert supportability[0].reason == "lotus-risk rolling endpoint is unavailable."


def test_risk_metadata_preserves_methodology_when_supplied() -> None:
    metadata = risk_metadata(
        input_mode="stateful",
        cache_status="miss",
        methodology_version="lotus-risk",
    )

    assert metadata.input_mode == "stateful"
    assert metadata.cache_status == "miss"
    assert metadata.methodology_version == "lotus-risk"
    assert metadata.generated_at
