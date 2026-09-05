"""Transport-safe datetime inputs for caller-supplied contract fields.

Pydantic's lax datetime parsing accepts JSON numbers as Unix timestamps and
re-serializes them to ISO strings, so a caller could send a number despite the
OpenAPI date-time string contract and Gateway would forward a value the caller
never wrote. Caller-supplied datetime fields annotate with TransportDatetime,
which refuses numeric input before parsing; strings keep today's timezone
validation, and only genuine ISO text reaches the upstream contract.

These fields stay datetime-typed, so an ISO string's SPELLING is canonicalized
(".1" serializes as ".100000"). That is canonicalization, not corruption: the
outbound body is the request's mode="json" dump, and the evidence-echo
assertion compares the request's own dump against the source's echo — both
sides of every load-bearing comparison pass through the same normalization,
and a replayed caller string converges to the same canonical form. A field
whose exact bytes ARE part of upstream identity must instead use the
str-typed pattern (see idea_ai_explanations.requested_at_utc).
"""

import numbers
from datetime import datetime
from typing import Annotated, Any

from pydantic import BeforeValidator


def reject_numeric_datetime_input(value: Any) -> Any:
    if isinstance(value, numbers.Number):
        raise ValueError("must be an ISO-8601 date-time string; Unix-timestamp numbers are refused")
    return value


TransportDatetime = Annotated[datetime, BeforeValidator(reject_numeric_datetime_input)]
