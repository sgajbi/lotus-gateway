"""Validate the deterministic duplicate-code report against a reviewed baseline."""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import tokenize
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any

STATUS_PATTERN = re.compile(r"^QUALITY_COMMAND_STATUS=(\d+)$", re.MULTILINE)
FRAGMENT_WHITESPACE = re.compile(r"\s+")
# Python 3.12 introduced dedicated f-string tokens while Python 3.11 exposes
# the complete literal as STRING. Keep private sentinels for the older
# interpreter so both token shapes can be regression-tested on Python 3.11.
FSTRING_START_TOKEN = getattr(tokenize, "FSTRING_START", 10_001)
FSTRING_END_TOKEN = getattr(tokenize, "FSTRING_END", 10_002)
DETECTOR_POLICY = {
    "name": "jscpd",
    "version": "4.2.2",
    "format": "python",
    "input_root": "src/app",
    "pattern": "**/*.py",
    "min_lines": 15,
    "min_tokens": 50,
    "max_lines": 10000,
    "max_size": "1mb",
}


@dataclass(frozen=True)
class DuplicateFinding:
    fingerprint: str
    first_file: str
    second_file: str
    lines: int


@dataclass(frozen=True)
class SourceLocation:
    source: str
    start: int
    start_column: int | None = None
    end: int | None = None
    end_column: int | None = None


@dataclass(frozen=True)
class DuplicateIdentity:
    format: str
    fragment_digest: str
    first_file: str
    second_file: str
    lines: int
    sources: tuple[str, str]
    locations: tuple[tuple[str, int], tuple[str, int]]
    context_digests: tuple[str | None, str | None]

    @property
    def grouping_key(
        self,
    ) -> tuple[str, str, tuple[str, str], tuple[str | None, str | None]]:
        return self.format, self.fragment_digest, self.sources, self.context_digests


@dataclass(frozen=True)
class DuplicateReport:
    findings: tuple[DuplicateFinding, ...]
    duplicated_lines: int
    duplicated_percentage: Decimal


@dataclass(frozen=True)
class RatchetResult:
    report: DuplicateReport
    baseline_clone_count: int
    baseline_duplicated_lines: int
    baseline_duplicated_percentage: Decimal
    baseline_fingerprint_count: int
    unexpected_fingerprints: tuple[str, ...]
    stale_fingerprints: tuple[str, ...]
    status: int

    @property
    def clone_count(self) -> int:
        return len(self.report.findings)

    @property
    def metrics_passed(self) -> bool:
        return (
            self.status == 0
            and self.clone_count <= self.baseline_clone_count
            and self.report.duplicated_lines <= self.baseline_duplicated_lines
            and self.report.duplicated_percentage <= self.baseline_duplicated_percentage
            and not self.unexpected_fingerprints
        )

    @property
    def can_update_baseline(self) -> bool:
        return self.metrics_passed

    @property
    def passed(self) -> bool:
        return self.metrics_passed and not self.stale_fingerprints

    @property
    def all_fingerprints_changed(self) -> bool:
        current_fingerprint_count = len({finding.fingerprint for finding in self.report.findings})
        return (
            bool(self.unexpected_fingerprints)
            and len(self.unexpected_fingerprints) == current_fingerprint_count
            and len(self.stale_fingerprints) == self.baseline_fingerprint_count
        )


