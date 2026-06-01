# Security

`lotus-gateway` is an API entry point and must protect downstream services, client data, and
operator surfaces.

## Current Controls

1. `pip-audit` runs in repo-native CI.
2. A governed temporary exception exists for `PYSEC-2026-161` because FastAPI constrains Starlette
   below the fixed line.
3. Correlation middleware avoids leaking raw payloads.
4. Analytics audit and diagnostics paths use bounded product-safe fields.
5. CORS, downstream HTTP resilience, and error handling are covered by existing tests.

## Security Baseline Additions

This slice adds report-only baseline tooling for:

1. `bandit`,
2. `deptry`,
3. `vulture`,
4. `import-linter`,
5. `spectral` OpenAPI checks.

## Required Security Posture

1. Secrets must come from environment/configuration, not source code.
2. Logs and metrics must not expose sensitive client, portfolio, holding, transaction, prompt,
   model-output, entitlement, or document content.
3. Downstream errors must be product-safe and should not leak raw upstream stack traces or internal
   topology beyond governed service names.
4. Protected diagnostics must be auditable and role-aware.
5. Mutating operations should define idempotency and audit behavior.

## Future Blocking Gates

1. No new high-severity Bandit findings.
2. No new dependency vulnerabilities outside governed exceptions.
3. No new route that logs or returns sensitive raw downstream payloads.
4. Dedicated regression tests for auth, diagnostics, data masking, and problem-details errors.
