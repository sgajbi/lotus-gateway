from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _normalized(document: str) -> str:
    return " ".join(document.split())


def test_report_ordering_route_and_authority_are_documented_consistently() -> None:
    documents = [
        _read("README.md"),
        _read("REPOSITORY-ENGINEERING-CONTEXT.md"),
        _read("docs/supported-features.md"),
        _read("docs/standards/RFC-0082-upstream-contract-family-map.md"),
        _read("wiki/API-Surface.md"),
        _read("wiki/Supported-Features.md"),
    ]

    for document in documents:
        assert "/api/v1/report-ordering/options" in document
        assert "lotus-report" in document


def test_report_ordering_wiki_keeps_business_boundaries_explicit() -> None:
    supported_features = _normalized(_read("wiki/Supported-Features.md"))
    api_surface = _normalized(_read("wiki/API-Surface.md"))

    assert "does not expand portfolio membership" in api_surface
    assert "does not authorize client distribution" in supported_features
    assert "whole-book portfolio expansion" in supported_features
    assert "known Report ordering-validation codes" in supported_features
