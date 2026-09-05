import ast
import json
from pathlib import Path

import httpx
import pytest

from app.clients.http_json_resilience import (
    RequestFailureKind,
    request_with_retry_outcome,
)
from app.clients.http_resilience import request_binary_with_retry, request_with_retry
from app.clients.http_response_payloads import (
    binary_communication_failure_result,
    communication_failure_result,
    response_payload,
    unsupported_method_payload,
)
from app.clients.http_retry_policy import (
    is_ambiguous_response_loss_error,
    is_retryable_request_error,
    retry_attempts,
    retry_delay,
    should_retry_request_error,
    should_retry_status,
)
from app.services.upstream_envelope import safe_upstream_detail


def test_http_resilience_delegates_retry_policy() -> None:
    resilience_path = Path(__file__).parents[2] / "src" / "app" / "clients" / "http_resilience.py"
    tree = ast.parse(resilience_path.read_text(encoding="utf-8"), filename=str(resilience_path))
    resilience_functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }

    assert retry_attempts(-1) == 1
    assert retry_delay(-1.0, attempt=2) == 0.0
    assert should_retry_status(
        response_status_code=503,
        retry_status_codes={503},
        attempt=0,
        max_retries=1,
    )
    assert is_retryable_request_error(httpx.NetworkError("disconnected")) is True
    assert is_retryable_request_error(httpx.RemoteProtocolError("disconnected")) is True
    assert is_retryable_request_error(httpx.TooManyRedirects("loop")) is False
    assert "_retry_attempts" not in resilience_functions
    assert "_retry_delay" not in resilience_functions
    assert "_should_retry_status" not in resilience_functions


def test_ambiguous_response_loss_classification_separates_pre_send_failures() -> None:
    # The request may already have reached the producer.
    assert is_ambiguous_response_loss_error(httpx.ReadError("response lost")) is True
    assert is_ambiguous_response_loss_error(httpx.WriteError("send interrupted")) is True
    assert is_ambiguous_response_loss_error(httpx.NetworkError("disconnected")) is True
    assert is_ambiguous_response_loss_error(httpx.RemoteProtocolError("no response")) is True
    # The request never left the caller.
    assert is_ambiguous_response_loss_error(httpx.ConnectError("refused")) is False


def test_should_retry_request_error_can_stop_ambiguous_replays() -> None:
    common = {"retry_timeout_exceptions": False, "attempt": 0, "max_retries": 2}

    assert (
        should_retry_request_error(
            exc=httpx.ReadError("response lost"),
            retry_ambiguous_request_errors=False,
            **common,
        )
        is False
    )
    assert (
        should_retry_request_error(
            exc=httpx.ConnectError("refused"),
            retry_ambiguous_request_errors=False,
            **common,
        )
        is True
    )
    assert (
        should_retry_request_error(
            exc=httpx.ReadError("response lost"),
            retry_ambiguous_request_errors=True,
            **common,
        )
        is True
    )


def test_http_response_payload_helpers_normalize_upstream_errors() -> None:
    json_response = httpx.Response(
        503,
        json={"detail": "try-again"},
        request=httpx.Request("GET", "http://test"),
    )
    list_response = httpx.Response(
        502,
        json=["not", "a", "dict"],
        request=httpx.Request("GET", "http://test"),
    )
    text_response = httpx.Response(
        500,
        text="plain-text-error",
        request=httpx.Request("GET", "http://test"),
    )

    assert response_payload(json_response) == {"detail": "try-again"}
    assert response_payload(list_response) == {"detail": ["not", "a", "dict"]}
    assert response_payload(text_response) == {"detail": "plain-text-error"}
    assert unsupported_method_payload("") == {"detail": "unsupported upstream HTTP method: <blank>"}
    assert communication_failure_result("NetworkError") == (
        503,
        {"detail": "upstream communication failure: NetworkError"},
    )
    assert binary_communication_failure_result("TimeoutException") == (
        503,
        b"",
        {},
        {"detail": "upstream communication failure: TimeoutException"},
    )


