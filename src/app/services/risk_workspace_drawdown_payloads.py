from collections.abc import Iterator
from typing import Any

from app.contracts.risk_workspace_drawdown import (
    WorkbenchRiskDrawdownEpisode,
    WorkbenchRiskDrawdownPeriodResult,
    WorkbenchRiskDrawdownSummary,
    WorkbenchRiskRelativeDrawdownContext,
    WorkbenchRiskRelativeDrawdownSummary,
    WorkbenchRiskUnderwaterPoint,
)


def iter_drawdown_result_items(results: Any) -> Iterator[tuple[Any, dict[str, Any]]]:
    if not isinstance(results, dict):
        return
    for key, value in results.items():
        if isinstance(value, dict):
            yield key, value


def map_drawdown_period_result(
    *,
    key: Any,
    value: dict[str, Any],
) -> WorkbenchRiskDrawdownPeriodResult:
    summary_payload = value.get("summary")
    episodes_payload = value.get("episodes")
    relative_payload = value.get("relative_to_benchmark")
    underwater_payload = value.get("underwater_series")
    error = value.get("error")

    return WorkbenchRiskDrawdownPeriodResult(
        key=str(key),
        label=str(key),
        start_date=str(value.get("start_date", "")),
        end_date=str(value.get("end_date", "")),
        portfolio_observation_count=int(value.get("portfolio_observation_count", 0)),
        benchmark_observation_count=int(value.get("benchmark_observation_count", 0)),
        summary=(
            map_drawdown_summary(summary_payload) if isinstance(summary_payload, dict) else None
        ),
        episodes=(
            map_drawdown_episodes(episodes_payload) if isinstance(episodes_payload, list) else []
        ),
        relative_to_benchmark=(
            WorkbenchRiskRelativeDrawdownSummary.model_validate(relative_payload)
            if isinstance(relative_payload, dict)
            else None
        ),
        relative_to_benchmark_context=(
            WorkbenchRiskRelativeDrawdownContext.model_validate(
                value.get("relative_to_benchmark_context")
            )
            if isinstance(value.get("relative_to_benchmark_context"), dict)
            else None
        ),
        underwater_series=(
            map_underwater_series(underwater_payload)
            if isinstance(underwater_payload, list)
            else None
        ),
        error=str(error) if isinstance(error, str) and error.strip() else None,
    )


def map_drawdown_summary(summary_payload: dict[str, Any]) -> WorkbenchRiskDrawdownSummary:
    return WorkbenchRiskDrawdownSummary.model_validate(summary_payload)


def map_drawdown_episodes(episodes_payload: list[Any]) -> list[WorkbenchRiskDrawdownEpisode]:
    episodes: list[WorkbenchRiskDrawdownEpisode] = []
    for payload in episodes_payload:
        if not isinstance(payload, dict):
            continue
        episodes.append(WorkbenchRiskDrawdownEpisode.model_validate(payload))
    episodes.sort(key=lambda episode: episode.depth)
    return episodes


def map_underwater_series(series_payload: list[Any]) -> list[WorkbenchRiskUnderwaterPoint]:
    points: list[WorkbenchRiskUnderwaterPoint] = []
    for payload in series_payload:
        if not isinstance(payload, dict):
            continue
        points.append(WorkbenchRiskUnderwaterPoint.model_validate(payload))
    return points
