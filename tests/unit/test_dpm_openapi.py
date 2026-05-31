from app.contracts.dpm_construction import DpmConstructionErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses


def test_manage_upstream_error_responses_builds_standard_response_map() -> None:
    responses = manage_upstream_error_responses(
        error_model=DpmConstructionErrorDetail,
        not_found_description="not found",
        conflict_description="conflict",
        invalid_payload_description="invalid",
        unavailable_description="unavailable",
    )

    assert responses == {
        404: {"model": DpmConstructionErrorDetail, "description": "not found"},
        409: {"model": DpmConstructionErrorDetail, "description": "conflict"},
        422: {"model": DpmConstructionErrorDetail, "description": "invalid"},
        503: {"model": DpmConstructionErrorDetail, "description": "unavailable"},
    }


def test_manage_upstream_error_responses_omits_not_found_when_not_supported() -> None:
    responses = manage_upstream_error_responses(
        error_model=DpmConstructionErrorDetail,
        conflict_description="conflict",
        invalid_payload_description="invalid",
        unavailable_description="unavailable",
    )

    assert sorted(responses) == [409, 422, 503]
