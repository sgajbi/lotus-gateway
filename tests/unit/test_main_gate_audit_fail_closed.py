"""The fail-closed audit branches for per-commit main-gate coverage.

Ported from lotus-report (cross-repo review, 2026-08-31): a watchdog that can
pass while verifying nothing is the liveness defect it exists to catch, so a
missing gh, an unfetchable run listing, and a verdict-less run all fail the
audit instead of passing it.

Extended for #774. Coverage was the only question the audit asked, so eight
commits sat red on main while it reported a clean pass. Coverage, the current
outcome and the history of failure are now three separate numbers, and the
failing count is pinned in both directions here: a fixture with a red commit
must not report zero, and an all-green fixture must.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from scripts import audit_main_gate_coverage as audit

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"


def run(
    conclusion: str = "",
    *,
    status: str = "completed",
    at: str = "2026-09-01T00:00:00Z",
    run_id: str = "",
    attempt: str = "1",
) -> dict[str, str]:
    """One attempt record in the shape ``_gate_runs`` hands to ``classify``."""

    return {
        "conclusion": conclusion,
        "status": status,
        "startedAt": at,
        "databaseId": run_id,
        "attempt": attempt,
    }


def drive(
    monkeypatch,
    commits: Mapping[str, list[dict[str, str]] | None],
    *,
    fail_on_gap: bool = True,
) -> int:
    monkeypatch.setattr(
        audit,
        "_git",
        lambda *args: [f"{sha} {sha[:9]} subject line" for sha in commits],
    )
    monkeypatch.setattr(audit, "_all_gate_runs", lambda: [])
    monkeypatch.setattr(audit, "_gate_runs", lambda sha, _all_runs: commits[sha])
    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    monkeypatch.setattr(
        audit.argparse.ArgumentParser,
        "parse_args",
        lambda self: argparse_namespace(limit=60, fail_on_gap=fail_on_gap),
    )
    return audit.main()


def test_audit_counts_only_verdict_bearing_runs_and_fails_closed(monkeypatch, capsys) -> None:
    """A cancelled run evaluated nothing, an unfetchable listing proves
    nothing, and both must fail the audit rather than pass it."""

    commits = {
        "a" * 40: [run("success")],
        "b" * 40: [run("cancelled")],
        "c" * 40: None,
        "d" * 40: [],
    }

    exit_code = drive(monkeypatch, commits)
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "UNGATED      ddddddddd" in output
    assert "UNVERIFIABLE ccccccccc" in output
    assert "UNVERIFIABLE bbbbbbbbb" in output
    assert "1 with no verdict-bearing run; 2 unverifiable" in output


def test_audit_fails_closed_when_gh_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(audit.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        audit.argparse.ArgumentParser,
        "parse_args",
        lambda self: argparse_namespace(limit=60, fail_on_gap=True),
    )

    assert audit.main() == 1


def test_audit_passes_when_every_commit_has_a_verdict(monkeypatch) -> None:
    commits = {
        "a" * 40: [run("success")],
        "b" * 40: [run("failure"), run("cancelled")],
    }

    assert drive(monkeypatch, commits) == 0


def test_a_failing_commit_is_reported_and_counted_but_does_not_fail_the_audit(
    monkeypatch, capsys
) -> None:
    """The load-bearing decision from #774.

    Failing the audit on a red commit would make the eight already on main a
    permanent red that no dispatch can clear, and rewriting history to clear it
    is not on the table. So it is reported, counted, and the exit code stays
    reserved for coverage.
    """

    commits = {"a" * 40: [run("success")], "b" * 40: [run("failure")]}

    exit_code = drive(monkeypatch, commits)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "FAILING      bbbbbbbbb" in output
    assert "1 passing; 1 failing" in output
    assert "1 commit(s) ever failed (0 recovered on re-run, 1 still failing)" in output


def test_an_all_green_fixture_reports_zero_failing(monkeypatch, capsys) -> None:
    """The other direction of the same pin.

    Without this, a classifier that called everything failing would satisfy the
    test above and the number would mean nothing.
    """

    commits = {"a" * 40: [run("success")], "b" * 40: [run("success")]}

    assert drive(monkeypatch, commits) == 0
    output = capsys.readouterr().out
    assert "2 passing; 0 failing" in output
    assert "0 commit(s) ever failed" in output
    assert "FAILING" not in output


def test_a_retry_that_goes_green_is_recovered_rather_than_passing(monkeypatch, capsys) -> None:
    """Retry handling, stated rather than incidental.

    A re-run going green is the current truth and the commit is not failing
    now. It is also true that the commit was broken when it landed, and only
    the history line still says so.
    """

    commits = {
        "a" * 40: [
            run("failure", at="2026-09-01T00:00:00Z", run_id="1"),
            run("success", at="2026-09-01T01:00:00Z", run_id="2"),
        ]
    }

    assert drive(monkeypatch, commits) == 0
    output = capsys.readouterr().out
    assert "RECOVERED    aaaaaaaaa" in output
    assert "1 failing verdict(s) (failure), then green on re-run" in output
    assert "1 passing; 0 failing" in output
    assert "1 commit(s) ever failed (1 recovered on re-run, 0 still failing)" in output


def test_the_newest_verdict_decides_whatever_order_the_api_returns() -> None:
    """Order comes from the timestamps, not from the list.

    ``gh`` lists most-recent-first today. An audit that read the current verdict
    off list position would be correct only until that changed, and would then
    report a green commit as red with nothing to indicate why.
    """

    green_then_red = [
        run("success", at="2026-09-01T00:00:00Z", run_id="1"),
        run("failure", at="2026-09-01T01:00:00Z", run_id="2"),
    ]

    assert audit.classify(green_then_red).state == audit.FAILING
    assert audit.classify(list(reversed(green_then_red))).state == audit.FAILING


def test_runs_sharing_a_timestamp_are_ordered_by_run_id() -> None:
    same_second = [
        run("failure", at="2026-09-01T00:00:00Z", run_id="2"),
        run("success", at="2026-09-01T00:00:00Z", run_id="1"),
    ]

    assert audit.classify(same_second).state == audit.FAILING


def test_a_pending_rerun_does_not_mask_the_verdict_a_commit_already_has() -> None:
    """Pending handling. A queued re-run is not evidence about anything, and
    must neither create coverage nor withdraw it."""

    verdict_then_pending = [
        run("failure", at="2026-09-01T00:00:00Z", run_id="1"),
        run(status="queued", at="2026-09-01T01:00:00Z", run_id="2"),
    ]

    outcome = audit.classify(verdict_then_pending)
    assert outcome.state == audit.FAILING
    assert outcome.is_covered


def test_a_commit_with_only_pending_runs_is_unverifiable_and_says_so() -> None:
    outcome = audit.classify([run(status="in_progress")])

    assert outcome.state == audit.UNVERIFIABLE
    assert not outcome.is_covered
    assert "still running (in_progress)" in outcome.detail


def test_no_runs_at_all_is_ungated_not_unverifiable() -> None:
    """The distinction the issue turns on: a gap is a dispatch failure to fix,
    an unverifiable commit is a question still open."""

    assert audit.classify([]).state == audit.UNGATED
    assert audit.classify(None).state == audit.UNVERIFIABLE


def test_a_rerun_attempt_that_goes_green_still_counts_the_attempt_that_failed() -> None:
    """The representative rerun shape, which two separate runs are not.

    `gh run rerun` adds an attempt to the *same* run: same `databaseId`, a
    higher `attempt`, and a `startedAt` that resets. Reading only the newest
    attempt is how a failure disappears from a history that promises to keep it.
    """

    same_run_reran = [
        run("failure", at="2026-09-01T00:00:00Z", run_id="9", attempt="1"),
        run("success", at="2026-09-01T02:00:00Z", run_id="9", attempt="2"),
    ]

    outcome = audit.classify(same_run_reran)
    assert outcome.state == audit.RECOVERED
    assert "1 failing verdict(s) (failure), then green on re-run" in outcome.detail


def test_a_rerun_of_an_older_run_sorts_after_a_newer_run() -> None:
    """Why the sort key is each attempt's own start time.

    Run 1 fails, run 2 passes, then run 1 is re-run and fails again. Ordering by
    the run's creation time would bury that second failure behind run 2 and
    report the commit as recovered when it is currently red.
    """

    reran_after = [
        run("failure", at="2026-09-01T00:00:00Z", run_id="1", attempt="1"),
        run("success", at="2026-09-01T01:00:00Z", run_id="2", attempt="1"),
        run("failure", at="2026-09-01T03:00:00Z", run_id="1", attempt="2"),
    ]

    assert audit.classify(reran_after).state == audit.FAILING


def test_attempts_of_one_run_sharing_a_start_time_are_ordered_by_attempt_number() -> None:
    """The last tiebreaker, and the only one that can separate these two.

    Two attempts of the same run share a `databaseId`, and a re-run started
    inside the same second shares `startedAt` too. Without the attempt number
    the sort falls back to input order -- which is the API ordering this module
    deliberately does not trust.
    """

    same_second_rerun = [
        run("success", at="2026-09-01T00:00:00Z", run_id="9", attempt="2"),
        run("failure", at="2026-09-01T00:00:00Z", run_id="9", attempt="1"),
    ]

    assert audit.classify(same_second_rerun).state == audit.RECOVERED
    assert audit.classify(list(reversed(same_second_rerun))).state == audit.RECOVERED


def test_attempt_ordering_is_numeric_not_lexicographic() -> None:
    """Attempt 10 is newer than attempt 9, and these are strings."""

    ten_then_nine = [
        run("failure", at="2026-09-01T00:00:00Z", run_id="9", attempt="10"),
        run("success", at="2026-09-01T00:00:00Z", run_id="9", attempt="9"),
    ]

    assert audit.classify(ten_then_nine).state == audit.FAILING


def test_a_verdict_with_no_attempt_start_time_is_unverifiable() -> None:
    """Ordering decides which verdict is current, so a verdict that cannot be
    placed makes the commit unverifiable rather than guessable."""

    outcome = audit.classify([run("failure", at="")])

    assert outcome.state == audit.UNVERIFIABLE
    assert not outcome.is_covered
    assert "no attempt start time" in outcome.detail


def test_an_undated_rerun_is_not_ordered_from_the_runs_creation_time() -> None:
    """The case the `createdAt` fallback got wrong.

    Run 1 fails at t0, run 2 passes at t1, run 1 is re-run and fails again --
    with no start time on that attempt. Substituting run 1's creation time sorts
    the second failure back at t0, behind the success, and reports RECOVERED for
    a commit that is currently red. Refusing is the only honest answer, because
    the attempt genuinely cannot be placed.
    """

    outcome = audit.classify(
        [
            run("failure", at="2026-09-01T00:00:00Z", run_id="1", attempt="1"),
            run("success", at="2026-09-01T01:00:00Z", run_id="2", attempt="1"),
            run("failure", at="", run_id="1", attempt="2"),
        ]
    )

    assert outcome.state == audit.UNVERIFIABLE
    assert outcome.state != audit.RECOVERED


def test_a_pending_attempt_needs_no_start_time() -> None:
    """The refusal is scoped to verdicts. A queued attempt decides no ordering,
    so requiring a timestamp of it would withdraw a verdict the commit has."""

    outcome = audit.classify(
        [
            run("success", at="2026-09-01T00:00:00Z", run_id="1"),
            run(status="queued", at="", run_id="2"),
        ]
    )

    assert outcome.state == audit.PASSING


def test_terminal_failure_conclusions_are_failures_not_absent_verdicts() -> None:
    """A gate that timed out ran and did not pass. Counting that as "no verdict"
    moves a red commit into the unverifiable column instead of the failing one."""

    for conclusion in ("timed_out", "startup_failure"):
        outcome = audit.classify([run(conclusion)])
        assert outcome.state == audit.FAILING, conclusion
        assert conclusion in outcome.detail


def test_a_terminal_failure_followed_by_a_green_rerun_is_recovered() -> None:
    outcome = audit.classify(
        [
            run("timed_out", at="2026-09-01T00:00:00Z", run_id="9", attempt="1"),
            run("success", at="2026-09-01T02:00:00Z", run_id="9", attempt="2"),
        ]
    )

    assert outcome.state == audit.RECOVERED
    assert "timed_out" in outcome.detail


def test_non_verdict_completions_stay_outside_the_verdict_set() -> None:
    """`cancelled`, `neutral`, `skipped` and `stale` are not the gate answering.

    Kept explicit so widening the failing set later is a decision rather than an
    accident.
    """

    for conclusion in ("cancelled", "neutral", "skipped", "stale"):
        outcome = audit.classify([run(conclusion)])
        assert outcome.state == audit.UNVERIFIABLE, conclusion
        assert not outcome.is_covered


def test_the_run_history_is_paginated_once_instead_of_capped_per_commit(monkeypatch) -> None:
    """The audit reads every REST page once, rather than silently aging history out."""

    captured: list[list[str]] = []

    class _Completed:
        returncode = 0
        stdout = json.dumps([{"workflow_runs": []}])

    def _capture(argv, **kwargs):
        captured.append(argv)
        return _Completed()

    monkeypatch.setattr(audit.subprocess, "run", _capture)
    assert audit._all_gate_runs() == []

    assert captured[0][:4] == ["gh", "api", "--paginate", "--slurp"]
    assert captured[0][4].endswith(f"actions/workflows/{audit.WORKFLOW}/runs?per_page=100")


def test_audit_reuses_the_one_paginated_history_for_every_commit(monkeypatch) -> None:
    calls = 0

    def _all_runs() -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        return []

    commits: dict[str, list[dict[str, str]]] = {"a" * 40: [], "b" * 40: []}
    monkeypatch.setattr(audit, "_all_gate_runs", _all_runs)
    monkeypatch.setattr(
        audit, "_git", lambda *args: [f"{sha} {sha[:9]} subject" for sha in commits]
    )
    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    monkeypatch.setattr(
        audit.argparse.ArgumentParser,
        "parse_args",
        lambda self: argparse_namespace(limit=60, fail_on_gap=True),
    )

    assert audit.main() == 1
    assert calls == 1


def test_mainline_source_identity_beats_workflow_definition_head_sha(monkeypatch) -> None:
    """B can fail, then define a successful gate of A, without either being lost.

    This is the mainline-ref shape: when A's dispatch starts after B merges,
    GitHub records B as the workflow definition `headSha`. A must still receive
    its own success by evaluated-source identity, while B retains its failure.
    """
    source_a = "a" * 40
    definition_b = "b" * 40

    class _Completed:
        returncode = 0
        stdout = json.dumps(
            [
                {
                    "conclusion": "failure",
                    "status": "completed",
                    "startedAt": "2026-09-01T00:00:00Z",
                    "databaseId": 1,
                    "attempt": 1,
                    "headSha": definition_b,
                    "displayTitle": f"Main Releasability · {definition_b}",
                },
                {
                    "conclusion": "success",
                    "status": "completed",
                    "startedAt": "2026-09-01T01:00:00Z",
                    "databaseId": 2,
                    "attempt": 1,
                    "headSha": definition_b,
                    "displayTitle": f"Main Releasability · {source_a}",
                },
            ]
        )

    runs = json.loads(_Completed.stdout)

    assert audit.classify(audit._gate_runs(source_a, runs)).state == audit.PASSING
    assert audit.classify(audit._gate_runs(definition_b, runs)).state == audit.FAILING


def test_malformed_mainline_title_does_not_erase_other_source_verdicts(monkeypatch) -> None:
    source_a = "a" * 40
    source_b = "b" * 40

    class _Completed:
        returncode = 0
        stdout = json.dumps(
            [
                {
                    "conclusion": "success",
                    "status": "completed",
                    "startedAt": "2026-09-01T00:00:00Z",
                    "databaseId": 1,
                    "attempt": 1,
                    "headSha": source_b,
                    "displayTitle": "Main Releasability · not-a-sha",
                },
                {
                    "conclusion": "success",
                    "status": "completed",
                    "startedAt": "2026-09-01T01:00:00Z",
                    "databaseId": 2,
                    "attempt": 1,
                    "headSha": source_b,
                    "displayTitle": f"Main Releasability · {source_a}",
                },
            ]
        )

    runs = json.loads(_Completed.stdout)

    assert audit.classify(audit._gate_runs(source_a, runs)).state == audit.PASSING
    # Never manufacture B's authority from the workflow definition SHA: its
    # malformed title leaves B uncovered, which --fail-on-gap treats as red.
    assert audit.classify(audit._gate_runs(source_b, runs)).state == audit.UNGATED


def test_the_fetcher_does_not_fill_a_missing_start_time_from_createdat(monkeypatch) -> None:
    """`createdAt` is the run's creation, not the attempt's start.

    Reading it in as though it were the attempt's own start time is what let a
    re-run sort back at the original attempt's position. This asserts at the
    fetcher rather than only at `classify`, because the substitution would
    happen here and `classify` would then have no way to know it was invented.
    """

    class _Completed:
        returncode = 0
        stdout = json.dumps(
            [
                {
                    "conclusion": "failure",
                    "status": "completed",
                    "createdAt": "2026-09-01T00:00:00Z",
                    "databaseId": 1,
                    "attempt": 1,
                    "headSha": "a" * 40,
                    "displayTitle": "",
                }
            ]
        )

    attempts = audit._gate_runs("a" * 40, json.loads(_Completed.stdout))
    assert attempts is not None
    assert attempts[0]["startedAt"] == ""
    assert audit.classify(attempts).state == audit.UNVERIFIABLE


def test_a_malformed_paginated_page_is_unverifiable_rather_than_dropped(monkeypatch) -> None:
    """Pagination may be complete only if every returned page has its run list."""

    class _Completed:
        returncode = 0
        stdout = json.dumps([{"workflow_runs": []}, {"not_workflow_runs": []}])

    monkeypatch.setattr(audit.subprocess, "run", lambda argv, **kwargs: _Completed())

    assert audit._all_gate_runs() is None
    assert audit.classify(None).state == audit.UNVERIFIABLE


def test_a_malformed_entry_makes_the_whole_listing_unverifiable(monkeypatch) -> None:
    """Not "skip the bad entry and classify from the rest".

    A listing with a hole in it is not the listing. Keeping the valid runs and
    dropping the malformed one would let a commit read PASSING off evidence
    already known to be incomplete, which is the fail-open direction.
    """

    class _Completed:
        returncode = 0
        stdout = json.dumps(
            [
                {"conclusion": "success", "status": "completed", "databaseId": 1, "attempt": 1},
                "not an object",
            ]
        )

    assert audit._gate_runs("a" * 40, json.loads(_Completed.stdout)) is None


def test_a_non_integer_attempt_count_fails_closed(monkeypatch) -> None:
    class _Completed:
        returncode = 0
        stdout = json.dumps(
            [{"conclusion": "success", "status": "completed", "databaseId": 1, "attempt": "many"}]
        )

    assert audit._gate_runs("a" * 40, json.loads(_Completed.stdout)) is None


def test_an_unreadable_superseded_attempt_fails_closed(monkeypatch) -> None:
    """We know the attempt exists, because the run says so. Reporting the
    history without it would be reporting a history we do not have."""

    listing = json.dumps(
        [{"conclusion": "success", "status": "completed", "databaseId": 9, "attempt": 3}]
    )

    monkeypatch.setattr(audit, "_earlier_attempt", lambda run_id, attempt: None)

    assert audit._gate_runs("a" * 40, json.loads(listing)) is None


def test_superseded_attempts_are_fetched_and_included(monkeypatch) -> None:
    listing = json.dumps(
        [
            {
                "conclusion": "success",
                "status": "completed",
                "startedAt": "2026-09-01T02:00:00Z",
                "databaseId": 9,
                "attempt": 2,
                "headSha": "a" * 40,
                "displayTitle": "",
            }
        ]
    )
    monkeypatch.setattr(
        audit,
        "_earlier_attempt",
        lambda run_id, attempt: audit._record(
            "failure", "completed", "2026-09-01T00:00:00Z", run_id, str(attempt)
        ),
    )

    attempts = audit._gate_runs("a" * 40, json.loads(listing))
    assert attempts is not None
    assert len(attempts) == 2
    assert audit.classify(attempts).state == audit.RECOVERED


def argparse_namespace(**kwargs):
    import argparse

    return argparse.Namespace(**kwargs)
