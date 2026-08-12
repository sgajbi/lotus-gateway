from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_report_batch_authority_boundary_is_documented_consistently() -> None:
    documents = [
        _read("README.md"),
        _read("REPOSITORY-ENGINEERING-CONTEXT.md"),
        _read("docs/standards/RFC-0082-upstream-contract-family-map.md"),
        _read("wiki/API-Surface.md"),
    ]

    for document in documents:
        normalized = " ".join(document.split())
        assert "/api/v1/report-batches" in document
        assert "source" in normalized.lower()
        assert "membership" in normalized.lower()
        assert "lotus-report" in normalized


def test_report_batch_wiki_example_contains_selection_not_candidate_authority() -> None:
    api_surface = _read("wiki/API-Surface.md")
    command_start = api_surface.index('curl -X POST "$GATEWAY_BASE_URL/api/v1/report-batches"')
    command_end = api_surface.index("```", command_start)
    command = api_surface[command_start:command_end]

    assert '\\"portfolio_ids\\"' in command
    assert "X-Caller-Capabilities: advisor.book.read" in command
    assert '\\"source_candidates\\"' not in command
    assert '\\"tenant_id\\"' not in command
    assert '\\"region\\"' not in command
