from typing import Literal

__all__ = ["WorkbenchAsOfState"]


WorkbenchAsOfState = Literal[
    "confirmed",
    "accepted_unverified",
    "unavailable",
]
