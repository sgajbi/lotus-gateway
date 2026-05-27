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


def test_gateway_exposes_supported_lotus_advise_policy_surface() -> None:
    routes = _route_keys()
    expected = {
        ("GET", "/api/v1/advisory-policy-packs"),
        ("GET", "/api/v1/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}"),
        (
            "POST",
            "/api/v1/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}/validate",
        ),
        (
            "POST",
            "/api/v1/advisory-policy-packs/{policy_pack_id}/versions/{policy_version}/activate",
        ),
        (
            "POST",
            "/api/v1/proposals/{proposal_id}/versions/{proposal_version_id}/policy-evaluations",
        ),
        ("GET", "/api/v1/advisory-policy-evaluations/review-queue"),
        ("GET", "/api/v1/advisory-policy-evaluations/{evaluation_id}"),
        ("POST", "/api/v1/advisory-policy-evaluations/{evaluation_id}/replay"),
        ("POST", "/api/v1/advisory-policy-evaluations/{evaluation_id}/events"),
        ("GET", "/api/v1/advisory-policy-evaluations/{evaluation_id}/lineage"),
        ("GET", "/api/v1/advisory-policy-evaluations/{evaluation_id}/sign-off-package"),
        ("GET", "/api/v1/advisory-policy-evaluations/{evaluation_id}/workflow"),
        ("POST", "/api/v1/advisory-policy-evaluations/{evaluation_id}/sign-off-decisions"),
        ("POST", "/api/v1/advisory-policy-evaluations/{evaluation_id}/report-packages"),
        ("POST", "/api/v1/advisory-policy-evaluations/{evaluation_id}/ai-evidence"),
    }

    assert expected - routes == set()


def test_gateway_exposes_supported_lotus_advise_advisor_cockpit_surface() -> None:
    routes = _route_keys()
    expected = {
        ("GET", "/api/v1/advisor-cockpit/actions"),
        ("GET", "/api/v1/advisor-cockpit/actions/{action_item_id}"),
        ("GET", "/api/v1/advisor-cockpit/snapshot"),
        ("GET", "/api/v1/advisor-cockpit/supportability"),
        ("POST", "/api/v1/advisor-cockpit/actions/{action_item_id}/acknowledgements"),
    }

    assert expected - routes == set()


def test_gateway_policy_report_package_openapi_stays_within_supported_boundary() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/advisory-policy-evaluations/{evaluation_id}/report-packages"
    ]["post"]

    assert "client-draft" not in operation["description"].lower()
    assert "advisor/compliance policy sign-off package" in operation["description"]
    assert "client-ready publication" in operation["description"]
