# Operations Runbook

## Important operational checks

- confirm canonical gateway identity is `gateway.dev.lotus` before product validation
- if Windows startup looks healthy but routes fail, verify `--app-dir src`
- treat partial-failure and supportability signals as contract data, not as noise to suppress
- use repo-native gates before inventing custom checks

## Health and readiness surfaces

- `/health`
  broad service-health probe
- `/health/live`
  liveness probe
- `/health/ready`
  readiness probe
- `/metrics`
  observability surface for runtime monitoring

## Practical probes

```powershell
curl http://127.0.0.1:8111/health/ready
curl "http://127.0.0.1:8111/api/v1/foundation/portfolios/PF_1001/workspace"
curl "http://127.0.0.1:8111/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=default"
```

## Key references

- [docs/documentation/experience-api-foundation-blueprint.md](../docs/documentation/experience-api-foundation-blueprint.md)
- [docs/standards/RFC-0082-upstream-contract-family-map.md](../docs/standards/RFC-0082-upstream-contract-family-map.md)
- [docs/demo/README.md](../docs/demo/README.md)
