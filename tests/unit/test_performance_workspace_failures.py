from app.services.performance_workspace_failures import (
    build_performance_failure,
    classify_detail_failure_codes,
)


def test_build_performance_failure_maps_workbench_partial_failure() -> None:
    failure = build_performance_failure(
        source_service="lotus-performance",
        error_code="HTTP_503",
        detail="Performance analytics unavailable",
    )

    assert failure.source_service == "lotus-performance"
    assert failure.error_code == "HTTP_503"
    assert failure.detail == "Performance analytics unavailable"


def test_classify_detail_failure_codes_preserves_canonical_currency_rejection() -> None:
    warning_code, error_code = classify_detail_failure_codes(
        status_code=422,
        payload={
            "detail": (
                "Stateful contribution input requires fx.rates when currency_mode=BOTH "
                "and sourced positions include currencies different from report_ccy."
            ),
            "error_code": "INVALID_REQUEST",
            "message": (
                "Stateful contribution input requires fx.rates when currency_mode=BOTH "
                "and sourced positions include currencies different from report_ccy."
            ),
        },
        unavailable_warning_code="CONTRIBUTION_UNAVAILABLE",
    )

    assert warning_code == "PERFORMANCE_DETAILS_CURRENCY_REJECTED"
    assert error_code == "REPORTING_CURRENCY_REJECTED"
