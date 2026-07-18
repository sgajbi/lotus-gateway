from app.services import advisor_book_service_provider
from app.services.advisor_book_service import AdvisorBookService


def test_advisor_book_service_provider_caches_by_upstream_signature(monkeypatch) -> None:
    signatures = iter([("core-a",), ("core-a",), ("core-b",)])
    built = [object(), object()]
    build_calls: list[int] = []

    monkeypatch.setattr(
        advisor_book_service_provider,
        "advisor_book_service_signature",
        lambda: next(signatures),
    )

    def _build():
        build_calls.append(1)
        return built[len(build_calls) - 1]

    monkeypatch.setattr(advisor_book_service_provider, "build_advisor_book_service", _build)
    monkeypatch.setattr(advisor_book_service_provider, "_ADVISOR_BOOK_SERVICE", None)
    monkeypatch.setattr(advisor_book_service_provider, "_ADVISOR_BOOK_SERVICE_SIGNATURE", None)

    first = advisor_book_service_provider.advisor_book_service()
    second = advisor_book_service_provider.advisor_book_service()
    third = advisor_book_service_provider.advisor_book_service()

    assert first is second is built[0]
    assert third is built[1]
    assert len(build_calls) == 2


def test_advisor_book_factory_builds_typed_service(monkeypatch) -> None:
    from app.services import advisor_book_service_factory

    client = object()
    monkeypatch.setattr(
        advisor_book_service_factory, "build_lotus_core_query_client", lambda: client
    )

    service = advisor_book_service_factory.build_advisor_book_service()

    assert isinstance(service, AdvisorBookService)
    assert service._membership_client is client
