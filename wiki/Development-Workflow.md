# Development Workflow

## Branching and slice model

- branch from `main`
- keep one branch per RFC or documentation slice
- use PR-first delivery
- keep commits small and scoped to one real improvement area
- preserve behavior unless a change is intentional, tested, and documented
- merge with rebase only and delete the feature branch after merge

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
- `make demo-certification`
  deterministic Gateway demo-certification evidence; report-only until promoted by governance

## Documentation workflow

- keep `README.md` concise and repo-front-door focused
- keep `wiki/` as the authored wiki source
- keep route-family detail and request examples in the wiki, not in the README
- keep deep architecture and RFC detail in `docs/`
- update [REPOSITORY-ENGINEERING-CONTEXT.md](https://github.com/sgajbi/lotus-gateway/blob/main/REPOSITORY-ENGINEERING-CONTEXT.md) when route
  ownership, startup commands, CI posture, or integration boundaries change
- update [docs/demo/README.md](https://github.com/sgajbi/lotus-gateway/blob/main/docs/demo/README.md) when demo-safe claims or certification
  evidence change
- run the repo wiki check before merge when wiki source changes:

```powershell
..\lotus-platform\automation\Sync-RepoWikis.ps1 -CheckOnly -Repository lotus-gateway
```

## Merge hygiene

PR auto-merge is rebase-only for linear history. The `Queue Auto Merge` helper uses
`LOTUS_AUTOMERGE_TOKEN` with `gh pr merge --auto --rebase --delete-branch`; when that token is not
available, the helper emits a warning and exits successfully so an authorized human or release actor
can perform the rebase merge without leaving a false red CI check.

## Engineering guardrails

1. Workbench should consume Gateway, not raw upstream services.
2. Gateway may compose, reshape, and annotate responses, but domain authority stays upstream.
3. Request-shape differences must be documented in [API Surface](API-Surface) with examples.
4. New route families need contract or integration tests before they become supported claims.
5. Do not add metric labels, logs, or evidence fields that expose portfolio, client, document,
   prompt, response, trace, or correlation payloads.
