from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_proposal_risk_impact_docs_preserve_source_authority_and_boundaries() -> None:
    contract = _read("docs/contracts/proposal-risk-impact-v1.md")
    supported = _read("docs/supported-features.md")
    upstream_map = _read("docs/standards/RFC-0082-upstream-contract-family-map.md")
    context = _read("REPOSITORY-ENGINEERING-CONTEXT.md")
    wiki_supported = _read("wiki/Supported-Features.md")
    wiki_api = _read("wiki/API-Surface.md")

    for content in (contract, wiki_supported, wiki_api):
        normalized = " ".join(content.split())
        assert "/api/v1/proposals/{proposal_id}/risk-impact" in content
        assert any(
            phrase in normalized for phrase in ("not_supported", "not supported", "unsupported")
        )
        assert "allocation" in content.lower()
        assert "approval" in content.lower()

    assert "one bounded `lotus-advise` proposal-detail read" in contract
    assert "does not calculate risk" in contract
    assert "does not calculate" in wiki_supported
    assert "does not calculate risk or allocation deltas" in " ".join(wiki_api.split())
    assert "typed selected-proposal risk-and-impact evidence" in supported
    assert "Operational Read experience projection" in upstream_map
    assert "calculating\n   proposal risk or allocation deltas" in context


def test_proposal_risk_impact_docs_name_the_unsupported_producer_gaps() -> None:
    contract = _read("docs/contracts/proposal-risk-impact-v1.md")
    wiki_supported = _read("wiki/Supported-Features.md")

    for evidence_family in ("benchmark/limit", "scenario", "valuation"):
        assert evidence_family in contract
        assert evidence_family in wiki_supported
