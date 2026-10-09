# Qualified protected image acquisition

Gateway #835 adopts Platform #945's existing finite image-acquisition prerequisite. It changes
distribution and immutable selection, with no scanner downgrade, security exception or feature
authority change. Gateway #834 remains a separate verified-principal consumer slice.

## Inputs and authority

| Purpose | Publisher source | Official distribution | Selected digest |
| --- | --- | --- | --- |
| Python3.11 base | docker.io/library/python | public.ecr.aws/docker/library/python | sha256:e529028263dbe6910a2d96f7d2b8f5266385e917fd45d286ef166977c094a51e |
| Trivy0.72.0 | docker.io/aquasec/trivy | ghcr.io/aquasecurity/trivy | sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f |
| Syft1.42.3 | docker.io/anchore/syft | ghcr.io/anchore/syft | sha256:5999d209a342e55e9edf70bf8930fb5b86d8f2a783fa401178372c50e21b1d36 |

The Python selection is the already-admitted single-platform manifest. Scanner selections are
indices whose admitted child/config must match linux/amd64. The retained observations establish
source/distribution metadata equality at observation, not earlier hosted mutable-tag identity.

## Operator setup

From the Gateway repository root, after independently verifying that Platform's supplied exact
main revision has green release evidence and admits all three tuples, set the existing repository
Actions variable. Replace the value with that verified complete commit SHA; never use a branch,
tag, anticipated commit or the previous six-mapping revision386b40 for the new scanner inputs.

PowerShell:

```powershell
$qualifiedPlatformSha = '<qualified-40-character-Platform-main-SHA>'
gh variable set LOTUS_PLATFORM_GOVERNANCE_SHA --repo sgajbi/lotus-gateway --body $qualifiedPlatformSha
```

Bash:

```bash
qualified_platform_sha='<qualified-40-character-Platform-main-SHA>'
gh variable set LOTUS_PLATFORM_GOVERNANCE_SHA --repo sgajbi/lotus-gateway --body "$qualified_platform_sha"
```

No registry account or secret is needed for these public publisher distributions. An absent,
malformed or refusing policy revision stops before Docker acquisition; there is no mutable
fallback. Updating this variable is an operator action requiring the recorded qualification.

## Admission and acquisition evidence

Both protected workflows run the existing Platform validator with exact original/distribution
references, linux/amd64, live distribution verification and GitHub outputs. Platform bounds
requests, elapsed time and rate-limit recovery. Failure artifacts retain raw public responses.
Build and parity jobs depend on successful admission. Main admission also depends on the exact
revision assertion; existing integration, coverage and duplicate-code dependencies remain.

The Python output reaches `GATEWAY_BASE_IMAGE` in Dockerfile and CI-local Compose. Trivy and Syft
outputs reach their actual pull/run commands. Hosted explicit linux/amd64 pulls and subsequent
Docker image inspection are retained as `base-acquired.json`, `trivy-acquired.json` and
`syft-acquired.json` in container release evidence; parity retains its own base receipt. Green
manifest verification alone does not establish that those hosted layer acquisitions succeeded.
Existing vulnerability severity/exit policy, main signing/attestation and runtime health checks
remain required. No image metadata check grants enterprise or financial acceptance.

## Local static proof

From the Gateway repository root, the following command is identical in PowerShell and Bash:

```text
python -m pytest tests/unit/test_image_acquisition_bindings.py tests/unit/test_workflow_action_runtime.py tests/unit/test_workflow_pipeline_exit_codes.py -q
```

The binding controls accept valid wiring and reject missing acquisition dependencies, mutable
base/scanner substitutions, omitted live verification, altered distribution digest and mutable
policy checkout. This command fetches no image layers and starts no Docker resources. Protected
hosted CI and exact-main release independently qualify acquisition/build/runtime behavior.
