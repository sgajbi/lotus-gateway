from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.contracts.workbench import WorkbenchSandboxChangeInput


def _change(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "security_id": "EQ_1",
        "transaction_type": "BUY",
    }
    payload.update(overrides)
    return payload


def test_sandbox_financial_values_preserve_exact_boundaries() -> None:
    change = WorkbenchSandboxChangeInput.model_validate(
        _change(
            quantity="-99999999.9999999999",
            price="99999999.9999999999",
            amount=0,
        )
    )

    assert change.quantity == Decimal("-99999999.9999999999")
    assert change.price == Decimal("99999999.9999999999")
    assert change.amount == Decimal("0")
    assert change.model_dump(mode="json", exclude_none=True) == {
        "security_id": "EQ_1",
        "transaction_type": "BUY",
        "quantity": "-99999999.9999999999",
        "price": "99999999.9999999999",
        "amount": "0",
    }


@pytest.mark.parametrize("field", ["quantity", "price", "amount"])
@pytest.mark.parametrize(
    "value",
    [
        0.1,
        "1.00000000001",
        "100000000.0000000000",
        "NaN",
    ],
)
def test_sandbox_financial_values_reject_lossy_or_unpersistable_input(
    field: str,
    value: object,
) -> None:
    with pytest.raises(ValidationError):
        WorkbenchSandboxChangeInput.model_validate(_change(**{field: value}))


def test_sandbox_price_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="greater than 0"):
        WorkbenchSandboxChangeInput.model_validate(_change(price="0"))


def test_sandbox_financial_values_may_be_omitted() -> None:
    change = WorkbenchSandboxChangeInput.model_validate(_change())

    assert change.quantity is None
    assert change.price is None
    assert change.amount is None
