from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app


def test_health_live_and_ready_endpoints():
    client = TestClient(app)
    assert client.get("/health/live").json() == {"status": "live"}
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_unhandled_exception_handler_returns_problem_json(monkeypatch):
    # The synthetic route and any schema generated from it belong to this test,
    # not to later contract checks against the shared production application.
    with monkeypatch.context() as local:
        local.setattr(app.router, "routes", list(app.router.routes))
        local.setattr(app, "openapi_schema", None)
        local.setattr(app.state, "is_draining", False, raising=False)

        @app.get("/_test/error")
        async def _test_error():
            raise RuntimeError("boom")

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/_test/error")

    assert not any(getattr(route, "path", None) == "/_test/error" for route in app.routes)
    assert "/_test/error" not in app.openapi()["paths"]
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["title"] == "Internal Server Error"
    assert body["status"] == 500
    assert body["error_code"] == "INTERNAL_ERROR"


def test_health_live_concurrency():
    client = TestClient(app)

    def _call_live() -> int:
        return client.get("/health/live").status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(lambda _: _call_live(), range(32)))

    assert all(status == 200 for status in statuses)


def test_health_ready_returns_503_when_draining():
    app.state.is_draining = True
    try:
        client = TestClient(app)
        response = client.get("/health/ready")
    finally:
        app.state.is_draining = False

    assert response.status_code == 503
    assert response.json() == {"status": "draining"}


def test_lifespan_marks_draining_on_shutdown():
    app.state.is_draining = True
    try:
        with TestClient(app) as client:
            response = client.get("/health/ready")
            assert response.status_code == 200
            assert response.json() == {"status": "ready"}
            assert app.state.is_draining is False

        assert app.state.is_draining is True
    finally:
        # The shared app outlives this test; later in-process consumers must not
        # inherit the drained flag this assertion deliberately produced.
        app.state.is_draining = False
