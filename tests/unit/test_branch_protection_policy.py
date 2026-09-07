"""The documented branch-protection policy must stay complete and self-consistent.

The live comparison runs in CI where a token exists; these offline checks keep
the policy document itself honest so the live gate always has a valid table to
compare against, and so the zero-approval exception cannot be silently deleted
while the configuration stays weak.
"""

import copy
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.check_branch_protection_policy import (
    _AUDITED_EXCEPTION_FIELDS as AUDITED_FIELDS,
)
from scripts.check_branch_protection_policy import (
    _MERGEABILITY_EXPECTED_KEYS as MERGEABILITY_KEYS,
)
from scripts.check_branch_protection_policy import (
    _WEAK_POSTURES as WEAK_POSTURES,
)
from scripts.check_branch_protection_policy import (
    _resolve_expected as resolve_expected,
)
from scripts.check_branch_protection_policy import (
    compare_live_to_policy,
    detect_repository,
    load_policy,
    resolve_effective_codeowners,
    validate_policy_document,
)


def _live_matching_policy(policy: dict[str, Any]) -> dict[str, Any]:
    expected = policy["expected"]
    return {
        "enforce_admins": {"enabled": expected["enforce_admins"]},
        "required_linear_history": {"enabled": expected["required_linear_history"]},
        "allow_force_pushes": {"enabled": expected["allow_force_pushes"]},
        "allow_deletions": {"enabled": expected["allow_deletions"]},
        "required_conversation_resolution": {
            "enabled": expected["required_conversation_resolution"]
        },
        "restrictions": {"users": []} if expected["restrictions_present"] else None,
        **{key: {"enabled": expected[key]} for key in MERGEABILITY_KEYS},
        "required_status_checks": {
            "strict": expected["required_status_checks"]["strict"],
            # Mirrors the API shape, derived from the table so the double cannot
            # drift from what it stands in for.
            "checks": [dict(check) for check in expected["required_status_checks"]["checks"]],
        },
        "required_pull_request_reviews": (
            {
                key: expected["required_pull_request_reviews"][key]
                for key in (
                    "required_approving_review_count",
                    "dismiss_stale_reviews",
                    "require_code_owner_reviews",
                    "require_last_push_approval",
                )
            }
            if expected["required_pull_request_reviews"]["present"]
            else None
        ),
    }


def test_policy_document_is_complete() -> None:
    assert validate_policy_document(load_policy()) == []


def test_the_weak_postures_named_here_are_the_ones_that_must_be_documented() -> None:
    """Pinned explicitly, because the parametrized test below cannot catch a gap.

    That test derives its cases FROM `_WEAK_POSTURES`, so deleting an entry
    deletes its own case and the suite stays green — the self-referential trap:
    a test generated from the thing under test can prove the wiring and never the
    contents.

    Listed literally here. Adding a posture is a deliberate act that updates this
    line; removing one fails.
    """
    assert set(WEAK_POSTURES) == {
        "enforce_admins",
        "required_linear_history",
        "allow_force_pushes",
        "allow_deletions",
        "required_conversation_resolution",
        "required_status_checks.strict",
        "required_pull_request_reviews.present",
        "required_pull_request_reviews.required_approving_review_count",
    }
    # The omissions are deliberate: their safe direction is a policy choice
    # rather than a universal, so asserting one would invent policy for every
    # adopter. Named so a future reader sees a decision, not an oversight.
    for policy_choice in (
        "lock_branch",
        "required_signatures",
        "block_creations",
        "allow_fork_syncing",
        "restrictions_present",
        "codeowners_present",
    ):
        assert policy_choice not in WEAK_POSTURES


