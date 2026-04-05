# Lotus Gateway Experience API Foundation Blueprint

- Status: Proposed target architecture
- Date: 2026-03-26
- Owners: lotus-gateway, lotus-workbench, lotus-platform

## Purpose

This document defines the target `lotus-gateway` architecture as the experience API for
`lotus-workbench`.

The gateway should evolve toward:

1. workspace-oriented contracts,
2. shared response-envelope and partial-failure patterns,
3. product-area orchestration modules,
4. replacement-first pre-live cleanup instead of default route versioning.

## Pre-Live API Rule

Because Lotus is not live yet:

1. stale API shapes should be replaced,
2. old APIs should be removed after migration,
3. versioned duplication should be rare and temporary,
4. the target is one clean active surface, not a growing archive.

## Core Direction

The gateway should own:

1. experience orchestration,
2. UI-facing aggregation,
3. graceful partial-failure behavior,
4. workflow-friendly action contracts,
5. supportability and evidence access for product surfaces,
6. preserved upstream provenance for AI-authored surfaces so downstream UIs can distinguish
   managed and local provider authorship without direct provider integration.

The gateway should not own:

1. domain truth,
2. permanent workarounds for upstream contract defects,
3. business semantics that belong in domain apps.

## Product Areas

The long-term gateway direction should support:

1. workspace
2. foundation
3. performance
4. risk
5. proposal
6. manage
7. reporting
8. activity
