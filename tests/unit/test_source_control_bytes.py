"""Source files must not carry control bytes a shell escape produced.

A backslash escape written through an interpreting heredoc is expanded before
the file exists: ``\\b`` in a regex becomes a literal 0x08 backspace, ``\\t`` a
tab, ``\\f`` a formfeed. The corruption is invisible by construction — a
terminal does not render 0x08, a diff shows nothing unusual, and re-reading the
source cannot see it. Only the bytes can.

It is not hypothetical. A sibling repository's guard compiled to
``'\\x08([A-Z][a-z]+)-only\\x08'`` and passed on the exact defect it was written
to catch, because no real text contains a backspace. A guard corrupted this way
does not fail loudly; it silently matches nothing. In a sibling's review ledger
the same mechanism ate the first letter of nine real identifiers in prose, where
nothing in Markdown rendering signals it at all.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# How much of a file decides its type. A NUL byte does not occur in text and
# appears within the first block of every binary format in this repository.
TYPE_SNIFF_BYTES = 8192


def is_suspicious(byte: int) -> bool:
    """True for control bytes never legitimate in a text file.

    Tab (0x09), newline (0x0A) and carriage return (0x0D) are excluded: they are
    ordinary formatting. Everything else below 0x20 indicates an escape that was
    interpreted when it should have been written literally.
    """
    return byte < 0x09 or byte in (0x0B, 0x0C) or 0x0D < byte < 0x20


def is_text(data: bytes) -> bool:
    """Classify by CONTENT, not by name.

    An extension allowlist cannot express "text": it silently omits every
    dot-prefixed or extensionless file, and `.importlinter` and `quality/.npmrc`
    are both real configuration this guard must cover. Deciding on a NUL byte
    inverts that — text is the default and binary is the exception that can
    actually be detected — so a file is skipped only when its own bytes say it
    is not text.
    """
    return b"\x00" not in data[:TYPE_SNIFF_BYTES]


@lru_cache(maxsize=1)
def _inventory() -> tuple[Path, ...]:
    """Tracked files, from git, as the reproducible definition of source.

    Two properties matter and only git provides both.

    It is REPRODUCIBLE: the same commit yields the same inventory on a runner, in
    the container and on a workstation, where a filesystem walk yields whatever
    happens to be lying in the tree.

    It EXCLUDES BUILD OUTPUT BY CONSTRUCTION. An ANSI-coloured log is full of
    0x1b, which this guard is right to reject in source and must never reject in
    a file nobody tracks. A walk reads those logs and fails on them, which
    teaches the reader to ignore the gate — and a gate that gets ignored is
    worse than no gate. Ignored-ness is not a property a walk can recover, so it
    is taken from the tool that owns it.

    An earlier revision walked the filesystem to avoid needing the git binary
    inside the CI-local container. That fixed the wrong half: the container
    bind-mounts the repository, `.git` and all, so the inventory was always
    available there — only the binary was missing, and that is a property of the
    lane, not of this check.
    """
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z"],
        capture_output=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "git ls-files failed, so the source inventory cannot be established: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}. This check must not "
            "fall back to walking the filesystem — that reads untracked build output "
            "and fails on logs nobody tracks."
        )

    paths: list[Path] = []
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        path = REPO_ROOT / entry.decode("utf-8")
        if not path.is_file() or path.is_symlink():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if is_text(data):
            paths.append(path)
    return tuple(paths)


def _source_inventory() -> list[Path]:
    """The cached inventory, as a list.

    Cached because four assertions need it and each rebuild reads every tracked
    file. Over the CI-local bind mount that difference was minutes, and a gate
    people wait for is a gate people skip.
    """
    return list(_inventory())


def find_offenders(paths: list[Path]) -> list[str]:
    """Report the first control byte in each file that carries one."""
    offenders: list[str] = []
    for path in paths:
        data = path.read_bytes()
        for offset, byte in enumerate(data):
            if is_suspicious(byte):
                line = data[:offset].count(b"\n") + 1
                try:
                    name = path.relative_to(REPO_ROOT).as_posix()
                except ValueError:
                    name = str(path)
                offenders.append(f"{name}:{line} byte=0x{byte:02x}")
                break
    return offenders


def test_no_source_file_carries_an_interpreted_escape() -> None:
    offenders = find_offenders(_source_inventory())

    assert not offenders, (
        "these files carry control bytes, which a shell escape produces when a "
        "literal backslash sequence was meant; a pattern corrupted this way "
        "matches nothing and its guard passes silently: " + "; ".join(offenders)
    )


def test_the_scan_reads_a_meaningful_number_of_files() -> None:
    """A zero-input scan would pass while checking nothing."""
    files = _source_inventory()
    assert len(files) > 100, f"only {len(files)} files scanned; the assertion would be hollow"


def test_the_detector_recognises_each_corruption_it_exists_for() -> None:
    """Prove the check fails on the shapes it forbids, not only that it passes."""
    for escape, byte in (("\\b", 0x08), ("\\f", 0x0C), ("\\v", 0x0B), ("\\a", 0x07)):
        assert is_suspicious(byte), f"{escape} expands to 0x{byte:02x} and must be rejected"
    for legitimate in (0x09, 0x0A, 0x0D, 0x20, 0x41):
        assert not is_suspicious(legitimate), f"0x{legitimate:02x} is ordinary text"


def test_corrupted_tracked_text_is_rejected(tmp_path: Path) -> None:
    """The rejection half, exercised rather than asserted about."""
    victim = tmp_path / "config.toml"
    victim.write_bytes(b"[tool]\nname = " + bytes([0x08]) + b"business_date\n")

    offenders = find_offenders([victim])

    assert offenders, "a tracked text file carrying 0x08 must be reported"
    assert "byte=0x08" in offenders[0]
    assert offenders[0].endswith(":2 byte=0x08"), f"the finding must name the line: {offenders[0]}"


def test_ignored_ansi_logs_are_accepted_because_they_are_not_source(tmp_path: Path) -> None:
    """The acceptance half, and the reason it holds.

    An ANSI-coloured log is genuinely full of 0x1b, so it would be REPORTED if it
    were scanned. What protects it is not the byte classifier but the inventory:
    it is not tracked, so it is not source. Proving both halves separately is the
    point — otherwise "the gate is quiet" could equally mean the classifier is
    broken.
    """
    log = tmp_path / "gateway-ci.log"
    log.write_bytes(b"\x1b[31mFAILED\x1b[0m tests/unit/test_x.py\n")

    assert find_offenders([log]), "an ANSI log does carry bytes this guard rejects"

    tracked = {path.relative_to(REPO_ROOT).as_posix() for path in _source_inventory()}
    assert not [name for name in tracked if name.endswith(".log")], (
        "no .log file is tracked, so none may appear in the inventory"
    )


def test_the_inventory_covers_dot_prefixed_and_extensionless_configuration() -> None:
    """The files a suffix allowlist silently omitted must be in scope.

    `.importlinter` and `quality/.npmrc` are real tracked configuration whose
    names carry no usable extension. Under the previous name-based rule the scan
    passed while never opening either — a guard reporting success about files it
    did not read.
    """
    scanned = {path.relative_to(REPO_ROOT).as_posix() for path in _source_inventory()}

    for required in (".importlinter", "quality/.npmrc"):
        assert (REPO_ROOT / required).is_file(), f"{required} is missing from the repository"
        assert required in scanned, f"{required} is tracked but the inventory omits it"


def test_binary_content_is_excluded_by_its_own_bytes() -> None:
    """Classification must reject binary without consulting the file name."""
    assert is_text(b"# a comment\nkey = value\n")
    assert is_text(b"")
    assert not is_text(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    # A NUL beyond the sniff window does not reclassify a text file.
    assert is_text(b"x" * (TYPE_SNIFF_BYTES + 16) + b"\x00")


def test_a_clean_corpus_produces_no_findings() -> None:
    """Silence on known-good input, not only a hit on known-bad input.

    A scan that flags correct files trains its reader to ignore it, so the
    accepted case is asserted as explicitly as the rejected one.
    """
    clean = (
        b"[importlinter]\nroot_package = app\n",
        b"registry=https://registry.npmjs.org/\n",
        b"# Title\n\nProse with tabs\tand CRLF line ends.\r\n",
    )
    for data in clean:
        assert is_text(data)
        assert not [byte for byte in data if is_suspicious(byte)]
