from app.services.portfolio_workspace_payloads import (
    optional_text,
    parse_cashflow_outlook,
    parse_operational_readiness,
    parse_portfolio_identity,
    parse_portfolio_profile,
    parse_portfolio_summary,
    resolve_portfolio_display_name,
)


def test_parse_portfolio_identity_prefers_display_name_fallbacks() -> None:
    identity = parse_portfolio_identity(
        {
            "portfolio_id": "PF_1001",
            "name": "Global Balanced",
            "cif_id": "CIF_1",
            "booking_center": "SGPB",
        }
    )

    assert identity.portfolio_id == "PF_1001"
    assert identity.display_name == "Global Balanced"
    assert identity.client_id == "CIF_1"
    assert identity.base_currency == "USD"
    assert identity.booking_center_code == "SGPB"
    assert resolve_portfolio_display_name({}, fallback_portfolio_id="PF_FALLBACK") == "PF_FALLBACK"


def test_parse_portfolio_profile_normalizes_blank_optional_text() -> None:
    profile = parse_portfolio_profile(
        {
            "status": "ACTIVE",
            "portfolio_type": "ADVISORY",
            "risk_exposure": " ",
            "is_leverage_allowed": False,
            "advisor_id": "ADV_1001",
        }
    )

    assert profile.status == "ACTIVE"
    assert profile.portfolio_type == "ADVISORY"
    assert profile.risk_exposure is None
    assert profile.is_leverage_allowed is False
    assert profile.advisor_id == "ADV_1001"
    assert optional_text("  ") is None


def test_parse_portfolio_summary_quantizes_cash_and_ignores_non_dict_rows() -> None:
    summary = parse_portfolio_summary(
        aum_payload={
            "portfolios": [
                "not-a-row",
                {
                    "aum_reporting_currency": "1000.005",
                    "position_count": "7",
                },
            ]
        },
        cash_payload={
            "totals": {
                "total_balance_reporting_currency": "125.555",
                "cash_account_count": "2",
            }
        },
    )

    assert summary.assets_under_management_base == 1000.0
    assert summary.invested_market_value_base == 874.44
    assert summary.cash_market_value_base == 125.56
    assert summary.cash_weight_pct == 12.556
    assert summary.position_count == 7
    assert summary.cash_balance_count == 2


def test_parse_cashflow_outlook_quantizes_points_and_filters_invalid_rows() -> None:
    outlook = parse_cashflow_outlook(
        {
            "as_of_date": "2026-03-31",
            "range_end_date": "2026-04-30",
            "total_net_cashflow": "10.005",
            "projection_days": "30",
            "include_projected": True,
            "points": [
                {
                    "projection_date": "2026-04-01",
                    "net_cashflow": "5.125",
                    "projected_cumulative_cashflow": "5.125",
                },
                None,
            ],
        }
    )

    assert outlook.as_of_date == "2026-03-31"
    assert outlook.range_end_date == "2026-04-30"
    assert outlook.total_net_cashflow_base == 10.0
    assert outlook.projection_days == 30
    assert outlook.include_projected is True
    assert len(outlook.upcoming_points) == 1
    assert outlook.upcoming_points[0].net_cashflow_base == 5.12


def test_parse_operational_readiness_projects_supported_fields_only() -> None:
    readiness = parse_operational_readiness(
        {
            "business_date": "2026-03-31",
            "publish_allowed": True,
            "controls_blocking": False,
            "ignored": "not projected",
        }
    )

    assert readiness.business_date == "2026-03-31"
    assert readiness.publish_allowed is True
    assert readiness.controls_blocking is False
    assert not hasattr(readiness, "ignored")
