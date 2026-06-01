from app.services.performance_workspace_failures import build_performance_failure


def test_build_performance_failure_maps_workbench_partial_failure() -> None:
    failure = build_performance_failure(
        source_service="lotus-performance",
        error_code="HTTP_503",
        detail="Performance analytics unavailable",
    )

    assert failure.source_service == "lotus-performance"
    assert failure.error_code == "HTTP_503"
    assert failure.detail == "Performance analytics unavailable"
