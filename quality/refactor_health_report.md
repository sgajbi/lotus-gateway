# Refactor Health Report

Date: 2026-06-02  
Phase: baseline/report-only

## Current Direction

Recent gateway hardening has reduced monolithic Workbench, router-registry, performance workspace,
advisor-brief, risk drawdown, risk rolling, and risk attribution responsibilities by extracting
focused service adapters and has extracted risk concentration response mapping behind a dedicated
service module. Shared risk unavailable-envelope helpers now centralize risk upstream failure
detail mapping, risk-service unavailable supportability, and risk metadata construction while
preserving public behavior and keeping CI green. The risk drawdown response mapper has now been
extracted to a dedicated drawdown module, reducing `risk_workspace_service.py` to 1,594 lines while
leaving request orchestration and cache semantics in the workspace service. The risk rolling
response mapper, Sharpe fallback policy, and unavailable envelope have been extracted to a
dedicated rolling module, reducing `risk_workspace_service.py` to 1,185 lines while preserving
retry, request, and cache semantics in the workspace service. The risk attribution response
mapper, blocked/unavailable envelopes, and focused attribution module tests have been extracted to
a dedicated attribution module, reducing `risk_workspace_service.py` to 780 lines while preserving
request, cache, and correlation semantics in the workspace service. The remaining work is still
substantial: large portfolio, performance workspace, contract, and client modules remain.

## Health Signals

| Area | Current posture | Evidence |
| --- | --- | --- |
| Branch hygiene | Healthy | clean `main` before the router-registry split |
| Unit/contract coverage | Healthy | 942 tests passed in latest `make check` evidence |
| Integration coverage | Healthy | 207 integration tests passed in recent `make ci` evidence |
| Total coverage | Healthy | 92.65%, above the 84% floor |
| Security audit | Governed | `pip-audit` passes with one documented FastAPI/Starlette exception |
| Modularity | Improving, incomplete | Several service files remain above 1,000 lines |
| API governance | Improving, incomplete | Generated OpenAPI has only small description/tag/error gaps |
| Architecture rules | Improving, incomplete | AST boundary tests exist; import-linter is new report-only baseline |
| Observability | Partial | Health/readiness/metrics/correlation exist; trace/log scoring not enforced |

## Primary Refactor Backlog

1. Split `portfolio_service.py` into source-readiness, transaction/activity, income, workspace,
   and workflow-cue adapters.
2. Continue splitting `risk_workspace_service.py` by risk surface; the next risk workspace target
   should be a bounded summary response module extraction after the shared unavailable-envelope,
   drawdown, rolling, and attribution helpers.
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
