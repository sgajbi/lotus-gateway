# Troubleshooting

## Common checks

- if startup looks healthy but routes 404, verify `--app-dir src`
- if the UI gets partial or degraded payloads, inspect upstream readiness and supportability first
- if platform capabilities look wrong, verify `consumerSystem` and `tenantId` query shape
- if domain-product discovery returns `503`, verify the generated platform catalog and dependency
  graph paths before changing gateway contracts
- if intake upload requests fail, verify the camelCase multipart aliases expected by gateway
- if proposal writes fail, verify `Idempotency-Key`

## Useful commands

```bash
make check
make ci
make ci-local-docker
```

## References

- [docs/documentation/experience-api-foundation-blueprint.md](../docs/documentation/experience-api-foundation-blueprint.md)
- [docs/standards/RFC-0082-upstream-contract-family-map.md](../docs/standards/RFC-0082-upstream-contract-family-map.md)
