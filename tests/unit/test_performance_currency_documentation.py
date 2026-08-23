from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _normalized(value: str) -> str:
    return " ".join(value.split()).lower()


def test_detail_currency_fallback_contract_is_documented_without_forwarding_claim() -> None:
    documents = (
        _read("docs/supported-features.md"),
        _read("wiki/Supported-Features.md"),
        _read("wiki/API-Surface.md"),
    )

    for document in documents:
        normalized = _normalized(document)
        assert "independent contribution and attribution detail requests" in normalized
        assert "currently use the portfolio base currency" in normalized
        assert "does not send `currency_mode=both`" in normalized
        assert "use `currency_mode=both`" not in normalized
        assert "with `report_ccy`" not in normalized
        assert "performance_details_currency_not_applied_base" in normalized
        assert "lotus-performance#470" in normalized
        assert "accepted_unverified" in normalized
        assert "source-applied currency evidence" in normalized
