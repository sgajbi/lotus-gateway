from app.routers.platform import _platform_capabilities_service
from app.routers.proposals import _proposal_service
from app.routers.workbench import _workbench_service


def test_proposals_router_targets_advisory_base_url(monkeypatch):
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.decisioning_service_base_url",
        "http://advise:8000",
    )
    service = _proposal_service()
    assert service._advise_client._base_url == "http://advise:8000"


def test_workbench_router_targets_manage_for_runs_and_advise_for_proposals(monkeypatch):
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.decisioning_service_base_url",
        "http://advise:8000",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.management_service_base_url",
        "http://manage:8000",
    )
    service = _workbench_service()
    assert service._dpm_client._base_url == "http://manage:8000"
    assert service._advise_client._base_url == "http://advise:8000"


def test_workbench_router_cache_signature_changes_on_manage_or_advise_url(monkeypatch):
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.decisioning_service_base_url",
        "http://advise:8000",
    )
    monkeypatch.setattr(
        "app.services.workbench_service_factory.settings.management_service_base_url",
        "http://manage:8000",
    )
    service = _workbench_service()
    assert service._dpm_client._base_url == "http://manage:8000"
    assert service._advise_client._base_url == "http://advise:8000"


def test_platform_capabilities_keeps_manage_and_advise_clients_separate(monkeypatch):
    monkeypatch.setattr(
        "app.services.advise_client_factory.settings.decisioning_service_base_url",
        "http://advise:8000",
    )
    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.management_service_base_url",
        "http://manage:8000",
    )
    service = _platform_capabilities_service()
    assert service._advise_client._base_url == "http://advise:8000"
    assert service._manage_client._base_url == "http://manage:8000"


def test_platform_capabilities_uses_configured_source_timeout(monkeypatch):
    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.platform_capabilities_source_timeout_seconds",
        7.5,
    )
    service = _platform_capabilities_service()
    assert service._source_timeout_seconds == 7.5
