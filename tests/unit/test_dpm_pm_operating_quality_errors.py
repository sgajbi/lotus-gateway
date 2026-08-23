from app.services.dpm_pm_operating_quality_errors import (
    extract_pm_operating_quality_validation_evidence,
)


def test_extracts_pydantic_validation_codes_and_indexed_field_paths_without_payload_values() -> (
    None
):
    evidence = extract_pm_operating_quality_validation_evidence(
        422,
        {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["body", "policy", "tenant_id"],
                    "msg": "Field required",
                    "input": {"secret": "do-not-expose"},
                },
                {
                    "type": "string_type",
                    "loc": ["body", "governance", "approval", 0],
                },
            ]
        },
    )

    assert evidence.reason_codes == ("missing", "string_type")
    assert evidence.field_paths == ("policy.tenant_id", "governance.approval.0")
    assert "Field required" not in str(evidence)
    assert "do-not-expose" not in str(evidence)


def test_extracts_bounded_manage_problem_detail_metadata() -> None:
    evidence = extract_pm_operating_quality_validation_evidence(
        422,
        {
            "detail": {
                "code": "PM_QUALITY_GOVERNANCE_APPROVAL_REQUIRED",
                "field": "policy.tenant_id",
                "message": "submitted value must not be returned",
            }
        },
    )

    assert evidence.reason_codes == ("PM_QUALITY_GOVERNANCE_APPROVAL_REQUIRED",)
    assert evidence.field_paths == ("policy.tenant_id",)
    assert "submitted value" not in str(evidence)


def test_ignores_generic_or_unparseable_details_and_all_five_x_payloads() -> None:
    assert (
        extract_pm_operating_quality_validation_evidence(
            422,
            {"detail": "validation failed for submitted secret value"},
        ).reason_codes
        == ()
    )
    assert extract_pm_operating_quality_validation_evidence(
        422,
        {"detail": "Forbidden"},
    ).reason_codes == ("Forbidden",)
    assert extract_pm_operating_quality_validation_evidence(
        500,
        {
            "detail": {
                "code": "INTERNAL_SECRET_CODE",
                "field": "policy.tenant_id",
                "message": "internal failure details",
            }
        },
    ) == extract_pm_operating_quality_validation_evidence(500, {"detail": "unavailable"})


def test_deduplicates_and_bounds_validation_metadata() -> None:
    detail = [{"type": f"reason_{index}", "field": f"field_{index}"} for index in range(10)]
    detail.extend(detail[:2])

    evidence = extract_pm_operating_quality_validation_evidence(422, {"detail": detail})

    assert len(evidence.reason_codes) == 8
    assert len(evidence.field_paths) == 8
    assert evidence.reason_codes == tuple(f"reason_{index}" for index in range(8))
    assert evidence.field_paths == tuple(f"field_{index}" for index in range(8))


def test_bounds_mixed_field_first_and_location_metadata_per_node() -> None:
    detail = {
        "errors": [
            {
                "field": f"field_{index}",
                "loc": ["body", f"field_{index}", "value"],
            }
            for index in range(5)
        ]
    }

    evidence = extract_pm_operating_quality_validation_evidence(422, {"detail": detail})

    assert len(evidence.field_paths) == 8
    assert evidence.field_paths == (
        "field_0",
        "field_0.value",
        "field_1",
        "field_1.value",
        "field_2",
        "field_2.value",
        "field_3",
        "field_3.value",
    )
