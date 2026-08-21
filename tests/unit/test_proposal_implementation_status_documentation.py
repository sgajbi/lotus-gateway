from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_implementation_status_docs_preserve_source_authority_and_boundaries() -> None:
    contract = _read("docs/contracts/proposal-implementation-status-v1.md")
    supported = _read("docs/supported-features.md")
    upstream_map = _read("docs/standards/RFC-0082-upstream-contract-family-map.md")
    context = _read("REPOSITORY-ENGINEERING-CONTEXT.md")
    wiki_supported = _read("wiki/Supported-Features.md")
    wiki_api = _read("wiki/API-Surface.md")
    integrations = _read("wiki/Integrations.md")

    for content in (contract, wiki_supported, wiki_api):
        normalized = " ".join(content.split()).lower()
        assert "/api/v1/proposals/{proposal_id}/execution-status" in content
        assert "proposal-implementation-status.v1" in content
        for boundary in ("order", "fill", "settlement"):
            assert boundary in normalized

    assert "all eight states" in contract
    assert "downstream execution provider" in contract.lower()
    assert "Operational Read experience projection" in upstream_map
    assert "implementation-status evidence" in supported
    assert "typed implementation" in context
    assert "execution system of record" in integrations


def test_implementation_status_docs_name_workbench_runtime_proof_as_remaining() -> None:
    contract = _read("docs/contracts/proposal-implementation-status-v1.md")
    wiki_supported = _read("wiki/Supported-Features.md")

    assert "Focused live API evidence is required" in contract
    assert "lotus-workbench#750" in wiki_supported
