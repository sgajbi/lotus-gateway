from fastapi import Path

WORKSPACE_ID_PATH = Path(
    ...,
    description="Advisory workspace identifier returned by lotus-advise.",
    examples=["aws_001"],
)
