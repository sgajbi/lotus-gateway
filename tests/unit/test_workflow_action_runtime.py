from pathlib import Path

from scripts.check_workflow_action_runtime import (
    ACTION_MAJOR_BASELINE,
    MAX_JOB_TIMEOUT_MINUTES,
    find_workflow_action_runtime_violations,
    find_workflow_job_timeout_violations,
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


def test_workflow_job_timeout_accepts_bounded_jobs(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "\n".join(
            [
                "jobs:",
                "  test:",
                "    runs-on: ubuntu-latest",
                "    timeout-minutes: 10",
                "    steps:",
                "      - run: echo ok",
            ]
        ),
        encoding="utf-8",
    )

    violations = find_workflow_job_timeout_violations([workflow])

    assert violations == ()


def test_workflow_job_timeout_reports_missing_timeout(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "\n".join(
            [
                "jobs:",
                "  test:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - run: echo ok",
            ]
        ),
        encoding="utf-8",
    )

    violations = find_workflow_job_timeout_violations([workflow])

    assert len(violations) == 1
    assert violations[0].job_id == "test"
    assert violations[0].reason == "missing"


def test_workflow_job_timeout_reports_unbounded_timeout(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "\n".join(
            [
                "jobs:",
                "  test:",
                "    runs-on: ubuntu-latest",
                f"    timeout-minutes: {MAX_JOB_TIMEOUT_MINUTES + 1}",
                "    steps:",
                "      - run: echo ok",
            ]
        ),
        encoding="utf-8",
    )

    violations = find_workflow_job_timeout_violations([workflow])

    assert len(violations) == 1
    assert violations[0].job_id == "test"
    assert (
        violations[0].reason
        == f"{MAX_JOB_TIMEOUT_MINUTES + 1} outside 1..{MAX_JOB_TIMEOUT_MINUTES}"
    )


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
    assert find_workflow_job_timeout_violations([REPO_ROOT / ".github" / "workflows"]) == ()


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


def test_main_releasability_retains_release_and_container_evidence() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "main-releasability.yml").read_text(
        encoding="utf-8"
    )

    for fragment in (
        "name: main-releasability-release-evidence",
        "output/main-releasability/",
        "output/demo-certification/",
        "openapi.json",
        "python scripts/check_main_release_evidence.py",
        "name: main-container-release-evidence",
        "SYFT_IMAGE: anchore/syft:v1.42.3",
        "TRIVY_IMAGE: aquasec/trivy:0.72.0",
        "--ignore-unfixed",
        "sigstore/cosign-installer@v4.1.0",
        'set -o pipefail\n          cosign sign --yes "${LOTUS_IMAGE_REF}"',
        '"builder":',
        '"buildType": "https://github.com/sgajbi/lotus-gateway/.github/workflows/main-releasability.yml"',
        "cosign attest --yes",
        "2>&1 | tee output/container-security/provenance-attestation.txt",
        "python scripts/write_container_release_manifest.py",
        "python scripts/check_container_release_evidence.py",
    ):
        assert fragment in workflow

    assert 'docker push "${IMAGE_NAME}:${IMAGE_TAG}"' in workflow
    assert "LOTUS_IMAGE_REF=${IMAGE_NAME}@${IMAGE_DIGEST}" in workflow
    assert workflow.index("- name: Vulnerability Scan") < workflow.index(
        "- name: Push image from CI"
    )
    assert "--build-arg LOTUS_IMAGE_DIGEST" not in workflow


def test_pr_merge_gate_builds_sha_tagged_scanned_unsigned_container_evidence() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "pr-merge-gate.yml").read_text(
        encoding="utf-8"
    )

    for fragment in (
        "IMAGE_TAG: ${{ github.sha }}",
        "SYFT_IMAGE: anchore/syft:v1.42.3",
        "TRIVY_IMAGE: aquasec/trivy:0.72.0",
        '-t "${IMAGE_NAME}:${IMAGE_TAG}"',
        '--build-arg LOTUS_GIT_COMMIT_SHA="${GITHUB_SHA}"',
        '"${SYFT_IMAGE}" "${IMAGE_NAME}:${IMAGE_TAG}"',
        '"${TRIVY_IMAGE}" image',
        "--ignore-unfixed",
        "python scripts/write_container_release_manifest.py",
        "python scripts/check_container_release_evidence.py --allow-unsigned",
        "name: pr-container-release-evidence",
    ):
        assert fragment in workflow

    assert "--build-arg LOTUS_IMAGE_DIGEST" not in workflow
    assert "docker push" not in workflow
    assert "PR images are not pushed or signed" in workflow
