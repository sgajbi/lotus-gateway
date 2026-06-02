# Refactor Health Report

Date: 2026-06-02  
Phase: baseline/report-only

## Current Direction

Recent gateway hardening has reduced monolithic Workbench, router-registry, performance workspace,
and advisor-brief responsibilities by extracting focused service adapters while preserving public
behavior and keeping CI green. The remaining work is still substantial: large portfolio, risk
workspace, contract, and client modules remain.

## Health Signals

| Area | Current posture | Evidence |
| --- | --- | --- |
| Branch hygiene | Healthy | clean `main` before the router-registry split |
| Unit/contract coverage | Healthy | 934 tests passed in `make check` for the router-registry split |
| Integration coverage | Healthy | 207 integration tests passed in recent `make ci` evidence |
| Total coverage | Healthy | 92.60%, above the 84% floor |
| Security audit | Governed | `pip-audit` passes with one documented FastAPI/Starlette exception |
| Modularity | Improving, incomplete | Multiple service files remain above 1,000 lines |
| API governance | Improving, incomplete | Generated OpenAPI has only small description/tag/error gaps |
| Architecture rules | Improving, incomplete | AST boundary tests exist; import-linter is new report-only baseline |
| Observability | Partial | Health/readiness/metrics/correlation exist; trace/log scoring not enforced |

## Primary Refactor Backlog

1. Split `portfolio_service.py` into source-readiness, transaction/activity, income, workspace,
   and workflow-cue adapters.
2. Split `risk_workspace_service.py` response mappers by risk surface.
3. Split `platform_capabilities_service.py` capability normalization into smaller adapters.
4. Continue extracting performance workspace evidence and attribution helpers behind stable
   response contracts.
5. Split large contract modules only when contract ownership boundaries are clear and tests remain
   stable.
6. Normalize route-specific upstream errors toward shared problem-details mapping.
7. Add explicit API governance tests for missing operation descriptions, tags, standard errors, and
   deprecation posture.

## Quality-Gate Roadmap

1. Report-only workflow introduced in this slice.
2. Report-only workflow uploads quality logs for baseline classification.
3. Then enforce no-new-regression thresholds for:
   - ruff/mypy,
   - coverage,
   - import-linter,
   - OpenAPI spectral warnings,
   - largest-file and longest-function thresholds,
   - `pip-audit` and high-confidence `bandit` findings.
4. Enterprise-readiness gates should require docs, API, security, observability, and architecture
   scorecard sections to be green before release promotion.
