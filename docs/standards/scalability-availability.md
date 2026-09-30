# Scalability and Availability Standard Alignment

Service: lotus-gateway (lotus-gateway)

This repository adopts the platform-wide standard defined in lotus-platform/Scalability and Availability Standard.md.

## Implemented Baseline

- Stateless service behavior with externalized durable state.
- Explicit timeout and bounded retry/backoff for inter-service communication where applicable.
- Request retry policy uses an explicit HTTPX allow-list: timeouts (when enabled), network errors,
  and remote protocol disconnects may retry; redirect loops, unsupported protocols, local protocol
  errors, and unclassified request errors are terminal and are not reinterpreted as deadline-worthy
  transient polling failures.
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
- Attribution-history source work uses a process-wide bulkhead configured by
  `ATTRIBUTION_TREND_CONCURRENCY_LIMIT` (default `4`) and one monotonic queued-plus-active
  request budget configured by `ATTRIBUTION_TREND_DEADLINE_SECONDS` (default `30`). Each
  requested date bucket keeps one ordered final disposition; failed or timed-out buckets retain
  null financial values rather than becoming zero effects. Deployment-wide source admission is
  the per-process limit multiplied by the number of Gateway replicas, so replica changes must be
  reconciled with the Performance admission budget.
- Durable accepted-job recovery is not yet provided for attribution history. The current
  Performance client combines submission and polling and exposes `result_path` only in its final
  response; cancellation after a source `202` can therefore lose that handle, and a later
  Workbench GET has no stable replay key with which to recover it. Gateway has no durable
  calculation-job store, so a process-local cache or shielded background task would not survive a
  restart and is not a valid recovery control. The smallest follow-up contract is a
  tenant-scoped, caller-stable idempotency key accepted by Performance attribution submission,
  payload-mismatch rejection, and a durable accepted response that replays the same
  `calculation_id` and authorized `result_path` for the source-declared retention period. Gateway
  must accept and forward that key before retry/disconnect recovery can be claimed. The
  source-owned contract is tracked by `sgajbi/lotus-performance#563`.
- Submission and result reads use the smaller of the per-request timeout and the remaining
  completion budget. Gateway also wraps each complete HTTP await in the remaining monotonic
  budget, so multiple transport phases and slow response-byte trickles cannot extend the
  caller-visible deadline beyond the configured allowance.
  Gateway waits for the accepted response's `recommended_poll_after_seconds` minimum cadence
  before the first result read and honors refreshed guidance after each pending result. Polling is
  bounded by elapsed time, not an attempt count. Result reads do not add nested transport retries
  because the outer polling loop owns the remaining budget and next-read decision. Typed transient
  transport and timeout outcomes continue through that outer loop while budget remains; an actual
  upstream HTTP error response remains terminal and is not reclassified as a transport failure.
- One calculation identity, caller correlation, trace, and authorization context are preserved
  from submission through result retrieval. Gateway does not respond to an identity conflict by
  submitting another financial calculation.
- If the budget expires, the analytics client returns reason code
  `ASYNC_RESULT_DEADLINE_EXHAUSTED`. It includes the original calculation identity and result path
  only after the source has published an accepted response; if submission acceptance is unknown,
  Gateway omits that identity rather than inventing retrievability. The Workbench experience API
  converts that source failure into the specific
  `PERFORMANCE_WORKSPACE_SUMMARY_DEADLINE_EXHAUSTED` partial-readiness warning and preserves the
  source error code. It does not start execution or lineage evidence reads after the budget has
  expired; a warm-cache retry is not treated as readiness proof.
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


