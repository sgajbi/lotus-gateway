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

## Docker Parity

```powershell
make ci-local-docker
make ci-local-docker-down
```

Docker parity is required because gateway is a live integration boundary.

## Quality Baseline

The report-only quality workflow installs optional quality tooling and runs:

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

The workflow is intentionally `continue-on-error` during baseline classification.

## Incident Notes

1. Preserve correlation IDs when escalating gateway issues.
2. Capture upstream service, route family, status class, degraded reason, and support reference.
3. Do not paste raw client, holding, prompt, model-output, entitlement, or document payloads into
   tickets or chat.
4. Verify whether the failure is gateway composition, upstream domain truth, ingress, or platform
   runtime before changing code.
