"""Audit what the Main Releasability Gate said about every commit on main.

The gate is dispatched per merged pull request; this repository merges by
rebase, so a pull request holding N commits puts N on main and every one of
them must have a gate run - a commit that was never head becomes the deployed
tree on rollback and bisect. A run that is never created is not a failure, so
nothing else reports the loss; this audit does.

Three questions are reported separately because they need opposite responses
and answering only the first is how eight red commits stayed invisible here
(#774):

1. **Coverage** - was every commit evaluated at all? A gap is a dispatch
   failure. This is the load-bearing property and the only one ``--fail-on-gap``
   acts on.
2. **Current outcome** - what does each commit's newest verdict say? A failing
   one is a code failure that already happened and cannot be undone by
   dispatching more runs.
3. **History** - did a commit ever fail, even though a re-run later went green?
   Collapsing this into the current outcome would let a retry erase the record
   that the commit was broken when it landed.

Retry and pending handling is defined rather than incidental:

- the unit is the **attempt**, not the run. ``gh run rerun`` adds an attempt to
  an existing run rather than creating a new one, and the run listing reports
  only the newest attempt's conclusion - so a gate that failed and was re-run
  green would otherwise read as having never failed. Superseded attempts are
  fetched and counted;
- attempts are ordered oldest-first by when each *attempt* started, so the
  newest verdict decides the current outcome no matter what order the API
  returns, and a re-run of an older run sorts after a newer run rather than back
  in the older run's place;
- a re-run that goes green makes a commit RECOVERED, not PASSING: the earlier
  failing verdict is history and stays counted as one;
- an attempt still queued or in progress is pending. It never decides an outcome
  and never masks an existing verdict - a commit with a verdict plus a pending
  re-run keeps the verdict it has;
- ``timed_out`` and ``startup_failure`` are terminal *failures*. The gate ran and
  did not pass, so they count as failing rather than as an absent verdict.

Fail-closed by design (a watchdog that can pass while verifying nothing is
the same liveness defect it exists to catch):

- a missing ``gh`` binary is a failure under ``--fail-on-gap``, never a skip;
- a commit whose run listing cannot be fetched (rate limit, token scope,
  transient API failure) is UNVERIFIABLE, and unverifiable commits fail the
  audit under ``--fail-on-gap`` - they are unverified, not implicitly fine;
- so is a commit whose listing came back saturated at the fetch limit, or one
  superseded attempt of which could not be read: a history we cannot see in full
  is not a history we can report on;
- only attempts that reached a verdict count as evaluation: one cancelled
  seconds after dispatch evaluated nothing.

Failing commits are reported, not failed on. Failing the audit on them would
turn the eight historical reds into a permanent red that no action can clear,
and history is not to be rewritten to make a gate green. The count is printed
and pinned by tests so it cannot silently become zero, which makes its growth
a review question.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass

WORKFLOW = "main-releasability.yml"

# `gh run list` fetches 20 by default, and a commit that exceeded that would have
# its oldest runs silently dropped -- erasing exactly the early failure this
# audit promises to keep. Raised, and saturation is treated as unverifiable
# rather than assumed complete: an audit that cannot see all of the history
# cannot report on it.
_RUN_FETCH_LIMIT = 100

_SUCCESS_CONCLUSION = "success"

# `timed_out` and `startup_failure` are terminal failures, not absent verdicts.
# The gate ran and did not pass; reporting that as "no verdict" would have moved
# a red commit into the unverifiable column instead of the failing one.
_FAILING_CONCLUSIONS = frozenset({"failure", "timed_out", "startup_failure"})
_VERDICT_CONCLUSIONS = frozenset({_SUCCESS_CONCLUSION}) | _FAILING_CONCLUSIONS

# `cancelled`, `neutral`, `skipped` and `stale` stay deliberately outside the
# verdict set: none of them is the gate saying yes or no, and a commit whose only
# run was cancelled is unverified rather than good.
_PENDING_STATUSES = frozenset({"queued", "in_progress", "waiting", "requested", "pending"})

UNGATED = "ungated"
UNVERIFIABLE = "unverifiable"
PASSING = "passing"
RECOVERED = "recovered"
FAILING = "failing"


@dataclass(frozen=True)
class CommitOutcome:
    """What the gate said about one commit, across all three questions."""

    state: str
    detail: str = ""

    @property
    def is_covered(self) -> bool:
        """Whether the gate reached a verdict, whatever the verdict was.

        This is the coverage question and nothing else: a commit that failed is
        covered. Conflating it with "is the commit good" is the defect in #774.
        """

        return self.state in {PASSING, RECOVERED, FAILING}


def _git(*args: str) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def _record(conclusion: str, status: str, at: str, run_id: str, attempt: str) -> dict[str, str]:
    return {
        "conclusion": conclusion,
        "status": status,
        "startedAt": at,
        "databaseId": run_id,
        "attempt": attempt,
    }


def _earlier_attempt(run_id: str, attempt: int) -> dict[str, str] | None:
    """One superseded attempt of a run, or None when it cannot be read.

    ``gh run rerun`` does not create a second run: it adds an attempt to the
    existing one, and the run listing then reports only the newest attempt's
    conclusion. Without this, a gate that failed and was re-run green would read
    as having never failed -- erasing precisely the history this audit exists to
    keep, and doing it in the reassuring direction.
    """

    completed = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/attempts/{attempt}",
            "--jq",
            "{conclusion,status,run_started_at}",
        ],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    try:
        payload = json.loads(completed.stdout or "null")
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return _record(
        str(payload.get("conclusion") or ""),
        str(payload.get("status") or ""),
        str(payload.get("run_started_at") or ""),
        run_id,
        str(attempt),
    )


def _gate_runs(sha: str) -> list[dict[str, str]] | None:
    """Every gate *attempt* for one commit, in any order, or None if unknowable.

    Attempts rather than runs, because a re-run is an attempt of the same run
    and the listing shows only the newest one.

    Ordering is deliberately not established here. ``classify`` sorts, so the
    guarantee holds for every caller rather than only for this path.
    """

    completed = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--workflow",
            WORKFLOW,
            "--commit",
            sha,
            "--limit",
            str(_RUN_FETCH_LIMIT),
            "--json",
            "conclusion,status,startedAt,databaseId,attempt",
        ],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    try:
        runs = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        return None
    if not isinstance(runs, list):
        return None
    if len(runs) >= _RUN_FETCH_LIMIT:
        # The listing is saturated, so the oldest runs may have been dropped and
        # an early failure with them. Unverifiable, not complete.
        return None

    attempts: list[dict[str, str]] = []
    for run in runs:
        if not isinstance(run, dict):
            # Dropping the malformed entry and keeping the rest would let a
            # commit classify from a listing we know is not the listing -- a
            # PASSING verdict read off evidence with a hole in it. Unverifiable.
            return None
        run_id = str(run.get("databaseId") or "")
        try:
            newest = int(run.get("attempt") or 1)
        except (TypeError, ValueError):
            return None
        attempts.append(
            _record(
                str(run.get("conclusion") or ""),
                str(run.get("status") or ""),
                str(run.get("startedAt") or ""),
                run_id,
                str(newest),
            )
        )
        for superseded in range(1, newest):
            earlier = _earlier_attempt(run_id, superseded)
            if earlier is None:
                # An attempt we know exists and cannot read. Reporting the
                # history without it would be reporting a history we do not have.
                return None
            attempts.append(earlier)
    return attempts


def _oldest_first(attempts: list[dict[str, str]]) -> list[dict[str, str]]:
    """Order attempts by when each one started, not by list position.

    ``gh`` lists most-recent-first today, but an audit that decides which
    verdict is current from an undocumented ordering is only correct until that
    changes -- and would then report green commits as red with nothing to say
    why.

    Each attempt carries its own start time, which is what makes a re-run of an
    older run sort *after* a newer run rather than back in the older run's
    place. ``databaseId`` and ``attempt`` break ties, both zero-padded because
    these are strings and "10" sorts before "9".
    """

    return sorted(
        attempts,
        key=lambda run: (
            run["startedAt"],
            run["databaseId"].rjust(24, "0"),
            run["attempt"].rjust(6, "0"),
        ),
    )


def classify(attempts: list[dict[str, str]] | None) -> CommitOutcome:
    """Reduce one commit's gate attempts, in any order, to a single outcome."""

    if attempts is None:
        return CommitOutcome(UNVERIFIABLE, "run history could not be read in full")
    undated = [
        run
        for run in attempts
        if run["conclusion"] in _VERDICT_CONCLUSIONS and not run["startedAt"]
    ]
    if undated:
        # Ordering decides which verdict is current, so an attempt that carries a
        # verdict and no start time cannot be placed. Substituting the run's
        # creation time would put a re-run back at the original attempt's
        # position -- so an old run re-run to failure after a newer run passed
        # would read as RECOVERED when the commit is currently red. That is a
        # manufactured ordering presented as a measured one.
        return CommitOutcome(
            UNVERIFIABLE,
            f"{len(undated)} verdict(s) with no attempt start time; order cannot be established",
        )
    ordered = _oldest_first(attempts)
    verdicts = [run["conclusion"] for run in ordered if run["conclusion"] in _VERDICT_CONCLUSIONS]
    if verdicts:
        failures = [verdict for verdict in verdicts if verdict in _FAILING_CONCLUSIONS]
        if verdicts[-1] == _SUCCESS_CONCLUSION:
            if not failures:
                return CommitOutcome(PASSING)
            reasons = ", ".join(sorted(set(failures)))
            return CommitOutcome(
                RECOVERED,
                f"{len(failures)} failing verdict(s) ({reasons}), then green on re-run",
            )
        return CommitOutcome(FAILING, f"newest verdict is {verdicts[-1]}")
    if not ordered:
        return CommitOutcome(UNGATED)
    pending = sorted({run["status"] for run in ordered if run["status"] in _PENDING_STATUSES})
    if pending:
        return CommitOutcome(UNVERIFIABLE, f"still running ({', '.join(pending)}); no verdict yet")
    reached = sorted({run["conclusion"] or run["status"] for run in ordered})
    return CommitOutcome(UNVERIFIABLE, f"attempts exist without a verdict: {reached}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=60,
        help="how many commits of origin/main history to audit",
    )
    parser.add_argument(
        "--fail-on-gap",
        action="store_true",
        help=(
            "exit non-zero when a commit has no verdict-bearing releasability run "
            "OR when any commit could not be verified (unknown fails closed). "
            "Commits with a failing verdict are reported, never failed on: they "
            "are history, and no dispatch can clear them."
        ),
    )
    arguments = parser.parse_args()

    if shutil.which("gh") is None:
        print("gh is not available; cannot ask which commits the gate evaluated.")
        return 1 if arguments.fail_on_gap else 0

    commits = _git("log", f"-{arguments.limit}", "--format=%H %h %s", "origin/main")
    counts = {UNGATED: 0, UNVERIFIABLE: 0, PASSING: 0, RECOVERED: 0, FAILING: 0}
    ungated: list[str] = []

    for entry in commits:
        sha, short, subject = entry.split(" ", 2)
        outcome = classify(_gate_runs(sha))
        counts[outcome.state] += 1
        if outcome.state == UNGATED:
            ungated.append(short)
            print(f"UNGATED      {short}  {subject[:70]}")
        elif outcome.state == UNVERIFIABLE:
            print(f"UNVERIFIABLE {short}  ({outcome.detail})")
        elif outcome.state == FAILING:
            print(f"FAILING      {short}  {subject[:70]}")
        elif outcome.state == RECOVERED:
            print(f"RECOVERED    {short}  {subject[:70]}  ({outcome.detail})")

    ever_failed = counts[FAILING] + counts[RECOVERED]
    print(
        f"\naudited {len(commits)} commit(s) on main against {WORKFLOW}."
        f"\n  coverage:        {counts[UNGATED]} with no verdict-bearing run; "
        f"{counts[UNVERIFIABLE]} unverifiable"
        f"\n  current outcome: {counts[PASSING] + counts[RECOVERED]} passing; "
        f"{counts[FAILING]} failing"
        f"\n  history:         {ever_failed} commit(s) ever failed "
        f"({counts[RECOVERED]} recovered on re-run, {counts[FAILING]} still failing)"
    )
    if counts[FAILING] or counts[RECOVERED]:
        print(
            "\nFailing and recovered commits are reported, not failed on: they are a "
            "record of what happened and no re-dispatch can change them. Growth in "
            "these counts is the review question."
        )
    if ungated:
        print(
            "\nBackfill one with:\n"
            "  gh api repos/OWNER/REPO/git/refs "
            "-f ref=refs/tags/main-releasability-SHA -f sha=SHA\n"
            "  gh workflow run main-releasability.yml --ref main-releasability-SHA "
            "-f expected_sha=SHA -f triggering_pr=backfill\n"
        )
    if arguments.fail_on_gap and (counts[UNGATED] or counts[UNVERIFIABLE]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
