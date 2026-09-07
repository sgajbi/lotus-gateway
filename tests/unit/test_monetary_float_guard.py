from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_guard_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_monetary_float_usage.py"
    spec = importlib.util.spec_from_file_location("check_monetary_float_usage", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_scan_repo_ignores_local_virtualenv_directories(tmp_path: Path) -> None:
    guard = _load_guard_module()
    product_file = tmp_path / "src" / "app" / "services" / "portfolio_service.py"
    product_file.parent.mkdir(parents=True)
    product_file.write_text("market_value: float = 1.0\n", encoding="utf-8")

    virtualenv_file = tmp_path / ".venv-codex" / "Lib" / "site-packages" / "vendor.py"
    virtualenv_file.parent.mkdir(parents=True)
    virtualenv_file.write_text("market_value: float = 1.0\n", encoding="utf-8")

    findings = guard.scan_repo(tmp_path)

    assert findings == ["src/app/services/portfolio_service.py:1:market_value: float = 1.0"]


def test_a_comment_naming_the_hazard_is_not_a_use_of_it(tmp_path: Path) -> None:
    """Prose explaining the rule must not trip the rule.

    A comment cannot introduce a monetary float, and flagging one teaches authors
    to reword explanations to satisfy the guard rather than trust it. This exact
    line failed CI: an explanation of why a float value must not bind an integer
    setting, in a file about branch protection, with no money anywhere in it.

    Both directions are asserted, because a guard that stopped catching real
    usage would be a worse outcome than the false positive it fixes.
    """
    guard = _load_guard_module()
    source = tmp_path / "src" / "app" / "services" / "policy.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            (
                "# a float value would bind an integer setting and be treated as equal",
                "    # indented prose about market_value as a float is still prose",
                "market_value: float = 1.0",
                "price: float = 2.0  # a trailing comment leaves real code before the hash",
                "",
            )
        ),
        encoding="utf-8",
    )

    findings = guard.scan_repo(tmp_path)

    assert findings == [
        "src/app/services/policy.py:3:market_value: float = 1.0",
        "src/app/services/policy.py:4:price: float = 2.0  "
        "# a trailing comment leaves real code before the hash",
    ], findings


def test_allowlist_matching_tolerates_line_number_shift(tmp_path: Path) -> None:
    guard = _load_guard_module()
    product_file = tmp_path / "src" / "app" / "services" / "portfolio_service.py"
    product_file.parent.mkdir(parents=True)
    product_file.write_text("import asyncio\nmarket_value: float = 1.0\n", encoding="utf-8")
    allowlist_file = tmp_path / "docs" / "standards" / "monetary-float-allowlist.json"
    allowlist_file.parent.mkdir(parents=True)
    allowlist_file.write_text(
        """
{
  "allowlist": [
    {
      "finding": "src/app/services/portfolio_service.py:1:market_value: float = 1.0",
      "justification": "Approved baseline.",
      "owner": "platform-governance",
      "review_by": "2099-01-01"
    }
  ]
}
""".lstrip(),
        encoding="utf-8",
    )

    findings = guard.scan_repo(tmp_path)
    allowlist_entries, errors, stale_entries = guard.load_allowlist(allowlist_file)

    assert errors == []
    assert stale_entries == []
    assert findings == ["src/app/services/portfolio_service.py:2:market_value: float = 1.0"]
    assert guard.find_unapproved_findings(findings, allowlist_entries) == []


def test_allowlist_matching_keeps_duplicate_findings_bounded() -> None:
    guard = _load_guard_module()
    allowlist_entries = {
        "src/app/services/portfolio_service.py:1:market_value: float = 1.0": {
            "finding": "src/app/services/portfolio_service.py:1:market_value: float = 1.0",
            "justification": "Approved baseline.",
            "owner": "platform-governance",
            "review_by": "2099-01-01",
        },
        "src/app/services/portfolio_service.py:3:market_value: float = 1.0": {
            "finding": "src/app/services/portfolio_service.py:3:market_value: float = 1.0",
            "justification": "Approved baseline.",
            "owner": "platform-governance",
            "review_by": "2099-01-01",
        },
    }
    shifted_findings = [
        "src/app/services/portfolio_service.py:2:market_value: float = 1.0",
        "src/app/services/portfolio_service.py:4:market_value: float = 1.0",
        "src/app/services/portfolio_service.py:6:market_value: float = 1.0",
    ]

    assert guard.find_unapproved_findings(shifted_findings, allowlist_entries) == [
        "src/app/services/portfolio_service.py:6:market_value: float = 1.0"
    ]


def test_write_allowlist_preserves_metadata_when_line_number_shifts(tmp_path: Path) -> None:
    guard = _load_guard_module()
    allowlist_file = tmp_path / "monetary-float-allowlist.json"
    existing_entries = {
        "src/app/services/portfolio_service.py:1:market_value: float = 1.0": {
            "finding": "src/app/services/portfolio_service.py:1:market_value: float = 1.0",
            "justification": "Approved baseline.",
            "owner": "platform-governance",
            "review_by": "2099-01-01",
        }
    }

    guard.write_allowlist(
        allowlist_file,
        ["src/app/services/portfolio_service.py:2:market_value: float = 1.0"],
        existing_entries,
        "2099-12-31",
    )

    refreshed_entries, errors, stale_entries = guard.load_allowlist(allowlist_file)

    assert errors == []
    assert stale_entries == []
    assert refreshed_entries[
        "src/app/services/portfolio_service.py:2:market_value: float = 1.0"
    ] == {
        "finding": "src/app/services/portfolio_service.py:2:market_value: float = 1.0",
        "justification": "Approved baseline.",
        "owner": "platform-governance",
        "review_by": "2099-01-01",
    }
