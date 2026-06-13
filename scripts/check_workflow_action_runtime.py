from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_WORKFLOW_ROOT = Path(".github/workflows")
ACTION_MAJOR_BASELINE = {
    "actions/checkout": 6,
    "actions/setup-python": 6,
    "actions/setup-node": 5,
    "actions/upload-artifact": 5,
}
USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<uses>[^#\s]+)")
VERSION_PATTERN = re.compile(r"^(?P<action>[^@]+)@v(?P<major>\d+)$")


@dataclass(frozen=True)
class WorkflowActionRuntimeViolation:
    path: Path
    line_number: int
    uses_value: str
    required_value: str

    def format(self) -> str:
        return (
            f"{self.path}:{self.line_number} {self.uses_value} is below "
            f"the required baseline {self.required_value}"
        )


def iter_workflow_files(workflow_roots: Sequence[Path]) -> Iterable[Path]:
    for workflow_root in workflow_roots:
        if workflow_root.is_file() and workflow_root.suffix in {".yml", ".yaml"}:
            yield workflow_root
            continue
        if workflow_root.is_dir():
            yield from sorted(workflow_root.glob("*.yml"))
            yield from sorted(workflow_root.glob("*.yaml"))


def find_workflow_action_runtime_violations(
    workflow_roots: Sequence[Path],
) -> tuple[WorkflowActionRuntimeViolation, ...]:
    violations: list[WorkflowActionRuntimeViolation] = []
    for path in iter_workflow_files(workflow_roots):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            uses_match = USES_PATTERN.match(line)
            if uses_match is None:
                continue
            version_match = VERSION_PATTERN.match(uses_match.group("uses"))
            if version_match is None:
                continue
            action = version_match.group("action")
            required_major = ACTION_MAJOR_BASELINE.get(action)
            if required_major is None:
                continue
            actual_major = int(version_match.group("major"))
            if actual_major < required_major:
                violations.append(
                    WorkflowActionRuntimeViolation(
                        path=path,
                        line_number=line_number,
                        uses_value=uses_match.group("uses"),
                        required_value=f"{action}@v{required_major}",
                    )
                )
    return tuple(violations)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail when governed GitHub Actions use deprecated runtime majors."
    )
    parser.add_argument(
        "workflow_roots",
        nargs="*",
        type=Path,
        default=[DEFAULT_WORKFLOW_ROOT],
        help="Workflow directories or files to scan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    violations = find_workflow_action_runtime_violations(args.workflow_roots)
    if violations:
        print("Workflow action runtime baseline violations:")
        for violation in violations:
            print(f"- {violation.format()}")
        return 1

    print(
        "Workflow action runtime baseline passed: "
        + ", ".join(f"{action}@v{major}" for action, major in sorted(ACTION_MAJOR_BASELINE.items()))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
