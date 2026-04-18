# Development Workflow

## Branching and slice model

- branch from `main`
- keep one branch per RFC or documentation slice
- use PR-first delivery

## Repo-native commands

- `make lint`
  formatting, linting, and monetary-float guard
- `make typecheck`
  mypy on `src/`
- `make check`
  contract and unit gate
- `make ci`
  PR-grade local proof
- `make ci-local-docker`
  docker parity check

## Documentation workflow

- keep `README.md` concise and repo-front-door focused
- keep `wiki/` as the authored wiki source
- keep route-family detail and request examples in the wiki, not in the README
- keep deep architecture and RFC detail in `docs/`
