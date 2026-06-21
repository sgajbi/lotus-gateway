# Getting Started

This page is for a new engineer, operator, or demo-prep reviewer who needs a working Gateway
process and a few high-signal probes.

## Prerequisites

1. Python dependencies available for the repo.
2. `make` available in the shell.
3. Optional platform ingress when using `http://gateway.dev.lotus`.
4. Sibling `lotus-platform` generated artifacts when testing domain-product discovery.

## Install

```bash
make install
```

## Run locally

```bash
make run-canonical
```

Canonical identities:

- cross-app and product validation: `http://gateway.dev.lotus`
- direct process debugging: `http://127.0.0.1:8111`

`make run-canonical` uses `uvicorn app.main:app --reload --app-dir src --host 0.0.0.0 --port 8111`.
The `--app-dir src` flag is part of the supported startup contract.

## First checks

```powershell
curl http://127.0.0.1:8111/health
curl "http://127.0.0.1:8111/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=default"
curl "http://127.0.0.1:8111/api/v1/domain-products/catalog?consumerSystem=lotus-workbench"
curl "http://127.0.0.1:8111/api/v1/domain-products/trust-certification?consumerSystem=lotus-workbench"
```

If health is green but product routes still 404 on Windows, verify startup used `--app-dir src`
before debugging gateway contracts.

Domain-product discovery depends on platform-generated artifacts under the sibling
`lotus-platform/generated/` directory by default. Live trust certification depends on
`lotus-platform/output/trust-certification/domain-product-live-trust-certification.json` by
default and returns an explicit unavailable posture until that artifact exists. The Docker Compose
runtime mounts these platform artifact directories read-only at `/lotus-platform/generated` and
`/lotus-platform/output/trust-certification`. Use `DOMAIN_PRODUCT_CATALOG_PATH`,
`DOMAIN_PRODUCT_DEPENDENCY_GRAPH_PATH`, and `DOMAIN_PRODUCT_LIVE_TRUST_CERTIFICATION_PATH` when a
runtime image mounts those artifacts elsewhere.

## Demo readiness smoke

Run the deterministic app-level Gateway certification before using Gateway claims in a demo:

```bash
make demo-certification
```

The command writes:

```text
output/demo-certification/gateway-demo-certification.json
```

This is Gateway API evidence only. UI screenshots and populated Workbench demo claims still need
the governed Workbench runtime and platform QA evidence.

## First docs to read

- [README.md](../README.md)
- [REPOSITORY-ENGINEERING-CONTEXT.md](../REPOSITORY-ENGINEERING-CONTEXT.md)
- [docs/demo/README.md](../docs/demo/README.md)
- [docs/documentation/experience-api-foundation-blueprint.md](../docs/documentation/experience-api-foundation-blueprint.md)
- [docs/standards/RFC-0082-upstream-contract-family-map.md](../docs/standards/RFC-0082-upstream-contract-family-map.md)
