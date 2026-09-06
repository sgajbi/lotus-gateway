"""Workflow steps must not hide a gate's exit code behind a pipe.

A shell pipeline exits with the status of its **last** command, so a step
written as ``gate.py | tee log.txt`` reports ``tee``'s success whatever the gate
decided; ``bash -e`` does not catch it because the pipeline succeeded. This is
how six enforcement steps in this repository became incapable of failing, the
branch-protection gate among them: it raised ``CalledProcessError`` on an empty
token in every run beneath a green check.

The estate-wide equivalent lives in ``lotus-platform`` as
``automation/validate_workflow_pipeline_exit_codes.py``; that one asserts over
default branches, so this repo-local check is what refuses the defect at PR time.
"""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"

# Commands that report their own success no matter what fed them. `grep` and
# `jq` are deliberately absent: as a terminal stage they are usually the
# assertion, and their failure does fail the step.
PASSIVE_SINKS = frozenset(
    {"tee", "tail", "head", "cat", "sort", "uniq", "tr", "sed", "awk", "wc", "fold", "column"}
)
# Wrappers that run another command; the sink is whatever follows them.
STAGE_PREFIXES = frozenset({"sudo", "env", "command", "exec", "nohup", "time", "stdbuf"})
# Producers with no verdict to lose: `echo x | sudo tee file` hides nothing.
TRIVIAL_SOURCES = frozenset({"echo", "printf", "true", ":", "yes"})
CONDITION_KEYWORDS = ("if", "elif", "while", "until")

# Bash block structure: a `set -o pipefail` inside one of these may never
# execute, so only an unconditional setting is honoured.
BLOCK_OPENERS = frozenset({"if", "while", "until", "for", "case"})
BLOCK_CLOSERS = frozenset({"fi", "done", "esac"})

_STEPS_KEY = re.compile(r"^\s*steps:\s*$")
_NAME = re.compile(r"(?:^|-\s+)name:\s*(?P<name>.+?)\s*$")
_RUN_KEY = re.compile(r"^\s*(?:-\s+)?run:\s*(?P<inline>.*)$")
_PIPEFAIL_ON = re.compile(r"^\s*set\s+(?:[-+]\w+\s+)*-\w*o\s+pipefail\b")
_PIPEFAIL_OFF = re.compile(r"^\s*set\s+(?:[-+]\w+\s+)*\+\w*o\s+pipefail\b")
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
_PIPESTATUS_CAPTURE = re.compile(r"(?P<var>[A-Za-z_][A-Za-z0-9_]*)=[\"']?\$\{PIPESTATUS\[0\]\}")
_PIPESTATUS_DIRECT = re.compile(r"(?:exit|return)\s+\"?\$\{PIPESTATUS\[0\]\}")


def workflow_files() -> list[Path]:
    """GitHub recognizes both extensions; scanning one would miss the other."""
    return sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))


def iter_steps(text: str):
    """Yield (step name, step body) by YAML list structure.

    Not by a ``name:`` key: ``- run: gate.py | tee log.txt`` is a valid unnamed
    step, and keying on the name would skip the exact shape this catches.
    """

    def name_of(block: list[str]) -> str:
        for line in block:
            match = _NAME.search(line)
            if match:
                return match.group("name").strip().strip("\"'")
        return "(unnamed step)"

    in_steps = False
    steps_indent = 0
    item_indent: int | None = None
    current: list[str] | None = None

    for line in text.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if not stripped:
            if current is not None:
                current.append(line)
            continue
        if _STEPS_KEY.match(line):
            if current is not None:
                yield name_of(current), "\n".join(current)
                current = None
            in_steps, steps_indent, item_indent = True, indent, None
            continue
        if not in_steps:
            continue
        if indent <= steps_indent:
            if current is not None:
                yield name_of(current), "\n".join(current)
                current = None
            in_steps, item_indent = False, None
            continue
        is_item = stripped.startswith("- ")
        if is_item and item_indent is None:
            item_indent = indent
        if is_item and indent == item_indent:
            if current is not None:
                yield name_of(current), "\n".join(current)
            current = [line]
        elif current is not None:
            current.append(line)

    if current is not None:
        yield name_of(current), "\n".join(current)


def _join_continuations(lines: list[str]) -> list[str]:
    """Join lines Bash treats as one command, so a split pipeline is seen whole."""
    joined: list[str] = []
    for line in lines:
        stripped = line.strip()
        if joined and (joined[-1].rstrip().endswith(("|", "\\")) or stripped.startswith("|")):
            previous = joined.pop().rstrip().rstrip("\\").rstrip()
            joined.append(f"{previous} {stripped}".strip())
            continue
        joined.append(stripped)
    return joined


def run_lines(step_body: str) -> list[str]:
    """Return the shell lines of a step's run: block, in execution order."""
    lines: list[str] = []
    collecting = False
    block_indent: int | None = None
    for line in step_body.splitlines():
        match = _RUN_KEY.match(line)
        if match:
            inline = match.group("inline").strip()
            if inline and inline not in {"|", ">", "|-", ">-", "|+", ">+"}:
                lines.append(inline)
                collecting = False
            else:
                collecting, block_indent = True, None
            continue
        if not collecting or not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if block_indent is None:
            block_indent = indent
        if indent < block_indent:
            collecting = False
            continue
        lines.append(line.strip())
    return _join_continuations(lines)


