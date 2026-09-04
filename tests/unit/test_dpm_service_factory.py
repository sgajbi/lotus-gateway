from app.services.dpm_service_factory import (
    build_dpm_command_center_service,
    build_dpm_construction_service,
    build_dpm_proof_pack_service,
    build_dpm_wave_service,
    build_lotus_ai_client,
    build_manage_client,
    lotus_ai_client_signature,
    manage_client_signature,
)


def test_dpm_service_factory_builds_governed_manage_and_ai_clients(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.management_service_base_url",
        "http://manage:8000",
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.ai_service_base_url",
        "http://ai:8000",
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.upstream_timeout_seconds",
        6.5,
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.ai_service_timeout_seconds",
        55.0,
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.upstream_max_retries",
        4,
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.upstream_retry_backoff_seconds",
        0.75,
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.lotus_ai_caller_credential",
        "eyJhbGciOiJFZERTQSJ9.ops-issued.credential",
    )

    manage_client = build_manage_client()
    ai_client = build_lotus_ai_client()

    assert manage_client._base_url == "http://manage:8000"
    assert manage_client._timeout == 6.5
    assert manage_client._max_retries == 4
    assert manage_client._retry_backoff_seconds == 0.75
    assert ai_client._base_url == "http://ai:8000"
    assert ai_client._timeout == 55.0
    assert ai_client._max_retries == 4
    assert ai_client._retry_backoff_seconds == 0.75
    assert ai_client._caller_credential == "eyJhbGciOiJFZERTQSJ9.ops-issued.credential"
    assert manage_client_signature() == ("http://manage:8000", 6.5, 4, 0.75)
    assert lotus_ai_client_signature() == (
        "http://ai:8000",
        55.0,
        4,
        0.75,
        "eyJhbGciOiJFZERTQSJ9.ops-issued.credential",
    )


def test_dpm_service_factory_wires_all_dpm_route_services(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.management_service_base_url",
        "http://manage:8000",
    )
    monkeypatch.setattr(
        "app.services.dpm_service_factory.settings.ai_service_base_url",
        "http://ai:8000",
    )

    command_center = build_dpm_command_center_service()
    construction = build_dpm_construction_service()
    proof_pack = build_dpm_proof_pack_service()
    wave = build_dpm_wave_service()

    assert command_center._dpm_client._base_url == "http://manage:8000"
    assert command_center._lotus_ai_client._base_url == "http://ai:8000"
    assert construction._dpm_client._base_url == "http://manage:8000"
    assert proof_pack._dpm_client._base_url == "http://manage:8000"
    assert proof_pack._lotus_ai_client._base_url == "http://ai:8000"
    assert wave._dpm_client._base_url == "http://manage:8000"
    assert wave._lotus_ai_client._base_url == "http://ai:8000"
