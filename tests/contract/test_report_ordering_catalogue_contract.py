import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.contracts.report_ordering import (
    ReportConfigurationField,
    ReportOrderingMode,
    ReportOutputFormat,
    ReportScopeSelection,
)
from app.contracts.report_ordering_source import SourceReportOrderingCatalogue
from app.main import app
from app.services.report_ordering_eligibility import ReportOrderingEntitlements
from app.services.report_ordering_projection import project_report_ordering_catalogue

UPSTREAM_CONTRACT_DIR = Path(__file__).resolve().parents[2] / "contracts" / "upstream"
CATALOGUE_PATH = UPSTREAM_CONTRACT_DIR / "lotus-report-ordering-catalogue.v1.json"
PROVENANCE_PATH = UPSTREAM_CONTRACT_DIR / "lotus-report-ordering-catalogue.v1.provenance.json"


def _stored_fixture_bytes() -> bytes:
    return CATALOGUE_PATH.read_bytes()


def _captured_body_bytes() -> bytes:
    stored = _stored_fixture_bytes()
    assert stored.endswith(b"\n")
    assert not stored.endswith(b"\n\n")
    return stored[:-1]


def _catalogue() -> dict[str, Any]:
    return json.loads(_captured_body_bytes())


def _provenance() -> dict[str, Any]:
    return json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))


def _portfolio_entitlements(role: str) -> ReportOrderingEntitlements:
    return ReportOrderingEntitlements.from_headers(
        {
            "X-Role": role,
            "X-Caller-Portfolio-Ids": "PB_SG_GLOBAL_BAL_001",
        }
    )


def test_pinned_catalogue_matches_the_retained_one_read_and_honest_provenance() -> None:
    body = _captured_body_bytes()
    provenance = _provenance()

    assert len(body) == provenance["capture"]["bodyBytes"] == 13837
    assert hashlib.sha256(body).hexdigest() == provenance["capture"]["bodySha256"]
    assert provenance["capture"]["bodySha256"] == (
        "adbdcb811a8fd5d3d254837eb411a17b8714f9fe3186ebde70a9bd258c84e88a"
    )
    assert provenance["capture"] == {
        "capturedAtUtc": "2026-10-14T05:22:41.052385+00:00",
        "httpStatus": 200,
        "requestCount": 1,
        "retryCount": 0,
        "bodyBytes": 13837,
        "bodySha256": "adbdcb811a8fd5d3d254837eb411a17b8714f9fe3186ebde70a9bd258c84e88a",
        "credentialBearingHeadersSent": False,
    }
    assert provenance["observedRuntime"]["revisionLabel"] == (
        "11fe4981a856a078cd0ed0ada881935cc803a214"
    )
    assert provenance["observedRuntime"]["imageContentsVerified"] is False
    assert any(
        "does not automatically detect future lotus-report source drift" in limitation
        for limitation in provenance["limitations"]
    )


def test_gateway_ingests_the_exact_five_family_producer_contract() -> None:
    source = SourceReportOrderingCatalogue.model_validate(_catalogue())

    assert [family.report_family_id for family in source.report_families] == [
        "portfolio_review",
        "proof_pack",
        "rebalance_wave",
        "outcome_review",
        "composite_review",
    ]
    composite = source.report_families[-1]
    assert [mode.mode_id for mode in composite.ordering_modes] == ["single_composite"]
    assert [output.format_id for output in composite.output_formats] == ["json", "xlsx"]
    assert len(composite.configuration_fields) == 7
    assert {field.input_type for field in composite.configuration_fields} == {
        "pinned_source_selection"
    }
    assert {field.value_source for field in composite.configuration_fields} == {"caller"}


def test_source_contract_accepts_xlsx_as_a_known_mode_default() -> None:
    payload = deepcopy(_catalogue())
    payload["report_families"][-1]["ordering_modes"][0]["default_output_format"] = "xlsx"

    source = SourceReportOrderingCatalogue.model_validate(payload)

    assert source.report_families[-1].ordering_modes[0].default_output_format == "xlsx"


def test_portfolio_manager_projection_retains_all_truth_without_composite_submission() -> None:
    source = SourceReportOrderingCatalogue.model_validate(_catalogue())
    response = project_report_ordering_catalogue(
        source=source,
        selection=ReportScopeSelection(
            scope_type="portfolio",
            scope_id="PB_SG_GLOBAL_BAL_001",
        ),
        entitlements=_portfolio_entitlements("portfolio_manager"),
    )

    assert [family.report_family_id for family in response.report_families] == [
        "portfolio_review",
        "proof_pack",
        "rebalance_wave",
        "outcome_review",
        "composite_review",
    ]
    composite = response.report_families[-1]
    mode = composite.ordering_modes[0]
    assert mode.mode_id == "single_composite"
    assert mode.interactive is False
    assert mode.eligibility.state == "unsupported"
    assert mode.eligibility.reason_code == "gateway_submission_not_supported"
    assert mode.submission is None
    assert [output.format_id for output in composite.output_formats] == ["json", "xlsx"]
    assert composite.output_formats[1].state == "ready"
    assert composite.output_formats[1].reason_code == "render_supportability_ready"
    assert len(composite.configuration_fields) == 7
    assert all(
        field.input_type == "pinned_source_selection" for field in composite.configuration_fields
    )