def terminal_sink(segment: str) -> str | None:
    """Return the passive sink this single command segment ends in, if any.

    A segment is one command in a shell list; the caller splits on ``&&``,
    ``||`` and ``;``. ``|&`` is Bash shorthand for ``2>&1 |`` and is normalised
    first, or the ``&`` would be read as the sink's command name.
    """
    words = segment.replace("|&", "|").split()
    while words and (words[0] in CONDITION_KEYWORDS or words[0] == "!"):
        words = words[1:]
    text = re.split(r"\b(?:then|do)\b", " ".join(words))[0]
    if "|" not in text:
        return None

    stages = [stage.strip() for stage in text.split("|")]
    last = _command_of(stages[-1])
    if last not in PASSIVE_SINKS:
        return None
    # Only harmless when *every* stage feeding the sink is a producer with no
    # verdict: `printf x | gate.py | tee log` still hides gate.py's failure.
    upstream = [_command_of(stage) for stage in stages[:-1]]
    if upstream and all(command in TRIVIAL_SOURCES for command in upstream):
        return None
    return last


def _command_of(stage: str) -> str:
    """Return the command a pipeline stage runs, past prefixes and assignments."""
    words = stage.split()
    while words and (words[0] in STAGE_PREFIXES or "=" in words[0]):
        words = words[1:]
    if not words:
        return ""
    return words[0].lstrip("$(").split("/")[-1]


def _status_is_propagated(shell: list[str], index: int) -> bool:
    """True when this pipeline's stage-0 status reaches an exit or return."""
    following = shell[index + 1] if index + 1 < len(shell) else ""
    if _PIPESTATUS_DIRECT.search(following):
        return True
    capture = _PIPESTATUS_CAPTURE.search(following)
    if capture is None:
        return False
    variable = capture.group("var")
    exits = re.compile(rf"(?:exit|return)\s+\"?\$\{{?{re.escape(variable)}\}}?")
    return any(exits.search(line) for line in shell[index + 2 :])


def unguarded_pipelines(step_body: str) -> list[str]:
    """Return each pipeline whose gate status never reaches the step.

    The step is read as command segments in execution order, so a ``set`` and a
    pipeline on the same line are handled in the order Bash runs them.

    Two Bash facts shape the guard rules. ``PIPESTATUS`` describes only the most
    recently executed pipeline, so a capture on the next line vouches for the
    **last** pipeline of the previous line and no earlier one. And a ``set -o
    pipefail`` inside a conditional or loop body may never execute, so only an
    unconditional one — at the top level of the block — is honoured.
    """
    shell = run_lines(step_body)
    pipefail = False
    depth = 0
    offenders: list[str] = []

    for index, line in enumerate(shell):
        probe = _QUOTED.sub("", line)
        if probe.strip().startswith("#"):
            continue

        segments = re.split(r"&&|\|\||;", probe)
        piped = [i for i, segment in enumerate(segments) if terminal_sink(segment) is not None]
        last_piped = piped[-1] if piped else None
        reported = False

        for position, segment in enumerate(segments):
            words = segment.split()
            for word in words:
                if word in BLOCK_OPENERS:
                    depth += 1
                elif word in BLOCK_CLOSERS:
                    depth = max(0, depth - 1)

            if _PIPEFAIL_OFF.match(segment):
                if depth == 0:
                    pipefail = False
                continue
            if _PIPEFAIL_ON.match(segment):
                if depth == 0:
                    pipefail = True
                continue
            if position not in piped or reported:
                continue
            if pipefail:
                continue
            if position == last_piped and _status_is_propagated(shell, index):
                continue
            offenders.append(line)
            reported = True

    return offenders


def test_no_workflow_step_hides_a_gate_exit_code() -> None:
    offenders = [
        f"{workflow.name}: {name}"
        for workflow in workflow_files()
        for name, body in iter_steps(workflow.read_text(encoding="utf-8"))
        if unguarded_pipelines(body)
    ]
    assert not offenders, (
        "these steps pipe a gate without propagating its exit code, so the step "
        "reports the pipe's status and cannot fail: " + "; ".join(offenders)
    )


def test_every_workflow_is_scanned() -> None:
    """A silent zero-input scan would pass while checking nothing."""
    files = workflow_files()
    assert files, "no workflows found: the scan would pass vacuously"
    scanned = sum(1 for f in files for _ in iter_steps(f.read_text(encoding="utf-8")))
    assert scanned > 0, "no steps parsed: the assertion would be vacuous"


def test_unnamed_steps_are_scanned() -> None:
    bodies = [
        body
        for workflow in workflow_files()
        for _, body in iter_steps(workflow.read_text(encoding="utf-8"))
        if "actions/checkout" in body
    ]
    assert bodies, "checkout steps are usually unnamed `- uses:` items and must be seen"


