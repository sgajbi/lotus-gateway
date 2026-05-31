from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_gateway_overview_wiki_is_audience_aware_and_implementation_backed() -> None:
    overview = (ROOT / "wiki" / "Overview.md").read_text(encoding="utf-8")
    home = (ROOT / "wiki" / "Home.md").read_text(encoding="utf-8")

    assert "## Functional Capability Matrix" in overview
    assert "## Non-Functional Capability Matrix" in overview
    assert "## Audience Guide" in overview
    assert "```mermaid" in overview
    assert "implementation-backed" in overview
    assert "product-safe upstream errors" in overview
    assert "Sales, client-demo, and presentation teams" in overview
    assert "[Supported Features](Supported-Features)" in home
