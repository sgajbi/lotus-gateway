"""The lint and type-check toolchain must be one version, not two.

`pyproject.toml` decides what CI installs. `.pre-commit-config.yaml` decides what
a developer's commit hook runs, and pre-commit resolves each hook into its own
isolated environment from `rev:` — it never reads the project's dependencies.
Nothing connects the two files, so they drift silently and each gate keeps
reporting confidently.

That is a correctness problem rather than hygiene, because a formatter's OUTPUT
is its contract. Two versions can disagree about what "formatted" means, and
then one gate's clean run and the other's failure are both true. A sibling
repository measured 665 files clean under one pin and three files needing
reformatting under another, on the same unchanged tree, and a commit message
there recorded "three pre-existing format failures" that did not exist under the
enforced version. The number was real; the conclusion was not.

This repository had the same drift latent: pre-commit ran ruff v0.15.1 while
`pyproject` admitted anything in `>=0.15.15,<0.16` — a rev that did not even
satisfy the project's own floor — and pre-commit pinned mypy v1.13.0 while an
open `mypy>=1.13.0` floor let CI resolve 2.3.1. Two major versions apart on a
type checker, where a newer release finding new errors on unchanged code is
indistinguishable from a regression.

The check compares the two SOURCES rather than asserting a literal version, so
bumping either file fails until the other is bumped in the same change.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
PRE_COMMIT = REPO_ROOT / ".pre-commit-config.yaml"

# Tools whose output is the contract, so two versions can disagree about a
# verdict on identical code. Both must be exactly pinned and identical across
# the two files.
OUTPUT_DEFINING_TOOLS = ("ruff", "mypy")

_EXACT_PIN = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[0-9][^\s,;]*)$")


def _declared_pins() -> dict[str, str]:
    """Exact versions pyproject declares for the output-defining tools."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dev = data["project"]["optional-dependencies"]["dev"]

    pins: dict[str, str] = {}
    for requirement in dev:
        match = _EXACT_PIN.match(requirement.strip())
        if match and match.group("name").lower() in OUTPUT_DEFINING_TOOLS:
            pins[match.group("name").lower()] = match.group("version")
    return pins


def _hook_revisions() -> dict[str, str]:
    """Versions pre-commit resolves, keyed by the tool the repo provides.

    Read line by line rather than with a YAML parser: this repository declares no
    YAML dependency, and buying one to read two fields would be a dependency
    added for a single call.
    """
    # A revision is only recorded once the stanza is known to RUN the hook. A
    # repository stanza whose hook has been removed, renamed, commented out or
    # restricted to a non-default stage still carries a `rev:`, and accepting it
    # would let this comparison pass while pre-commit runs nothing -- a gate
    # agreeing with a tool that is not there.
    revisions: dict[str, str] = {}
    current_repo = ""
    pending_revision = ""
    enabled_hooks: set[str] = set()
    last_hook = ""

    def record() -> None:
        for tool in OUTPUT_DEFINING_TOOLS:
            if tool in current_repo and pending_revision and tool in enabled_hooks:
                revisions[tool] = pending_revision

    for line in PRE_COMMIT.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            # A commented-out hook does not run, so it must not be credited.
            continue
        if stripped.startswith("- repo:"):
            record()
            current_repo = stripped.partition("- repo:")[2].strip()
            pending_revision = ""
            enabled_hooks = set()
            last_hook = ""
        elif stripped.startswith("rev:"):
            pending_revision = stripped.partition("rev:")[2].strip().lstrip("v")
        elif stripped.startswith("- id:"):
            last_hook = stripped.partition("- id:")[2].strip()
            enabled_hooks.add(last_hook)
        elif stripped.startswith("stages:") and last_hook:
            # A hook restricted to explicit stages does not run on an ordinary
            # commit, so it cannot be credited as the version developers get.
            enabled_hooks.discard(last_hook)
    record()
    return revisions


def test_every_output_defining_tool_is_exactly_pinned() -> None:
    """A range lets CI resolve a version no one chose.

    An open floor is the obvious case, but a bounded range drifts too: the newest
    release inside it arrives without a commit, so main can turn red with no code
    change and the cause is invisible in the diff.
    """
    pins = _declared_pins()

    missing = [tool for tool in OUTPUT_DEFINING_TOOLS if tool not in pins]
    assert not missing, (
        f"{', '.join(missing)} must be pinned exactly in pyproject's dev extra "
        "(name==version); a range lets CI resolve a version nobody chose"
    )


def test_pre_commit_runs_the_same_versions_ci_enforces() -> None:
    """The two sources are compared, so neither can be bumped alone."""
    pins = _declared_pins()
    revisions = _hook_revisions()

    # Without this the loop below iterates nothing when the pins are ranges, and
    # the comparison passes while comparing no versions at all -- a zero-input
    # pass, which is the failure mode this whole file exists to describe.
    assert set(pins) == set(OUTPUT_DEFINING_TOOLS), (
        f"expected an exact pin for each of {', '.join(OUTPUT_DEFINING_TOOLS)}, found "
        f"{sorted(pins) or 'none'}; with nothing pinned there is nothing to compare"
    )

    for tool, pinned in sorted(pins.items()):
        assert tool in revisions, (
            f"pyproject pins {tool}=={pinned} but .pre-commit-config.yaml declares no "
            f"{tool} hook, so the commit hook and CI check different things"
        )
        assert revisions[tool] == pinned, (
            f"{tool} disagrees between the gates: pyproject enforces {pinned} and "
            f"pre-commit runs {revisions[tool]}. A formatter or type checker's output "
            "is its contract, so both gates would report confidently and disagree. "
            "Bump both in the same change."
        )


def test_a_removed_or_disabled_hook_is_not_credited(tmp_path, monkeypatch) -> None:
    """A `rev:` proves a repository is listed, not that its hook runs.

    A stanza whose hook has been removed, renamed, commented out or restricted to
    another stage still carries its revision. Crediting it would let this
    comparison agree with a tool that is not running -- the same shape as a
    dispatch tag being read as proof a gate passed.
    """
    baseline = PRE_COMMIT.read_text(encoding="utf-8")

    def parse(config: str) -> dict[str, str]:
        written = tmp_path / "pre-commit.yaml"
        written.write_text(config, encoding="utf-8")
        monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)
        return _hook_revisions()

    assert parse(baseline).get("mypy"), "the real config must credit its mypy hook"

    removed = baseline.replace("      - id: mypy\n", "")
    assert "mypy" not in parse(removed), "a removed hook must not be credited"

    commented = baseline.replace("      - id: mypy", "      # - id: mypy")
    assert "mypy" not in parse(commented), "a commented-out hook must not be credited"

    staged = baseline.replace("      - id: mypy\n", "      - id: mypy\n        stages: [manual]\n")
    assert "mypy" not in parse(staged), "a hook restricted to another stage does not run on commit"