@pytest.mark.parametrize("field", sorted(WEAK_POSTURES))
def test_every_weak_posture_requires_its_own_documented_exception(field: str) -> None:
    """Deleting ANY exception must leave the weakness reported, not just one.

    Retirement was enforced for every exception and this direction for exactly
    one, so removing any other left a live weakness silently undocumented — its
    reason, compensating controls and retirement condition gone while the
    configuration stayed weak. Parametrized per posture: a single case would be
    satisfied by one entry working while the rest went unread.
    """
    policy = copy.deepcopy(load_policy())
    found, weak_value = resolve_expected(policy["expected"], field)
    assert found, f"{field} is named as a weak posture but is not in the shipped table"

    # Put the table on the weak side and remove every exception.
    parts = field.split(".")
    node = policy["expected"]
    for part in parts[:-1]:
        node = node[part]
    node[parts[-1]] = WEAK_POSTURES[field]
    policy["documented_exceptions"] = []

    issues = validate_policy_document(policy)

    assert any(f"expected.{field} is" in issue for issue in issues), issues
    assert weak_value is not None or True


def test_a_malformed_exception_entry_does_not_crash_the_collector() -> None:
    """The missing-keys check reports it; the collector then called .get() on a string.

    The gate crashed instead of returning the finding it had already made — the
    third instance of that shape on this change.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_pull_request_reviews"]["required_approving_review_count"] = 1
    policy["documented_exceptions"] = ["not a mapping"]

    issues = validate_policy_document(policy)

    assert any("missing keys" in issue for issue in issues), issues


def test_the_shipped_policy_documents_every_weakness_it_declares() -> None:
    """The accept side, against the real table rather than a constructed one."""
    assert [
        issue
        for issue in validate_policy_document(load_policy())
        if "without a documented" in issue
    ] == []


def test_an_exception_that_outlives_its_weakness_is_refused() -> None:
    """The retirement half, which nothing enforced for any exception but one.

    An exception claiming `required_approving_review_count: 0` must go when the
    count rises. Left behind, its reason, compensating controls and retirement
    condition keep asserting something that is no longer true — which is how a
    policy accumulates permanent "temporary" text.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_pull_request_reviews"]["required_approving_review_count"] = 1

    issues = validate_policy_document(policy)

    assert any("no longer exists" in issue for issue in issues), issues


def test_a_review_exception_is_refused_when_the_review_block_is_absent() -> None:
    """With `present: false` the live comparison skips every nested review field.

    An exception naming one is then bound to something no observed drift can
    retire — the unaudited-control case again, reached through a value rather
    than a field name.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_pull_request_reviews"]["present"] = False

    issues = validate_policy_document(policy)

    assert any("skips every nested review field" in issue for issue in issues), issues


def test_an_unhashable_declared_context_fails_through_the_gate() -> None:
    """A malformed declared context must be reported, not raise inside the validator.

    `_required_check_issues` records it correctly and the membership set then
    crashed on it — the gate that exists to report findings falling over on the
    very input it is reporting about.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["checks"][0]["context"] = ["not", "a", "string"]
    policy["documented_exceptions"].append(
        {
            "field": "required_status_checks.checks",
            "value": "Some Omitted Context",
            "reason": "documented omission",
            "compensating_controls": "none",
            "retires_when": "the context is required",
        }
    )

    issues = validate_policy_document(policy)

    assert any("must name a context" in issue for issue in issues), issues


@pytest.mark.parametrize("value", [None, 123, ["a"], {"context": "a"}, "", "   "])
def test_an_omitted_context_exception_must_name_a_context_string(value: object) -> None:
    """Membership against context names: a non-string can never match one.

    The exception would apply forever, and an unhashable value raises TypeError
    inside the validator rather than reporting an issue — a crash where a
    finding belongs.
    """
    policy = copy.deepcopy(load_policy())
    policy["documented_exceptions"].append(
        {
            "field": "required_status_checks.checks",
            "value": value,
            "reason": "malformed target",
            "compensating_controls": "none",
            "retires_when": "never",
        }
    )

    issues = validate_policy_document(policy)

    assert any("must name a required context" in issue for issue in issues), issues


