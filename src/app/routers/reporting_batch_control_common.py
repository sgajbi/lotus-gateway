from app.contracts.reporting import BatchControlResponse
from app.middleware.correlation import correlation_id_var
from app.services.reporting_service_provider import reporting_batch_control_service


async def control_report_batch(
    *,
    batch_id: str,
    action: str,
    caller_headers: dict[str, str],
) -> BatchControlResponse:
    return await reporting_batch_control_service().control_batch(
        batch_id=batch_id,
        action=action,
        caller_headers=caller_headers,
        correlation_id=correlation_id_var.get(),
    )
