# Overview

## Business role

`lotus-gateway` is the governed experience API for Lotus product clients, primarily
`lotus-workbench`.

It shapes product-facing contracts from upstream domain services without becoming the authority for
their business truth.

## Ownership boundaries

This repo owns:

1. product-facing API composition
2. partial-readiness-aware aggregation
3. gateway-level routing and contract governance
4. experience-oriented payload shaping and degraded-state handling

This repo does not own:

1. portfolio source truth, which belongs to `lotus-core`
2. performance methodology, which belongs to `lotus-performance`
3. risk methodology, which belongs to `lotus-risk`
4. reporting methodology, which belongs to `lotus-report`
5. advisory and management workflow truth, which belong upstream

## Current posture

- primary backend contract for `lotus-workbench`
- canonical local service identity is `gateway.dev.lotus`
- live integration boundary where Docker parity matters
- high drift risk because gateway changes directly affect the product UI
