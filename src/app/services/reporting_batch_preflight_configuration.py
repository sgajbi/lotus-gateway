from pydantic import ValidationError

from app.contracts.report_ordering_source import (
    SourceReportFamily,
    SourceReportOrderingCatalogue,
)
from app.contracts.reporting_batch_preflight import PreflightConfigurationState
from app.contracts.reporting_batches import BatchCreateRequest
from app.services.reporting_client_protocols import ReportingCatalogueClient


async def load_report_configuration_posture(
    *,
    reporting_client: ReportingCatalogueClient,
    request: BatchCreateRequest,
    correlation_id: str,
) -> dict[str, str]:
    invalid = _validate_requested_formats(request)
    if invalid is not None:
        return invalid
    try:
        status_code, payload = await reporting_client.get_report_ordering_catalogue(
            correlation_id=correlation_id
        )
    except Exception:
        return _posture(
            "unavailable",
            "report_catalogue_unavailable",
            "Report configuration availability is temporarily unavailable.",
        )
    if status_code >= 400:
        return _posture(
            "unavailable",
            "report_catalogue_unavailable",
            "Report configuration availability is temporarily unavailable.",
        )
    try:
        catalogue = SourceReportOrderingCatalogue.model_validate(payload)
    except ValidationError:
        return _posture(
            "unavailable",
            "report_catalogue_contract_invalid",
            "Report configuration availability could not be safely verified.",
        )
    return _project_catalogue(catalogue, request)


def _validate_requested_formats(request: BatchCreateRequest) -> dict[str, str] | None:
    if not request.requested_output_formats:
        return _posture(
            "unavailable",
            "report_output_formats_missing",
            "At least one report output format is required.",
        )
    if len(set(request.requested_output_formats)) != len(request.requested_output_formats):
        return _posture(
            "unavailable",
            "report_output_formats_duplicate",
            "Report output formats must be unique.",
        )
    return None


def _project_catalogue(
    catalogue: SourceReportOrderingCatalogue,
    request: BatchCreateRequest,
) -> dict[str, str]:
    if catalogue.supportability.state == "unavailable":
        return _posture(
            "unavailable",
            catalogue.supportability.reason_code,
            "Report configuration availability is temporarily unavailable.",
        )
    family = next(
        (item for item in catalogue.report_families if item.report_family_id == "portfolio_review"),
        None,
    )
    if family is None or not _has_batch_mode(family):
        return _posture(
            "unavailable",
            "report_batch_mode_unavailable",
            "Explicit report-batch configuration is not currently available.",
        )
    if family.supportability.state == "unavailable":
        return _posture(
            "unavailable",
            family.supportability.reason_code,
            "Report configuration availability is temporarily unavailable.",
        )
    return _project_formats(catalogue, family, request.requested_output_formats)


def _has_batch_mode(family: SourceReportFamily) -> bool:
    return any(mode.mode_id == "explicit_portfolio_batch" for mode in family.ordering_modes)


def _project_formats(
    catalogue: SourceReportOrderingCatalogue,
    family: SourceReportFamily,
    requested_formats: list[str],
) -> dict[str, str]:
    requested = [
        next((item for item in family.output_formats if item.format_id == format_id), None)
        for format_id in requested_formats
    ]
    if any(item is None for item in requested):
        return _posture(
            "unavailable",
            "report_output_format_unsupported",
            "One or more requested report output formats are unsupported.",
        )
    if any(item.state == "unavailable" for item in requested if item is not None):
        return _posture(
            "unavailable",
            "report_output_format_unavailable",
            "One or more requested report output formats are unavailable.",
        )
    if any(item.state == "partial" for item in requested if item is not None):
        return _posture(
            "partial",
            "report_output_format_partial",
            "One or more requested report output formats are temporarily degraded.",
        )
    if catalogue.supportability.state == "partial" or family.supportability.state == "partial":
        reason = (
            family.supportability.reason_code
            if family.supportability.state == "partial"
            else catalogue.supportability.reason_code
        )
        return _posture(
            "partial", reason, "Report configuration is available with a degraded source posture."
        )
    return _posture(
        "ready",
        "report_configuration_ready",
        "The requested report configuration is source-backed.",
    )


def _posture(
    state: PreflightConfigurationState,
    reason_code: str,
    message: str,
) -> dict[str, str]:
    return {"state": state, "reason_code": reason_code, "message": message}


__all__ = ["load_report_configuration_posture"]
