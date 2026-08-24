"""Reconcile Gateway proposal policy with the source-owned Advise vocabulary."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from app.contracts.proposal_decision_vocabulary import (  # noqa: E402
    ProposalDecisionVocabulary,
    load_proposal_decision_vocabulary,
    parse_proposal_decision_vocabulary,
)

DEFAULT_SOURCE_URL_ENV = "LOTUS_ADVISE_PROPOSAL_DECISION_VOCABULARY_URL"


def compare_vocabularies(
    packaged: ProposalDecisionVocabulary,
    source: ProposalDecisionVocabulary,
) -> list[str]:
    """Return stable, pairing-specific drift findings."""

    findings = _metadata_differences(packaged, source)
    findings.extend(
        _mapping_differences(
            "decision top-level statuses",
            packaged.decision_status_top_levels,
            source.decision_status_top_levels,
        )
    )
    findings.extend(
        _mapping_differences(
            "decision recommended actions",
            packaged.decision_status_next_actions,
            source.decision_status_next_actions,
        )
    )
    findings.extend(
        _mapping_differences(
            "decision workflow gates",
            packaged.decision_status_workflow_gates,
            source.decision_status_workflow_gates,
        )
    )
    findings.extend(
        _mapping_differences(
            "workflow gate next steps",
            packaged.workflow_gate_next_steps,
            source.workflow_gate_next_steps,
        )
    )
    return findings


def _metadata_differences(
    packaged: ProposalDecisionVocabulary,
    source: ProposalDecisionVocabulary,
) -> list[str]:
    fields = (
        "schema_version",
        "contract_version",
        "source_service",
        "source_authority",
        "source_rule_modules",
    )
    return [
        f"proposal decision vocabulary {field} differs: "
        f"packaged={getattr(packaged, field)!r}, source={getattr(source, field)!r}"
        for field in fields
        if getattr(packaged, field) != getattr(source, field)
    ]


def _mapping_differences(
    label: str,
    packaged: Mapping[str, object],
    source: Mapping[str, object],
) -> list[str]:
    findings: list[str] = []
    for key in sorted(set(packaged) | set(source)):
        packaged_value = _ordered_value(packaged.get(key))
        source_value = _ordered_value(source.get(key))
        if packaged_value != source_value:
            findings.append(
                f"{label} differ for {key}: packaged={packaged_value}, source={source_value}"
            )
    return findings


def _ordered_value(value: object) -> object:
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    return value


def fetch_github_contents_contract(url: str) -> tuple[dict[str, Any], str]:
    """Fetch one public GitHub contents artifact and return payload plus blob revision."""

    headers = {"Accept": "application/vnd.github+json", "User-Agent": "lotus-gateway-ci"}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:  # noqa: S310
        envelope = json.load(response)
    return _decode_github_contents_envelope(envelope)


def _decode_github_contents_envelope(envelope: object) -> tuple[dict[str, Any], str]:
    if not isinstance(envelope, dict):
        raise ValueError("GitHub contents response must be an object")
    encoded = envelope.get("content")
    revision = envelope.get("sha")
    if envelope.get("encoding") != "base64" or not isinstance(encoded, str):
        raise ValueError("GitHub contents response must contain base64 artifact content")
    if not isinstance(revision, str) or not revision:
        raise ValueError("GitHub contents response must contain the source blob revision")
    payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("source proposal decision vocabulary must be a JSON object")
    return payload, revision


def _source_vocabulary(args: argparse.Namespace) -> tuple[ProposalDecisionVocabulary, str]:
    if args.source_contract is not None:
        return load_proposal_decision_vocabulary(args.source_contract), str(args.source_contract)
    source_url = args.source_url or os.getenv(DEFAULT_SOURCE_URL_ENV)
    if source_url:
        payload, revision = fetch_github_contents_contract(source_url)
        return parse_proposal_decision_vocabulary(payload), f"github-blob:{revision}"
    if args.allow_packaged_snapshot:
        return load_proposal_decision_vocabulary(), "packaged-snapshot-explicit"
    raise ValueError(
        "current Advise proposal decision vocabulary is required; pass --source-contract, "
        f"--source-url, or set {DEFAULT_SOURCE_URL_ENV}. Use --allow-packaged-snapshot only "
        "for an explicit offline package-integrity check."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare Gateway proposal policy with the Advise vocabulary artifact."
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--source-contract", type=Path)
    source_group.add_argument("--source-url")
    source_group.add_argument("--allow-packaged-snapshot", action="store_true")
    args = parser.parse_args(argv)
    packaged = load_proposal_decision_vocabulary()
    source, source_revision = _source_vocabulary(args)
    findings = compare_vocabularies(packaged, source)
    if findings:
        print(f"Proposal decision vocabulary gate failed: source={source_revision}")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"Proposal decision vocabulary gate passed: source={source_revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
