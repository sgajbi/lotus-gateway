from types import SimpleNamespace

from app.contracts.portfolio import PortfolioExceptionSummary, PortfolioInsight
from app.services import portfolio_insight_response


def test_build_portfolio_insights_response_assembles_status_backed_sections(monkeypatch):
    captured: dict[str, object] = {}

    def fake_build_portfolio_insights(**kwargs):
        captured["insights"] = kwargs
        return [
            PortfolioInsight(
                key="pricing-check",
                title="Pricing check",
                detail="Pricing status was forwarded.",
                severity="info",
                href="#portfolio-attention",
            )
        ]

    def fake_build_portfolio_exception_summaries(**kwargs):
        captured["exceptions"] = kwargs
        return [
            PortfolioExceptionSummary(
                key="reporting",
                title="Reporting check",
                detail="Reporting status was forwarded.",
                tone="warn",
                href="#portfolio-health",
            )
        ]

    monkeypatch.setattr(
        portfolio_insight_response,
        "build_portfolio_insights",
        fake_build_portfolio_insights,
    )
    monkeypatch.setattr(
        portfolio_insight_response,
        "build_portfolio_exception_summaries",
        fake_build_portfolio_exception_summaries,
    )

    position = SimpleNamespace(market_value_base=250.0)
    allocation_view = SimpleNamespace()
    partial_failure = SimpleNamespace(error_code="UPSTREAM_PARTIAL", detail="degraded")
    sources = SimpleNamespace(
        workspace=SimpleNamespace(
            as_of_date="2026-03-27",
            portfolio=SimpleNamespace(portfolio_id="PF_1001"),
            summary=SimpleNamespace(position_count=1),
            reporting=SimpleNamespace(status="PENDING", row_count=3),
            operations=SimpleNamespace(
                controls_blocking=True,
                latest_booked_transaction_date=None,
            ),
            partial_failures=[partial_failure],
        ),
        positions=SimpleNamespace(
            positions=[position],
            top_positions=[],
        ),
        allocations=SimpleNamespace(views=[allocation_view]),
        transactions=SimpleNamespace(total=0),
        activity=SimpleNamespace(buckets=[]),
    )

    response = portfolio_insight_response.build_portfolio_insights_response(
        correlation_id="corr-insights",
        contract_version="v1",
        portfolio_id="PF_1001",
        sources=sources,
    )

    assert response.model_dump() == {
        "correlation_id": "corr-insights",
        "contract_version": "v1",
        "portfolio_id": "PF_1001",
        "as_of_date": "2026-03-27",
        "insights": [
            {
                "key": "pricing-check",
                "title": "Pricing check",
                "detail": "Pricing status was forwarded.",
                "severity": "info",
                "href": "#portfolio-attention",
            }
        ],
        "exception_summaries": [
            {
                "key": "reporting",
                "title": "Reporting check",
                "detail": "Reporting status was forwarded.",
                "tone": "warn",
                "href": "#portfolio-health",
            }
        ],
    }

    insight_kwargs = captured["insights"]
    assert insight_kwargs["portfolio_id"] == "PF_1001"
    assert insight_kwargs["positions"] == [position]
    assert insight_kwargs["top_positions"] == []
    assert insight_kwargs["activity_summary"] is sources.activity
    assert insight_kwargs["pricing_status"] == "Ready"
    assert insight_kwargs["reporting_status"] == "Partial"

    exception_kwargs = captured["exceptions"]
    readiness = exception_kwargs["readiness"]
    assert readiness.holdings_status == "Ready"
    assert readiness.pricing_status == "Ready"
    assert readiness.transaction_status == "Missing"
    assert readiness.reporting_status == "Partial"
    assert exception_kwargs["controls_blocking"] is True
    assert exception_kwargs["partial_failures"] == [partial_failure]
