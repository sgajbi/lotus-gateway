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

# The repository each rev-pinned tool must come from. Matching on a URL
# SUBSTRING would accept any fork, mirror or unrelated project whose address
# happens to contain the tool's name, and then compare ITS revision against our
# pin — reporting agreement between the pinned version and something else
# entirely.
EXPECTED_HOOK_REPOSITORIES = {"ruff": "https://github.com/astral-sh/ruff-pre-commit"}

_REQUIRED_HOOK_IDS = {hook for hooks in REV_PINNED_HOOKS.values() for hook in hooks}

# Tools that must run from the project environment instead, because they need
# the resolved dependency graph to produce a correct verdict.
PROJECT_ENVIRONMENT_TOOLS = ("mypy",)

# The arguments a rev-pinned hook may carry. An ALLOWLIST, after a blocklist of
# neutralising flags was extended three times by review — `--exit-zero`, then
# `--fix-only`, then `--isolated` — each addition correct and each proving the
# same thing: enumerating the ways to break agreement is unbounded, because it
# means enumerating ruff's CLI.
#
# The three named here narrow or strengthen what the hook refuses and leave the
# program and its configuration alone. Everything else diverges from CI in one of
# two ways: it suppresses a verdict (`--exit-zero`, `--fix-only`), or it changes
# the configuration producing one (`--isolated` discards this repository's
# `line-length` and `lint.select`, so the SAME pinned version formats and lints
# differently on the two sides).
#
# An argument outside this set may be perfectly reasonable. It just has to be
# added here deliberately, having checked the CI lane agrees — which is the whole
# subject of this file.
PERMITTED_HOOK_ARGS = frozenset({"--fix", "--force-exclude", "--exit-non-zero-on-fix"})

# A wildcard equality such as `mypy==2.3.*` is a RANGE wearing `==`: it still
# lets the newest matching release arrive without a commit.
_EXACT_PIN = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[0-9]+(?:\.[0-9]+)*(?:[abrc][0-9]+)?)$"
)


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


def _agrees_with_ci(hook: dict[str, object]) -> bool:
    """Whether a hook's arguments leave it judging the same tree the CI lane does.

    The pin promises one PROGRAM. Arguments decide whether it is also one CHECK:
    `--exit-zero` leaves ruff reading every file, printing every violation and
    exiting 0, while `--isolated` discards this repository's `line-length` and
    `lint.select` so the same pinned version reaches a different verdict. Both
    end with a green commit and a red CI run on one tree.

    A flag written `--flag=value` is judged by its name.
    """
    names = {str(argument).split("=", 1)[0] for argument in hook.get("args") or []}
    return names <= PERMITTED_HOOK_ARGS


def _repository_identity(source: str) -> str:
    """A `repo:` reduced to the thing it clones, for comparison against the pin.

    pre-commit treats `repo` as a URL to clone, not as a canonical identifier, so
    `…/ruff-pre-commit` and `…/ruff-pre-commit.git` are the same upstream and run
    the same pinned hooks. Comparing the text refused the second and reported no
    runnable ruff hooks — a checker failing valid configuration, which is the
    fifth of this kind here and the failure mode that gets a checker ignored.

    Deliberately not a URL parser: case, a trailing slash and a trailing `.git`
    are the forms of the same address. A different scheme or host is a different
    address, and the strict comparison this normalises is the point — a fork or
    mirror must not be credited with the pinned version.
    """
    return source.strip().rstrip("/").removesuffix(".git").rstrip("/").lower()


