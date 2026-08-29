from typing import TypeAlias

from pydantic import BaseModel, ConfigDict

MemoReasonValue: TypeAlias = str | bool | int | None
MemoReason: TypeAlias = dict[str, MemoReasonValue]


class ClosedProposalMemoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


__all__ = ["ClosedProposalMemoModel", "MemoReason"]
