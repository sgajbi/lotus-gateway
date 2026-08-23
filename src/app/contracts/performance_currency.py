from typing import Literal

__all__ = ["ReportingCurrencyState"]


ReportingCurrencyState = Literal[
    "applied",
    "accepted_unverified",
    "rejected",
    "unavailable",
]