def test_unguarded_pipe_is_reported() -> None:
    assert unguarded_pipelines("run: gate.py 2>&1 | tee log.txt\n")


def test_pipefail_before_protects_and_after_does_not() -> None:
    before = "run: |\n  set -o pipefail\n  gate.py | tee log\n"
    after = "run: |\n  gate.py | tee log\n  set -o pipefail\n"
    assert unguarded_pipelines(before) == []
    assert unguarded_pipelines(after) == ["gate.py | tee log"]


def test_disabling_pipefail_removes_the_guard() -> None:
    body = "run: |\n  set -o pipefail\n  set +o pipefail\n  gate.py | tee log\n"
    assert unguarded_pipelines(body) == ["gate.py | tee log"]


def test_each_pipeline_is_judged_on_its_own_guard() -> None:
    body = (
        "run: |\n"
        "  a.py | tee a.log\n"
        "  a_status=${PIPESTATUS[0]}\n"
        "  b.py | tee b.log\n"
        '  exit "$a_status"\n'
    )
    assert unguarded_pipelines(body) == ["b.py | tee b.log"]


def test_mentioning_pipestatus_is_not_a_guard() -> None:
    body = "run: |\n  gate.py | tee log\n  status=${PIPESTATUS[0]}\n  echo done\n"
    assert unguarded_pipelines(body) == ["gate.py | tee log"]


def test_capturing_the_wrong_stage_is_not_a_guard() -> None:
    body = 'run: |\n  gate.py | tee log\n  status=${PIPESTATUS[1]}\n  exit "$status"\n'
    assert unguarded_pipelines(body) == ["gate.py | tee log"]


def test_captured_status_reaching_exit_is_a_guard() -> None:
    body = 'run: |\n  gate.py | tee log\n  status=${PIPESTATUS[0]}\n  exit "$status"\n'
    assert unguarded_pipelines(body) == []


def test_condition_pipeline_into_a_sink_is_reported() -> None:
    body = "run: |\n  if gate.py | tee log; then\n    echo ok\n  fi\n"
    assert unguarded_pipelines(body) == ["if gate.py | tee log; then"]


def test_assertion_and_trivial_producer_pipelines_stay_quiet() -> None:
    condition = 'run: |\n  if echo "$o" | grep -qi already; then\n    :\n  fi\n'
    assert unguarded_pipelines(condition) == []
    assert unguarded_pipelines("run: echo deb-line | sudo tee /etc/apt/x.list\n") == []


def test_pipeline_split_across_lines_is_joined() -> None:
    body = "run: |\n  gate.py |\n    tee gate.log\n"
    assert unguarded_pipelines(body) == ["gate.py | tee gate.log"]


def test_sink_behind_a_runner_prefix_is_detected() -> None:
    assert unguarded_pipelines("run: gate.py | sudo tee out.txt\n")


def test_pipeline_before_a_later_shell_command_is_reported() -> None:
    """`gate.py | tee log; echo done` ends the step on echo, hiding the gate."""
    for line in ("gate.py | tee log; echo done", "gate.py | tee log && echo done"):
        assert unguarded_pipelines(f"run: {line}\n") == [line], line


def test_bash_pipe_ampersand_operator_is_recognized() -> None:
    """`|&` is shorthand for `2>&1 |` and hides the gate the same way."""
    assert unguarded_pipelines("run: gate.py |& tee log\n") == ["gate.py |& tee log"]


def test_a_gate_after_a_trivial_source_is_still_reported() -> None:
    """Only the whole upstream being verdict-free makes a pipeline harmless."""
    line = "printf data | python gate.py | tee log"
    assert unguarded_pipelines(f"run: {line}\n") == [line]


def test_compact_pipefail_option_clusters_are_accepted() -> None:
    """`set -euo pipefail` is the repository idiom; rejecting it blocks valid PRs."""
    for options in ("-o", "-eo", "-euo", "-euxo"):
        body = f"run: |\n  set {options} pipefail\n  gate.py | tee log\n"
        assert unguarded_pipelines(body) == [], options


def test_same_line_set_is_applied_before_the_pipeline_after_it() -> None:
    disabled = "set +o pipefail; gate.py | tee log"
    enabled = "set -o pipefail; gate.py | tee log"
    assert unguarded_pipelines(f"run: |\n  {disabled}\n") == [disabled]
    assert unguarded_pipelines(f"run: |\n  {enabled}\n") == []


def test_pipestatus_vouches_only_for_the_last_pipeline_on_the_line() -> None:
    """PIPESTATUS describes the most recent pipeline, not every one on the line."""
    body = 'run: |\n  a.py | tee a; b.py | tee b\n  s=${PIPESTATUS[0]}\n  exit "$s"\n'
    assert unguarded_pipelines(body) == ["a.py | tee a; b.py | tee b"]


def test_pipefail_inside_an_untaken_branch_is_not_honoured() -> None:
    """`if false; then set -o pipefail; fi` never runs; assuming it did is unsafe."""
    body = "run: |\n  if false; then set -o pipefail; fi\n  gate.py | tee log\n"
    assert unguarded_pipelines(body) == ["gate.py | tee log"]
