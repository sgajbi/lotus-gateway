from typing import Any

from pydantic import ValidationError

from app.contracts.advisor_cockpit_action_models import (
    AdvisorCockpitActionItem,
    AdvisorCockpitActionPage,
)
from app.services.advisor_cockpit_action_errors import (
    raise_advisor_cockpit_action_contract_invalid,
)


def project_advisor_cockpit_action_page(
    payload: dict[str, Any],
) -> AdvisorCockpitActionPage:
    try:
        return AdvisorCockpitActionPage.model_validate(payload)
    except ValidationError as exc:
        raise_advisor_cockpit_action_contract_invalid(exc)


def project_advisor_cockpit_action(
    payload: dict[str, Any],
) -> AdvisorCockpitActionItem:
    try:
        return AdvisorCockpitActionItem.model_validate(payload)
    except ValidationError as exc:
        raise_advisor_cockpit_action_contract_invalid(exc)


__all__ = [
    "project_advisor_cockpit_action",
    "project_advisor_cockpit_action_page",
]
