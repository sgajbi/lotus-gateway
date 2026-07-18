from pathlib import Path

_ROOT = Path(__file__).parents[2]


def _read(relative_path: str) -> str:
    return (_ROOT / relative_path).read_text(encoding="utf-8")


def _squash(value: str) -> str:
    return " ".join(value.split())


def test_supported_feature_docs_preserve_authenticated_own_book_boundary() -> None:
    docs = _read("docs/supported-features.md")
    wiki = _read("wiki/Supported-Features.md")

    for content in (docs, wiki):
        assert "/api/v1/advisor-book/portfolios" in content
        assert "PortfolioManagerBookMembership:v1" in content
        assert "global portfolio catalogue" in _squash(content)
        assert "tenant" in content.lower()
    assert "advisor.book.read" in wiki
    assert "no advisor-id override" in wiki


def test_rfc_0082_map_classifies_advisor_book_as_core_operational_read() -> None:
    family_map = _read("docs/standards/RFC-0082-upstream-contract-family-map.md")

    assert "get_portfolio_manager_book_memberships" in family_map
    assert "Operational Read" in family_map
    assert "never widen through the global portfolio catalogue" in family_map


def test_operator_example_requires_complete_trusted_caller_context() -> None:
    api_surface = _read("wiki/API-Surface.md")

    for value in (
        "asOfDate=2026-04-10",
        "X-Actor-Id: PM_SG_001",
        "X-Tenant-Id: tenant-sg",
        "X-Booking-Center-Code: Singapore",
        "X-Role: ADVISOR",
        "X-Caller-Capabilities: advisor.book.read",
    ):
        assert value in api_surface
    assert "there is no advisor-id query override" in _squash(api_surface)


def test_repository_context_and_review_ledger_record_known_follow_up_owners() -> None:
    context = _read("REPOSITORY-ENGINEERING-CONTEXT.md")
    ledger = _read("CODEBASE-REVIEW-LEDGER.md")

    assert "PortfolioManagerBookMembership:v1" in context
    assert "Gateway/Workbench #436" in ledger
    assert "Core #513" in ledger
    assert "No duplicate downstream issue was opened" in ledger
