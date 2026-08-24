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

`make check` covers lint, formatting, monetary-float guard, refactor and agent-quality thresholds,
workflow governance, the packaged Advise proposal decision-vocabulary contract, typecheck,
Workbench OpenAPI contract smoke, and unit/contract tests. Set
`LOTUS_ADVISE_PROPOSAL_DECISION_VOCABULARY_URL` to the governed GitHub contents URL when the run
must reconcile the current producer artifact; protected CI does this automatically.

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

The development and Docker test extras include `httpx2>=2.12.0,<3.0.0` because the supported
Starlette TestClient path uses HTTPX2. `make lint` runs
`scripts/check_testclient_dependency.py`, which fails on a missing or below-floor HTTPX2 version
or when importing TestClient emits Starlette's deprecated `httpx` fallback warning. The
production-only `requirements-audit.txt` intentionally excludes this test-only dependency.

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
thresholds, workflow action-runtime governance, agent quality evidence, required artifact
presence, and the checked-in quality ratchet. The ratchet fails when coverage, architecture,
complexity, dead-code, dependency, security, documentation, or OpenAPI metrics regress beyond
their reviewed baseline, while preserving current known findings as explicit trend data.

Each report-producing quality step writes one `QUALITY_COMMAND_STATUS=<integer>` marker from the
producer exit status. Artifact validation fails on missing, malformed, or duplicate markers, and
the ratchet rejects a failed tool that emitted no parseable measurement. Non-zero status alongside
known baseline findings remains visible trend evidence; it is not a claim that the tool passed
cleanly.

Run `python scripts/check_quality_baseline_ratchet.py --update-baseline` only as part of a reviewed
baseline change after inspecting the full tool output. The command auto-tightens improvements;
loosening requires a per-metric `--allow-regression METRIC=VALUE --reason "..."` justification.
CI never updates the baseline automatically.

Quality Baseline is triggered automatically by `pull_request` events targeting `main`, not by
feature-branch pushes. A feature push before a PR therefore produces no duplicate report; opening
or synchronizing the PR produces the single protected check for that head SHA. Manual dispatch
remains available for explicit revalidation. The event matrix and concurrency contract are recorded
in [`docs/quality-baseline-event-matrix.md`](quality-baseline-event-matrix.md).

The CI-local Docker parity targets derive a stable, checkout-specific Compose project from the
absolute repository path for both startup and cleanup. `CI_LOCAL_COMPOSE_PROJECT` may override that
value when an orchestrator supplies its own unique identity. This keeps `docker compose ... down
--remove-orphans` scoped to CI-owned containers, networks, and volumes; it must not stop the product
Compose project or its active Gateway container. If a shared Gateway runtime is running, verify it
remains healthy after `make ci-local-docker` and `make ci-local-docker-down`.

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
