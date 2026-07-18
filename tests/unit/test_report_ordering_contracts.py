import pytest
from pydantic import ValidationError

from app.contracts.report_ordering import WorkbenchReportOrderingResponse
from app.contracts.report_ordering_examples import REPORT_ORDERING_RESPONSE_EXAMPLE
from app.contracts.report_ordering_source import SourceReportOrderingCatalogue


def test_workbench_report_ordering_example_is_executable_contract() -> None:
    response = WorkbenchReportOrderingResponse.model_validate(REPORT_ORDERING_RESPONSE_EXAMPLE)

    serialized = response.model_dump(by_alias=True, mode="json")

    assert serialized == REPORT_ORDERING_RESPONSE_EXAMPLE
    assert serialized["sourceAuthority"] == "reporting"
    assert "sourceService" not in serialized
    assert serialized["reportFamilies"][0]["orderingModes"][0]["submission"]["path"] == (
        "/api/v1/reports/portfolio-reviews"
    )


def test_source_catalogue_rejects_unknown_transport_fields() -> None:
    with pytest.raises(ValidationError):
        SourceReportOrderingCatalogue.model_validate(
            {
                "source_service": "lotus-report",
                "contract_version": "report-ordering-catalogue.v1",
                "report_families": [],
                "supportability": {
                    "state": "ready",
                    "reason_code": "report_catalogue_ready",
                    "message": "Ready.",
                },
                "unexpected": "unsafe",
            }
        )


def test_experience_contract_rejects_unsupported_submission_paths() -> None:
    payload = {
        **REPORT_ORDERING_RESPONSE_EXAMPLE,
        "reportFamilies": [
            {
                **REPORT_ORDERING_RESPONSE_EXAMPLE["reportFamilies"][0],
                "orderingModes": [
                    {
                        **REPORT_ORDERING_RESPONSE_EXAMPLE["reportFamilies"][0]["orderingModes"][0],
                        "submission": {
                            "capabilityId": "reporting.portfolio_review.single",
                            "method": "POST",
                            "path": "/internal/report-service",
                            "state": "ready",
                            "reasonCode": "single_portfolio_ordering_ready",
                        },
                    }
                ],
            }
        ],
    }

    with pytest.raises(ValidationError):
        WorkbenchReportOrderingResponse.model_validate(payload)
