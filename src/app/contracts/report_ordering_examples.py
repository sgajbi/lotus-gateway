REPORT_ORDERING_RESPONSE_EXAMPLE = {
    "contractVersion": "workbench-report-ordering.v1",
    "sourceAuthority": "reporting",
    "sourceContractVersion": "report-ordering-catalogue.v1",
    "scopeSelection": {
        "scopeType": "portfolio",
        "scopeId": "PB_SG_GLOBAL_BAL_001",
    },
    "catalogueAvailability": {
        "state": "partial",
        "reasonCode": "report_catalogue_partially_available",
        "message": "Some report outputs are temporarily unavailable.",
    },
    "scopeEligibility": {
        "state": "ready",
        "reasonCode": "selected_scope_eligible",
        "message": "The selected portfolio is available for report ordering.",
    },
    "reportFamilies": [
        {
            "reportFamilyId": "portfolio_review",
            "businessLabel": "Portfolio review report",
            "description": "Advisor review pack for a client portfolio and selected business date.",
            "intendedUse": "advisor_client_portfolio_review",
            "audienceRoles": ["client_advisor", "portfolio_manager"],
            "clientReleasePosture": ("advisor_review_required_distribution_not_supported"),
            "orderingModes": [
                {
                    "modeId": "single_portfolio",
                    "businessLabel": "Single portfolio",
                    "description": "Create one report for the selected portfolio.",
                    "defaultOutputFormat": "json",
                    "interactive": True,
                    "eligibility": {
                        "state": "ready",
                        "reasonCode": "single_portfolio_ordering_ready",
                        "message": "This portfolio can be submitted for report creation.",
                    },
                    "submission": {
                        "capabilityId": "reporting.portfolio_review.single",
                        "method": "POST",
                        "path": "/api/v1/reports/portfolio-reviews",
                        "state": "ready",
                        "reasonCode": "single_portfolio_ordering_ready",
                    },
                }
            ],
            "outputFormats": [
                {
                    "formatId": "json",
                    "businessLabel": "Structured data package",
                    "usePosture": "system_integration",
                    "state": "ready",
                    "reasonCode": "report_data_ready",
                },
                {
                    "formatId": "pdf",
                    "businessLabel": "Governed PDF document",
                    "usePosture": "governed_document",
                    "state": "unavailable",
                    "reasonCode": "render_metadata_unavailable",
                },
            ],
            "configurationFields": [
                {
                    "fieldId": "as_of_date",
                    "businessLabel": "Report date",
                    "description": "Business date used for portfolio reporting evidence.",
                    "inputType": "business_date",
                    "requirement": "required",
                    "defaultingPolicy": "caller_required",
                    "valueSource": "caller",
                    "options": [],
                }
            ],
            "sections": [
                {
                    "sectionId": "CLIENT_PROFILE",
                    "businessLabel": "Client and mandate profile",
                    "description": "Client, relationship, portfolio, and mandate context.",
                    "displayOrder": 10,
                    "selectionPosture": "required",
                    "defaultSelected": True,
                    "dependencyFieldIds": [],
                }
            ],
            "availability": {
                "state": "partial",
                "reasonCode": "report_family_partially_available",
                "message": "Available with a reduced set of output formats.",
            },
            "eligibility": {
                "state": "ready",
                "reasonCode": "report_family_eligible",
                "message": "This report family is available for the caller and selected scope.",
            },
        }
    ],
}
