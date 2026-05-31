from app.services.advisory_service_factory import (
    build_advisor_cockpit_service,
    build_advisory_policy_service,
    build_advisory_workspace_service,
    build_bank_demo_proof_service,
    build_proposal_service,
)


def _set_advise_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.decisioning_service_base_url",
        "http://advise:8000/",
    )
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.upstream_timeout_seconds",
        6.5,
    )
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.upstream_max_retries",
        4,
    )
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.upstream_retry_backoff_seconds",
        0.75,
    )


def _assert_configured_advise_client(service: object) -> None:
    client = service._advise_client
    assert client._base_url == "http://advise:8000"
    assert client._timeout == 6.5
    assert client._max_retries == 4
    assert client._retry_backoff_seconds == 0.75


def test_advisory_service_factory_builds_configured_advise_backed_services(
    monkeypatch,
) -> None:
    _set_advise_settings(monkeypatch)

    services = (
        build_advisory_policy_service(),
        build_advisory_workspace_service(),
        build_advisor_cockpit_service(),
        build_bank_demo_proof_service(),
        build_proposal_service(),
    )

    for service in services:
        _assert_configured_advise_client(service)
