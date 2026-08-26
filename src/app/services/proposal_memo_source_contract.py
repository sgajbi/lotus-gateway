"""Tolerant Advise memo payload parsers and strict Gateway projections."""

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict

from app.contracts.proposal_memo_action_models import (
    ProposalMemoAiCommentaryResponse,
    ProposalMemoReportPackageEventResponse,
    ProposalMemoReportPackageResponse,
    ProposalMemoReviewResponse,
)
from app.contracts.proposal_memo_lineage_models import (
    ProposalMemoLineageResponse,
    ProposalMemoReplayEvidenceResponse,
)
from app.contracts.proposal_memo_models import ProposalMemoProjectionResponse, ProposalMemoResponse

PayloadT = TypeVar("PayloadT", bound=BaseModel)


class SourceProposalMemoResponse(ProposalMemoResponse):
    """Accept additive Advise memo fields before strict Gateway publication."""

    model_config = ConfigDict(extra="ignore")


class SourceProposalMemoProjectionResponse(ProposalMemoProjectionResponse):
    """Accept additive Advise projection fields before strict Gateway publication."""

    model_config = ConfigDict(extra="ignore")


class SourceProposalMemoReviewResponse(ProposalMemoReviewResponse):
    """Accept additive Advise review-result fields before strict Gateway publication."""

    model_config = ConfigDict(extra="ignore")


class SourceProposalMemoReportPackageEventResponse(ProposalMemoReportPackageEventResponse):
    """Accept additive Advise report-event fields before strict Gateway publication."""

    model_config = ConfigDict(extra="ignore")


class SourceProposalMemoReportPackageResponse(ProposalMemoReportPackageResponse):
    """Accept additive Advise report-package fields before strict Gateway publication."""

    model_config = ConfigDict(extra="ignore")


class SourceProposalMemoAiCommentaryResponse(ProposalMemoAiCommentaryResponse):
    """Accept additive Advise AI-commentary fields before strict Gateway publication."""

    model_config = ConfigDict(extra="ignore")


class SourceProposalMemoLineageResponse(ProposalMemoLineageResponse):
    """Accept additive Advise lineage fields before strict Gateway publication."""

    model_config = ConfigDict(extra="ignore")


class SourceProposalMemoReplayEvidenceResponse(ProposalMemoReplayEvidenceResponse):
    """Accept additive Advise replay-evidence fields before strict Gateway publication."""

    model_config = ConfigDict(extra="ignore")


_SOURCE_MODELS: dict[type[BaseModel], type[BaseModel]] = {
    ProposalMemoResponse: SourceProposalMemoResponse,
    ProposalMemoProjectionResponse: SourceProposalMemoProjectionResponse,
    ProposalMemoReviewResponse: SourceProposalMemoReviewResponse,
    ProposalMemoReportPackageEventResponse: SourceProposalMemoReportPackageEventResponse,
    ProposalMemoReportPackageResponse: SourceProposalMemoReportPackageResponse,
    ProposalMemoAiCommentaryResponse: SourceProposalMemoAiCommentaryResponse,
    ProposalMemoLineageResponse: SourceProposalMemoLineageResponse,
    ProposalMemoReplayEvidenceResponse: SourceProposalMemoReplayEvidenceResponse,
}


def project_tolerant_memo_source_payload(
    published_model: type[PayloadT], upstream_payload: dict[str, Any]
) -> PayloadT:
    """Drop additive source fields, then revalidate the closed published payload.

    Pydantic's per-call ``extra="ignore"`` override applies through the nested source graph.
    The second validation deliberately uses the unmodified published model so Workbench-facing
    OpenAPI contracts remain closed and all required-evidence validators still fail closed.
    """

    source_model = _SOURCE_MODELS[published_model]
    source_payload = source_model.model_validate(upstream_payload, extra="ignore")
    return published_model.model_validate(source_payload.model_dump(mode="python"))


__all__ = [
    "SourceProposalMemoAiCommentaryResponse",
    "SourceProposalMemoLineageResponse",
    "SourceProposalMemoProjectionResponse",
    "SourceProposalMemoReplayEvidenceResponse",
    "SourceProposalMemoReportPackageEventResponse",
    "SourceProposalMemoReportPackageResponse",
    "SourceProposalMemoResponse",
    "SourceProposalMemoReviewResponse",
    "project_tolerant_memo_source_payload",
]
