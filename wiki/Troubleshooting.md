# Troubleshooting

Use this page to decide whether a failure belongs in Gateway, an upstream domain service, platform
runtime, or documentation.

## Common checks

- if startup looks healthy but routes 404, verify `--app-dir src`
- if the UI gets partial or degraded payloads, inspect upstream readiness and supportability first
- if platform capabilities look wrong, verify `consumerSystem` and `tenantId` query shape
- if domain-product discovery returns `503`, verify the generated platform catalog and dependency
  graph paths before changing gateway contracts
- if intake upload requests fail, verify the camelCase multipart aliases expected by gateway
- if proposal writes fail, verify `Idempotency-Key`
- if archived document lookup or download fails, verify caller context headers and `lotus-archive`
  readiness before changing Gateway response contracts
- if analytics diagnostics returns forbidden, verify `X-Actor-Id`, `X-Tenant-Id`, `X-Region`, and
  an operator support role in `X-Role`
- if Workbench direct upstream calls appear in evidence, treat that as an integration-boundary
  defect; product UI should consume Gateway

## Useful commands

```bash
make check
make ci
make ci-local-docker
make demo-certification
```

## Triage checklist

1. Identify the route family and exact request shape.
2. Confirm the canonical runtime used `make run-canonical` or `--app-dir src`.
3. Capture product-safe status class, source service, degraded reason, and support reference.
4. Check the owning upstream service before changing Gateway business semantics.
5. For docs defects, update README/wiki/docs together with any pinned documentation tests.

## References

- [docs/architecture.md](../docs/architecture.md)
- [docs/standards/RFC-0082-upstream-contract-family-map.md](../docs/standards/RFC-0082-upstream-contract-family-map.md)
- [docs/demo/README.md](../docs/demo/README.md)
