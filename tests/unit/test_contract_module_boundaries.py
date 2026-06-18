import ast
from pathlib import Path

_CONTRACT_ROOT = Path(__file__).parents[2] / "src" / "app" / "contracts"


def _class_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


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


def test_proposal_lifecycle_contracts_live_outside_proposals_facade() -> None:
    proposal_facade_classes = _class_names(_CONTRACT_ROOT / "proposals.py")
    lifecycle_contract_classes = _class_names(_CONTRACT_ROOT / "proposal_lifecycle.py")

    expected_lifecycle_contracts = {
        "ProposalApprovalsData",
        "ProposalApprovalsEnvelopeResponse",
        "ProposalApprovalRecordData",
        "ProposalCreateData",
        "ProposalCreateEnvelopeResponse",
        "ProposalLineageData",
        "ProposalLineageEnvelopeResponse",
        "ProposalStateTransitionData",
        "ProposalStateTransitionEnvelopeResponse",
        "ProposalSummaryData",
        "ProposalVersionData",
        "ProposalVersionEnvelopeResponse",
        "ProposalVersionLineageItemData",
        "ProposalWorkflowEventData",
        "ProposalWorkflowEventsData",
        "ProposalWorkflowEventsEnvelopeResponse",
    }

    assert expected_lifecycle_contracts <= lifecycle_contract_classes
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