def _normalise_source(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("duplicate report source name must be a string")
    source = value.replace("\\", "/")
    if source.startswith("./"):
        source = source[2:]
    path = PurePosixPath(source)
    if len(path.parts) < 3 or path.parts[:2] != ("src", "app") or ".." in path.parts:
        raise ValueError(f"duplicate report contains an out-of-scope source: {value!r}")
    return path.as_posix()


def _normalise_location(value: dict[str, Any]) -> SourceLocation:
    source = _normalise_source(value.get("name"))
    start = value.get("start")
    if isinstance(start, bool) or not isinstance(start, int) or start <= 0:
        raise ValueError("duplicate report source has an invalid start line")
    start_loc = value.get("startLoc")
    end_loc = value.get("endLoc")
    if start_loc is None and end_loc is None:
        return SourceLocation(source, start)
    if not isinstance(start_loc, dict) or not isinstance(end_loc, dict):
        raise ValueError("duplicate report source has incomplete location columns")
    start_line = start_loc.get("line")
    start_column = start_loc.get("column")
    end_line = end_loc.get("line")
    end_column = end_loc.get("column")
    if (
        isinstance(start_line, bool)
        or not isinstance(start_line, int)
        or start_line != start
        or isinstance(start_column, bool)
        or not isinstance(start_column, int)
        or start_column < 0
        or isinstance(end_line, bool)
        or not isinstance(end_line, int)
        or isinstance(end_column, bool)
        or not isinstance(end_column, int)
        or end_column < 0
    ):
        raise ValueError("duplicate report source has invalid location columns")
    # jscpd 4.2.2 can emit a non-monotonic endLoc for an overlapping clone on
    # a non-canonical report side. Keep the trusted line range for that side;
    # canonical source extraction still uses columns whenever the range is
    # coherent, and malformed scalar fields remain hard input errors above.
    if end_line < start_line or (end_line == start_line and end_column < start_column):
        return SourceLocation(source, start)
    return SourceLocation(source, start, start_column, end_line, end_column)


def _source_fragment(source_root: Path, location: SourceLocation, lines: int) -> str:
    source_path = source_root.joinpath(*PurePosixPath(location.source).parts)
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"duplicate report source cannot be read: {source_path}") from exc
    source_lines = source_text.splitlines(keepends=True)
    end_line = location.end or location.start + lines - 1
    if end_line > len(source_lines):
        raise ValueError(f"duplicate report source range exceeds file: {source_path}")
    if location.start_column is None or location.end_column is None:
        end = location.start - 1 + lines
        if end > len(source_lines):
            raise ValueError(f"duplicate report source range exceeds file: {source_path}")
        return "".join(source_lines[location.start - 1 : end])

    line_offsets = [0]
    for source_line in source_lines:
        line_offsets.append(line_offsets[-1] + len(source_line))

    def absolute(line: int, column: int) -> int:
        return line_offsets[line - 1] + column

    start_offset = absolute(location.start, location.start_column)
    end_offset = absolute(end_line, location.end_column)
    if end_offset < start_offset or end_offset > len(source_text):
        raise ValueError(f"duplicate report source range exceeds file: {source_path}")
    return source_text[start_offset:end_offset]


def _context_digest(source_root: Path, source: str, start: int, lines: int) -> str:
    source_path = source_root.joinpath(*PurePosixPath(source).parts)
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"duplicate report source cannot be read: {source_path}") from exc
    try:
        tree = ast.parse(source_text, filename=str(source_path))
    except SyntaxError as exc:
        raise ValueError(f"duplicate report source is not valid Python: {source_path}") from exc
    end = start + lines - 1
    context = _scope_context(tree, start, end)
    return hashlib.sha256(context.encode("utf-8")).hexdigest()


def _scope_context(tree: ast.Module, start: int, end: int) -> str:
    """Return the stable class/function scope containing a duplicate occurrence.

    The enclosing scope name is structural evidence for replacement detection,
    while its body is deliberately excluded: an unrelated statement in the
    same function must not invalidate every duplicate fingerprint in it.
    """
    best: tuple[str, ...] = ()

    def visit(node: ast.AST, scopes: tuple[str, ...]) -> None:
        nonlocal best
        node_start = getattr(node, "lineno", None)
        node_end = getattr(node, "end_lineno", None)
        contains_occurrence = node is tree or (
            isinstance(node_start, int)
            and isinstance(node_end, int)
            and node_start <= start
            and node_end >= end
        )
        if not contains_occurrence:
            return
        next_scopes = scopes
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            next_scopes = scopes + (f"{type(node).__name__}:{node.name}",)
        if len(next_scopes) > len(best):
            best = next_scopes
        for child in ast.iter_child_nodes(node):
            visit(child, next_scopes)

    visit(tree, ())
    return "/".join(best) or "module"


def _normalise_fragment(fragment: str) -> str:
    """Normalize Python layout while preserving actual string-token contents."""
    text = fragment.replace("\r\n", "\n").replace("\r", "\n")
    tokens, tokenize_error = _tokenize_fragment(text)
    if any(token.type == tokenize.ERRORTOKEN for token in tokens) or (
        tokenize_error is not None
        and any(
            marker in str(tokenize_error).lower()
            for marker in ("unterminated string", "multi-line string")
        )
    ):
        return _normalise_fragment_lexically(text)
    if not tokens:
        return _normalise_fragment_lexically(text)
    return _normalise_token_stream(text, tokens)


