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

import yaml

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


def _runs_on_commit(stages: object) -> bool:
    """Whether a resolved stages list still includes the ordinary commit run.

    pre-commit accepts both the modern `pre-commit` name and the legacy `commit`
    name, so either counts. An empty list runs nothing.
    """
    if stages is None:
        return True
    names = {str(stage).strip() for stage in stages}
    return bool(names & {"pre-commit", "commit"})


def _hook_revisions() -> dict[str, str]:
    """Versions pre-commit resolves, for tools whose hooks all run on commit.

    A revision is credited only when EVERY hook the tool needs is present and
    runs on an ordinary commit. A `rev:` proves a repository stanza is listed,
    not that its hooks execute -- a stanza whose hook was removed, renamed,
    commented out or moved to another stage still carries its revision.

    Parsed with a real YAML parser rather than scanned line by line. That was a
    deliberate reversal: reading two fields by hand was proportionate, but
    correctness here needs actual YAML semantics -- block sequences (`stages:`
    followed by `- pre-commit` on its own line), quoting, and mapping order,
    since a `default_stages` written after `repos` applies to hooks declared
    before it. Four consecutive review findings were all the hand scanner
    mishandling valid configurations, and each fix added a branch that attracted
    the next one. A parser is what this needs.
    """
    document = yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8")) or {}

    # Resolved after the whole document is read, because mapping order carries
    # no meaning: a default declared last still governs hooks declared first.
    default_stages = document.get("default_stages")

    revisions: dict[str, str] = {}
    for repository in document.get("repos", []) or []:
        source = str(repository.get("repo", ""))
        revision = str(repository.get("rev", "")).lstrip("v")
        if not revision:
            continue

        runs: dict[str, bool] = {}
        hooks = repository.get("hooks") or []
        if not isinstance(hooks, list):
            # A malformed stanza describes no runnable hook, so it credits
            # nothing rather than crashing the gate on someone's typo.
            continue
        for hook in hooks:
            if not isinstance(hook, dict):
                continue
            identifier = str(hook.get("id", ""))
            if not identifier:
                continue
            # A per-hook `stages` OVERRIDES the file default; absent, the hook
            # inherits it.
            runs[identifier] = _runs_on_commit(hook.get("stages", default_stages))

        for tool, required in REQUIRED_HOOKS.items():
            if tool in source and all(runs.get(hook, False) for hook in required):
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

    # Whole hook blocks, not just their id lines: leaving an orphaned `args:`
    # behind would make `hooks:` a mapping rather than a list, and the case would
    # then be exercising a malformed file instead of a removed hook.
    mypy_hook = '      - id: mypy\n        args: ["src"]\n'

    removed = baseline.replace(mypy_hook, "")
    assert "mypy" not in parse(removed), "a removed hook must not be credited"

    commented = baseline.replace(mypy_hook, '      # - id: mypy\n      #   args: ["src"]\n')
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


def _parse_config(text: str, tmp_path, monkeypatch) -> dict[str, str]:
    written = tmp_path / "pre-commit.yaml"
    written.write_text(text, encoding="utf-8")
    monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)
    return _hook_revisions()


def test_a_default_declared_after_the_repos_still_applies(tmp_path, monkeypatch) -> None:
    """YAML mapping order carries no meaning.

    A `default_stages` written below `repos:` governs hooks declared above it.
    Reading the file top to bottom and snapshotting the default as each hook is
    encountered gets this wrong, and the result is a config pre-commit treats as
    disabled while the check reports the gates agreeing.
    """
    config = """
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.3.1
    hooks:
      - id: mypy
default_stages: [manual]
"""
    assert _parse_config(config, tmp_path, monkeypatch) == {}, (
        "a default declared after the repos still disables them"
    )


def test_block_style_stage_sequences_are_read(tmp_path, monkeypatch) -> None:
    """`stages:` with items on following lines is ordinary YAML.

    Treating only the inline `[...]` form as a stage list makes a valid
    block-style config look like a hook with no stages, so a hook that does run
    on commit is rejected -- a checker failing correct configuration.
    """
    block_style = """
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.3.1
    hooks:
      - id: mypy
        stages:
          - pre-commit
"""
    assert _parse_config(block_style, tmp_path, monkeypatch).get("mypy") == "2.3.1", (
        "a block-style stages list naming the commit stage must be credited"
    )

    block_manual = block_style.replace("          - pre-commit", "          - manual")
    assert _parse_config(block_manual, tmp_path, monkeypatch) == {}, (
        "and a block-style list naming another stage must not be"
    )
