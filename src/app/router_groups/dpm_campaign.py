from app.router_groups.dpm_types import RouterGroup
from app.routers.dpm_wave_campaign_approval_commands import (
    router as dpm_wave_campaign_approval_commands_router,
)
from app.routers.dpm_wave_campaign_approval_inbox import (
    router as dpm_wave_campaign_approval_inbox_router,
)
from app.routers.dpm_wave_campaign_approvals import (
    router as dpm_wave_campaign_approvals_router,
)
from app.routers.dpm_wave_campaign_assignment_action_commands import (
    router as dpm_wave_campaign_assignment_action_commands_router,
)
from app.routers.dpm_wave_campaign_assignment_task_actions import (
    router as dpm_wave_campaign_assignment_task_actions_router,
)
from app.routers.dpm_wave_campaign_assignment_task_transitions import (
    router as dpm_wave_campaign_assignment_task_transitions_router,
)
from app.routers.dpm_wave_campaign_assignment_tasks import (
    router as dpm_wave_campaign_assignment_tasks_router,
)
from app.routers.dpm_wave_campaign_assignment_views import (
    router as dpm_wave_campaign_assignment_views_router,
)
from app.routers.dpm_wave_campaign_assignments import (
    router as dpm_wave_campaign_assignments_router,
)
from app.routers.dpm_wave_campaign_definition_detail import (
    router as dpm_wave_campaign_definition_detail_router,
)
from app.routers.dpm_wave_campaign_definition_lookup import (
    router as dpm_wave_campaign_definition_lookup_router,
)
from app.routers.dpm_wave_campaign_definitions import (
    router as dpm_wave_campaign_definitions_router,
)
from app.routers.dpm_wave_campaign_discovery import (
    router as dpm_wave_campaign_discovery_router,
)
from app.routers.dpm_wave_campaign_maker_checker_commands import (
    router as dpm_wave_campaign_maker_checker_commands_router,
)
from app.routers.dpm_wave_campaign_operating_queue import (
    router as dpm_wave_campaign_operating_queue_router,
)
from app.routers.dpm_wave_campaign_workflow import (
    router as dpm_wave_campaign_workflow_router,
)
from app.routers.dpm_wave_campaign_workflow_automation import (
    router as dpm_wave_campaign_workflow_automation_router,
)
from app.routers.dpm_wave_campaign_workflow_boards import (
    router as dpm_wave_campaign_workflow_boards_router,
)

DPM_CAMPAIGN_ROUTERS: RouterGroup = (
    dpm_wave_campaign_definitions_router,
    dpm_wave_campaign_definition_lookup_router,
    dpm_wave_campaign_definition_detail_router,
    dpm_wave_campaign_discovery_router,
    dpm_wave_campaign_workflow_boards_router,
    dpm_wave_campaign_operating_queue_router,
    dpm_wave_campaign_assignment_views_router,
    dpm_wave_campaign_workflow_automation_router,
    dpm_wave_campaign_approval_inbox_router,
    dpm_wave_campaign_approvals_router,
    dpm_wave_campaign_assignment_action_commands_router,
    dpm_wave_campaign_approval_commands_router,
    dpm_wave_campaign_assignments_router,
    dpm_wave_campaign_assignment_tasks_router,
    dpm_wave_campaign_assignment_task_actions_router,
    dpm_wave_campaign_assignment_task_transitions_router,
    dpm_wave_campaign_workflow_router,
    dpm_wave_campaign_maker_checker_commands_router,
)
