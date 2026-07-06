# Operations Runbook

This page summarizes everyday operational checks. Use
[docs/operations-runbook.md](../docs/operations-runbook.md) for the root runbook and
[Troubleshooting](Troubleshooting) for failure triage.

## Important operational checks

- confirm canonical gateway identity is `gateway.dev.lotus` before product validation
- if Windows startup looks healthy but routes fail, verify `--app-dir src`
- treat partial-failure and supportability signals as contract data, not as noise to suppress
- use repo-native gates before inventing custom checks
- preserve support references and bounded degraded reasons when escalating incidents
- use [docs/operations-runbook.md](../docs/operations-runbook.md),
  [docs/observability.md](../docs/observability.md), and
  [docs/security.md](../docs/security.md) as the consolidated root-doc entry points for
  operators and enterprise-readiness reviews

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
  metric-family names and label contracts.
- Do not add gateway analytics metric labels outside that contract.
- Prometheus collector labels are covered by the static unit gate in
  `tests/unit/test_prometheus_metric_label_contracts.py`; add new metric families to the code-owned
  contract before expecting CI to pass.
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
- Degraded metric `reason` labels are limited to the code-owned vocabulary:
  `source_supportability_partial`, `source_supportability_degraded`, `upstream_warning`,
  `partial_failure_code`, `upstream_unavailable`, `upstream_error`, and `unknown`. Upstream
  supportability prose, warning text, portfolio IDs, client names, trace IDs, prompts, model output,
  entitlement text, and partial-failure details must not become Prometheus label values.
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

## Foundation workspace performance horizon

- The Foundation workspace resolves the Core analytics reference before calling
  `lotus-performance`.
- `PortfolioAnalyticsReference.performance_end_date` is the report end date for the Foundation YTD
  TWR request when Core publishes it.
- This prevents a weekend, holiday, or otherwise incomplete calendar date from creating a
  misleading degraded performance fan-out when the latest complete performance horizon is ready.
- If the analytics reference lookup is unavailable, Gateway falls back to the snapshot as-of date
  and surfaces any resulting performance degradation through the normal warning and partial-failure
  contract.

## Practical probes

```powershell
$GATEWAY_BASE_URL = "http://127.0.0.1:8111"
curl "$GATEWAY_BASE_URL/health/ready"
curl "$GATEWAY_BASE_URL/api/v1/foundation/portfolios/PF_1001/workspace"
curl "$GATEWAY_BASE_URL/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=default"
curl "$GATEWAY_BASE_URL/api/v1/analytics-ui/diagnostics/gdiag-risk-summary-permission-blocked" \
  -H "X-Actor-Id: support-operator-1" \
  -H "X-Tenant-Id: tenant-sg" \
  -H "X-Region: APAC" \
  -H "X-Role: support-operator"
```

## Demo certification probe

```powershell
make demo-certification
```

Use the generated `output/demo-certification/gateway-demo-certification.json` as Gateway API
evidence. It is not a replacement for populated Workbench browser proof.

## Key references

- [docs/documentation/experience-api-foundation-blueprint.md](../docs/documentation/experience-api-foundation-blueprint.md)
- [docs/standards/RFC-0082-upstream-contract-family-map.md](../docs/standards/RFC-0082-upstream-contract-family-map.md)
- [docs/demo/README.md](../docs/demo/README.md)
