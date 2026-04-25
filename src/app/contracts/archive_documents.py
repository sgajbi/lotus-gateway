from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

ARCHIVE_DOCUMENT_EXAMPLE: dict[str, Any] = {
    "correlationId": "corr-archive-document-1",
    "contractVersion": "v1",
    "sourceService": "lotus-archive",
    "documentId": "doc_7d5f1f1e4d0d4d0f9b7f1a2a6b8c9d10",
    "reportJobId": "rjob_83ca965c50334c40a17d2b8cc94873a5",
    "reportRequestId": "rrq_4f7c85b39f7d4e7b8d0bb420d34a1d2c",
    "reportType": "portfolio_review",
    "portfolioScope": "PB_SG_GLOBAL_BAL_001",
    "portfolioId": "PB_SG_GLOBAL_BAL_001",
    "clientReference": "Private client relationship",
    "asOfDate": "2026-04-22",
    "reportingPeriodStart": "2026-01-01",
    "reportingPeriodEnd": "2026-04-22",
    "frequency": "ad_hoc",
    "templateId": "portfolio-review",
    "templateVersion": "v1",
    "renderServiceVersion": "lotus-render@2026.04",
    "reportDataContractVersion": "portfolio-review.v1",
    "checksumAlgorithm": "sha256",
    "checksum": "8e2f8f3f53d2b6d4c5b4a6f3e6b4c7d8e9f00112233445566778899aabbccdde",
    "sizeBytes": 384912,
    "mimeType": "application/pdf",
    "outputFormat": "pdf",
    "classification": "confidential",
    "region": "APAC",
    "tenantId": "tenant-sg",
    "retentionPolicyId": "sg-private-banking-retention-v1",
    "retentionStartDate": "2026-04-22",
    "retainUntilDate": "2033-04-22",
    "purgeStatus": "retained",
    "legalHoldStatus": "clear",
    "legalHoldCount": 0,
    "supersedesDocumentId": None,
    "supersededByDocumentId": None,
    "correctionOfDocumentId": None,
    "reissueOfDocumentId": None,
    "createdByService": "lotus-report",
    "createdByActor": "report-worker",
    "createdAt": "2026-04-22T09:04:00Z",
    "updatedAt": "2026-04-22T09:04:00Z",
    "downloadUrl": "/api/v1/documents/doc_7d5f1f1e4d0d4d0f9b7f1a2a6b8c9d10/download",
}

ARCHIVE_DOCUMENT_ERROR_EXAMPLES: dict[str, dict[str, Any]] = {
    "missing_caller_context": {
        "detail": {
            "code": "missing_caller_context",
            "message": "Required caller context headers are missing.",
            "missing_headers": ["X-Actor-Id", "X-Tenant-Id", "X-Region"],
        }
    },
    "archived_document_not_found": {
        "detail": {
            "code": "archived_document_not_found",
            "message": "Archived document was not found.",
        }
    },
    "document_access_unauthorized": {
        "detail": {
            "code": "document_access_unauthorized",
            "message": "Caller is not authorized to access this archived document.",
        }
    },
    "document_download_failed": {
        "detail": {
            "code": "document_download_failed",
            "message": "Archived document download is unavailable.",
        }
    },
    "archive_upstream_unavailable": {
        "detail": {
            "code": "archive_upstream_unavailable",
            "message": "Archived document service is unavailable.",
        }
    },
}


class ArchivedDocumentErrorDetail(BaseModel):
    code: str = Field(
        ...,
        description="Stable product-safe error code for archived document operations.",
        examples=["archived_document_not_found"],
    )
    message: str = Field(
        ...,
        description="Product-safe error message.",
        examples=["Archived document was not found."],
    )
    missing_headers: list[str] | None = Field(
        default=None,
        description="Required caller context headers that were absent from the request.",
        examples=[["X-Actor-Id", "X-Tenant-Id", "X-Region"]],
    )


class ArchivedDocumentErrorResponse(BaseModel):
    detail: ArchivedDocumentErrorDetail = Field(
        description="Product-safe archived document error payload."
    )


