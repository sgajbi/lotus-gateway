from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _normalized(relative_path: str) -> str:
    content = (ROOT / relative_path).read_text(encoding="utf-8")
    return " ".join(content.lower().split())


def test_attribution_trend_bounds_are_durable_across_operator_and_product_truth() -> None:
    standard = _normalized("docs/standards/scalability-availability.md")
    supported_features = _normalized("docs/supported-features.md")
    wiki_features = _normalized("wiki/Supported-Features.md")
    wiki_architecture = _normalized("wiki/Architecture.md")
    context = _normalized("REPOSITORY-ENGINEERING-CONTEXT.md")

    for document in (standard, context):
        assert "attribution_trend_concurrency_limit" in document
        assert "attribution_trend_deadline_seconds" in document
        assert "replica" in document
        assert "process" in document
        assert "idempotency key" in document
        assert "result_path" in document
        assert "durable" in document

    for document in (supported_features, wiki_features, wiki_architecture):
        assert "process" in document
        assert "queued-plus-active" in document
        assert "completed" in document
        assert "timed_out" in document or "timed-out" in document
        assert "null financial values" in document or "source facts remain null" in document
        assert "process-local cache" in document or "cached in gateway memory" in document
        assert "restart-safe" in document