class _FlakyAsyncClient:
    calls = 0
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _FlakyAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = url, params, headers
        _FlakyAsyncClient.calls += 1
        if _FlakyAsyncClient.calls == 1:
            raise httpx.TimeoutException("timed out")
        return httpx.Response(
            200,
            content=json.dumps({"ok": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            request=httpx.Request("GET", "http://test"),
        )

    async def post(self, url, params=None, headers=None, json=None, data=None, files=None):
        _ = url, params, headers, json, data, files
        _FlakyAsyncClient.calls += 1
        if _FlakyAsyncClient.calls == 1:
            raise httpx.TimeoutException("timed out")
        return httpx.Response(
            200,
            content=json.dumps({"ok": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            request=httpx.Request("POST", "http://test"),
        )


class _RetryStatusAsyncClient:
    calls = 0
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _RetryStatusAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = url, params, headers
        _RetryStatusAsyncClient.calls += 1
        if _RetryStatusAsyncClient.calls == 1:
            return httpx.Response(
                503, json={"detail": "try-again"}, request=httpx.Request("GET", "http://test")
            )
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", "http://test"))


class _NetworkErrorAsyncClient:
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _NetworkErrorAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = url, params, headers
        raise httpx.NetworkError("disconnected")


class _RetryableNetworkErrorThenSuccessAsyncClient:
    calls = 0
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _RetryableNetworkErrorThenSuccessAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, exc, _tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = params, headers
        _RetryableNetworkErrorThenSuccessAsyncClient.calls += 1
        if _RetryableNetworkErrorThenSuccessAsyncClient.calls == 1:
            raise httpx.NetworkError("disconnected")
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", url))


class _RaisedRequestErrorAsyncClient:
    calls = 0
    exception_type = httpx.RequestError
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _RaisedRequestErrorAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, exc, _tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = url, params, headers
        _RaisedRequestErrorAsyncClient.calls += 1
        raise _RaisedRequestErrorAsyncClient.exception_type("permanent request failure")


class _ProtocolErrorAsyncClient:
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _ProtocolErrorAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, params=None, headers=None, json=None, data=None, files=None):
        _ = url, params, headers, json, data, files
        raise httpx.RemoteProtocolError("Server disconnected without sending a response.")


class _TextPayloadAsyncClient:
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _TextPayloadAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, params=None, headers=None, json=None, data=None, files=None):
        _ = url, params, headers, json, data, files
        return httpx.Response(
            500,
            text="plain-text-error",
            request=httpx.Request("POST", "http://test"),
        )


class _PostParamsAsyncClient:
    calls: list[dict] = []
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _PostParamsAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, params=None, headers=None, json=None, data=None, files=None):
        _ = headers, data, files
        _PostParamsAsyncClient.calls.append({"url": url, "params": params, "json": json})
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("POST", url))


class _BinaryRetryStatusAsyncClient:
    calls = 0
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _BinaryRetryStatusAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = params, headers
        _BinaryRetryStatusAsyncClient.calls += 1
        if _BinaryRetryStatusAsyncClient.calls == 1:
            return httpx.Response(503, text="try again", request=httpx.Request("GET", url))
        return httpx.Response(
            200,
            content=b"binary-content",
            headers={"Content-Type": "application/pdf"},
            request=httpx.Request("GET", url),
        )


class _BinaryTextErrorAsyncClient:
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _BinaryTextErrorAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = params, headers
        return httpx.Response(502, text="archive unavailable", request=httpx.Request("GET", url))


class _BinarySuccessAsyncClient:
    calls = 0
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _BinarySuccessAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = params, headers
        _BinarySuccessAsyncClient.calls += 1
        return httpx.Response(
            200,
            content=b"binary-content",
            headers={"Content-Type": "application/pdf"},
            request=httpx.Request("GET", url),
        )


class _BinaryNetworkErrorAsyncClient:
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _BinaryNetworkErrorAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = url, params, headers
        raise httpx.NetworkError("binary disconnected")


class _UnexpectedAsyncClient:
    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout, follow_redirects
        raise AssertionError("AsyncClient should not be opened for unsupported methods")


@pytest.mark.asyncio
async def test_request_with_retry_retries_on_timeout(monkeypatch):
    _FlakyAsyncClient.calls = 0
    monkeypatch.setattr("httpx.AsyncClient", _FlakyAsyncClient)

    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=2,
        backoff_seconds=0.0,
    )

    assert status == 200
    assert payload == {"ok": True}
    assert _FlakyAsyncClient.calls == 2
    assert _FlakyAsyncClient.follow_redirects is True


@pytest.mark.asyncio
async def test_request_with_retry_can_disable_timeout_retries(monkeypatch):
    _FlakyAsyncClient.calls = 0
    monkeypatch.setattr("httpx.AsyncClient", _FlakyAsyncClient)

    status, payload = await request_with_retry(
        method="POST",
        url="http://service/workspace-summary",
        timeout_seconds=1.0,
        max_retries=2,
        backoff_seconds=0.0,
        json_body={"calculation_id": "calc-1"},
        retry_timeout_exceptions=False,
    )

    assert status == 503
    assert payload == {"detail": "upstream communication failure: TimeoutException"}
    assert _FlakyAsyncClient.calls == 1


