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
    assert command_center._lotus_ai_client._base_url == "http://ai-provider:8000"
    assert construction._dpm_client._base_url == "http://manage-provider:8000"
    assert proof_pack._dpm_client._base_url == "http://manage-provider:8000"
    assert proof_pack._lotus_ai_client._base_url == "http://ai-provider:8000"
    assert wave._dpm_client._base_url == "http://manage-provider:8000"
    assert wave._lotus_ai_client._base_url == "http://ai-provider:8000"
