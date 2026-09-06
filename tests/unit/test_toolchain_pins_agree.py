"""The lint and type-check toolchain must be one version, not two.

`pyproject.toml` decides what CI installs. `.pre-commit-config.yaml` decides what
a developer's commit hook runs, and pre-commit resolves each hook into its own
isolated environment from `rev:` — it never reads the project's dependencies.
Nothing connects the two files, so they drift silently and each gate keeps
reporting confidently.

That is a correctness problem rather than hygiene, because a formatter's OUTPUT
is its contract. Two versions can disagree about what "formatted" means, and then
one gate's clean run and the other's failure are both true. A sibling repository
measured 665 files clean under one pin and three needing reformatting under
another on the same unchanged tree, and a commit message there recorded "three
pre-existing format failures" that did not exist under the enforced version. The
number was real; the conclusion was not.

This repository had the same drift latent: pre-commit ran ruff v0.15.1 while
`pyproject` admitted anything in `>=0.15.15,<0.16` — a rev that did not even
satisfy the project's own floor — and pre-commit pinned mypy v1.13.0 while an
open `mypy>=1.13.0` floor let CI resolve 2.3.1.

The two tools are held together in DIFFERENT ways, because their failure modes
differ:

* **ruff** is pinned by `rev`, and this file compares that rev to the pyproject
  pin. Ruff needs no project context, so an isolated hook environment runs it
  correctly.
* **mypy** runs from the PROJECT environment via a `local` hook. A mirrored hook
  resolves its own environment without the project's dependencies, so it cannot
  see fastapi or pydantic and reports import errors on every commit that CI does
  not. A sibling repository measured 586 errors in 233 files from such a hook
  against 385 files clean from CI, with the versions already matching. Matching
  the rev does not fix that — the version was never the problem.

What this file does NOT do is model pre-commit's file selection. `files`,
`exclude`, `types`, `types_or`, `exclude_types` and `always_run` interact in ways
that amount to reimplementing pre-commit, and an earlier revision that tried
produced five findings of which three were the check failing VALID configuration.
A checker that fails correct configuration teaches its reader to ignore it. Stage
exclusion is modelled because it is unambiguous; the rest is pre-commit's own
semantics and is deliberately out of scope.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
PRE_COMMIT = REPO_ROOT / ".pre-commit-config.yaml"

# Tools whose output is the contract, so two versions can disagree about a
# verdict on identical code. Every one must be pinned exactly in pyproject.
OUTPUT_DEFINING_TOOLS = ("ruff", "mypy")

# Hooks pinned by `rev`, with every hook id that tool needs for pre-commit to
# cover what CI runs. The Makefile invokes `ruff check` AND `ruff format
# --check`, so a config keeping `- id: ruff` while dropping `- id: ruff-format`
# leaves the formatter unenforced locally.
REV_PINNED_HOOKS: dict[str, tuple[str, ...]] = {"ruff": ("ruff", "ruff-format")}

# Tools that must run from the project environment instead, because they need
# the resolved dependency graph to produce a correct verdict.
PROJECT_ENVIRONMENT_TOOLS = ("mypy",)

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

    pre-commit accepts the modern `pre-commit` name and the legacy `commit` name,
    so either counts. An empty list runs nothing.
    """
    if stages is None:
        return True
    names = {str(stage).strip() for stage in stages}
    return bool(names & {"pre-commit", "commit"})


def _config() -> dict[str, object]:
    return yaml.safe_load(PRE_COMMIT.read_text(encoding="utf-8")) or {}


def _hooks_by_repository() -> list[tuple[str, str, list[dict[str, object]]]]:
    """(source, rev, hooks) per repository stanza, with malformed entries dropped.

    A malformed stanza describes no runnable hook, so it contributes nothing
    rather than crashing the gate on someone's typo.
    """
    stanzas: list[tuple[str, str, list[dict[str, object]]]] = []
    for repository in _config().get("repos", []) or []:
        if not isinstance(repository, dict):
            continue
        hooks = repository.get("hooks") or []
        if not isinstance(hooks, list):
            continue
        stanzas.append(
            (
                str(repository.get("repo", "")),
                str(repository.get("rev", "")).lstrip("v"),
                [hook for hook in hooks if isinstance(hook, dict)],
            )
        )
    return stanzas


