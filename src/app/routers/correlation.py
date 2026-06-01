from app.middleware.correlation import correlation_id_var


def resolve_router_correlation_id(header_value: str | None) -> str:
    return header_value or correlation_id_var.get() or ""
