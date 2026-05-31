from fastapi import Path

PROPOSAL_ID_PATH = Path(
    ...,
    description="Gateway-visible proposal identifier returned by lotus-advise.",
    examples=["pp_1"],
)
VERSION_NO_PATH = Path(
    ...,
    description="Immutable proposal version number used as the memo source.",
    examples=[2],
)
