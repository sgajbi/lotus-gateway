from typing import cast

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.services.dpm_service_provider import (
    dpm_command_center_service,
    dpm_construction_service,
    dpm_proof_pack_service,
    dpm_wave_service,
)


def test_dpm_service_provider_wires_manage_and_ai_backed_services(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.management_service_base_url",
        "http://manage-provider:8000",
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.ai_service_base_url",
        "http://ai-provider:8000",
    )

    command_center = dpm_command_center_service()
    construction = dpm_construction_service()
    proof_pack = dpm_proof_pack_service()
    wave = dpm_wave_service()

    assert command_center._dpm_client._base_url == "http://manage-provider:8000"
    assert cast(LotusAiClient, command_center._lotus_ai_client)._base_url == (
        "http://ai-provider:8000"
    )
    assert cast(DpmClient, construction._dpm_client)._base_url == "http://manage-provider:8000"
    assert cast(DpmClient, proof_pack._dpm_client)._base_url == "http://manage-provider:8000"
    assert cast(LotusAiClient, proof_pack._lotus_ai_client)._base_url == ("http://ai-provider:8000")
    assert wave._dpm_client._base_url == "http://manage-provider:8000"
    assert cast(LotusAiClient, wave._lotus_ai_client)._base_url == "http://ai-provider:8000"


def test_dpm_service_provider_reuses_services_for_unchanged_signature(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.management_service_base_url",
        "http://manage-provider-cache:8000",
    )

    first = dpm_command_center_service()
    second = dpm_command_center_service()

    assert first is second


def test_dpm_service_provider_rebuilds_when_manage_routing_changes(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.management_service_base_url",
        "http://manage-provider-a:8000",
    )
    first = dpm_wave_service()

    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.management_service_base_url",
        "http://manage-provider-b:8000",
    )
    second = dpm_wave_service()

    assert first is not second
    assert second._dpm_client._base_url == "http://manage-provider-b:8000"
