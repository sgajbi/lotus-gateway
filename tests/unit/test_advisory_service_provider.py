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
