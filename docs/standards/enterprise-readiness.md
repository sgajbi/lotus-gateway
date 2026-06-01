# Enterprise Readiness Baseline (lotus-gateway/lotus-gateway)

- Standard reference: `lotus-platform/Enterprise Readiness Standard.md`
- Scope: lotus-gateway orchestration, API gateway behavior, downstream API integration controls.
- Change control: RFC required for platform rule changes; ADR required for temporary deviations.

## Security and IAM Baseline

- Service-level audit middleware captures privileged write actions (`POST/PUT/PATCH/DELETE`).
- Audit records include actor, tenant, role, and correlation identifiers.
- Sensitive fields are redacted before logging, including normalized key variants such as
  camelCase, snake_case, hyphenated, and prefixed token/account/client-email fields.

Evidence:
- `src/app/enterprise_readiness.py`
- `src/app/main.py`
- `tests/unit/test_enterprise_readiness.py`

## API Governance Baseline

- OpenAPI remains contract-first with versioned service metadata.
- Backward-compatibility and deprecation decisions are governed by RFC workflow.
- Contract and integration tests are part of CI gates.

Evidence:
- `src/app/main.py`
- `tests/contract`
- `tests/integration`

## Configuration and Feature Management Baseline

- Feature flags are centrally loaded from `ENTERPRISE_FEATURE_FLAGS_JSON`.
- Flags support tenant and role scoping with deterministic fallback order.
- Write capability rules use method plus path-segment-aware matching, with more-specific path
  rules evaluated before broader prefixes.
- Invalid config payload defaults to deny-by-default behavior.

Evidence:
- `src/app/enterprise_readiness.py`
- `tests/unit/test_enterprise_readiness.py`

## Data Quality and Reconciliation Baseline

- Request contract validation uses typed schemas; invalid payloads are rejected.
- Critical write orchestration remains fail-fast on downstream errors.

Evidence:
- `src/app/contracts`
- `src/app/services/proposal_service.py`

## Reliability and Operations Baseline

- Standard resilient HTTP client behavior (timeouts, bounded retries, explicit failures).
- Retry configuration is defensive: negative retry counts are clamped to a single attempt and
  negative backoff values are clamped to zero-delay retry behavior, preventing configuration drift
  from suppressing all upstream calls or producing invalid sleeps.
- Shared upstream HTTP helpers fail closed on unsupported methods instead of silently downgrading to
  a different verb; JSON fan-out currently supports `GET`, `POST`, and `PUT`, while binary fan-out
  supports `GET` and `POST`.
- Runbooks and migration/change controls are standardized in shared PPD standards.

Evidence:
- `src/app/clients/http_resilience.py`
- `tests/unit/test_http_resilience.py`
- `docs/standards/scalability-availability.md`
- `docs/standards/migration-contract.md`

## Privacy and Compliance Baseline

- Sensitive fields are redacted in audit metadata.
- Correlation IDs and actor context provide audit-trail traceability.

Evidence:
- `src/app/enterprise_readiness.py`
- `tests/unit/test_enterprise_readiness.py`

## Deviations

- Any deviation from the enterprise readiness baseline requires ADR with expiry/review date.


