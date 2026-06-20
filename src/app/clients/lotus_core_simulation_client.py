from typing import Any


class LotusCoreSimulationClientMixin:
    async def _get_control_plane_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _post_control_plane_resource(
        self,
        *,
        operation: str,
        path: str,
        correlation_id: str,
        payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def create_simulation_session(
        self,
        portfolio_id: str,
        created_by: str | None,
        ttl_hours: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {
            "portfolio_id": portfolio_id,
            "created_by": created_by,
            "ttl_hours": ttl_hours,
        }
        return await self._post_control_plane_resource(
            operation="core.simulation-sessions.create",
            path="/simulation-sessions",
            correlation_id=correlation_id,
            payload=payload,
        )

    async def add_simulation_changes(
        self,
        session_id: str,
        changes: list[dict[str, Any]],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        payload = {"changes": changes}
        return await self._post_control_plane_resource(
            operation="core.simulation-sessions.changes.add",
            path=f"/simulation-sessions/{session_id}/changes",
            correlation_id=correlation_id,
            payload=payload,
        )

    async def get_projected_positions(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_control_plane_resource(
            operation="core.simulation-sessions.projected-positions.get",
            path=f"/simulation-sessions/{session_id}/projected-positions",
            correlation_id=correlation_id,
        )

    async def get_projected_summary(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_control_plane_resource(
            operation="core.simulation-sessions.projected-summary.get",
            path=f"/simulation-sessions/{session_id}/projected-summary",
            correlation_id=correlation_id,
        )
