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
- `portfolio_id`, `client_id`, `client_name`, `holding_id`, `transaction_id`, `session_id`,
  `simulation_session_id`, `upload_id`, `document_id`, `trace_id`, `correlation_id`, request
  bodies, response bodies, raw prompts, model output, and raw entitlement failures must not become
  metric labels or structured telemetry dimensions.
- Gateway emits product-safe structured fan-out logs for selected Workbench performance and risk
  analytics operations.
- Gateway also emits product-safe fan-out logs and metrics through the central `lotus-manage`,
  `lotus-report`, `lotus-archive`, `lotus-ai`, direct `lotus-core` query/control-plane, and
  `lotus-core` ingestion client seams.
- Gateway emits `lotus_gateway_analytics_fanout_duration_seconds` with bounded `operation`,
  `service`, and `status_class` labels for implemented Gateway fan-out operations.
- Gateway emits `lotus_gateway_analytics_degraded_total` with bounded `operation`, `service`, and
  `reason` labels when implemented Gateway fan-out is partial, degraded, or failed.
- Gateway emits product-safe selected analytics read audit logs for upstream read outcomes:
  `gateway.analytics.audit.analytics_read_allowed` for successful upstream reads and
  `gateway.analytics.audit.analytics_read_denied` for `401` or `403` upstream denials.
- Gateway requires caller context on the RFC-0108 certified Workbench read paths now enforced in
  this repository: performance summary, risk summary, and advisor brief. The advisor-brief
  review-action route also requires the same caller context because it records a bounded workflow
  review action through the Gateway boundary.
- Advisor-brief read audit records use `operation=advisor_brief.summary` and
  `panel=advisor-brief`. Treat `analytics_read_denied` with `reason=upstream_authorization_denied`
  as a permission-blocked read and investigate upstream entitlement posture without expecting
  portfolio, client, prompt, response-body, trace, or raw entitlement details in the audit fields.
- Gateway exposes a protected operator lookup at
  `GET /api/v1/analytics-ui/diagnostics/{support_reference}`. It requires `X-Actor-Id`,
  `X-Tenant-Id`, `X-Region`, and an operator support role in `X-Role`.
- Protected analytics diagnostics lookups emit
  `gateway.analytics.audit.protected_diagnostics_lookup` with only bounded audit fields:
  route, panel, operation, state, reason, status class, region, and environment.
- The diagnostics response resolves opaque safe support references into panel, operation, service,
  supportability state, and operator guidance. It must not expose portfolio, client, holding,
  trace, correlation, request, response, or raw entitlement-failure identifiers.
- Dashboard claims and Workbench attention events outside the Workbench surface remain planned
  until later RFC-0108 slices promote them with evidence.

## Practical probes

```powershell
curl http://127.0.0.1:8111/health/ready
curl "http://127.0.0.1:8111/api/v1/foundation/portfolios/PF_1001/workspace"
curl "http://127.0.0.1:8111/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=default"
curl "http://127.0.0.1:8111/api/v1/analytics-ui/diagnostics/gdiag-risk-summary-permission-blocked" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: support-operator"
```

## Key references

- [docs/documentation/experience-api-foundation-blueprint.md](../docs/documentation/experience-api-foundation-blueprint.md)
- [docs/standards/RFC-0082-upstream-contract-family-map.md](../docs/standards/RFC-0082-upstream-contract-family-map.md)
- [docs/demo/README.md](../docs/demo/README.md)
