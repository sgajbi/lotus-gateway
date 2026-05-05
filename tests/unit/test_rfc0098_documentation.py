from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_rfc0098_ownership_matches_manage_rfc0040_rfc0041_and_rfc0042() -> None:
    rfc = (
        ROOT / "docs" / "rfcs" / "RFC-0098-dpm-command-center-composition-contract.md"
    ).read_text(encoding="utf-8")
    index = (ROOT / "docs" / "rfcs" / "README.md").read_text(encoding="utf-8")
    api_surface = (ROOT / "wiki" / "API-Surface.md").read_text(encoding="utf-8")
    integrations = (ROOT / "wiki" / "Integrations.md").read_text(encoding="utf-8")

    assert "RFC-0042 OUTCOME-REVIEW BFF ROUTES IMPLEMENTED" in rfc
    assert "RFC-0042 OUTCOME-REVIEW BFF ROUTES IMPLEMENTED" in index
    assert "`lotus-manage` RFC-0040" in rfc
    assert "`lotus-manage` RFC-0041" in rfc
    assert "`lotus-manage` RFC-0042" in rfc
    assert "Gateway must not" in rfc
    assert "treat `lotus-report` as the proof-pack authority" in rfc
    assert "calculate affected portfolios, source readiness, aggregate metrics" in rfc
    assert "`GET /api/v1/dpm/command-center/waves/{wave_id}/supportability`" in rfc
    assert "proof_pack_evidence" in rfc
    assert "wave_summary" in rfc
    assert "DpmPreTradeProofPack:v1" in rfc
    assert "RFC-0042 Post-Trade Outcome Review Addendum" in rfc
    assert "`GET /api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}`" in rfc
    assert "`GET /api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review`" in rfc
    assert "`GET /api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews`" in rfc
    assert "outcome_review_summary" in rfc
    assert "dimension_outcomes" in rfc
    assert "not recompute outcome truth" in api_surface
    assert "outcome reviews remain `lotus-manage` truth" in integrations
    assert "proof-pack authority APIs" in integrations
    assert "RFC-0041 rebalance-wave orchestration" in integrations
    assert "not proof-pack authority" in api_surface
    assert "must not calculate affected portfolios" in api_surface
    assert "Gateway does not generate proof packs. That belongs to `lotus-report`." not in rfc
