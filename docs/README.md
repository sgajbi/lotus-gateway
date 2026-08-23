# Docs Guide

## Responsibility

`docs/` owns durable Gateway engineering documentation: architecture, API governance, operations,
security, demo support, standards, and RFC source material that should remain true after the current
branch merges.

## Boundary Rules

| Area | Rule | Evidence |
| --- | --- | --- |
| Durable truth | Keep implementation-backed truth in docs; avoid speculative claims. | `docs/architecture.md` |
| Standards | Link platform standards instead of copying long cross-repo policy. | `docs/standards/` |
| Operations | Keep runbooks and release notes aligned with Make targets, CI lanes, and supported runtime behavior. | `docs/operations-runbook.md` and `docs/operations/` |
| Wiki source | Reader-facing wiki truth is authored under `wiki/`, not hand-edited in the wiki remote. | `AGENTS.md` |

## Validation

Run focused documentation tests when available and `make lint` for deterministic docs/context
alignment checks. For wiki-impacting changes, run the platform wiki sync check before merge.

## Update Triggers

Update docs when architecture, API contracts, supported behavior, CI/release posture, operations,
security, demo evidence, or governance expectations change. Record an explicit no-wiki-change
decision when docs changed but repo-local wiki truth did not.