@pytest.mark.asyncio
async def test_request_with_retry_retries_on_status_code(monkeypatch):
    _RetryStatusAsyncClient.calls = 0
    monkeypatch.setattr("httpx.AsyncClient", _RetryStatusAsyncClient)

    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=2,
        backoff_seconds=0.0,
        retry_status_codes={503},
    )

    assert status == 200
    assert payload == {"ok": True}
    assert _RetryStatusAsyncClient.calls == 2


@pytest.mark.asyncio
async def test_request_with_retry_returns_503_after_network_error(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _NetworkErrorAsyncClient)

    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
    )

    assert status == 503
    assert payload["detail"] == "upstream communication failure: NetworkError"


@pytest.mark.asyncio
async def test_request_outcome_classifies_transport_failure_without_parsing_payload(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _NetworkErrorAsyncClient)

    outcome = await request_with_retry_outcome(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
    )

    assert outcome.status_code == 503
    assert outcome.failure_kind == RequestFailureKind.TRANSPORT
    assert outcome.is_transient_transport_failure is True


@pytest.mark.asyncio
async def test_request_outcome_retries_allowlisted_network_error(monkeypatch):
    _RetryableNetworkErrorThenSuccessAsyncClient.calls = 0
    monkeypatch.setattr("httpx.AsyncClient", _RetryableNetworkErrorThenSuccessAsyncClient)

    outcome = await request_with_retry_outcome(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=1,
        backoff_seconds=0.0,
    )

    assert outcome.status_code == 200
    assert outcome.payload == {"ok": True}
    assert _RetryableNetworkErrorThenSuccessAsyncClient.calls == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception_type",
    [
        httpx.TooManyRedirects,
        httpx.UnsupportedProtocol,
        httpx.LocalProtocolError,
        httpx.RequestError,
    ],
)
async def test_request_outcome_stops_for_terminal_request_errors(
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[httpx.RequestError],
) -> None:
    _RaisedRequestErrorAsyncClient.calls = 0
    _RaisedRequestErrorAsyncClient.exception_type = exception_type
    monkeypatch.setattr("httpx.AsyncClient", _RaisedRequestErrorAsyncClient)

    outcome = await request_with_retry_outcome(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=2,
        backoff_seconds=0.0,
    )

    assert outcome.status_code == 503
    assert outcome.failure_kind == RequestFailureKind.TERMINAL_REQUEST_ERROR
    assert outcome.is_transient_transport_failure is False
    assert _RaisedRequestErrorAsyncClient.calls == 1


@pytest.mark.asyncio
async def test_request_outcome_keeps_source_503_distinct_from_transport_failure(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _RetryStatusAsyncClient)
    _RetryStatusAsyncClient.calls = 0

    outcome = await request_with_retry_outcome(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
    )

    assert outcome.status_code == 503
    assert outcome.failure_kind is None
    assert outcome.is_transient_transport_failure is False


@pytest.mark.asyncio
async def test_request_with_retry_returns_503_after_protocol_disconnect(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _ProtocolErrorAsyncClient)

    status, payload = await request_with_retry(
        method="POST",
        url="http://service/workflow-packs/execute",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
        json_body={"pack_id": "dpm_pm_memo.pack"},
    )

    assert status == 503
    assert payload["detail"] == "upstream communication failure: RemoteProtocolError"


@pytest.mark.asyncio
async def test_request_with_retry_wraps_non_json_payload(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _TextPayloadAsyncClient)

    status, payload = await request_with_retry(
        method="POST",
        url="http://service/workbench",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
        json_body={"x": 1},
    )

    assert status == 500
    assert payload == {"detail": "plain-text-error"}
    assert (
        safe_upstream_detail(payload, default_detail="upstream request failed")
        == "upstream request failed"
    )


@pytest.mark.asyncio
async def test_request_with_retry_forwards_post_query_params(monkeypatch):
    _PostParamsAsyncClient.calls = []
    monkeypatch.setattr("httpx.AsyncClient", _PostParamsAsyncClient)

    status, payload = await request_with_retry(
        method="POST",
        url="http://service/advisory/cockpit/actions/action-1/acknowledgements",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
        json_body={"action_item_version": 1},
    )

    assert status == 200
    assert payload == {"ok": True}
    assert _PostParamsAsyncClient.calls == [
        {
            "url": "http://service/advisory/cockpit/actions/action-1/acknowledgements",
            "params": {"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
            "json": {"action_item_version": 1},
        }
    ]


@pytest.mark.asyncio
async def test_request_with_retry_clamps_negative_retry_configuration(monkeypatch):
    _RedirectAwareAsyncClient.requested_urls = []
    monkeypatch.setattr("httpx.AsyncClient", _RedirectAwareAsyncClient)

    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=-1,
        backoff_seconds=-1.0,
    )

    assert status == 200
    assert payload == {"redirected": True}
    assert _RedirectAwareAsyncClient.requested_urls == ["http://service/health"]


