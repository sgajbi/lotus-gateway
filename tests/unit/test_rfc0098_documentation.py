from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_rfc0098_proof_pack_ownership_matches_manage_rfc0040() -> None:
    rfc = (
        ROOT / "docs" / "rfcs" / "RFC-0098-dpm-command-center-composition-contract.md"
    ).read_text(encoding="utf-8")
    index = (ROOT / "docs" / "rfcs" / "README.md").read_text(encoding="utf-8")
    api_surface = (ROOT / "wiki" / "API-Surface.md").read_text(encoding="utf-8")
    integrations = (ROOT / "wiki" / "Integrations.md").read_text(encoding="utf-8")

    assert "RFC-0040 PROOF-PACK OWNERSHIP ALIGNED" in rfc
    assert "RFC-0040 PROOF-PACK OWNERSHIP ALIGNED" in index
    assert "`lotus-manage` RFC-0040" in rfc
    assert "Gateway must not" in rfc
    assert "treat `lotus-report` as the proof-pack authority" in rfc
    assert "proof_pack_evidence" in rfc
    assert "DpmPreTradeProofPack:v1" in rfc
    assert "proof-pack authority APIs" in integrations
    assert "not proof-pack authority" in api_surface
    assert "Gateway does not generate proof packs. That belongs to `lotus-report`." not in rfc
