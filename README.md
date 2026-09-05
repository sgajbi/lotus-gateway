# lotus-gateway

The experience API for Lotus wealth applications.

Gateway brings source-owned portfolio, analytics and workflow information together for
Workbench, preserving access boundaries, evidence and explicit unavailable states.

## What Gateway Enables

For product teams building on Lotus, Gateway provides:

- one governed, product-oriented API for `lotus-workbench` instead of nine service integrations
- composed product views — advisor book, performance and risk workspaces, proposals with policy
  evaluation, DPM command center, reporting, advisor brief — that preserve each source's
  authority, evidence and supportability
- explicit partial, degraded, unavailable and permission-blocked states the UI can render
  truthfully: in composed views, a degraded optional enrichment source degrades only its own
  typed fact block (the Advisor Book workspace keeps its cohort rows, for example), while a
  failed required source — an unresolvable membership cohort, a missing core portfolio payload —
  still fails that request explicitly rather than fabricating a partial answer
- trusted caller-context admission, replay-identified writes for the mutation families whose
  contracts require an `Idempotency-Key`, semantic validation of source responses, and bounded
  product-safe errors at every route

## Place In The Platform

```text
lotus-workbench  (product UI and BFF consumer)
        │
        ▼
lotus-gateway    (experience API: context admission → bounded composition →
        │         source-semantic response validation → explicit supportability)
        ▼
owning services  lotus-core · lotus-performance · lotus-risk · lotus-advise ·
                 lotus-manage · lotus-report · lotus-archive · lotus-idea · lotus-ai
```

Domain authority stays with the owning services: Core owns portfolio facts, Performance and Risk
own analytics, Advise/Manage/Idea own their workflows, Report owns report execution, Archive owns
documents, and AI owns its execution and accepted-output contracts. Gateway composes, validates
and publishes; it never recomputes domain truth, mints source-owned domain record identity, or
invents evidence (transport identifiers such as correlation ids and replay keys are
Gateway-generated plumbing, not domain records).

## Capability And Availability

Supported business journeys, concisely: portfolio views with allocations, transactions and
tax-lot drill-down; performance and risk workspaces with evidence lineage; proposal lifecycle
with policy evaluation, reviewed narrative and delivery posture; advisor book and
advisor cockpit; bank-demo proof publication; DPM command center (construction, waves and campaigns,
proof packs, outcome reviews, portfolio memory, PM operating quality); report ordering options
(`/api/v1/report-ordering/options`) and durable report jobs and batches
(`/api/v1/report-batches`), where own-book membership is resolved through Core source truth and
`lotus-report` keeps catalogue and lifecycle authority; archived document retrieval; idea review
queues with governed candidate actions; and AI-assisted summaries through governed workflow-pack
seams.

- Full route catalogue with copy-paste examples:
  [wiki/API-Surface.md](wiki/API-Surface.md)
- Implementation-backed capability claims:
  [wiki/Supported-Features.md](wiki/Supported-Features.md)

Availability limits stay visible: Gateway by itself does not certify end-to-end demo readiness —
populated Workbench proof requires the governed Workbench canonical runtime and platform QA
evidence, entered through [docs/demo/README.md](docs/demo/README.md).

## Getting Started

Prerequisites: Python 3.11+, `make`, and network access to the Lotus upstream services you
exercise (unit and contract tests run without them).

```bash
make install
make run-canonical
```

Health check and expected result:

```bash
curl http://127.0.0.1:8111/health
# {"status":"ok"}
```

Two local addresses with different purposes:

- `http://gateway.dev.lotus` — canonical identity for cross-app product validation
- `http://127.0.0.1:8111` — direct process debugging only

On Windows, canonical startup depends on `--app-dir src` (already part of `make run-canonical`);
see [wiki/Getting-Started.md](wiki/Getting-Started.md) if health is green but product routes 404.

## Where To Go Next

| You need | Start here |
| --- | --- |
| Capabilities and demo claims | [wiki/Supported-Features.md](wiki/Supported-Features.md), [docs/demo/README.md](docs/demo/README.md) |
| API integration | [wiki/API-Surface.md](wiki/API-Surface.md), [REPOSITORY-ENGINEERING-CONTEXT.md](REPOSITORY-ENGINEERING-CONTEXT.md) |
| Architecture | [docs/architecture.md](docs/architecture.md), [docs/standards/RFC-0082-upstream-contract-family-map.md](docs/standards/RFC-0082-upstream-contract-family-map.md) |
| Operations | [wiki/Operations-Runbook.md](wiki/Operations-Runbook.md), [wiki/Troubleshooting.md](wiki/Troubleshooting.md), [wiki/Validation-and-CI.md](wiki/Validation-and-CI.md) |
| Contribution and quality gates | [CONTRIBUTING.md](CONTRIBUTING.md), [wiki/Development-Workflow.md](wiki/Development-Workflow.md), [quality/README.md](quality/README.md) |
| Folder guides | [src/app](src/app/README.md) · [routers](src/app/routers/README.md) · [services](src/app/services/README.md) · [contracts](src/app/contracts/README.md) · [clients](src/app/clients/README.md) · [tests](tests/README.md) · [docs](docs/README.md) · [scripts](scripts/README.md) |

Repository-authored wiki pages live under [wiki/](wiki); `wiki/` is the canonical source and the
published GitHub wiki is publication plumbing only.
