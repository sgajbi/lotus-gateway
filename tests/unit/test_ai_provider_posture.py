import pytest

from app.contracts.ai_provider_posture import (
    is_valid_ai_provider_posture,
    require_valid_ai_provider_posture,
)


@pytest.mark.parametrize(
    ("provider_mode", "stubbed"),
    (
        ("disabled", True),
        ("stub", True),
        ("openai", False),
        ("local_openai_compatible", False),
    ),
)
def test_supported_provider_postures_are_explicitly_valid(
    provider_mode: object,
    stubbed: object,
) -> None:
    assert is_valid_ai_provider_posture(provider_mode=provider_mode, stubbed=stubbed)
    require_valid_ai_provider_posture(provider_mode=provider_mode, stubbed=stubbed)


@pytest.mark.parametrize(
    ("provider_mode", "stubbed"),
    (
        ("disabled", False),
        ("stub", False),
        ("openai", True),
        ("local_openai_compatible", True),
        ("unknown", True),
        (None, True),
        ("openai", None),
    ),
)
def test_missing_unknown_and_contradictory_provider_postures_fail_closed(
    provider_mode: object,
    stubbed: object,
) -> None:
    assert not is_valid_ai_provider_posture(provider_mode=provider_mode, stubbed=stubbed)

    with pytest.raises(ValueError, match="provider mode and stub posture"):
        require_valid_ai_provider_posture(provider_mode=provider_mode, stubbed=stubbed)