def _hook_revisions() -> dict[str, str]:
    """Revisions for rev-pinned tools whose required hooks all run on commit.

    A `rev:` proves a repository stanza is listed, not that its hooks execute — a
    stanza whose hook was removed, renamed, commented out or moved to another
    stage still carries its revision.

    `default_stages` is applied after the whole document is read, because YAML
    mapping order carries no meaning: a default written below `repos` still
    governs hooks declared above it.
    """
    default_stages = _config().get("default_stages")

    revisions: dict[str, str] = {}
    for source, revision, hooks in _hooks_by_repository():
        if not revision:
            continue
        # A per-hook `stages` OVERRIDES the file default; absent, it inherits.
        runs = {
            str(hook.get("id", "")): _runs_on_commit(hook.get("stages", default_stages))
            for hook in hooks
            if hook.get("id")
        }
        for tool, required in REV_PINNED_HOOKS.items():
            if tool in source and all(runs.get(hook, False) for hook in required):
                if tool in revisions and revisions[tool] != revision:
                    # pre-commit runs BOTH stanzas. Taking the last match would
                    # hide an obsolete revision that still executes on every
                    # commit, so an ambiguous configuration is refused rather
                    # than resolved by file order.
                    raise AssertionError(
                        f"two runnable {tool} hook sets are configured, at "
                        f"{revisions[tool]} and {revision}; pre-commit runs both, so the "
                        "version developers get depends on which one reports first"
                    )
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


def test_rev_pinned_hooks_run_the_versions_ci_enforces() -> None:
    """The two sources are compared, so neither can be bumped alone."""
    pins = _declared_pins()
    revisions = _hook_revisions()

    # Without this the loop iterates nothing when the pins are ranges, and the
    # comparison passes while comparing no versions at all — a zero-input pass,
    # which is the failure mode this whole file exists to describe.
    assert set(REV_PINNED_HOOKS) <= set(pins), (
        f"expected an exact pin for each of {', '.join(REV_PINNED_HOOKS)}, found "
        f"{sorted(pins) or 'none'}; with nothing pinned there is nothing to compare"
    )

    for tool in sorted(REV_PINNED_HOOKS):
        pinned = pins[tool]
        assert tool in revisions, (
            f"pyproject pins {tool}=={pinned} but .pre-commit-config.yaml declares no "
            f"runnable {tool} hook set, so the commit hook and CI check different things"
        )
        assert revisions[tool] == pinned, (
            f"{tool} disagrees between the gates: pyproject enforces {pinned} and "
            f"pre-commit runs {revisions[tool]}. A formatter's output is its contract, "
            "so both gates would report confidently and disagree. Bump both together."
        )


def test_dependency_aware_tools_run_from_the_project_environment() -> None:
    """mypy needs the resolved dependency graph, which a hook environment lacks.

    A mirrored hook installs mypy alone, so it cannot see fastapi or pydantic and
    reports import errors on every commit that CI does not. A sibling repository
    measured 586 errors in 233 files from such a hook against 385 files clean
    from CI — with the versions already matching. That is why matching a rev is
    the right fix for ruff and the wrong one for mypy.
    """
    stanzas = _hooks_by_repository()

    for tool in PROJECT_ENVIRONMENT_TOOLS:
        mirrored = [
            source
            for source, _revision, hooks in stanzas
            if source != "local" and any(hook.get("id") == tool for hook in hooks)
        ]
        assert not mirrored, (
            f"{tool} is declared by {mirrored[0]}, which resolves its own environment "
            "without the project's dependencies. Declare it as a local hook running the "
            "project environment instead."
        )

        local_hooks = [
            hook
            for source, _revision, hooks in stanzas
            if source == "local"
            for hook in hooks
            if hook.get("id") == tool
        ]
        assert local_hooks, f"{tool} must be declared as a local hook"

        hook = local_hooks[0]
        default_stages = _config().get("default_stages")
        assert _runs_on_commit(hook.get("stages", default_stages)), (
            f"the local {tool} hook is configured but does not run on an ordinary commit, "
            "so the environment it would have used is irrelevant"
        )
        assert hook.get("language") == "system", (
            f"{tool} must use language: system so it runs in the environment the project "
            "was installed into, not one pre-commit builds for it"
        )
        # `python -m mypy` rather than a bare `mypy` executable: it follows the
        # interpreter running pre-commit instead of whatever is first on PATH.
        # The residual is real and is the same contract `make lint` already has
        # -- run from the environment the project was installed into. A hook
        # cannot enforce that; it can only avoid making it worse.
        assert str(hook.get("entry", "")).startswith("python -m "), (
            f"the local {tool} hook must invoke the interpreter, not a PATH executable; "
            f"entry is {hook.get('entry')!r}"
        )
        assert tool in str(hook.get("entry", "")), (
            f"the local {tool} hook must actually invoke {tool}; entry is {hook.get('entry')!r}"
        )


