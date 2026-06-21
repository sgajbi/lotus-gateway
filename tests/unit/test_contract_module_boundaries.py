import ast
from pathlib import Path

_CONTRACT_ROOT = Path(__file__).parents[2] / "src" / "app" / "contracts"


def _class_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _assigned_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names.update(target.id for target in targets if isinstance(target, ast.Name))
    return names


def test_proposal_memo_contracts_live_outside_proposal_facade() -> None:
    proposal_facade_classes = _class_names(_CONTRACT_ROOT / "proposals.py")
    memo_contract_classes = _class_names(_CONTRACT_ROOT / "proposal_memos.py")

    expected_memo_contracts = {
        "ProposalMemoAiCommentaryEnvelopeResponse",
        "ProposalMemoAiCommentaryRequest",
        "ProposalMemoCreateRequest",
        "ProposalMemoEnvelopeResponse",
        "ProposalMemoLineageEnvelopeResponse",
        "ProposalMemoProjectionEnvelopeResponse",
        "ProposalMemoReplayEvidenceEnvelopeResponse",
        "ProposalMemoReportPackageEnvelopeResponse",
        "ProposalMemoReportPackageRequest",
        "ProposalMemoReviewEnvelopeResponse",
        "ProposalMemoReviewRequest",
    }

    assert expected_memo_contracts <= memo_contract_classes
    assert proposal_facade_classes.isdisjoint(expected_memo_contracts)


def test_proposal_generation_contracts_live_outside_proposal_facade() -> None:
    proposal_facade_classes = _class_names(_CONTRACT_ROOT / "proposals.py")
    generation_contract_classes = _class_names(_CONTRACT_ROOT / "proposal_generation.py")

    expected_generation_contracts = {
        "ProposalSimulateRequest",
        "ProposalSimulateResponse",
        "ProposalSimulationData",
    }

    assert expected_generation_contracts <= generation_contract_classes
    assert proposal_facade_classes.isdisjoint(expected_generation_contracts)


def test_portfolio_liquidity_contracts_live_outside_portfolio_facade() -> None:
    portfolio_facade_classes = _class_names(_CONTRACT_ROOT / "portfolio.py")
    liquidity_contract_classes = _class_names(_CONTRACT_ROOT / "portfolio_liquidity.py")

    expected_liquidity_contracts = {
        "PortfolioCashflowOutlook",
        "PortfolioCashflowPoint",
        "PortfolioLiquidityResponse",
        "PortfolioProjectedCashflowResponse",
    }

    assert expected_liquidity_contracts <= liquidity_contract_classes
    assert portfolio_facade_classes.isdisjoint(expected_liquidity_contracts)


def test_performance_horizon_contracts_live_outside_performance_workspace_facade() -> None:
    performance_workspace_facade_classes = _class_names(_CONTRACT_ROOT / "performance_workspace.py")
    horizon_contract_classes = _class_names(_CONTRACT_ROOT / "performance_horizon.py")

    expected_horizon_contracts = {
        "PerformanceBenchmarkOptionView",
        "PerformanceHorizonComparisonResponse",
        "PerformanceHorizonComparisonRow",
    }

    assert expected_horizon_contracts <= horizon_contract_classes
    assert performance_workspace_facade_classes.isdisjoint(expected_horizon_contracts)


def test_performance_workspace_contracts_live_outside_performance_workspace_facade() -> None:
    performance_workspace_facade_classes = _class_names(_CONTRACT_ROOT / "performance_workspace.py")
    common_contract_classes = _class_names(_CONTRACT_ROOT / "performance_workspace_common.py")
    summary_contract_classes = _class_names(
        _CONTRACT_ROOT / "performance_workspace_summary_contract.py"
    )
    details_contract_classes = _class_names(
        _CONTRACT_ROOT / "performance_workspace_details_contract.py"
    )

    expected_common_contracts = {
        "MoneyWeightedReturnSummary",
        "PerformanceChartPoint",
        "PerformanceComparativeSummary",
        "PerformanceModuleCapability",
        "PerformanceWorkspaceCapabilities",
        "PerformanceWorkspaceResponse",
    }
    expected_summary_contracts = {"PerformanceWorkspaceSummaryResponse"}
    expected_details_contracts = {"PerformanceWorkspaceDetailsResponse"}

    assert expected_common_contracts <= common_contract_classes
    assert expected_summary_contracts <= summary_contract_classes
    assert expected_details_contracts <= details_contract_classes
    assert performance_workspace_facade_classes.isdisjoint(expected_common_contracts)
    assert performance_workspace_facade_classes.isdisjoint(expected_summary_contracts)
    assert performance_workspace_facade_classes.isdisjoint(expected_details_contracts)


