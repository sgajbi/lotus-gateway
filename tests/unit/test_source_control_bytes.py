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
SCANNED_ROOTS = (
    "scripts",
    "src",
    "tests",
    "quality",
    ".github",
    "docs",
    "wiki",
)
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".ps1",
    ".sh",
    ".txt",
    ".toml",
    ".cfg",
}


def is_suspicious(byte: int) -> bool:
    """True for control bytes never legitimate in these files.

    Tab (0x09), newline (0x0A) and carriage return (0x0D) are excluded: they are
    ordinary formatting. Everything below 0x20 otherwise indicates an escape
    that was interpreted when it should have been written literally.
    """
    return byte < 0x09 or byte in (0x0B, 0x0C) or 0x0D < byte < 0x20


def _scanned_files() -> list[Path]:
    files: list[Path] = []
    for root in SCANNED_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        files.extend(
            path
            for path in base.rglob("*")
            if path.is_file()
            and path.suffix.lower() in TEXT_SUFFIXES
            and "__pycache__" not in path.parts
        )
    return files


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