def _runs_the_pinned_tool(hook: dict[str, object]) -> bool:
    """Whether a rev-pinned hook still runs the program its revision names.

    pre-commit lets a hook override `entry` and `language`, and that is exactly
    what makes a `rev:` a claim about the SOURCE rather than about the command.
    An override keeps the id, the stage and the revision while running something
    else entirely — `entry: python -c 'pass'` satisfies every check that reads
    the id, and ruff never runs.

    An override may be perfectly deliberate. It is simply no longer described by
    the pin, which is the only thing this file can speak about.
    """
    return not ({"entry", "language"} & set(hook))


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
    running: dict[str, set[str]] = {}
    covered: dict[tuple[str, str], set[str]] = {}
    overridden: list[str] = []
    for source, revision, hooks in _hooks_by_repository():
        if not revision:
            continue
        pinned_repository = any(
            _repository_identity(source) == _repository_identity(expected)
            for expected in EXPECTED_HOOK_REPOSITORIES.values()
        )
        # Two different questions, deliberately not one. `executes` asks whether
        # pre-commit runs the hook at all; `covers` asks whether it also counts
        # as the check CI performs. Collapsing them let a stale stanza carrying
        # `--fix-only` disappear from BOTH — dropped from coverage, correctly,
        # and thereby dropped from the record of which versions execute, so a
        # second ruff modifying the tree on every commit went unreported.
        #
        # A per-hook `stages` OVERRIDES the file default; absent, it inherits.
        # OR across occurrences, not last-wins: pre-commit executes every hook
        # entry, so an id listed twice runs if ANY of its occurrences does.
        # Collapsing by id would let a manual duplicate mask a running one.
        executes: dict[str, bool] = {}
        covers: dict[str, bool] = {}
        for hook in hooks:
            identifier = str(hook.get("id", ""))
            if not identifier:
                continue
            on_commit = _runs_on_commit(hook.get("stages", default_stages))
            executes[identifier] = executes.get(identifier, False) or on_commit
            # Both conditions OR correctly, because a second sound occurrence
            # restores what a bad one gave up: a hook that never runs, and a hook
            # whose arguments diverge from CI, both leave the commit gated as
            # long as a sibling does the job.
            covers[identifier] = covers.get(identifier, False) or (
                on_commit and _agrees_with_ci(hook)
            )
            # An override does NOT or away, and that asymmetry is the point. A
            # sound sibling adds a gate; an overridden occurrence ADDS AN
            # EXECUTION — `entry: ruff` with `language: system` runs whatever
            # version is on PATH, on every commit, no matter how correct its
            # neighbour is. Nothing a sibling does takes that back, so it is
            # collected rather than OR'd.
            if (
                pinned_repository
                and identifier in _REQUIRED_HOOK_IDS
                and on_commit
                and not _runs_the_pinned_tool(hook)
            ):
                overridden.append(identifier)

        for tool, required in REV_PINNED_HOOKS.items():
            # Both sides normalised, so the constant cannot be written in a form
            # that never matches anything.
            if _repository_identity(source) != _repository_identity(
                EXPECTED_HOOK_REPOSITORIES[tool]
            ):
                continue
            # Hooks may legitimately be split across stanzas that share the same
            # repository and revision. Judging each stanza alone would find
            # neither complete and credit nothing -- failing a configuration
            # pre-commit runs correctly.
            covered.setdefault((tool, revision), set()).update(
                hook for hook in required if covers.get(hook, False)
            )
            # ANY required hook that EXECUTES makes this stanza's version one
            # developers actually run — whatever its arguments, and whether or
            # not it counts as coverage. A stale stanza holding `- id: ruff` with
            # `--fix-only` still applies fixes from another version on every
            # commit; asking for coverage here would drop it from the record for
            # the very reason it is dangerous.
            if any(executes.get(hook, False) for hook in required):
                running.setdefault(tool, set()).add(revision)
            if covered[(tool, revision)] >= set(required):
                revisions[tool] = revision

    if overridden:
        raise AssertionError(
            f"{', '.join(sorted(set(overridden)))} overrides the pinned command or language "
            "while still running on commit, so pre-commit executes a version this repository "
            "never chose. A correct sibling hook does not take that back"
        )

    for tool, found in running.items():
        if len(found) > 1:
            # pre-commit runs every stanza. Resolving this by file order would
            # hide a revision that genuinely executes behind one that looks
            # correct.
            raise AssertionError(
                f"{len(found)} runnable {tool} revisions are configured "
                f"({', '.join(sorted(found))}); pre-commit runs all of them, so the "
                "version developers get is decided by file order"
            )
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
    default_stages = _config().get("default_stages")

    for tool in PROJECT_ENVIRONMENT_TOOLS:
        # Only occurrences that run on an ordinary commit. A mirrored hook held
        # at `stages: [manual]` is not part of the gate being compared and cannot
        # report the wrong verdict on a commit, so rejecting it would fail a
        # configuration that works — the failure that gets a checker ignored, and
        # the one this file has already made three times.
        mirrored = [
            source
            for source, _revision, hooks in stanzas
            if source != "local"
            and any(
                hook.get("id") == tool and _runs_on_commit(hook.get("stages", default_stages))
                for hook in hooks
            )
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

        running_local = [
            hook for hook in local_hooks if _runs_on_commit(hook.get("stages", default_stages))
        ]
        assert running_local, (
            f"the local {tool} hook is configured but does not run on an ordinary commit, "
            "so the environment it would have used is irrelevant"
        )

        # EVERY running occurrence, not the first. pre-commit executes them all,
        # so a second hook invoking something else would run unexamined behind a
        # correct one.
        for hook in running_local:
            assert hook.get("language") == "system", (
                f"{tool} must use language: system so it runs in the environment the "
                "project was installed into, not one pre-commit builds for it"
            )
            # The WHOLE entry, not a prefix: trailing tokens change what runs,
            # and `python -m mypyc` contains the name without being the tool.
            # `python -m` rather than a bare executable so it follows the
            # interpreter running pre-commit instead of whatever is first on
            # PATH. The residual — that the interpreter must BE the project's —
            # is the same contract `make lint` already has; a hook cannot
            # enforce it, only avoid making it worse.
            assert str(hook.get("entry", "")).split() == ["python", "-m", tool], (
                f"the local {tool} hook must invoke `python -m {tool}` exactly; "
                f"entry is {hook.get('entry')!r}"
            )
            # The entry alone is not what runs. `args: ['--version']` keeps a
            # perfect entry and checks nothing, so the arguments must name the
            # source tree the CI lane checks.
            assert list(hook.get("args") or []) == ["src"], (
                f"the local {tool} hook must check `src`, as the CI lane does; "
                f"args are {hook.get('args')!r}"
            )
            # `args` alone does not fix the command either: with filenames passed,
            # pre-commit appends each changed path AFTER `src`, so the tool sees
            # the same module twice — once through the tree and once by name —
            # and fails on a duplicate while `make lint` stays clean. A local gate
            # that fails where CI passes gets disabled, so the argument list has
            # to be the whole argument list.
            assert hook.get("pass_filenames") is False, (
                f"the local {tool} hook must set pass_filenames: false, or "
                "pre-commit appends changed paths after `src`; "
                f"pass_filenames is {hook.get('pass_filenames')!r}"
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
    with pytest.raises(AssertionError, match="runnable ruff revisions"):
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


def test_a_partial_stale_stanza_is_refused(tmp_path, monkeypatch) -> None:
    """A stanza holding only one required hook still runs that hook.

    An old stanza with `- id: ruff` alone executes an obsolete checker on every
    commit. Requiring a stanza to carry ALL the tool's hooks before considering
    it would leave that one unexamined, because it was never a candidate to be
    credited in the first place.
    """
    partial_stale = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
      - id: ruff-format
"""
    with pytest.raises(AssertionError, match="runnable ruff revisions"):
        _parse_config(partial_stale, tmp_path, monkeypatch)

    disabled_stale = partial_stale.replace(
        "      - id: ruff\n  - repo:", "      - id: ruff\n        stages: [manual]\n  - repo:"
    )
    assert _parse_config(disabled_stale, tmp_path, monkeypatch).get("ruff") == "0.15.22", (
        "a stale stanza that does not run on commit is not a conflict"
    )


def test_a_wildcard_equality_is_not_an_exact_pin() -> None:
    """`mypy==2.3.*` is a range wearing `==`.

    It still lets the newest matching release arrive without a commit, which is
    the drift this file exists to remove — so accepting it would defeat the
    check while looking like a pin.
    """
    assert _EXACT_PIN.match("mypy==2.3.1")
    assert _EXACT_PIN.match("ruff==0.15.22")
    assert not _EXACT_PIN.match("mypy==2.3.*")
    assert not _EXACT_PIN.match("ruff>=0.15.0")


def test_a_duplicate_hook_id_runs_if_any_occurrence_does(tmp_path, monkeypatch) -> None:
    """pre-commit executes every hook entry, not the last one with a given id.

    Collapsing occurrences by id would let a manual duplicate mask a running one,
    or the reverse, depending on file order.
    """
    duplicated_ids = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
        stages: [manual]
      - id: ruff
      - id: ruff-format
"""
    assert _parse_config(duplicated_ids, tmp_path, monkeypatch).get("ruff") == "0.15.22", (
        "one manual occurrence does not disable a sibling that runs on commit"
    )


def test_ruff_must_come_from_its_own_repository(tmp_path, monkeypatch) -> None:
    """A URL containing the tool's name is not the tool's repository.

    Matching on a substring would accept a fork or an unrelated project and then
    compare its revision against our pin — reporting agreement between the pinned
    version and something else entirely.
    """
    impostor = """
repos:
  - repo: https://github.com/someone/ruff-lookalike
    rev: v0.15.22
    hooks:
      - id: ruff
      - id: ruff-format
"""
    assert _parse_config(impostor, tmp_path, monkeypatch) == {}, (
        "a repository that merely contains 'ruff' must not be credited"
    )


def test_a_trailing_token_changes_what_runs(tmp_path, monkeypatch) -> None:
    """The whole entry is compared, not a prefix.

    `python -m mypy --follow-imports=skip` starts with the right three tokens and
    resolves every import to Any — a hook that runs, reports success, and checks
    nothing.
    """
    weakened = """
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: python -m mypy --follow-imports=skip
        language: system
"""
    written = tmp_path / "pre-commit.yaml"
    written.write_text(weakened, encoding="utf-8")
    monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)

    with pytest.raises(AssertionError, match="exactly"):
        test_dependency_aware_tools_run_from_the_project_environment()


def test_required_hooks_may_be_split_across_stanzas(tmp_path, monkeypatch) -> None:
    """Two stanzas at the same repository and revision are one configuration.

    pre-commit runs both, so the tool is covered. Judging each stanza alone would
    find neither complete and credit nothing — failing a configuration that works.
    """
    split = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff-format
"""
    assert _parse_config(split, tmp_path, monkeypatch).get("ruff") == "0.15.22", (
        "hooks split across stanzas at the same revision still cover the tool"
    )


def test_a_hook_that_cannot_refuse_is_not_credited(tmp_path, monkeypatch) -> None:
    """`--exit-zero` leaves ruff running and unable to fail the commit.

    The stanza is listed, the hook is present, the revision agrees, and every
    violation is printed — then the hook exits 0. Crediting it says developers
    are covered by a checker that refuses nothing.

    The accept side is asserted as explicitly as the reject side: the SAME
    configuration without the flag must be credited, so the case cannot pass
    because of some unrelated defect in the stanza.
    """
    template = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
        args: [{args}]
      - id: ruff-format
"""
    assert (
        _parse_config(template.format(args='"--fix"'), tmp_path, monkeypatch).get("ruff")
        == "0.15.22"
    ), "a hook that can still fail the commit is credited"

    assert "ruff" not in _parse_config(
        template.format(args='"--fix", "--exit-zero"'), tmp_path, monkeypatch
    ), "a hook that always exits 0 does not cover the tool"


def test_the_same_repository_written_differently_is_the_same_repository(
    tmp_path, monkeypatch
) -> None:
    """`repo:` is a URL to clone, not a canonical identifier.

    `…/ruff-pre-commit.git` clones the same upstream and runs the same pinned
    hooks, so refusing it reports that no runnable ruff hook set exists — a
    checker failing valid configuration, the fifth of that kind here.

    The reject side is asserted in the same case: a fork at a different address
    must still not be credited with the pinned version, which is the whole reason
    the comparison is strict rather than a substring.
    """
    template = """
repos:
  - repo: {source}
    rev: v0.15.22
    hooks:
      - id: ruff
      - id: ruff-format
"""
    for source in (
        "https://github.com/astral-sh/ruff-pre-commit.git",
        "https://github.com/astral-sh/ruff-pre-commit/",
        "https://github.com/Astral-sh/Ruff-Pre-Commit",
    ):
        assert (
            _parse_config(template.format(source=source), tmp_path, monkeypatch).get("ruff")
            == "0.15.22"
        ), f"{source} clones the same upstream and runs the same pinned hooks"

    assert "ruff" not in _parse_config(
        template.format(source="https://github.com/someone/ruff-pre-commit"),
        tmp_path,
        monkeypatch,
    ), "a fork at another address is not the pinned repository"


def test_an_overridden_entry_is_not_the_pinned_tool(tmp_path, monkeypatch) -> None:
    """A `rev:` describes the source, not the command.

    pre-commit lets a hook override `entry`, so `entry: python -c 'pass'` keeps
    the id, the stage and the revision while ruff never runs. Every check that
    reads the id is satisfied and the pin describes nothing.
    """
    overridden = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
        entry: python -c 'pass'
      - id: ruff-format
"""
    with pytest.raises(AssertionError, match="overrides the pinned command"):
        _parse_config(overridden, tmp_path, monkeypatch)


def test_a_sound_hook_does_not_excuse_an_overriding_sibling(tmp_path, monkeypatch) -> None:
    """An override adds an execution; a correct sibling only adds a gate.

    A duplicate `- id: ruff` with `entry: ruff` and `language: system` runs
    whatever version is on PATH, on every commit, however correct the hook above
    it is. OR-ing the two — which is right for stages and for neutralised args,
    where a sound sibling restores the gate — lets the good one hide the bad one.
    """
    masked = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
      - id: ruff-format
      - id: ruff
        entry: ruff
        language: system
"""
    with pytest.raises(AssertionError, match="overrides the pinned command"):
        _parse_config(masked, tmp_path, monkeypatch)

    # The same override held off the commit stage runs nothing, so it is not a
    # finding — the check is about execution, not about the text.
    staged = masked.replace(
        "        language: system", "        language: system\n        stages: [manual]"
    )
    assert _parse_config(staged, tmp_path, monkeypatch).get("ruff") == "0.15.22", (
        "an override that never runs on commit executes nothing"
    )


@pytest.mark.parametrize(
    ("argument", "why"),
    [
        ("--fix-only", "exits 0 on the violations it could not fix"),
        ("--isolated", "discards this repository's line-length and lint.select"),
        ("--config=/tmp/other.toml", "judges the tree against a different configuration"),
        ("--line-length=200", "overrides a setting CI reads from pyproject"),
    ],
)
def test_arguments_that_diverge_from_ci_are_refused(argument, why, tmp_path, monkeypatch) -> None:
    """Divergence has two shapes, and the allowlist covers both.

    A flag can suppress the verdict (`--fix-only` exits 0 on what it could not
    fix) or change the configuration producing it (`--isolated` drops this
    repository's settings). Either way the commit is green and `ruff check .` is
    red on one unchanged tree — a hook that is evidence pointing the wrong way.
    """
    diverging = f"""
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
        args: ["{argument}"]
      - id: ruff-format
"""
    assert "ruff" not in _parse_config(diverging, tmp_path, monkeypatch), (
        f"`{argument}` {why}, so the hook does not cover the tool"
    )


def test_a_diverging_stanza_still_counts_as_a_running_version(tmp_path, monkeypatch) -> None:
    """Dropping a hook from coverage must not drop it from the record of what runs.

    A stale stanza at another revision carrying `--fix-only` does not cover the
    tool — and still applies fixes from a version this repository never chose, on
    every commit. Judging both questions with one answer made it vanish for
    exactly the reason it is dangerous.
    """
    stale_and_pinned = """
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.1
    hooks:
      - id: ruff
        args: ["--fix-only"]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
      - id: ruff-format
"""
    with pytest.raises(AssertionError, match="runnable ruff revisions"):
        _parse_config(stale_and_pinned, tmp_path, monkeypatch)


def test_the_configured_arguments_are_permitted(tmp_path, monkeypatch) -> None:
    """The allowlist must admit what this repository actually configures.

    An allowlist that refused the shipped config would be found immediately; one
    that refuses a reasonable neighbour is the failure worth guarding, so the
    arguments a hook may legitimately want are asserted acceptable rather than
    discovered later by someone whose correct change was rejected.
    """
    for argument in sorted(PERMITTED_HOOK_ARGS):
        permitted = f"""
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.22
    hooks:
      - id: ruff
        args: ["{argument}"]
      - id: ruff-format
"""
        assert _parse_config(permitted, tmp_path, monkeypatch).get("ruff") == "0.15.22", (
            f"`{argument}` narrows or strengthens the hook and must stay acceptable"
        )


def test_a_manual_mirrored_hook_is_not_a_conflict(tmp_path, monkeypatch) -> None:
    """A mirrored hook held at `stages: [manual]` is not part of the commit gate.

    It cannot report a wrong verdict on a commit, so rejecting it fails a
    configuration that works — the failure that gets a checker ignored, and one
    this file has made three times.
    """
    coexisting = """
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.3.1
    hooks:
      - id: mypy
        stages: [manual]
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: python -m mypy
        args: ["src"]
        language: system
        pass_filenames: false
"""
    written = tmp_path / "pre-commit.yaml"
    written.write_text(coexisting, encoding="utf-8")
    monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)

    test_dependency_aware_tools_run_from_the_project_environment()

    # The accept side must not be an accept-everything: the SAME mirrored hook
    # on the commit stage is still refused.
    running = coexisting.replace("stages: [manual]", "stages: [pre-commit]")
    written.write_text(running, encoding="utf-8")
    with pytest.raises(AssertionError, match="mirrors-mypy"):
        test_dependency_aware_tools_run_from_the_project_environment()


