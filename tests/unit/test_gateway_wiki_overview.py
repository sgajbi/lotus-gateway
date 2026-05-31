from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_gateway_overview_wiki_is_audience_aware_and_implementation_backed() -> None:
    overview = (ROOT / "wiki" / "Overview.md").read_text(encoding="utf-8")
    home = (ROOT / "wiki" / "Home.md").read_text(encoding="utf-8")
    supported_features = (ROOT / "wiki" / "Supported-Features.md").read_text(encoding="utf-8")

    assert "## Functional Capability Matrix" in overview
    assert "## Non-Functional Capability Matrix" in overview
    assert "## Audience Guide" in overview
    assert "```mermaid" in overview
    assert "implementation-backed" in overview
    assert "product-safe upstream errors" in overview
    assert "Sales, client-demo, and presentation teams" in overview
    assert "[Supported Features](Supported-Features)" in home
    assert "Production-readiness controls" in supported_features
    assert "shared upstream-envelope behavior" in supported_features
    assert "workflow-pack execution instead of local prompt construction" in supported_features
    assert "workflow responses plus product-safe manage error detail" in supported_features
    assert "mandate command-center, outcome-review" in supported_features
    assert "shared product-safe upstream error helper" in supported_features
    assert "shared Gateway guard" in supported_features
