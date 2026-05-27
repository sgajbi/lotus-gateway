from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_rfc0026_gateway_documentation_matches_implemented_cockpit_boundary() -> None:
    readme = _read("README.md")
    repo_context = _read("REPOSITORY-ENGINEERING-CONTEXT.md")
    rfc_index = _read("docs/rfcs/README.md")
    gateway_rfc = _read("docs/rfcs/RFC-0026-advisor-cockpit-gateway-publication.md")
    upstream_map = _read("docs/standards/RFC-0082-upstream-contract-family-map.md")
    wiki_api = _read("wiki/API-Surface.md")
    wiki_architecture = _read("wiki/Architecture.md")
    wiki_home = _read("wiki/Home.md")
    wiki_integrations = _read("wiki/Integrations.md")
    wiki_rfc_index = _read("wiki/RFC-Index.md")
    wiki_supported_features = _read("wiki/Supported-Features.md")

    for document in [
        readme,
        repo_context,
        rfc_index,
        gateway_rfc,
        upstream_map,
        wiki_api,
        wiki_architecture,
        wiki_home,
        wiki_integrations,
        wiki_rfc_index,
        wiki_supported_features,
    ]:
        lowered = document.lower()
        assert "advisor cockpit" in lowered or "advisor-cockpit" in lowered

    assert "`GET /api/v1/advisor-cockpit/actions`" in gateway_rfc
    assert "`GET /api/v1/advisor-cockpit/actions/{action_item_id}`" in gateway_rfc
    assert "`GET /api/v1/advisor-cockpit/snapshot`" in gateway_rfc
    assert "`GET /api/v1/advisor-cockpit/supportability`" in gateway_rfc
    assert "`POST /api/v1/advisor-cockpit/actions/{action_item_id}/acknowledgements`" in gateway_rfc
    assert "`/advisory/cockpit/*`" in upstream_map
    assert "without reconstructing advisory semantics" in wiki_architecture
    assert "not reconstruct advisory policy, memo blockers, cockpit action semantics" in wiki_api
    assert "publication remains blocked" in wiki_supported_features.lower()
    assert "Workbench product realization" in wiki_supported_features
    assert "RFC26_ADVISOR_COCKPIT_CANONICAL" in gateway_rfc
    assert "full product support remain mandatory later RFC-0026 slices" in gateway_rfc
    assert "full demo readiness" in gateway_rfc