def test_an_exception_naming_an_unaudited_control_is_refused() -> None:
    """Resolving inside `expected` is not enough — it must be a field the gate reads.

    An adopter can add a control the live comparison never looks at, point an
    exception at it, and have both resolve cleanly. The exception is then bound to
    something no observed drift can ever retire: the same rot the binding rule
    removes, with one more step in front of it.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["invented_control"] = False
    policy["documented_exceptions"][0]["field"] = "invented_control"
    policy["documented_exceptions"][0]["value"] = False

    issues = validate_policy_document(policy)

    assert any("does not audit" in issue for issue in issues), issues


def test_every_audited_field_is_a_valid_exception_target() -> None:
    """The accept side, asserted against the real table rather than a list.

    A restriction that refused a legitimate field would be found only by the
    adopter it blocked, so each audited control is exercised as an exception
    target using the value the shipped policy actually declares.
    """
    for field in sorted(AUDITED_FIELDS):
        policy = copy.deepcopy(load_policy())
        found, actual = resolve_expected(policy["expected"], field)
        assert found, f"{field} is advertised as audited but is not in the shipped table"
        if field == "required_status_checks.checks":
            continue  # membership semantics, covered by its own case
        # Appended rather than replacing the list: removing the shipped
        # zero-approval exception would trip its own required-direction rule and
        # be mistaken for this field being refused.
        policy["documented_exceptions"].append(
            {
                "field": field,
                "value": actual,
                "reason": "exercising the accept side",
                "compensating_controls": "none",
                "retires_when": "never",
            }
        )
        issues = [i for i in validate_policy_document(policy) if field in i]
        assert issues == [], f"{field} was refused as an exception target: {issues}"


def test_an_exception_bound_to_nothing_is_refused() -> None:
    """An exception naming a field outside `expected` can never be retired.

    It cannot be checked, no configuration change removes it, and it reads as a
    live deviation forever — the rot this rule exists to prevent, wearing the
    shape of documentation.
    """
    # An AUDITED field that the table omits. A field the gate does not audit is
    # refused earlier and by a different rule; this is the remaining case where a
    # resolvable-looking exception points at nothing.
    policy = copy.deepcopy(load_policy())
    policy["documented_exceptions"][0]["field"] = "required_status_checks.strict"
    del policy["expected"]["required_status_checks"]["strict"]

    issues = validate_policy_document(policy)

    assert any("bound to nothing can never be retired" in issue for issue in issues), issues


def test_an_omitted_context_exception_retires_when_the_context_is_required() -> None:
    """Membership, not equality: this exception documents a context NOT required.

    The adopters' transition-state exception — the gate's own context not yet
    self-anchored — must be refused once that context is declared, so the
    retirement condition is enforceable rather than aspirational.
    """
    policy = copy.deepcopy(load_policy())
    policy["documented_exceptions"].append(
        {
            "field": "required_status_checks.checks",
            "value": "Main Gate Coverage Audit / Enforce Branch Protection Policy",
            "reason": "the gate's own context is not yet self-anchored",
            "compensating_controls": "the scheduled audit reports its own failure",
            "retires_when": "the context is added to the required set",
        }
    )
    assert validate_policy_document(policy) == [], "an omitted context is a live deviation"

    # Now require it: the exception must retire.
    policy["expected"]["required_status_checks"]["checks"].append(
        {
            "context": "Main Gate Coverage Audit / Enforce Branch Protection Policy",
            "app_id": 15368,
        }
    )
    issues = validate_policy_document(policy)

    assert any("has been retired" in issue for issue in issues), issues


@pytest.mark.parametrize("value", [False, 0.0])
def test_an_exception_value_of_the_wrong_type_does_not_bind(value: object) -> None:
    """`False == 0` and `0.0 == 0`, so equality alone is not agreement.

    Both would otherwise bind the integer zero-approval setting and be treated as
    documenting it, while declaring something the table does not say.
    """
    policy = copy.deepcopy(load_policy())
    policy["documented_exceptions"][0]["value"] = value

    issues = validate_policy_document(policy)

    assert any("no longer exists" in issue for issue in issues), issues


def test_zero_approval_count_requires_a_documented_exception() -> None:
    policy = copy.deepcopy(load_policy())
    policy["documented_exceptions"] = []

    issues = validate_policy_document(policy)

    assert any("documented exception" in issue for issue in issues)


def test_matching_live_configuration_passes() -> None:
    policy = load_policy()

    assert compare_live_to_policy(policy, _live_matching_policy(policy)) == []


def test_weakened_live_protection_fails() -> None:
    policy = load_policy()
    live = _live_matching_policy(policy)
    live["enforce_admins"] = {"enabled": False}
    live["required_status_checks"]["checks"] = live["required_status_checks"]["checks"][:-1]

    issues = compare_live_to_policy(policy, live)

    assert any(issue.startswith("enforce_admins") for issue in issues)
    assert any("missing from live protection" in issue for issue in issues)


@pytest.mark.parametrize("control", MERGEABILITY_KEYS)
def test_each_mergeability_control_is_actually_compared(control: str) -> None:
    """Enabling any of these must be reported, one field at a time.

    Parametrized per field rather than asserted as a group: a group assertion is
    satisfied by ONE of them being compared, which is how three could stay
    unread behind a fourth that works. Each case flips exactly one control, so
    the case that fails names the control nobody is looking at.

    These four are worth their own test because they decide whether main can be
    merged to at all. `lock_branch` makes the branch read-only and
    `required_signatures` fails every unsigned merge -- an administrator could
    enable either and the scheduled audit reported a clean match.
    """
    policy = load_policy()
    live = _live_matching_policy(policy)
    live[control] = {"enabled": not policy["expected"][control]}

    issues = compare_live_to_policy(policy, live)

    assert any(issue.startswith(f"{control}:") for issue in issues), (
        f"{control} drifted and the comparison reported: {issues}"
    )


@pytest.mark.parametrize("control", MERGEABILITY_KEYS)
def test_a_policy_omitting_a_mergeability_control_is_refused(control: str) -> None:
    """An undeclared control is an unmeasured one, so the table must not omit it.

    This is the half an adopter cannot supply on their own: before this change
    an unknown key in `expected` was simply never read, so declaring the field
    did nothing. Requiring it means a lifted table fails loudly until it is
    updated, which is the intended way a fix reaches every adopter.
    """
    policy = copy.deepcopy(load_policy())
    del policy["expected"][control]

    issues = validate_policy_document(policy)

    assert any(control in issue for issue in issues), (
        f"a policy without {control} was accepted: {issues}"
    )


def test_a_rebound_context_is_reported_though_its_name_is_unchanged() -> None:
    """The #740 defect: a required check can change WHO may satisfy it.

    Removing or replacing a context's source binding leaves its name in the
    response, so a name-only comparison reports a clean match while a different
    GitHub App -- or a legacy commit status -- satisfies branch protection in its
    place. Without a binding the name is the whole credential.
    """
    policy = load_policy()
    live = _live_matching_policy(policy)
    rebound = live["required_status_checks"]["checks"][0]
    original = rebound["app_id"]
    rebound["app_id"] = 99999

    issues = compare_live_to_policy(policy, live)

    assert any("app binding differs" in issue for issue in issues), issues
    assert any(rebound["context"] in issue for issue in issues), (
        "the report must name the context whose binding moved"
    )
    assert original != 99999


def test_an_unpinned_live_binding_is_reported() -> None:
    """`app_id: null` live against a pinned declaration means any app may report it."""
    policy = load_policy()
    live = _live_matching_policy(policy)
    live["required_status_checks"]["checks"][0]["app_id"] = None

    issues = compare_live_to_policy(policy, live)

    assert any("app binding differs" in issue for issue in issues), issues


def test_a_check_without_a_declared_app_id_is_refused() -> None:
    """Absent is not the same as null, and must not resolve to the weaker one.

    GitHub uses `null` for "any app may report this context" -- a real, weaker
    posture. If omitting the key silently meant that, the weakest binding would
    be what you get by writing nothing.
    """
    policy = copy.deepcopy(load_policy())
    del policy["expected"]["required_status_checks"]["checks"][0]["app_id"]

    issues = validate_policy_document(policy)

    assert any("does not declare app_id" in issue for issue in issues), issues


def test_an_explicit_null_app_id_is_accepted() -> None:
    """Opting into "any app" deliberately is allowed; doing it by omission is not.

    The accept side matters as much as the reject side: a validator that refused
    every `null` would force adopters to misdeclare a genuinely unpinned context.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["checks"][0]["app_id"] = None

    assert validate_policy_document(policy) == []


