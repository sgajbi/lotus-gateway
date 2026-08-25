from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_risk_mandate_docs_preserve_source_authority_and_fail_closed_behavior() -> None:
    documents = [
        _read("docs/supported-features.md"),
        _read("wiki/API-Surface.md"),
        _read("wiki/Integrations.md"),
        _read("wiki/Supported-Features.md"),
        _read("REPOSITORY-ENGINEERING-CONTEXT.md"),
    ]

    for content in documents:
        normalized = " ".join(content.lower().split())
        assert "mandate" in normalized
        assert "lotus-manage#639" in normalized

    supported = " ".join(documents[0].lower().split())
    wiki = " ".join(documents[3].lower().split())
    context = " ".join(documents[4].lower().split())
    assert "never an inferred all-clear" in supported
    assert "does not calculate mandate health or invent limits" in wiki
    assert "must not calculate mandate health" in context


def test_risk_mandate_docs_name_current_historical_limit_without_claiming_completion() -> None:
    api_surface = " ".join(_read("wiki/API-Surface.md").lower().split())
    supported = " ".join(_read("wiki/Supported-Features.md").lower().split())

    for content in (api_surface, supported):
        assert "historical" in content
        assert "mismatch" in content
        assert "lotus-manage#639" in content
