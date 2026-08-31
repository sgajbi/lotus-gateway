"""The fail-closed audit branches for per-commit main-gate coverage.

Ported from lotus-report (cross-repo review, 2026-08-31): a watchdog that can
pass while verifying nothing is the liveness defect it exists to catch, so a
missing gh, an unfetchable run listing, and a verdict-less run all fail the
audit instead of passing it.
"""

from __future__ import annotations

from pathlib import Path

from scripts import audit_main_gate_coverage as audit

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"


def test_audit_counts_only_verdict_bearing_runs_and_fails_closed(monkeypatch, capsys) -> None:
    """A cancelled run evaluated nothing, an unfetchable listing proves
    nothing, and both must fail the audit rather than pass it."""

    commits = {
        "a" * 40: ["success"],
        "b" * 40: ["cancelled"],
        "c" * 40: None,
        "d" * 40: [],
    }
    monkeypatch.setattr(
        audit,
        "_git",
        lambda *args: [f"{sha} {sha[:9]} subject line" for sha in commits],
    )
    monkeypatch.setattr(audit, "_run_conclusions", lambda sha: commits[sha])
    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    monkeypatch.setattr(
        audit.argparse.ArgumentParser,
        "parse_args",
        lambda self: argparse_namespace(limit=60, fail_on_gap=True),
    )

    exit_code = audit.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "UNGATED  ddddddddd" in output
    assert "UNKNOWN  ccccccccc" in output
    assert "UNKNOWN  bbbbbbbbb" in output
    assert "1 with no verdict-bearing" in output


def test_audit_fails_closed_when_gh_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(audit.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        audit.argparse.ArgumentParser,
        "parse_args",
        lambda self: argparse_namespace(limit=60, fail_on_gap=True),
    )

    assert audit.main() == 1


def test_audit_passes_when_every_commit_has_a_verdict(monkeypatch) -> None:
    commits = {"a" * 40: ["success"], "b" * 40: ["failure", "cancelled"]}
    monkeypatch.setattr(
        audit,
        "_git",
        lambda *args: [f"{sha} {sha[:9]} subject line" for sha in commits],
    )
    monkeypatch.setattr(audit, "_run_conclusions", lambda sha: commits[sha])
    monkeypatch.setattr(audit.shutil, "which", lambda name: "/usr/bin/gh")
    monkeypatch.setattr(
        audit.argparse.ArgumentParser,
        "parse_args",
        lambda self: argparse_namespace(limit=60, fail_on_gap=True),
    )

    assert audit.main() == 0


def argparse_namespace(**kwargs):
    import argparse

    return argparse.Namespace(**kwargs)
