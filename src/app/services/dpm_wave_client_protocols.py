"""The single protocol the wave services depend on.

The operations live in `dpm_wave_client_protocol_parts`, grouped as the client
groups them. This module stays one class because the service-layer boundary
test requires it: the wave protocol is deliberately split from the shared
`dpm_client_protocols` aggregator, and that split is only meaningful while this
module names exactly one thing.
"""

from typing import Protocol

from app.services.dpm_wave_client_protocol_parts import (
    DpmWaveCampaignDefinitionClientProtocol,
    DpmWaveCampaignWorkflowClientProtocol,
    DpmWaveCoreClientProtocol,
)


class DpmWaveClient(
    DpmWaveCampaignDefinitionClientProtocol,
    DpmWaveCampaignWorkflowClientProtocol,
    DpmWaveCoreClientProtocol,
    Protocol,
):
    """Everything the wave services depend on, composed as the client is."""
