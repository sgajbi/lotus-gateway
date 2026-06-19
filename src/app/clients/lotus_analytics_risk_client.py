from typing import Any


class LotusAnalyticsRiskClientMixin:
    async def _post_analytics_request(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        correlation_id: str,
        service: str = "lotus-performance",
        operation: str | None = None,
        async_poll_attempts: int = 10,
        async_poll_interval_seconds: float = 0.35,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def post_risk_calculate(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/calculate",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.calculate",
        )

    async def post_risk_concentration(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/concentration",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.concentration",
        )

    async def post_risk_drawdown(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/drawdown",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.drawdown",
        )

    async def post_risk_rolling_metrics(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/rolling-metrics",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.rolling-metrics",
        )

    async def post_risk_historical_attribution(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post_analytics_request(
            path="/analytics/risk/historical-attribution",
            payload=payload,
            correlation_id=correlation_id,
            service="lotus-risk",
            operation="analytics.risk.historical-attribution",
        )
