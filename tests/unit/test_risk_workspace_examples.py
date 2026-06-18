import pytest
from pydantic import BaseModel

from app.contracts.risk_workspace import (
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskSummaryResponse,
)
from app.contracts.risk_workspace_examples import (
    _RISK_ATTRIBUTION_RESPONSE_EXAMPLE,
    _RISK_CONCENTRATION_RESPONSE_EXAMPLE,
    _RISK_DRAWDOWN_RESPONSE_EXAMPLE,
    _RISK_ROLLING_RESPONSE_EXAMPLE,
    _RISK_SUMMARY_RESPONSE_EXAMPLE,
)


@pytest.mark.parametrize(
    ("response_model", "example"),
    [
        (WorkbenchRiskSummaryResponse, _RISK_SUMMARY_RESPONSE_EXAMPLE),
        (WorkbenchRiskConcentrationResponse, _RISK_CONCENTRATION_RESPONSE_EXAMPLE),
        (WorkbenchRiskDrawdownResponse, _RISK_DRAWDOWN_RESPONSE_EXAMPLE),
        (WorkbenchRiskRollingResponse, _RISK_ROLLING_RESPONSE_EXAMPLE),
        (WorkbenchRiskAttributionResponse, _RISK_ATTRIBUTION_RESPONSE_EXAMPLE),
    ],
)
def test_risk_workspace_response_examples_remain_model_valid(
    response_model: type[BaseModel],
    example: dict[str, object],
) -> None:
    response = response_model.model_validate(example)

    assert response.model_dump(mode="json")["correlation_id"] == example["correlation_id"]
    assert response_model.model_config["json_schema_extra"] == {"example": example}
