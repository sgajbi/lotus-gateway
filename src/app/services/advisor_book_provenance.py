"""Shared advisor-book projections of Core membership evidence."""

from datetime import date

from app.contracts.advisor_book import AdvisorBookProvenance, AdvisorBookScope
from app.services.advisor_book_source_contract import SourceAdvisorBookResponse


def membership_provenance(source: SourceAdvisorBookResponse) -> AdvisorBookProvenance:
    return AdvisorBookProvenance(
        product_name=source.product_name,
        product_version=source.product_version,
        generated_at=source.generated_at,
        latest_evidence_timestamp=source.latest_evidence_timestamp,
        freshness_status=source.freshness_status,
        data_quality_status=source.data_quality_status,
        source_evidence_current=source.source_evidence_current,
        snapshot_id=source.snapshot_id,
        content_hash=source.content_hash,
        lineage=source.lineage,
    )


def own_book_scope(*, booking_center_code: str, as_of_date: date) -> AdvisorBookScope:
    return AdvisorBookScope(
        kind="own_book",
        label="My book",
        as_of_date=as_of_date,
        booking_center_code=booking_center_code,
    )
