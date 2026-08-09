# Scalability and Availability Standard Alignment

Service: lotus-gateway (lotus-gateway)

This repository adopts the platform-wide standard defined in lotus-platform/Scalability and Availability Standard.md.

## Implemented Baseline

- Stateless service behavior with externalized durable state.
- Explicit timeout and bounded retry/backoff for inter-service communication where applicable.
- Health/liveness/readiness endpoints for runtime orchestration.
- Observability instrumentation for latency/error/throughput diagnostics.

## Required Evidence

- Compliance matrix entry in lotus-platform/output/scalability-availability-compliance.md.
- Service-specific tests covering resilience and concurrency-critical paths.

## Availability Baseline

- Internal SLO baseline: p95 response latency < 300 ms for health and capability endpoints; error rate < 1%.
- Recovery assumptions: RTO 30 minutes, RPO 15 minutes for dependent platform data recovery.
- Backup and restore: persistence-owning upstream services are required to expose validated backup/restore runbooks;
  lotus-gateway validates readiness through `/health/ready` and dependency checks during platform startup.

## Performance Summary Completion Deadline

- The Workbench performance-summary route applies a 30-second end-to-end monotonic completion
  budget to the `lotus-performance` workspace-summary submission and result polling flow. The
  budget is configured by `PERFORMANCE_SUMMARY_DEADLINE_SECONDS`; the separate
  `PERFORMANCE_ANALYTICS_TIMEOUT_SECONDS` remains the maximum for one upstream request.
- Result reads use the smaller of the per-request timeout and the remaining completion budget.
  Polling honors source `recommended_poll_after_seconds` guidance and is bounded by elapsed time,
  not an attempt count. Result reads do not add nested transport retries because the outer polling
  loop owns the remaining budget and next-read decision.
- One calculation identity, caller correlation, trace, and authorization context are preserved
  from submission through result retrieval. Gateway does not respond to an identity conflict by
  submitting another financial calculation.
- If the budget expires, the analytics client returns reason code
  `ASYNC_RESULT_DEADLINE_EXHAUSTED` with the original result identity. The Workbench experience API
  converts that source failure into its existing explicit partial-readiness response before the
  caller transport closes; a warm-cache retry is not treated as readiness proof.
- Gateway fan-out telemetry records the bounded degraded reason
  `async_poll_deadline_exhausted`. It does not place calculation, portfolio, client, correlation,
  or trace identifiers in metric labels or structured log fields.

## Database Scalability Fundamentals

- Query plan and index ownership remain with lotus-core/lotus-performance/lotus-manage/lotus-report persistence domains; lotus-gateway does not own tables.
- Growth assumptions for upstream payload sizes are reviewed quarterly and reflected in lotus-gateway timeout and pagination policies.
- Retention and archival execution remains upstream, while lotus-gateway enforces request shaping to avoid unbounded historical fan-out.

## Caching Policy Baseline

- lotus-gateway does not own correctness-critical caches for financial calculations; upstream lotus-core/lotus-performance/lotus-report remain the source of truth.
- Client-facing response shaping may use explicit TTL request controls where contract-approved (`ttl_hours`), with ownership in lotus-gateway read orchestration.
- Invalidation owner is the upstream domain service that owns source data; stale-read tolerance is limited to UI convenience views only.
- Any cache addition requires explicit TTL, invalidation owner, and stale-read behavior documented via ADR/RFC.

## Scale Signal Metrics Coverage

- lotus-gateway exports service HTTP metrics via `/metrics` and follows platform label conventions (`service`, `env`, `endpoint`, `status_code`).
- Platform-shared infrastructure metrics for CPU/memory, database, and queue signals are sourced through:
  - `lotus-platform/platform-stack/prometheus/prometheus.yml`
  - `lotus-platform/platform-stack/docker-compose.yml`
  - `lotus-platform/Platform Observability Standards.md`

## Deviation Rule

Any deviation from this standard requires ADR/RFC with remediation timeline.


