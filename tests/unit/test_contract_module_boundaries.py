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
