from app.services.risk_workspace_attribution_controls import (
    build_attribution_controls,
    metadata_grouping_dimension_set,
    normalize_risk_attribution_grouping,
    normalize_risk_attribution_type,
    resolve_active_risk_grouping_support,
)
from app.services.risk_workspace_attribution_supportability import (
    build_attribution_supportability,
    total_risk_gated_grouping_reason,
)


def test_normalize_risk_attribution_controls_fail_closed_to_supported_defaults() -> None:
    assert normalize_risk_attribution_type("active_risk") == "ACTIVE_RISK"
    assert normalize_risk_attribution_type("unsupported") == "TOTAL_RISK"
    assert normalize_risk_attribution_grouping("asset_class") == "ASSET_CLASS"
    assert normalize_risk_attribution_grouping("unsupported") == "SECTOR"


def test_build_attribution_controls_marks_active_risk_without_benchmark_blocked() -> None:
    controls = build_attribution_controls(
        benchmark_code=None,
        attribution_type="ACTIVE_RISK",
        grouping_dimension="SECTOR",
    )

    type_options = {option.key: option for option in controls.attribution_types}
    grouping_options = {option.key: option for option in controls.grouping_dimensions}

    assert type_options["ACTIVE_RISK"].state == "blocked"
    assert grouping_options["SECTOR"].state == "blocked"
    assert grouping_options["SECTOR"].reason == "Active risk requires benchmark context."


def test_build_attribution_controls_uses_upstream_grouping_gate_metadata() -> None:
    controls = build_attribution_controls(
        benchmark_code="BMK_1",
        attribution_type="TOTAL_RISK",
        grouping_dimension="SECTOR",
        upstream_metadata={
            "stateful_active_risk_supported_grouping_dimensions": ["ASSET_CLASS"],
            "stateful_active_risk_gated_grouping_dimensions": ["SECTOR"],
            "stateful_active_risk_gate_reason": "Upstream active-risk grouping gate.",
        },
    )

    grouping_options = {option.key: option for option in controls.grouping_dimensions}
    assert grouping_options["POSITION"].supported_attribution_types == ["TOTAL_RISK"]
    assert grouping_options["SECTOR"].state == "partial"
    assert grouping_options["SECTOR"].reason == (
        "Supported for total risk. Upstream active-risk grouping gate."
    )
    assert grouping_options["ASSET_CLASS"].supported_attribution_types == [
        "TOTAL_RISK",
        "ACTIVE_RISK",
    ]


def test_build_attribution_supportability_blocks_gated_active_risk_grouping() -> None:
    supportability = build_attribution_supportability(
        benchmark_code="BMK_1",
        attribution_type="ACTIVE_RISK",
        grouping_dimension="ISSUER",
    )

    items = {item.key: item for item in supportability}
    assert items["benchmark_returns"].state == "ready"
    assert items["benchmark_exposure_context"].state == "blocked"
    assert "benchmark issuer exposure semantics" in (
        items["benchmark_exposure_context"].reason or ""
    )


def test_resolve_active_risk_grouping_support_defaults_and_metadata_override() -> None:
    default_supported, default_gated, default_reason = resolve_active_risk_grouping_support(None)
    metadata_supported, metadata_gated, metadata_reason = resolve_active_risk_grouping_support(
        {
            "stateful_active_risk_supported_grouping_dimensions": ["ASSET_CLASS", "unsupported"],
            "stateful_active_risk_gated_grouping_dimensions": ["ISSUER"],
            "stateful_active_risk_gate_reason": "Metadata gate.",
        }
    )

    assert default_supported == {"POSITION", "SECTOR", "ASSET_CLASS"}
    assert default_gated == {"ISSUER"}
    assert "benchmark issuer exposure semantics" in default_reason
    assert metadata_supported == {"ASSET_CLASS", "SECTOR"}
    assert metadata_gated == {"ISSUER"}
    assert metadata_reason == "Metadata gate."


def test_metadata_grouping_dimension_set_falls_back_for_non_list_values() -> None:
    assert metadata_grouping_dimension_set(
        metadata={"groups": "SECTOR"},
        field_name="groups",
        default=("POSITION",),
    ) == {"POSITION"}


def test_total_risk_gated_grouping_reason_lowercases_first_character() -> None:
    assert total_risk_gated_grouping_reason("Active risk remains gated.") == (
        "active risk remains gated."
    )
    assert total_risk_gated_grouping_reason(None) == (
        "active risk remains gated for this grouping."
    )