def test_client_advisor_projection_stays_bounded_to_orderable_portfolio_review() -> None:
    source = SourceReportOrderingCatalogue.model_validate(_catalogue())
    response = project_report_ordering_catalogue(
        source=source,
        selection=ReportScopeSelection(
            scope_type="portfolio",
            scope_id="PB_SG_GLOBAL_BAL_001",
        ),
        entitlements=_portfolio_entitlements("client_advisor"),
    )

    assert [family.report_family_id for family in response.report_families] == ["portfolio_review"]
    single = response.report_families[0].ordering_modes[0]
    assert single.mode_id == "single_portfolio"
    assert single.eligibility.state == "ready"
    assert single.submission is not None
    assert single.submission.path == "/api/v1/reports/portfolio-reviews"


@pytest.mark.parametrize(
    ("axis", "unknown_value"),
    [
        ("mode_id", "unknown_composite_mode"),
        ("format_id", "xlsm"),
        ("input_type", "source_reference"),
    ],
)
def test_source_contract_still_rejects_unknown_vocabulary(
    axis: str,
    unknown_value: str,
) -> None:
    payload = deepcopy(_catalogue())
    composite = payload["report_families"][-1]
    target = {
        "mode_id": composite["ordering_modes"][0],
        "format_id": composite["output_formats"][1],
        "input_type": composite["configuration_fields"][0],
    }[axis]
    target[axis] = unknown_value

    with pytest.raises(ValidationError):
        SourceReportOrderingCatalogue.model_validate(payload)


def test_source_contract_still_rejects_malformed_known_fields() -> None:
    payload = deepcopy(_catalogue())
    payload["report_families"][-1]["configuration_fields"][0]["unexpected"] = True

    with pytest.raises(ValidationError):
        SourceReportOrderingCatalogue.model_validate(payload)


@pytest.mark.parametrize(
    ("model", "payload", "field_name", "unknown_value"),
    [
        (
            ReportOrderingMode,
            {
                "modeId": "single_composite",
                "businessLabel": "Exact composite selection",
                "description": "Captured source selection.",
                "defaultOutputFormat": "xlsx",
                "interactive": False,
                "eligibility": {
                    "state": "unsupported",
                    "reasonCode": "gateway_submission_not_supported",
                    "message": "No Gateway submission path is published.",
                },
                "submission": None,
            },
            "modeId",
            "unknown_composite_mode",
        ),
        (
            ReportOutputFormat,
            {
                "formatId": "xlsx",
                "businessLabel": "Calculated review workbook",
                "usePosture": "governed_document",
                "state": "ready",
                "reasonCode": "render_supportability_ready",
            },
            "formatId",
            "xlsm",
        ),
        (
            ReportConfigurationField,
            {
                "fieldId": "composite_selection",
                "businessLabel": "Pinned calculated source",
                "description": "Exact source identity.",
                "inputType": "pinned_source_selection",
                "requirement": "conditional",
                "defaultingPolicy": "caller_required",
                "valueSource": "caller",
                "options": [],
            },
            "inputType",
            "source_reference",
        ),
    ],
)
def test_public_contract_accepts_only_known_extended_vocabulary(
    model: type[Any],
    payload: dict[str, Any],
    field_name: str,
    unknown_value: str,
) -> None:
    assert model.model_validate(payload)
    invalid = {**payload, field_name: unknown_value}
    with pytest.raises(ValidationError):
        model.model_validate(invalid)


def test_openapi_publishes_the_closed_extended_vocabulary() -> None:
    schemas = app.openapi()["components"]["schemas"]

    assert schemas["ReportOrderingMode"]["properties"]["modeId"]["enum"] == [
        "single_portfolio",
        "explicit_portfolio_batch",
        "governed_schedule",
        "source_workflow",
        "single_composite",
    ]
    assert schemas["ReportOutputFormat"]["properties"]["formatId"]["enum"] == [
        "json",
        "pdf",
        "xlsx",
    ]
    assert schemas["ReportOrderingMode"]["properties"]["defaultOutputFormat"]["enum"] == [
        "json",
        "pdf",
        "xlsx",
    ]
    assert schemas["ReportConfigurationField"]["properties"]["inputType"]["enum"] == [
        "business_date",
        "currency",
        "benchmark",
        "multi_select",
        "text",
        "pinned_source_selection",
    ]
