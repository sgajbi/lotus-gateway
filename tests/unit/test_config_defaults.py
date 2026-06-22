import os
from pathlib import Path

import pytest

from app.config import Settings


def test_settings_default_to_canonical_dev_service_identities():
    settings = Settings(
        _env_file=None,
        _env_prefix="__LOTUS_GATEWAY_TEST_UNUSED__",
    )

    assert settings.decisioning_service_base_url == "http://advise.dev.lotus"
    assert settings.portfolio_data_query_base_url == "http://core-query.dev.lotus"
    assert settings.portfolio_data_control_plane_base_url == "http://core-control.dev.lotus"
    assert settings.portfolio_data_ingestion_base_url == "http://core-ingestion.dev.lotus"
    assert settings.performance_analytics_base_url == "http://performance.dev.lotus"
    assert settings.ai_service_base_url == "http://ai.dev.lotus"
    assert settings.ai_service_timeout_seconds == 45.0
    assert settings.risk_analytics_base_url == "http://risk.dev.lotus"
    assert settings.reporting_aggregation_base_url == "http://report.dev.lotus"
    assert settings.archive_service_base_url == "http://archive.dev.lotus"
    assert settings.idea_service_base_url == "http://idea.dev.lotus"
    assert settings.management_service_base_url == "http://manage.dev.lotus"
    assert Path(settings.domain_product_catalog_path).parts[-3:] == (
        "lotus-platform",
        "generated",
        "domain-product-catalog.json",
    )
    assert Path(settings.domain_product_dependency_graph_path).parts[-3:] == (
        "lotus-platform",
        "generated",
        "domain-product-dependency-graph.json",
    )


def test_settings_accept_legacy_platform_stack_env_aliases():
    previous_platform_url = os.environ.get("PORTFOLIO_DATA_PLATFORM_BASE_URL")
    previous_control_plane_url = os.environ.get("PORTFOLIO_DATA_CONTROL_PLANE_BASE_URL")
    previous_ingestion_url = os.environ.get("PORTFOLIO_DATA_INGESTION_BASE_URL")

    os.environ["PORTFOLIO_DATA_PLATFORM_BASE_URL"] = "http://lotus-core-query:8001"
    os.environ["PORTFOLIO_DATA_CONTROL_PLANE_BASE_URL"] = "http://lotus-core-control:8002"
    os.environ["PORTFOLIO_DATA_INGESTION_BASE_URL"] = "http://lotus-core-ingestion:8000"

    try:
        settings = Settings(
            _env_file=None,
            _env_prefix="__LOTUS_GATEWAY_TEST_UNUSED__",
        )
    finally:
        if previous_platform_url is None:
            os.environ.pop("PORTFOLIO_DATA_PLATFORM_BASE_URL", None)
        else:
            os.environ["PORTFOLIO_DATA_PLATFORM_BASE_URL"] = previous_platform_url

        if previous_control_plane_url is None:
            os.environ.pop("PORTFOLIO_DATA_CONTROL_PLANE_BASE_URL", None)
        else:
            os.environ["PORTFOLIO_DATA_CONTROL_PLANE_BASE_URL"] = previous_control_plane_url

        if previous_ingestion_url is None:
            os.environ.pop("PORTFOLIO_DATA_INGESTION_BASE_URL", None)
        else:
            os.environ["PORTFOLIO_DATA_INGESTION_BASE_URL"] = previous_ingestion_url

    assert settings.portfolio_data_query_base_url == "http://lotus-core-query:8001"
    assert settings.portfolio_data_control_plane_base_url == "http://lotus-core-control:8002"
    assert settings.portfolio_data_ingestion_base_url == "http://lotus-core-ingestion:8000"


def test_settings_reject_local_loopback_upstream_urls():
    with pytest.raises(ValueError, match="canonical service hostnames"):
        Settings(
            _env_file=None,
            _env_prefix="__LOTUS_GATEWAY_TEST_UNUSED__",
            ai_service_base_url="http://127.0.0.1:8140/",
        )


def test_settings_normalize_trailing_slashes_on_upstream_urls():
    settings = Settings(
        _env_file=None,
        _env_prefix="__LOTUS_GATEWAY_TEST_UNUSED__",
        performance_analytics_base_url="http://performance.dev.lotus/",
    )

    assert settings.performance_analytics_base_url == "http://performance.dev.lotus"
