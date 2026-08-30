from collections.abc import Mapping

from fastapi import status

SourceErrorMessages = Mapping[int, Mapping[str, str]]

STANDARD_IDEA_ERROR_MESSAGES: Mapping[int, tuple[str, str]] = {
    status.HTTP_400_BAD_REQUEST: ("idea_invalid_request", "Lotus Idea rejected the request."),
    status.HTTP_403_FORBIDDEN: (
        "idea_permission_denied",
        "Caller is not permitted to use the requested Idea capability.",
    ),
    status.HTTP_404_NOT_FOUND: (
        "idea_resource_not_found",
        "The requested Idea resource was not found.",
    ),
    status.HTTP_409_CONFLICT: (
        "idea_conflict",
        "The requested Idea action conflicts with current source state or replay evidence.",
    ),
    status.HTTP_422_UNPROCESSABLE_CONTENT: (
        "idea_validation_failed",
        "Lotus Idea could not validate the action request.",
    ),
}

FEEDBACK_SOURCE_ERROR_MESSAGES: SourceErrorMessages = {
    status.HTTP_400_BAD_REQUEST: {
        "feedback_taxonomy_combination_invalid": (
            "The feedback outcome and reason are not allowed by the governed taxonomy."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "idempotency_conflict": "The idempotency key conflicts with existing feedback evidence.",
        "review_identity_conflict": (
            "The feedback identity conflicts with existing immutable evidence."
        ),
    },
}

PRESENTATION_RECEIPT_SOURCE_ERROR_MESSAGES: SourceErrorMessages = {
    status.HTTP_400_BAD_REQUEST: {
        "invalid_request": "Lotus Idea rejected the bounded presentation receipt request.",
    },
    status.HTTP_403_FORBIDDEN: {
        "permission_denied": "Caller is not permitted to record presentation evidence.",
    },
    status.HTTP_404_NOT_FOUND: {
        "candidate_not_found": "The requested Idea candidate was not found.",
    },
    status.HTTP_409_CONFLICT: {
        "presentation_receipt_identity_conflict": (
            "The idempotency key conflicts with immutable presentation evidence."
        ),
        "presentation_receipt_candidate_state_conflict": (
            "The receipt conflicts with current candidate tenant, version, or chronology."
        ),
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "durable_repository_not_configured": (
            "Lotus Idea durable presentation-receipt storage is not configured."
        ),
        "durable_repository_unavailable": (
            "Lotus Idea durable presentation-receipt storage is unavailable."
        ),
        "service_restoring": "Lotus Idea is restoring and cannot accept presentation evidence.",
        "service_recovery_degraded": (
            "Lotus Idea recovery posture cannot accept presentation evidence."
        ),
        "service_draining": "Lotus Idea is draining and cannot accept presentation evidence.",
        "presentation_receipt_unavailable": (
            "Lotus Idea presentation-receipt persistence is unavailable."
        ),
    },
}
