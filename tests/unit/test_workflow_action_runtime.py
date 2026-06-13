from pathlib import Path

from scripts.check_workflow_action_runtime import (
    ACTION_MAJOR_BASELINE,
    find_workflow_action_runtime_violations,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_workflow_action_runtime_accepts_current_baseline(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "\n".join(
            [
                "jobs:",
                "  test:",
                "    steps:",
                "      - uses: actions/checkout@v6",
                "      - uses: actions/setup-python@v6",
                "      - uses: actions/setup-node@v5",
                "      - uses: actions/upload-artifact@v5",
            ]
        ),
        encoding="utf-8",
    )

    violations = find_workflow_action_runtime_violations([workflow])

    assert violations == ()


def test_workflow_action_runtime_reports_deprecated_major(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "\n".join(
            [
                "jobs:",
                "  test:",
                "    steps:",
                "      - uses: actions/checkout@v4",
                "      - uses: actions/setup-python@v5",
            ]
        ),
        encoding="utf-8",
    )

    violations = find_workflow_action_runtime_violations([workflow])

    assert [violation.uses_value for violation in violations] == [
        "actions/checkout@v4",
        "actions/setup-python@v5",
    ]
    assert [violation.required_value for violation in violations] == [
        "actions/checkout@v6",
        "actions/setup-python@v6",
    ]


def test_workflow_action_runtime_ignores_ungoverned_actions(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text("steps:\n  - uses: reviewdog/action-actionlint@v1\n", encoding="utf-8")

    violations = find_workflow_action_runtime_violations([workflow])

    assert violations == ()


def test_gateway_workflows_match_platform_action_runtime_baseline() -> None:
    assert ACTION_MAJOR_BASELINE == {
        "actions/checkout": 6,
        "actions/setup-python": 6,
        "actions/setup-node": 5,
        "actions/upload-artifact": 5,
    }
    assert find_workflow_action_runtime_violations([REPO_ROOT / ".github" / "workflows"]) == ()