def _tokenize_fragment(text: str) -> tuple[list[Any], Exception | None]:
    """Retain partial tokens while making indentation-only slices interpreter-stable."""
    tokens: list[Any] = []
    tokenize_error: Exception | None = None
    try:
        tokens.extend(tokenize.generate_tokens(io.StringIO(text).readline))
        return tokens, None
    except (IndentationError, SyntaxError, tokenize.TokenError) as exc:
        tokenize_error = exc

    indentation_neutralized = _neutralize_fragment_indentation(text)
    if indentation_neutralized == text:
        return tokens, tokenize_error

    retry_tokens: list[Any] = []
    retry_error: Exception | None = None
    try:
        retry_tokens.extend(tokenize.generate_tokens(io.StringIO(indentation_neutralized).readline))
    except (IndentationError, SyntaxError, tokenize.TokenError) as exc:
        retry_error = exc
    if retry_tokens:
        return retry_tokens, retry_error
    return tokens, tokenize_error


def _neutralize_fragment_indentation(text: str) -> str:
    """Strip code indentation for a tokenizer retry without changing literals/comments."""
    pieces: list[str] = []
    line_start = True
    in_comment = False
    index = 0
    while index < len(text):
        character = text[index]
        if line_start:
            while index < len(text) and text[index] in " \t":
                index += 1
            line_start = False
            if index == len(text):
                break
            character = text[index]
        if in_comment:
            pieces.append(character)
            index += 1
            if character == "\n":
                in_comment = False
                line_start = True
            continue
        if character == "#":
            pieces.append(character)
            in_comment = True
            index += 1
            continue
        literal_end = _string_literal_end(text, index)
        if literal_end is not None:
            literal = text[index:literal_end]
            pieces.append(literal)
            index = literal_end
            line_start = literal.endswith("\n")
            continue
        pieces.append(character)
        index += 1
        if character == "\n":
            line_start = True
    return "".join(pieces)


def _normalise_token_stream(text: str, tokens: Any) -> str:
    """Normalize a complete token stream with stable f-string handling.

    Python 3.11 reports an f-string as one STRING token, while Python 3.12+
    reports FSTRING_START/MIDDLE/END plus expression tokens. Reconstructing
    the source span for the complete f-string makes both token shapes produce
    the same identity without changing whitespace that is part of the literal.
    """
    pieces: list[str] = []
    fstring_depth = 0
    fstring_start: tuple[int, int] | None = None
    for token in list(tokens):
        if token.type == FSTRING_START_TOKEN:
            if fstring_depth == 0:
                fstring_start = token.start
            fstring_depth += 1
            continue
        if fstring_depth:
            if token.type == FSTRING_END_TOKEN:
                fstring_depth -= 1
                if fstring_depth == 0 and fstring_start is not None:
                    pieces.append(_source_span(text, fstring_start, token.end))
                    fstring_start = None
            continue
        if token.type in {
            tokenize.ENCODING,
            tokenize.ENDMARKER,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.NEWLINE,
            tokenize.NL,
        }:
            continue
        value = token.string
        if token.type == tokenize.COMMENT:
            value = FRAGMENT_WHITESPACE.sub(" ", value).strip()
        pieces.append(value)
    return " ".join(pieces).strip()


def _source_span(
    text: str,
    start: tuple[int, int],
    end: tuple[int, int],
) -> str:
    """Return a token-position span from normalized source text."""
    lines = text.splitlines(keepends=True)
    offsets: list[int] = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def absolute(position: tuple[int, int]) -> int:
        line, column = position
        if line < 1 or line > len(lines) + 1:
            raise ValueError("token position is outside fragment")
        return offsets[line - 1] + column

    return text[absolute(start) : absolute(end)]


