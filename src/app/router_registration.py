"""Reusable route-cloning mechanics for the central Gateway registry."""

from collections.abc import Callable
from typing import cast

from fastapi import APIRouter, FastAPI
from fastapi.params import Depends as DependsParameter
from fastapi.routing import APIRoute

_MUTATION_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def include_routers(
    app: FastAPI,
    *routers: APIRouter,
    mutation_dependencies: tuple[DependsParameter, ...] = (),
) -> None:
    """Clone concrete routes and apply dependencies only to mutations."""

    for router in routers:
        _include_router_routes(
            app,
            router,
            mutation_dependencies=mutation_dependencies,
        )


def _include_router_routes(
    app: FastAPI,
    router: APIRouter,
    *,
    mutation_dependencies: tuple[DependsParameter, ...],
) -> None:
    for route in router.routes:
        if not isinstance(route, APIRoute):
            raise TypeError(f"Unsupported router route type: {type(route).__name__}")
        dependencies = list(route.dependencies)
        if route.methods & _MUTATION_METHODS:
            dependencies.extend(mutation_dependencies)
        app.add_api_route(
            route.path,
            route.endpoint,
            response_model=route.response_model,
            status_code=route.status_code,
            tags=route.tags,
            dependencies=dependencies,
            summary=route.summary,
            description=route.description,
            response_description=route.response_description,
            responses=route.responses,
            deprecated=route.deprecated,
            methods=list(route.methods or []),
            operation_id=route.operation_id,
            response_model_include=route.response_model_include,
            response_model_exclude=route.response_model_exclude,
            response_model_by_alias=route.response_model_by_alias,
            response_model_exclude_unset=route.response_model_exclude_unset,
            response_model_exclude_defaults=route.response_model_exclude_defaults,
            response_model_exclude_none=route.response_model_exclude_none,
            include_in_schema=route.include_in_schema,
            response_class=route.response_class,
            name=route.name,
            openapi_extra=route.openapi_extra,
            generate_unique_id_function=cast(
                Callable[[APIRoute], str],
                route.generate_unique_id_function,
            ),
        )
