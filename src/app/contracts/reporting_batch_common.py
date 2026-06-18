from typing import Literal

BatchStatus = Literal[
    "materialized",
    "running",
    "paused",
    "cancelled",
    "completed",
    "completed_with_failures",
    "failed",
]
BatchItemStatus = Literal[
    "materialized",
    "leased",
    "waiting_on_report_job",
    "succeeded",
    "failed_retryable",
    "failed_terminal",
    "cancelled",
    "recovery_pending",
]

__all__ = ["BatchItemStatus", "BatchStatus"]