def test_dpm_pm_operating_quality_contracts_live_outside_dpm_command_center_facade() -> None:
    dpm_command_center_facade_classes = _class_names(_CONTRACT_ROOT / "dpm_command_center.py")
    pm_quality_contract_classes = _class_names(_CONTRACT_ROOT / "dpm_pm_operating_quality.py")

    expected_pm_quality_contracts = {
        "DpmPmOperatingQualityForwardRequest",
        "DpmPmOperatingQualityGatewayResponse",
        "DpmPmOperatingQualitySummaryGatewayResponse",
        "DpmPmOperatingQualitySummaryRequest",
        "DpmPmOperatingQualitySupportability",
    }

    assert expected_pm_quality_contracts <= pm_quality_contract_classes
    assert dpm_command_center_facade_classes.isdisjoint(expected_pm_quality_contracts)


def test_dpm_portfolio_memory_contracts_live_outside_dpm_command_center_facade() -> None:
    dpm_command_center_facade_classes = _class_names(_CONTRACT_ROOT / "dpm_command_center.py")
    portfolio_memory_contract_classes = _class_names(_CONTRACT_ROOT / "dpm_portfolio_memory.py")

    expected_portfolio_memory_contracts = {
        "DpmPortfolioMemoryGatewayResponse",
        "DpmPortfolioMemorySupportability",
    }

    assert expected_portfolio_memory_contracts <= portfolio_memory_contract_classes
    assert dpm_command_center_facade_classes.isdisjoint(expected_portfolio_memory_contracts)


def test_dpm_command_center_contracts_live_outside_dpm_command_center_facade() -> None:
    dpm_command_center_facade_classes = _class_names(_CONTRACT_ROOT / "dpm_command_center.py")
    command_center_core_contract_classes = _class_names(
        _CONTRACT_ROOT / "dpm_command_center_core.py"
    )
    outcome_review_contract_classes = _class_names(_CONTRACT_ROOT / "dpm_outcome_review.py")

    expected_core_contracts = {
        "DpmCommandCenterForwardRequest",
        "DpmCommandCenterGatewayResponse",
        "DpmCommandCenterResolveExceptionRequest",
        "DpmCommandCenterSupportability",
    }
    expected_outcome_review_contracts = {
        "DpmExceptionSummaryGatewayResponse",
        "DpmExceptionSummaryRequest",
        "DpmOutcomeReviewErrorDetail",
        "DpmOutcomeReviewForwardRequest",
        "DpmOutcomeReviewGatewayResponse",
        "DpmOutcomeReviewNarrativeGatewayResponse",
        "DpmOutcomeReviewNarrativeRequest",
        "DpmOutcomeReviewRefreshRequest",
        "DpmOutcomeReviewSupportability",
    }

    assert expected_core_contracts <= command_center_core_contract_classes
    assert expected_outcome_review_contracts <= outcome_review_contract_classes
    assert dpm_command_center_facade_classes.isdisjoint(expected_core_contracts)
    assert dpm_command_center_facade_classes.isdisjoint(expected_outcome_review_contracts)


def test_dpm_wave_campaign_definition_contracts_live_outside_dpm_waves_facade() -> None:
    dpm_waves_facade_classes = _class_names(_CONTRACT_ROOT / "dpm_waves.py")
    campaign_definition_contract_classes = _class_names(
        _CONTRACT_ROOT / "dpm_wave_campaign_definitions.py"
    )

    expected_campaign_definition_contracts = {
        "DpmCampaignDefinitionForwardRequest",
        "DpmCampaignDefinitionGatewayResponse",
        "DpmCampaignDefinitionLaunchRequest",
        "DpmCampaignDefinitionLifecycleCommandRequest",
    }

    assert expected_campaign_definition_contracts <= campaign_definition_contract_classes
    assert dpm_waves_facade_classes.isdisjoint(expected_campaign_definition_contracts)