def _normalise_fragment_lexically(text: str) -> str:
    """Normalize an incomplete fragment without treating comment quotes as strings."""
    pieces: list[str] = []
    pending_space = False
    in_comment = False
    index = 0
    while index < len(text):
        character = text[index]
        if in_comment:
            if character == "\n":
                in_comment = False
            else:
                if character.isspace():
                    pending_space = True
                    index += 1
                    continue
                if pending_space and pieces:
                    pieces.append(" ")
                pieces.append(character)
                pending_space = False
                index += 1
                continue
        if character.isspace():
            pending_space = True
            index += 1
            continue
        literal_end = _string_literal_end(text, index)
        if character == "#" and literal_end is None:
            if pending_space and pieces:
                pieces.append(" ")
            pieces.append(character)
            pending_space = False
            in_comment = True
            index += 1
            continue
        piece = text[index:literal_end] if literal_end is not None else character
        if pending_space and pieces:
            pieces.append(" ")
        pieces.append(piece)
        pending_space = False
        index = literal_end if literal_end is not None else index + 1
    return "".join(pieces).strip()


def _string_literal_end(text: str, start: int) -> int | None:
    """Return the exclusive end of a Python string token at ``start``."""
    prefix_end = start
    while prefix_end < len(text) and text[prefix_end] in "rRuUbBfF":
        prefix_end += 1
    if prefix_end == start or prefix_end - start > 3:
        prefix_end = start
    if prefix_end >= len(text) or text[prefix_end] not in "'\"":
        return None
    quote = text[prefix_end]
    delimiter = quote * 3 if text.startswith(quote * 3, prefix_end) else quote
    index = prefix_end + len(delimiter)
    while index < len(text):
        if text[index] == "\\":
            index += 2
        elif text.startswith(delimiter, index):
            return index + len(delimiter)
        else:
            index += 1
    return len(text)


def _identity(entry: dict[str, Any], source_root: Path | None) -> DuplicateIdentity:
    first = entry.get("firstFile")
    second = entry.get("secondFile")
    fragment = entry.get("fragment")
    if not isinstance(first, dict) or not isinstance(second, dict) or not isinstance(fragment, str):
        raise ValueError("duplicate report entry is missing source or fragment data")
    first_location = _normalise_location(first)
    second_location = _normalise_location(second)
    first_file = first_location.source
    second_file = second_location.source
    lines = entry.get("lines")
    if isinstance(lines, bool) or not isinstance(lines, int) or lines <= 0:
        raise ValueError("duplicate report entry has an invalid line count")
    format_name = entry.get("format")
    if not isinstance(format_name, str) or not format_name:
        raise ValueError("duplicate report entry has an invalid format")
    sorted_locations = sorted(
        (first_location, second_location),
        key=lambda location: (
            location.source,
            location.start,
            location.start_column if location.start_column is not None else -1,
        ),
    )
    locations = (
        (sorted_locations[0].source, sorted_locations[0].start),
        (sorted_locations[1].source, sorted_locations[1].start),
    )
    sorted_sources = sorted((first_file, second_file))
    sources = (sorted_sources[0], sorted_sources[1])
    canonical_fragment = (
        _source_fragment(source_root, sorted_locations[0], lines)
        if source_root is not None
        else fragment
    )
    normalised_fragment = _normalise_fragment(canonical_fragment)
    if not normalised_fragment:
        raise ValueError("duplicate report entry has an empty fragment")
    fragment_digest = hashlib.sha256(normalised_fragment.encode("utf-8")).hexdigest()
    context_digests = tuple(
        _context_digest(source_root, location.source, location.start, lines)
        if source_root is not None
        else None
        for location in sorted_locations
    )
    return DuplicateIdentity(
        format_name,
        fragment_digest,
        first_file,
        second_file,
        lines,
        sources,
        locations,
        context_digests,
    )


