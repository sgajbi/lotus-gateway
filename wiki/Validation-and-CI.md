# Validation and CI

## Lane model

`lotus-gateway` uses:

1. `Remote Feature Lane`
2. `Pull Request Merge Gate`
3. `Main Releasability Gate`
4. platform-facing validation for cross-app experience changes

## Local command mapping

- `make check`
  lint, typecheck, OpenAPI contract proof, unit tests
- `make ci`
  migration smoke, integration tests, coverage, security audit
- `make ci-local`
  local feature-lane validation
- `make ci-local-docker`
  Docker parity for the integration boundary

## What the gates protect

- workbench-facing contract integrity
- startup and migration truth
- upstream composition safety
- live integration-boundary parity
