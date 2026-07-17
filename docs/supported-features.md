# Supported Features

`lotus-gateway` currently supports the following product-facing route families.

## Platform And Foundation

1. health, liveness, readiness, metrics, and docs,
2. foundation workspace composition,
3. platform capability aggregation,
4. source-product execution acknowledgement.

## Workbench

1. Workbench overview and sandbox surfaces,
2. performance workspace summary, detail, evidence, attribution trend, modules, and advisor brief,
3. risk workspace summary, concentration, drawdown, rolling risk, and attribution,
4. portfolio 360 composition.

## Advisory And Proposals

1. proposal simulation, lifecycle, workflow, approval, lineage, replay, report request, delivery
   posture, and execution updates,
2. advisory workspace create, draft, save, resume, compare, rationale, review, and handoff,
3. advisory policy packs, evaluations, review queue, workflow, sign-off, report package, lineage,
   replay, event, and AI evidence,
4. advisor cockpit actions, preparation packets, snapshot, supportability, acknowledgements, and
   house-view cohorts,
5. advisory copilot evidence packets, action runs, review decisions, supportability, and
   proposal-version run lineage,
6. bank-demo proof scenario contract, supported-claim register, and proof-pack capture.

## DPM Command Center

1. command-center summary, monitoring, exceptions, mandates, and mandate drill-down,
2. construction alternative-set generation, retrieval, and selection,
3. proof-pack generation/read/Markdown/report-input/AI-evidence/AI PM memo,
4. portfolio memory,
5. outcome-review preview/create/search/detail/source-refresh/supportability/report-input,
   AI-evidence, AI narrative, and handoff,
6. PM operating quality policy, score-run, fairness, review-action, and summary-invocation route
   families,
7. wave campaign definitions, queues, approval inbox, workflow board, assignment plan,
   automation, wave report input, AI PM memo, and operations handoff summary.

## Reporting And Archive

1. portfolio-review report job submission,
2. report-job search/status/event-history/cancellation,
3. RFC-0104 report-batch materialization/status/control/retry/recovery/bounded operator-run,
4. report-batch scheduler list and run-due,
5. archived generated-document metadata and controlled binary download.

## Data Products

1. domain-product catalog,
2. product detail,
3. dependency graph,
4. live trust certification discovery.

## Ideas

1. advisor idea review queue read through `/api/v1/ideas/review-queues/advisor`,
2. source-safe idea candidate detail read through `/api/v1/ideas/candidates/{candidate_id}`,
3. candidate-scoped review-action recording through
   `/api/v1/ideas/candidates/{candidate_id}/review-actions`,
4. candidate-scoped feedback recording through `/api/v1/ideas/candidates/{candidate_id}/feedback`,
5. candidate-scoped conversion-intent recording through
   `/api/v1/ideas/candidates/{candidate_id}/conversion-intents`.

These are implementation-backed Gateway BFF routes over `lotus-idea`; they do not promote an Idea
supported feature or claim Workbench, runtime, data-product, suitability, execution, or client
communication readiness. Gateway preserves `lotus-idea` ranking, source signal identifiers, source
references, durable-storage posture, accepted/replayed mutation outcomes, and
`supportedFeaturePromoted=false`. For mutations it forwards trusted caller context, entitlement
scope, `Idempotency-Key`, correlation and trace context, and optional `X-Causation-Id` without
deriving lifecycle, authorization, audit, or downstream authority locally.

## Boundaries

Supported does not mean gateway owns source truth. Domain authority remains with the upstream
services listed in `docs/architecture.md` and `REPOSITORY-ENGINEERING-CONTEXT.md`.