def test_dpm_wave_campaign_workflow_contracts_live_outside_dpm_waves_facade() -> None:
    dpm_waves_facade_classes = _class_names(_CONTRACT_ROOT / "dpm_waves.py")
    campaign_workflow_contract_classes = _class_names(
        _CONTRACT_ROOT / "dpm_wave_campaign_workflow.py"
    )

    expected_campaign_workflow_contracts = {
        "DpmCampaignWorkflowForwardRequest",
        "DpmCampaignWorkflowGatewayResponse",
    }

    assert expected_campaign_workflow_contracts <= campaign_workflow_contract_classes
    assert dpm_waves_facade_classes.isdisjoint(expected_campaign_workflow_contracts)


def test_dpm_wave_ai_contracts_live_outside_dpm_waves_facade() -> None:
    dpm_waves_facade_classes = _class_names(_CONTRACT_ROOT / "dpm_waves.py")
    wave_ai_contract_classes = _class_names(_CONTRACT_ROOT / "dpm_wave_ai.py")
    supportability_contract_classes = _class_names(_CONTRACT_ROOT / "dpm_wave_supportability.py")

    expected_wave_ai_contracts = {
        "DpmOperationsHandoffSummaryGatewayResponse",
        "DpmOperationsHandoffSummaryRequest",
        "DpmWaveMemoGatewayResponse",
        "DpmWaveMemoRequest",
    }
    expected_supportability_contracts = {"DpmWaveSupportability"}

    assert expected_wave_ai_contracts <= wave_ai_contract_classes
    assert expected_supportability_contracts <= supportability_contract_classes
    assert dpm_waves_facade_classes.isdisjoint(expected_wave_ai_contracts)
    assert dpm_waves_facade_classes.isdisjoint(expected_supportability_contracts)


def test_risk_rolling_payload_example_lives_outside_contract_models() -> None:
    rolling_contract_assignments = _assigned_names(_CONTRACT_ROOT / "risk_workspace_rolling.py")
    rolling_example_assignments = _assigned_names(
        _CONTRACT_ROOT / "risk_workspace_rolling_examples.py"
    )

    assert "RISK_ROLLING_PAYLOAD_EXAMPLE" in rolling_example_assignments
    assert "RISK_ROLLING_PAYLOAD_EXAMPLE" not in rolling_contract_assignments


def test_advisor_brief_workflow_contracts_live_outside_advisor_brief_facade() -> None:
    advisor_brief_facade_classes = _class_names(_CONTRACT_ROOT / "advisor_brief.py")
    workflow_contract_classes = _class_names(_CONTRACT_ROOT / "advisor_brief_workflow.py")

    expected_workflow_contracts = {
        "AdvisorBriefWorkflowPackRun",
        "AdvisorBriefWorkflowPackRunFinding",
        "AdvisorBriefWorkflowPackRunReviewActionRequest",
        "AdvisorBriefWorkflowPackRunReviewActionType",
        "AdvisorBriefWorkflowPackTaskFlow",
        "AdvisorBriefWorkflowPackTaskFlowHandoff",
        "AdvisorBriefWorkflowPackTaskFlowLineage",
    }

    assert expected_workflow_contracts <= workflow_contract_classes
    assert advisor_brief_facade_classes.isdisjoint(expected_workflow_contracts)


def test_advisor_brief_item_contracts_live_outside_advisor_brief_facade() -> None:
    advisor_brief_facade_classes = _class_names(_CONTRACT_ROOT / "advisor_brief.py")
    item_contract_classes = _class_names(_CONTRACT_ROOT / "advisor_brief_items.py")
    supportability_contract_classes = _class_names(
        _CONTRACT_ROOT / "advisor_brief_supportability.py"
    )

    expected_item_contracts = {
        "AdvisorBriefActionItem",
        "AdvisorBriefEvidenceRef",
        "AdvisorBriefNarrativeItem",
        "AdvisorBriefSourceMetric",
        "AdvisorBriefStatus",
        "AdvisorBriefSupportabilityItem",
        "AdvisorBriefTone",
    }
    expected_supportability_contracts = {
        "AdvisorBriefAdvisorySupportability",
        "AdvisorBriefAiSurfaceSupportability",
        "AdvisorBriefAiSurfaceSupportabilityItem",
    }

    assert expected_item_contracts <= item_contract_classes
    assert expected_supportability_contracts <= supportability_contract_classes
    assert advisor_brief_facade_classes.isdisjoint(expected_item_contracts)
    assert advisor_brief_facade_classes.isdisjoint(expected_supportability_contracts)


