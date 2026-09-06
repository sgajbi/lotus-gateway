"""Source files must not carry control bytes a shell escape produced.

A backslash escape written through an interpreting heredoc is expanded before
the file exists: ``\\b`` in a regex becomes a literal 0x08 backspace, ``\\t`` a
tab, ``\\f`` a formfeed. The corruption is invisible by construction — a
terminal does not render 0x08, a diff shows nothing unusual, and re-reading the
source cannot see it. Only the bytes can.

It is not hypothetical. A sibling repository's guard compiled to
``'\\x08([A-Z][a-z]+)-only\\x08'`` and passed on the exact defect it was written
to catch, because no real text contains a backspace. A guard corrupted this way
does not fail loudly; it silently matches nothing.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Directories that are not source: version control internals, dependency trees,
# build output and caches. Everything else is walked. Enumerating what to SKIP
# rather than what to scan means a new top-level directory is covered the day it
# is added, which a suffix or directory allowlist is not.
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "venv",
}

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
    are both real configuration this guard must cover. A name-based rule also
    has to be extended for every new format, and the omission is invisible --
    the scan still passes, having looked at less.

    Deciding on a NUL byte inverts that. Text is the default and binary is the
    exception it can actually detect, so a file is only skipped when its own
    bytes say it is not text.
    """
    return b"\x00" not in data[:TYPE_SNIFF_BYTES]


def _scanned_files() -> list[Path]:
    """Every file under the repository that its own content shows to be text.

    Deliberately free of any subprocess: this suite runs inside the CI-local
    container, which has no git binary, so shelling out to `git ls-files` made
    the whole gate fail to run there while passing on the runner. A guard that
    cannot execute in one of its two required environments is not a guard.
    """
    found: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if any(part in EXCLUDED_DIRECTORY_NAMES for part in path.parts):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if is_text(data):
            found.append(path)
    return found


def test_no_source_file_carries_an_interpreted_escape() -> None:
    offenders: list[str] = []
    for path in _scanned_files():
        data = path.read_bytes()
        for offset, byte in enumerate(data):
            if is_suspicious(byte):
                line = data[:offset].count(b"\n") + 1
                offenders.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}:{line} byte=0x{byte:02x}"
                )
                break

    assert not offenders, (
        "these files carry control bytes, which a shell escape produces when a "
        "literal backslash sequence was meant; a pattern corrupted this way "
        "matches nothing and its guard passes silently: " + "; ".join(offenders)
    )


def test_the_scan_reads_a_meaningful_number_of_files() -> None:
    """A zero-input scan would pass while checking nothing."""
    files = _scanned_files()
    assert len(files) > 100, f"only {len(files)} files scanned; the assertion would be hollow"


def test_the_detector_recognises_each_corruption_it_exists_for() -> None:
    """Prove the check fails on the shapes it forbids, not only that it passes."""
    for escape, byte in (("\\b", 0x08), ("\\f", 0x0C), ("\\v", 0x0B), ("\\a", 0x07)):
        assert is_suspicious(byte), f"{escape} expands to 0x{byte:02x} and must be rejected"
    for legitimate in (0x09, 0x0A, 0x0D, 0x20, 0x41):
        assert not is_suspicious(legitimate), f"0x{legitimate:02x} is ordinary text"


def test_the_policy_covers_dot_prefixed_and_extensionless_configuration() -> None:
    """The files a suffix allowlist silently omitted must be in scope.

    `.importlinter` and `quality/.npmrc` are real configuration whose names carry
    no usable extension. Under the previous name-based rule the scan passed
    while never opening either, which is the failure mode that matters: a guard
    reporting success about files it did not read.
    """
    scanned = {path.relative_to(REPO_ROOT).as_posix() for path in _scanned_files()}

    for required in (".importlinter", "quality/.npmrc"):
        assert (REPO_ROOT / required).is_file(), f"{required} is missing from the repository"
        assert required in scanned, f"{required} exists but the scan does not cover it"


def test_binary_content_is_excluded_by_its_own_bytes() -> None:
    """Classification must reject binary without consulting the file name."""
    assert is_text(b"# a comment\nkey = value\n")
    assert is_text(b"")
    assert not is_text(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    # A NUL beyond the sniff window does not make the file binary.
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