def _fingerprint(identity: DuplicateIdentity, occurrence_index: int) -> DuplicateFinding:
    identity_payload = {
        "format": identity.format,
        "fragment_digest": identity.fragment_digest,
        "occurrence_index": occurrence_index,
        "sources": identity.sources,
        "context_digests": identity.context_digests,
    }
    digest = hashlib.sha256(
        json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return DuplicateFinding(digest, identity.first_file, identity.second_file, identity.lines)


def load_report(path: Path, *, source_root: Path | None = None) -> DuplicateReport:
    document = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if not isinstance(document, dict):
        raise ValueError("duplicate report must contain a JSON object")
    duplicates = document.get("duplicates")
    statistics = document.get("statistics")
    if not isinstance(duplicates, list) or not isinstance(statistics, dict):
        raise ValueError("duplicate report is missing duplicates or total statistics")
    total = statistics.get("total")
    if not isinstance(total, dict) or not all(isinstance(entry, dict) for entry in duplicates):
        raise ValueError("duplicate report has invalid duplicate entries or total statistics")
    identities = tuple(_identity(entry, source_root) for entry in duplicates)
    grouped_indices: defaultdict[
        tuple[str, str, tuple[str, str], tuple[str | None, str | None]], list[int]
    ] = defaultdict(list)
    for index, identity in enumerate(identities):
        grouped_indices[identity.grouping_key].append(index)
    occurrence_indices: dict[int, int] = {}
    for indices in grouped_indices.values():
        for occurrence_index, index in enumerate(
            sorted(indices, key=lambda item: identities[item].locations), start=1
        ):
            occurrence_indices[index] = occurrence_index
    findings = tuple(
        _fingerprint(identity, occurrence_indices[index])
        for index, identity in enumerate(identities)
    )
    clones = total.get("clones")
    if isinstance(clones, bool) or not isinstance(clones, int) or clones < 0:
        raise ValueError("duplicate report has an invalid clone count")
    if clones != len(findings):
        raise ValueError("duplicate report clone count does not match its entries")
    duplicated_lines = total.get("duplicatedLines")
    percentage = total.get("percentage")
    if (
        isinstance(duplicated_lines, bool)
        or not isinstance(duplicated_lines, int)
        or duplicated_lines < 0
    ):
        raise ValueError("duplicate report has an invalid duplicated-line count")
    if isinstance(percentage, bool) or not isinstance(percentage, (int, Decimal)) or percentage < 0:
        raise ValueError("duplicate report has an invalid duplicated percentage")
    return DuplicateReport(findings, duplicated_lines, Decimal(str(percentage)))


def load_status(path: Path) -> int:
    matches = STATUS_PATTERN.findall(path.read_text(encoding="utf-8"))
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one QUALITY_COMMAND_STATUS marker, found {len(matches)}"
        )
    return int(matches[0])


def _decimal_metric(metrics: dict[str, Any], name: str) -> Decimal:
    metric = metrics.get(name)
    if not isinstance(metric, dict):
        raise ValueError(f"missing duplicate baseline metric {name}")
    value = metric.get("threshold")
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)) or value < 0:
        raise ValueError(f"invalid duplicate baseline threshold for {name}")
    return Decimal(str(value))


def _integer_metric(metrics: dict[str, Any], name: str) -> int:
    value = _decimal_metric(metrics, name)
    if value != value.to_integral_value():
        raise ValueError(f"invalid integer duplicate baseline threshold for {name}")
    return int(value)


def evaluate(report: DuplicateReport, baseline: dict[str, Any], status: int) -> RatchetResult:
    if baseline.get("schema_version") != 1:
        raise ValueError("duplicate baseline has an unsupported schema version")
    if baseline.get("detector") != DETECTOR_POLICY:
        raise ValueError("duplicate baseline detector policy does not match the pinned policy")
    metrics = baseline.get("metrics")
    allowed = baseline.get("allowed_fingerprints")
    if not isinstance(metrics, dict) or not isinstance(allowed, list):
        raise ValueError("duplicate baseline is missing metrics or allowed_fingerprints")
    if not all(isinstance(value, str) for value in allowed):
        raise ValueError("duplicate baseline fingerprints must be strings")
    if len(set(allowed)) != len(allowed):
        raise ValueError("duplicate baseline fingerprints must be unique")
    allowed_set = set(allowed)
    current_set = {finding.fingerprint for finding in report.findings}
    return RatchetResult(
        report=report,
        baseline_clone_count=_integer_metric(metrics, "clone_count"),
        baseline_duplicated_lines=_integer_metric(metrics, "duplicated_lines"),
        baseline_duplicated_percentage=_decimal_metric(metrics, "duplicated_percentage"),
        baseline_fingerprint_count=len(allowed_set),
        unexpected_fingerprints=tuple(sorted(current_set - allowed_set)),
        stale_fingerprints=tuple(sorted(allowed_set - current_set)),
        status=status,
    )


