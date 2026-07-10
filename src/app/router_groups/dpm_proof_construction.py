from app.router_groups.dpm_types import RouterGroup
from app.routers.dpm_construction import router as dpm_construction_router
from app.routers.dpm_construction_actions import router as dpm_construction_actions_router
from app.routers.dpm_construction_selection import router as dpm_construction_selection_router
from app.routers.dpm_proof_pack_ai import router as dpm_proof_pack_ai_router
from app.routers.dpm_proof_pack_ai_evidence_input import (
    router as dpm_proof_pack_ai_evidence_input_router,
)
from app.routers.dpm_proof_pack_detail import router as dpm_proof_pack_detail_router
from app.routers.dpm_proof_pack_evidence import router as dpm_proof_pack_evidence_router
from app.routers.dpm_proof_pack_report_input import (
    router as dpm_proof_pack_report_input_router,
)
from app.routers.dpm_proof_packs import router as dpm_proof_packs_router

DPM_PROOF_AND_CONSTRUCTION_ROUTERS: RouterGroup = (
    dpm_construction_router,
    dpm_construction_actions_router,
    dpm_construction_selection_router,
    dpm_proof_packs_router,
    dpm_proof_pack_detail_router,
    dpm_proof_pack_evidence_router,
    dpm_proof_pack_report_input_router,
    dpm_proof_pack_ai_evidence_input_router,
    dpm_proof_pack_ai_router,
)
