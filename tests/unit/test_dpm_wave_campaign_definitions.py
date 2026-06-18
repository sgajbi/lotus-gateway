from app.services.dpm_wave_campaign_definitions import DpmWaveCampaignDefinitionMixin
from app.services.dpm_wave_service import DpmWaveService


def test_dpm_wave_service_uses_campaign_definition_mixin() -> None:
    assert issubclass(DpmWaveService, DpmWaveCampaignDefinitionMixin)