def test_advisor_brief_response_example_lives_outside_contract_model() -> None:
    advisor_brief_assignments = _assigned_names(_CONTRACT_ROOT / "advisor_brief.py")
    example_assignments = _assigned_names(_CONTRACT_ROOT / "advisor_brief_examples.py")

    assert "ADVISOR_BRIEF_RESPONSE_EXAMPLE" in example_assignments
    assert "ADVISOR_BRIEF_RESPONSE_EXAMPLE" not in advisor_brief_assignments


def test_proposal_lifecycle_contracts_live_outside_proposals_facade() -> None:
    proposal_facade_classes = _class_names(_CONTRACT_ROOT / "proposals.py")
    lifecycle_facade_classes = _class_names(_CONTRACT_ROOT / "proposal_lifecycle.py")
    summary_contract_classes = _class_names(_CONTRACT_ROOT / "proposal_lifecycle_summary.py")
    workflow_contract_classes = _class_names(_CONTRACT_ROOT / "proposal_lifecycle_workflow.py")
    lineage_contract_classes = _class_names(_CONTRACT_ROOT / "proposal_lifecycle_lineage.py")
    envelope_contract_classes = _class_names(_CONTRACT_ROOT / "proposal_lifecycle_envelopes.py")

    expected_summary_contracts = {
        "ProposalSummaryData",
        "ProposalVersionData",
    }
    expected_workflow_contracts = {
        "ProposalApprovalsData",
        "ProposalApprovalRecordData",
        "ProposalWorkflowEventData",
        "ProposalWorkflowEventsData",
    }
    expected_lineage_contracts = {
        "ProposalLineageData",
        "ProposalVersionLineageItemData",
    }
    expected_envelope_contracts = {
        "ProposalApprovalsEnvelopeResponse",
        "ProposalCreateData",
        "ProposalCreateEnvelopeResponse",
        "ProposalLineageEnvelopeResponse",
        "ProposalStateTransitionData",
        "ProposalStateTransitionEnvelopeResponse",
        "ProposalVersionEnvelopeResponse",
        "ProposalWorkflowEventsEnvelopeResponse",
    }
    expected_lifecycle_contracts = (
        expected_summary_contracts
        | expected_workflow_contracts
        | expected_lineage_contracts
        | expected_envelope_contracts
    )

    assert expected_summary_contracts <= summary_contract_classes
    assert expected_workflow_contracts <= workflow_contract_classes
    assert expected_lineage_contracts <= lineage_contract_classes
    assert expected_envelope_contracts <= envelope_contract_classes
    assert lifecycle_facade_classes.isdisjoint(expected_lifecycle_contracts)
    assert proposal_facade_classes.isdisjoint(expected_lifecycle_contracts)


def test_workbench_contracts_live_outside_workbench_facade() -> None:
    workbench_facade_classes = _class_names(_CONTRACT_ROOT / "workbench.py")
    common_contract_classes = _class_names(_CONTRACT_ROOT / "workbench_common.py")
    overview_contract_classes = _class_names(_CONTRACT_ROOT / "workbench_overview.py")
    sandbox_contract_classes = _class_names(_CONTRACT_ROOT / "workbench_sandbox.py")

    expected_common_contracts = {
        "WorkbenchOverviewSummary",
        "WorkbenchPartialFailure",
        "WorkbenchPerformanceSnapshot",
        "WorkbenchPortfolioSummary",
        "WorkbenchPositionView",
        "WorkbenchProjectedPositionView",
        "WorkbenchProjectedSummary",
        "WorkbenchRebalanceRunSummary",
        "WorkbenchRebalanceSnapshot",
    }
    expected_overview_contracts = {
        "WorkbenchOverviewResponse",
        "WorkbenchPortfolio360Response",
    }
    expected_sandbox_contracts = {
        "WorkbenchAnalyticsBucket",
        "WorkbenchAnalyticsResponse",
        "WorkbenchPolicyFeedback",
        "WorkbenchSandboxApplyChangesRequest",
        "WorkbenchSandboxChangeInput",
        "WorkbenchSandboxSessionCreateRequest",
        "WorkbenchSandboxStateResponse",
        "WorkbenchTopChange",
    }

    assert expected_common_contracts <= common_contract_classes
    assert expected_overview_contracts <= overview_contract_classes
    assert expected_sandbox_contracts <= sandbox_contract_classes
    assert workbench_facade_classes == set()


