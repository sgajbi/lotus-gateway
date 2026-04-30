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
  proposal and advisory workflow
- `lotus-manage`
  split-routing management workflows when enabled
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
   basis, benchmark, source services, freshness, methodology, calculation versions, coverage,
   fallbacks, and limitations; `lotus-performance` remains the calculation, lineage, and methodology
   authority
5. advisor-brief responses preserve `lotus-ai` workflow-pack run posture and task-flow lineage but do not make gateway the review-state or task-flow authority
6. archived document retrieval is product-facing only through gateway document routes; Workbench
   does not call `lotus-archive` directly