class ArchivedDocumentMetadataResponse(BaseModel):
    correlation_id: str = Field(
        ...,
        alias="correlationId",
        description="Correlation identifier for support tracing.",
        examples=["corr-archive-document-1"],
    )
    contract_version: str = Field(
        ...,
        alias="contractVersion",
        description="Gateway archived-document contract version.",
        examples=["v1"],
    )
    source_service: str = Field(
        ...,
        alias="sourceService",
        description="Authoritative upstream service for archived document metadata.",
        examples=["lotus-archive"],
    )
    document_id: str = Field(
        ...,
        alias="documentId",
        description="Stable archived document identifier.",
        examples=["doc_7d5f1f1e4d0d4d0f9b7f1a2a6b8c9d10"],
    )
    report_job_id: str = Field(
        ..., alias="reportJobId", description="Source report job identifier."
    )
    report_request_id: str = Field(
        ..., alias="reportRequestId", description="Source report request identifier."
    )
    report_type: str = Field(
        ..., alias="reportType", description="Report type represented by the archived document."
    )
    portfolio_scope: str = Field(
        ..., alias="portfolioScope", description="Portfolio scope represented by the document."
    )
    portfolio_id: str = Field(
        ..., alias="portfolioId", description="Portfolio identifier represented by the document."
    )
    client_reference: str | None = Field(
        default=None,
        alias="clientReference",
        description="Support-safe client relationship reference when supplied by reporting.",
    )
    as_of_date: date = Field(..., alias="asOfDate", description="Report as-of date.")
    reporting_period_start: date = Field(
        ..., alias="reportingPeriodStart", description="Reporting period start date."
    )
    reporting_period_end: date = Field(
        ..., alias="reportingPeriodEnd", description="Reporting period end date."
    )
    frequency: str = Field(description="Report frequency.")
    template_id: str = Field(
        ..., alias="templateId", description="Template identifier used for rendering."
    )
    template_version: str = Field(
        ..., alias="templateVersion", description="Template version used for rendering."
    )
    render_service_version: str = Field(
        ...,
        alias="renderServiceVersion",
        description="Render service version that produced the archived document.",
    )
    report_data_contract_version: str = Field(
        ...,
        alias="reportDataContractVersion",
        description="Report data contract version used for generation.",
    )
    checksum_algorithm: str = Field(
        ..., alias="checksumAlgorithm", description="Checksum algorithm used for integrity checks."
    )
    checksum: str = Field(description="Checksum of the archived binary.")
    size_bytes: int = Field(..., alias="sizeBytes", description="Archived binary size in bytes.")
    mime_type: str = Field(..., alias="mimeType", description="Archived binary media type.")
    output_format: str = Field(..., alias="outputFormat", description="Archived output format.")
    classification: str = Field(description="Document classification.")
    region: str = Field(description="Operating region for the archive record.")
    tenant_id: str | None = Field(
        default=None, alias="tenantId", description="Tenant scope when available."
    )
    retention_policy_id: str | None = Field(
        default=None,
        alias="retentionPolicyId",
        description="Retention policy assigned to the document.",
    )
    retention_start_date: date | None = Field(
        default=None,
        alias="retentionStartDate",
        description="Date retention starts for the document.",
    )
    retain_until_date: date | None = Field(
        default=None,
        alias="retainUntilDate",
        description="Date until which the document must be retained.",
    )
    purge_status: str = Field(alias="purgeStatus", description="Current purge status.")
    legal_hold_status: str = Field(
        alias="legalHoldStatus",
        description="Current legal-hold summary. Active holds do not hide metadata retrieval.",
    )
    legal_hold_count: int = Field(
        alias="legalHoldCount", description="Number of active legal holds."
    )
    supersedes_document_id: str | None = Field(
        default=None,
        alias="supersedesDocumentId",
        description="Document superseded by this document, when applicable.",
    )
    superseded_by_document_id: str | None = Field(
        default=None,
        alias="supersededByDocumentId",
        description="Document that supersedes this document, when applicable.",
    )
    correction_of_document_id: str | None = Field(
        default=None,
        alias="correctionOfDocumentId",
        description="Document corrected by this document, when applicable.",
    )
    reissue_of_document_id: str | None = Field(
        default=None,
        alias="reissueOfDocumentId",
        description="Document reissued by this document, when applicable.",
    )
    created_by_service: str = Field(
        ..., alias="createdByService", description="Service that created the archive record."
    )
    created_by_actor: str = Field(
        ..., alias="createdByActor", description="Actor that created the archive record."
    )
    created_at: datetime = Field(
        ..., alias="createdAt", description="UTC timestamp when the archive record was created."
    )
    updated_at: datetime = Field(
        ...,
        alias="updatedAt",
        description="UTC timestamp when the archive record was last updated.",
    )
    download_url: str = Field(
        ...,
        alias="downloadUrl",
        description="Gateway-controlled download route for the archived document binary.",
        examples=["/api/v1/documents/doc_7d5f1f1e4d0d4d0f9b7f1a2a6b8c9d10/download"],
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {"examples": [ARCHIVE_DOCUMENT_EXAMPLE]},
    }

    @classmethod
    def from_archive_payload(
        cls,
        payload: dict[str, Any],
        *,
        correlation_id: str,
        contract_version: str,
    ) -> "ArchivedDocumentMetadataResponse":
        document_id = str(payload.get("document_id", ""))
        gateway_payload = {
            **payload,
            "correlationId": correlation_id,
            "contractVersion": contract_version,
            "sourceService": "lotus-archive",
            "downloadUrl": f"/api/v1/documents/{document_id}/download",
        }
        return cls.model_validate(gateway_payload)