def test_portfolio_workspace_control_contracts_live_outside_workspace_facade() -> None:
    portfolio_workspace_facade_classes = _class_names(_CONTRACT_ROOT / "portfolio_workspace.py")
    control_contract_classes = _class_names(_CONTRACT_ROOT / "portfolio_workspace_controls.py")

    expected_control_contracts = {
        "PortfolioWorkspaceControlCapabilities",
        "PortfolioWorkspaceHistoricalSnapshotCapability",
        "PortfolioWorkspaceModuleCapability",
        "PortfolioWorkspaceReportingCurrencyCapability",
    }

    assert expected_control_contracts <= control_contract_classes
    assert portfolio_workspace_facade_classes.isdisjoint(expected_control_contracts)


def test_portfolio_position_book_contracts_live_outside_holdings_facade() -> None:
    portfolio_holdings_facade_classes = _class_names(_CONTRACT_ROOT / "portfolio_holdings.py")
    position_book_contract_classes = _class_names(_CONTRACT_ROOT / "portfolio_position_book.py")

    expected_position_book_contracts = {
        "PortfolioPositionBookResponse",
        "PortfolioPositionView",
        "PortfolioTopPosition",
    }

    assert expected_position_book_contracts <= position_book_contract_classes
    assert portfolio_holdings_facade_classes.isdisjoint(expected_position_book_contracts)


def test_domain_product_trust_contracts_live_outside_domain_products_facade() -> None:
    domain_products_facade_classes = _class_names(_CONTRACT_ROOT / "domain_products.py")
    trust_contract_classes = _class_names(_CONTRACT_ROOT / "domain_product_trust.py")

    expected_trust_contracts = {
        "DomainProductLiveTrustCertification",
        "DomainProductLiveTrustIssue",
        "DomainProductLiveTrustSummary",
        "DomainProductTrustCertificationData",
        "DomainProductTrustCertificationResponse",
    }

    assert expected_trust_contracts <= trust_contract_classes
    assert domain_products_facade_classes.isdisjoint(expected_trust_contracts)


def test_reporting_batch_contracts_live_outside_reporting_batches_facade() -> None:
    reporting_batches_facade_classes = _class_names(_CONTRACT_ROOT / "reporting_batches.py")
    materialization_contract_classes = _class_names(
        _CONTRACT_ROOT / "reporting_batch_materialization.py"
    )
    worker_contract_classes = _class_names(_CONTRACT_ROOT / "reporting_batch_worker.py")
    scheduler_contract_classes = _class_names(_CONTRACT_ROOT / "reporting_batch_scheduler.py")

    expected_materialization_contracts = {
        "BatchControlResponse",
        "BatchCreateRequest",
        "BatchHandleResponse",
        "BatchItemStatusResponse",
        "BatchRecoveryResponse",
        "BatchStatusResponse",
        "PortfolioBatchCandidate",
        "RenderSupportabilitySummary",
        "ReportingEvidenceSurfaceSupportability",
    }
    expected_worker_contracts = {
        "BatchDispatchPolicy",
        "BatchRuntimeLoad",
        "BatchWorkerItemExecutionResponse",
        "BatchWorkerRunRequest",
        "BatchWorkerRunResponse",
    }
    expected_scheduler_contracts = {
        "BatchScheduleListResponse",
        "BatchScheduleSummaryResponse",
        "BatchSchedulerMaterializationResponse",
        "BatchSchedulerRunRequest",
        "BatchSchedulerRunResponse",
    }

    assert expected_materialization_contracts <= materialization_contract_classes
    assert expected_worker_contracts <= worker_contract_classes
    assert expected_scheduler_contracts <= scheduler_contract_classes
    assert reporting_batches_facade_classes.isdisjoint(expected_materialization_contracts)
    assert reporting_batches_facade_classes.isdisjoint(expected_worker_contracts)
    assert reporting_batches_facade_classes.isdisjoint(expected_scheduler_contracts)


def test_reporting_job_contracts_live_outside_reporting_facade() -> None:
    reporting_facade_classes = _class_names(_CONTRACT_ROOT / "reporting.py")
    reporting_job_contract_classes = _class_names(_CONTRACT_ROOT / "reporting_jobs.py")

    expected_reporting_job_contracts = {
        "OutcomeReviewReportJobRequest",
        "PortfolioReviewJobRequest",
        "ReportJobErrorDetail",
        "ReportJobErrorResponse",
        "ReportJobHandleResponse",
        "ReportJobStatusResponse",
    }

    assert expected_reporting_job_contracts <= reporting_job_contract_classes
    assert reporting_facade_classes.isdisjoint(expected_reporting_job_contracts)