@pytest.mark.asyncio
async def test_request_with_retry_rejects_unsupported_method(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _UnexpectedAsyncClient)

    status, payload = await request_with_retry(
        method="PATCH",
        url="http://service/health",
        timeout_seconds=1.0,
    )

    assert status == 503
    assert payload == {"detail": "unsupported upstream HTTP method: PATCH"}


class _RedirectAwareAsyncClient:
    requested_urls: list[str] = []
    follow_redirects = None

    def __init__(self, timeout: float, follow_redirects: bool = False):
        _ = timeout
        _RedirectAwareAsyncClient.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = params, headers
        _RedirectAwareAsyncClient.requested_urls.append(url)
        return httpx.Response(200, json={"redirected": True}, request=httpx.Request("GET", url))


@pytest.mark.asyncio
async def test_request_with_retry_enables_redirect_following(monkeypatch):
    _RedirectAwareAsyncClient.requested_urls = []
    monkeypatch.setattr("httpx.AsyncClient", _RedirectAwareAsyncClient)

    status, payload = await request_with_retry(
        method="GET",
        url="http://service/portfolios",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
    )

    assert status == 200
    assert payload == {"redirected": True}
    assert _RedirectAwareAsyncClient.requested_urls == ["http://service/portfolios"]
    assert _RedirectAwareAsyncClient.follow_redirects is True


@pytest.mark.asyncio
async def test_request_binary_with_retry_retries_status_and_preserves_headers(monkeypatch):
    _BinaryRetryStatusAsyncClient.calls = 0
    monkeypatch.setattr("httpx.AsyncClient", _BinaryRetryStatusAsyncClient)

    status, content, headers, error_payload = await request_binary_with_retry(
        method="GET",
        url="http://archive/documents/doc_1/download",
        timeout_seconds=1.0,
        max_retries=2,
        backoff_seconds=0.0,
        retry_status_codes={503},
    )

    assert status == 200
    assert content == b"binary-content"
    assert headers["content-type"] == "application/pdf"
    assert error_payload == {}
    assert _BinaryRetryStatusAsyncClient.calls == 2
    assert _BinaryRetryStatusAsyncClient.follow_redirects is True


@pytest.mark.asyncio
async def test_request_binary_with_retry_returns_text_error_payload(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _BinaryTextErrorAsyncClient)

    status, content, headers, error_payload = await request_binary_with_retry(
        method="GET",
        url="http://archive/documents/doc_1/download",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
    )

    assert status == 502
    assert content == b"archive unavailable"
    assert headers["content-length"] == "19"
    assert error_payload == {"detail": "archive unavailable"}


@pytest.mark.asyncio
async def test_request_binary_with_retry_clamps_negative_retry_configuration(monkeypatch):
    _BinarySuccessAsyncClient.calls = 0
    monkeypatch.setattr("httpx.AsyncClient", _BinarySuccessAsyncClient)

    status, content, headers, error_payload = await request_binary_with_retry(
        method="GET",
        url="http://archive/documents/doc_1/download",
        timeout_seconds=1.0,
        max_retries=-1,
        backoff_seconds=-1.0,
    )

    assert status == 200
    assert content == b"binary-content"
    assert headers["content-type"] == "application/pdf"
    assert error_payload == {}
    assert _BinarySuccessAsyncClient.calls == 1


@pytest.mark.asyncio
async def test_request_binary_with_retry_rejects_unsupported_method(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _UnexpectedAsyncClient)

    status, content, headers, error_payload = await request_binary_with_retry(
        method="PUT",
        url="http://archive/documents/doc_1/download",
        timeout_seconds=1.0,
    )

    assert status == 503
    assert content == b""
    assert headers == {}
    assert error_payload == {"detail": "unsupported upstream HTTP method: PUT"}


@pytest.mark.asyncio
async def test_request_binary_with_retry_returns_structured_communication_failure(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _BinaryNetworkErrorAsyncClient)

    status, content, headers, error_payload = await request_binary_with_retry(
        method="GET",
        url="http://archive/documents/doc_1/download",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
    )

    assert status == 503
    assert content == b""
    assert headers == {}
    assert error_payload == {"detail": "upstream communication failure: NetworkError"}
