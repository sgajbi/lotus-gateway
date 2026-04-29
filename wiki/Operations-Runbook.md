# Operations Runbook

## Important operational checks

- confirm canonical gateway identity is `gateway.dev.lotus` before product validation
- if Windows startup looks healthy but routes fail, verify `--app-dir src`
- treat partial-failure and supportability signals as contract data, not as noise to suppress
- use repo-native gates before inventing custom checks

## Health and readiness surfaces

- `/health`
  broad service-health probe
- `/health/live`
  liveness probe
- `/health/ready`
  readiness probe
- `/metrics`
  observability surface for runtime monitoring

## Analytics UI observability posture

- RFC-0108 analytics UI observability vocabulary is code-owned in
  `src/app/observability/analytics_ui.py`.
- The module defines allowed labels, forbidden fields, state vocabulary, and gateway analytics
  metric-family names.
- Do not add gateway analytics metric labels outside that contract.
- `portfolio_id`, `client_id`, `client_name`, `holding_id`, `transaction_id`, `trace_id`,
  `correlation_id`, request bodies, response bodies, and raw entitlement failures must not become
  metric labels or structured telemetry dimensions.
- Gateway emits product-safe structured fan-out logs for selected Workbench performance and risk
  analytics operations.
- Gateway emits `lotus_gateway_analytics_fanout_duration_seconds` with bounded `operation`,
  `service`, and `status_class` labels for selected Workbench analytics fan-out operations.
- Gateway emits `lotus_gateway_analytics_degraded_total` with bounded `operation`, `service`, and
  `reason` labels when selected Workbench analytics fan-out is partial, degraded, or failed.
- Gateway emits product-safe selected analytics read audit logs for upstream read outcomes:
  `gateway.analytics.audit.analytics_read_allowed` for successful upstream reads and
  `gateway.analytics.audit.analytics_read_denied` for `401` or `403` upstream denials.
- Dashboard claims, Workbench attention events outside the Workbench surface, and protected
  diagnostics lookup audit remain planned until later RFC-0108 slices promote them with evidence.

## Practical probes

```powershell
curl http://127.0.0.1:8111/health/ready
curl "http://127.0.0.1:8111/api/v1/foundation/portfolios/PF_1001/workspace"
curl "http://127.0.0.1:8111/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=default"
```

## Key references

- [docs/documentation/experience-api-foundation-blueprint.md](../docs/documentation/experience-api-foundation-blueprint.md)
- [docs/standards/RFC-0082-upstream-contract-family-map.md](../docs/standards/RFC-0082-upstream-contract-family-map.md)
- [docs/demo/README.md](../docs/demo/README.md)
