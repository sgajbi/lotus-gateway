from app.router_groups.dpm_types import RouterGroup
from app.routers.dpm_wave_actions import router as dpm_wave_actions_router
from app.routers.dpm_wave_ai import router as dpm_wave_ai_router
from app.routers.dpm_wave_campaign_launch import (
    router as dpm_wave_campaign_launch_router,
)
from app.routers.dpm_wave_campaign_launch_actions import (
    router as dpm_wave_campaign_launch_actions_router,
)
from app.routers.dpm_wave_campaign_launch_package import (
    router as dpm_wave_campaign_launch_package_router,
)
from app.routers.dpm_wave_campaign_lifecycle import (
    router as dpm_wave_campaign_lifecycle_router,
)
from app.routers.dpm_wave_campaign_preview_readiness import (
    router as dpm_wave_campaign_preview_readiness_router,
)
from app.routers.dpm_wave_campaign_readiness import (
    router as dpm_wave_campaign_readiness_router,
)
from app.routers.dpm_wave_campaign_supersede import (
    router as dpm_wave_campaign_supersede_router,
)
from app.routers.dpm_wave_cancellation import router as dpm_wave_cancellation_router
from app.routers.dpm_wave_detail import router as dpm_wave_detail_router
from app.routers.dpm_wave_evidence import router as dpm_wave_evidence_router
from app.routers.dpm_wave_handoff import router as dpm_wave_handoff_router
from app.routers.dpm_wave_item_selection import router as dpm_wave_item_selection_router
from app.routers.dpm_wave_items import router as dpm_wave_items_router
from app.routers.dpm_wave_lifecycle_actions import router as dpm_wave_lifecycle_actions_router
from app.routers.dpm_wave_lookup import router as dpm_wave_lookup_router
from app.routers.dpm_wave_operations_handoff_ai import (
    router as dpm_wave_operations_handoff_ai_router,
)
from app.routers.dpm_wave_preview import router as dpm_wave_preview_router
from app.routers.dpm_wave_report_input import router as dpm_wave_report_input_router
from app.routers.dpm_wave_simulation import router as dpm_wave_simulation_router
from app.routers.dpm_wave_supportability import router as dpm_wave_supportability_router
from app.routers.dpm_wave_workflow_actions import router as dpm_wave_workflow_actions_router
from app.routers.dpm_waves import router as dpm_waves_router

DPM_WAVE_ROUTERS: RouterGroup = (
    dpm_wave_preview_router,
    dpm_waves_router,
    dpm_wave_lookup_router,
    dpm_wave_detail_router,
    dpm_wave_items_router,
    dpm_wave_item_selection_router,
    dpm_wave_actions_router,
    dpm_wave_simulation_router,
    dpm_wave_lifecycle_actions_router,
    dpm_wave_cancellation_router,
    dpm_wave_workflow_actions_router,
    dpm_wave_handoff_router,
    dpm_wave_evidence_router,
    dpm_wave_report_input_router,
    dpm_wave_supportability_router,
    dpm_wave_ai_router,
    dpm_wave_operations_handoff_ai_router,
    dpm_wave_campaign_launch_router,
    dpm_wave_campaign_launch_package_router,
    dpm_wave_campaign_launch_actions_router,
    dpm_wave_campaign_lifecycle_router,
    dpm_wave_campaign_supersede_router,
    dpm_wave_campaign_preview_readiness_router,
    dpm_wave_campaign_readiness_router,
)
