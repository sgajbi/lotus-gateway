from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionCapability,
    ProposalDiscussionConsentEvidence,
    ProposalDiscussionMemoEvidence,
    ProposalDiscussionNarrativeEvidence,
    ProposalDiscussionPackageEvidence,
)


def proposal_discussion_pack_capabilities(
    narrative: ProposalDiscussionNarrativeEvidence,
    memo: ProposalDiscussionMemoEvidence,
    package: ProposalDiscussionPackageEvidence,
    consent: ProposalDiscussionConsentEvidence,
) -> list[ProposalDiscussionCapability]:
    return [
        *_identity_capabilities(),
        *_content_capabilities(narrative, memo),
        *_workflow_capabilities(package, consent),
        *_boundary_capabilities(),
    ]


def _identity_capabilities() -> list[ProposalDiscussionCapability]:
    return [
        ProposalDiscussionCapability(
            key="proposal_identity",
            state="supported",
            reason_code="request_bound_proposal_version_available",
            source_service="lotus-advise",
            support_reference="ProposalDetailResponse",
        )
    ]


def _content_capabilities(
    narrative: ProposalDiscussionNarrativeEvidence,
    memo: ProposalDiscussionMemoEvidence,
) -> list[ProposalDiscussionCapability]:
    return [
        ProposalDiscussionCapability(
            key="advisor_narrative",
            state=narrative.state,
            reason_code=narrative.reason_code,
            source_service="lotus-advise" if narrative.state == "supported" else None,
            support_reference="ProposalNarrativeReadResponse",
        ),
        ProposalDiscussionCapability(
            key="advisor_memo",
            state=memo.state,
            reason_code=memo.reason_code,
            source_service="lotus-advise" if memo.state == "supported" else None,
            support_reference="ProposalMemoResponse",
        ),
        ProposalDiscussionCapability(
            key="disclosure_policy",
            state=narrative.state,
            reason_code=(
                "narrative_disclosure_policy_available"
                if narrative.state == "supported"
                else narrative.reason_code
            ),
            source_service="lotus-advise" if narrative.state == "supported" else None,
            support_reference="ProposalNarrativePolicy.required_disclosures",
        ),
    ]


def _workflow_capabilities(
    package: ProposalDiscussionPackageEvidence,
    consent: ProposalDiscussionConsentEvidence,
) -> list[ProposalDiscussionCapability]:
    return [
        ProposalDiscussionCapability(
            key="report_package",
            state=package.state,
            reason_code=package.reason_code,
            source_service=("lotus-report" if package.state in {"supported", "partial"} else None),
            support_reference="ProposalDeliverySummaryResponse.reporting",
        ),
        ProposalDiscussionCapability(
            key="approval_and_consent_records",
            state=consent.state,
            reason_code=consent.reason_code,
            source_service="lotus-advise" if consent.state in {"supported", "partial"} else None,
            support_reference="ProposalApprovalsResponse.approvals",
        ),
    ]


def _boundary_capabilities() -> list[ProposalDiscussionCapability]:
    return [
        ProposalDiscussionCapability(
            key="client_release",
            state="not_supported",
            reason_code="client_release_authority_not_exposed",
            support_reference="RFC-0023/RFC-0024 boundary",
        ),
        ProposalDiscussionCapability(
            key="client_delivery",
            state="not_supported",
            reason_code="client_communication_delivery_not_supported",
        ),
    ]


__all__ = ["proposal_discussion_pack_capabilities"]
