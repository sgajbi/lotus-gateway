"""Assert that live branch protection matches the documented policy, field by field.

An undocumented protection exception is indistinguishable from a misconfiguration,
and a policy document that outlives the configuration it describes is worse than
none. This gate fails in both drift directions: when live protection weakens
relative to `quality/branch_protection_policy.v1.json`, and when the documented
zero-approval exception is removed without the configuration strengthening.

The policy document is the only repository-specific input, so a sibling
repository can lift this script verbatim and edit the table. Absent settings are
compared as absent, never coerced to false (a missing
`required_pull_request_reviews` block and `required_approving_review_count: 0`
are different postures and must be distinguishable).

**This file must pass `mypy --strict` and `ruff` under the strictest settings any
adopter uses.** Byte-identity is the mechanism by which a fix here reaches every
adopter, and a local lint or type setting strict enough to force even a cosmetic
edit forks the control: the copy then diverges permanently and later fixes stop
propagating. Three adopters already differ by two such edits. Keep the annotations
explicit rather than relying on inference, so lifting is never a choice between a
clean local build and a byte-identical control.

Usage:
  python scripts/check_branch_protection_policy.py --offline   # document shape only
  python scripts/check_branch_protection_policy.py             # live comparison (needs gh auth)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

POLICY_PATH = Path(__file__).resolve().parents[1] / "quality" / "branch_protection_policy.v1.json"

_REQUIRED_EXCEPTION_KEYS = {"field", "value", "reason", "compensating_controls", "retires_when"}

# Every field the live comparison reads. Without these lists an edit could drop
# a field, pass --offline in the blocking lane, and only fail hours later in the
# scheduled live run.
_BYPASS_CATEGORIES = ("users", "teams", "apps")

_REQUIRED_REVIEW_KEYS = (
    "required_approving_review_count",
    "dismiss_stale_reviews",
    "require_code_owner_reviews",
    "require_last_push_approval",
    "bypass_pull_request_allowances",
)

_BOOLEAN_REVIEW_KEYS = (
    "present",
    "dismiss_stale_reviews",
    "require_code_owner_reviews",
    "require_last_push_approval",
)

# Controls the branch-protection API returns that decide whether main can be
# merged to at all. `lock_branch` makes the branch read-only; `required_signatures`
# fails every unsigned merge; `block_creations` changes what may be created.
# Absent from this list they were never compared, so an administrator could
# enable any of them and the scheduled audit still reported a clean match.
_MERGEABILITY_EXPECTED_KEYS = (
    "lock_branch",
    "required_signatures",
    "block_creations",
    "allow_fork_syncing",
)

_BOOLEAN_EXPECTED_KEYS = (
    "enforce_admins",
    "required_linear_history",
    "allow_force_pushes",
    "allow_deletions",
    "required_conversation_resolution",
    "restrictions_present",
    "codeowners_present",
    *_MERGEABILITY_EXPECTED_KEYS,
)

_REQUIRED_EXPECTED_KEYS = (
    "enforce_admins",
    "required_linear_history",
    "allow_force_pushes",
    "allow_deletions",
    "required_conversation_resolution",
    "required_status_checks",
    "required_pull_request_reviews",
    "restrictions_present",
    "codeowners_present",
    # REQUIRED, not optional. An undeclared control is an unmeasured one, and
    # silence is precisely the defect this list closes: an adopter cannot fix it
    # by declaring the field unless the checker reads it, and the checker must
    # not pass a table that omits it.
    *_MERGEABILITY_EXPECTED_KEYS,
)


# Exactly the fields `compare_live_to_policy` reads. DERIVED from the same
# constants it uses rather than listed again, so the two cannot drift apart.
#
# An exception may only name one of these. Pointing one at an invented control --
# `expected.invented_control: false` plus a matching exception -- would otherwise
# validate cleanly while being bound to a field the live gate never reads: the
# same rot the binding rule removes, with one more step in front of it.
_AUDITED_EXCEPTION_FIELDS = frozenset(
    {
        *_BOOLEAN_EXPECTED_KEYS,
        "required_status_checks.strict",
        "required_status_checks.checks",
        "required_pull_request_reviews.present",
        *(f"required_pull_request_reviews.{key}" for key in _REQUIRED_REVIEW_KEYS),
        *(
            f"required_pull_request_reviews.bypass_pull_request_allowances.{category}"
            for category in _BYPASS_CATEGORIES
        ),
    }
)


# Postures that must be DOCUMENTED when chosen: the value is weaker than the
# alternative and an undocumented deviation is indistinguishable from a mistake.
# This generalises the zero-approval rule rather than sitting beside it -- that
# rule was the only one binding a weak setting to its exception, so deleting any
# OTHER exception left a live weakness silently undocumented.
#
# Deliberately NOT exhaustive. `lock_branch`, `required_signatures`,
# `block_creations`, `allow_fork_syncing`, `restrictions_present` and
# `codeowners_present` are absent because their safe direction is a policy choice
# rather than a universal, and asserting one here would be inventing policy for
# every adopter. Drift in them is still compared against the declared table; what
# is not claimed is which value they ought to hold.
_WEAK_POSTURES: dict[str, Any] = {
    "enforce_admins": False,
    "required_linear_history": False,
    "allow_force_pushes": True,
    "allow_deletions": True,
    "required_conversation_resolution": False,
    # `strict: false` drops the up-to-date-branch requirement, so a merge can be
    # approved against a base it was never tested on.
    "required_status_checks.strict": False,
    "required_pull_request_reviews.present": False,
    # A stale approval surviving new commits means the approved tree is not the
    # merged tree. `require_last_push_approval` and `require_code_owner_reviews`
    # are deliberately NOT here: not enabling a stronger option is a policy
    # choice, whereas switching dismissal off weakens a control that is on.
    "required_pull_request_reviews.dismiss_stale_reviews": False,
    "required_pull_request_reviews.required_approving_review_count": 0,
}


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    policy: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return policy


def detect_repository(repo_root: Path) -> str | None:
    """Return the repository this checkout actually is, or None if unknowable.

    Identity must be corroborated from OUTSIDE the policy document. The document
    is the thing being validated, so trusting its own `repository` field lets a
    lifted table point at the repository it was copied from: the checker then
    reads someone else's protection, finds it matches, and passes. A sibling
    that lifts the table and forgets to edit one field gets a green gate that
    measured nothing about itself.

    `GITHUB_REPOSITORY` is authoritative in Actions. Locally the origin remote
    is the equivalent fact, and it is read rather than the directory name
    because worktrees and clones are routinely named something else.
    """
    from_env = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if from_env:
        return from_env

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
        )
    except (OSError, FileNotFoundError):
        # No git binary is the same situation as no remote: identity cannot be
        # corroborated from outside the document, so it is unknowable rather
        # than an error to crash on. The caller already refuses on None.
        return None
    if result.returncode != 0:
        return None
    url = result.stdout.strip()
    if not url:
        return None
    url = url.removesuffix(".git")
    if url.startswith("git@"):
        url = url.partition(":")[2]
    parts = [part for part in url.replace("\\", "/").split("/") if part]
    if len(parts) < 2:
        return None
    return f"{parts[-2]}/{parts[-1]}"


def _required_check_issues(declared: Any) -> list[str]:
    """Each required context must name the app permitted to satisfy it.

    The table mirrors the API's own `required_status_checks.checks` shape --
    `[{"context": ..., "app_id": ...}]` -- so the declaration compares against
    the response with no translation between them. A normaliser sitting between
    the declared and the measured is a place where the two can be made to agree.

    `app_id: null` is MEANINGFUL: GitHub uses it for "any app may report this
    context", which is a real and deliberately weaker posture. So an ABSENT
    `app_id` is refused and an explicit `null` is required to opt into it.
    Otherwise the weakest binding would be the one you get by writing nothing --
    the same failure removed from the four mergeability controls, in a new place.

    Without a binding the context name is the whole credential: any GitHub App
    able to post a status by that name satisfies the required check.
    """
    if not isinstance(declared, list):
        return [
            "expected.required_status_checks.checks must be a list of "
            '{"context": ..., "app_id": ...} objects'
        ]
    if not declared:
        return ["expected.required_status_checks.checks is empty: nothing would be required"]

    issues: list[str] = []
    seen: set[str] = set()
    for index, check in enumerate(declared):
        if not isinstance(check, dict):
            issues.append(f"required_status_checks.checks[{index}] must be an object")
            continue
        context = check.get("context")
        label = context if isinstance(context, str) and context.strip() else f"[{index}]"
        if not isinstance(context, str) or not context.strip():
            issues.append(f"required_status_checks.checks[{index}] must name a context")
        else:
            # A context declared twice collapses to one binding when compared, so
            # the discarded declaration is never checked against anything: a table
            # naming both 99999 and 15368 would compare cleanly against live
            # protection holding only 15368. Two declarations for one context are
            # not a field-by-field audit of either.
            if context in seen:
                issues.append(
                    f"required_status_checks.checks declares {context!r} more than once: "
                    "one context has one binding, and a repeated declaration is silently "
                    "discarded rather than compared"
                )
            seen.add(context)
        if "app_id" not in check:
            issues.append(
                f"required_status_checks.checks {label!r} does not declare app_id: "
                "name the app permitted to satisfy this context, or declare null "
                "to allow any app deliberately"
            )
        elif check["app_id"] is not None and (
            # `bool` is a subclass of `int` in Python, so `True` would satisfy an
            # int check and then compare EQUAL to app id 1. The declaration would
            # pass the blocking offline gate and match the wrong app.
            isinstance(check["app_id"], bool) or not isinstance(check["app_id"], int)
        ):
            issues.append(
                f"required_status_checks.checks {label!r} app_id must be an integer or null"
            )
    return issues


def _undocumented_weakness_issues(
    expected: dict[str, Any], exceptions: list[dict[str, Any]]
) -> list[str]:
    """Every weak posture must carry an exception, not only the zero-approval one.

    LIMIT, stated rather than left to be discovered: this covers scalar postures
    only. An omitted-context exception cannot be required in this direction,
    because "which contexts ought to be present" is not derivable from the table
    -- `checks` IS the declaration of what must be required, so an omitted
    context is indistinguishable from one that was never wanted. Such an
    exception is still checked in the retirement direction: it is refused once
    the context it names becomes required.

    Retirement was enforced for all exceptions and this direction for exactly
    one, so deleting any OTHER exception left the weakness live and undocumented
    -- losing its reason, compensating controls and retirement condition while
    the configuration stayed weak. That is the half of the promise that was not
    true.
    """
    # Only mapping entries. A malformed one -- a bare string -- is already
    # reported by the missing-keys check above, and calling `.get()` on it here
    # raised AttributeError: the gate crashing instead of returning the finding
    # it had already made. Third instance of that shape on this PR.
    documented = {str(e.get("field", "")) for e in exceptions if isinstance(e, dict)}
    issues: list[str] = []

    # Two weaknesses that are not scalar postures and so cannot live in the map.
    #
    # An UNBOUND required check -- `app_id: null` -- is the explicitly weaker
    # "any app may report this context" posture, and the omitted-context
    # exception form cannot document it: that form reads its value as a context
    # NOT required, and retires once the context is declared, which is the
    # opposite condition.
    _found, declared_checks = _resolve_expected(expected, "required_status_checks.checks")
    unbound = sorted(
        check["context"]
        for check in (declared_checks or [])
        if isinstance(check, dict)
        and isinstance(check.get("context"), str)
        and "app_id" in check
        and check["app_id"] is None
    )
    for context in unbound:
        if f"required_status_checks.checks.app_id:{context}" not in documented:
            issues.append(
                f"required_status_checks.checks {context!r} permits any app (app_id: null) "
                "without a documented exception: name it as "
                f"'required_status_checks.checks.app_id:{context}' or pin the app"
            )

    # A NON-EMPTY bypass lets the named principal evade the review requirement
    # entirely, so its reason and retirement condition matter as much as any
    # scalar's.
    _found, bypass = _resolve_expected(
        expected, "required_pull_request_reviews.bypass_pull_request_allowances"
    )
    if isinstance(bypass, dict):
        populated = sorted(
            category
            for category in _BYPASS_CATEGORIES
            if isinstance(bypass.get(category), list) and bypass[category]
        )
        for category in populated:
            field = f"required_pull_request_reviews.bypass_pull_request_allowances.{category}"
            if field not in documented:
                issues.append(
                    f"{field} is non-empty without a documented exception: the named "
                    f"{category} can evade the review requirement"
                )

    for field, weak_value in _WEAK_POSTURES.items():
        found, actual = _resolve_expected(expected, field)
        if not found:
            continue
        # `False == 0` and `0.0 == 0`, so the type must match exactly for a
        # declared value to count as this weak posture.
        if actual == weak_value and type(actual) is type(weak_value):
            if field not in documented:
                issues.append(
                    f"expected.{field} is {actual!r} without a documented exception: "
                    "either strengthen protection or document the deliberate deviation"
                )
    return issues


def _resolve_expected(expected: dict[str, Any], field: str) -> tuple[bool, Any]:
    """Resolve a dotted `field` inside `expected`. Returns (found, value)."""
    node: Any = expected
    for part in field.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _exception_binding_issues(expected: dict[str, Any], exception: dict[str, Any]) -> list[str]:
    """An exception must document a deviation that is still present.

    The zero-approval rule already binds ONE exception to its setting: a table
    claiming `required_approving_review_count: 0` without the exception fails.
    That invariant is what makes the table's promise true -- an exception cannot
    be silently deleted while the configuration stays weak.

    Nothing bound any OTHER exception, in either direction. So an exception could
    outlive the weakness it documents, which is how a policy accumulates
    permanent "temporary" text, and the reason, compensating controls and
    retirement condition would keep asserting something no longer true.

    This binds every exception generically rather than adding a second special
    case: the deviation it names must still be visible in `expected`.

    `required_status_checks.checks` is membership rather than equality -- an
    exception there documents a context deliberately NOT required, so it retires
    when that context is declared.
    """
    field = str(exception.get("field", ""))
    value = exception.get("value")

    if field.startswith("required_status_checks.checks.app_id:"):
        # A per-context binding exception. Its target is the unpinned check, so
        # it retires when that context gains an app_id rather than when a value
        # changes; handled here rather than by the scalar rules below.
        context = field.partition(":")[2]
        _found, declared = _resolve_expected(expected, "required_status_checks.checks")
        bindings = {
            check["context"]: check.get("app_id")
            for check in (declared or [])
            if isinstance(check, dict) and isinstance(check.get("context"), str)
        }
        if context not in bindings:
            return [
                f"documented exception names an unpinned binding for {context!r}, which is "
                "not a declared required context"
            ]
        if value is not None:
            # The exception documents "any app may report this", which IS the
            # null binding. Any other value describes a posture the table does
            # not hold, so nothing could ever retire it.
            return [
                f"documented exception for {field} must declare null, not {value!r}: "
                "it documents the unpinned binding itself"
            ]
        if bindings[context] is not None:
            return [
                f"documented exception says {context!r} permits any app, but it is now pinned "
                f"to {bindings[context]!r}: the deviation has been retired, so remove it"
            ]
        return []

    if field.startswith("required_pull_request_reviews.bypass_pull_request_allowances."):
        category = field.rpartition(".")[2]
        _found, bypass = _resolve_expected(
            expected, "required_pull_request_reviews.bypass_pull_request_allowances"
        )
        entries = bypass.get(category) if isinstance(bypass, dict) else None
        if not isinstance(entries, list) or not entries:
            # The retirement direction: with the allowance emptied, nobody can
            # evade review through it and the exception documents nothing.
            return [
                f"documented exception for {field} but that allowance is empty: "
                "the deviation it documents has been retired, so remove the exception"
            ]
        return []

    if field not in _AUDITED_EXCEPTION_FIELDS:
        # Resolving inside `expected` is not enough: an adopter can add a control
        # the live comparison never reads, point an exception at it, and the
        # exception is bound to something no observed drift can ever retire.
        return [
            f"documented exception names {field!r}, which the live comparison does not audit: "
            "an exception must name a control the gate actually reads, or no configuration "
            "change can retire it"
        ]

    if field.startswith("required_pull_request_reviews.") and field != (
        "required_pull_request_reviews.present"
    ):
        # With the review block declared absent, the live comparison skips every
        # nested field -- so an exception naming one is bound to something no
        # observed drift can retire, exactly like an unaudited control.
        present_found, present = _resolve_expected(
            expected, "required_pull_request_reviews.present"
        )
        if present_found and present is not True:
            return [
                f"documented exception names {field!r} while "
                "required_pull_request_reviews.present is not true: the live comparison "
                "skips every nested review field, so nothing can retire this exception"
            ]

    if field == "required_status_checks.checks":
        found, declared = _resolve_expected(expected, field)
        if not found or not isinstance(declared, list):
            # Returning nothing here made the exception unverifiable AND silent:
            # `_required_check_issues` reports the malformed table, but this
            # exception then binds to something that cannot be read at all.
            return [
                f"documented exception for {field} cannot be checked because the declared "
                "checks are missing or not a list"
            ]
        if not isinstance(value, str) or not value.strip():
            # Membership against a set of context names. A non-string is never in
            # it, so the exception would apply forever; an unhashable value would
            # raise TypeError inside the validator rather than report an issue.
            return [
                f"documented exception for {field} must name a required context as a "
                f"non-blank string, not {value!r}: no context can ever match it, so "
                "adding the check would not retire the exception"
            ]
        # Only validated strings. An unhashable declared context -- a list or
        # object -- would raise TypeError building this set, so `_required_check_issues`
        # would correctly record the malformed entry and then the validator would
        # crash before returning it. A gate that exists to report findings must
        # not fall over on the input it is reporting about.
        contexts = {
            check["context"]
            for check in declared
            if isinstance(check, dict) and isinstance(check.get("context"), str)
        }
        if value in contexts:
            return [
                f"documented exception for {field} names {value!r}, which IS now a required "
                "context: the deviation it documents has been retired, so remove the exception"
            ]
        return []

    if field in _WEAK_POSTURES:
        weak = _WEAK_POSTURES[field]
        if value != weak or type(value) is not type(weak):
            # An exception declaring the STRONG value documents no deviation and
            # can sit there permanently while the control is already safe --
            # contradicting the promise that exceptions bind to weaknesses.
            return [
                f"documented exception for {field!r} declares {value!r}, which is not the "
                f"weak posture {weak!r} this control is registered with: an exception must "
                "document a deviation, not the safe value"
            ]

    found, actual = _resolve_expected(expected, field)
    if not found:
        # An exception bound to nothing is the rot itself: it cannot be checked,
        # cannot be retired by any change, and reads as a live deviation forever.
        return [
            f"documented exception names {field!r}, which is not a field of `expected`: "
            "an exception bound to nothing can never be retired by a configuration change"
        ]
    # Exact types, not just equality and boolean-ness. `0.0 == 0` and neither is
    # a bool, so a float exception value would bind an integer setting and be
    # treated as documenting it -- the same trap as `False == 0`, one type along.
    if actual != value or type(actual) is not type(value):
        return [
            f"documented exception for {field!r} claims {value!r} but the policy declares "
            f"{actual!r}: the deviation it documents no longer exists, so remove the exception"
        ]
    return []


def validate_policy_document(policy: dict[str, Any]) -> list[str]:
    """Offline shape check: the document must be complete enough to gate against."""
    issues: list[str] = []

    # Present-but-blank is not a declaration. An empty identity field would pass
    # the mismatch comparison by having nothing to mismatch -- the same gap as
    # omitting it, wearing the shape of a filled-in field.
    if not str(policy.get("repository", "")).strip():
        issues.append(
            "policy declares no repository: the identity field is present but "
            "empty, so nothing can be compared against this checkout"
        )
    for key in ("repository", "protected_branch", "expected", "documented_exceptions"):
        if key not in policy:
            issues.append(f"policy is missing required key: {key}")
    authority = policy.get("review_authority", {})
    for key in ("review_lead", "mergeable_meaning", "escalation"):
        if not str(authority.get(key, "")).strip():
            issues.append(f"review_authority.{key} must be documented")
    expected = policy.get("expected", {})
    for key in _REQUIRED_EXPECTED_KEYS:
        if key not in expected:
            issues.append(f"expected.{key} must be declared")
    checks = expected.get("required_status_checks", {})
    for key in ("strict", "checks"):
        if key not in checks:
            issues.append(f"expected.required_status_checks.{key} must be declared")
    if "contexts" in checks:
        # `checks` REPLACED `contexts`; nothing reads the old field. Left beside
        # the new one it is a list of required gates that looks authoritative and
        # is compared against nothing -- so a migration that adds `checks` and
        # forgets to remove `contexts` can name a context the audit ignores.
        issues.append(
            "expected.required_status_checks.contexts is retired and is read by nothing: "
            "remove it, and declare every required context in `checks` with its app_id"
        )
    if "checks" in checks:
        issues.extend(_required_check_issues(checks["checks"]))
    if "strict" in checks and not isinstance(checks["strict"], bool):
        issues.append("expected.required_status_checks.strict must be a boolean")
    for key in _BOOLEAN_EXPECTED_KEYS:
        if key in expected and not isinstance(expected[key], bool):
            issues.append(f"expected.{key} must be a boolean")
    declared_reviews = expected.get("required_pull_request_reviews", {})
    if "present" not in declared_reviews:
        issues.append("expected.required_pull_request_reviews.present must be declared")
    elif declared_reviews.get("present"):
        for key in _REQUIRED_REVIEW_KEYS:
            if key not in declared_reviews:
                issues.append(f"expected.required_pull_request_reviews.{key} must be declared")
        for key in _BOOLEAN_REVIEW_KEYS:
            if key in declared_reviews and not isinstance(declared_reviews[key], bool):
                issues.append(f"expected.required_pull_request_reviews.{key} must be a boolean")
        count = declared_reviews.get("required_approving_review_count")
        if count is not None and (isinstance(count, bool) or not isinstance(count, int)):
            issues.append(
                "expected.required_pull_request_reviews."
                "required_approving_review_count must be an integer"
            )
        bypass = declared_reviews.get("bypass_pull_request_allowances", {})
        for category in _BYPASS_CATEGORIES:
            if category not in bypass:
                issues.append(
                    "expected.required_pull_request_reviews."
                    f"bypass_pull_request_allowances.{category} must be declared"
                )
            elif not isinstance(bypass[category], list):
                issues.append(
                    "expected.required_pull_request_reviews."
                    f"bypass_pull_request_allowances.{category} must be a list"
                )
    for exception in policy.get("documented_exceptions", []):
        missing = _REQUIRED_EXCEPTION_KEYS - set(exception)
        if missing:
            issues.append(f"documented exception is missing keys: {sorted(missing)}")
        else:
            issues.extend(_exception_binding_issues(expected, exception))
    issues.extend(_undocumented_weakness_issues(expected, policy.get("documented_exceptions", [])))
    return issues


def fetch_live_protection(repository: str, branch: str) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "api", f"repos/{repository}/branches/{branch}/protection"],
        capture_output=True,
        text=True,
        check=True,
    )
    payload: dict[str, Any] = json.loads(result.stdout)
    return payload


def resolve_effective_codeowners(repo_root: Path) -> Path | None:
    """Return the CODEOWNERS file GitHub would apply, or None if there is none.

    GitHub does not merge the recognized locations: it uses the first file it
    finds, in this order. A stale or empty file in an earlier location shadows a
    valid one later, so presence-anywhere is not the posture GitHub enforces.
    """
    for location in (".github", "", "docs"):
        candidate = repo_root / location / "CODEOWNERS" if location else repo_root / "CODEOWNERS"
        if candidate.is_file():
            return candidate
    return None


def _enabled(node: Any) -> Any:
    return node.get("enabled") if isinstance(node, dict) else node


def _compare_required_checks(*, live: Any, declared: list[dict[str, Any]]) -> list[str]:
    """Compare required contexts AND the app bound to each.

    A required check whose source binding is removed or replaced keeps its name
    in the response, so comparing names alone reports a clean match while a
    different GitHub App -- or a legacy commit status -- satisfies branch
    protection in its place.
    """
    entries = list(live or [])
    live_checks = [check for check in entries if isinstance(check, dict)]
    # No coercion. `str(123)` would normalise a malformed numeric context into
    # the string key a policy declares and compare cleanly -- a normaliser making
    # the two sides agree, which is the one thing a drift audit must never do.
    named = [
        check
        for check in live_checks
        if isinstance(check.get("context"), str) and check["context"].strip()
    ]
    live_bindings = {check["context"]: check.get("app_id") for check in named}
    policy_bindings = {str(check["context"]): check.get("app_id") for check in declared}

    issues: list[str] = []
    unnamed = len(live_checks) - len(named)
    if unnamed:
        issues.append(
            f"live protection returned {unnamed} required-check record"
            f"{'' if unnamed == 1 else 's'} without a usable context name: "
            "an absent, blank or non-string context is not coerced into one"
        )
    # A malformed element is not an absent one. Filtering non-objects would let a
    # changed payload lose an entry and still compare cleanly against a table
    # that happens to match what survived.
    malformed = len(entries) - len(live_checks)
    if malformed:
        issues.append(
            f"live protection returned {malformed} required-check entr"
            f"{'y' if malformed == 1 else 'ies'} that are not objects: "
            "the payload cannot be fully interpreted, so it is not compared as if it could"
        )
    # `15368.0 == 15368` in Python and `True == 1`, so a float or boolean binding
    # compares EQUAL to the declared integer. Type the measured value rather than
    # trusting equality to mean the same thing on both sides.
    mistyped = sorted(
        check["context"]
        for check in named
        if "app_id" in check
        and check["app_id"] is not None
        and (isinstance(check["app_id"], bool) or not isinstance(check["app_id"], int))
    )
    if mistyped:
        issues.append(
            f"live protection reports non-integer app_id values for: {mistyped}; "
            "a float or boolean can compare equal to the declared integer"
        )
    # Absent is not null on the MEASURED side either. `.get()` returns None for
    # both, so a live check omitting `app_id` would read as the deliberate
    # "any app permitted" posture and match a table that declares it. GitHub
    # always returns the key, so its absence means the payload changed or is
    # malformed -- fail closed rather than resolve to the weaker reading.
    unbound = sorted(check["context"] for check in named if "app_id" not in check)
    if unbound:
        issues.append(
            f"live protection reports these contexts without an app_id field: {unbound}; "
            "an absent binding is not the same as an explicit null and is not compared as one"
        )
    # The same collapsing hazard as the declared side, in the direction the gate
    # is actually auditing. If live protection reports one context twice -- an
    # undeclared binding followed by the declared one -- keying by context keeps
    # only the last, and the extra binding disappears from a comparison whose
    # whole purpose is to notice it.
    if len(live_bindings) != len(named):
        repeated = sorted(
            {
                check["context"]
                for index, check in enumerate(named)
                if check["context"] in {other["context"] for other in named[:index]}
            }
        )
        issues.append(
            f"live protection reports these contexts more than once: {repeated}; "
            "each carries its own app binding and only the last would be compared"
        )
    missing = sorted(set(policy_bindings) - set(live_bindings))
    extra = sorted(set(live_bindings) - set(policy_bindings))
    if missing:
        issues.append(f"required_status_checks.checks missing from live protection: {missing}")
    if extra:
        issues.append(f"required_status_checks.checks present live but undeclared: {extra}")
    for context in sorted(set(policy_bindings) & set(live_bindings)):
        if live_bindings[context] != policy_bindings[context]:
            issues.append(
                f"required_status_checks.checks {context!r} app binding differs: "
                f"live={live_bindings[context]!r} policy={policy_bindings[context]!r}"
            )
    return issues


def compare_live_to_policy(policy: dict[str, Any], live: dict[str, Any]) -> list[str]:
    expected = policy["expected"]
    issues: list[str] = []

    scalar_fields = {
        "enforce_admins": _enabled(live.get("enforce_admins")),
        "required_linear_history": _enabled(live.get("required_linear_history")),
        "allow_force_pushes": _enabled(live.get("allow_force_pushes")),
        "allow_deletions": _enabled(live.get("allow_deletions")),
        "required_conversation_resolution": _enabled(live.get("required_conversation_resolution")),
        "restrictions_present": live.get("restrictions") is not None,
        **{key: _enabled(live.get(key)) for key in _MERGEABILITY_EXPECTED_KEYS},
    }
    for name, actual in scalar_fields.items():
        if actual != expected[name]:
            issues.append(f"{name}: live={actual!r} policy={expected[name]!r}")

    checks = live.get("required_status_checks") or {}
    if checks.get("strict") != expected["required_status_checks"]["strict"]:
        issues.append(f"required_status_checks.strict: live={checks.get('strict')!r}")
    issues.extend(
        _compare_required_checks(
            live=checks.get("checks"),
            declared=expected["required_status_checks"]["checks"],
        )
    )

    reviews = live.get("required_pull_request_reviews")
    expected_reviews = expected["required_pull_request_reviews"]
    if (reviews is not None) != expected_reviews["present"]:
        issues.append(
            "required_pull_request_reviews block presence: "
            f"live={'present' if reviews is not None else 'ABSENT'} "
            f"policy={'present' if expected_reviews['present'] else 'ABSENT'}"
        )
    elif reviews is not None:
        for key in (
            "required_approving_review_count",
            "dismiss_stale_reviews",
            "require_code_owner_reviews",
            "require_last_push_approval",
        ):
            if reviews.get(key) != expected_reviews[key]:
                issues.append(
                    f"required_pull_request_reviews.{key}: "
                    f"live={reviews.get(key)!r} policy={expected_reviews[key]!r}"
                )
        live_bypass = reviews.get("bypass_pull_request_allowances") or {}
        expected_bypass = expected_reviews["bypass_pull_request_allowances"]
        actual_bypass = {
            "users": sorted(u.get("login", "") for u in live_bypass.get("users", [])),
            "teams": sorted(t.get("slug", "") for t in live_bypass.get("teams", [])),
            "apps": sorted(a.get("slug", "") for a in live_bypass.get("apps", [])),
        }
        if actual_bypass != {k: sorted(v) for k, v in expected_bypass.items()}:
            issues.append(
                "required_pull_request_reviews.bypass_pull_request_allowances: "
                f"live={actual_bypass!r} policy={expected_bypass!r}"
            )

    effective_codeowners = resolve_effective_codeowners(Path(__file__).resolve().parents[1])
    codeowners = effective_codeowners is not None
    if codeowners != expected["codeowners_present"]:
        issues.append(
            f"CODEOWNERS presence: live={codeowners} policy={expected['codeowners_present']}"
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="validate the policy document only")
    args = parser.parse_args()

    policy = load_policy()
    issues = validate_policy_document(policy)

    declared = str(policy.get("repository", "")).strip()
    actual = detect_repository(POLICY_PATH.resolve().parents[1])
    if actual is None:
        issues.append(
            "cannot determine which repository this checkout is (no "
            "GITHUB_REPOSITORY and no origin remote); refusing rather than "
            "trusting the policy document's own repository field"
        )
    elif declared and declared.lower() != actual.lower():
        issues.append(
            f"policy declares repository {declared!r} but this checkout is "
            f"{actual!r}: a lifted policy table that keeps the source "
            "repository would validate the wrong repository and pass"
        )
    if not args.offline and not issues:
        live = fetch_live_protection(policy["repository"], policy["protected_branch"])
        issues.extend(compare_live_to_policy(policy, live))

    if issues:
        print("Branch-protection policy gate failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    mode = "document shape" if args.offline else "live configuration"
    print(f"Branch-protection policy gate passed ({mode}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
