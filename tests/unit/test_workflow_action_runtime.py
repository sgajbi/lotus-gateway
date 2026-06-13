from pathlib import Path

from scripts.check_workflow_action_runtime import (
    ACTION_MAJOR_BASELINE,
    find_workflow_action_runtime_violations,
    find_workflow_node24_opt_in_violations,
    normalize_uses_value,
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
                "      - uses: actions/upload-artifact@v7",
                "env:",
                '  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"',
            ]
        ),
        encoding="utf-8",
    )

    violations = find_workflow_action_runtime_violations([workflow])

    assert violations == ()


def test_workflow_node24_opt_in_accepts_governed_workflow_with_env(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "\n".join(
            [
                "env:",
                '  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"',
                "steps:",
                "  - uses: actions/checkout@v6",
            ]
        ),
        encoding="utf-8",
    )

    violations = find_workflow_node24_opt_in_violations([workflow])

    assert violations == ()


def test_workflow_node24_opt_in_reports_missing_env_for_governed_workflow(
    tmp_path: Path,
) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text("steps:\n  - uses: actions/checkout@v6\n", encoding="utf-8")

    violations = find_workflow_node24_opt_in_violations([workflow])

    assert len(violations) == 1
    assert violations[0].path == workflow


def test_workflow_node24_opt_in_rejects_job_scoped_env_for_governed_workflow(
    tmp_path: Path,
) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "\n".join(
            [
                "jobs:",
                "  test:",
                "    env:",
                '      FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"',
                "    steps:",
                "      - uses: actions/checkout@v6",
                "  unprotected:",
                "    steps:",
                "      - uses: actions/setup-python@v6",
            ]
        ),
        encoding="utf-8",
    )

    violations = find_workflow_node24_opt_in_violations([workflow])

    assert len(violations) == 1
    assert violations[0].path == workflow


def test_workflow_node24_opt_in_ignores_workflows_without_governed_actions(
    tmp_path: Path,
) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text("steps:\n  - run: echo ok\n", encoding="utf-8")

    violations = find_workflow_node24_opt_in_violations([workflow])

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


def test_workflow_action_runtime_reports_quoted_deprecated_major(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "steps:\n  - uses: \"actions/checkout@v4\"\n  - uses: 'actions/setup-python@v5'\n",
        encoding="utf-8",
    )

    violations = find_workflow_action_runtime_violations([workflow])

    assert [violation.uses_value for violation in violations] == [
        "actions/checkout@v4",
        "actions/setup-python@v5",
    ]


def test_workflow_action_runtime_reports_full_deprecated_semver_tag(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text("steps:\n  - uses: actions/checkout@v4.2.2\n", encoding="utf-8")

    violations = find_workflow_action_runtime_violations([workflow])

    assert len(violations) == 1
    assert violations[0].uses_value == "actions/checkout@v4.2.2"
    assert violations[0].required_value == "actions/checkout@v6"


def test_workflow_action_runtime_ignores_ungoverned_actions(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text("steps:\n  - uses: reviewdog/action-actionlint@v1\n", encoding="utf-8")

    violations = find_workflow_action_runtime_violations([workflow])

    assert violations == ()


def test_normalize_uses_value_strips_yaml_quotes() -> None:
    assert normalize_uses_value('"actions/checkout@v6"') == "actions/checkout@v6"
    assert normalize_uses_value("'actions/checkout@v6'") == "actions/checkout@v6"


def test_gateway_workflows_match_platform_action_runtime_baseline() -> None:
    assert ACTION_MAJOR_BASELINE == {
        "actions/checkout": 6,
        "actions/setup-python": 6,
        "actions/setup-node": 5,
        "actions/upload-artifact": 7,
    }
    assert find_workflow_action_runtime_violations([REPO_ROOT / ".github" / "workflows"]) == ()
    assert find_workflow_node24_opt_in_violations([REPO_ROOT / ".github" / "workflows"]) == ()


def test_main_releasability_runs_coverage_in_parallel_with_integration() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "main-releasability.yml").read_text(
        encoding="utf-8"
    )

    assert (
        "      - name: Lint and Refactor Quality Thresholds\n        run: make lint"
    ) in workflow
    assert (
        "  integration:\n    name: Main Releasability / Integration Tests\n"
        "    needs: [lint-typecheck-unit]"
    ) in workflow
    assert (
        "  coverage:\n    name: Main Releasability / Coverage Gate\n"
        "    needs: [lint-typecheck-unit]"
    ) in workflow
    assert (
        "  docker-build:\n    name: Main Releasability / Validate Docker Build\n"
        "    needs: [integration, coverage]"
    ) in workflow
    assert (
        "  ci-local-docker:\n    name: Main Releasability / CI Local Docker Parity\n"
        "    needs: [integration, coverage]"
    ) in workflow
