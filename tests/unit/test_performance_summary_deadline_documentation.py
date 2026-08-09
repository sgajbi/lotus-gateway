from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_performance_summary_deadline_is_durable_across_operator_and_product_truth() -> None:
    standard = _read("docs/standards/scalability-availability.md")
    supported_features = _read("docs/supported-features.md")
    wiki = _read("wiki/Supported-Features.md")
    context = _read("REPOSITORY-ENGINEERING-CONTEXT.md")
    standard_normalized = " ".join(standard.lower().split())
    wiki_normalized = " ".join(wiki.lower().split())

    for document in (standard, wiki, context):
        normalized = " ".join(document.lower().split())
        assert "30-second" in normalized or "=30" in normalized
        assert "one calculation identity" in normalized
        assert "partial-readiness" in normalized

    assert "monotonic" in standard
    assert "monotonic" in context
    assert "ASYNC_RESULT_DEADLINE_EXHAUSTED" in standard
    assert "async_poll_deadline_exhausted" in standard
    assert "PERFORMANCE_WORKSPACE_SUMMARY_DEADLINE_EXHAUSTED" in standard
    assert "before the first result read" in standard
    assert "execution or lineage evidence reads" in standard
    assert "complete http await" in standard_normalized
    assert "typed transient transport" in standard_normalized
    assert "submission acceptance is unknown" in standard_normalized
    assert "warm retry" in supported_features
    assert "slow multi-phase or response-trickle" in supported_features
    assert "blind retry" in wiki
    assert "complete-await cancellation" in wiki_normalized
    assert "warm response" in wiki
