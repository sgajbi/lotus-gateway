from app.services.advise_client_factory import build_advise_client


def test_advise_client_factory_builds_configured_lotus_advise_client(monkeypatch) -> None:
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

    client = build_advise_client()

    assert client._base_url == "http://advise:8000"
    assert client._timeout == 6.5
    assert client._max_retries == 4
    assert client._retry_backoff_seconds == 0.75
