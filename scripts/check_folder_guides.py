"""Validate folder-local Gateway engineering guides."""

from __future__ import annotations

from pathlib import Path

REQUIRED_GUIDES = (
    Path("src/app/README.md"),
    Path("src/app/routers/README.md"),
    Path("src/app/services/README.md"),
    Path("src/app/contracts/README.md"),
    Path("src/app/clients/README.md"),
    Path("tests/README.md"),
    Path("docs/README.md"),
    Path("quality/README.md"),
    Path("scripts/README.md"),
)
REQUIRED_SECTIONS = (
    "## Responsibility",
    "## Boundary Rules",
    "## Validation",
    "## Update Triggers",
)
TABLE_MARKER = "| Area | Rule | Evidence |"


def validate_folder_guides(repo_root: Path | None = None) -> list[str]:
    root = (repo_root or Path.cwd()).resolve()
    findings: list[str] = []
    for relative_path in REQUIRED_GUIDES:
        path = root / relative_path
        if not path.is_file():
            findings.append(f"Missing folder guide: {relative_path.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# "):
            findings.append(f"{relative_path.as_posix()} must start with an H1 heading")
        for section in REQUIRED_SECTIONS:
            if section not in text:
                findings.append(f"{relative_path.as_posix()} missing section: {section}")
        if TABLE_MARKER not in text:
            findings.append(f"{relative_path.as_posix()} missing ownership/rule/evidence table")
    return findings


def main() -> int:
    findings = validate_folder_guides()
    if findings:
        print("Folder guide check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"Folder guide check passed: {len(REQUIRED_GUIDES)} guide(s) validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
