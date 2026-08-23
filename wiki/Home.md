# lotus-gateway wiki

`lotus-gateway` is the Lotus experience API and product-facing composition boundary.

It is the API contract that `lotus-workbench` should consume for product surfaces. It composes
domain-service responses into product-safe payloads, but it does not become the authority for
portfolio, performance, risk, advisory, DPM, reporting, archive, or AI truth.

## Start here

- Repo entrypoint: [README.md](../README.md)
- Repo context: [REPOSITORY-ENGINEERING-CONTEXT.md](../REPOSITORY-ENGINEERING-CONTEXT.md)
- Demo pack and claim control:
  [docs/demo/README.md](../docs/demo/README.md)
- Architecture guide:
  [docs/architecture.md](../docs/architecture.md)
- Upstream contract-family map:
  [docs/standards/RFC-0082-upstream-contract-family-map.md](../docs/standards/RFC-0082-upstream-contract-family-map.md)
- Quality and enterprise-readiness baseline:
  [quality/baseline_report.md](../quality/baseline_report.md),
  [quality/quality_scorecard.md](../quality/quality_scorecard.md), and
  [docs/architecture.md](../docs/architecture.md)

## Current phase

- primary backend contract for `lotus-workbench`
- active route families across Workbench, platform capabilities, domain-product
  discovery, proposals, reviewed advisory narrative posture, advisory policy, advisor cockpit,
  bank-demo proof, reporting, portfolio, and intake/lookups
- still replacing thin pass-through patterns with cleaner experience-API contracts

## Audience paths

- Business and demo reviewers:
  [Overview](Overview), [Supported Features](Supported-Features), [API Surface](API-Surface), and
  [Roadmap](Roadmap)
- Operators and support:
  [Getting Started](Getting-Started), [Operations Runbook](Operations-Runbook),
  [Troubleshooting](Troubleshooting), and [Integrations](Integrations)
- Engineers and agents:
  [Architecture](Architecture), [Development Workflow](Development-Workflow),
  [Validation and CI](Validation-and-CI), [RFC Index](RFC-Index), and
  [Security and Governance](Security-and-Governance)

## Most important commands

- `make install`
- `make check`
- `make ci`
- `make ci-local-docker`
- `make run-canonical`
- `make demo-certification`

## Navigation

- [Overview](Overview)
- [Architecture](Architecture)
- [API Surface](API-Surface)
- [Supported Features](Supported-Features)
- [Getting Started](Getting-Started)
- [Development Workflow](Development-Workflow)
- [Validation and CI](Validation-and-CI)
- [Operations Runbook](Operations-Runbook)
- [Integrations](Integrations)
- [Security and Governance](Security-and-Governance)
- [RFC Index](RFC-Index)
- [Roadmap](Roadmap)
- [Troubleshooting](Troubleshooting)
