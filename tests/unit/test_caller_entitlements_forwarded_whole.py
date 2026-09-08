"""A caller's entitlement set reaches lotus-idea whole, or not at all.

Gateway forwards `X-Caller-*` headers verbatim and must never narrow them. If it
sent only the first of a caller's tenants, the request would be indistinguishable
from an honest one while asserting a scope the caller never claimed -- the defect
gateway#753 removed, where advisory-policy writes asserted a seeded tenant from a
module constant so every write executed under one identity whoever called.

Nothing enforced that. Replacing any forwarded value with `value.split(",")[0]`
left the whole suite green for four of the six plural headers; the two that did
fail failed by accident, because some unrelated fixture happened to carry a comma
and a test happened to assert it downstream. Coverage by coincidence is the most
dangerous state of the three, because it makes the pattern look considered.

These tests are written against the header population rather than a list of
names, so a header added to `as_idea_context` is covered the day it is added.
"""

import ast
from pathlib import Path

import pytest

from app.routers.ideas_common import IdeaCallerHeaders, idea_caller_headers

_IDEAS_COMMON = Path(__file__).resolve().parents[2] / "src" / "app" / "routers" / "ideas_common.py"

# Deliberately multi-valued, deliberately not in sorted order, and deliberately
# distinct per field: a shared value could be asserted from the wrong header and
# still pass, and a sorted one cannot detect a reordering.
_MULTI_VALUED = {
    "roles": "reviewer,advisor,supervisor",
    "capabilities": "idea.review,idea.convert,idea.suppress",
    "tenant_ids": "tenant-sg,tenant-hk,tenant-ch",
    "book_ids": "BOOK_SG_2,BOOK_SG_1,BOOK_HK_9",
    "portfolio_ids": "PB_SG_2,PB_SG_1,PB_HK_7",
    "client_ids": "CL_9,CL_2,CL_5",
}

_FIELD_TO_HEADER = {
    "roles": "X-Caller-Roles",
    "capabilities": "X-Caller-Capabilities",
    "tenant_ids": "X-Caller-Tenant-Ids",
    "book_ids": "X-Caller-Book-Ids",
    "portfolio_ids": "X-Caller-Portfolio-Ids",
    "client_ids": "X-Caller-Client-Ids",
}


def _forwarded_header_to_field() -> dict[str, str]:
    """The `X-Caller-*` header each field is forwarded as, read from the assignments.

    An earlier version selected fields by name suffix -- `_ids`, `roles`,
    `capabilities` -- which made the completeness guard vacuous for any future
    field named otherwise, such as `regions` or `entitlements`. Worse, the
    falsification that "proved" the guard added `mandate_ids`, a name the filter
    already matched, so it demonstrated only that the guard catches names of the
    shape it was written for.

    Reading `headers["X-Caller-..."] = self.<field>` from the method body has no
    such blind spot: the mapping is whatever the code actually forwards.
    """
    tree = ast.parse(_IDEAS_COMMON.read_text(encoding="utf-8"))
    method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "as_idea_context"
    )
    mapping: dict[str, str] = {}
    for node in ast.walk(method):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if not (
            isinstance(target, ast.Subscript)
            and isinstance(target.slice, ast.Constant)
            and isinstance(target.slice.value, str)
            and target.slice.value.startswith("X-Caller-")
        ):
            continue
        if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
            mapping[target.slice.value] = value.attr
    return mapping


def _headers_for(**overrides: str) -> dict[str, str]:
    return IdeaCallerHeaders(
        subject="advisor_1",
        roles=_MULTI_VALUED["roles"],
        capabilities=_MULTI_VALUED["capabilities"],
        tenant_ids=_MULTI_VALUED["tenant_ids"],
        book_ids=_MULTI_VALUED["book_ids"],
        portfolio_ids=_MULTI_VALUED["portfolio_ids"],
        client_ids=_MULTI_VALUED["client_ids"],
        **overrides,
    ).as_idea_context()


@pytest.mark.parametrize("field", sorted(_MULTI_VALUED))
def test_a_multi_valued_entitlement_is_forwarded_whole(field: str) -> None:
    """The entire value survives, character for character.

    Asserting membership or the first element would pass under exactly the
    truncation this exists to catch.
    """
    header = _FIELD_TO_HEADER[field]
    assert _headers_for()[header] == _MULTI_VALUED[field]


def test_entitlement_order_is_preserved() -> None:
    """Order is the caller's, not Gateway's.

    A sorted or de-duplicated set would still contain every entry, so an
    assertion on membership cannot tell a faithful forward from a rewritten one.
    Upstream may treat these as unordered; that is upstream's decision to make
    from the value it was given, not one Gateway may pre-empt.
    """
    forwarded = _headers_for()["X-Caller-Tenant-Ids"]
    assert forwarded.split(",") == ["tenant-sg", "tenant-hk", "tenant-ch"]
    assert forwarded != ",".join(sorted(["tenant-sg", "tenant-hk", "tenant-ch"]))


def test_every_forwarded_plural_field_is_covered_here() -> None:
    """A new plural header must not be able to arrive uncovered.

    This is the reason the cases above are parametrised from a mapping rather
    than written out: the failure that produced gateway#767 was a header nobody
    thought to assert, not an assertion someone got wrong.
    """
    # Compared as a whole mapping rather than as a set of fields. Collapsing to
    # fields loses the header keys, so a new header wired to an already-covered
    # field -- `headers["X-Caller-Region-Ids"] = self.tenant_ids` -- would leave
    # the field set unchanged, `uncovered` empty, and the new header both
    # unasserted and forwarding an entitlement that is not its own.
    forwarded = _forwarded_header_to_field()
    expected = {"X-Caller-Subject": "subject"} | {
        header: field for field, header in _FIELD_TO_HEADER.items()
    }
    assert forwarded == expected, (
        "the X-Caller-* headers as_idea_context forwards no longer match what this "
        "module asserts. Only in the code: "
        f"{sorted(set(forwarded.items()) - set(expected.items()))}; only asserted here: "
        f"{sorted(set(expected.items()) - set(forwarded.items()))}"
    )


@pytest.mark.parametrize("field", sorted(_MULTI_VALUED))
def test_the_ingress_dependency_does_not_narrow_before_serialization(field: str) -> None:
    """Both sides of the boundary, not just the serialization half.

    The cases above construct `IdeaCallerHeaders` directly. Every real Idea route
    receives it through `Depends(idea_caller_headers)` instead, so a regression
    that split a value at ingress -- before `as_idea_context` ever runs -- would
    leave all of them green while the caller's entitlement set was already
    truncated. Driving the dependency closes that half.
    """
    context = idea_caller_headers(
        x_caller_subject="advisor_1",
        x_caller_roles=_MULTI_VALUED["roles"],
        x_caller_capabilities=_MULTI_VALUED["capabilities"],
        x_caller_tenant_ids=_MULTI_VALUED["tenant_ids"],
        x_caller_book_ids=_MULTI_VALUED["book_ids"],
        x_caller_portfolio_ids=_MULTI_VALUED["portfolio_ids"],
        x_caller_client_ids=_MULTI_VALUED["client_ids"],
    )
    assert context.as_idea_context()[_FIELD_TO_HEADER[field]] == _MULTI_VALUED[field]
