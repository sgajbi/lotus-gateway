from pathlib import Path

from scripts.github_issue_pr_text_gate import main, validate_pr_text

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_accepts_a_standalone_intended_close_reference() -> None:
    closing_issues, findings = validate_pr_text("Fix lifecycle guard", "Closes #673")

    assert closing_issues == [673]
    assert findings == []


def test_accepts_neutral_keep_open_wording() -> None:
    closing_issues, findings = validate_pr_text(
        "Publish a partial contract", "Keep #575 open\n\nWorkbench proof remains outstanding."
    )

    assert closing_issues == []
    assert findings == []


def test_rejects_closing_wording_in_a_title() -> None:
    closing_issues, findings = validate_pr_text("Closes #673", "Lifecycle implementation")

    assert closing_issues == []
    assert len(findings) == 1
    assert "unsafe issue-closing wording" in findings[0]
    assert "Closes #673" in findings[0]


def test_rejects_negated_closing_language() -> None:
    closing_issues, findings = validate_pr_text(
        "Partial implementation", "This does not close #575 because Workbench proof remains."
    )

    assert closing_issues == []
    assert len(findings) == 1
    assert "unsafe negated closing wording" in findings[0]
    assert "Keep #123 open" in findings[0]


def test_rejects_malformed_closing_reference() -> None:
    closing_issues, findings = validate_pr_text("Fix lifecycle guard", "Closes issue #673")

    assert closing_issues == []
    assert len(findings) == 1
    assert "ambiguous or malformed closing reference" in findings[0]
    assert "Closes #123" in findings[0]


def test_requires_named_environment_variables(monkeypatch) -> None:
    monkeypatch.delenv("LOTUS_PR_TITLE", raising=False)
    monkeypatch.delenv("LOTUS_PR_BODY", raising=False)

    assert main(["--title-env", "LOTUS_PR_TITLE", "--body-env", "LOTUS_PR_BODY"]) == 2


def test_pr_merge_gate_runs_the_repo_native_command() -> None:
    workflow = (REPO_ROOT / ".github/workflows/pr-merge-gate.yml").read_text(encoding="utf-8")

    assert "PR Merge Gate / Issue Lifecycle Text" in workflow
    assert "types: [opened, synchronize, reopened, ready_for_review, edited]" in workflow
    assert "LOTUS_PR_TITLE: ${{ github.event.pull_request.title }}" in workflow
    assert "LOTUS_PR_BODY: ${{ github.event.pull_request.body }}" in workflow
    assert "make pr-issue-lifecycle" in workflow
