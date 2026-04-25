from fastapi.testclient import TestClient

from app.contracts.archive_documents import ArchivedDocumentMetadataResponse
from app.main import app


def test_archive_document_contract_shape() -> None:
    payload = ArchivedDocumentMetadataResponse(
        correlationId="corr-archive-document-1",
        contractVersion="v1",
        sourceService="lotus-archive",
        documentId="doc_1",
        reportJobId="rjob_1",
        reportRequestId="rrq_1",
        reportType="portfolio_review",
        portfolioScope="PB_SG_GLOBAL_BAL_001",
        portfolioId="PB_SG_GLOBAL_BAL_001",
        clientReference="Private client relationship",
        asOfDate="2026-04-22",
        reportingPeriodStart="2026-01-01",
        reportingPeriodEnd="2026-04-22",
        frequency="ad_hoc",
        templateId="portfolio-review",
        templateVersion="v1",
        renderServiceVersion="lotus-render@2026.04",
        reportDataContractVersion="portfolio-review.v1",
        checksumAlgorithm="sha256",
        checksum="abc123",
        sizeBytes=8,
        mimeType="application/pdf",
        outputFormat="pdf",
        classification="confidential",
        region="APAC",
        tenantId="tenant-sg",
        retentionPolicyId="sg-private-banking-retention-v1",
        retentionStartDate="2026-04-22",
        retainUntilDate="2033-04-22",
        purgeStatus="retained",
        legalHoldStatus="clear",
        legalHoldCount=0,
        createdByService="lotus-report",
        createdByActor="report-worker",
        createdAt="2026-04-22T09:04:00Z",
        updatedAt="2026-04-22T09:04:00Z",
        downloadUrl="/api/v1/documents/doc_1/download",
    )

    assert payload.source_service == "lotus-archive"
    assert payload.download_url == "/api/v1/documents/doc_1/download"
    assert payload.model_dump(by_alias=True)["documentId"] == "doc_1"


def test_archive_document_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    assert "/api/v1/documents/{document_id}" in spec["paths"]
    assert "/api/v1/documents/{document_id}/download" in spec["paths"]
    metadata_operation = spec["paths"]["/api/v1/documents/{document_id}"]["get"]
    download_operation = spec["paths"]["/api/v1/documents/{document_id}/download"]["get"]
    metadata_schema = spec["components"]["schemas"]["ArchivedDocumentMetadataResponse"]
    error_schema = spec["components"]["schemas"]["ArchivedDocumentErrorResponse"]

    assert metadata_operation["summary"] == "Get archived document metadata"
    assert "gateway boundary" in metadata_operation["description"]
    assert download_operation["summary"] == "Download archived document"
    assert "storage locations hidden" in download_operation["description"]
    assert metadata_operation["responses"]["403"]["description"]
    assert metadata_operation["responses"]["404"]["description"]
    assert metadata_operation["responses"]["502"]["description"]
    assert download_operation["responses"]["502"]["description"]
    assert "RFC-" not in str(metadata_operation)
    assert "RFC-" not in str(download_operation)

    metadata_parameters = {
        parameter["name"]: parameter for parameter in metadata_operation["parameters"]
    }
    download_parameters = {
        parameter["name"]: parameter for parameter in download_operation["parameters"]
    }
    assert metadata_parameters["document_id"]["description"]
    assert metadata_parameters["current"]["description"]
    assert download_parameters["document_id"]["description"]

    for property_contract in metadata_schema["properties"].values():
        assert property_contract.get("description")
    for property_contract in error_schema["properties"].values():
        assert property_contract.get("description")
    assert metadata_schema["properties"]["downloadUrl"]["description"].startswith(
        "Gateway-controlled"
    )
    assert metadata_schema["properties"]["legalHoldStatus"]["description"]
    assert metadata_schema["properties"]["checksum"]["description"]
    assert metadata_schema["examples"][0]["sourceService"] == "lotus-archive"
    assert metadata_schema["examples"][0]["downloadUrl"].startswith("/api/v1/documents/")
