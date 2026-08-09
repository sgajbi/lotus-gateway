from app.services.analytics_client_factory import (
    build_performance_analytics_client,
    build_risk_analytics_client,
    performance_analytics_client_signature,
    risk_analytics_client_signature,
)


def test_performance_analytics_client_factory_uses_performance_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_base_url",
        "http://performance:8000/",
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_timeout_seconds",
        7.5,
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_summary_deadline_seconds",
        28.0,
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.upstream_max_retries",
        4,
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.upstream_retry_backoff_seconds",
        0.75,
    )

    client = build_performance_analytics_client()

    assert client._base_url == "http://performance:8000"
    assert client._timeout == 7.5
    assert client._workspace_summary_deadline_seconds == 28.0
    assert client._max_retries == 4
    assert client._retry_backoff_seconds == 0.75
    assert performance_analytics_client_signature() == (
        "http://performance:8000/",
        7.5,
        28.0,
        4,
        0.75,
    )


def test_risk_analytics_client_factory_uses_risk_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.risk_analytics_base_url",
        "http://risk:8000/",
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.upstream_timeout_seconds",
        6.5,
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.upstream_max_retries",
        3,
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.upstream_retry_backoff_seconds",
        0.5,
    )

    client = build_risk_analytics_client()

    assert client._base_url == "http://risk:8000"
    assert client._timeout == 6.5
    assert client._max_retries == 3
    assert client._retry_backoff_seconds == 0.5
    assert risk_analytics_client_signature() == ("http://risk:8000/", 6.5, 3, 0.5)
