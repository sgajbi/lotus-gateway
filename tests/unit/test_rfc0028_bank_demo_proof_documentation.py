from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_rfc0028_gateway_documentation_matches_bank_demo_proof_boundary() -> None:
    readme = _read("README.md")
    repo_context = _read("REPOSITORY-ENGINEERING-CONTEXT.md")
    rfc_index = _read("docs/rfcs/README.md")
    gateway_rfc = _read("docs/rfcs/RFC-0028-bank-demo-proof-gateway-publication.md")
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
        assert (
            "bank-demo proof" in document
            or "bank-demo-proof" in document
            or "Bank Demo Proof" in document
        )

    assert "`GET /api/v1/advisory/bank-demo-proof/scenario-contract`" in gateway_rfc
    assert "`GET /api/v1/advisory/bank-demo-proof/supported-claim-register`" in gateway_rfc
    assert "`POST /api/v1/advisory/bank-demo-proof/proof-packs`" in gateway_rfc
    assert "`/advisory/bank-demo-proof/*`" in upstream_map
    assert "bank-demo scenario-contract" in wiki_architecture
    assert "material-review posture" in wiki_api
    assert "canonical runtime proof flow" in wiki_api
    assert "supported-claim classifications" in wiki_supported_features
    assert "409 Conflict" in wiki_supported_features
    assert "Workbench product UI, browser proof" in wiki_supported_features
    assert "does not by itself certify" in wiki_supported_features

    overclaim_boundaries = [
        "client-ready publication",
        "RFP/security",
        "screenshot",
        "OMS/order/fill/settlement",
        "external client communication",
    ]
    for boundary in overclaim_boundaries:
        assert boundary in gateway_rfc
        assert boundary in wiki_supported_features
