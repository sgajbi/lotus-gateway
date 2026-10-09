"""Protect exact admission-to-acquisition wiring, without fetching image layers."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
IMAGES = {
    "base": (
        "docker.io/library/python",
        "public.ecr.aws/docker/library/python",
        "e529028263dbe6910a2d96f7d2b8f5266385e917fd45d286ef166977c094a51e",
    ),
    "trivy": (
        "docker.io/aquasec/trivy",
        "ghcr.io/aquasecurity/trivy",
        "cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f",
    ),
    "syft": (
        "docker.io/anchore/syft",
        "ghcr.io/anchore/syft",
        "5999d209a342e55e9edf70bf8930fb5b86d8f2a783fa401178372c50e21b1d36",
    ),
}


def assert_bindings(workflow: dict) -> None:
    jobs = workflow["jobs"]
    admission = jobs["image-acquisition"]
    steps = admission["steps"]
    assert '[[ "$GOVERNANCE_SHA" =~ ^[0-9a-f]{40}$ ]]' == steps[0]["run"]
    checkout = steps[1]["with"]
    assert checkout["repository"] == "sgajbi/lotus-platform"
    assert checkout["ref"] == "${{ vars.LOTUS_PLATFORM_GOVERNANCE_SHA }}"
    assert checkout["persist-credentials"] is False
    for kind, (source, distribution, digest) in IMAGES.items():
        step = next(step for step in steps if step.get("id") == kind)
        assert step["env"]["SOURCE_IMAGE"] == f"{source}@sha256:{digest}"
        assert step["env"]["DISTRIBUTION_IMAGE"] == f"{distribution}@sha256:{digest}"
        assert "--verify-distribution" in step["run"]
        assert "--platform linux/amd64" in step["run"]
        assert '--github-output "$GITHUB_OUTPUT"' in step["run"]
        assert admission["outputs"][kind] == f"${{{{ steps.{kind}.outputs.image }}}}"
    for job_name in ("docker-build", "ci-local-docker"):
        job = jobs[job_name]
        assert {"integration", "coverage", "image-acquisition"} <= set(job["needs"])
        assert job["env"]["GATEWAY_BASE_IMAGE"] == "${{ needs.image-acquisition.outputs.base }}"
        commands = "\n".join(step.get("run", "") for step in job["steps"])
        pull = 'docker pull --platform linux/amd64 "${GATEWAY_BASE_IMAGE}"'
        assert pull in commands
        acquisition = 'docker image inspect "${GATEWAY_BASE_IMAGE}"'
        assert acquisition in commands
        assert commands.index(pull) < commands.index(acquisition)
        if job_name == "docker-build":
            assert commands.index(acquisition) < commands.index("docker build")
            assert '--build-arg GATEWAY_BASE_IMAGE="${GATEWAY_BASE_IMAGE}"' in commands
            for kind in ("syft", "trivy"):
                variable = f"{kind.upper()}_IMAGE"
                assert job["env"][variable] == f"${{{{ needs.image-acquisition.outputs.{kind} }}}}"
                assert f'docker pull --platform linux/amd64 "${{{variable}}}"' in commands
                assert f'docker image inspect "${{{variable}}}"' in commands
            assert "--severity HIGH,CRITICAL" in commands
            assert "--exit-code 1" in commands
        else:
            assert commands.index(acquisition) < commands.index("make ci-local-docker")


@pytest.fixture(params=["pr-merge-gate.yml", "main-releasability.yml"])
def workflow(request: pytest.FixtureRequest) -> dict:
    return yaml.safe_load((ROOT / ".github/workflows" / request.param).read_text(encoding="utf-8"))


def test_protected_acquisition_uses_admitted_outputs(workflow: dict) -> None:
    assert_bindings(workflow)


@pytest.mark.parametrize("fault", ["dependency", "scanner", "base", "verify", "digest", "ref"])
def test_binding_guard_refuses_acquisition_bypasses(workflow: dict, fault: str) -> None:
    invalid = deepcopy(workflow)
    jobs = invalid["jobs"]
    steps = jobs["image-acquisition"]["steps"]
    if fault == "dependency":
        jobs["ci-local-docker"]["needs"].remove("image-acquisition")
    elif fault == "scanner":
        jobs["docker-build"]["env"]["TRIVY_IMAGE"] = "aquasec/trivy:0.72.0"
    elif fault == "base":
        jobs["docker-build"]["env"]["GATEWAY_BASE_IMAGE"] = "python:3.11-slim"
    elif fault == "verify":
        step = next(step for step in steps if step.get("id") == "syft")
        step["run"] = step["run"].replace("--verify-distribution", "")
    elif fault == "digest":
        step = next(step for step in steps if step.get("id") == "trivy")
        step["env"]["DISTRIBUTION_IMAGE"] = "ghcr.io/aquasecurity/trivy:latest"
    else:
        steps[1]["with"]["ref"] = "main"
    with pytest.raises(AssertionError):
        assert_bindings(invalid)


def test_base_output_reaches_dockerfile_and_compose() -> None:
    distribution = f"{IMAGES['base'][1]}@sha256:{IMAGES['base'][2]}"
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert dockerfile.startswith(
        f"ARG GATEWAY_BASE_IMAGE={distribution}\nFROM ${{GATEWAY_BASE_IMAGE}} AS base\n"
    )
    compose = yaml.safe_load((ROOT / "docker-compose.ci-local.yml").read_text(encoding="utf-8"))
    service = compose["services"]["ci-local"]
    assert service["platform"] == "linux/amd64"
    assert service["build"]["args"]["GATEWAY_BASE_IMAGE"] == (
        f"${{GATEWAY_BASE_IMAGE:-{distribution}}}"
    )
