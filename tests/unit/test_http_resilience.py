import json

import httpx
import pytest

from app.clients.http_resilience import request_binary_with_retry, request_with_retry


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
async def test_request_with_retry_handles_negative_retry_configuration():
    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=-1,
        backoff_seconds=0.0,
    )

    assert status == 503
    assert payload == {"detail": "upstream communication failure: exhausted retries"}


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
