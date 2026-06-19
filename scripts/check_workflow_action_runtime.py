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
    "actions/upload-artifact": 7,
}
NODE24_OPT_IN_ENV_NAME = "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24"
NODE24_OPT_IN_ENV_VALUE = "true"
MAX_JOB_TIMEOUT_MINUTES = 60
USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<uses>[^#\s]+)")
VERSION_PATTERN = re.compile(r"^(?P<action>[^@]+)@v(?P<major>\d+)(?:\D.*)?$")
NODE24_OPT_IN_PATTERN = re.compile(
    rf"^\s*{NODE24_OPT_IN_ENV_NAME}:\s*['\"]?{NODE24_OPT_IN_ENV_VALUE}['\"]?\s*$"
)
JOB_ID_PATTERN = re.compile(r"^  (?P<job_id>[A-Za-z0-9_-]+):\s*$")
JOB_TIMEOUT_PATTERN = re.compile(r"^    timeout-minutes:\s*(?P<timeout>\d+)\s*$")


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


@dataclass(frozen=True)
class WorkflowNode24OptInViolation:
    path: Path

    def format(self) -> str:
        return (
            f"{self.path}: missing {NODE24_OPT_IN_ENV_NAME}: "
            f'"{NODE24_OPT_IN_ENV_VALUE}" for GitHub JavaScript action runtime opt-in'
        )


@dataclass(frozen=True)
class WorkflowJobTimeoutViolation:
    path: Path
    job_id: str
    reason: str

    def format(self) -> str:
        return f"{self.path}: job '{self.job_id}' has invalid timeout-minutes: {self.reason}"


def iter_workflow_files(workflow_roots: Sequence[Path]) -> Iterable[Path]:
    for workflow_root in workflow_roots:
        if workflow_root.is_file() and workflow_root.suffix in {".yml", ".yaml"}:
            yield workflow_root
            continue
        if workflow_root.is_dir():
            yield from sorted(workflow_root.glob("*.yml"))
            yield from sorted(workflow_root.glob("*.yaml"))


def normalize_uses_value(uses_value: str) -> str:
    return uses_value.strip().strip("\"'")


def collect_governed_action_refs(source: str) -> list[str]:
    action_refs: list[str] = []
    for line in source.splitlines():
        uses_match = USES_PATTERN.match(line)
        if uses_match is None:
            continue
        uses_value = normalize_uses_value(uses_match.group("uses"))
        version_match = VERSION_PATTERN.match(uses_value)
        if version_match is None:
            continue
        action = version_match.group("action")
        if action in ACTION_MAJOR_BASELINE:
            action_refs.append(uses_value)
    return action_refs


def has_workflow_level_node24_opt_in(source: str) -> bool:
    in_workflow_env = False
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            in_workflow_env = stripped == "env:"
            continue

        if in_workflow_env and NODE24_OPT_IN_PATTERN.match(line):
            return True
    return False


def find_workflow_action_runtime_violations(
    workflow_roots: Sequence[Path],
) -> tuple[WorkflowActionRuntimeViolation, ...]:
    violations: list[WorkflowActionRuntimeViolation] = []
    for path in iter_workflow_files(workflow_roots):
        source = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(source.splitlines(), start=1):
            uses_match = USES_PATTERN.match(line)
            if uses_match is None:
                continue
            uses_value = normalize_uses_value(uses_match.group("uses"))
            version_match = VERSION_PATTERN.match(uses_value)
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
                        uses_value=uses_value,
                        required_value=f"{action}@v{required_major}",
                    )
                )
    return tuple(violations)


def find_workflow_node24_opt_in_violations(
    workflow_roots: Sequence[Path],
) -> tuple[WorkflowNode24OptInViolation, ...]:
    violations: list[WorkflowNode24OptInViolation] = []
    for path in iter_workflow_files(workflow_roots):
        source = path.read_text(encoding="utf-8")
        if collect_governed_action_refs(source) and not has_workflow_level_node24_opt_in(source):
            violations.append(WorkflowNode24OptInViolation(path=path))
    return tuple(violations)


def find_workflow_job_timeout_violations(
    workflow_roots: Sequence[Path],
) -> tuple[WorkflowJobTimeoutViolation, ...]:
    violations: list[WorkflowJobTimeoutViolation] = []
    for path in iter_workflow_files(workflow_roots):
        source = path.read_text(encoding="utf-8")
        current_job_id: str | None = None
        current_timeout: int | None = None
        in_jobs = False

        def record_current_job() -> None:
            if current_job_id is None:
                return
            if current_timeout is None:
                violations.append(
                    WorkflowJobTimeoutViolation(
                        path=path,
                        job_id=current_job_id,
                        reason="missing",
                    )
                )
                return
            if current_timeout < 1 or current_timeout > MAX_JOB_TIMEOUT_MINUTES:
                violations.append(
                    WorkflowJobTimeoutViolation(
                        path=path,
                        job_id=current_job_id,
                        reason=f"{current_timeout} outside 1..{MAX_JOB_TIMEOUT_MINUTES}",
                    )
                )

        for line in source.splitlines():
            if line == "jobs:":
                in_jobs = True
                continue
            if not in_jobs:
                continue

            if line and not line.startswith(" "):
                record_current_job()
                current_job_id = None
                current_timeout = None
                in_jobs = False
                continue

            job_match = JOB_ID_PATTERN.match(line)
            if job_match is not None:
                record_current_job()
                current_job_id = job_match.group("job_id")
                current_timeout = None
                continue

            timeout_match = JOB_TIMEOUT_PATTERN.match(line)
            if timeout_match is not None and current_job_id is not None:
                current_timeout = int(timeout_match.group("timeout"))

        record_current_job()

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
    action_violations = find_workflow_action_runtime_violations(args.workflow_roots)
    node24_violations = find_workflow_node24_opt_in_violations(args.workflow_roots)
    timeout_violations = find_workflow_job_timeout_violations(args.workflow_roots)
    if action_violations or node24_violations or timeout_violations:
        print("Workflow governance baseline violations:")
        for violation in action_violations:
            print(f"- {violation.format()}")
        for violation in node24_violations:
            print(f"- {violation.format()}")
        for violation in timeout_violations:
            print(f"- {violation.format()}")
        return 1

    print(
        "Workflow governance baseline passed: "
        + ", ".join(f"{action}@v{major}" for action, major in sorted(ACTION_MAJOR_BASELINE.items()))
        + f"; {NODE24_OPT_IN_ENV_NAME}={NODE24_OPT_IN_ENV_VALUE}; "
        + f"job_timeout_minutes<= {MAX_JOB_TIMEOUT_MINUTES}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