@pytest.mark.parametrize("bad_context", [123, None, "", "   "])
def test_a_live_context_is_never_coerced_into_the_declared_name(bad_context: object) -> None:
    """`str(123)` would normalise a malformed context into the key a table declares.

    A policy declaring the string context "123" would then compare cleanly
    against a live record holding numeric 123 — a normaliser making the two sides
    agree, which is the one thing a drift audit must never do.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["checks"] = [{"context": "123", "app_id": 15368}]
    live = _live_matching_policy(policy)
    live["required_status_checks"]["checks"][0]["context"] = bad_context

    issues = compare_live_to_policy(policy, live)

    assert any("without a usable context name" in issue for issue in issues), issues
    assert not any("app binding differs" in issue for issue in issues), (
        "a malformed context must not be matched against the declared one at all"
    )


def test_a_malformed_live_check_entry_is_not_silently_dropped() -> None:
    """Filtering non-objects would let a changed payload lose an entry quietly.

    The seven expected records plus one malformed element must not compare
    cleanly merely because the seven that survived the filter happen to match.
    """
    policy = load_policy()
    live = _live_matching_policy(policy)
    live["required_status_checks"]["checks"].append("PR Merge Gate / Not An Object")

    issues = compare_live_to_policy(policy, live)

    assert any("not objects" in issue for issue in issues), issues


@pytest.mark.parametrize("value", [15368.0, True])
def test_a_live_app_id_that_is_not_an_integer_is_reported(value: object) -> None:
    """`15368.0 == 15368` and `True == 1`, so equality alone is not agreement.

    The declared side already refuses these. Trusting Python equality on the
    measured side would let a changed payload match the table while carrying a
    different type — the comparison would be right about the number and wrong
    about what it is.
    """
    policy = load_policy()
    live = _live_matching_policy(policy)
    live["required_status_checks"]["checks"][0]["app_id"] = value

    issues = compare_live_to_policy(policy, live)

    assert any("non-integer app_id" in issue for issue in issues), issues


def test_a_live_check_without_an_app_id_is_not_read_as_unpinned() -> None:
    """Absent is not null on the measured side either.

    `.get("app_id")` returns None for both an explicit null and a missing key, so
    a live check omitting the field would read as the deliberate "any app
    permitted" posture and compare EQUAL to a table declaring it. GitHub always
    returns the key, so its absence means the payload changed or is malformed.

    Third instance of one shape in this change: a distinction enforced on the
    declared side and collapsed on the measured side. The declared side is
    reviewed before it lands; the measured side is the thing that moved.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["checks"][0]["app_id"] = None
    live = _live_matching_policy(policy)
    del live["required_status_checks"]["checks"][0]["app_id"]

    issues = compare_live_to_policy(policy, live)

    assert any("without an app_id field" in issue for issue in issues), issues


