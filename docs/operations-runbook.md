# Operations Runbook

This runbook summarizes local and CI operations for `lotus-gateway`.

## Local Startup

Use the canonical app-dir startup path:

```powershell
make run-canonical
```

The canonical local route is `http://gateway.dev.lotus` when platform ingress is active.

## Health And Metrics

1. `/health`
2. `/health/live`
3. `/health/ready`
4. `/metrics`

Readiness should fail when the process is draining and should remain product-safe.

## Local Validation

```powershell
make check
make ci
```

`make check` covers lint, formatting, monetary-float guard, typecheck, Workbench OpenAPI contract
smoke, and unit/contract tests.

`make ci` adds migration smoke, integration tests, coverage, and security audit.

Use `make clean` to remove disposable local generated artifacts and caches. It deletes `output/`,
`.codex-logs/`, coverage outputs, Python bytecode caches, package metadata, and `gateway-*.log`;
publish or preserve required evidence before cleanup.

## Docker Parity

```powershell
make ci-local-docker
make ci-local-docker-down
```

Docker parity is required because gateway is a live integration boundary.

CI-owned image release evidence is retained under `output/container-security/` artifacts. PRs build
and scan the Git-SHA-tagged image without pushing it. The Trivy image scan fails on fixable
HIGH/CRITICAL vulnerabilities and retains the full JSON scan artifact so unfixed vendor findings
remain visible for operator review. Main releasability performs SBOM generation and the Trivy scan
before pushing the same Git-SHA tag to GHCR, then captures the digest, signs the digest-pinned
image, writes provenance attestation evidence, and records the digest-pinned Kubernetes deployment
reference in `image-release-manifest.json`. Do not deploy mutable image tags. The image digest is
captured after push and must be supplied to runtime `/version` metadata by deployment configuration;
do not bake an `unknown` digest into Docker build args, ENV, or OCI labels.

## Quality Baseline

The Quality Baseline workflow installs optional quality tooling and runs:

1. ruff,
2. mypy,
3. coverage,
4. import-linter,
5. radon/xenon,
6. vulture,
7. deptry,
8. bandit,
9. pip-audit,
10. interrogate,
11. spectral.

It is no longer purely report-only. It blocks the promoted no-regression checks for refactor
thresholds, workflow action-runtime governance, agent quality evidence, and required artifact
presence, while keeping broader advisory tools report-only until false positives, thresholds,
exception policy, and lane placement are clear.

Demo certification evidence is also generated from the repo-native command:

```powershell
make demo-certification
```

The command writes:

```text
output/demo-certification/gateway-demo-certification.json
```

Use it as Gateway API evidence only. Full populated Workbench proof still requires the governed
Workbench canonical runtime and platform QA evidence.

## Incident Notes

1. Preserve correlation IDs when escalating gateway issues.
2. Capture upstream service, route family, status class, degraded reason, and support reference.
3. Do not paste raw client, holding, prompt, model-output, entitlement, or document payloads into
   tickets or chat.
4. Verify whether the failure is gateway composition, upstream domain truth, ingress, or platform
   runtime before changing code.
