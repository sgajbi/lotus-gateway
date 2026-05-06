# Integrations

## Downstream posture

- primary product consumer:
  `lotus-workbench`

## Upstream posture

- `lotus-core`
  portfolio, lookups, ingestion, simulation, and supportability
- `lotus-performance`
  performance workspace analytics and evidence lineage
- `lotus-risk`
  stateful risk workspace analytics
- `lotus-advise`
  proposal simulation, proposal persistence, workflow events, approvals, and lineage through
  `/advisory/proposals/*`
- `lotus-manage`
  discretionary management run lookup, supportability summary, capabilities, RFC-0038 mandate
  command-center summary/monitoring/exception/mandate drill-down authority APIs, RFC-0039
  construction alternative-set authority APIs, RFC-0040
  proof-pack authority APIs, RFC-0041 rebalance-wave orchestration authority APIs, and RFC-0042
  post-trade outcome-review authority APIs. RFC-0098 remains the strategic Gateway DPM
  command-center contract; the RFC-0038 mandate command-center BFF route family, RFC-0039
  construction alternative-set BFF route family, and RFC-0042 outcome-review BFF route family are
  now implementation-backed, while RFC-0041 wave composition, proof-pack modules, report
  materialization, archive, and optional AI posture remain governed follow-on slices until
  implemented and proven
- `lotus-report`
  reporting snapshot, summary, and review payloads
- `lotus-archive`
  archived generated-document metadata and controlled binary retrieval
- `lotus-ai`
  evidence-grounded advisor brief narration through the explicit workflow-pack execution seam plus shared workflow-pack run-ledger and RFC-0097 task-flow inspection surfaces

## Canonical local identities

- `lotus-gateway`
  `http://gateway.dev.lotus`
- `lotus-core query`
  `http://core-query.dev.lotus`
- `lotus-core control`
  `http://core-control.dev.lotus`
- `lotus-core ingestion`
  `http://core-ingestion.dev.lotus`
- `lotus-performance`
  `http://performance.dev.lotus`
- `lotus-risk`
  `http://risk.dev.lotus`
- `lotus-report`
  `http://report.dev.lotus`
- `lotus-archive`
  `http://archive.dev.lotus`
- `lotus-ai`
  `http://ai.dev.lotus`

## Contract notes

1. gateway contracts are product-facing and may differ intentionally from upstream parameter shapes
2. RFC-0082 governs how upstream dependency families are classified
3. supportability, readiness, and partial-failure metadata should survive composition
4. performance `evidence_view` payloads expose UI-safe product context for as-of date, period,
   basis, benchmark, source services, freshness, methodology, calculation versions, source
   calculation supportability, coverage, fallbacks, and limitations; `lotus-performance` remains
   the calculation, lineage, and methodology authority
5. risk workspace module payloads preserve source calculation supportability from `lotus-risk`
   alongside dependency-specific supportability entries; Gateway does not recompute risk
   supportability
6. advisor-brief responses preserve `lotus-ai` workflow-pack run posture and task-flow lineage but do not make gateway the review-state or task-flow authority
7. archived document retrieval is product-facing only through gateway document routes; Workbench
   does not call `lotus-archive` directly
8. Workbench and other product clients consume `lotus-gateway`; they do not call `lotus-advise` or
   `lotus-manage` directly for proposal or management workflow data
9. RFC-0098 keeps Gateway as the DPM command-center composition boundary. `lotus-manage` remains
   the DPM operating-state, rebalance-wave, and proof-pack authority, `lotus-report` remains report
   materialization authority, `lotus-risk` and `lotus-performance` remain analytics authorities,
   and Workbench remains a renderer of Gateway truth.
10. RFC-0038 mandate command-center truth remains in `lotus-manage`. Gateway realization exposes
    `/api/v1/dpm/command-center`, `/api/v1/dpm/command-center/monitoring/*`,
    `/api/v1/dpm/command-center/exceptions*`, and `/api/v1/dpm/command-center/mandates*` for
    Workbench. Gateway forwards filters and request bodies to manage, then preserves health
    distribution, monitoring-run state, active exceptions, reason codes, recommended actions,
    mandate source lineage, version diffs, and supportability without calculating health,
    discovering PM books, inferring source readiness, or resolving exceptions locally.
11. RFC-0042 outcome reviews remain `lotus-manage` truth. Gateway outcome-review realization must
    compose expected-versus-realized review summaries, dimension outcomes, source lineage,
    supportability, report-input posture, and AI-evidence posture without recomputing outcome
    values or calling source-owner apps behind manage's review authority. The implemented Gateway
    route family is `/api/v1/dpm/command-center/outcome-reviews*`,
    `/api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`, and
    `/api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`.
12. RFC-0039 construction alternatives remain `lotus-manage` truth. Gateway construction
    realization exposes `/api/v1/dpm/command-center/construction/alternative-sets/generate`,
    `/api/v1/dpm/command-center/construction/alternative-sets/{alternative_set_id}`, and
    `/api/v1/dpm/command-center/construction/alternative-sets/{alternative_set_id}/selections`
    for Workbench. Gateway forwards request bodies and idempotency/correlation context to manage,
    then preserves alternatives, method status, diagnostics, comparison metrics, supportability,
    and selection decisions without performing optimization, recomputation, readiness inference, or
    order execution.
13. RFC36-WTBD-003 portfolio-level DPM operations dashboards consume Gateway Workbench
    `rebalance_snapshot` only. Gateway reads manage rebalance runs, preserves manage
    supportability summary and bounded recent-run posture, and keeps Workbench from calling
    `lotus-manage` directly or inventing workflow/error semantics. Supportability comes from
    manage `/api/v1/rebalance/supportability/summary`; run posture comes from
    `/api/v1/rebalance/runs`.
