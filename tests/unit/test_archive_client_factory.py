from app.services.archive_client_factory import archive_client_signature, build_archive_client


def test_archive_client_factory_builds_configured_archive_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.archive_service_base_url",
        "http://archive:8000/",
    )
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.upstream_timeout_seconds",
        6.5,
    )
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.archive_access_preflight_timeout_seconds",
        3.0,
    )
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.upstream_max_retries",
        4,
    )
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.upstream_retry_backoff_seconds",
        0.75,
    )

    client = build_archive_client()

    assert client._base_url == "http://archive:8000"
    assert client._timeout == 6.5
    assert client._access_preflight_timeout == 3.0
    assert client._max_retries == 4
    assert client._retry_backoff_seconds == 0.75
    assert archive_client_signature() == ("http://archive:8000/", 6.5, 3.0, 4, 0.75)
