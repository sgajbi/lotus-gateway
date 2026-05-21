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
  proof-pack authority APIs, RFC-0040/RFC-0041/RFC-0042 portfolio-memory read APIs,
  RFC-0041 rebalance-wave orchestration authority APIs, and RFC-0042
  post-trade outcome-review authority APIs plus PM operating quality policy/score-run lifecycle
  APIs. RFC-0098 remains the strategic Gateway DPM
  command-center contract; the RFC-0038 mandate command-center BFF route family, RFC-0039
  construction alternative-set BFF route family, RFC-0040 proof-pack BFF route family, RFC-0041
  rebalance-wave BFF route family, RFC-0042 outcome-review BFF route family, and PM operating
  quality BFF route family are now implementation-backed, while report materialization, archive,
  and optional AI posture remain governed follow-on slices until implemented and proven
- `lotus-report`
  reporting snapshot, summary, and review payloads
- `lotus-archive`
  archived generated-document metadata and controlled binary retrieval
- `lotus-ai`
  evidence-grounded advisor brief narration, DPM exception-summary support, proof-pack PM memo
  support, wave PM memo support, and outcome-review narrative support through explicit
  workflow-pack execution seams plus shared workflow-pack run-ledger and RFC-0097 task-flow
  inspection surfaces

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
    The exception-summary AI route filters the manage exception queue by exception id and optional
    portfolio, mandate, or state, builds a bounded no-raw-payload evidence envelope, and calls
    `lotus-ai` `dpm_exception_summary.pack@v1`. Gateway preserves manage source refs and content
    hashes; it does not generate summaries locally, score PMs, approve trades, contact clients,
    route orders, or invent evidence.
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
13. RFC-0040 proof packs remain `lotus-manage` truth. Gateway proof-pack realization exposes
    `/api/v1/dpm/command-center/proof-packs`,
    `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}`,
    `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/summary.md`,
    `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/report-input`, and
    `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/ai-evidence-input` for Workbench.
    Gateway also exposes
    `/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/ai-pm-memo` as a governed handoff to
    `lotus-ai` `dpm_pm_memo.pack@v1` after reading manage-owned proof-pack AI evidence input.
    Gateway forwards request bodies, idempotency keys, and correlation context to manage, then
    preserves proof-pack identity, section states, reason codes, content hashes, source hashes,
    source refs, report refs, AI refs, and lotus-ai workflow-pack run posture without generating
    proof sections, recalculating hashes, rendering reports, generating PM memos locally, or
    generating AI narrative.
14. RFC40-WTBD-010 portfolio memory remains `lotus-manage` truth. Gateway portfolio-memory
    realization exposes `/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory` for
    Workbench. Gateway forwards portfolio id, limit, and correlation context to manage, then
    preserves event order, event types, source systems, source refs, artifact refs, reason codes,
    supportability state, bounded metadata, and content hash without reconstructing timeline
    nodes, inferring mandate exceptions, calculating source-owner methods, or letting Workbench
    call `lotus-manage` directly.
15. RFC-0041 rebalance waves remain `lotus-manage` truth. Gateway wave realization exposes
    `/api/v1/dpm/command-center/waves*` for Workbench. Gateway forwards request bodies,
    idempotency keys, query filters, campaign-definition payloads, and correlation context to
    manage, then preserves wave ids, lifecycle state, item states, aggregate metrics,
    selected-alternative refs, proof-pack refs, internal handoff refs, campaign definition payloads,
    campaign workflow/audit payloads, count/page metadata, source refs, hashes, report-input
    evidence, supportability issues, remediation routes, and no-external-execution posture without
    discovering affected portfolios, discovering cohorts, recomputing campaign membership,
    calculating task state, approval state, maker-checker state, SLA posture, or workflow
    orchestration, classifying readiness, generating alternatives, approving/staging locally,
    rebuilding proof packs, generating report evidence, or claiming execution. The wave AI PM memo
    route first reads manage-owned
    `DpmWaveReportInput`, then calls `lotus-ai` `dpm_wave_pm_memo.pack@v1` for review-required
    support text; Gateway does not generate narrative locally, score PMs, approve trades, contact
    clients, place orders, or invent evidence.
    The operations-handoff summary route also reads manage-owned `DpmWaveReportInput`, including
    bounded internal `handoff_refs`, then calls `lotus-ai`
    `dpm_operations_handoff_summary.pack@v1` for review-required operations support text; Gateway
    does not route orders, claim external execution, approve trades, contact clients, or invent
    evidence.
16. PM operating quality remains `lotus-manage` truth. Gateway realization exposes
    `/api/v1/dpm/command-center/pm-operating-quality/*` for Workbench. Gateway forwards policy
    list/get/upsert, score-run preview/create/list/get, fairness-analysis preview/create/list/get,
    and review-action preview/create/list/get requests to manage, and reads Manage score-run
    evidence before invoking `lotus-ai`
    `pm_quality_summary.pack@v1` for review-gated support-only summaries. Gateway preserves policy
    configuration, score-run state, fairness-analysis state, review-action state, bounded
    rationale, target content hashes, segment posture, governance evidence, source refs, reason
    codes, content hashes, supportability, and forbidden-use posture without calculating scores,
    discovering segments, calculating segment averages or fairness spread, inferring protected
    classes, ranking PMs, administering policy locally, reinterpreting review rationale, creating
    HR or compensation decisions, performing conduct enforcement, approving trades, contacting
    clients, routing orders, claiming OMS/execution, or inventing evidence.
17. RFC36-WTBD-003 portfolio-level DPM operations dashboards consume Gateway Workbench
    `rebalance_snapshot` only. Gateway reads manage rebalance runs, preserves manage
    supportability summary and bounded recent-run posture, and keeps Workbench from calling
    `lotus-manage` directly or inventing workflow/error semantics. Supportability comes from
    manage `/api/v1/rebalance/supportability/summary`; run posture comes from
    `/api/v1/rebalance/runs`.
