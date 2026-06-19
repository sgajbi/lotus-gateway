from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts.advisor_brief import (
    AdvisorBriefAdvisorySupportability,
    AdvisorBriefAiSurfaceSupportability,
    AdvisorBriefWorkflowPackRun,
    AdvisorBriefWorkflowPackTaskFlow,
)
from app.services.advisor_brief_client_protocols import (
    AdvisorBriefAdviseClient,
    AdvisorBriefAiClient,
)
from app.services.advisor_brief_supportability import (
    load_advisory_supportability,
    load_ai_surface_supportability,
)
from app.services.advisor_brief_workflow_pack import (
    load_advisor_brief_workflow_pack_run,
    load_advisor_brief_workflow_pack_task_flow,
)


@dataclass(frozen=True)
class AdvisorBriefRuntimeContext:
    workflow_pack_run: AdvisorBriefWorkflowPackRun | None
    workflow_pack_task_flow: AdvisorBriefWorkflowPackTaskFlow | None
    ai_surface_supportability: AdvisorBriefAiSurfaceSupportability | None
    advisory_supportability: AdvisorBriefAdvisorySupportability | None


async def load_advisor_brief_runtime_context(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    advise_client: AdvisorBriefAdviseClient | None,
    correlation_id: str,
    ai_audit: dict[str, Any],
) -> AdvisorBriefRuntimeContext:
    workflow_pack_run = await load_advisor_brief_workflow_pack_run(
        lotus_ai_client=lotus_ai_client,
        ai_audit=ai_audit,
        correlation_id=correlation_id,
    )
    workflow_pack_task_flow = await load_advisor_brief_workflow_pack_task_flow(
        lotus_ai_client=lotus_ai_client,
        ai_audit=ai_audit,
        correlation_id=correlation_id,
    )
    ai_surface_supportability = await load_ai_surface_supportability(
        lotus_ai_client=lotus_ai_client,
        correlation_id=correlation_id,
    )
    advisory_supportability = await load_advisory_supportability(
        advise_client=advise_client,
        correlation_id=correlation_id,
    )
    return AdvisorBriefRuntimeContext(
        workflow_pack_run=workflow_pack_run,
        workflow_pack_task_flow=workflow_pack_task_flow,
        ai_surface_supportability=ai_surface_supportability,
        advisory_supportability=advisory_supportability,
    )