def test_neutralising_args_are_rejected(tmp_path, monkeypatch) -> None:
    """A perfect entry with `--version` checks nothing.

    The entry says which program runs; the arguments say what it does. Verifying
    only the first is the same shape as crediting a hook for existing.
    """
    neutralised = """
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: python -m mypy
        args: ["--version"]
        language: system
"""
    written = tmp_path / "pre-commit.yaml"
    written.write_text(neutralised, encoding="utf-8")
    monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)

    with pytest.raises(AssertionError, match="must check `src`"):
        test_dependency_aware_tools_run_from_the_project_environment()


def test_passing_filenames_is_rejected(tmp_path, monkeypatch) -> None:
    """`args: ["src"]` is not the command unless it is the WHOLE command.

    With filenames passed, pre-commit appends each changed path after `src`, so
    the tool sees the same module through the tree and again by name and fails on
    a duplicate — a local gate red where `make lint` is green. That gets the hook
    disabled, which is how the drift this file exists to catch starts.
    """
    passing = """
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: python -m mypy
        args: ["src"]
        language: system
        pass_filenames: true
"""
    written = tmp_path / "pre-commit.yaml"
    written.write_text(passing, encoding="utf-8")
    monkeypatch.setattr("test_toolchain_pins_agree.PRE_COMMIT", written)

    with pytest.raises(AssertionError, match="pass_filenames"):
        test_dependency_aware_tools_run_from_the_project_environment()
