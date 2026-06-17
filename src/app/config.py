from pathlib import Path
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings


def _default_platform_generated_path(filename: str) -> str:
    workspace_root = Path(__file__).resolve().parents[3]
    return str(workspace_root / "lotus-platform" / "generated" / filename)


def _default_platform_output_path(*parts: str) -> str:
    workspace_root = Path(__file__).resolve().parents[3]
    return str(workspace_root / "lotus-platform" / "output" / Path(*parts))


class Settings(BaseSettings):
    app_name: str = "Advisor Experience API"
    contract_version: str = "v1"
    decisioning_service_base_url: str = Field(default="http://advise.dev.lotus")
    portfolio_data_query_base_url: str = Field(
        default="http://core-query.dev.lotus",
        validation_alias=AliasChoices(
            "PORTFOLIO_DATA_QUERY_BASE_URL",
            "PORTFOLIO_DATA_PLATFORM_BASE_URL",
        ),
    )
    portfolio_data_control_plane_base_url: str = Field(
        default="http://core-control.dev.lotus",
        validation_alias=AliasChoices(
            "PORTFOLIO_DATA_CONTROL_PLANE_BASE_URL",
            "PORTFOLIO_DATA_PLATFORM_BASE_URL",
        ),
    )
    portfolio_data_ingestion_base_url: str = Field(
        default="http://core-ingestion.dev.lotus",
        validation_alias=AliasChoices("PORTFOLIO_DATA_INGESTION_BASE_URL"),
    )
    performance_analytics_base_url: str = Field(default="http://performance.dev.lotus")
    ai_service_base_url: str = Field(default="http://ai.dev.lotus")
    risk_analytics_base_url: str = Field(default="http://risk.dev.lotus")
    reporting_aggregation_base_url: str = Field(default="http://report.dev.lotus")
    render_service_base_url: str = Field(default="http://render.dev.lotus")
    archive_service_base_url: str = Field(default="http://archive.dev.lotus")
    management_service_base_url: str = Field(default="http://manage.dev.lotus")
    upstream_timeout_seconds: float = Field(default=3.0)
    platform_capabilities_source_timeout_seconds: float = Field(default=5.0)
    performance_analytics_timeout_seconds: float = Field(default=15.0)
    ai_service_timeout_seconds: float = Field(default=45.0)
    upstream_max_retries: int = Field(default=2)
    upstream_retry_backoff_seconds: float = Field(default=0.2)
    portfolio_upstream_cache_ttl_seconds: float = Field(default=5.0)
    advisor_brief_cache_ttl_seconds: float = Field(default=30.0)
    risk_bff_cache_ttl_seconds: int = Field(default=15)
    domain_product_catalog_path: str = Field(
        default_factory=lambda: _default_platform_generated_path("domain-product-catalog.json")
    )
    domain_product_dependency_graph_path: str = Field(
        default_factory=lambda: _default_platform_generated_path(
            "domain-product-dependency-graph.json"
        )
    )
    domain_product_live_trust_certification_path: str = Field(
        default_factory=lambda: _default_platform_output_path(
            "trust-certification",
            "domain-product-live-trust-certification.json",
        )
    )
    workbench_default_benchmark_code: str = Field(default="BMK_PB_GLOBAL_BALANCED_60_40")

    @field_validator(
        "decisioning_service_base_url",
        "portfolio_data_query_base_url",
        "portfolio_data_control_plane_base_url",
        "portfolio_data_ingestion_base_url",
        "performance_analytics_base_url",
        "ai_service_base_url",
        "risk_analytics_base_url",
        "reporting_aggregation_base_url",
        "render_service_base_url",
        "archive_service_base_url",
        "management_service_base_url",
        mode="before",
    )
    @classmethod
    def normalize_upstream_base_url(cls, value: str) -> str:
        normalized = str(value).strip().rstrip("/")
        hostname = urlparse(normalized).hostname

        if hostname and hostname.lower() in {"localhost", "127.0.0.1", "0.0.0.0"}:
            raise ValueError(
                "Gateway upstream base URLs must use canonical service hostnames, "
                f"not local loopback ({hostname})."
            )

        return normalized


settings = Settings()
