from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_discussion_pack_docs_preserve_identity_authority_and_client_boundary() -> None:
    contract = _read("docs/contracts/proposal-discussion-pack-review-v1.md")
    supported = _read("docs/supported-features.md")
    upstream_map = _read("docs/standards/RFC-0082-upstream-contract-family-map.md")
    context = _read("REPOSITORY-ENGINEERING-CONTEXT.md")
    wiki_supported = _read("wiki/Supported-Features.md")
    wiki_api = _read("wiki/API-Surface.md")
    integrations = _read("wiki/Integrations.md")

    for content in (contract, wiki_supported, wiki_api):
        normalized = " ".join(content.split()).lower()
        assert "/api/v1/proposals/{proposal_id}/discussion-pack-review" in content
        assert "proposal-discussion-pack-review.v1" in content
        assert "advisor-use" in normalized
        assert "client release" in normalized or "client-release" in normalized
        assert "client delivery" in normalized or "client-delivery" in normalized

    assert "five bounded concurrent reads" in " ".join(contract.split())
    assert "discussion-pack-review evidence" in supported
    assert "Operational Read experience projection" in upstream_map
    assert "discussion-pack-review evidence" in context
    assert "lotus-workbench#749" in wiki_supported
    assert "lotus-report" in integrations


def test_discussion_pack_docs_do_not_claim_consumer_runtime_completion() -> None:
    contract = _read("docs/contracts/proposal-discussion-pack-review-v1.md")
    wiki_supported = _read("wiki/Supported-Features.md")

    assert "Focused live Gateway/BFF and Workbench browser evidence remains required" in contract
    assert "canonical browser proof remain" in wiki_supported
