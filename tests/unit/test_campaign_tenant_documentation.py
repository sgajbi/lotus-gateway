"""The campaign tenant figure the documentation states must be the measured one.

The wiki and the repository context both scoped the campaign tenant requirement
to "campaign-definition list/get and campaign-discovery reads" -- three or four
operations -- when every campaign operation requires it (gateway#776). Nothing
caught that, because the documentation test that existed asked whether the page
*mentioned* the subject, and a stale page mentions it exactly as well as a
current one.

So the number is derived and compared to the number the pages claim. Adding a
campaign operation fails this test until both pages are updated, which is the
property "the page mentions tenants" cannot have.

**Derived from the served contract, not from a list of clients.** The first
version of this test counted public methods on two hand-picked client modules
and produced 24. Review found that campaign discovery lives on a third client,
so the real figure is 25 -- and the prose it was blessing said "not only list/get
and discovery", making the count disagree with the sentence beside it. A chosen
set of files is an enumeration wearing a population's clothes, which is the exact
failure this test exists to prevent. The route table cannot omit a route.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.main import app

ROOT = Path(__file__).resolve().parents[2]

DOCUMENTS = (
    Path("wiki") / "API-Surface.md",
    Path("REPOSITORY-ENGINEERING-CONTEXT.md"),
)

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})
TENANT_HEADER = "X-Tenant-Id"


def _campaign_operations() -> list[tuple[str, str, dict[str, Any]]]:
    """Every served campaign operation, as (method, path, operation)."""

    spec = app.openapi()
    return [
        (method.upper(), path, operation)
        for path, operations in spec["paths"].items()
        if "campaign" in path.lower()
        for method, operation in operations.items()
        if method.lower() in _HTTP_METHODS
    ]


def _tenant_header(operation: dict[str, Any]) -> dict[str, Any] | None:
    for parameter in operation.get("parameters", []):
        if parameter.get("name") == TENANT_HEADER and parameter.get("in") == "header":
            return parameter
    return None


def _prose(relative: Path) -> str:
    """Document text with runs of whitespace collapsed.

    These pages are hard-wrapped, so a sentence spans lines and where it breaks
    changes with editing. Asserting against the raw bytes would fail on a rewrap
    -- a false positive that teaches the next reader to edit the assertion
    rather than the documentation.
    """

    return re.sub(r"\s+", " ", (ROOT / relative).read_text(encoding="utf-8"))


def test_every_served_campaign_operation_requires_the_tenant() -> None:
    """The claim itself, before any documentation is consulted.

    If this ever fails, the documentation is right to change and this test is
    reporting a real hole in the contract -- an operation reachable without the
    scope every other campaign operation demands.
    """

    operations = _campaign_operations()
    assert operations, "no campaign operations found; the derivation is broken, not the contract"

    not_required = [
        f"{method} {path}"
        for method, path, operation in operations
        if (header := _tenant_header(operation)) is None or not header.get("required")
    ]
    assert not_required == [], (
        f"{len(not_required)} campaign operation(s) do not require {TENANT_HEADER}: {not_required}"
    )


def test_every_document_states_the_measured_campaign_operation_count() -> None:
    measured = len(_campaign_operations())

    for relative in DOCUMENTS:
        text = _prose(relative)
        claims = [int(match) for match in re.findall(r"[Aa]ll (\d+) campaign operations", text)]
        assert claims, (
            f"{relative} no longer states how many campaign operations require the tenant. "
            "The sentence is the thing under test: deleting it must fail, not pass."
        )
        assert all(claim == measured for claim in claims), (
            f"{relative} claims {claims} campaign operations require {TENANT_HEADER}, "
            f"measured {measured} on the served contract. Update the documentation."
        )


def test_neither_document_still_scopes_the_requirement_to_reads() -> None:
    """The specific wrong claim #776 was filed for.

    Both pages named list/get and discovery, which is four of the twenty-five --
    a reader would have concluded the writes were unscoped.
    """

    for relative in DOCUMENTS:
        assert "list/get and campaign-discovery reads require" not in _prose(relative), (
            f"{relative} still scopes the campaign tenant requirement to reads"
        )


def test_the_documented_claim_covers_writes_explicitly() -> None:
    """A correct total alone would still read as a claim about reads.

    Nineteen of the twenty-five are reads, so a reader who skims the number and
    keeps the old mental model is not contradicted by it. The sentence has to say
    writes are included.
    """

    for relative in DOCUMENTS:
        assert "reads and writes alike" in _prose(relative), relative