def build_baseline(report: DuplicateReport) -> dict[str, Any]:
    fingerprints = sorted({finding.fingerprint for finding in report.findings})
    return {
        "schema_version": 1,
        "detector": DETECTOR_POLICY.copy(),
        "metrics": {
            "clone_count": {"baseline": len(report.findings), "threshold": len(report.findings)},
            "duplicated_lines": {
                "baseline": report.duplicated_lines,
                "threshold": report.duplicated_lines,
            },
            "duplicated_percentage": {
                "baseline": report.duplicated_percentage,
                "threshold": report.duplicated_percentage,
            },
        },
        "allowed_fingerprints": fingerprints,
    }


def _encode_json(value: Any, *, indent: int = 0) -> str:
    """Serialize the baseline while preserving exact decimal JSON numbers."""

    if isinstance(value, bool) or value is None or isinstance(value, int):
        return json.dumps(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        if not value:
            return "[]"
        items = [_encode_json(item, indent=indent + 2) for item in value]
        prefix = " " * (indent + 2)
        return "[\n" + ",\n".join(prefix + item for item in items) + "\n" + " " * indent + "]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = [
            f"{json.dumps(str(key))}: {_encode_json(item, indent=indent + 2)}"
            for key, item in value.items()
        ]
        prefix = " " * (indent + 2)
        return "{\n" + ",\n".join(prefix + item for item in items) + "\n" + " " * indent + "}"
    raise TypeError(f"Unsupported baseline JSON value: {type(value).__name__}")


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(_encode_json(document) + "\n", encoding="utf-8")


def _print_result(result: RatchetResult) -> None:
    print(
        "Duplicate-code ratchet: "
        f"clones={result.clone_count}/{result.baseline_clone_count}, "
        f"duplicated_lines={result.report.duplicated_lines}/{result.baseline_duplicated_lines}, "
        "duplicated_percentage="
        f"{result.report.duplicated_percentage}/{result.baseline_duplicated_percentage}"
    )
    print(f"Unexpected stable duplicate findings: {len(result.unexpected_fingerprints)}")
    print(f"Stale baseline duplicate findings: {len(result.stale_fingerprints)}")
    metrics_unchanged = (
        result.clone_count == result.baseline_clone_count
        and result.report.duplicated_lines == result.baseline_duplicated_lines
        and result.report.duplicated_percentage == result.baseline_duplicated_percentage
    )
    if result.all_fingerprints_changed and metrics_unchanged:
        print(
            "  all fingerprints changed while duplicate metrics held steady; this indicates "
            "an identity-algorithm or generating-environment change, not new duplication"
        )
    if result.status != 0:
        print(f"Duplicate detector failed with QUALITY_COMMAND_STATUS={result.status}.")
    for finding in sorted(
        (
            finding
            for finding in result.report.findings
            if finding.fingerprint in result.unexpected_fingerprints
        ),
        key=lambda finding: (finding.first_file, finding.second_file, finding.lines),
    ):
        print(
            "  unexpected source pair and fragment: "
            f"{finding.first_file} <-> {finding.second_file} ({finding.lines} lines)"
        )
    if result.stale_fingerprints:
        print(
            "  stale baseline fingerprints require a reviewed --update-baseline to bank "
            "the improvement"
        )
    if not result.passed:
        print(
            "Duplicate-code ratchet failed: remove the new clone, correct the detector input, "
            "or make a reviewed baseline change after inspecting both source locations."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--artifact-log", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Repository root used to add stable local source-context evidence to identities.",
    )
    parser.add_argument("--initialize-baseline", action="store_true")
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()
    if args.initialize_baseline and args.update_baseline:
        parser.error("--initialize-baseline and --update-baseline are mutually exclusive")
    try:
        report = load_report(args.report, source_root=args.source_root)
        status = load_status(args.artifact_log)
        if args.initialize_baseline:
            if status != 0:
                print("Refusing to initialize duplicate-code baseline after detector failure.")
                return 2
            _write_json(args.baseline, build_baseline(report))
            print(f"Initialized duplicate-code baseline: {args.baseline}")
            return 0
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"), parse_float=Decimal)
        result = evaluate(report, baseline, status)
        _print_result(result)
        if args.update_baseline:
            if not result.can_update_baseline:
                print(
                    "Refusing to update duplicate-code baseline while new duplicates, "
                    "metric regressions, or detector failures remain."
                )
                return 2
            _write_json(args.baseline, build_baseline(report))
            print(f"Updated duplicate-code baseline: {args.baseline}")
            return 0
        return 0 if result.passed else 1
    except (AttributeError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Duplicate-code ratchet input error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
