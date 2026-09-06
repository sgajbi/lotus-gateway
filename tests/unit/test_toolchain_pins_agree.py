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
#
# The hook ids are every hook that tool needs for pre-commit to cover what CI
# runs. The Makefile invokes `ruff check` AND `ruff format --check`, so a config
# keeping `- id: ruff` while dropping `- id: ruff-format` leaves the formatter
# unenforced locally while this comparison still saw a Ruff revision.
REQUIRED_HOOKS: dict[str, tuple[str, ...]] = {
    "ruff": ("ruff", "ruff-format"),
    "mypy": ("mypy",),
}
OUTPUT_DEFINING_TOOLS = tuple(REQUIRED_HOOKS)

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


def _runs_on_commit(stages: str) -> bool:
    """Whether a stages list still includes the ordinary commit run.

    pre-commit accepts both the modern `pre-commit` name and the legacy `commit`
    name, so either counts. An empty list runs nothing.
    """
    names = {token.strip().strip("[]'\"") for token in stages.split(",")}
    names.discard("")
    return bool(names & {"pre-commit", "commit"})


def _hook_revisions() -> dict[str, str]:
    """Versions pre-commit resolves, for tools whose hooks all run on commit.

    Read line by line rather than with a YAML parser: this repository declares no
    YAML dependency, and buying one to read a handful of fields would be a
    dependency added for a single call.

    A revision is credited only when EVERY hook the tool needs is present and
    runs on an ordinary commit. A `rev:` proves a repository stanza is listed,
    not that its hooks execute -- a stanza whose hook was removed, renamed,
    commented out or moved to another stage still carries its revision.

    Stage resolution follows pre-commit's own rule rather than a shortcut: a
    per-hook `stages:` OVERRIDES the file-level `default_stages`. Treating a
    manual default as disabling everything would reject the valid combination of
    a manual default with explicit per-hook overrides -- a checker failing a
    correct config, which is how checkers stop being read.
    """
    default_runs_on_commit = True
    repositories: list[tuple[str, str, dict[str, bool]]] = []
    current_repo = ""
    pending_revision = ""
    hooks: dict[str, bool] = {}
    last_hook = ""

    def close_repo() -> None:
        if current_repo:
            repositories.append((current_repo, pending_revision, dict(hooks)))

    for line in PRE_COMMIT.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            # A commented-out hook does not run, so it must not be credited.
            continue
        top_level = line[:1] not in (" ", "\t", "")
        if top_level and stripped.startswith("default_stages:"):
            default_runs_on_commit = _runs_on_commit(stripped.partition("default_stages:")[2])
        elif stripped.startswith("- repo:"):
            close_repo()
            current_repo = stripped.partition("- repo:")[2].strip()
            pending_revision = ""
            hooks = {}
            last_hook = ""
        elif stripped.startswith("rev:"):
            pending_revision = stripped.partition("rev:")[2].strip().lstrip("v")
        elif stripped.startswith("- id:"):
            last_hook = stripped.partition("- id:")[2].strip()
            hooks[last_hook] = default_runs_on_commit
        elif stripped.startswith("stages:") and last_hook:
            hooks[last_hook] = _runs_on_commit(stripped.partition("stages:")[2])
    close_repo()

    revisions: dict[str, str] = {}
    for tool, required in REQUIRED_HOOKS.items():
        for repository, revision, repo_hooks in repositories:
            if tool not in repository or not revision:
                continue
            if all(repo_hooks.get(hook, False) for hook in required):
                revisions[tool] = revision
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


def test_top_level_default_stages_can_disable_everything(tmp_path, monkeypatch) -> None:
    """A file-wide default_stages excluding the commit makes every hook inert.

    The per-hook branch cannot see this: it only fires after a hook id, so a
    setting at the top of the file would leave every hook credited while none of
    them runs on a developer's commit.
    """
    baseline = PRE_COMMIT.read_text(encoding="utf-8")

    def parse(config: str) -> dict[str, str]:
        written = tmp_path / "pre-commit.yaml"
        written.write_text(config, encoding="utf-8")
        monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)
        return _hook_revisions()

    assert parse(baseline), "the real config must credit its hooks"

    disabled = "default_stages: [manual]\n" + baseline
    assert parse(disabled) == {}, "a manual-only default must credit nothing"

    still_running = "default_stages: [pre-commit]\n" + baseline
    assert parse(still_running), "a default that includes the commit stage still counts"

    legacy_name = "default_stages: [commit]\n" + baseline
    assert parse(legacy_name), "pre-commit's legacy stage name still counts"


def test_every_hook_ci_runs_must_be_present(tmp_path, monkeypatch) -> None:
    """Ruff needs both hooks, because CI runs both commands.

    The Makefile invokes `ruff check` and `ruff format --check`. A config keeping
    `- id: ruff` while dropping `- id: ruff-format` leaves the formatter
    unenforced locally, and crediting the Ruff revision anyway would report the
    two gates as agreeing about a command one of them no longer runs.
    """
    baseline = PRE_COMMIT.read_text(encoding="utf-8")

    def parse(config: str) -> dict[str, str]:
        written = tmp_path / "pre-commit.yaml"
        written.write_text(config, encoding="utf-8")
        monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)
        return _hook_revisions()

    assert parse(baseline).get("ruff"), "the real config runs both Ruff hooks"

    without_formatter = baseline.replace("      - id: ruff-format\n", "")
    assert "ruff" not in parse(without_formatter), (
        "dropping the formatter hook must stop crediting Ruff"
    )

    formatter_staged = baseline.replace(
        "      - id: ruff-format\n",
        "      - id: ruff-format\n        stages: [manual]\n",
    )
    assert "ruff" not in parse(formatter_staged), (
        "a formatter moved off the commit stage is not enforced on commit"
    )
    assert parse(formatter_staged).get("mypy"), "and mypy is unaffected by Ruff's hooks"


def test_a_per_hook_stage_overrides_the_file_default(tmp_path, monkeypatch) -> None:
    """pre-commit resolves per-hook stages OVER default_stages.

    A manual file default paired with explicit per-hook overrides is a valid
    configuration that does run on commit. Treating the default as disabling
    everything would fail a correct config, which is how a checker earns the
    habit of being ignored.
    """
    baseline = PRE_COMMIT.read_text(encoding="utf-8")

    def parse(config: str) -> dict[str, str]:
        written = tmp_path / "pre-commit.yaml"
        written.write_text(config, encoding="utf-8")
        monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)
        return _hook_revisions()

    overridden = "default_stages: [manual]\n" + baseline.replace(
        "      - id: mypy\n", "      - id: mypy\n        stages: [pre-commit]\n"
    )
    assert parse(overridden).get("mypy"), "an explicit per-hook stage still runs on commit"
    assert "ruff" not in parse(overridden), "hooks without an override follow the manual default"
