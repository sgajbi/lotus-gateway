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

_STEP = re.compile(r"^(?P<indent>\s+)- name: (?P<name>.+)$")


def _iter_steps() -> list[tuple[Path, str, str]]:
    """Return (workflow, step name, step body) for every step in every workflow."""
    steps: list[tuple[Path, str, str]] = []
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        lines = workflow.read_text(encoding="utf-8").splitlines()
        current: tuple[str, str] | None = None
        body: list[str] = []
        for line in lines:
            match = _STEP.match(line)
            if match:
                if current is not None:
                    steps.append((workflow, current[1], "\n".join(body)))
                current = (match.group("indent"), match.group("name"))
                body = []
            elif current is not None:
                indent = current[0]
                if line.strip() and not line.startswith(indent + " "):
                    steps.append((workflow, current[1], "\n".join(body)))
                    current = None
                    body = []
                else:
                    body.append(line)
        if current is not None:
            steps.append((workflow, current[1], "\n".join(body)))
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
    on_disk = set(WORKFLOWS.glob("*.yml"))
    assert on_disk, "no workflows found: the scan would pass vacuously"
    assert scanned == on_disk, f"workflows never scanned: {on_disk - scanned}"
