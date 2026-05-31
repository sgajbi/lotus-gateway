from app.services.archive_document_service_factory import build_archive_document_service


def test_archive_document_service_factory_wires_archive_client_and_contract(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.archive_service_base_url",
        "http://archive:8000/",
    )
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.upstream_timeout_seconds",
        6.5,
    )
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.upstream_max_retries",
        4,
    )
    monkeypatch.setattr(
        "app.services.archive_client_factory.settings.upstream_retry_backoff_seconds",
        0.75,
    )
    monkeypatch.setattr(
        "app.services.archive_document_service_factory.settings.contract_version",
        "contract-test",
    )

    service = build_archive_document_service()

    assert service._archive_client._base_url == "http://archive:8000"
    assert service._archive_client._timeout == 6.5
    assert service._archive_client._max_retries == 4
    assert service._archive_client._retry_backoff_seconds == 0.75
    assert service._contract_version == "contract-test"