def _parse_config(text: str, tmp_path, monkeypatch) -> dict[str, str]:
    written = tmp_path / "pre-commit.yaml"
    written.write_text(text, encoding="utf-8")
    monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)
    return _hook_revisions()


_RUFF_STANZA = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
      - id: ruff-format
"""


def test_a_removed_or_disabled_hook_is_not_credited(tmp_path, monkeypatch) -> None:
    """A `rev:` proves a repository is listed, not that its hooks run."""
    assert _parse_config(_RUFF_STANZA, tmp_path, monkeypatch).get("ruff") == "0.15.22"

    without_formatter = _RUFF_STANZA.replace("      - id: ruff-format\n", "")
    assert "ruff" not in _parse_config(without_formatter, tmp_path, monkeypatch), (
        "CI runs `ruff format --check`, so dropping that hook must stop crediting Ruff"
    )

    commented = _RUFF_STANZA.replace("      - id: ruff-format", "      # - id: ruff-format")
    assert "ruff" not in _parse_config(commented, tmp_path, monkeypatch), (
        "a commented-out hook does not run"
    )

    staged = _RUFF_STANZA.replace(
        "      - id: ruff-format\n", "      - id: ruff-format\n        stages: [manual]\n"
    )
    assert "ruff" not in _parse_config(staged, tmp_path, monkeypatch), (
        "a hook restricted to another stage does not run on commit"
    )


def test_stage_resolution_follows_pre_commit(tmp_path, monkeypatch) -> None:
    """Per-hook stages override the file default, whatever the key order."""
    after_repos = _RUFF_STANZA + "default_stages: [manual]\n"
    assert _parse_config(after_repos, tmp_path, monkeypatch) == {}, (
        "a default declared after the repos still governs hooks declared before it"
    )

    overridden = "default_stages: [manual]\n" + _RUFF_STANZA.replace(
        "      - id: ruff\n", "      - id: ruff\n        stages: [pre-commit]\n"
    ).replace(
        "      - id: ruff-format\n",
        "      - id: ruff-format\n        stages: [pre-commit]\n",
    )
    assert _parse_config(overridden, tmp_path, monkeypatch).get("ruff") == "0.15.22", (
        "explicit per-hook stages override a manual default"
    )

    block_style = _RUFF_STANZA.replace(
        "      - id: ruff\n",
        "      - id: ruff\n        stages:\n          - pre-commit\n",
    )
    assert _parse_config(block_style, tmp_path, monkeypatch).get("ruff") == "0.15.22", (
        "a block-style stages list is ordinary YAML and must be read"
    )


def test_a_malformed_stanza_credits_nothing(tmp_path, monkeypatch) -> None:
    """Someone's typo produces a finding, not a crash that reads as a broken gate."""
    malformed = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      args: ["--fix"]
"""
    assert _parse_config(malformed, tmp_path, monkeypatch) == {}


def test_two_runnable_stanzas_for_one_tool_are_refused(tmp_path, monkeypatch) -> None:
    """pre-commit runs both, so the version is decided by file order.

    An obsolete stanza left above the pinned one still executes on every commit.
    Taking the last match would hide it behind a revision that looks correct.
    """
    duplicated = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
      - id: ruff-format
"""
    with pytest.raises(AssertionError, match="two runnable ruff hook sets"):
        _parse_config(duplicated, tmp_path, monkeypatch)


def test_a_manual_local_hook_is_reported(tmp_path, monkeypatch) -> None:
    """Being declared locally is not the same as running.

    A local hook restricted to another stage never executes, so the environment
    it would have used is irrelevant — and checking only its language and entry
    would report agreement about a hook nobody runs.
    """
    manual_local = """
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: python -m mypy
        language: system
        stages: [manual]
"""
    written = tmp_path / "pre-commit.yaml"
    written.write_text(manual_local, encoding="utf-8")
    monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)

    with pytest.raises(AssertionError, match="does not run on an ordinary commit"):
        test_dependency_aware_tools_run_from_the_project_environment()
