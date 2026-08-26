"""Fail closed when pull-request text has unsafe issue-lifecycle wording."""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Sequence

CLOSING_KEYWORD = r"(?:close(?:s|d)?|fix(?:es|ed)?|resolve(?:s|d)?)"
ISSUE_REFERENCE_TOKEN = r"(?:#[^\s]*|https?://github\.com/[^\s/]+/[^\s/]+/issues/[^\s]*)"
CLOSING_REFERENCE = re.compile(
    rf"^\s*(?:[-*+]\s+)?{CLOSING_KEYWORD}\s+#(?P<issue>[1-9][0-9]*)\s*$",
    re.IGNORECASE,
)
CLOSING_KEYWORD_WITH_REFERENCE = re.compile(
    rf"\b{CLOSING_KEYWORD}\b[^\r\n]*{ISSUE_REFERENCE_TOKEN}",
    re.IGNORECASE,
)
NEGATED_CLOSING_REFERENCE = re.compile(
    rf"\b(?:do\s+not|does\s+not|don't|doesn't|not|never)\s+{CLOSING_KEYWORD}\s+"
    rf"{ISSUE_REFERENCE_TOKEN}",
    re.IGNORECASE,
)


def validate_pr_text(title: str, body: str) -> tuple[list[int], list[str]]:
    """Return intended close references and actionable lifecycle-text findings."""
    findings = _title_findings(title)
    closing_issues, body_findings = _body_lifecycle_findings(body)
    return closing_issues, [*findings, *body_findings]


def _title_findings(title: str) -> list[str]:
    if not CLOSING_KEYWORD_WITH_REFERENCE.search(title):
        return []
    return [
        f"PR title has unsafe issue-closing wording: {title!r}. "
        "Put an intended close on its own body line as "
        "`Closes #123`; use `Keep #123 open` for partial work."
    ]


def _body_lifecycle_findings(body: str) -> tuple[list[int], list[str]]:
    closing_issues: list[int] = []
    findings: list[str] = []
    for line_number, line in enumerate(body.splitlines(), start=1):
        if NEGATED_CLOSING_REFERENCE.search(line):
            findings.append(
                f"PR body line {line_number} uses unsafe negated closing wording: {line!r}. "
                "Use `Keep #123 open` without a closing keyword."
            )
            continue
        if not CLOSING_KEYWORD_WITH_REFERENCE.search(line):
            continue
        reference = CLOSING_REFERENCE.fullmatch(line)
        if reference is None:
            findings.append(
                f"PR body line {line_number} has an ambiguous or malformed closing reference: "
                f"{line!r}. Use a standalone `Closes #123` line."
            )
            continue
        closing_issues.append(int(reference["issue"]))
    return closing_issues, findings


def _environment_text(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Required environment variable {name!r} is not set.")
    return value


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--title-env", required=True, help="Environment variable holding the PR title."
    )
    parser.add_argument(
        "--body-env", required=True, help="Environment variable holding the PR body."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    try:
        title = _environment_text(args.title_env)
        body = _environment_text(args.body_env)
    except ValueError as error:
        print(f"PR issue lifecycle text check failed: {error}")
        return 2

    closing_issues, findings = validate_pr_text(title, body)
    if findings:
        print("PR issue lifecycle text check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print(f"PR issue lifecycle text check passed: intended_close_issues={closing_issues or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
