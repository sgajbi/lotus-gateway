from app.services.advisory_service_provider import (
    advisor_cockpit_service,
    advisory_policy_service,
    advisory_workspace_service,
    bank_demo_proof_service,
    proposal_service,
)


def test_advisory_service_provider_wires_advise_backed_services(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.decisioning_service_base_url",
        "http://advise-provider:8000",
    )

    services = (
        advisory_policy_service(),
        advisory_workspace_service(),
        advisor_cockpit_service(),
        bank_demo_proof_service(),
        proposal_service(),
    )

    for service in services:
        assert service._advise_client._base_url == "http://advise-provider:8000"


def test_advisory_service_provider_reuses_services_for_unchanged_signature(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.decisioning_service_base_url",
        "http://advise-provider-cache:8000",
    )

    first = advisory_policy_service()
    second = advisory_policy_service()

    assert first is second


def test_advisory_service_provider_rebuilds_when_advise_routing_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.decisioning_service_base_url",
        "http://advise-provider-a:8000",
    )
    first = proposal_service()

    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.decisioning_service_base_url",
        "http://advise-provider-b:8000",
    )
    second = proposal_service()

    assert first is not second
    assert second._advise_client._base_url == "http://advise-provider-b:8000"
