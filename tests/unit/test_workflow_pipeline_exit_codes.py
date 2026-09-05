"""Workflow steps must not hide a gate's exit code behind a pipe.

A step written as ``gate.py | tee log.txt`` exits with ``tee``'s status, so the
gate can fail on every run while the step stays green. This is how the branch
protection gate shipped fail-open: its checker raised ``CalledProcessError`` on
an empty token in every run beneath a green check.
"""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"

_STEPS_KEY = re.compile(r"^\s*steps:\s*$")
_NAME = re.compile(r"(?:^|-\s+)name:\s*(?P<name>.+?)\s*$")


def _workflow_files() -> list[Path]:
    """GitHub recognizes both extensions; scanning one would miss the other."""
    return sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))


def _iter_steps() -> list[tuple[Path, str, str]]:
    """Return (workflow, step name, step body) for every step in every workflow.

    Steps are found by list structure, not by a ``name:`` key: ``- run: gate.py
    | tee log.txt`` is a valid unnamed step, and keying on ``- name:`` would
    skip exactly the pipeline this scan exists to catch.
    """

    def name_of(block: list[str]) -> str:
        for line in block:
            match = _NAME.search(line)
            if match:
                return match.group("name").strip().strip("\"'")
        return "(unnamed step)"

    steps: list[tuple[Path, str, str]] = []
    for workflow in _workflow_files():
        in_steps = False
        steps_indent = 0
        item_indent: int | None = None
        current: list[str] | None = None

        for line in workflow.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())

            if not stripped:
                if current is not None:
                    current.append(line)
                continue

            if _STEPS_KEY.match(line):
                if current is not None:
                    steps.append((workflow, name_of(current), "\n".join(current)))
                    current = None
                in_steps = True
                steps_indent = indent
                item_indent = None
                continue

            if not in_steps:
                continue

            if indent <= steps_indent:
                if current is not None:
                    steps.append((workflow, name_of(current), "\n".join(current)))
                    current = None
                in_steps = False
                item_indent = None
                continue

            is_item = stripped.startswith("- ")
            if is_item and item_indent is None:
                item_indent = indent

            if is_item and indent == item_indent:
                if current is not None:
                    steps.append((workflow, name_of(current), "\n".join(current)))
                current = [line]
            elif current is not None:
                current.append(line)

        if current is not None:
            steps.append((workflow, name_of(current), "\n".join(current)))
    return steps


def test_piped_steps_propagate_the_real_exit_code() -> None:
    offenders = []
    for workflow, name, body in _iter_steps():
        if "| tee" not in body and "| tail" not in body:
            continue
        if "pipefail" in body or "PIPESTATUS" in body:
            continue
        offenders.append(f"{workflow.name}: {name}")

    assert not offenders, (
        "these steps pipe a command without propagating its exit code, so the "
        "step reports the pipe's status and cannot fail: " + "; ".join(offenders)
    )


def test_the_detector_recognizes_an_unguarded_pipe() -> None:
    """The scan must fail on the shape it exists to forbid, not just pass."""
    unguarded = "run: |\n  python gate.py 2>&1 | tee log.txt"
    guarded = "run: |\n  set -o pipefail\n  python gate.py 2>&1 | tee log.txt"

    def is_offending(body: str) -> bool:
        piped = "| tee" in body or "| tail" in body
        return piped and "pipefail" not in body and "PIPESTATUS" not in body

    assert is_offending(unguarded)
    assert not is_offending(guarded)


def test_every_workflow_is_scanned() -> None:
    """A silent zero-input scan would pass while checking nothing."""
    scanned = {workflow for workflow, _, _ in _iter_steps()}
    on_disk = set(_workflow_files())
    assert on_disk, "no workflows found: the scan would pass vacuously"
    assert scanned == on_disk, f"workflows never scanned: {on_disk - scanned}"


def test_unnamed_steps_are_scanned() -> None:
    """`- run: gate | tee log` is a step; keying on `- name:` would skip it."""
    named = [name for _, name, _ in _iter_steps()]
    assert named, "no steps parsed at all"
    checkout_steps = [body for _, _, body in _iter_steps() if "actions/checkout" in body]
    assert checkout_steps, (
        "every workflow checks out the repository, often as an unnamed "
        "`- uses:` step; finding none means the parser only sees named steps"
    )
