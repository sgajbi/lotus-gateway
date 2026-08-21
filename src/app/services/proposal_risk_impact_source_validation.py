from pydantic import ValidationError

from app.services.proposal_risk_impact_errors import (
    raise_proposal_risk_impact_contract_invalid,
)
from app.services.proposal_risk_impact_source_contract import (
    SourceProposalRiskImpactDetail,
)


def validated_proposal_risk_impact_source(
    payload: dict[str, object],
    expected_proposal_id: str,
) -> SourceProposalRiskImpactDetail:
    """Validate source shape and bind returned evidence to the requested proposal."""

    try:
        source = SourceProposalRiskImpactDetail.model_validate(payload)
    except ValidationError as exc:
        raise_proposal_risk_impact_contract_invalid(exc)
    if (
        source.proposal.proposal_id != expected_proposal_id
        or source.proposal.proposal_id != source.current_version.proposal_id
        or source.proposal.current_version_no != source.current_version.version_no
    ):
        raise_proposal_risk_impact_contract_invalid()
    return source


__all__ = ["validated_proposal_risk_impact_source"]
