# RFC-0097 Gateway Task-Flow Posture Slice Review

## Scope

This slice publishes bounded `lotus-ai` RFC-0097 task-flow posture through the existing
advisor-brief Gateway contract. Gateway remains a composition boundary: it forwards filters to
`lotus-ai`, selects the task flow linked to the advisor-brief run id, and preserves returned
posture without deriving review states or replacement lineage from narrative text.

## Implemented

1. `LotusAiClient` can read filtered workflow-pack task-flow catalog posture from `lotus-ai`.
2. `AdvisorBriefResponse` now carries optional `workflow_pack_task_flow` posture.
3. Advisor-brief execution and review-action responses refresh both run posture and task-flow
   posture.
4. Replacement lineage is preserved as structured task-flow lineage for `REVISE` and `SUPERSEDE`.
5. RFC-0082 upstream-family documentation and Gateway wiki integration notes now describe the
   bounded task-flow posture dependency.

## Review Findings

1. The slice uses the existing advisor-brief product contract instead of adding a thin generic
   pass-through route.
2. Gateway does not infer task-flow state from review-action requests or summaries; it only preserves
   the `lotus-ai` read model.
3. The task-flow parser fails closed to `None` on malformed or unavailable upstream posture, which
   keeps the advisor brief usable while avoiding invented lineage.
4. The focused tests prove both client forwarding and product-contract preservation; broader
   Workbench rendering remains a downstream slice.

## Proof

1. `python -m pytest tests\unit\test_advisor_brief_service.py tests\unit\test_upstream_clients.py tests\integration\test_workbench_router.py -q`
   - 92 passed.
2. `python -m ruff check ...touched gateway files...`
   - passed.
3. `python -m pytest tests\unit\test_advisor_brief_service.py tests\unit\test_upstream_clients.py tests\integration\test_workbench_router.py tests\contract\test_workbench_contract.py -q`
   - 95 passed.
4. `make typecheck`
   - passed.
5. `git diff --check`
   - passed with existing CRLF normalization warnings only.
6. `powershell -ExecutionPolicy Bypass -File C:\Users\Sandeep\projects\lotus-platform\automation\Sync-RepoWikis.ps1 -CheckOnly -Repository lotus-gateway`
   - reported expected branch-local drift for `Integrations.md`; publish after merge to `main`.
7. Post-review contract correction: parser now accepts real upstream `workflow_pack_version`.
   `python -m pytest tests\unit\test_advisor_brief_service.py tests\unit\test_upstream_clients.py tests\integration\test_workbench_router.py tests\contract\test_workbench_contract.py -q`
   - 95 passed.
8. Post-review `python -m ruff check src\app\services\advisor_brief_service.py tests\unit\test_advisor_brief_service.py`
   - passed.
9. Post-review `make typecheck`
   - passed.

## Remaining RFC-0097 Gaps

1. Workbench must consume and render the Gateway task-flow posture without relying on fallback data.
2. Heartbeat attention needs an adapter for stale, blocked, degraded, and review-waiting task flows.
3. Domain handoff execution remains a future cross-service slice.
4. Final governance review, API certification check, docs/context/wiki publication, and branch
   hygiene remain required before RFC closure.
