from app.clients.dpm_wave_campaign_definition_client import DpmWaveCampaignDefinitionClientMixin
from app.clients.dpm_wave_campaign_workflow_client import DpmWaveCampaignWorkflowClientMixin
from app.clients.dpm_wave_core_client import DpmWaveCoreClientMixin


class DpmWaveClientMixin(
    DpmWaveCoreClientMixin,
    DpmWaveCampaignDefinitionClientMixin,
    DpmWaveCampaignWorkflowClientMixin,
):
    """Compatibility facade for Manage rebalance-wave route-family client mixins."""
