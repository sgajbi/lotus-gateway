from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from app.contracts.dpm_waves import (
    DpmCampaignApprovalDecisionRequest,
    DpmCampaignAssignmentActionRequest,
    DpmCampaignAssignmentTaskRequest,
    DpmCampaignAssignmentTaskTransitionRequest,
    DpmCampaignDefinitionLaunchRequest,
    DpmCampaignDefinitionRetirementRequest,
    DpmCampaignDefinitionSupersessionRequest,
    DpmCampaignMakerCheckerControlRequest,
)
from tests.support.dpm_campaign_command_fixtures import (
    STALE_CAMPAIGN_COMMAND_BODIES,
    VALID_CAMPAIGN_COMMAND_BODIES,
)

REQUEST_MODELS: list[type[BaseModel]] = [
    DpmCampaignDefinitionLaunchRequest,
    DpmCampaignDefinitionRetirementRequest,
    DpmCampaignDefinitionSupersessionRequest,
    DpmCampaignApprovalDecisionRequest,
    DpmCampaignAssignmentActionRequest,
    DpmCampaignAssignmentTaskRequest,
    DpmCampaignAssignmentTaskTransitionRequest,
    DpmCampaignMakerCheckerControlRequest,
]


@pytest.mark.parametrize(
    ("request_model", "body"),
    list(zip(REQUEST_MODELS, VALID_CAMPAIGN_COMMAND_BODIES, strict=True)),
)
def test_current_manage_campaign_command_shapes_round_trip_without_mutation(
    request_model: type[BaseModel], body: dict[str, Any]
) -> None:
    request = request_model.model_validate({"body": body})

    assert request.model_dump(mode="json")["body"] == body


@pytest.mark.parametrize(
    ("request_model", "body"),
    list(zip(REQUEST_MODELS, STALE_CAMPAIGN_COMMAND_BODIES, strict=True)),
)
def test_stale_campaign_command_shapes_fail_closed(
    request_model: type[BaseModel], body: dict[str, Any]
) -> None:
    with pytest.raises(ValidationError):
        request_model.model_validate({"body": body})


def test_optional_campaign_command_fields_remain_omitted_for_forwarding() -> None:
    request = DpmCampaignDefinitionLaunchRequest.model_validate(
        {"body": {"requested_as_of_date": "2026-05-10", "actor_id": "pm_sg_1"}}
    )

    assert request.body.model_dump(mode="json", exclude_unset=True) == {
        "requested_as_of_date": "2026-05-10",
        "actor_id": "pm_sg_1",
    }
