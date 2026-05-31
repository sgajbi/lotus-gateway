from starlette.datastructures import QueryParams

from app.routers.query_params import query_params_with_repeated_values


def test_query_params_with_repeated_values_preserves_scalar_and_repeated_keys() -> None:
    params = query_params_with_repeated_values(
        QueryParams(
            [
                ("campaign_id", "campaign-1"),
                ("state", "READY"),
                ("state", "BLOCKED"),
                ("source_system", "lotus-core"),
                ("source_system", "lotus-manage"),
            ]
        )
    )

    assert params == {
        "campaign_id": "campaign-1",
        "state": ["READY", "BLOCKED"],
        "source_system": ["lotus-core", "lotus-manage"],
    }


def test_query_params_with_repeated_values_handles_empty_query_params() -> None:
    assert query_params_with_repeated_values(QueryParams("")) == {}
