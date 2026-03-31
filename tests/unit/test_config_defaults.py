from app.config import Settings


def test_settings_default_to_canonical_dev_service_identities():
    settings = Settings(
        _env_file=None,
        _env_prefix="__LOTUS_GATEWAY_TEST_UNUSED__",
    )

    assert settings.decisioning_service_base_url == "http://advise.dev.lotus"
    assert settings.portfolio_data_query_base_url == "http://core-query.dev.lotus"
    assert settings.portfolio_data_control_plane_base_url == "http://core-query.dev.lotus"
    assert settings.portfolio_data_ingestion_base_url == "http://core-ingestion.dev.lotus"
    assert settings.performance_analytics_base_url == "http://performance.dev.lotus"
    assert settings.risk_analytics_base_url == "http://risk.dev.lotus"
    assert settings.reporting_aggregation_base_url == "http://report.dev.lotus"
    assert settings.management_service_base_url == "http://manage.dev.lotus"
