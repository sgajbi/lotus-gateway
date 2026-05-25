from fastapi.routing import APIRoute

from app.main import app


def _route_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or set():
            if method in {"HEAD", "OPTIONS"}:
                continue
            keys.add((method, route.path))
    return keys


def test_gateway_exposes_supported_lotus_advise_proposal_surface() -> None:
    routes = _route_keys()
    expected = {
        ("POST", "/api/v1/proposals/simulate"),
        ("POST", "/api/v1/proposals/artifact"),
        ("POST", "/api/v1/proposals"),
        ("GET", "/api/v1/proposals"),
        ("POST", "/api/v1/proposals/async"),
        ("GET", "/api/v1/proposals/operations/{operation_id}"),
        ("GET", "/api/v1/proposals/operations/by-correlation/{operation_correlation_id}"),
        ("GET", "/api/v1/proposals/operations/{operation_id}/replay-evidence"),
        ("GET", "/api/v1/proposals/idempotency/{idempotency_key}"),
        ("GET", "/api/v1/proposals/{proposal_id}"),
        ("GET", "/api/v1/proposals/{proposal_id}/versions/{version_no}"),
        ("GET", "/api/v1/proposals/{proposal_id}/versions/{version_no}/replay-evidence"),
        ("POST", "/api/v1/proposals/{proposal_id}/versions"),
        ("POST", "/api/v1/proposals/{proposal_id}/versions/async"),
        ("POST", "/api/v1/proposals/{proposal_id}/submit"),
        ("POST", "/api/v1/proposals/{proposal_id}/approve-risk"),
        ("POST", "/api/v1/proposals/{proposal_id}/approve-compliance"),
        ("POST", "/api/v1/proposals/{proposal_id}/record-client-consent"),
        ("GET", "/api/v1/proposals/{proposal_id}/workflow-events"),
        ("GET", "/api/v1/proposals/{proposal_id}/approvals"),
        ("GET", "/api/v1/proposals/{proposal_id}/lineage"),
        ("POST", "/api/v1/proposals/{proposal_id}/versions/{version_no}/narrative/regenerate"),
        ("GET", "/api/v1/proposals/{proposal_id}/versions/{version_no}/narrative"),
        ("POST", "/api/v1/proposals/{proposal_id}/versions/{version_no}/narrative/review"),
        ("POST", "/api/v1/proposals/{proposal_id}/report-requests"),
        ("POST", "/api/v1/proposals/{proposal_id}/execution-handoffs"),
        ("GET", "/api/v1/proposals/{proposal_id}/delivery-summary"),
        ("GET", "/api/v1/proposals/{proposal_id}/delivery-events"),
        ("GET", "/api/v1/proposals/{proposal_id}/execution-status"),
        ("POST", "/api/v1/proposals/{proposal_id}/execution-updates"),
        ("POST", "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo"),
        ("GET", "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo"),
        ("GET", "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/projection"),
        ("POST", "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/review"),
        (
            "POST",
            "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/report-package-events",
        ),
        ("POST", "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/report-packages"),
        ("POST", "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/ai-commentary"),
        ("GET", "/api/v1/proposals/{proposal_id}/memos/lineage"),
        ("GET", "/api/v1/proposals/{proposal_id}/versions/{version_no}/memo/replay-evidence"),
    }

    assert expected - routes == set()


def test_gateway_exposes_supported_lotus_advise_workspace_surface() -> None:
    routes = _route_keys()
    expected = {
        ("POST", "/api/v1/advisory-workspaces"),
        ("GET", "/api/v1/advisory-workspaces/{workspace_id}"),
        ("POST", "/api/v1/advisory-workspaces/{workspace_id}/draft-actions"),
        ("POST", "/api/v1/advisory-workspaces/{workspace_id}/evaluate"),
        ("POST", "/api/v1/advisory-workspaces/{workspace_id}/save"),
        ("GET", "/api/v1/advisory-workspaces/{workspace_id}/saved-versions"),
        (
            "GET",
            "/api/v1/advisory-workspaces/{workspace_id}/saved-versions/"
            "{workspace_version_id}/replay-evidence",
        ),
        ("POST", "/api/v1/advisory-workspaces/{workspace_id}/resume"),
        ("POST", "/api/v1/advisory-workspaces/{workspace_id}/compare"),
        ("POST", "/api/v1/advisory-workspaces/{workspace_id}/assistant/rationale"),
        (
            "POST",
            "/api/v1/advisory-workspaces/{workspace_id}/assistant/rationale/review-actions",
        ),
        ("POST", "/api/v1/advisory-workspaces/{workspace_id}/handoff"),
    }

    assert expected - routes == set()
