from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


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
    management_service_base_url: str = Field(default="http://manage.dev.lotus")
    manage_split_enabled: bool = Field(default=True)
    upstream_timeout_seconds: float = Field(default=3.0)
    performance_analytics_timeout_seconds: float = Field(default=15.0)
    ai_service_timeout_seconds: float = Field(default=45.0)
    upstream_max_retries: int = Field(default=2)
    upstream_retry_backoff_seconds: float = Field(default=0.2)
    portfolio_upstream_cache_ttl_seconds: float = Field(default=5.0)
    advisor_brief_cache_ttl_seconds: float = Field(default=30.0)


settings = Settings()