def test_a_context_reported_twice_by_live_protection_is_reported() -> None:
    """The same collapsing hazard, in the direction the gate actually audits.

    Rejecting duplicates in the DECLARED table left the LIVE side collapsing:
    an undeclared 99999 binding followed by the declared 15368 one keyed to the
    same context, and only the last survived the comparison. The extra binding
    disappeared from the audit whose purpose is to notice exactly that.
    """
    policy = load_policy()
    live = _live_matching_policy(policy)
    declared_first = live["required_status_checks"]["checks"][0]
    live["required_status_checks"]["checks"].insert(
        0, {"context": declared_first["context"], "app_id": 99999}
    )

    issues = compare_live_to_policy(policy, live)

    assert any("more than once" in issue for issue in issues), issues
    assert any(declared_first["context"] in issue for issue in issues), (
        "the report must name the repeated context"
    )


def test_the_retired_contexts_field_is_refused_when_left_beside_checks() -> None:
    """A half-finished migration must fail, not look complete.

    `checks` replaced `contexts` and nothing reads the old field. An adopter who
    adds `checks` and leaves `contexts` behind has a table that names required
    gates in a list compared against nothing — it reads as authoritative and is
    inert. That is the same class this whole change removes, arriving through the
    migration itself.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["contexts"] = [
        "PR Merge Gate / A Gate Nobody Compares"
    ]

    issues = validate_policy_document(policy)

    assert any("retired" in issue for issue in issues), issues


def test_a_context_declared_twice_is_refused() -> None:
    """One context has one binding; a repeat is discarded, not compared.

    The comparison keys by context, so a second declaration for the same context
    silently replaces the first. A table naming both 99999 and 15368 for one
    context would then validate AND compare cleanly against live protection
    holding only 15368 -- two declarations, one of them never checked against
    anything.
    """
    policy = copy.deepcopy(load_policy())
    checks = policy["expected"]["required_status_checks"]["checks"]
    checks.append({"context": checks[0]["context"], "app_id": 99999})

    issues = validate_policy_document(policy)

    assert any("more than once" in issue for issue in issues), issues


@pytest.mark.parametrize("value", [True, False])
def test_a_boolean_app_id_is_refused(value: bool) -> None:
    """`bool` is a subclass of `int`, so a naive integer check accepts it.

    Worse than a type slip: `True == 1`, so a boolean binding would compare EQUAL
    to app id 1 rather than merely being malformed.
    """
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["checks"][0]["app_id"] = value

    issues = validate_policy_document(policy)

    assert any("must be an integer or null" in issue for issue in issues), issues


def test_a_boolean_app_id_would_have_matched_app_one() -> None:
    """The consequence, not merely the shape: True compares equal to app id 1.

    Stated as its own case because "the validator rejects it" is a weaker claim
    than "here is what it would otherwise have matched".
    """
    assert True == 1  # noqa: E712 -- the point of the test is this equality
    assert isinstance(True, int)


def test_an_undeclared_live_context_is_reported() -> None:
    """A context required live but absent from the table is drift in the other direction."""
    policy = load_policy()
    live = _live_matching_policy(policy)
    live["required_status_checks"]["checks"].append(
        {"context": "Some Other Gate / Added Quietly", "app_id": 15368}
    )

    issues = compare_live_to_policy(policy, live)

    assert any("undeclared" in issue for issue in issues), issues


def test_absent_reviews_block_is_distinguished_from_zero_count() -> None:
    # The render#66 drift class: a missing required_pull_request_reviews block
    # must be reported as ABSENT, never conflated with a present zero-count.
    policy = load_policy()
    live = _live_matching_policy(policy)
    live["required_pull_request_reviews"] = None

    issues = compare_live_to_policy(policy, live)

    assert any("ABSENT" in issue for issue in issues)


def test_codeowners_resolution_follows_github_precedence(tmp_path: Path) -> None:
    """A .github/ file wins over root and docs/, as GitHub resolves it."""
    for location in (".github", "docs"):
        (tmp_path / location).mkdir()
    (tmp_path / "CODEOWNERS").write_text("* @root\n", encoding="utf-8")
    (tmp_path / "docs" / "CODEOWNERS").write_text("* @docs\n", encoding="utf-8")

    assert resolve_effective_codeowners(tmp_path) == tmp_path / "CODEOWNERS"

    (tmp_path / ".github" / "CODEOWNERS").write_text("", encoding="utf-8")
    effective = resolve_effective_codeowners(tmp_path)
    assert effective == tmp_path / ".github" / "CODEOWNERS"
    assert effective is not None  # equality above guarantees this; mypy cannot narrow it
    assert effective.read_text(encoding="utf-8") == "", (
        "an empty higher-precedence file must shadow the valid lower ones, "
        "because that is the posture GitHub applies"
    )


def test_codeowners_resolution_reports_absence(tmp_path: Path) -> None:
    assert resolve_effective_codeowners(tmp_path) is None


def test_offline_validation_rejects_a_policy_missing_expected_fields() -> None:
    """--offline is the only PR-time gate; it must not accept a gutted policy."""
    policy = load_policy()
    for field in ("enforce_admins", "required_status_checks", "required_pull_request_reviews"):
        incomplete = copy.deepcopy(policy)
        del incomplete["expected"][field]
        issues = validate_policy_document(incomplete)
        assert any(f"expected.{field} must be declared" in issue for issue in issues), (
            f"removing expected.{field} passed the offline gate"
        )


def test_offline_validation_rejects_an_empty_required_check_list() -> None:
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["checks"] = []
    issues = validate_policy_document(policy)
    assert any("checks is empty" in issue for issue in issues)


def test_offline_validation_rejects_missing_nested_fields() -> None:
    """Deleting a nested field must not pass offline and crash the live run."""
    policy = load_policy()
    cases = [
        (("required_status_checks", "strict"), "expected.required_status_checks.strict"),
        (("required_status_checks", "checks"), "expected.required_status_checks.checks"),
        (
            ("required_pull_request_reviews", "present"),
            "expected.required_pull_request_reviews.present",
        ),
        (
            ("required_pull_request_reviews", "dismiss_stale_reviews"),
            "expected.required_pull_request_reviews.dismiss_stale_reviews",
        ),
        (
            ("required_pull_request_reviews", "bypass_pull_request_allowances"),
            "expected.required_pull_request_reviews.bypass_pull_request_allowances",
        ),
    ]
    for (parent, field), expected_message in cases:
        incomplete = copy.deepcopy(policy)
        del incomplete["expected"][parent][field]
        issues = validate_policy_document(incomplete)
        assert any(expected_message in issue for issue in issues), (
            f"removing expected.{parent}.{field} passed the offline gate"
        )


def test_offline_validation_requires_each_bypass_category() -> None:
    """The live comparison builds all three categories; offline must demand them."""
    policy = load_policy()
    for category in ("users", "teams", "apps"):
        incomplete = copy.deepcopy(policy)
        del incomplete["expected"]["required_pull_request_reviews"][
            "bypass_pull_request_allowances"
        ][category]
        issues = validate_policy_document(incomplete)
        assert any(
            f"bypass_pull_request_allowances.{category} must be declared" in issue
            for issue in issues
        ), f"removing bypass_pull_request_allowances.{category} passed the offline gate"


def test_offline_validation_rejects_wrong_value_types() -> None:
    """A bare string would be compared character by character after merge."""
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["checks"] = "PR Merge Gate / Coverage"
    assert any("must be a list of" in issue for issue in validate_policy_document(policy))

    # A list of bare strings is the pre-#740 shape: it declares contexts with no
    # bindings at all, and must be refused rather than read as unpinned.
    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["checks"] = ["PR Merge Gate / Coverage"]
    assert any("must be an object" in issue for issue in validate_policy_document(policy))

    policy = copy.deepcopy(load_policy())
    policy["expected"]["required_status_checks"]["strict"] = "true"
    assert any(
        "required_status_checks.strict must be a boolean" in issue
        for issue in validate_policy_document(policy)
    )

    policy = copy.deepcopy(load_policy())
    policy["expected"]["enforce_admins"] = "true"
    assert any(
        "expected.enforce_admins must be a boolean" in issue
        for issue in validate_policy_document(policy)
    )


def test_offline_validation_rejects_wrong_review_value_types() -> None:
    """A string "true" or "0" would merge and mismatch only in the live run."""
    base = load_policy()

    policy = copy.deepcopy(base)
    policy["expected"]["required_pull_request_reviews"]["dismiss_stale_reviews"] = "true"
    assert any(
        "dismiss_stale_reviews must be a boolean" in issue
        for issue in validate_policy_document(policy)
    )

    policy = copy.deepcopy(base)
    policy["expected"]["required_pull_request_reviews"]["required_approving_review_count"] = "0"
    assert any(
        "required_approving_review_count must be an integer" in issue
        for issue in validate_policy_document(policy)
    )

    policy = copy.deepcopy(base)
    policy["expected"]["required_pull_request_reviews"]["bypass_pull_request_allowances"][
        "users"
    ] = "nobody"
    assert any(
        "bypass_pull_request_allowances.users must be a list" in issue
        for issue in validate_policy_document(policy)
    )


def test_identity_is_corroborated_from_outside_the_document(tmp_path, monkeypatch):
    """A lifted table keeping its source repository must not pass.

    The document is the thing being validated, so its own `repository` field
    cannot establish which repository the checker is running in. Without an
    outside source, a sibling that lifts the table and forgets one field reads
    the original repository's protection, finds it matches, and goes green.
    """
    monkeypatch.setenv("GITHUB_REPOSITORY", "sgajbi/lotus-render")
    assert detect_repository(tmp_path) == "sgajbi/lotus-render"


# The CI-local container is python:3.11-slim, which ships no git binary. These
# two cases exercise git-derived identity, so in that lane they would assert the
# behaviour of an absent tool rather than of this code. Skipping is honest;
# asserting a fallback that cannot run there is not. They still execute in the
# unit lane, which is where the behaviour is actually verified.
requires_git = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git is required to exercise remote-derived repository identity",
)


@requires_git
def test_identity_falls_back_to_the_origin_remote(tmp_path, monkeypatch):
    """Locally there is no GITHUB_REPOSITORY; the remote is the equivalent fact."""
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "remote",
            "add",
            "origin",
            "https://github.com/sgajbi/lotus-example.git",
        ],
        check=True,
    )
    assert detect_repository(tmp_path) == "sgajbi/lotus-example"


@requires_git
def test_identity_ignores_the_checkout_directory_name(tmp_path, monkeypatch):
    """Worktrees and clones are routinely named something else."""
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    checkout = tmp_path / "some-unrelated-worktree-name"
    checkout.mkdir()
    subprocess.run(["git", "init", "--quiet", str(checkout)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "remote",
            "add",
            "origin",
            "git@github.com:sgajbi/lotus-example.git",
        ],
        check=True,
    )
    assert detect_repository(checkout) == "sgajbi/lotus-example"


@requires_git
def test_unknowable_identity_refuses(tmp_path, monkeypatch):
    """No env and no remote means the gate cannot know what it is validating."""
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert detect_repository(tmp_path) is None


def test_a_blank_repository_field_is_not_a_declaration(monkeypatch, tmp_path):
    """Present-but-empty must fail, not skip the comparison.

    An empty field would otherwise pass the mismatch check by having nothing to
    mismatch — the same gap as omitting the field, wearing the shape of a
    filled-in one.
    """
    policy = copy.deepcopy(load_policy())
    policy["repository"] = "   "

    issues = validate_policy_document(policy)
    blank = [issue for issue in issues if "no repository" in issue or "empty" in issue]

    assert blank, f"a blank repository field must be reported: {issues}"


def test_identity_is_unknowable_without_a_git_binary(tmp_path, monkeypatch):
    """No git is the same situation as no remote, not a crash.

    The caller refuses when identity is None, so returning None keeps the gate
    fail-closed. Raising would surface as an unhandled error in a lane that
    simply has no git, which reads as a broken checker rather than an
    uncorroborated identity.
    """
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    def no_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", no_git)

    assert detect_repository(tmp_path) is None
