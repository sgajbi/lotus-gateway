from datetime import date
from typing import cast

from app.contracts.reporting_batch_preflight import (
    PreflightConfigurationState,
    PreflightOverallState,
    ReportBatchCandidatePreflight,
    ReportBatchPreflightConfigurationPosture,
    ReportBatchPreflightResponse,
    ReportBatchPreflightSourceEvidence,
    ReportBatchPreflightSourcePosture,
)
from app.contracts.reporting_batches import BatchCreateRequest
from app.services.advisor_book_service_errors import AdvisorBookServiceError
from app.services.advisor_book_source_contract import (
    SourceAdvisorBookMember,
    SourceAdvisorBookResponse,
)


def project_candidates(
    *,
    request: BatchCreateRequest,
    source: SourceAdvisorBookResponse,
    configuration: dict[str, str],
) -> list[ReportBatchCandidatePreflight]:
    members_by_id = {member.portfolio_id: member for member in source.members}
    return [
        _project_candidate(
            portfolio_id=portfolio_id,
            member=members_by_id.get(portfolio_id),
            source_as_of_date=source.as_of_date,
            configuration=configuration,
        )
        for portfolio_id in request.portfolio_ids
    ]


def source_posture(source: SourceAdvisorBookResponse) -> ReportBatchPreflightSourcePosture:
    ready = source.supportability.state == "READY"
    return ReportBatchPreflightSourcePosture(
        state="ready" if ready else "incomplete",
        reason_code="membership_source_ready" if ready else "membership_source_incomplete",
        message=(
            "Core membership evidence is current for the requested business date."
            if ready
            else "Core membership evidence is incomplete for the requested business date."
        ),
        as_of_date=source.as_of_date,
    )


def source_posture_from_error(exc: AdvisorBookServiceError) -> ReportBatchPreflightSourcePosture:
    incomplete = exc.code == "advisor_book_source_incomplete"
    return ReportBatchPreflightSourcePosture(
        state="incomplete" if incomplete else "unavailable",
        reason_code=exc.code,
        message="Core membership evidence could not be safely verified.",
        as_of_date=None,
    )


def unavailable_response(
    *,
    request: BatchCreateRequest,
    correlation_id: str,
    source_posture: ReportBatchPreflightSourcePosture,
    reason_code: str,
    message: str,
) -> ReportBatchPreflightResponse:
    candidates = [
        ReportBatchCandidatePreflight(
            portfolio_id=portfolio_id,
            state="unavailable",
            reason_code=reason_code,
            message=message,
        )
        for portfolio_id in request.portfolio_ids
    ]
    return build_response(
        request=request,
        correlation_id=correlation_id,
        source_posture=source_posture,
        configuration_posture=configuration_not_evaluated(),
        candidates=candidates,
    )


def build_response(
    *,
    request: BatchCreateRequest,
    correlation_id: str,
    source_posture: ReportBatchPreflightSourcePosture,
    configuration_posture: ReportBatchPreflightConfigurationPosture,
    candidates: list[ReportBatchCandidatePreflight],
) -> ReportBatchPreflightResponse:
    counts = _counts(candidates)
    state, reason_code, message = _overall_posture(counts, len(candidates))
    return ReportBatchPreflightResponse(
        request=request,
        state=state,
        reason_code=reason_code,
        message=message,
        source_posture=source_posture,
        configuration_posture=configuration_posture,
        candidate_count=len(candidates),
        ready_count=counts["ready"],
        partial_count=counts["partial"],
        stale_count=counts["stale"],
        permission_blocked_count=counts["permission_blocked"],
        unavailable_count=counts["unavailable"],
        candidates=candidates,
        correlation_id=correlation_id,
    )


def _project_candidate(
    *,
    portfolio_id: str,
    member: SourceAdvisorBookMember | None,
    source_as_of_date: date,
    configuration: dict[str, str],
) -> ReportBatchCandidatePreflight:
    if member is None:
        return ReportBatchCandidatePreflight(
            portfolio_id=portfolio_id,
            state="permission_blocked",
            reason_code="portfolio_not_entitled",
            message="The portfolio is not available in the authenticated book.",
        )
    evidence = _evidence(member=member, source_as_of_date=source_as_of_date)
    if member.status.strip().upper() != "ACTIVE":
        return ReportBatchCandidatePreflight(
            portfolio_id=portfolio_id,
            state="stale",
            reason_code="portfolio_inactive",
            message="The portfolio is not active for report creation at the requested date.",
            source_evidence=evidence,
        )
    return _configuration_candidate(
        portfolio_id=portfolio_id,
        evidence=evidence,
        configuration=configuration,
    )


def _configuration_candidate(
    *,
    portfolio_id: str,
    evidence: ReportBatchPreflightSourceEvidence,
    configuration: dict[str, str],
) -> ReportBatchCandidatePreflight:
    state = cast(str, configuration["state"])
    if state == "unavailable":
        return ReportBatchCandidatePreflight(
            portfolio_id=portfolio_id,
            state="unavailable",
            reason_code=configuration["reason_code"],
            message=(
                "The portfolio is entitled, but the requested report configuration is unavailable."
            ),
            source_evidence=evidence,
        )
    if state == "partial":
        return ReportBatchCandidatePreflight(
            portfolio_id=portfolio_id,
            state="partial",
            reason_code=configuration["reason_code"],
            message=configuration["message"],
            source_evidence=evidence,
        )
    return ReportBatchCandidatePreflight(
        portfolio_id=portfolio_id,
        state="ready",
        reason_code="portfolio_reporting_ready",
        message="The portfolio is active in the authenticated source-owned book.",
        source_evidence=evidence,
    )


def _evidence(
    *,
    member: SourceAdvisorBookMember,
    source_as_of_date: date,
) -> ReportBatchPreflightSourceEvidence:
    return ReportBatchPreflightSourceEvidence(
        source_system="lotus-core",
        source_contract_version="PortfolioManagerBookMembership:v1",
        as_of_date=source_as_of_date,
        membership_reference=member.source_record_id,
    )


def configuration_posture(
    configuration: dict[str, str],
) -> ReportBatchPreflightConfigurationPosture:
    return ReportBatchPreflightConfigurationPosture(
        state=cast(PreflightConfigurationState, configuration["state"]),
        reason_code=configuration["reason_code"],
        message=configuration["message"],
    )


def configuration_not_evaluated() -> ReportBatchPreflightConfigurationPosture:
    return ReportBatchPreflightConfigurationPosture(
        state="unavailable",
        reason_code="configuration_not_evaluated",
        message=(
            "Report configuration was not evaluated because membership evidence was unavailable."
        ),
    )


def _counts(candidates: list[ReportBatchCandidatePreflight]) -> dict[str, int]:
    return {
        state: sum(item.state == state for item in candidates)
        for state in ("ready", "partial", "stale", "permission_blocked", "unavailable")
    }


def _overall_posture(
    counts: dict[str, int], candidate_count: int
) -> tuple[PreflightOverallState, str, str]:
    if counts["ready"] == candidate_count:
        return "ready", "preflight_ready", "All requested portfolios are ready for report creation."
    if counts["ready"] or counts["partial"]:
        return (
            "partial",
            "candidate_scope_partial",
            "Some requested portfolios are not currently ready for reporting.",
        )
    return (
        "unavailable",
        "no_reportable_candidates",
        "No requested portfolios are currently ready for reporting.",
    )


__all__ = [
    "build_response",
    "configuration_not_evaluated",
    "configuration_posture",
    "project_candidates",
    "source_posture",
    "source_posture_from_error",
    "unavailable_response",
]
