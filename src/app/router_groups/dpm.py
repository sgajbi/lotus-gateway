from app.router_groups.dpm_campaign import DPM_CAMPAIGN_ROUTERS
from app.router_groups.dpm_command_center import DPM_COMMAND_CENTER_ROUTERS
from app.router_groups.dpm_proof_construction import DPM_PROOF_AND_CONSTRUCTION_ROUTERS
from app.router_groups.dpm_types import RouterGroup
from app.router_groups.dpm_wave import DPM_WAVE_ROUTERS

__all__ = [
    "DPM_CAMPAIGN_ROUTERS",
    "DPM_COMMAND_CENTER_ROUTERS",
    "DPM_PROOF_AND_CONSTRUCTION_ROUTERS",
    "DPM_WAVE_ROUTERS",
    "RouterGroup",
]
